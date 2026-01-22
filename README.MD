# MCP Linker SDK

一个用于管理和调用 MCP (Model Context Protocol) 服务的 Python SDK，支持多服务注册、工具发现和异步执行。

## 📋 目录

- [功能特性](#功能特性)
- [安装](#安装)
- [快速开始](#快速开始)
- [核心组件](#核心组件)
- [使用指南](#使用指南)
- [配置文件格式](#配置文件格式)
- [AgentScope 集成](#agentscope-集成)
- [示例](#示例)
- [API 文档](#api-文档)
- [技术栈](#技术栈)
- [许可证](#许可证)

## ✨ 功能特性

- **多服务管理**：支持同时注册和管理多个 MCP 服务
- **配置文件支持**：从 JSON 配置文件批量注册服务
- **工具发现**：自动发现和注册服务提供的所有工具
- **异步执行**：基于 asyncio 的异步工具调用
- **AgentScope 集成**：提供 AgentScope 框架的工具包装器
- **HTTP 无状态客户端**：使用 streamable HTTP 传输协议
- **完善的错误处理**：详细的异常信息和日志记录

## 📦 安装

### 依赖要求

```bash
pip install agentscope mcp
```

### 从源码安装

```bash
git clone <repository-url>
cd mcp-linker-sdk
pip install -e .
```

## 🚀 快速开始

### 基本使用

```python
import asyncio
from linker.manager import MCPServiceManager

async def main():
    # 创建服务管理器
    manager = MCPServiceManager()
    
    # 注册单个服务
    await manager.register_service(
        service_name="my-service",
        mcp_url="http://example.com/mcp/",
        headers={"Authorization": "Bearer token"},
        description="我的 MCP 服务"
    )
    
    # 获取所有服务
    services = manager.get_all_services()
    print(f"已注册服务: {services}")
    
    # 获取服务的工具列表
    tools = manager.get_all_tools_by_service("my-service")
    print(f"可用工具: {tools}")
    
    # 执行工具
    result = await manager.execute_tool(
        service_name="my-service",
        tool_name="some-tool",
        input_data={"param": "value"}
    )
    print(f"执行结果: {result}")

asyncio.run(main())
```

### 从配置文件注册服务

```python
import asyncio
from linker.manager import MCPServiceManager

async def main():
    manager = MCPServiceManager()
    
    # 从配置文件批量注册
    results = await manager.register_services_from_file("./mcp.json")
    
    # 查看注册结果
    for service_name, success in results.items():
        status = "成功" if success else "失败"
        print(f"服务 {service_name}: {status}")

asyncio.run(main())
```

## 🏗️ 核心组件

### MCPServiceManager

MCP 服务管理器，负责服务的注册、管理和工具调用。

**主要方法：**

- `register_service()` - 注册单个 MCP 服务
- `register_services_from_file()` - 从配置文件批量注册服务
- `get_all_services()` - 获取所有已注册的服务
- `get_all_tools_by_service()` - 获取指定服务的工具列表
- `get_tool_info()` - 获取工具的详细信息
- `execute_tool()` - 执行指定的工具
- `close_all()` - 关闭所有客户端连接

### ServiceInfo

服务信息数据类，包含：

- `name` - 服务名称
- `description` - 服务描述
- `tools` - 工具字典 (工具名 -> Tool 对象)

## 📖 使用指南

### 1. 注册服务

#### 方式一：单个注册

```python
await manager.register_service(
    service_name="github",
    mcp_url="http://github-mcp.example.com/mcp",
    headers={"Authorization": "Bearer your-token"},
    description="GitHub MCP 服务"
)
```

#### 方式二：配置文件批量注册

创建 `mcp.json` 配置文件：

```json
{
    "mcpServers": {
        "github": {
            "type": "streamable_http",
            "url": "http://github-mcp.example.com/mcp",
            "headers": {
                "Authorization": "Bearer your-token"
            },
            "timeout": 30000
        },
        "amap": {
            "type": "streamable_http",
            "url": "http://amap-mcp.example.com/mcp",
            "headers": {
                "Authorization": "Bearer your-token"
            }
        }
    }
}
```

然后批量注册：

```python
results = await manager.register_services_from_file("./mcp.json")
```

### 2. 发现工具

```python
# 获取所有服务
services = manager.get_all_services()
# 返回: [{"name": "github", "description": "GitHub MCP 服务"}, ...]

# 获取服务的工具列表
tools = manager.get_all_tools_by_service("github")
# 返回: [{"name": "search_repos", "description": "搜索仓库"}, ...]

# 获取工具详细信息
tool_info = manager.get_tool_info("github", "search_repos")
# 返回: {"name": "search_repos", "description": "...", "inputSchema": {...}}
```

### 3. 执行工具

```python
result = await manager.execute_tool(
    service_name="github",
    tool_name="search_repos",
    input_data={"query": "python", "limit": 10}
)
print(result)  # JSON 字符串或文本结果
```

### 4. 错误处理

```python
try:
    result = await manager.execute_tool(
        service_name="github",
        tool_name="search_repos",
        input_data={"query": "python"}
    )
except ValueError as e:
    print(f"参数错误: {e}")
except RuntimeError as e:
    print(f"执行失败: {e}")
```

## 📝 配置文件格式

`mcp.json` 配置文件结构：

```json
{
    "mcpServers": {
        "服务名称": {
            "type": "streamable_http",
            "url": "MCP 服务的 URL 地址",
            "headers": {
                "Authorization": "认证令牌（可选）",
                "其他自定义头": "值"
            },
            "timeout": 30000,
            "description": "服务描述（可选）"
        }
    }
}
```

**字段说明：**

- `type` - 传输类型，目前仅支持 `streamable_http`
- `url` - MCP 服务的 URL 地址（必填）
- `headers` - HTTP 请求头（可选）
- `timeout` - 超时时间，单位毫秒（可选）
- `description` - 服务描述（可选）

## 🤖 AgentScope 集成

SDK 提供了 AgentScope 框架的工具包装器，可以将 MCP 工具转换为 AgentScope 工具。

### 创建 AgentScope 工具

```python
from linker.manager import MCPServiceManager
from linker.agentscope_tool import (
    create_get_all_mcp_services_tool,
    create_get_service_tools_tool,
    create_get_tool_info_tool,
    create_execute_tool
)

# 创建管理器
manager = MCPServiceManager()
await manager.register_services_from_file("./mcp.json")

# 创建 AgentScope 工具
get_services = create_get_all_mcp_services_tool(manager)
get_tools = create_get_service_tools_tool(manager)
get_info = create_get_tool_info_tool(manager)
execute = create_execute_tool(manager)

# 在 AgentScope 中使用
response = get_services()
print(response.content)
```

### 可用的 AgentScope 工具

1. **get_all_mcp_services** - 获取所有已注册的 MCP 服务列表
2. **get_service_tools** - 获取指定服务的工具列表
3. **get_tool_info** - 获取工具的详细信息
4. **execute_tool** - 执行指定的 MCP 工具

## 💡 示例

### 示例 1: 创建 MCP 服务器

参考 `examples/mcp_server.py`，使用 FastMCP 创建一个 MCP 服务器：

```python
from mcp.server.fastmcp import FastMCP
from linker.manager import MCPServiceManager
import asyncio

mcp = FastMCP("mcp-linker")
mcp_manager = MCPServiceManager()

@mcp.tool()
def get_all_services():
    """获取所有已注册的 MCP 服务列表"""
    return mcp_manager.get_all_services()

@mcp.tool()
async def execute_tool(service_name: str, tool_name: str, input_data: dict):
    """执行指定的 MCP 工具"""
    return await mcp_manager.execute_tool(service_name, tool_name, input_data)

if __name__ == "__main__":
    asyncio.run(mcp_manager.register_services_from_file("./mcp.json"))
    mcp.run(transport="streamable-http")
```

### 示例 2: 链式调用

```python
async def demo():
    manager = MCPServiceManager()
    await manager.register_services_from_file("./mcp.json")
    
    # 1. 获取所有服务
    services = manager.get_all_services()
    print(f"可用服务: {[s['name'] for s in services]}")
    
    # 2. 获取第一个服务的工具
    service_name = services[0]['name']
    tools = manager.get_all_tools_by_service(service_name)
    print(f"{service_name} 的工具: {[t['name'] for t in tools]}")
    
    # 3. 获取第一个工具的详细信息
    tool_name = tools[0]['name']
    tool_info = manager.get_tool_info(service_name, tool_name)
    print(f"工具信息: {tool_info}")
    
    # 4. 执行工具（根据实际的 inputSchema 构造参数）
    # result = await manager.execute_tool(service_name, tool_name, {...})

asyncio.run(demo())
```

## 📚 API 文档

### MCPServiceManager

#### `__init__()`

创建 MCP 服务管理器实例。

#### `async register_service(service_name, mcp_url, headers=None, description=None)`

注册单个 MCP 服务。

**参数：**
- `service_name` (str) - 服务名称
- `mcp_url` (str) - MCP 服务 URL
- `headers` (dict, 可选) - HTTP 请求头
- `description` (str, 可选) - 服务描述

**异常：**
- `ValueError` - 服务名称已存在
- `ConnectionError` - 无法连接到 MCP 服务

#### `async register_services_from_file(config_path)`

从配置文件批量注册服务。

**参数：**
- `config_path` (str | Path) - 配置文件路径

**返回：**
- `Dict[str, bool]` - 服务名称到注册结果的映射

**异常：**
- `FileNotFoundError` - 配置文件不存在
- `json.JSONDecodeError` - 配置文件格式错误
- `ValueError` - 配置文件缺少必需字段

#### `get_all_services()`

获取所有已注册的服务信息。

**返回：**
- `List[Dict[str, str]]` - 服务列表，每个服务包含 name 和 description

#### `get_all_tools_by_service(service_name)`

获取指定服务的所有工具。

**参数：**
- `service_name` (str) - 服务名称

**返回：**
- `List[Dict[str, str]]` - 工具列表，每个工具包含 name 和 description

**异常：**
- `ValueError` - 服务不存在

#### `get_tool_info(service_name, tool_name)`

获取工具的详细信息。

**参数：**
- `service_name` (str) - 服务名称
- `tool_name` (str) - 工具名称

**返回：**
- `Dict[str, Any]` - 工具信息，包含 name、description 和 inputSchema

**异常：**
- `ValueError` - 服务或工具不存在

#### `async execute_tool(service_name, tool_name, input_data)`

执行指定的 MCP 工具。

**参数：**
- `service_name` (str) - 服务名称
- `tool_name` (str) - 工具名称
- `input_data` (dict) - 工具输入参数

**返回：**
- `str` - 工具执行结果（JSON 字符串或文本）

**异常：**
- `ValueError` - 服务、工具不存在或参数错误
- `RuntimeError` - 工具执行失败

#### `async close_all()`

关闭所有 MCP 客户端连接。

## 🔧 技术栈

- **Python 3.8+**
- **asyncio** - 异步 I/O
- **AgentScope** - Agent 框架集成
- **MCP (Model Context Protocol)** - 协议实现
- **Pydantic** - 数据验证
- **FastMCP** - MCP 服务器框架（示例使用）

## 📄 许可证

[在此添加许可证信息]

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

[在此添加联系方式]

---

**注意：** 本 SDK 目前仅支持 `streamable_http` 传输类型的 MCP 服务。
