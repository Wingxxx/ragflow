# RagFlow 对接 DeerFlow 技术整合指南

> **WING** 2026-04-16
>
> 本文档为 AI 开发者提供 RagFlow 对接 DeerFlow 的完整技术参考，涵盖所有可用接口、集成方式和配置示例。

***

## 一、概述

### 1.1 文档目的

本文档旨在帮助 DeerFlow 开发者快速集成 RagFlow 知识检索能力。RagFlow 已提供完善的对外接口，包括 MCP Server、HTTP REST API、Python SDK 和 CLI，DeerFlow 可直接复用。

### 1.2 RagFlow 角色定位

RagFlow 在本架构中作为**企业知识引擎**，负责：

* 文档解析入库（DeepDoc）

* 向量索引检索（Elasticsearch/Infinity）

* RAG 对话生成

* 知识库管理 Web UI

### 1.3 核心接口一览

| 接口类型              | 地址                                    | 协议                    | 支持模式   |
| ----------------- | ------------------------------------- | --------------------- | ------ |
| **HTTP REST API** | `:9380/api/v1/*`                      | HTTP/JSON             | 全部功能   |
| **OpenAI 兼容 API** | `:9380/api/v1/chats_openai/<chat_id>` | OpenAI                | 对话     |
| **Python SDK**    | `pip install ragflow-sdk`             | -                     | 全部功能   |
| **MCP Server**    | `:9382`                               | SSE / Streamable-HTTP | **检索** |
| **CLI 管理工具**      | `pip install ragflow-cli`             | TCP                   | 管理     |

***

## 二、MCP 模式集成（推荐）

### 2.1 方案说明

RagFlow 已自带 MCP Server，DeerFlow 可通过 `extensions_config.json` 直接配置使用，**零代码开发**。

**架构图：**

```
DeerFlow (MCP Client)
        │
        │ SSE / Streamable-HTTP
        ▼
RagFlow MCP Server (:9382)
        │
        │ HTTP + Bearer Token
        ▼
RagFlow API Server (:9380)
```

### 2.2 RagFlow MCP Server 启动

#### 方式一：源码启动

```bash
cd ragflow

# Self-host 模式（单租户，推荐）
uv run mcp/server/server.py \
  --host=127.0.0.1 \
  --port=9382 \
  --base-url=http://127.0.0.1:9380 \
  --mode=self-host \
  --api-key=ragflow-xxxxx

# Host 模式（多租户，客户端需提供 Token）
uv run mcp/server/server.py \
  --host=0.0.0.0 \
  --port=9382 \
  --base-url=http://127.0.0.1:9380 \
  --mode=host
```

#### 方式二：Docker 启动

在 `docker/docker-compose.yml` 中启用 MCP Server：

```yaml
services:
  ragflow:
    image: ${RAGFLOW_IMAGE}
    command:
      - --enable-mcpserver
      - --mcp-host=0.0.0.0
      - --mcp-port=9382
      - --mcp-base-url=http://127.0.0.1:9380
      - --mcp-script-path=/ragflow/mcp/server/server.py
      - --mcp-mode=self-host
      - --mcp-host-api-key=ragflow-xxxxx
```

### 2.3 DeerFlow 配置

编辑 `extensions_config.json`：

```json
{
  "mcpServers": {
    "ragflow": {
      "enabled": true,
      "type": "sse",
      "url": "http://ragflow-server:9382/sse",
      "headers": {
        "Authorization": "Bearer ragflow-xxxxx"
      }
    }
  }
}
```

### 2.4 MCP Tool 规格

| 属性            | 值                     |
| ------------- | --------------------- |
| **Tool Name** | `ragflow_retrieval`   |
| **传输协议**      | SSE / Streamable-HTTP |
| **认证方式**      | Bearer Token          |

**输入参数（inputSchema）：**

| 参数                         | 类型             | 必填 | 默认值   | 说明           |
| -------------------------- | -------------- | -- | ----- | ------------ |
| `question`                 | string         | ✅  | -     | 查询问题         |
| `dataset_ids`              | array\[string] | ❌  | 全部数据集 | 指定知识库 ID 列表  |
| `document_ids`             | array\[string] | ❌  | -     | 指定文档 ID 列表   |
| `page`                     | integer        | ❌  | 1     | 页码           |
| `page_size`                | integer        | ❌  | 10    | 每页结果数（最大100） |
| `similarity_threshold`     | number         | ❌  | 0.2   | 相似度阈值（0-1）   |
| `vector_similarity_weight` | number         | ❌  | 0.3   | 向量相似度权重（0-1） |
| `keyword`                  | boolean        | ❌  | false | 是否启用关键词匹配    |
| `top_k`                    | integer        | ❌  | 1024  | 参与排序的最大结果数   |
| `rerank_id`                | string         | ❌  | -     | 重排序模型 ID     |
| `force_refresh`            | boolean        | ❌  | false | 是否强制刷新元数据缓存  |

