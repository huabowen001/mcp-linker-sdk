import json
from agentscope.tool import ToolResponse
from linker.manager import MCPServiceManager
from typing import Callable
from agentscope.message import TextBlock
from pydantic import Field


def create_get_all_mcp_services_tool(mcp_manager: MCPServiceManager) -> Callable:
    """创建获取所有MCP服务的工具"""
    def get_all_mcp_services() -> ToolResponse:
        """获取所有已注册的 MCP 服务列表，包含服务名称和描述信息"""

        try:
            services = mcp_manager.get_all_services()
            return ToolResponse(content=[TextBlock(text=json.dumps(services, ensure_ascii=False))])
        except Exception as e:
            return ToolResponse(content=[TextBlock(text=f"获取MCP服务列表失败: {str(e)}")])

    return get_all_mcp_services 


def create_get_service_tools_tool(mcp_manager: MCPServiceManager) -> Callable:
    """创建获取指定MCP服务所有工具的工具"""
    def get_service_tools(service_name: str = Field(..., description="【必填】MCP 服务名称，必须是 get_all_services 返回结果中的服务名称")
    ) -> ToolResponse:
        """获取指定 MCP 服务下的所有可用工具列表，包含工具名称和描述，在调用此工具前，应先使用 get_all_services 获取可用的服务列表"""
        try:
            if not service_name:
                return ToolResponse(content=[TextBlock(text="服务名称不能为空")])
            # 检查服务是否存在
            services = mcp_manager.get_all_services()
            if not services:
                return ToolResponse(content=[TextBlock(text="没有可用的服务")])
            
            if service_name not in [service["name"] for service in services]:
                return ToolResponse(content=[TextBlock(text=f"服务 '{service_name}' 不存在。可用服务: {[service['name'] for service in services]}")])
            
            # 获取该服务的所有工具
            tools = mcp_manager.get_all_tools_by_service(service_name)
            return ToolResponse(content=[TextBlock(text=json.dumps(tools, ensure_ascii=False))])
        except Exception as e:
            return ToolResponse(content=[TextBlock(text=f"获取服务工具列表失败: {str(e)}")])

    return get_service_tools

# 创建获取工具详情的工具
def create_get_tool_info_tool(mcp_manager: MCPServiceManager) -> Callable:
    def get_tool_info(service_name: str = Field(..., description="【必填】MCP 服务名称，必须是 get_all_services 返回结果中的服务名称"),
    tool_name: str = Field(..., description="【必填】工具名称，必须是 get_all_tools_by_service 返回结果中的工具名称")
    ) -> ToolResponse:
        """获取指定 MCP 工具的详细信息，包括工具描述、参数定义和使用说明，在调用此工具前，应先使用 get_all_tools_by_service 获取可用的工具列表"""
        try:
            if not service_name or not tool_name:
                return ToolResponse(content=[TextBlock(text="服务名称和工具名称不能为空")])

            # 获取工具详细信息
            tool_info = mcp_manager.get_tool_info(service_name, tool_name)
            if not tool_info:
                return ToolResponse(content=[TextBlock(text=f"无法获取工具 '{tool_name}' 的详细信息")])
            
            # 格式化工具信息
            return ToolResponse(content=[TextBlock(text=json.dumps(tool_info, ensure_ascii=False, default=str))])
        except Exception as e:
            return ToolResponse(content=[TextBlock(text=f"获取工具详情失败: {str(e)}")])
    return get_tool_info


def create_execute_tool(mcp_manager: MCPServiceManager) -> Callable:
    async def execute_tool(service_name: str = Field(..., description="【必填】MCP 服务名称，必须是 get_all_services 返回结果中的服务名称"),
    tool_name: str = Field(..., description="【必填】工具名称，必须是 get_all_tools_by_service 返回结果中的工具名称"),
    input_data: dict = Field(..., description="【必填】工具的输入参数，必须符合工具的 inputSchema 定义")
    ) -> ToolResponse:
        """执行指定的 MCP 工具，并返回执行结果，input_data 必须符合工具的 inputSchema 定义，如果不知道工具所需参数，必须通过 get_tool_info 查询工具详情"""
        try:
            # 注意：这里需要 await，因为 execute_tool 是异步方法
            result = await mcp_manager.execute_tool(service_name, tool_name, input_data)
            return ToolResponse(content=[TextBlock(text=result)])
        except (ValueError, RuntimeError) as e:
            # 已知的业务异常，直接返回错误信息
            return ToolResponse(content=[TextBlock(text=f"执行工具失败: {str(e)}")])
        except Exception as e:
            # 未预期的异常，返回详细堆栈信息
            import traceback
            error_detail = traceback.format_exc()
            return ToolResponse(content=[TextBlock(text=f"执行工具时发生未预期错误: {str(e)}\n\n堆栈跟踪:\n{error_detail}")])
    return execute_tool