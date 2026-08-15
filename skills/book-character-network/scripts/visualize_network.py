#!/usr/bin/env python3
"""
visualize_network.py — 生成人物关系网络可视化（PNG / SVG / HTML）

用法:
    python visualize_network.py --graphml network.graphml --characters characters_enriched.json [--top 30] [--output-dir ./output]

输出:
    network_top30.png   (300 DPI)
    network_top30.svg
    network_top30.html  (交互式)
"""

import argparse
import json
import math
import os
import sys

import networkx as nx

# 中文字体
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt


# ── 颜色方案 ──────────────────────────────────────────────

COMMUNITY_COLORS = [
    "#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6",
    "#1abc9c", "#e67e22", "#34495e", "#e91e63", "#00bcd4",
    "#8bc34a", "#ff5722", "#607d8b", "#795548", "#cddc39",
    "#4caf50", "#03a9f4", "#ff9800", "#673ab7", "#ffc107",
]

EDGE_STYLE_MAP = {
    1: "-",   # 明确关系: 实线
    2: "-",   # 互动: 实线半透明
    3: "--",  # 共同事件: 虚线
    4: ":",   # 共现: 点线
}


def log_scale(value, min_val, max_val, min_out, max_out):
    """对数缩放"""
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


def select_top_nodes(G: nx.Graph, characters: list[dict], top_n: int) -> nx.Graph:
    """选取 Top N 人物构建子图"""
    top_ids = [c["id"] for c in characters[:top_n]]
    sub = G.subgraph(top_ids).copy()
    return sub


def generate_static(G: nx.Graph, characters: list[dict], output_path: str, fmt: str = "png"):
    """生成静态拓扑图 PNG/SVG"""
    if G.number_of_nodes() == 0:
        print("警告: 空图，跳过可视化", file=sys.stderr)
        return

    mention_counts = [G.nodes[n].get("mention_count", 1) for n in G.nodes()]
    min_mc = min(mention_counts) if mention_counts else 1
    max_mc = max(mention_counts) if mention_counts else 1

    # 节点大小 (对数缩放)
    node_sizes = []
    for n in G.nodes():
        mc = G.nodes[n].get("mention_count", 1)
        size = log_scale(mc, min_mc, max_mc, 300, 3000)
        node_sizes.append(size)

    # 标签字号 (对数缩放)
    font_sizes = {}
    for n in G.nodes():
        mc = G.nodes[n].get("mention_count", 1)
        font_sizes[n] = log_scale(mc, min_mc, max_mc, 8, 20)

    # 布局
    pos = nx.spring_layout(G, k=1.8 / math.sqrt(max(1, len(G))), iterations=200, seed=42)

    # 节点颜色 (按社区)
    node_colors = []
    for n in G.nodes():
        comm = G.nodes[n].get("community", 0)
        node_colors.append(COMMUNITY_COLORS[comm % len(COMMUNITY_COLORS)])

    fig, ax = plt.subplots(1, 1, figsize=(24, 18), dpi=300 if fmt == "png" else 100)
    ax.set_facecolor("#fafafa")
    fig.set_facecolor("#fafafa")

    # 边
    edges = list(G.edges(data=True))
    for u, v, d in edges:
        strength = d.get("strength", 0.1)
        level = d.get("level", 4)
        width = log_scale(strength, 0, 1, 0.5, 5)
        style = EDGE_STYLE_MAP.get(level, ":")
        alpha = log_scale(strength, 0, 1, 0.15, 0.8)
        ax.plot(
            [pos[u][0], pos[v][0]],
            [pos[u][1], pos[v][1]],
            linestyle=style,
            linewidth=width,
            color="#555555",
            alpha=alpha,
            zorder=1,
        )

    # 节点
    xs = [pos[n][0] for n in G.nodes()]
    ys = [pos[n][1] for n in G.nodes()]
    ax.scatter(xs, ys, s=node_sizes, c=node_colors, alpha=0.85, edgecolors="#333", linewidths=0.8, zorder=2)

    # 标签
    for n in G.nodes():
        name = G.nodes[n].get("name", n)
        fs = font_sizes[n]
        ax.annotate(
            name,
            pos[n],
            fontsize=fs,
            fontweight="bold",
            ha="center",
            va="bottom",
            xytext=(0, 5),
            textcoords="offset points",
            color="#222",
            zorder=3,
        )

    ax.set_aspect("equal")
    ax.axis("off")
    title = f"人物关系网络 (Top {G.number_of_nodes()})"
    ax.set_title(title, fontsize=20, fontweight="bold", pad=20)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="#fafafa")
    plt.close()
    print(f"已生成: {output_path}")


