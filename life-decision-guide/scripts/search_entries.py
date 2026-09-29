"""search_entries.py — 《高性价比人生指南》条目检索

在技能内置的书正文（references/book/ 34 节，630 条建议）中按关键词检索，
输出匹配的完整条目（标题 + 成本标签 + 成本/说人话/收益/证据等级/来源/备注），
并标注出处（第几节第几条）。纯 Python 标准库，离线可用。

用法：
    python search_entries.py <关键词1> [关键词2 ...]          # OR 检索，按命中数排序
    python search_entries.py --and <关键词1> [关键词2 ...]    # AND 检索（须全部命中）
    python search_entries.py --list                          # 列出全部条目标题
    python search_entries.py --section 08 [关键词...]        # 只在第 08 节内检索
    python search_entries.py --all                           # 输出全部条目（慎用）

条目即书中的 `### N. 标题` 块，检索范围为标题、成本标签、说人话、收益、
来源、备注等整条文本；命中关键词在输出中以【】标出。
"""

import argparse
import re
import sys
from pathlib import Path

BOOK_DIR = Path(__file__).resolve().parent.parent / "references" / "book"
DOCS_DIR = Path(__file__).resolve().parent.parent / "references" / "docs"

ENTRY_RE = re.compile(r"^###\s+(\d+)\.\s*(.+)$", re.M)
SEC_RE = re.compile(r"^(\d+)-(.+)\.md$")


def parse_sections():
    """解析全部节文件 → [(节号, 节名, [条目dict])]"""
    sections = []
    for f in sorted(BOOK_DIR.glob("*.md")):
        m = SEC_RE.match(f.name)
        if not m:
            continue
        sec_no, sec_name = int(m.group(1)), m.group(2)
        text = f.read_text(encoding="utf-8")
        # 切条目：以每个 ### N. 为界
        marks = list(ENTRY_RE.finditer(text))
        entries = []
        for i, mk in enumerate(marks):
            start = mk.start()
            end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
            body = text[start:end].rstrip()
            header = mk.group(2).strip()
            tag = ""
            tm = re.search(r"<!--\s*成本标签[:：]\s*(.+?)\s*-->", body)
            if tm:
                tag = tm.group(1).strip()
            entries.append({
                "no": int(mk.group(1)),
                "title": header,
                "tag": tag,
                "body": body,
                "sec_no": sec_no,
                "sec_name": sec_name,
            })
        sections.append((sec_no, sec_name, entries))
    return sections


def iter_entries(sections):
    for sec_no, sec_name, entries in sections:
        for e in entries:
            yield e


def source_label(e):
    return f"第 {e['sec_no']} 节第 {e['no']} 条（{e['title']}）"


def highlight(text, keywords):
    for kw in keywords:
        text = re.sub(re.escape(kw), f"【{kw}】", text, flags=re.IGNORECASE)
    return text


def main():
    ap = argparse.ArgumentParser(description="《高性价比人生指南》条目检索")
    ap.add_argument("keywords", nargs="*", help="关键词（空格分隔，默认 OR）")
    ap.add_argument("--and", dest="and_mode", action="store_true", help="AND 模式：须命中全部关键词")
    ap.add_argument("--list", action="store_true", help="只列出条目标题目录")
    ap.add_argument("--section", metavar="N", help="限定节号，如 08；或节名关键词")
    ap.add_argument("--all", action="store_true", help="输出全部条目")
    ap.add_argument("--limit", type=int, default=8, help="最多输出条数（默认 8）")
    args = ap.parse_args()

    sections = parse_sections()
    all_entries = list(iter_entries(sections))

    if args.list:
        cur = None
        for e in all_entries:
            if e["sec_no"] != cur:
                cur = e["sec_no"]
                print(f"\n## 第 {e['sec_no']} 节 {e['sec_name']}")
            grade = ""
            gm = re.search(r"证据等级[:：]\s*([ABC])", e["body"])
            if gm:
                grade = f" [{gm.group(1)}]"
            print(f"  {e['no']}. {e['title']}{grade}")
        print(f"\n共 {len(all_entries)} 条")
        return

    if args.section:
        sec_pat = re.compile(re.escape(args.section))
        sections = [s for s in sections
                    if sec_pat.search(str(s[0]).zfill(2)) or sec_pat.search(s[1])]
        all_entries = list(iter_entries(sections))

    if args.all or not args.keywords:
        hits = all_entries
        keywords = []
    else:
        kws = args.keywords
        hits = []
        for e in all_entries:
            hay = e["body"]
            matched = [kw for kw in kws if kw.lower() in hay.lower()]
            if args.and_mode:
                if len(matched) == len(kws):
                    e["_score"] = sum(hay.lower().count(kw.lower()) for kw in matched)
                    hits.append(e)
            elif matched:
                e["_score"] = sum(hay.lower().count(kw.lower()) for kw in matched)
                hits.append(e)
        hits.sort(key=lambda x: -x["_score"])

    if not hits:
        print("未命中。可换关键词重试，或用 --list 浏览全部条目标题。")
        return

    for e in hits[: args.limit]:
        print("=" * 60)
        print(f"出处：{source_label(e)}")
        if e["tag"]:
            print(f"成本标签：{e['tag']}")
        print(highlight(e["body"], args.keywords))
        print()
    if len(hits) > args.limit:
        print(f"... 另有 {len(hits) - args.limit} 条命中未显示（--limit 调整）")


if __name__ == "__main__":
    main()
