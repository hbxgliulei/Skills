#!/usr/bin/env python3
"""
build_network.py — 从 LLM 产出的人物/关系 JSON 构建 NetworkX 网络并计算指标

本脚本不负责人物识别（由 WorkBuddy LLM 完成），而是：
1. 接收 WorkBuddy 生成的人物 JSON 和关系 JSON
2. 构建 NetworkX 图
3. 计算中心度、社区、关系强度
4. 输出 GraphML / CSV / 增强后的 JSON

用法:
    python build_network.py --characters characters.json --relationships relationships.json [--output-dir ./output]

输入 characters.json:
[
  {"id": "C001", "name": "张伟", "aliases": ["老张"], "mention_count": 126, "chapter_count": 18, ...},
  ...
]

输入 relationships.json:
[
  {"source": "C001", "target": "C002", "relationship": "合作", "level": 1, "co_occurrence": 48, ...},
  ...
]

输出:
  network.graphml
  characters_enriched.json  (增加 centrality 字段)
  relationships_enriched.json  (增加 strength 字段)
  network_summary.json
"""

import argparse
import json
import math
import os
import sys

import networkx as nx


def calculate_relationship_strength(rel: dict) -> float:
    """
    strength = 0.30*explicit + 0.30*interaction + 0.20*shared_event + 0.10*co_occurrence + 0.10*continuity
    """
    level = rel.get("level", 4)
    co_occurrence = rel.get("co_occurrence", 0)
    interaction_count = rel.get("interaction_count", 0)
    event_count = rel.get("event_count", 0)
    has_explicit = rel.get("has_explicit_relationship", level == 1)
    has_interaction = rel.get("has_direct_interaction", level == 2)
    has_shared_event = rel.get("has_shared_event", level == 3)

    explicit_score = 1.0 if has_explicit else 0.0
    interaction_score = min(1.0, interaction_count / 10.0) if has_interaction else (min(1.0, interaction_count / 10.0) * 0.3)
    shared_event_score = min(1.0, event_count / 5.0) if has_shared_event else (min(1.0, event_count / 5.0) * 0.2)
    co_occurrence_score = min(1.0, co_occurrence / 20.0)

    # 关系持续性：跨章节出现加分
    cross_chapter = rel.get("cross_chapter_count", 0)
    continuity_score = min(1.0, cross_chapter / 10.0)

    strength = (
        0.30 * explicit_score
        + 0.30 * interaction_score
        + 0.20 * shared_event_score
        + 0.10 * co_occurrence_score
        + 0.10 * continuity_score
    )
    return round(strength, 4)


def build_graph(characters: list[dict], relationships: list[dict]) -> nx.Graph:
    G = nx.Graph()

    for char in characters:
        G.add_node(
            char["id"],
            name=char["name"],
            aliases=char.get("aliases", []),
            mention_count=char.get("mention_count", 0),
            chapter_count=char.get("chapter_count", 0),
            paragraph_count=char.get("paragraph_count", 0),
            event_count=char.get("event_count", 0),
            interaction_count=char.get("interaction_count", 0),
        )

    for rel in relationships:
        source = rel["source"]
        target = rel["target"]
        if source not in G or target not in G:
            print(f"警告: 节点不存在 {source} 或 {target}，跳过", file=sys.stderr)
            continue

        strength = calculate_relationship_strength(rel)
        G.add_edge(
            source,
            target,
            relationship=rel.get("relationship", "未知"),
            level=rel.get("level", 4),
            strength=strength,
            co_occurrence=rel.get("co_occurrence", 0),
            interaction_count=rel.get("interaction_count", 0),
            event_count=rel.get("event_count", 0),
            evidence=rel.get("evidence", []),
        )

    return G


def calculate_centrality(G: nx.Graph) -> dict:
    """计算各类中心度"""
    result = {}

    if len(G) == 0:
        return result

    degree = nx.degree_centrality(G)
    betweenness = nx.betweenness_centrality(G)
    try:
        eigenvector = nx.eigenvector_centrality(G, max_iter=1000)
    except Exception:
        eigenvector = {n: 0.0 for n in G.nodes()}

    for node in G.nodes():
        result[node] = {
            "degree_centrality": round(degree.get(node, 0), 4),
            "betweenness_centrality": round(betweenness.get(node, 0), 4),
            "eigenvector_centrality": round(eigenvector.get(node, 0), 4),
            "degree": G.degree(node),
        }

    return result


def detect_communities(G: nx.Graph) -> dict:
    """社区发现"""
    if len(G) == 0:
        return {}

    try:
        communities = nx.algorithms.community.louvain_communities(G, seed=42)
    except Exception:
        try:
            communities = list(nx.algorithms.community.greedy_modularity_communities(G))
        except Exception:
            communities = [set(G.nodes())]

    node_to_community = {}
    for i, community in enumerate(communities):
        for node in community:
            node_to_community[node] = i

    return node_to_community


def enrich_characters(characters: list[dict], G: nx.Graph, centrality: dict, communities: dict) -> list[dict]:
    for char in characters:
        cid = char["id"]
        if cid in centrality:
            char.update(centrality[cid])
        char["community"] = communities.get(cid, 0)
        # 综合中心度
        char["composite_centrality"] = round(
            char.get("mention_count", 0) / max(1, max(c.get("mention_count", 1) for c in characters)) * 0.3
            + char.get("degree_centrality", 0) * 0.3
            + char.get("betweenness_centrality", 0) * 0.2
            + char.get("eigenvector_centrality", 0) * 0.2,
            4,
        )
    # 按 composite_centrality 排序
    characters.sort(key=lambda c: c.get("composite_centrality", 0), reverse=True)
    for i, c in enumerate(characters):
        c["rank"] = i + 1
    return characters


