# Deep Research Search MCP

一个支持多搜索引擎的深度检索工具，提供：

- OpenAI 兼容的 Chat Completions API（由 `server.py` 提供）
- 可视化 WebUI（由 `webui.py` 提供）
- 多轮规划 + 搜索 + 汇总回答的 Deep Research 工作流

## 功能概览

- 支持多种搜索引擎：
  - `volc_bot`（默认）
  - `tavily`
  - `you`
  - `ask_echo`（BytePlus AskEcho Search Agent）
- 支持流式输出推理过程与最终答案
- 支持通过请求 `metadata` 动态切换搜索引擎与搜索轮次参数
- 前端可查看每轮搜索关键词与引用资料

## 运行环境

- Python 3.10+
- Poetry（用于依赖管理）

## 快速开始

### 1) 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install poetry
poetry install
```

### 2) 配置环境变量

在项目根目录创建 `.env`（可参考下面模板）：

```env
# ===== server 侧 =====
REASONING_MODEL=deepseek-r1-250528
SEARCH_ENGINE=volc_bot

# 选择 volc_bot 时需要
SEARCH_BOT_ID={YOUR_SEARCH_BOT_ID}

# 选择 tavily 时需要
TAVILY_API_KEY={YOUR_TAVILY_API_KEY}

# 选择 you 时需要
YOU_API_KEY={YOUR_YOU_API_KEY}

# 选择 ask_echo 时需要
ASK_ECHO_API_KEY={YOUR_ASK_ECHO_API_KEY}
ASK_ECHO_AGENT_ID={YOUR_ASK_ECHO_AGENT_ID}
# 可选，留空使用默认地址
ASK_ECHO_BASE_URL=

# Ark 鉴权（server 与 webui 都会使用）
ARK_API_KEY={YOUR_ARK_API_KEY}

# ===== webui 侧 =====
# 连接本地 server 时，建议配置：
API_ADDR=http://localhost:7859/api/v3/bots
# 国外站填模型名（如 deepseek-r1-250528），国内站一般填 bot id
API_BOT_ID=deepseek-r1-250528
```

> 注意：`config.py` 中有默认占位值，建议始终通过 `.env` 显式覆盖，避免误用。

## 启动方式

### 方式 A：启动 API 服务（推荐先启动）

```bash
source .venv/bin/activate
poetry run python -m server
```

默认监听：

- 端口：`7859`
- 健康检查：`/v1/ping`
- Chat API 路径：`/api/v3/bots/chat/completions`

### 方式 B：启动 WebUI

```bash
source .venv/bin/activate
poetry run python -m webui
```

浏览器访问：`http://localhost:7860/`

## API 调用示例

可参考 `run_client.py`，它演示了如何使用 OpenAI SDK 连接本地服务并处理流式推理输出。

如果手动调用，请确保：

- `base_url` 指向你的 API 地址（如 `http://localhost:7859/api/v3/bots`）
- `model` 与服务侧可用模型一致
- 可通过 `extra_body.metadata.search_engine` 动态切换引擎（如 `tavily` / `you` / `ask_echo`）

## 可选参数（metadata）

在请求中可透传以下参数控制检索行为：

- `search_engine`: 搜索引擎类型
- `max_search_words`: 每轮最多生成多少个搜索关键词
- `max_planning_rounds`: 最大搜索规划轮数

## 项目结构

```text
.
├── server.py                # OpenAI 兼容 API 服务入口
├── webui.py                 # Gradio 可视化界面
├── deep_search.py           # 多轮规划/搜索/总结核心逻辑
├── config.py                # 环境变量与默认配置
├── run_client.py            # API 调用示例
└── search_engine/
    ├── volc_bot.py          # Volc Bot 搜索实现
    ├── tavily.py            # Tavily 搜索实现
    ├── you.py               # You.com 搜索实现
    └── ask_echo.py          # AskEcho 搜索实现
```

## 常见问题

- **WebUI 无法出结果**
  - 确认 `API_ADDR` 指向可访问的服务地址
  - 确认 `ARK_API_KEY`、`API_BOT_ID` 配置正确
- **切换搜索引擎后报错**
  - 检查对应引擎所需的 API Key / Bot ID 是否已配置
- **本地服务已启动但请求失败**
  - 检查端口是否为 `7859`
  - 检查调用路径是否使用 `/api/v3/bots/chat/completions`