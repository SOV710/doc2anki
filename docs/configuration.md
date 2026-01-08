# Configuration Guide

## Configuration File Location

doc2anki searches for configuration files in the following order:

1. **CLI argument** - `--config /path/to/config.toml`
2. **Current directory** - `./config/ai_providers.toml`
3. **User config directory** - `~/.config/doc2anki/ai_providers.toml`

For first-time setup, place your configuration in the user directory for global access:

```sh
mkdir -p ~/.config/doc2anki
cp config/ai_providers.example.toml ~/.config/doc2anki/ai_providers.toml
```

## Configuration File Format

```toml
[provider_name]
enable = true                              # Whether to enable this provider
auth_type = "env"                          # Authentication method
api_key = "OPENAI_API_KEY"                 # API key or variable name
default_base_url = "https://api.openai.com/v1"
default_model = "gpt-4"
```

## Authentication Methods

### direct - Direct Configuration

API key is stored directly in the configuration file:

```toml
[local_llm]
enable = true
auth_type = "direct"
base_url = "http://localhost:11434/v1"
model = "qwen2.5:14b"
api_key = "ollama"
```

**Note:** Ensure proper file permissions to prevent key exposure.

### env - Environment Variable

Read API key from an environment variable:

```toml
[openai]
enable = true
auth_type = "env"
api_key = "OPENAI_API_KEY"           # Environment variable name
base_url = "OPENAI_BASE_URL"         # Optional: env var for base URL
model = "OPENAI_MODEL"               # Optional: env var for model
default_base_url = "https://api.openai.com/v1"  # Fallback value
default_model = "gpt-4o"                        # Fallback value
```

Set the environment variable before use:

```sh
export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxx"
```

### dotenv - .env File

Load credentials from a `.env` file:

```toml
[deepseek]
enable = true
auth_type = "dotenv"
dotenv_path = "/home/user/.env"      # Path to .env file (required)
api_key = "DEEPSEEK_API_KEY"         # Key name in .env file
base_url = "DEEPSEEK_BASE_URL"       # Optional: key name for base URL
model = "DEEPSEEK_MODEL"             # Optional: key name for model
default_base_url = "https://api.deepseek.com"
default_model = "deepseek-chat"
```

Example `.env` file content:

```
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
```

## Configuration Field Reference

### Required Fields

| Field | Description |
|-------|-------------|
| `enable` | Whether to enable this provider (`true`/`false`) |
| `auth_type` | Authentication method: `direct`, `env`, or `dotenv` |
| `api_key` | API key value or variable name (depends on auth_type) |

### Optional Fields

| Field | Description |
|-------|-------------|
| `base_url` | API endpoint URL (or env var name for `env`/`dotenv`) |
| `model` | Model name (or env var name for `env`/`dotenv`) |
| `default_base_url` | Fallback base URL for `env`/`dotenv` modes |
| `default_model` | Fallback model name for `env`/`dotenv` modes |
| `dotenv_path` | Path to `.env` file (required for `dotenv` auth) |

## Provider Configuration Examples

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
auth_type = "env"
api_key = "DEEPSEEK_API_KEY"
default_base_url = "https://api.deepseek.com"
default_model = "deepseek-chat"
```

### Alibaba Cloud Bailian (Qwen)

```toml
[qwen]
enable = true
auth_type = "env"
api_key = "DASHSCOPE_API_KEY"
default_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
default_model = "qwen-plus"
```

### Zhipu AI (GLM)

```toml
[zhipu]
enable = true
auth_type = "env"
api_key = "ZHIPU_API_KEY"
default_base_url = "https://open.bigmodel.cn/api/paas/v4"
default_model = "glm-4-flash"
```

### Moonshot AI

```toml
[moonshot]
enable = true
auth_type = "env"
api_key = "MOONSHOT_API_KEY"
default_base_url = "https://api.moonshot.cn/v1"
default_model = "moonshot-v1-auto"
```

### Local Ollama

```toml
[ollama]
enable = true
auth_type = "direct"
api_key = "ollama"              # Ollama doesn't require a real key
base_url = "http://localhost:11434/v1"
model = "qwen2.5:14b"
```

### OpenRouter

```toml
[openrouter]
enable = true
auth_type = "env"
api_key = "OPENROUTER_API_KEY"
default_base_url = "https://openrouter.ai/api/v1"
default_model = "anthropic/claude-3.5-sonnet"
```

### Together AI

```toml
[together]
enable = true
auth_type = "env"
api_key = "TOGETHER_API_KEY"
default_base_url = "https://api.together.xyz/v1"
default_model = "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
```

## Validating Configuration

Check all enabled providers:

```sh
doc2anki validate
```

Check a specific provider:

```sh
doc2anki validate -p openai
```

List all providers (including disabled):

```sh
doc2anki list --all
```

## Multiple Provider Setup

You can configure multiple providers and switch between them:

```toml
[openai]
enable = true
auth_type = "env"
api_key = "OPENAI_API_KEY"
default_base_url = "https://api.openai.com/v1"
default_model = "gpt-4o"

[deepseek]
enable = true
auth_type = "env"
api_key = "DEEPSEEK_API_KEY"
default_base_url = "https://api.deepseek.com"
default_model = "deepseek-chat"

[ollama]
enable = true
auth_type = "direct"
api_key = "ollama"
base_url = "http://localhost:11434/v1"
model = "qwen2.5:14b"
```

Use the `-p` flag to select a provider:

```sh
doc2anki generate notes.md -p openai
doc2anki generate notes.md -p deepseek
doc2anki generate notes.md -p ollama
```

## Security Best Practices

1. **Don't commit keys to version control** - `ai_providers.toml` is already in `.gitignore`
2. **Use environment variables or dotenv** - Recommended for production environments
3. **Restrict file permissions** - `chmod 600 ~/.config/doc2anki/ai_providers.toml`
4. **Rotate keys regularly** - Follow each provider's security best practices
5. **Use different configs for different projects** - Pass `--config` to isolate credentials

## Troubleshooting

### Provider not found

```
Error: Provider 'xxx' not found in configuration
```

Check that:
1. The provider section exists in your config file
2. `enable = true` is set
3. The config file path is correct

### Authentication failed

```
Error: Failed to authenticate with provider
```

Verify:
1. API key is correct
2. For `env` auth: environment variable is set
3. For `dotenv` auth: `.env` file path and key name are correct

### Connection refused

```
Error: Connection refused
```

For local providers (Ollama), ensure:
1. The service is running
2. The port is correct
3. No firewall blocking the connection
