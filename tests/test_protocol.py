import pytest
from mcp.server.fastmcp.exceptions import ToolError

from personal_mcp.server import create_server


async def test_tools_resources_and_prompts(tmp_path):
    server = create_server(tmp_path / "tasks.db")
    tools = await server.list_tools()
    assert len(tools) == 11
    assert next(t for t in tools if t.name == "query_database").annotations.readOnlyHint
    assert not next(t for t in tools if t.name == "create_task").annotations.readOnlyHint
    assert len(await server.list_resources()) == 2
    assert len(await server.list_prompts()) == 2
    result = await server.call_tool("create_task", {"title": "Protocol task"})
    assert result
    resource = await server.read_resource("database://schema")
    assert resource


async def test_invalid_tool_argument(tmp_path):
    server = create_server(tmp_path / "tasks.db")
    with pytest.raises(ToolError):
        await server.call_tool("create_task", {"title": "Task", "priority": "urgent"})
