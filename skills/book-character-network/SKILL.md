---
name: book-character-network
description: 书籍人物关系网络分析 + 人物频次可视化。输入一本书（PDF/DOCX/EPUB/TXT 或纯文本），自动完成人物识别、别名归一化、出现频次统计、共现关系提取、关系类型分级（A明确关系/B互动/C共同事件/D共现）、关系强度计算、网络中心度计算、社区发现，并生成可视化拓扑图（PNG/SVG/HTML）及 Markdown 分析报告。适用于小说、传记、纪实文学、商业书籍、访谈录、行业报告、会议纪要等任何包含人物的文本。触发词：书籍人物关系、人物网络图、人物频次、人物拓扑、角色关系分析、book character network。
agent_created: true
---

# Book Character Network

## Purpose

分析用户提供的书籍文本，识别人物实体，统计人物出现频次，提取人物之间的关系，计算人物网络结构，并生成可视化人物关系拓扑图。

## Core Principle

人物出现频次是人物视觉权重的核心指标。必须遵循：

```
Node Size     ∝ Mention Frequency
Label Size    ∝ Mention Frequency
Edge Width    ∝ Relationship Strength
Node Distance ∝ Network Relationship（关系越强距离越近）
```

所有视觉变量由书籍数据自动计算，不人工指定。

## When To Use

- 用户上传一本书（PDF / EPUB / DOCX / TXT）并要求分析人物关系
- 用户要求生成人物关系网络图 / 人物频次图 / 人物拓扑图
- 用户要求统计书中人物出现次数
- 用户要求分析小说、传记、纪实文学、商业案例中的人物圈层
- 关键词：人物关系、人物网络、人物频次、角色关系、人物拓扑、character network

## Workflow

按以下顺序执行，不得跳步：

1. **Parse the book** — 解析书籍文本，识别章节和段落结构
2. **Detect chapters and paragraphs** — 建立章节-段落索引
3. **Extract character entities** — 提取所有人物实体
4. **Resolve aliases and references** — 别名归一化，建立唯一人物 ID
5. **Calculate character mention frequency** — 统计 mention_count / chapter_count / paragraph_count / event_count / interaction_count
6. **Extract explicit relationships** — Level 1: 明确关系
7. **Extract direct interactions** — Level 2: 明确互动
8. **Extract shared events** — Level 3: 共同事件
9. **Record co-occurrence** — Level 4: 共同出现（单独记录，不自动认定关系）
10. **Calculate relationship strength** — 0~1 标准化
11. **Calculate network centrality** — degree / betweenness / eigenvector
12. **Detect communities** — 社区发现算法识别人物圈层
13. **Select core characters** — Top 20 / 30 / 50
14. **Generate network topology** — Force-directed layout
15. **Generate visualizations** — PNG / SVG / HTML
16. **Generate evidence-backed report** — Markdown 分析报告

## Character Resolution

### 实体分类

区分以下实体类型，不得混淆：

| 类型 | 说明 | 示例 |
|------|------|------|
| person | 人物 | 张伟 |
| alias | 别名/昵称 | 老张、张老师 |
| organization | 机构 | 腾讯、委员会 |
| location | 地名 | 北京、上海 |
| title | 职务 | 总经理、教授 |
| role | 角色 | 主角、 narrator |
| generic | 泛指 | 他、他们、某人 |

### 归一化规则

- 为每个标准人物建立唯一 ID（C001, C002, ...）
- 别名归入 `aliases` 数组
- 保留 `alias_confidence`（0~1）
- **置信度 < 0.5 不得合并，标记为 `pending`**
- **不得强行合并不确定的人物**

```json
{
  "id": "C001",
  "name": "张伟",
  "aliases": ["老张", "张老师", "张总"],
  "alias_confidence": 0.96,
  "entity_type": "person"
}
```

## Mention Frequency

核心指标，同时统计五个维度：

| 字段 | 说明 |
|------|------|
| mention_count | 人物名称或确认别名在全文中的出现次数 |
| chapter_count | 人物出现过的章节数 |
| paragraph_count | 人物出现过的段落数 |
| event_count | 人物实际参与的事件数 |
| interaction_count | 人物与其他人物发生明确互动的次数 |

## Relationship Rules

### 四级关系

**不得将共现直接等同于关系。** 按优先级处理：

| Level | 类型 | 说明 | weight |
|-------|------|------|--------|
| 1 | explicit_relationship | 文本直接表达（A是B的同事/夫妻/上级） | 0.30 |
| 2 | direct_interaction | 明确互动（A拜访B、A与B讨论） | 0.30 |
| 3 | shared_event | 共同参与事件（会议/项目/活动） | 0.20 |
| 4 | co_occurrence | 仅在同段出现 | 0.10 |

剩余 0.10 分配给 `relationship_continuity`（关系持续性：跨章节出现的关系加分）。

### 关系类型（开放式分类）

自动识别，不预设固定列表。常见类型见 `references/relationship_types.md`。

## Relationship Strength

```
strength = 0.30 * explicit + 0.30 * interaction + 0.20 * shared_event + 0.10 * co_occurrence + 0.10 * continuity
```

输出 0~1 标准化值。

## Visualization

### 视觉规范（四条铁律）