**返回格式：**

```json
{
  "chunks": [
    {
      "id": "chunk_id",
      "content": "文档内容...",
      "document_id": "doc_id",
      "document_name": "文档名称",
      "dataset_id": "dataset_id",
      "dataset_name": "知识库名称",
      "similarity": 0.75,
      "vector_similarity": 0.82,
      "term_similarity": 0.68,
      "positions": [[1, 2, 3]],
      "document_metadata": {
        "name": "文档名称",
        "type": "pdf",
        "size": 1024000,
        "chunk_count": 50
      }
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_chunks": 100,
    "total_pages": 10
  },
  "query_info": {
    "question": "查询内容",
    "similarity_threshold": 0.2,
    "vector_weight": 0.3,
    "keyword_search": false,
    "dataset_count": 3
  }
}
```

### 2.5 适用场景

✅ **MCP 模式适用：**

* 只需要检索功能

* 希望快速集成

* 需要标准 MCP 协议支持

❌ **MCP 模式不适用：**

* 需要管理知识库/文档（创建、删除、更新）

* 需要上传文档触发解析

* 需要对话功能

***

## 三、HTTP API 直调模式

### 3.1 方案说明

通过 DeerFlow Custom Tool 直接调用 RagFlow REST API，可访问完整功能。

### 3.2 认证方式

所有 API 请求需要携带 Bearer Token：

```bash
Authorization: Bearer <YOUR_API_KEY>
```

获取 API Key：RagFlow Web UI → 头像 → API

### 3.3 核心 API 详解

#### 3.3.1 检索 API（最常用）

**端点：** `POST /api/v1/datasets/{dataset_id}/retrieval`

**请求：**

```bash
curl -X POST "http://ragflow-server:9380/api/v1/datasets/{dataset_id}/retrieval" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ragflow-xxxxx" \
  -d '{
    "question": "如何安装软件？",
    "top_k": 10,
    "similarity_threshold": 0.2,
    "vector_similarity_weight": 0.3,
    "page": 1,
    "page_size": 10
  }'
```

**响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "chunks": [
      {
        "id": "chunk_id",
        "content": "安装步骤如下...",
        "document_id": "doc_id",
        "document_name": "安装指南.pdf",
        "dataset_id": "dataset_id",
        "similarity": 0.75,
        "vector_similarity": 0.82,
        "term_similarity": 0.68
      }
    ],
    "total": 50
  }
}
```

#### 3.3.2 知识库管理 API

| API                            | 方法      | 功能     |
| ------------------------------ | ------- | ------ |
| `POST /api/v1/datasets`        | 创建知识库   | <br /> |
| `GET /api/v1/datasets`         | 列出知识库   | <br /> |
| `GET /api/v1/datasets/{id}`    | 获取知识库详情 | <br /> |
| `PUT /api/v1/datasets/{id}`    | 更新知识库   | <br /> |
| `DELETE /api/v1/datasets/{id}` | 删除知识库   | <br /> |

**创建知识库：**

```bash
curl -X POST "http://ragflow-server:9380/api/v1/datasets" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ragflow-xxxxx" \
  -d '{
    "name": "my-knowledge-base",
    "description": "我的知识库",
    "embedding_model": "BAAI/bge-large-zh-v1.5@BAAI",
    "permission": "me",
    "chunk_method": "naive"
  }'
```

**列出知识库：**

```bash
curl -X GET "http://ragflow-server:9380/api/v1/datasets?page=1&page_size=30" \
  -H "Authorization: Bearer ragflow-xxxxx"
```

#### 3.3.3 文档管理 API

| API                                                   | 方法   | 功能     |
| ----------------------------------------------------- | ---- | ------ |
| `POST /api/v1/datasets/{id}/documents`                | 上传文档 | <br /> |
| `GET /api/v1/datasets/{id}/documents`                 | 列出文档 | <br /> |
| `DELETE /api/v1/datasets/{id}/documents/{doc_id}`     | 删除文档 | <br /> |
| `POST /api/v1/datasets/{id}/documents/{doc_id}/parse` | 解析文档 | <br /> |

**上传文档：**

```bash
curl -X POST "http://ragflow-server:9380/api/v1/datasets/{dataset_id}/documents" \
  -H "Authorization: Bearer ragflow-xxxxx" \
  -F "file=@/path/to/document.pdf"