def generate_html(G: nx.Graph, characters: list[dict], output_path: str):
    """生成交互式 HTML"""
    try:
        from pyvis.network import Network
    except ImportError:
        print("pyvis 未安装，跳过 HTML 生成。安装: pip install pyvis", file=sys.stderr)
        return

    if G.number_of_nodes() == 0:
        print("警告: 空图", file=sys.stderr)
        return

    net = Network(
        height="800px",
        width="100%",
        bgcolor="#1a1a2e",
        font_color="white",
        notebook=False,
        directed=False,
        cdn_resources="in_line",
    )

    mention_counts = [G.nodes[n].get("mention_count", 1) for n in G.nodes()]
    min_mc = min(mention_counts) if mention_counts else 1
    max_mc = max(mention_counts) if mention_counts else 1

    # 节点
    for n in G.nodes():
        data = G.nodes[n]
        mc = data.get("mention_count", 1)
        size = log_scale(mc, min_mc, max_mc, 15, 60)
        comm = data.get("community", 0)
        color = COMMUNITY_COLORS[comm % len(COMMUNITY_COLORS)]

        title = (
            f"人物: {data.get('name', n)}\n"
            f"出现次数: {mc}\n"
            f"出现章节: {data.get('chapter_count', 0)}\n"
            f"参与事件: {data.get('event_count', 0)}\n"
            f"互动次数: {data.get('interaction_count', 0)}\n"
            f"中心度: {data.get('degree_centrality', 0)}\n"
            f"社区: {comm}"
        )
        net.add_node(
            n,
            label=data.get("name", n),
            size=size,
            color=color,
            title=title,
        )

    # 边
    for u, v, d in G.edges():
        strength = d.get("strength", 0.1)
        width = log_scale(strength, 0, 1, 1, 8)
        level = d.get("level", 4)
        rel = d.get("relationship", "")
        evidence = d.get("evidence", [])

        evidence_text = ""
        if evidence:
            evidence_text = "\n\n证据:\n" + "\n".join(
                f"  - [{e.get('chapter','')} 第{e.get('paragraph','')}段] {e.get('text','')[:80]}..."
                for e in evidence[:5]
            )

        title = (
            f"关系: {rel}\n"
            f"强度: {strength}\n"
            f"共现: {d.get('co_occurrence', 0)}\n"
            f"互动: {d.get('interaction_count', 0)}\n"
            f"事件: {d.get('event_count', 0)}"
            f"{evidence_text}"
        )
        net.add_edge(
            u, v,
            width=width,
            title=title,
            color={"opacity": strength},
        )

    net.set_options(json.dumps({
        "physics": {
            "forceAtlas2Based": {
                "gravitationalConstant": -50,
                "centralGravity": 0.01,
                "springLength": 100,
                "springConstant": 0.08,
            },
            "minVelocity": 0.75,
            "solver": "forceAtlas2Based",
        },
        "nodes": {"font": {"size": 16, "face": "Microsoft YaHei, sans-serif"}},
        "edges": {
            "smooth": {"type": "continuous"},
            "font": {"face": "Microsoft YaHei, sans-serif"},
        },
        "interaction": {"hover": True, "tooltipDelay": 100},
    }))

    net.save_graph(output_path)
    print(f"已生成: {output_path}")