| 视觉变量 | 数据驱动 | 缩放方式 |
|----------|----------|----------|
| 节点大小 | mention_count | 对数缩放 |
| 标签字号 | mention_count | 对数缩放 |
| 连线粗细 | relationship_strength | 线性 |
| 节点距离 | relationship_strength | 力导向自动 |

### 对数缩放公式

```
font_size = min_font + scale_ratio * log(1 + mention_count)
node_size = min_node + scale_ratio * log(1 + mention_count)
```

防止高频人物占满整张图。

### 布局

- Force-Directed Graph（力导向布局）
- NetworkX spring_layout 或 ForceAtlas2
- 社区发现：Louvain / Greedy Modularity
- 节点距离由关系强度反向决定：关系越强 → 距离越近

### 默认显示

| 版本 | 人数 | 用途 |
|------|------|------|
| Top 20 | 核心人物图 | 快速概览 |
| Top 30 | 标准人物关系图 | 默认输出 |
| Top 50 | 扩展人物关系图 | 深入分析 |
| 全部 | 不渲染图 | 仅导出 JSON/GraphML/CSV |

## Centrality

不只看出现次数。同时计算：

```
人物中心度 = mention_count + 关系数量 + 关系强度 + betweenness + 事件参与度
```

区分两类人物：
- **高频人物**：出现次数多
- **网络核心人物**：连接大量人物（高 betweenness）

分别展示。

## Evidence

每条重要关系必须保存证据，可追溯到原文：

```json
{
  "source": "C001",
  "target": "C002",
  "relationship": "合作",
  "strength": 0.86,
  "evidence": [
    {
      "chapter": "第8章",
      "page": 126,
      "paragraph": 4,
      "text": "原文片段..."
    }
  ]
}
```

**不得编造无原文支持的关系。**

## Output Structure

用户上传书籍后，自动输出以下内容：

```
📚 《书名》

一、基本统计
────────────────
总字数 / 章节数 / 人物数量 / 核心人物数量

二、人物出现频次 TOP 30
────────────────
排名 / 人物 / 出现次数 / 章节数 / 事件数 / 中心度

三、人物关系 TOP 30
────────────────
人物A / 人物B / 关系类型 / 关系强度 / 共同事件

四、人物关系拓扑图
────────────────
PNG / SVG / HTML（只读版 + 可编辑版）

五、人物关系矩阵

六、人物圈层分析

七、人物关系详细分析

八、数据文件
────────────────
characters.json
relationships.json
network.graphml
network.csv
```

## Editable HTML (在线可编辑拓扑图)

使用 `--editable` 参数生成可在线编辑的人物关系拓扑图 HTML。

### 功能

- **点击节点** → 弹出人物编辑表单（名称/别名/频次/社区）
- **点击连线** → 弹出关系编辑表单（关系类型/级别/强度/共现/互动/事件/证据）
- **修改后实时更新** → 拓扑图节点大小/标签字号/连线粗细自动重算
- **新增节点** → 点击「+ 新增人物」按钮
- **新增关系** → 点击「+ 新增关系」后依次点击两个节点
- **删除节点/关系** → 选中后点击「删除选中」
- **导出 JSON** → 点击「导出 JSON」按钮下载 `characters_edited.json` 和 `relationships_edited.json`

### 生成命令

```bash
python visualize_network.py --graphml network.graphml --characters characters_enriched.json --top 30 --editable --output-dir ./output
```

### 用途

- 用户人工修正 AI 提取的人物关系（补充遗漏、删除误判、调整强度）
- 团队协作编辑人物关系网络
- 导出修正后的 JSON 重新输入 build_network.py 生成最终报告

### 工作流

```
build_network.py → characters_enriched.json + network.graphml
                         ↓
visualize_network.py --editable → network_editable.html
                         ↓
用户在浏览器中编辑节点/连线
                         ↓
导出 characters_edited.json + relationships_edited.json
                         ↓
（可选）重新运行 build_network.py 生成最终报告
```

## Resources

### scripts/

- `extract_text.py` — 从 PDF/EPUB/DOCX/TXT 提取纯文本并分章分段
- `build_network.py` — 人物识别、归一化、频次统计、关系提取、强度计算、中心度、社区发现，输出 JSON/GraphML/CSV
- `visualize_network.py` — 生成 PNG（300 DPI）/ SVG / 只读 HTML / 可编辑 HTML（`--editable` 参数）

### references/

- `relationship_types.md` — 开放式关系类型分类参考
- `visualization_spec.md` — 可视化规范详解（颜色、缩放、布局参数）

### assets/

无需静态资源。

## Execution Notes

- Python 运行环境：优先使用 managed Python `C:\Users\hbxgl\.workbuddy\binaries\python\versions\3.13.12\python.exe`
- 依赖安装到隔离 venv：`C:\Users\hbxgl\.workbuddy\binaries\python\envs\default`
- 必要依赖：networkx, matplotlib, pymupdf (fitz), python-docx, ebooklib, beautifulsoup4, pyvis
- 中文文本：人物识别依赖 LLM 语义理解，脚本负责文本预处理和结构化输出；人物提取本身由 WorkBuddy 完成
- 脚本设计为模块化：可单独运行某一步骤，也可串联执行全流程
- 大书（>50万字）分批处理，避免单次 LLM 调用超长
