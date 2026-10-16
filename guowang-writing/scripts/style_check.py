# -*- coding: utf-8 -*-
"""国网公文风格自检脚本（guowang-writing skill）

用法:
    python style_check.py <文件路径> [更多文件...]
    python style_check.py -            # 从标准输入读取

检查项:
    A 半角标点混用        B 直引号（非中文引号）
    C 单位不规范/混用     D 条目结构（一是/二是成组性）
    E 段落过长            F 结尾收束句
    G 数字与中文间多余空格

说明: 本脚本只做确定性检查，用于辅助人工复核；提示项需结合语境判断。
"""
import re
import sys

CJK = r"[\u4e00-\u9fff]"

PATTERNS = [
    ("A1 半角逗号/分号/冒号", re.compile(CJK + r"\s*[,;:]"), "中文后应使用全角标点（，；：）"),
    ("A2 半角问号/叹号", re.compile(CJK + r"\s*[!?]|[!?]" + r"\s*" + CJK), "中文语境应使用全角，正式件一般不用感叹号"),
    ("A3 半角括号", re.compile(r"\([^)]{0,40}" + CJK + r"[^)]{0,40}\)|" + CJK + r"\s*\(|\)\s*" + CJK), "中文语境括号应使用全角（）"),
    ("B 直引号", re.compile(r'["\']\s*' + CJK + r"|" + CJK + r'\s*["\']'), "应使用中文引号“”‘’"),
]

UNIT_RULES = [
    ("C1 电量单位", re.compile(r"\d\s*万?度(?!量)|\d\s*度电|千瓦小时|多少度"), "应使用 千瓦时/万千瓦时/亿千瓦时"),
    ("C2 英制单位混用", re.compile(r"kWh|KWH|kwh"), "正文宜用“千瓦时”；设备规格参数（如 125kW/261kWh）可保留"),
    ("C3 功率单位写法", re.compile(r"\bKW\b|千瓦KW"), "规范写法：kW（小写 k、大写 W）"),
    ("C4 功率单位混用", re.compile(r"兆瓦.{0,30}?千瓦(?!时)|千瓦(?!时).{0,30}?兆瓦"), "同句避免 兆瓦 与 千瓦 混用"),
]

ORDER = ["一是", "二是", "三是", "四是", "五是", "六是", "七是", "八是", "九是", "十是"]
ITEM_SPLIT = re.compile(
    r"(?=(?:一是|二是|三是|四是|五是|六是|七是|八是|九是|十是)|[一二三四五六七八九十]{1,2}、|（[一二三四五六七八九十]{1,2}）)"
)
CLOSING_WORDS = ["奠定", "贡献", "保障", "请总部放心", "恳请", "建议", "确保", "实效", "创造条件",
                 "以上报告", "请予审议", "汇报", "落实", "推进", "工作"]


def split_paragraphs(text):
    """拆分段落；对超长紧排段落（无空行的提取文本）再按条目/章节切分。"""
    paras = []
    for raw in re.split(r"\n\s*\n|\n", text):
        line = raw.strip()
        if not line:
            continue
        if line.startswith(("#", "|", "```", ">", "- ", "* ")):
            continue
        if re.match(r"^[\d\s.、（）()]+$", line):
            continue
        if line.count("|") > 1:
            continue
        if len(line) > 400:
            parts = [p.strip() for p in ITEM_SPLIT.split(line) if p.strip()]
            if len(parts) > 1:
                paras.extend(parts)
                continue
        paras.append(line)
    return paras


def scan(text):
    issues = []

    # A/B 标点
    for label, rx, msg in PATTERNS:
        for i, line in enumerate(text.splitlines(), 1):
            if line.strip().startswith(("|", "```")):
                continue
            if rx.search(line):
                issues.append((label, i, msg, line.strip()[:60]))

    # C 单位
    for label, rx, msg in UNIT_RULES:
        for i, line in enumerate(text.splitlines(), 1):
            if rx.search(line):
                issues.append((label, i, msg, line.strip()[:60]))

    paras = split_paragraphs(text)

    # D 条目结构
    item_paras = [p for p in paras if any(p.startswith(k) for k in ORDER)]
    counts = {k: sum(1 for p in item_paras if p.startswith(k)) for k in ORDER}
    if item_paras:
        summary = "、".join(f"{k}×{counts[k]}" for k in ORDER if counts[k])
        print(f"[信息] 条目统计: {summary}")
    if counts["一是"] and not counts["二是"]:
        issues.append(("D1 条目不成组", 0, "出现“一是”但全文无“二是”，条目应成组（≥3条）",
                       next(p for p in item_paras if p.startswith("一是"))[:60]))
    for i, p in enumerate(item_paras):
        if p.startswith("一是"):
            window = item_paras[i + 1:i + 7]
            if window and not any(w.startswith("二是") for w in window):
                issues.append(("D1 条目不成组", 0, "“一是…”条目后未见对应的“二是”条目", p[:60]))
    for p in item_paras:
        if re.match(r"^一是[，。]", p):
            issues.append(("D2 条目缺概括短语", 0, "“一是”后直接接标点，应先给概括短语", p[:60]))

    # E 段落过长
    for b in paras:
        body = re.sub(r"\s", "", b)
        if len(body) > 800:
            issues.append(("E 段落过长", 0, f"单段 {len(body)} 字，建议拆分（兼顾领导阅读体验）", body[:60]))

    # F 结尾收束
    if paras:
        tail = "".join(paras[-3:])
        if not any(w in tail for w in CLOSING_WORDS):
            issues.append(("F 结尾收束", 0, "文末未见表态/总括/请求类收束句，请人工确认", tail[-60:]))

    # G 数字空格（PDF 复制文本常成片出现，超阈值则聚合为一条）
    g_hits = []
    for i, line in enumerate(text.splitlines(), 1):
        if re.search(r"\d\s+[万亿千百]|\d\s+(元|户|项|个|台|座|家)", line):
            g_hits.append((i, line.strip()[:60]))
    if len(g_hits) > 15:
        issues.append(("G 数字空格", 0,
                       f"全文发现 {len(g_hits)} 处数字与单位间空格（疑似 PDF 复制产生的伪影），建议整体清理",
                       g_hits[0][1]))
    else:
        for i, snippet in g_hits:
            issues.append(("G 数字空格", i, "数字与单位间不应有多余空格", snippet))

    return issues


def report(name, text):
    issues = scan(text)
    print(f"\n===== 风格自检: {name} =====")
    print(f"正文约 {len(re.sub(r'[	\s]', '', text))} 字，发现 {len(issues)} 条提示")
    if not issues:
        print("未发现机器可检的风格问题（仍需人工复核语言分寸与数据准确性）。")
        return 0
    for label, line, msg, snippet in issues:
        loc = f"第{line}行" if line else "全文"
        print(f"[{label}] {loc}: {msg}")
        print(f"    → {snippet}")
    print("\n提示：A/C/G 类通常应直接修正；D/E/F 类需结合文种与语境判断。")
    return len(issues)


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    for path in args:
        if path == "-":
            report("(stdin)", sys.stdin.read())
        else:
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                    text = fh.read()
            except OSError as e:
                print(f"无法读取 {path}: {e}")
                continue
            report(path, text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
