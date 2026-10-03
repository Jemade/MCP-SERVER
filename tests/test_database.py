import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest

from personal_mcp.database import ReadOnlySQL, TaskStore


@pytest.fixture
def store(tmp_path):
    return TaskStore(tmp_path / "tasks.db")


def test_task_lifecycle_and_persistence(store):
    task = store.create("Ship MCP", due_date="2026-10-10", priority="high")
    task = store.update(task["id"], task["version"], {"status": "done", "due_date": None})
    archived = store.archive(task["id"], task["version"])
    assert store.list()["total"] == 0
    restored = store.archive(task["id"], archived["version"], False)
    assert restored["status"] == "done"
    assert len(store.history(task["id"])) == 4
    assert TaskStore(store.path).get(task["id"]) == restored


def test_stale_update_is_atomic(store):
    task = store.create("Original")
    store.update(task["id"], 1, {"title": "Changed"})
    with pytest.raises(ValueError, match="version conflict"):
        store.update(task["id"], 1, {"title": "Overwritten"})
    assert store.get(task["id"])["title"] == "Changed"
    assert len(store.history(task["id"])) == 2


def test_concurrent_versions_only_one_winner(store):
    task = store.create("Shared")

    def attempt(title):
        try:
            return store.update(task["id"], 1, {"title": title})
        except ValueError:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, ["A", "B"]))
    assert sum(x is not None for x in results) == 1


def test_filters_and_literal_search(store):
    store.create("50% delivery", priority="high", due_date="2026-10-05")
    store.create("Other")
    assert store.list(search="%")["total"] == 1
    assert store.list(priority="high", due_before="2026-10-06")["total"] == 1
    assert store.list(limit=1)["has_more"]


@pytest.mark.parametrize(
    "kwargs",
    [{"title": ""}, {"title": "x", "priority": "urgent"}, {"title": "x", "due_date": "tomorrow"}],
)
def test_create_validation(store, kwargs):
    with pytest.raises(ValueError):
        store.create(**kwargs)


@pytest.fixture
def reader(store):
    store.create("Ship MCP")
    with store.connection() as db:
        db.execute("CREATE TABLE secrets(value TEXT)")
        db.execute("INSERT INTO secrets VALUES ('private')")
    return ReadOnlySQL(store.path, ["tasks"])


def test_schema_and_parameterized_query(reader):
    assert set(reader.schema()) == {"tasks"}
    result = reader.query("SELECT title FROM tasks WHERE title=?", ["Ship MCP"])
    assert result["rows"] == [["Ship MCP"]]
    assert reader.query("SELECT count(*) FROM tasks")["rows"] == [[1]]


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM tasks",
        "UPDATE tasks SET title='bad'",
        "DROP TABLE tasks",
        "INSERT INTO tasks(title) VALUES ('bad')",
        "PRAGMA user_version",
        "ATTACH DATABASE ':memory:' AS extra",
        "SELECT * FROM secrets",
        "SELECT * FROM sqlite_master",
        "SELECT load_extension('anything')",
        "SELECT readfile('/etc/passwd')",
        "SELECT * FROM tasks; DELETE FROM tasks",
        "WITH x AS (SELECT * FROM secrets) SELECT * FROM x",
    ],
)
def test_sql_authorization(reader, sql):
    with pytest.raises(ValueError):
        reader.query(sql)
    assert reader.query("SELECT title FROM tasks")["rows"] == [["Ship MCP"]]


def test_result_limit(reader):
    result = reader.query("SELECT a.id FROM tasks a CROSS JOIN tasks b", max_rows=1)
    assert result["returned_rows"] == 1


def test_recursive_query_blocked(reader):
    with pytest.raises(ValueError):
        reader.query(
            "WITH RECURSIVE x(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM x) SELECT * FROM x"
        )


def test_large_output_truncated(store):
    for _ in range(12):
        store.create("x", description="a" * 10000)
    result = ReadOnlySQL(store.path, ["tasks"]).query("SELECT description FROM tasks")
    assert result["truncated"]
    assert result["returned_rows"] < 12


def test_external_database(tmp_path):
    path = tmp_path / "courses.db"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE courses(code TEXT, title TEXT)")
        db.execute("INSERT INTO courses VALUES ('DEMO101','Sample course')")
    reader = ReadOnlySQL(path, ["courses"])
    assert reader.query("SELECT code FROM courses")["rows"] == [["DEMO101"]]