```

#### 3.3.4 切片管理 API

| API                                | 方法     | 功能     |
| ---------------------------------- | ------ | ------ |
| `GET /api/v1/datasets/{id}/chunks` | 获取切片列表 | <br /> |
| `PUT /api/v1/chunks/{chunk_id}`    | 更新切片   | <br /> |
| `DELETE /api/v1/chunks/{chunk_id}` | 删除切片   | <br /> |

### 3.4 Custom Tool 实现示例

```python
# deer-flow/backend/packages/harness/deerflow/tools/builtins/ragflow_tool.py
"""
RagFlow 知识检索工具
"""
import os
import httpx
from typing import Optional

RAGFLOW_BASE_URL = os.getenv("RAGFLOW_BASE_URL", "http://ragflow-server:9380")
RAGFLOW_API_KEY = os.getenv("RAGFLOW_API_KEY", "")


async def ragflow_retrieve(
    query: str,
    dataset_id: Optional[str] = None,
    top_k: int = 10,
    similarity_threshold: float = 0.2,
    vector_similarity_weight: float = 0.3,
    page: int = 1,
    page_size: int = 10,
    keyword: bool = False,
) -> str:
    """
    查询 RagFlow 企业知识库。

    Args:
        query: 查询问题
        dataset_id: 知识库 ID，为空则搜索全部
        top_k: 参与排序的最大结果数
        similarity_threshold: 相似度阈值
        vector_similarity_weight: 向量相似度权重
        page: 页码
        page_size: 每页结果数
        keyword: 是否启用关键词匹配

    Returns:
        格式化检索结果字符串
    """
    payload = {
        "question": query,
        "top_k": top_k,
        "similarity_threshold": similarity_threshold,
        "vector_similarity_weight": vector_similarity_weight,
        "page": page,
        "page_size": page_size,
        "keyword": keyword,
    }

    if dataset_id:
        url = f"{RAGFLOW_BASE_URL}/api/v1/datasets/{dataset_id}/retrieval"
        payload["dataset_ids"] = [dataset_id]
    else:
        url = f"{RAGFLOW_BASE_URL}/api/v1/retrieval"

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {RAGFLOW_API_KEY}"}
        )

    result = resp.json()

    if result.get("code") != 0:
        return f"检索失败：{result.get('message', '未知错误')}"

    chunks = result.get("data", {}).get("chunks", [])
    total = result.get("data", {}).get("total", 0)

    if not chunks:
        return "未找到相关知识，请尝试其他关键词。"

    formatted = []
    for i, c in enumerate(chunks, 1):
        doc_name = c.get("document_name", "未知文档")
        similarity = c.get("similarity", 0)
        content = c.get("content", "")[:300]
        formatted.append(
            f"【结果 {i}】来源：{doc_name}（相似度：{similarity:.2f}）\n"
            f"{content}...\n"
        )

    return (
        f"找到 {total} 条相关结果，展示前 {len(chunks)} 条：\n\n"
        + "\n\n".join(formatted)
    )


