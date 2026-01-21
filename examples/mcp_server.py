"""FastMCP quickstart example.

Run from the repository root:
    python examples/mcp_server.py
"""

import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))


from mcp.server.fastmcp import FastMCP
from linker.manager import MCPServiceManager
import asyncio
from typing import List, Dict, Any
from pydantic import BaseModel, Field


# Create an MCP server
mcp = FastMCP("mcp-linker")
mcp_manager = MCPServiceManager()

# Add an addition tool
@mcp.tool()
def get_all_services() -> List[Dict[str, str]]:
    """获取所有已注册的 MCP 服务列表，包含服务名称和描述信息"""
    return mcp_manager.get_all_services()

@mcp.tool()
def get_all_tools_by_service(
    service_name: str = Field(..., description="【必填】MCP 服务名称，必须是 get_all_services 返回结果中的服务名称")
) -> List[Dict[str, str]]:
    """获取指定 MCP 服务下的所有可用工具列表，包含工具名称和描述，在调用此工具前，应先使用 get_all_services 获取可用的服务列表"""
    return mcp_manager.get_all_tools_by_service(service_name)

@mcp.tool()
def get_tool_info(
    service_name: str = Field(..., description="【必填】MCP 服务名称，必须是 get_all_services 返回结果中的服务名称"),
    tool_name: str = Field(..., description="【必填】工具名称，必须是 get_all_tools_by_service 返回结果中的工具名称")
) -> Dict[str, Any]:
    """获取指定 MCP 工具的详细信息，包括工具描述、参数定义和使用说明，在调用此工具前，应先使用 get_all_tools_by_service 获取可用的工具列表"""
    return mcp_manager.get_tool_info(service_name, tool_name)

@mcp.tool()
async def execute_tool(
    service_name: str = Field(..., description="【必填】MCP 服务名称，必须是 get_all_services 返回结果中的服务名称"),
    tool_name: str = Field(..., description="【必填】工具名称，必须是 get_all_tools_by_service 返回结果中的工具名称"),
    input_data: dict = Field(..., description="【必填】工具的输入参数，必须符合工具的 inputSchema 定义")
) -> dict:
    """执行指定的 MCP 工具，并返回执行结果，input_data 必须符合工具的 inputSchema 定义，如果不知道工具所需参数，必须通过 get_tool_info 查询工具详情"""
    result = await mcp_manager.execute_tool(service_name, tool_name, input_data)
    return result

# Run with streamable HTTP transport
if __name__ == "__main__":
    asyncio.run(mcp_manager.register_services_from_file("./mcp.json"))
    mcp.run(transport="streamable-http")