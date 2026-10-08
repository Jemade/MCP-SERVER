"""Contract tests for every exposed MCP tool and its safety metadata."""

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from personal_mcp.server import create_server


EXPECTED = {
    "create_task": (False, False, False, False),
    "list_tasks": (True, False, True, False),
    "get_task": (True, False, True, False),
    "update_task": (False, False, False, False),
    "archive_task": (False, True, False, False),
    "restore_task": (False, False, False, False),
    "task_history": (True, False, True, False),
    "database_schema": (True, False, True, False),
    "query_database": (True, False, True, False),
    "search_locations": (True, False, True, True),
    "weather_forecast": (True, False, True, True),
}


async def test_all_tools_have_explicit_annotations(tmp_path):
    server = create_server(tmp_path / "tasks.db")
    tools = {tool.name: tool for tool in await server.list_tools()}
    assert set(tools) == set(EXPECTED)
    for name, expected in EXPECTED.items():
        annotations = tools[name].annotations
        assert annotations is not None, name
        actual = (
            annotations.readOnlyHint,
            annotations.destructiveHint,
            annotations.idempotentHint,
            annotations.openWorldHint,
        )
        assert actual == expected, name


async def test_task_tool_lifecycle_through_mcp(tmp_path):
    server = create_server(tmp_path / "tasks.db")
    # Exercise the actual FastMCP argument-validation and dispatch layer.
    for name, args in (
        ("create_task", {"title": "Contract test"}),
        ("list_tasks", {}),
        ("get_task", {"task_id": 1}),
        ("update_task", {"task_id": 1, "expected_version": 1, "status": "done"}),
        ("task_history", {"task_id": 1}),
        ("archive_task", {"task_id": 1, "expected_version": 2}),
        ("restore_task", {"task_id": 1, "expected_version": 3}),
        ("database_schema", {}),
        ("query_database", {"sql_query": "SELECT count(*) AS total FROM tasks"}),
    ):
        result = await server.call_tool(name, args)
        assert result is not None, name


@pytest.mark.parametrize(
    ("name", "args"),
    [
        ("create_task", {"title": "", "priority": "urgent"}),
        ("list_tasks", {"limit": 101}),
        ("get_task", {}),
        ("update_task", {"task_id": 1, "expected_version": "invalid"}),
        ("archive_task", {"task_id": 1}),
        ("restore_task", {"task_id": 1}),
        ("task_history", {}),
        ("query_database", {"sql_query": ""}),
        ("search_locations", {}),
        ("weather_forecast", {"latitude": 0, "longitude": 0, "days": 8}),
    ],
)
async def test_invalid_arguments_rejected_at_tool_boundary(tmp_path, name, args):
    server = create_server(tmp_path / "tasks.db")
    with pytest.raises(ToolError):
        await server.call_tool(name, args)
