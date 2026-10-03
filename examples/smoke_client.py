"""Exercise a real MCP stdio subprocess without an LLM or an API key."""

import asyncio
import os
import sys
import tempfile

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    with tempfile.TemporaryDirectory() as folder:
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "personal_mcp.server", "--task-db", os.path.join(folder, "tasks.db")],
        )
        async with (
            stdio_client(params) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()
            tools = await session.list_tools()
            assert len(tools.tools) == 11
            created = await session.call_tool("create_task", {"title": "Test MCP connection"})
            assert not created.isError
            result = await session.call_tool(
                "query_database", {"sql_query": "SELECT title FROM tasks"}
            )
            assert not result.isError
            rejected = await session.call_tool("query_database", {"sql_query": "DELETE FROM tasks"})
            assert rejected.isError
            await session.read_resource("database://schema")
            prompt = await session.get_prompt("plan_day", {"day": "2026-10-04"})
            assert prompt.messages
            print(
                "MCP stdio smoke check passed: discovery, tools, resources, prompts, SQL rejection"
            )


if __name__ == "__main__":
    asyncio.run(main())
