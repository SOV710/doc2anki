# 配置指南

## 配置文件位置

doc2anki 按以下顺序查找配置文件：

1. **命令行指定** - `--config /path/to/config.toml`
2. **当前目录** - `./config/ai_providers.toml`
3. **用户配置目录** - `~/.config/doc2anki/ai_providers.toml`

首次使用建议将配置放在用户目录，全局可用：

```sh
mkdir -p ~/.config/doc2anki
cp config/ai_providers.example.toml ~/.config/doc2anki/ai_providers.toml
```

## 配置文件格式

```toml
[provider_name]
enable = true                              # 是否启用
auth_type = "env"                          # 认证方式
api_key = "OPENAI_API_KEY"                 # API 密钥或变量名
default_base_url = "https://api.openai.com/v1"
default_model = "gpt-4"
```

## 认证方式

### direct - 直接配置

API 密钥直接写在配置文件中：

```toml
[local_llm]
enable = true
auth_type = "direct"
api_key = "sk-xxxxxxxxxxxxxxxx"
default_base_url = "http://localhost:11434/v1"
default_model = "qwen2.5:14b"
```

**注意:** 确保配置文件权限正确，避免密钥泄露。

### env - 环境变量

从环境变量读取 API 密钥：

```toml
[openai]
enable = true
auth_type = "env"
api_key = "OPENAI_API_KEY"    # 环境变量名
default_base_url = "https://api.openai.com/v1"
default_model = "gpt-4o"
```

使用前设置环境变量：

```sh
export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxx"
```

### dotenv - .env 文件

从项目根目录的 `.env` 文件加载：

```toml
[deepseek]
enable = true
auth_type = "dotenv"
api_key = "DEEPSEEK_API_KEY"  # .env 文件中的键名
default_base_url = "https://api.deepseek.com/v1"
default_model = "deepseek-chat"
```

`.env` 文件内容：

```
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
```

## 常用提供商配置示例

### OpenAI

```toml
[openai]
enable = true
auth_type = "env"
api_key = "OPENAI_API_KEY"
default_base_url = "https://api.openai.com/v1"
default_model = "gpt-4o"
```

### DeepSeek

```toml
[deepseek]
enable = true
auth_type = "dotenv"
api_key = "DEEPSEEK_API_KEY"
default_base_url = "https://api.deepseek.com/v1"
default_model = "deepseek-chat"
```

### 阿里云百炼 (Qwen)

```toml
[qwen]
enable = true
auth_type = "env"
api_key = "DASHSCOPE_API_KEY"
default_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
default_model = "qwen-plus"
```

### 智谱 AI (GLM)

```toml
[zhipu]
enable = true
auth_type = "env"
api_key = "ZHIPU_API_KEY"
default_base_url = "https://open.bigmodel.cn/api/paas/v4"
default_model = "glm-4-flash"
```

### 月之暗面 (Moonshot)

```toml
[moonshot]
enable = true
auth_type = "env"
api_key = "MOONSHOT_API_KEY"
default_base_url = "https://api.moonshot.cn/v1"
default_model = "moonshot-v1-auto"
```

### 本地 Ollama

```toml
[ollama]
enable = true
auth_type = "direct"
api_key = "ollama"   # Ollama 不需要真实密钥
default_base_url = "http://localhost:11434/v1"
default_model = "qwen2.5:14b"
```

## 验证配置

检查所有启用的提供商：

```sh
doc2anki validate
```

检查特定提供商：

```sh
doc2anki validate -p openai
```

查看所有提供商（包括禁用的）：

```sh
doc2anki list --all
```

## 配置字段说明

| 字段 | 必需 | 说明 |
|-----|------|------|
| `enable` | Yes | 是否启用此提供商 |
| `auth_type` | Yes | 认证方式: `direct`, `env`, `dotenv` |
| `api_key` | Yes | API 密钥或变量名（取决于 auth_type） |
| `default_base_url` | Yes | API 端点 URL |
| `default_model` | Yes | 默认使用的模型名称 |

## 安全建议

1. **不要将密钥提交到版本控制** - `ai_providers.toml` 已在 `.gitignore` 中
2. **使用环境变量或 dotenv** - 生产环境推荐使用 `env` 或 `dotenv` 类型
3. **限制文件权限** - `chmod 600 ~/.config/doc2anki/ai_providers.toml`
4. **定期轮换密钥** - 遵循各提供商的安全最佳实践
