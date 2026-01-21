import os
import json
import asyncio
import logging
import mcp.types
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass
from agentscope.mcp import HttpStatelessClient

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class ServiceInfo:
    """服务信息"""
    name: str 
    description: Optional[str]
    tools: Dict[str, mcp.types.Tool]

# MCP服务管理器
class MCPServiceManager:
    """管理多个MCP服务，直接使用HttpStatelessClient"""
    
    def __init__(self):
        self.mcp_clients: Dict[str, HttpStatelessClient] = {} # service_name -> HttpStatelessClient
        self.services: Dict[str, ServiceInfo] = {}  # service_name -> ServiceInfo
    
    async def register_service(
        self, 
        service_name: str, 
        mcp_url: str, 
        headers: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
    ) -> None:
        """注册MCP服务
        
        Args:
            service_name: 服务名称
            mcp_url: MCP服务URL
            headers: 可选的HTTP headers字典
            description: 服务描述
            
        Raises:
            ValueError: 当服务名称已存在时
            ConnectionError: 当无法连接到MCP服务时
            Exception: 其他初始化或注册过程中的错误
        """
        # 检查服务是否已存在
        if service_name in self.services:
            raise ValueError(f"服务 '{service_name}' 已存在，请使用不同的服务名称")
        
        # 初始化HttpStatelessClient
        init_params = {
            "name": service_name,
            "transport": "streamable_http",
            "url": mcp_url,
        }
        
        # 如果有headers，添加到初始化参数中
        if headers:
            init_params["headers"] = headers
            
        client = HttpStatelessClient(**init_params)
        self.mcp_clients[service_name] = client

        # 获取所有工具
        all_tools = await client.list_tools()
        
        # 注册所有工具，并保存工具信息
        service_info = ServiceInfo(
            name=service_name, 
            description=description or f"MCP服务: {service_name}", 
            tools={}
        )
        for tool in all_tools:
            service_info.tools[tool.name] = tool
            
        self.services[service_name] = service_info
        logger.info(f"注册服务 '{service_name}' 成功，工具数量: {len(all_tools)}")

    async def register_services_from_file(
        self, 
        config_path: Union[str, Path]
    ) -> Dict[str, bool]:
        """从本地配置文件注册多个MCP服务
        
        此方法会尝试注册所有服务，即使某些服务注册失败也会继续处理其他服务。
        
        Args:
            config_path: 配置文件路径（支持字符串或Path对象）
            
        Returns:
            Dict[str, bool]: 服务名称到注册结果的映射
            
        Raises:
            FileNotFoundError: 当配置文件不存在时
            json.JSONDecodeError: 当配置文件格式错误时
            ValueError: 当配置文件缺少必需字段时
            
        配置文件格式示例:
        {
            "mcpServers": {
                "service_name": {
                    "type": "streamable_http",
                    "url": "http://example.com/mcp/",
                    "headers": {
                        "Authorization": "Bearer token"
                    },
                    "timeout": 30000
                }
            }
        }
        """
        # 转换为Path对象
        if isinstance(config_path, str):
            config_path = Path(config_path)
        
        # 检查文件是否存在
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        # 读取配置文件
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 获取所有MCP服务配置
        mcp_servers = config.get("mcpServers", {})
        
        if not mcp_servers:
            raise ValueError("配置文件中没有找到 'mcpServers' 配置")
        
        logger.info(f"从配置文件读取到 {len(mcp_servers)} 个服务配置")
        
        results = {}
        
        # 注册每个服务
        for service_name, service_config in mcp_servers.items():
            logger.info(f"正在注册服务: {service_name}")
            
            try:
                # 提取服务配置
                url = service_config.get("url")
                headers = service_config.get("headers", {})
                service_type = service_config.get("type", "streamable_http")
                description = service_config.get("description")
                
                # 验证必需参数
                if not url:
                    logger.warning(f"服务 '{service_name}' 缺少URL配置，跳过")
                    results[service_name] = False
                    continue
                
                # 验证服务类型
                if service_type != "streamable_http":
                    logger.warning(f"服务 '{service_name}' 的类型为 {service_type}，当前仅支持 streamable_http")
                
                # 注册服务
                await self.register_service(
                    service_name=service_name,
                    mcp_url=url,
                    headers=headers,
                    description=description
                )
                
                results[service_name] = True
                
            except Exception as e:
                logger.error(f"服务 '{service_name}' 注册失败: {str(e)}")
                results[service_name] = False
        
        # 统计注册结果
        success_count = sum(1 for v in results.values() if v)
        total_count = len(results)
        logger.info(f"注册完成: {success_count}/{total_count} 个服务注册成功")
        
        return results

    def get_all_services(self) -> List[Dict[str, str]]:
        """获取所有服务信息"""
        all_services = []
        for service_name in self.services:
            all_services.append({
                "name": service_name,
                "description": self.services[service_name].description
            })
        return all_services

    def get_all_tools_by_service(self, service_name: str) -> List[Dict[str, str]]:
        """获取指定服务的所有工具
        
        Args:
            service_name: 服务名称
            
        Returns:
            工具列表，如果服务不存在则抛出 ValueError
            
        Raises:
            ValueError: 当服务不存在时
        """
        if service_name not in self.services:
            raise ValueError(f"服务 '{service_name}' 不存在")
        
        all_tools = []
        for tool_name, tool in self.services[service_name].tools.items():
            all_tools.append({
                "name": tool_name,
                "description": tool.description
            })
        return all_tools

    def get_tool_info(self, service_name: str, tool_name: str) -> Dict[str, Any]:
        """获取指定工具的详细信息
        
        Args:
            service_name: 服务名称
            tool_name: 工具名称
            
        Returns:
            包含工具信息的字典，包含 name, description, inputSchema
            
        Raises:
            ValueError: 当服务或工具不存在时
        """
        if service_name not in self.services:
            raise ValueError(f"服务 '{service_name}' 不存在")
        
        if tool_name not in self.services[service_name].tools:
            raise ValueError(f"工具 '{tool_name}' 在服务 '{service_name}' 中不存在")
        
        tool = self.services[service_name].tools[tool_name]
        
        # 将 mcp.types.Tool 转换为可序列化的字典
        return {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.inputSchema if hasattr(tool, 'inputSchema') else {}
        }

    async def execute_tool(self, service_name: str, tool_name: str, input_data: dict) -> str:
        """执行指定的MCP工具，并返回执行结果
        
        Args:
            service_name: 服务名称
            tool_name: 工具名称
            input_data: 工具输入参数字典
            
        Returns:
            str: 工具执行结果（JSON字符串或文本）
            
        Raises:
            ValueError: 当服务或工具不存在时
            RuntimeError: 当工具执行失败时
        """
        # 验证服务存在
        if service_name not in self.services:
            raise ValueError(f"服务 '{service_name}' 不存在，可用服务: {list(self.services.keys())}")
        
        # 验证工具存在
        if tool_name not in self.services[service_name].tools:
            available_tools = list(self.services[service_name].tools.keys())
            raise ValueError(f"工具 '{tool_name}' 在服务 '{service_name}' 中不存在，可用工具: {available_tools}")

        try:
            client = self.mcp_clients[service_name]
            async_func = await client.get_callable_function(func_name=tool_name)
            
            if not async_func:
                raise RuntimeError(f"无法获取工具 '{tool_name}' 的可调用函数")
            
            # 执行工具
            result = await async_func(**input_data)
            
            # 格式化返回结果
            if isinstance(result, dict):
                return json.dumps(result, ensure_ascii=False, indent=2)
            elif isinstance(result, (list, tuple)):
                return json.dumps(result, ensure_ascii=False, indent=2)
            elif isinstance(result, str):
                return result
            else:
                return str(result)
                
        except TypeError as e:
            # 参数类型错误
            raise ValueError(f"工具参数错误: {str(e)}. 请检查 input_data 是否符合工具的 inputSchema")
        except Exception as e:
            # 其他执行错误
            raise RuntimeError(f"执行工具 '{tool_name}' 失败: {str(e)}")

    async def close_all(self):
        """关闭所有MCP客户端"""
        # HttpStatelessClient可能不需要显式关闭
        self.mcp_clients.clear()
        self.services.clear()