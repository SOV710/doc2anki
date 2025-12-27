# doc2anki

## 概述

doc2anki 将知识库文档转换为 Anki 学习卡片。

通过大语言模型从 Markdown 或 Org-mode 文件中提取知识点，生成符合间隔重复学习规律的记忆卡片。

## 环境要求

- Python 3.12 或更高版本
- 支持 OpenAI API 格式的语言模型服务

## 安装

```sh
uv sync
```

## 配置

在项目根目录创建 `ai_providers.toml` 文件，配置语言模型提供商:

```toml
[provider_name]
enable = true
auth_type = "env"
api_key_env = "YOUR_API_KEY_ENV_VAR"
default_base_url = "https://api.example.com/v1"
default_model = "model-name"
```

支持三种认证方式:
- `direct`: 凭据直接写在配置文件中
- `env`: 从环境变量读取
- `dotenv`: 从 .env 文件加载

## 使用

### 查看可用的模型提供商

```sh
doc2anki list
```

### 验证配置

```sh
doc2anki validate
doc2anki validate -p provider_name
```

### 生成卡片

```sh
doc2anki generate input.md -p provider_name -o output.apkg
```

处理整个目录:

```sh
doc2anki generate docs/ -p provider_name -o knowledge.apkg
```

常用选项:
- `--max-tokens`: 每个文本块的最大 token 数量 (默认 3000)
- `--deck-depth`: 从文件路径生成卡片组层级的深度 (默认 2)
- `--extra-tags`: 添加额外标签，用逗号分隔
- `--dry-run`: 仅解析和分块，不调用语言模型
- `--verbose`: 显示详细输出

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

## 许可证

MIT License
