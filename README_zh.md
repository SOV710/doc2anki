# doc2anki

使用大语言模型将知识库文档转换为 Anki 学习卡片。

## 概述

doc2anki 是一个命令行工具，可将 Markdown 和 Org-mode 文档转换为 Anki 兼容的卡片包（`.apkg`）。它通过 OpenAI 兼容的 API 调用大语言模型，智能提取知识点并生成基础问答卡片和填空卡片。

### 主要特性

- **智能文档解析**：基于 tree-sitter 的完整 AST 支持，解析 Markdown 和 Org-mode
- **智能分块**：自动检测最优标题级别进行文档分割
- **上下文感知**：保留标题层级和文档元数据，提升卡片质量
- **交互式分类**：精细控制哪些章节生成卡片
- **灵活输出**：根据文件路径自动生成卡组层级和标签

## 环境要求

- Python 3.12 或更高版本
- 支持 OpenAI 兼容 API 的 LLM 服务

## 安装

### 全局安装（推荐）

```sh
# 使用 pipx
pipx install doc2anki

# 或使用 uv
uv tool install doc2anki
```

### 开发环境

```sh
git clone https://github.com/SOV710/doc2anki
cd doc2anki
uv sync
```

## 快速开始

1. **创建配置文件** `~/.config/doc2anki/ai_providers.toml`：

```toml
[openai]
enable = true
auth_type = "env"
api_key = "OPENAI_API_KEY"
default_base_url = "https://api.openai.com/v1"
default_model = "gpt-4o"
```

2. **设置 API 密钥**：

```sh
export OPENAI_API_KEY="sk-..."
```

3. **生成卡片**：

```sh
doc2anki generate notes.md -p openai -o flashcards.apkg
```

## 配置

doc2anki 按以下顺序查找配置文件：

1. 通过 `--config` 指定的路径
2. `./config/ai_providers.toml`
3. `~/.config/doc2anki/ai_providers.toml`

### 认证方式

| 认证类型 | 描述 | `api_key` 字段含义 |
|---------|------|-------------------|
| `direct` | 直接写入配置文件 | API 密钥本身 |
| `env` | 从环境变量读取 | 环境变量名 |
| `dotenv` | 从 `.env` 文件加载 | `.env` 文件中的键名 |

### 示例：环境变量认证

```toml
[deepseek]
enable = true
auth_type = "env"
api_key = "DEEPSEEK_API_KEY"
default_base_url = "https://api.deepseek.com"
default_model = "deepseek-chat"
```

### 示例：直接认证（本地 LLM）

```toml
[ollama]
enable = true
auth_type = "direct"
api_key = "ollama"
default_base_url = "http://localhost:11434/v1"
default_model = "qwen2.5:14b"
```

详细配置说明请参阅 [docs/configuration.md](docs/configuration.md)。

## 使用方法

### 列出可用提供商

```sh
doc2anki list
doc2anki list --all  # 包含已禁用的提供商
```

### 验证配置

```sh
doc2anki validate
doc2anki validate -p openai
```

### 生成卡片

```sh
# 单个文件
doc2anki generate input.md -p openai -o output.apkg

# 整个目录（递归）
doc2anki generate docs/ -p openai -o knowledge.apkg
```

### 命令行选项

**基本选项：**

| 选项 | 默认值 | 描述 |
|-----|-------|------|
| `-o, --output` | `outputs/output.apkg` | 输出文件路径 |
| `-p, --provider` | （必需） | AI 提供商名称 |
| `-c, --config` | （自动检测） | 配置文件路径 |
| `--prompt-template` | （内置） | 自定义 Jinja2 提示词模板 |
| `--dry-run` | false | 仅解析和分块，跳过 LLM 调用 |
| `-I, --interactive` | false | 交互式分类每个章节 |
| `--verbose` | false | 显示详细输出 |

**分块选项：**