async def ragflow_list_datasets() -> str:
    """
    列出所有知识库。

    Returns:
        知识库列表字符串
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{RAGFLOW_BASE_URL}/api/v1/datasets",
            headers={"Authorization": f"Bearer {RAGFLOW_API_KEY}"}
        )

    result = resp.json()

    if result.get("code") != 0:
        return f"查询失败：{result.get('message', '未知错误')}"

    datasets = result.get("data", [])

    if not datasets:
        return "当前无知识库。"

    lines = []
    for ds in datasets:
        ds_id = ds.get("id", "")
        ds_name = ds.get("name", "未命名")
        ds_desc = ds.get("description", "")
        ds_chunk_num = ds.get("chunk_num", 0)
        lines.append(f"- **{ds_name}**（ID: {ds_id[:8]}...）\n  描述：{ds_desc[:50]}...\n  切片数：{ds_chunk_num}")

    return "\n\n".join(lines)
```

***

## 四、Python SDK 模式

### 4.1 安装

```bash
pip install ragflow-sdk
```

### 4.2 基础用法

```python
from ragflow_sdk import RAGFlow

# 初始化
rag = RAGFlow(
    api_key="ragflow-xxxxx",
    base_url="http://ragflow-server:9380"
)

# 列出知识库
datasets = rag.list_datasets()
for ds in datasets:
    print(f"{ds.id}: {ds.name}")

# 获取指定知识库
dataset = rag.list_datasets(name="my-kb")[0]

# 上传文档
with open("document.pdf", "rb") as f:
    dataset.upload_documents([{
        "display_name": "document.pdf",
        "blob": f.read()
    }])

# 触发解析
docs = dataset.list_documents()
dataset.async_parse_documents([doc.id for doc in docs])

# 检索
chunks = rag.retrieve(
    question="如何安装？",
    dataset_ids=[dataset.id],
    top_k=10
)
for chunk in chunks:
    print(chunk.content)
```

***

## 五、环境变量配置

### 5.1 DeerFlow 环境变量

```bash
# RagFlow 连接配置
RAGFLOW_BASE_URL=http://ragflow-server:9380
RAGFLOW_API_KEY=ragflow-xxxxx

# RagFlow MCP Server 配置（若使用 MCP 模式）
RAGFLOW_MCP_HOST=ragflow-server
RAGFLOW_MCP_PORT=9382
RAGFLOW_MCP_TRANSPORT=sse  # 或 streamable-http
```

### 5.2 RagFlow MCP Server 环境变量

```bash
# MCP Server 启动配置
RAGFLOW_MCP_BASE_URL=http://127.0.0.1:9380
RAGFLOW_MCP_HOST=0.0.0.0
RAGFLOW_MCP_PORT=9382
RAGFLOW_MCP_LAUNCH_MODE=self-host  # 或 host
RAGFLOW_MCP_HOST_API_KEY=ragflow-xxxxx
RAGFLOW_MCP_TRANSPORT_SSE_ENABLED=true
RAGFLOW_MCP_TRANSPORT_STREAMABLE_ENABLED=true
RAGFLOW_MCP_JSON_RESPONSE=true
```

***

## 六、错误处理

### 6.1 API 错误码

| 错误码 | 说明      | 处理建议            |
| --- | ------- | --------------- |
| 400 | 请求参数错误  | 检查请求参数格式        |
| 401 | 未授权     | 检查 API Key 是否正确 |
| 403 | 禁止访问    | 检查权限设置          |
| 404 | 资源不存在   | 检查数据集/文档 ID     |
| 500 | 服务器内部错误 | 联系 RagFlow 管理员  |

### 6.2 MCP 模式错误

RagFlow MCP Server 错误通过 MCP 协议返回 `Error` 类型：

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Invalid params: dataset_ids is required"
  }
}
```

***

## 六、MCP API Key 操作说明

### 6.1 获取 RagFlow API Key

1. 打开 RagFlow Web UI（默认 `http://localhost:9388`）
2. 登录账号
3. 点击右上角头像 → **API Key**
4. 点击「Create API Key」生成新 Key
5. 复制生成的 Key（格式：`ragflow-xxxxxxxx`）

> **注意**：API Key 一旦关闭页面将无法再次查看，请妥善保存。

### 6.2 API Key 在 MCP 中的配置方式

RagFlow MCP Server 支持两种模式，认证方式不同：

#### Self-host 模式（默认，推荐）

MCP Server 与 RagFlow 服务器绑定，单一租户专用。

**Docker 配置（docker-compose.yml）：**

```yaml
services:
  ragflow:
    command:
      - --enable-mcpserver
      - --mcp-host=0.0.0.0
      - --mcp-port=9382
      - --mcp-base-url=http://127.0.0.1:9380
      - --mcp-script-path=/ragflow/mcp/server/server.py
      - --mcp-mode=self-host
      - --mcp-host-api-key=ragflow-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**DeerFlow 连接配置（extensions_config.json）：**

```json
{
  "mcpServers": {
    "ragflow": {
      "enabled": true,
      "type": "sse",
      "url": "http://ragflow-server:9382/sse"
    }
  }
}
```

> Self-host 模式下，DeerFlow 连接时**无需在 headers 中传 Authorization**，因为 MCP Server 启动时已配置好 API Key。

#### Host 模式（多租户）

每个客户端访问自己的数据集，需要在请求头中携带 API Key。

**Docker 配置：**

```yaml
services:
  ragflow:
    command:
      - --enable-mcpserver
      - --mcp-host=0.0.0.0
      - --mcp-port=9382
      - --mcp-base-url=http://127.0.0.1:9380
      - --mcp-script-path=/ragflow/mcp/server/server.py
      - --mcp-mode=host
      - --no-transport-streamable-http-enabled
```

**DeerFlow 连接配置：**

```json
{
  "mcpServers": {
    "ragflow": {
      "enabled": true,
      "type": "sse",
      "url": "http://ragflow-server:9382/sse",
      "headers": {
        "Authorization": "Bearer ragflow-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

### 6.3 验证 MCP 服务

#### 方法一：检查端口

```bash
# Windows
netstat -an | findstr "9382"

# Linux/Mac
netstat -an | grep 9382
```

确认端口处于 `LISTENING` 状态。

#### 方法二：检查日志

```bash
docker logs docker-ragflow-cpu-1 2>&1 | findstr "MCP"
```

应看到类似输出：

```
Starting MCP Server on 0.0.0.0:9382 with base URL http://127.0.0.1:9380...
MCP launch mode: self-host
MCP port: 9382
Streamable HTTP endpoint available at /mcp
Uvicorn running on http://0.0.0.0:9382
```

#### 方法三：测试端点

```bash
# 测试 /mcp 端点（应返回 JSON-RPC 错误，表示服务正常）
curl -s -X GET "http://localhost:9382/mcp"

# 返回示例：
# {"jsonrpc":"2.0","id":"server-error","error":{"code":-32600,"message":"Not Acceptable: Client must accept text/event-stream"}}
```

### 6.4 MCP 端点说明

| 端点 | 协议 | 说明 |
|------|------|------|
| `/sse` | SSE | 传统 SSE 传输（已废弃但仍支持） |
| `/mcp` | Streamable-HTTP | **推荐**，MCP 标准传输协议 |

### 6.5 常见问题

**Q: MCP Server 启动后端口 9382 无法访问？**

A: 检查 docker-compose.yml 中是否正确映射端口：
```yaml
ports:
  - "${SVR_MCP_PORT}:9382"  # 确保 .env 中 SVR_MCP_PORT=9382
```

**Q: 返回 406 Not Acceptable 错误？**

A: 这是正常响应，表示 MCP 服务正常运行，但请求未携带正确的 Accept 头。

**Q: Self-host 模式下 DeerFlow 仍报认证错误？**

A: 检查 `--mcp-host-api-key` 配置的 Key 是否与 RagFlow 账号的 API Key 一致。

***

## 七、部署检查清单

### 7.1 RagFlow 侧

* [ ] RagFlow 服务运行正常（:9380）

* [ ] API Key 已生成并记录

* [ ] 知识库已创建并上传文档

* [ ] 文档解析完成（chunk\_count > 0）

### 7.2 MCP 模式（若使用）

* [ ] RagFlow MCP Server 安装/运行正常

* [ ] MCP Server 端口（默认9382）可达

* [ ] `extensions_config.json` 已配置

* [ ] DeerFlow 重启加载配置

### 7.3 Custom Tool 模式（若使用）

* [ ] 环境变量 `RAGFLOW_BASE_URL` 已设置

* [ ] 环境变量 `RAGFLOW_API_KEY` 已设置

* [ ] RagFlow Tool 代码已部署

* [ ] Tool 已注册到 DeerFlow

***

## 八、代码修改记录

> 本节记录所有需要的代码修改，按优先级排列。

### 优先级 1：MCP 模式（无需代码修改）

```diff
# extensions_config.json
{
  "mcpServers": {
+   "ragflow": {
+     "enabled": true,
+     "type": "sse",
+     "url": "http://ragflow-server:9382/sse",
+     "headers": {
+       "Authorization": "Bearer ragflow-xxxxx"
+     }
+   }
  }
}
```

### 优先级 2：Custom Tool 模式（如需完整功能）

**新增文件：**

```
deer-flow/backend/packages/harness/deerflow/tools/builtins/ragflow_tool.py
```

**修改文件：**

| 文件                                                                   | 修改内容                                          |
| -------------------------------------------------------------------- | --------------------------------------------- |
| `deer-flow/backend/packages/harness/deerflow/tools/__init__.py`      | 导出 RagFlowTool                                |
| `deer-flow/backend/packages/harness/deerflow/tools/builtin_tools.py` | 注册 ragflow\_retrieve, ragflow\_list\_datasets |
| `deer-flow/.env`                                                     | 添加 RAGFLOW\_BASE\_URL, RAGFLOW\_API\_KEY      |

***

## 九、联系方式

* **RagFlow 官方文档：** <https://ragflow.io/docs/>

* **RagFlow GitHub：** <https://github.com/infiniflow/ragflow>

* **MCP 协议文档：** <https://modelcontextprotocol.io>

***

**WING**
**2026-04-16**