def generate_editable_html(G: nx.Graph, characters: list[dict], output_path: str):
    """
    生成可在线编辑的人物关系拓扑图 HTML。

    功能：
    - 点击节点 → 弹出人物编辑表单（名称/别名/频次/社区）
    - 点击连线 → 弹出关系编辑表单（关系类型/级别/强度/共现/互动/事件）
    - 修改后实时更新拓扑图
    - 导出按钮 → 下载更新后的 characters.json 和 relationships.json
    - 新增节点/删除节点/新增连线/删除连线
    """
    if G.number_of_nodes() == 0:
        print("警告: 空图", file=sys.stderr)
        return

    mention_counts = [G.nodes[n].get("mention_count", 1) for n in G.nodes()]
    min_mc = min(mention_counts) if mention_counts else 1
    max_mc = max(mention_counts) if mention_counts else 1

    # 构建节点 JSON
    nodes_data = []
    for n in G.nodes():
        data = G.nodes[n]
        mc = data.get("mention_count", 1)
        size = log_scale(mc, min_mc, max_mc, 15, 60)
        comm = data.get("community", 0)
        color = COMMUNITY_COLORS[comm % len(COMMUNITY_COLORS)]
        font_size = log_scale(mc, min_mc, max_mc, 12, 28)
        nodes_data.append({
            "id": n,
            "label": data.get("name", n),
            "size": size,
            "color": color,
            "font": {"size": font_size, "face": "Microsoft YaHei, sans-serif"},
            # 原始数据，用于编辑表单
            "_name": data.get("name", n),
            "_aliases": data.get("aliases", []),
            "_mention_count": mc,
            "_chapter_count": data.get("chapter_count", 0),
            "_paragraph_count": data.get("paragraph_count", 0),
            "_event_count": data.get("event_count", 0),
            "_interaction_count": data.get("interaction_count", 0),
            "_community": comm,
        })

    # 构建边 JSON
    edges_data = []
    for u, v, d in G.edges(data=True):
        strength = d.get("strength", 0.1)
        width = log_scale(strength, 0, 1, 1, 8)
        level = d.get("level", 4)
        edges_data.append({
            "id": f"{u}__{v}",
            "from": u,
            "to": v,
            "width": width,
            "color": {"opacity": strength},
            "title": f"关系: {d.get('relationship','')} | 强度: {strength}",
            # 原始数据
            "_relationship": d.get("relationship", ""),
            "_level": level,
            "_strength": strength,
            "_co_occurrence": d.get("co_occurrence", 0),
            "_interaction_count": d.get("interaction_count", 0),
            "_event_count": d.get("event_count", 0),
            "_evidence": d.get("evidence", []),
        })

    nodes_json = json.dumps(nodes_data, ensure_ascii=False)
    edges_json = json.dumps(edges_data, ensure_ascii=False)

    html_content = EDITABLE_HTML_TEMPLATE.replace("__NODES_DATA__", nodes_json).replace("__EDGES_DATA__", edges_json)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"已生成可编辑 HTML: {output_path}")


