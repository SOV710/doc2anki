# doc2anki

## 概述

doc2anki 将知识库文档转换为 Anki 学习卡片。

通过大语言模型从 Markdown 或 Org-mode 文件中提取知识点，生成符合间隔重复学习规律的记忆卡片。

## 环境要求

- Python 3.12 或更高版本
- 支持 OpenAI API 格式的语言模型服务

## 安装

### 全局安装 (推荐)

使用 pipx 或 uv 全局安装后，可在任意位置运行：

```sh
# 使用 pipx
pipx install doc2anki

# 或使用 uv
uv tool install doc2anki
```

### 开发环境

```sh
git clone https://github.com/your-repo/doc2anki
cd doc2anki
uv sync
```

## 配置

### 配置文件位置

doc2anki 按以下顺序查找配置文件：

1. 命令行指定的路径 (`--config`)
2. 当前目录: `./config/ai_providers.toml`
3. 用户配置目录: `~/.config/doc2anki/ai_providers.toml`

### 配置格式

```toml
[provider_name]
enable = true
auth_type = "env"
api_key = "YOUR_API_KEY_ENV_VAR"
default_base_url = "https://api.example.com/v1"
default_model = "model-name"
```

支持三种认证方式:

| 认证类型 | api_key 含义 | 示例 |
|---------|-------------|------|
| `direct` | API 密钥本身 | `api_key = "sk-xxx..."` |
| `env` | 环境变量名 | `api_key = "OPENAI_API_KEY"` |
| `dotenv` | .env 文件中的键名 | `api_key = "API_KEY"` |

## 使用

### 查看可用的模型提供商

```sh
doc2anki list
doc2anki list --all  # 包含已禁用的提供商
```

### 验证配置

```sh
doc2anki validate
doc2anki validate -p provider_name
```

### 生成卡片

```sh
doc2anki generate input.md -p provider_name
```

处理整个目录:

```sh
doc2anki generate docs/ -p provider_name -o knowledge.apkg
```

### 命令行选项

**基本选项:**

| 选项 | 默认值 | 说明 |
|-----|-------|------|
| `-o, --output` | `outputs/output.apkg` | 输出文件路径 |
| `-p, --provider` | (必需) | AI 提供商名称 |
| `-c, --config` | (自动查找) | 配置文件路径 |
| `--dry-run` | false | 仅解析分块，不调用 LLM |
| `--verbose` | false | 显示详细输出 |

**分块控制:**

| 选项 | 默认值 | 说明 |
|-----|-------|------|
| `--chunk-level` | 自动检测 | 按指定标题级别分块 (1-6) |
| `--max-tokens` | 3000 | 每个块的最大 token 数量 |
| `--include-parent-chain` | true | 在提示词中包含标题层级路径 |

**卡片组织:**

| 选项 | 默认值 | 说明 |
|-----|-------|------|
| `--deck-depth` | 2 | 从文件路径生成卡组层级的深度 |
| `--extra-tags` | (无) | 额外标签，逗号分隔 |

## 分块策略

### 自动检测

默认情况下，doc2anki 自动检测最佳分块级别：

1. 遍历各标题级别 (1-6)
2. 计算每个级别的平均块大小和方差
3. 选择满足以下条件的级别：
   - 至少产生 2 个块
   - 平均块大小在 500-2400 tokens 之间
   - 块大小分布均匀（标准差 < 平均值的 50%）

### 手动指定

对于特殊文档结构，可手动指定分块级别：

```sh
# 按二级标题分块
doc2anki generate input.md -p provider --chunk-level 2

# 按三级标题分块，更细粒度
doc2anki generate input.md -p provider --chunk-level 3
```

### 标题层级上下文

启用 `--include-parent-chain` (默认) 时，每个块会包含其在文档中的位置：

```
## 内容位置
当前内容在文档中的位置：网络基础 > TCP/IP > 三次握手
```

这帮助 LLM 理解当前内容的上下文，生成更准确的卡片。

## 文档格式

### 全局上下文块

在文档开头定义领域术语，供语言模型生成卡片时参考。

Markdown 格式:

````markdown
```context
- TCP: "传输控制协议"
- HTTP: "超文本传输协议"
```
````

Org-mode 格式:

```org
#+BEGIN_CONTEXT
- TCP: "传输控制协议"
- HTTP: "超文本传输协议"
#+END_CONTEXT
```

### 文件路径与卡片组织

文件路径自动转换为 Anki 卡片组层级和标签。

例如: `computing/network/tcp_ip.md`
- 卡片组: `computing::network` (深度为 2)
- 标签: `computing`, `network`, `tcp_ip`

## 项目结构

```
src/doc2anki/
├── cli.py              # 命令行接口
├── config/             # 配置加载
├── parser/             # 文档解析
│   ├── tree.py         # AST 数据结构
│   ├── markdown.py     # Markdown 解析
│   └── orgmode.py      # Org-mode 解析
├── pipeline/           # 处理管道
│   ├── classifier.py   # 块类型分类
│   ├── context.py      # 上下文管理
│   └── processor.py    # 处理流程
├── llm/                # LLM 调用
└── output/             # APKG 生成
```

## 许可证

MIT License
