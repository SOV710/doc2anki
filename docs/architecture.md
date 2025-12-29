# 系统架构

## 数据流概览

```
输入文档 (.md/.org)
       │
       ▼
┌─────────────┐
│   Parser    │ 解析文档，提取全局上下文
└─────────────┘
       │
       ▼
┌─────────────┐
│ Tree Builder│ 构建文档 AST (HeadingNode 树)
└─────────────┘
       │
       ▼
┌─────────────┐
│  Pipeline   │ 分块、分类、上下文管理
└─────────────┘
       │
       ▼
┌─────────────┐
│  LLM Client │ 调用 AI 生成卡片
└─────────────┘
       │
       ▼
┌─────────────┐
│   Output    │ 生成 Anki .apkg 文件
└─────────────┘
```

## 模块职责

### Parser 模块 (`src/doc2anki/parser/`)

负责解析 Markdown 和 Org-mode 文档。

**核心组件:**

| 文件 | 职责 |
|-----|------|
| `base.py` | 定义 `ParseResult` 和 `BaseParser` 接口 |
| `markdown.py` | Markdown 解析，提取 ` ```context` 块 |
| `orgmode.py` | Org-mode 解析，提取 `#+BEGIN_CONTEXT` 块 |
| `tree.py` | AST 数据结构：`HeadingNode`, `DocumentTree` |
| `chunker.py` | Token 感知的分块逻辑 |

**AST 结构:**

```python
@dataclass
class HeadingNode:
    level: int              # 标题级别 (1-6)
    title: str              # 标题文本
    content: str            # 该标题下的内容（不含子节点）
    children: list[HeadingNode]

    @property
    def full_content(self) -> str:
        """包含所有子节点的完整内容"""

    @property
    def path(self) -> list[str]:
        """标题层级路径: ["父标题", "当前标题"]"""

@dataclass
class DocumentTree:
    children: list[HeadingNode]  # 顶级标题
    preamble: str                # 第一个标题前的内容

    def get_nodes_at_level(self, level: int) -> list[HeadingNode]:
        """获取指定级别的所有节点"""
```

### Pipeline 模块 (`src/doc2anki/pipeline/`)

处理分块、分类和上下文管理。

**核心组件:**

| 文件 | 职责 |
|-----|------|
| `classifier.py` | 定义 `ChunkType` 枚举和 `ClassifiedNode` |
| `context.py` | 定义 `ChunkWithContext` 数据结构 |
| `processor.py` | 处理流程和自动检测算法 |

**块类型分类 (2x2 矩阵):**

```
                │ 加入上下文 │ 不加入上下文
────────────────┼───────────┼──────────────
生成卡片        │ FULL      │ CARD_ONLY ← 默认
不生成卡片      │ CONTEXT_ONLY │ SKIP
```

| 类型 | 生成卡片 | 加入上下文 | 用途 |
|------|---------|-----------|------|
| `FULL` | Yes | Yes | 基础概念、定义、公理 |
| `CARD_ONLY` | Yes | No | 独立知识点 (v1 默认) |
| `CONTEXT_ONLY` | No | Yes | 背景铺垫、历史动机 |
| `SKIP` | No | No | 可跳过的内容 |

**自动检测算法:**

```python
def auto_detect_level(tree: DocumentTree, max_tokens: int) -> int:
    """
    纯本地启发式算法 - 零 API 成本

    策略:
    1. 遍历各标题级别 (1-6)
    2. 计算每个级别的节点数和平均 token 数
    3. 检查方差 - 如果过高，继续深入
    4. 选择满足条件的级别:
       - 至少 2 个块
       - 平均块大小在 500-2400 tokens
       - 分布均匀（标准差 < 平均值的 50%）
    """
```

### LLM 模块 (`src/doc2anki/llm/`)

处理与 AI 服务的交互。

**核心组件:**

| 文件 | 职责 |
|-----|------|
| `client.py` | OpenAI 兼容客户端，重试逻辑 |
| `prompt.py` | Jinja2 模板渲染 |
| `extractor.py` | 从响应中提取 JSON |

**模板加载:**

使用 `importlib.resources` 从包内加载模板，支持 pip 安装后使用：

```python
class PackageLoader(BaseLoader):
    """从 Python 包资源加载模板"""
    def get_source(self, environment, template):
        files = importlib.resources.files(self.package)
        source = (files / template).read_text(encoding="utf-8")
        return source, template, lambda: True
```

### Config 模块 (`src/doc2anki/config/`)

管理配置加载和验证。

**配置解析链:**

1. 命令行 `--config` 参数
2. `./config/ai_providers.toml`
3. `~/.config/doc2anki/ai_providers.toml`

**认证类型:**

| 类型 | `api_key` 含义 |
|------|---------------|
| `direct` | API 密钥本身 |
| `env` | 环境变量名 |
| `dotenv` | .env 文件中的键名 |

### Output 模块 (`src/doc2anki/output/`)

生成 Anki 包文件。

- 使用 `genanki` 库创建 .apkg 文件
- 支持基础卡片 (Q&A) 和填空卡片 (Cloze)
- 根据文件路径自动生成卡组层级和标签

## 关于上下文累积的成本警告

`FULL` 和 `CONTEXT_ONLY` 类型会将内容追加到后续 API 调用的上下文中。

**风险:**

- **Token 成本爆炸**: N 个块的总消耗从 O(N) 变成 O(N²)
- **效果劣化**: 上下文越长，LLM 对当前内容的注意力越分散
- **长文档不可用**: 超过十几个块就会撞上 context window 上限

**设计决策:**

- v1 默认所有块为 `CARD_ONLY`（独立处理，无累积）
- `FULL`/`CONTEXT_ONLY` 仅在未来的 interactive 模式下由用户显式选择
- 详见 [future/interactive.md](future/interactive.md)