def enrich_relationships(relationships: list[dict]) -> list[dict]:
    for rel in relationships:
        rel["strength"] = calculate_relationship_strength(rel)
    relationships.sort(key=lambda r: r["strength"], reverse=True)
    for i, r in enumerate(relationships):
        r["rank"] = i + 1
    return relationships


def export_csv(characters: list[dict], relationships: list[dict], output_dir: str):
    # characters.csv
    char_path = os.path.join(output_dir, "characters.csv")
    with open(char_path, "w", encoding="utf-8-sig") as f:
        f.write("rank,id,name,mention_count,chapter_count,paragraph_count,event_count,interaction_count,degree_centrality,betweenness_centrality,eigenvector_centrality,community,composite_centrality\n")
        for c in characters:
            f.write(f'{c.get("rank","")},{c["id"]},{c["name"]},{c.get("mention_count",0)},{c.get("chapter_count",0)},{c.get("paragraph_count",0)},{c.get("event_count",0)},{c.get("interaction_count",0)},{c.get("degree_centrality",0)},{c.get("betweenness_centrality",0)},{c.get("eigenvector_centrality",0)},{c.get("community",0)},{c.get("composite_centrality",0)}\n')

    # relationships.csv
    rel_path = os.path.join(output_dir, "relationships.csv")
    with open(rel_path, "w", encoding="utf-8-sig") as f:
        f.write("rank,source,target,relationship,level,strength,co_occurrence,interaction_count,event_count\n")
        for r in relationships:
            f.write(f'{r.get("rank","")},{r["source"]},{r["target"]},{r.get("relationship","")},{r.get("level",4)},{r.get("strength",0)},{r.get("co_occurrence",0)},{r.get("interaction_count",0)},{r.get("event_count",0)}\n')

    # matrix.csv (邻接矩阵)
    matrix_path = os.path.join(output_dir, "relationship_matrix.csv")
    node_ids = [c["id"] for c in characters]
    name_map = {c["id"]: c["name"] for c in characters}
    rel_lookup = {}
    for r in relationships:
        key = tuple(sorted([r["source"], r["target"]]))
        rel_lookup[key] = r.get("strength", 0)

    with open(matrix_path, "w", encoding="utf-8-sig") as f:
        f.write("," + ",".join(name_map[nid] for nid in node_ids) + "\n")
        for src in node_ids:
            row = [name_map[src]]
            for tgt in node_ids:
                if src == tgt:
                    row.append("")
                else:
                    key = tuple(sorted([src, tgt]))
                    row.append(str(rel_lookup.get(key, "")))
            f.write(",".join(row) + "\n")


def main():
    parser = argparse.ArgumentParser(description="构建人物关系网络")
    parser.add_argument("--characters", required=True, help="characters.json 路径")
    parser.add_argument("--relationships", required=True, help="relationships.json 路径")
    parser.add_argument("--output-dir", "-o", default="./output", help="输出目录")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    with open(args.characters, "r", encoding="utf-8") as f:
        characters = json.load(f)
    with open(args.relationships, "r", encoding="utf-8") as f:
        relationships = json.load(f)

    print(f"人物数: {len(characters)}")
    print(f"关系数: {len(relationships)}")

    G = build_graph(characters, relationships)
    print(f"网络节点: {G.number_of_nodes()}, 边: {G.number_of_edges()}")

    centrality = calculate_centrality(G)
    communities = detect_communities(G)
    print(f"社区数: {len(set(communities.values()))}")

    characters = enrich_characters(characters, G, centrality, communities)
    relationships = enrich_relationships(relationships)

    # 输出 GraphML
    graphml_path = os.path.join(args.output_dir, "network.graphml")
    nx.write_graphml(G, graphml_path)
    print(f"GraphML: {graphml_path}")

    # 输出增强 JSON
    char_path = os.path.join(args.output_dir, "characters_enriched.json")
    with open(char_path, "w", encoding="utf-8") as f:
        json.dump(characters, f, ensure_ascii=False, indent=2)
    print(f"人物: {char_path}")

    rel_path = os.path.join(args.output_dir, "relationships_enriched.json")
    with open(rel_path, "w", encoding="utf-8") as f:
        json.dump(relationships, f, ensure_ascii=False, indent=2)
    print(f"关系: {rel_path}")

    # CSV
    export_csv(characters, relationships, args.output_dir)
    print(f"CSV: {args.output_dir}/characters.csv, relationships.csv, relationship_matrix.csv")

    # 摘要
    summary = {
        "total_characters": len(characters),
        "total_relationships": len(relationships),
        "total_communities": len(set(communities.values())),
        "top_20": [{"rank": c["rank"], "name": c["name"], "mention_count": c.get("mention_count", 0)} for c in characters[:20]],
        "top_20_relationships": [{"rank": r["rank"], "source": r["source"], "target": r["target"], "strength": r["strength"]} for r in relationships[:20]],
    }
    summary_path = os.path.join(args.output_dir, "network_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"摘要: {summary_path}")


if __name__ == "__main__":
    main()