| 选项 | 默认值 | 描述 |
|-----|-------|------|
| `--max-tokens` | 3000 | 每个块的最大 token 数 |
| `--max-retries` | 3 | LLM API 重试次数 |
| `--include-parent-chain` | true | 在提示词中包含标题层级 |

**卡片组织：**

| 选项 | 默认值 | 描述 |
|-----|-------|------|
| `--deck-depth` | 2 | 从文件路径生成卡组层级的深度 |
| `--extra-tags` | （无） | 额外标签（逗号分隔） |

### 交互模式

使用 `-I` 或 `--interactive` 进行精细控制：

```sh
doc2anki generate notes.md -p openai --interactive
```

交互模式允许你将每个章节分类为：

| 类型 | 生成卡片 | 加入上下文 | 用途 |
|------|---------|-----------|------|
| **Full** | 是 | 是 | 基础概念、定义 |
| **Card-only** | 是 | 否 | 独立知识点（默认） |
| **Context-only** | 否 | 是 | 背景信息、前置知识 |
| **Skip** | 否 | 否 | 无关内容 |

### 自动分块

未指定分块级别时，doc2anki 会自动分析并选择最优标题级别：

- 产生的块数（至少 2 个）
- 平均块大小（目标：500-2500 tokens）
- 大小分布均匀度（标准差 < 平均值的 50%）

## 文档格式

### Markdown

doc2anki 解析 Markdown 文档，支持：
- YAML frontmatter 元数据
- ATX 和 Setext 标题样式
- 代码块、列表、表格和引用

### Org-mode

doc2anki 支持 Org-mode，包括：
- 文件级关键字（`#+TITLE`、`#+AUTHOR`、`#+FILETAGS`）
- 属性抽屉（Property drawers）
- 所有标准 Org 标题级别

### 文件路径到卡组映射

文件路径自动转换为 Anki 卡组层级和标签：

```
computing/network/tcp_ip.md
├── 卡组：computing::network（deck_depth=2 时）
└── 标签：computing, network, tcp_ip
```

## 项目结构

```
src/doc2anki/
├── cli.py              # CLI 入口（基于 Typer）
├── config/             # 配置加载和验证
├── parser/             # 文档解析（Markdown、Org-mode）
│   ├── tree.py         # 不可变 AST 数据结构
│   ├── markdown.py     # tree-sitter Markdown 解析器
│   ├── orgmode.py      # 基于 orgparse 的 Org 解析器
│   └── chunker.py      # Token 感知的文档分块
├── pipeline/           # 处理管道
│   ├── classifier.py   # 块类型分类
│   ├── context.py      # 上下文管理
│   ├── processor.py    # 主管道编排
│   └── interactive.py  # 交互式分类会话
├── llm/                # LLM 集成
│   ├── client.py       # OpenAI 兼容 API 客户端
│   ├── prompt.py       # Jinja2 模板渲染
│   └── extractor.py    # JSON 响应提取
├── models/             # Pydantic 数据模型
│   └── cards.py        # BasicCard、ClozeCard 定义
├── output/             # 输出生成
│   └── apkg.py         # 基于 genanki 的 APKG 创建
└── templates/          # 提示词模板
    └── generate_cards.j2
```

## 路线图

- **异步支持**：添加 threading/asyncio 支持并发 LLM 调用
- **样式解耦**：LLM 返回 Markdown IR，doc2anki 转换为带样式的 HTML 模板
- **内置主题**：开箱即用的多种卡片样式模板
- **扩展 API 支持**：原生支持 Anthropic 和 Google API
- **交互式 TUI**：使用 Textual 替换现有的 Rich 实现，打造精美的终端界面
- **优化非交互工作流**：使用 LLM 调用总结上下文管道，使 doc2anki 更加开箱即用

## 文档

- [架构概述](docs/architecture.md)
- [CLI 参考](docs/cli-reference.md)
- [配置指南](docs/configuration.md)

## 许可证

MIT License
