# Visualization Specification

## 核心原则

> 所有视觉变量由书籍数据自动计算，不人工指定。

## 四条视觉铁律

| # | 视觉变量 | 数据驱动 | 公式 |
|---|----------|----------|------|
| 1 | 节点大小 | mention_count | `min_node + scale * log(1 + count)` |
| 2 | 标签字号 | mention_count | `min_font + scale * log(1 + count)` |
| 3 | 连线粗细 | relationship_strength | `min_edge + strength * edge_range` |
| 4 | 节点距离 | relationship_strength | 力导向：强度越大，吸引力越大，距离越近 |

## 对数缩放

防止高频人物占满整张图：

```python
import math

def log_scale(value, min_val, max_val, min_out, max_out):
    """对数缩放：value → [min_out, max_out]"""
    if value <= 0:
        return min_out
    log_v = math.log(1 + value)
    log_min = math.log(1 + min_val) if min_val > 0 else 0
    log_max = math.log(1 + max_val)
    if log_max == log_min:
        return min_out
    ratio = (log_v - log_min) / (log_max - log_min)
    ratio = max(0, min(1, ratio))
    return min_out + ratio * (max_out - min_out)
```

### 推荐参数

| 参数 | 最小值 | 最大值 |
|------|--------|--------|
| 节点大小 | 200 | 3000 |
| 标签字号 | 8 | 28 |
| 连线粗细 | 0.5 | 6 |
| 连线透明度 | 0.15 | 0.85 |

## 布局

### Force-Directed Layout

```python
import networkx as nx

# 弹簧布局
pos = nx.spring_layout(G, k=1.5/len(G), iterations=200, seed=42)

# 或使用 ForceAtlas2 风格
pos = nx.forceatlas2_layout(G, ...)
```

### 社区发现

```python
# Louvain
from networkx.algorithms.community import louvain_communities
communities = louvain_communities(G)

# 或 Greedy Modularity
from networkx.algorithms.community import greedy_modularity_communities
communities = greedy_modularity_communities(G)
```

## 颜色方案

### 节点颜色

- 同一社区的人物使用相同颜色族
- 不同社区使用对比色
- 高中心度人物加金色边框

### 连线颜色

- Level 1 (明确关系)：实线，饱和色
- Level 2 (互动)：实线，半透明
- Level 3 (共同事件)：虚线
- Level 4 (共现)：点线，低透明度

## 中文显示

```python
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
```

## 输出规格

| 格式 | 用途 | 规格 | 生成参数 |
|------|------|------|----------|
| PNG | 公众号/PPT/Word | 300 DPI, A3 画布 | 默认 |
| SVG | 印刷/编辑 | 矢量，可无限放大 | 默认 |
| HTML (只读) | 交互式查看 | pyvis, 点击人物显示详情 | 默认 |
| HTML (可编辑) | 在线编辑+导出 | vis.js DataSet 双向绑定 | `--editable` |

## HTML 交互功能

### 只读版 (默认)

点击人物节点显示：

```
人物：张伟
出现次数：126
出现章节：18
关联人物：24
参与事件：31
主要关系：
  李娜  0.86
  王强  0.73
```

点击两个人物之间的连线显示关系证据原文。

### 可编辑版 (`--editable`)

基于 vis.js DataSet 双向绑定，修改即时反映到拓扑图。

**点击节点** → 右侧编辑面板：
- 人物名称、别名（逗号分隔）
- 出现次数 / 章节数 / 段落数 / 事件数 / 互动数
- 社区编号
- 保存后自动重算节点大小、标签字号、颜色

**点击连线** → 右侧编辑面板：
- 关系类型（自由输入）
- 关系级别（1-4 下拉选择）
- 关系强度（0~1，自动调整线宽）
- 共现次数 / 互动次数 / 事件数
- 证据（只读预览）
- 保存后自动重算连线粗细、透明度

**工具栏按钮**：
- 导出 JSON → 下载 `characters_edited.json` + `relationships_edited.json`
- + 新增人物 → 自动生成 C0XX 编号的新节点
- + 新增关系 → 进入连线模式，依次点击两个节点
- 删除选中 → 删除选中的节点和/或连线（删除节点时级联删除相关连线）
- 适应窗口 → 自动缩放至全部节点可见

**编辑工作流**：
```
build_network.py 生成 JSON + GraphML
        ↓
visualize_network.py --editable 生成 HTML
        ↓
浏览器打开 → 编辑节点/连线 → 导出 JSON
        ↓
重新运行 build_network.py 生成最终报告
```