EDITABLE_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>人物关系网络 - 可编辑拓扑图</title>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif; background: #1a1a2e; color: #e0e0e0; overflow: hidden; }
  #app { display: flex; height: 100vh; }
  #network-container { flex: 1; position: relative; }
  #mynetwork { width: 100%; height: 100%; }
  #toolbar {
    position: absolute; top: 10px; left: 10px; z-index: 10;
    display: flex; gap: 8px; flex-wrap: wrap;
  }
  .btn {
    padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer;
    font-size: 13px; font-weight: 600; transition: all 0.2s;
  }
  .btn-primary { background: #3498db; color: white; }
  .btn-success { background: #2ecc71; color: white; }
  .btn-danger { background: #e74c3c; color: white; }
  .btn-warning { background: #f39c12; color: white; }
  .btn:hover { opacity: 0.85; transform: translateY(-1px); }
  #edit-panel {
    width: 420px; background: #16213e; border-left: 2px solid #0f3460;
    padding: 0; overflow-y: auto; display: none;
  }
  #edit-panel.active { display: block; }
  .panel-header {
    padding: 15px 20px; background: #0f3460; font-size: 16px; font-weight: bold;
    display: flex; justify-content: space-between; align-items: center;
  }
  .panel-close { cursor: pointer; font-size: 20px; color: #aaa; }
  .panel-close:hover { color: #fff; }
  .panel-body { padding: 20px; }
  .form-group { margin-bottom: 15px; }
  .form-group label { display: block; margin-bottom: 5px; font-size: 13px; color: #aaa; }
  .form-group input, .form-group textarea, .form-group select {
    width: 100%; padding: 8px 10px; border: 1px solid #0f3460; border-radius: 4px;
    background: #1a1a2e; color: #e0e0e0; font-size: 14px; font-family: inherit;
  }
  .form-group textarea { resize: vertical; min-height: 60px; }
  .form-group input:focus, .form-group textarea:focus, .form-group select:focus {
    outline: none; border-color: #3498db;
  }
  .form-row { display: flex; gap: 10px; }
  .form-row .form-group { flex: 1; }
  .info-box {
    background: #0f3460; padding: 12px; border-radius: 6px; margin-bottom: 15px;
    font-size: 13px; line-height: 1.6;
  }
  .info-box strong { color: #3498db; }
  .hidden { display: none !important; }
  #toast {
    position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
    background: #2ecc71; color: white; padding: 10px 24px; border-radius: 6px;
    font-size: 14px; z-index: 100; opacity: 0; transition: opacity 0.3s;
    pointer-events: none;
  }
  #toast.show { opacity: 1; }
</style>
</head>
<body>
<div id="app">
  <div id="network-container">
    <div id="toolbar">
      <button class="btn btn-success" onclick="exportJSON()">导出 JSON</button>
      <button class="btn btn-primary" onclick="addNode()">+ 新增人物</button>
      <button class="btn btn-warning" onclick="addEdgeMode()">+ 新增关系</button>
      <button class="btn btn-danger" onclick="deleteSelected()">删除选中</button>
      <button class="btn btn-primary" onclick="fitNetwork()">适应窗口</button>
    </div>
    <div id="mynetwork"></div>
  </div>
  <div id="edit-panel">
    <div class="panel-header">
      <span id="panel-title">编辑</span>
      <span class="panel-close" onclick="closePanel()">&times;</span>
    </div>
    <div class="panel-body" id="panel-body"></div>
  </div>
</div>
<div id="toast"></div>

<script>
// ── 数据 ──
var nodesData = __NODES_DATA__;
var edgesData = __EDGES_DATA__;

// ── vis.js DataSet (双向绑定) ──
var nodes = new vis.DataSet(nodesData);
var edges = new vis.DataSet(edgesData);

var container = document.getElementById('mynetwork');
var data = { nodes: nodes, edges: edges };
var options = {
  physics: {
    forceAtlas2Based: {
      gravitationalConstant: -50,
      centralGravity: 0.01,
      springLength: 100,
      springConstant: 0.08
    },
    minVelocity: 0.75,
    solver: 'forceAtlas2Based'
  },
  interaction: { hover: true, tooltipDelay: 100, selectConnectedEdges: false },
  nodes: { shape: 'dot', scaling: { min: 15, max: 60 } },
  edges: { smooth: { type: 'continuous' } }
};
var network = new vis.Network(container, data, options);

// ── 状态 ──
var currentSelection = null; // {type: 'node'|'edge', id: ...}
var edgeMode = false;

// ── 点击事件 ──
network.on('click', function(params) {
  if (edgeMode) {
    handleEdgeCreation(params);
    return;
  }
  if (params.nodes.length > 0) {
    var nodeId = params.nodes[0];
    showNodeEditor(nodeId);
  } else if (params.edges.length > 0) {
    var edgeId = params.edges[0];
    showEdgeEditor(edgeId);
  } else {
    closePanel();
  }
});

// ── 节点编辑表单 ──
function showNodeEditor(nodeId) {
  var node = nodes.get(nodeId);
  if (!node) return;
  currentSelection = { type: 'node', id: nodeId };

  var aliases = (node._aliases || []).join(', ');
  var html = `
    <div class="info-box">
      <strong>节点 ID:</strong> ${nodeId}<br>
      <strong>当前标签:</strong> ${node.label}
    </div>
    <div class="form-group">
      <label>人物名称</label>
      <input type="text" id="edit-name" value="${node._name || node.label}">
    </div>
    <div class="form-group">
      <label>别名 (逗号分隔)</label>
      <input type="text" id="edit-aliases" value="${aliases}">
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>出现次数</label>
        <input type="number" id="edit-mention" value="${node._mention_count || 0}">
      </div>
      <div class="form-group">
        <label>章节数</label>
        <input type="number" id="edit-chapter" value="${node._chapter_count || 0}">
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>段落数</label>
        <input type="number" id="edit-paragraph" value="${node._paragraph_count || 0}">
      </div>
      <div class="form-group">
        <label>事件数</label>
        <input type="number" id="edit-event" value="${node._event_count || 0}">
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>互动数</label>
        <input type="number" id="edit-interaction" value="${node._interaction_count || 0}">
      </div>
      <div class="form-group">
        <label>社区编号</label>
        <input type="number" id="edit-community" value="${node._community || 0}">
      </div>
    </div>
    <button class="btn btn-success" onclick="saveNode('${nodeId}')" style="width:100%;margin-top:10px;">保存修改</button>
  `;
  document.getElementById('panel-title').textContent = '编辑人物';
  document.getElementById('panel-body').innerHTML = html;
  document.getElementById('edit-panel').classList.add('active');
}

// ── 边编辑表单 ──
function showEdgeEditor(edgeId) {
  var edge = edges.get(edgeId);
  if (!edge) return;
  currentSelection = { type: 'edge', id: edgeId };

  var levelOptions = [1,2,3,4].map(l => {
    var desc = {1:'明确关系',2:'互动',3:'共同事件',4:'共现'}[l];
    return `<option value="${l}" ${edge._level==l?'selected':''}>${l} - ${desc}</option>`;
  }).join('');

  var evidence = (edge._evidence || []).map(e =>
    `[${e.chapter||''} 第${e.paragraph||''}段] ${(e.text||'').substring(0,60)}...`
  ).join('\n');

  var html = `
    <div class="info-box">
      <strong>关系 ID:</strong> ${edgeId}<br>
      <strong>连接:</strong> ${edge.from} ↔ ${edge.to}
    </div>
    <div class="form-group">
      <label>关系类型</label>
      <input type="text" id="edit-relationship" value="${edge._relationship || ''}" placeholder="如: 合作/家人/上下级">
    </div>
    <div class="form-group">
      <label>关系级别</label>
      <select id="edit-level">${levelOptions}</select>
    </div>
    <div class="form-group">
      <label>关系强度 (0~1)</label>
      <input type="number" id="edit-strength" value="${edge._strength || 0}" step="0.01" min="0" max="1">
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>共现次数</label>
        <input type="number" id="edit-cooccurrence" value="${edge._co_occurrence || 0}">
      </div>
      <div class="form-group">
        <label>互动次数</label>
        <input type="number" id="edit-edge-interaction" value="${edge._interaction_count || 0}">
      </div>
    </div>
    <div class="form-group">
      <label>事件数</label>
      <input type="number" id="edit-edge-event" value="${edge._event_count || 0}">
    </div>
    <div class="form-group">
      <label>证据 (只读)</label>
      <textarea id="edit-evidence" readonly>${evidence || '无证据'}</textarea>
    </div>
    <button class="btn btn-success" onclick="saveEdge('${edgeId}')" style="width:100%;margin-top:10px;">保存修改</button>
  `;
  document.getElementById('panel-title').textContent = '编辑关系';
  document.getElementById('panel-body').innerHTML = html;
  document.getElementById('edit-panel').classList.add('active');
}

// ── 保存节点修改 ──
function saveNode(nodeId) {
  var name = document.getElementById('edit-name').value;
  var aliases = document.getElementById('edit-aliases').value.split(',').map(s => s.trim()).filter(Boolean);
  var mention = parseInt(document.getElementById('edit-mention').value) || 0;
  var chapter = parseInt(document.getElementById('edit-chapter').value) || 0;
  var paragraph = parseInt(document.getElementById('edit-paragraph').value) || 0;
  var event = parseInt(document.getElementById('edit-event').value) || 0;
  var interaction = parseInt(document.getElementById('edit-interaction').value) || 0;
  var community = parseInt(document.getElementById('edit-community').value) || 0;

  var mc = Math.max(1, mention);
  var minMc = 1, maxMc = Math.max(...nodes.get().map(n => n._mention_count || 1), mc);
  var size = logScale(mc, minMc, maxMc, 15, 60);
  var fontSize = logScale(mc, minMc, maxMc, 12, 28);
  var colors = ['#e74c3c','#3498db','#2ecc71','#f39c12','#9b59b6','#1abc9c','#e67e22','#34495e','#e91e63','#00bcd4'];
  var color = colors[community % colors.length];

  nodes.update({
    id: nodeId,
    label: name,
    size: size,
    color: color,
    font: { size: fontSize, face: 'Microsoft YaHei, sans-serif' },
    _name: name,
    _aliases: aliases,
    _mention_count: mention,
    _chapter_count: chapter,
    _paragraph_count: paragraph,
    _event_count: event,
    _interaction_count: interaction,
    _community: community
  });
  showToast('人物已更新: ' + name);
}

// ── 保存边修改 ──
function saveEdge(edgeId) {
  var rel = document.getElementById('edit-relationship').value;
  var level = parseInt(document.getElementById('edit-level').value) || 4;
  var strength = parseFloat(document.getElementById('edit-strength').value) || 0;
  strength = Math.max(0, Math.min(1, strength));
  var co = parseInt(document.getElementById('edit-cooccurrence').value) || 0;
  var inter = parseInt(document.getElementById('edit-edge-interaction').value) || 0;
  var evt = parseInt(document.getElementById('edit-edge-event').value) || 0;

  var width = logScale(strength, 0, 1, 1, 8);

  edges.update({
    id: edgeId,
    width: width,
    color: { opacity: strength },
    title: `关系: ${rel} | 强度: ${strength} | 级别: ${level}`,
    _relationship: rel,
    _level: level,
    _strength: strength,
    _co_occurrence: co,
    _interaction_count: inter,
    _event_count: evt
  });
  showToast('关系已更新: ' + rel);
}

// ── 新增节点 ──
function addNode() {
  var existing = nodes.get();
  var maxNum = 0;
  existing.forEach(n => {
    var m = (n.id || '').match(/^C(\d+)$/);
    if (m) maxNum = Math.max(maxNum, parseInt(m[1]));
  });
  var newId = 'C' + String(maxNum + 1).padStart(3, '0');
  nodes.add({
    id: newId,
    label: '新人物',
    size: 20,
    color: '#3498db',
    font: { size: 14, face: 'Microsoft YaHei, sans-serif' },
    _name: '新人物',
    _aliases: [],
    _mention_count: 1,
    _chapter_count: 0,
    _paragraph_count: 0,
    _event_count: 0,
    _interaction_count: 0,
    _community: 0
  });
  showToast('已新增节点: ' + newId);
  showNodeEditor(newId);
}

// ── 新增关系模式 ──
function addEdgeMode() {
  edgeMode = true;
  network.addEdgeMode();
  showToast('点击两个节点创建关系');
}

function handleEdgeCreation(params) {
  if (params.nodes.length === 2) {
    var from = params.nodes[0];
    var to = params.nodes[1];
    var edgeId = `${from}__${to}`;
    edges.add({
      id: edgeId,
      from: from,
      to: to,
      width: 2,
      color: { opacity: 0.5 },
      title: '新关系',
      _relationship: '未知',
      _level: 4,
      _strength: 0.1,
      _co_occurrence: 0,
      _interaction_count: 0,
      _event_count: 0,
      _evidence: []
    });
    showToast('已新增关系: ' + edgeId);
  }
  edgeMode = false;
  network.disableNodeMode();
}

// ── 删除选中 ──
function deleteSelected() {
  var selectedNodes = network.getSelectedNodes();
  var selectedEdges = network.getSelectedEdges();
  selectedEdges.forEach(eid => edges.remove(eid));
  selectedNodes.forEach(nid => {
    edges.get().forEach(e => {
      if (e.from === nid || e.to === nid) edges.remove(e.id);
    });
    nodes.remove(nid);
  });
  closePanel();
  showToast('已删除 ' + selectedNodes.length + ' 节点, ' + selectedEdges.length + ' 关系');
}

// ── 导出 JSON ──
function exportJSON() {
  var allNodes = nodes.get();
  var allEdges = edges.get();

  // characters.json
  var characters = allNodes.map((n, i) => ({
    id: n.id,
    name: n._name || n.label,
    aliases: n._aliases || [],
    mention_count: n._mention_count || 0,
    chapter_count: n._chapter_count || 0,
    paragraph_count: n._paragraph_count || 0,
    event_count: n._event_count || 0,
    interaction_count: n._interaction_count || 0,
    community: n._community || 0
  }));

  // relationships.json
  var relationships = allEdges.map(e => ({
    source: e.from,
    target: e.to,
    relationship: e._relationship || '',
    level: e._level || 4,
    strength: e._strength || 0,
    co_occurrence: e._co_occurrence || 0,
    interaction_count: e._interaction_count || 0,
    event_count: e._event_count || 0,
    evidence: e._evidence || []
  }));

  downloadJSON(characters, 'characters_edited.json');
  setTimeout(() => downloadJSON(relationships, 'relationships_edited.json'), 500);
  showToast('已导出 characters_edited.json 和 relationships_edited.json');
}

function downloadJSON(data, filename) {
  var blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  var url = URL.createObjectURL(blob);
  var a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ── 辅助 ──
function logScale(value, minVal, maxVal, minOut, maxOut) {
  if (value <= 0) return minOut;
  var logV = Math.log(1 + value);
  var logMin = minVal > 0 ? Math.log(1 + minVal) : 0;
  var logMax = Math.log(1 + maxVal);
  if (logMax === logMin) return minOut;
  var ratio = (logV - logMin) / (logMax - logMin);
  ratio = Math.max(0, Math.min(1, ratio));
  return minOut + ratio * (maxOut - minOut);
}

function closePanel() {
  document.getElementById('edit-panel').classList.remove('active');
  currentSelection = null;
}

function fitNetwork() {
  network.fit({ animation: { duration: 500 } });
}

function showToast(msg) {
  var toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2500);
}
</script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="生成人物关系网络可视化")
    parser.add_argument("--graphml", required=True, help="network.graphml 路径")
    parser.add_argument("--characters", required=True, help="characters_enriched.json 路径")
    parser.add_argument("--top", type=int, default=30, help="显示 Top N 人物")
    parser.add_argument("--output-dir", "-o", default="./output", help="输出目录")
    parser.add_argument("--editable", action="store_true", help="生成可编辑 HTML（默认生成只读 HTML）")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    G = nx.read_graphml(args.graphml)

    # 将 GraphML 的属性转回正确类型
    for n in G.nodes():
        for key in ["mention_count", "chapter_count", "paragraph_count", "event_count", "interaction_count", "community"]:
            if key in G.nodes[n]:
                try:
                    G.nodes[n][key] = int(float(G.nodes[n][key]))
                except (ValueError, TypeError):
                    pass
        for key in ["degree_centrality", "betweenness_centrality", "eigenvector_centrality", "composite_centrality"]:
            if key in G.nodes[n]:
                try:
                    G.nodes[n][key] = float(G.nodes[n][key])
                except (ValueError, TypeError):
                    pass

    with open(args.characters, "r", encoding="utf-8") as f:
        characters = json.load(f)

    top_n = args.top
    sub = select_top_nodes(G, characters, top_n)
    print(f"子图: {sub.number_of_nodes()} 节点, {sub.number_of_edges()} 边")

    # PNG
    png_path = os.path.join(args.output_dir, f"network_top{top_n}.png")
    generate_static(sub, characters, png_path, "png")

    # SVG
    svg_path = os.path.join(args.output_dir, f"network_top{top_n}.svg")
    generate_static(sub, characters, svg_path, "svg")

    # HTML
    if args.editable:
        html_path = os.path.join(args.output_dir, f"network_top{top_n}_editable.html")
        generate_editable_html(sub, characters, html_path)
    else:
        html_path = os.path.join(args.output_dir, f"network_top{top_n}.html")
        generate_html(sub, characters, html_path)


if __name__ == "__main__":
    main()
