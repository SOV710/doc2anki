# CLI 参考

## 安装

### 全局安装

```sh
# 使用 pipx (推荐)
pipx install doc2anki

# 或使用 uv
uv tool install doc2anki
```

### 开发模式

```sh
git clone https://github.com/your-repo/doc2anki
cd doc2anki
uv sync
uv run doc2anki --help
```

## 命令概览

```
doc2anki [OPTIONS] COMMAND [ARGS]

Commands:
  list      列出可用的 AI 提供商
  validate  验证配置文件
  generate  从文档生成 Anki 卡片
```

---

## doc2anki list

列出配置文件中的 AI 提供商。

### 语法

```sh
doc2anki list [OPTIONS]
```

### 选项

| 选项 | 说明 |
|-----|------|
| `-c, --config PATH` | 配置文件路径 |
| `--all` | 显示所有提供商（包括禁用的） |

### 示例

```sh
# 列出启用的提供商
doc2anki list

# 列出所有提供商
doc2anki list --all

# 使用指定配置文件
doc2anki list -c /path/to/config.toml
```

---

## doc2anki validate

验证配置文件的正确性。

### 语法

```sh
doc2anki validate [OPTIONS]
```

### 选项

| 选项 | 说明 |
|-----|------|
| `-c, --config PATH` | 配置文件路径 |
| `-p, --provider NAME` | 验证特定提供商 |

### 示例

```sh
# 验证所有启用的提供商
doc2anki validate

# 验证特定提供商
doc2anki validate -p openai

# 使用指定配置文件
doc2anki validate -c ~/.config/doc2anki/ai_providers.toml
```

---

## doc2anki generate

从文档生成 Anki 卡片。

### 语法

```sh
doc2anki generate INPUT_PATH [OPTIONS]
```

### 参数

| 参数 | 说明 |
|-----|------|
| `INPUT_PATH` | 输入文件或目录路径 |

### 基本选项

| 选项 | 默认值 | 说明 |
|-----|-------|------|
| `-o, --output PATH` | `outputs/output.apkg` | 输出 .apkg 文件路径 |
| `-p, --provider NAME` | (必需) | AI 提供商名称 |
| `-c, --config PATH` | (自动查找) | 配置文件路径 |
| `--prompt-template PATH` | (内置) | 自定义提示词模板路径 |
| `--dry-run` | false | 仅解析和分块，不调用 LLM |
| `--verbose` | false | 显示详细输出 |

### 分块控制选项

| 选项 | 默认值 | 说明 |
|-----|-------|------|
| `--chunk-level N` | 自动 | 按指定标题级别分块 (1-6) |
| `--max-tokens N` | 3000 | 每个块的最大 token 数量 |
| `--include-parent-chain` | true | 在提示词中包含标题层级路径 |
| `--no-parent-chain` | - | 禁用标题层级路径 |
| `--max-retries N` | 3 | LLM 调用最大重试次数 |

### 卡片组织选项

| 选项 | 默认值 | 说明 |
|-----|-------|------|
| `--deck-depth N` | 2 | 从文件路径生成卡组层级的深度 |
| `--extra-tags TAGS` | (无) | 额外标签，逗号分隔 |

### 示例

**基本用法:**

```sh
# 处理单个文件
doc2anki generate notes.md -p deepseek

# 处理目录
doc2anki generate knowledge/ -p openai -o my_cards.apkg
```

**分块控制:**

```sh
# 按二级标题分块
doc2anki generate notes.md -p deepseek --chunk-level 2

# 按三级标题分块，更细粒度
doc2anki generate notes.md -p deepseek --chunk-level 3

# 禁用标题层级上下文
doc2anki generate notes.md -p deepseek --no-parent-chain
```

**调试和测试:**

```sh
# 干跑模式 - 仅解析，不调用 LLM
doc2anki generate notes.md -p deepseek --dry-run

# 详细输出
doc2anki generate notes.md -p deepseek --verbose
```

**卡片组织:**

```sh
# 设置卡组层级深度为 3
doc2anki generate knowledge/ -p openai --deck-depth 3

# 添加额外标签
doc2anki generate notes.md -p deepseek --extra-tags "study,2024"
```

---

## 自动分块级别检测

当不指定 `--chunk-level` 时，doc2anki 自动选择最佳分块级别：

1. 遍历标题级别 1-6
2. 计算每个级别的平均块大小和方差
3. 选择满足以下条件的级别：
   - 至少产生 2 个块
   - 平均块大小在 500-2400 tokens
   - 块大小分布均匀（标准差 < 平均值的 50%）

使用 `--verbose` 查看选择的级别：

```sh
doc2anki generate notes.md -p deepseek --dry-run --verbose
```

---

## 标题层级上下文

默认启用 `--include-parent-chain`，每个块的提示词会包含其在文档中的位置：

```markdown
## 内容位置
当前内容在文档中的位置：网络基础 > TCP/IP > 三次握手
```

这帮助 LLM 理解当前内容的上下文，生成更准确的卡片。

若文档结构扁平或标题不具有层级含义，可禁用：

```sh
doc2anki generate notes.md -p deepseek --no-parent-chain
```

---

## 退出码

| 退出码 | 含义 |
|-------|------|
| 0 | 成功 |
| 1 | 错误（配置、解析、LLM 调用失败等） |

---

## 环境变量

| 变量 | 说明 |
|-----|------|
| `XDG_CONFIG_HOME` | 用户配置目录（默认 `~/.config`） |
| 各提供商 API 密钥变量 | 如 `OPENAI_API_KEY`, `DEEPSEEK_API_KEY` 等 |

