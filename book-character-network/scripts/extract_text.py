#!/usr/bin/env python3
"""
extract_text.py — 从 PDF/EPUB/DOCX/TXT 提取纯文本并分章分段

用法:
    python extract_text.py <input_file> [--output <output.json>]

输出 JSON 结构:
{
  "source": "book.pdf",
  "total_chars": 120000,
  "total_paragraphs": 850,
  "chapters": [
    {
      "index": 0,
      "title": "第一章 ...",
      "pages": [1, 2, 3],
      "paragraphs": [
        {"index": 0, "text": "..."},
        ...
      ]
    }
  ],
  "flat_paragraphs": [
    {"chapter_index": 0, "paragraph_index": 0, "text": "..."},
    ...
  ]
}
"""

import argparse
import json
import os
import re
import sys


# ── 文本提取 ──────────────────────────────────────────────

def extract_pdf(path: str) -> list[tuple[int, str]]:
    """返回 [(page_number, text), ...]"""
    import fitz  # PyMuPDF
    pages = []
    with fitz.open(path) as doc:
        for i, page in enumerate(doc):
            text = page.get_text()
            pages.append((i + 1, text))
    return pages


def extract_epub(path: str) -> list[tuple[int, str]]:
    """返回 [(chapter_number, text), ...]"""
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup

    book = epub.read_epub(path)
    chapters = []
    idx = 0
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        if text.strip():
            idx += 1
            chapters.append((idx, text))
    return chapters


def extract_docx(path: str) -> list[tuple[int, str]]:
    """返回 [(paragraph_number, text), ...]"""
    from docx import Document
    doc = Document(path)
    paragraphs = []
    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        if text:
            paragraphs.append((i, text))
    return paragraphs


def extract_txt(path: str) -> list[tuple[int, str]]:
    """返回 [(line_number, text), ...]  按非空行"""
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        lines = f.readlines()
    paragraphs = []
    buf = []
    buf_start = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped:
            if not buf:
                buf_start = i
            buf.append(stripped)
        else:
            if buf:
                paragraphs.append((buf_start, "\n".join(buf)))
                buf = []
    if buf:
        paragraphs.append((buf_start, "\n".join(buf)))
    return paragraphs


def detect_format(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return "pdf"
    elif ext == ".epub":
        return "epub"
    elif ext == ".docx":
        return "docx"
    elif ext in (".txt", ".md"):
        return "txt"
    else:
        raise ValueError(f"不支持的文件格式: {ext}")


def extract(path: str) -> list[tuple[int, str]]:
    fmt = detect_format(path)
    if fmt == "pdf":
        return extract_pdf(path)
    elif fmt == "epub":
        return extract_epub(path)
    elif fmt == "docx":
        return extract_docx(path)
    else:
        return extract_txt(path)


# ── 章节检测 ──────────────────────────────────────────────

CHAPTER_PATTERNS = [
    re.compile(r"^第[一二三四五六七八九十百千零〇\d]+[章节回卷部篇]", re.MULTILINE),
    re.compile(r"^Chapter\s+\d+", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\d+[\.\s]", re.MULTILINE),
]


def detect_chapters(pages: list[tuple[int, str]]) -> list[dict]:
    """
    将 (page_num, text) 列表按章节切分。
    每个章节包含 title, pages, paragraphs。
    """
    chapters = []
    current_chapter = {
        "index": 0,
        "title": "序言/前言",
        "pages": [],
        "paragraphs": [],
    }
    chapter_idx = 0

    for page_num, text in pages:
        lines = text.split("\n")
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue

            # 检测章节标题
            is_chapter_start = False
            for pat in CHAPTER_PATTERNS:
                if pat.match(line_stripped):
                    is_chapter_start = True
                    break

            if is_chapter_start and current_chapter["paragraphs"]:
                chapters.append(current_chapter)
                chapter_idx += 1
                current_chapter = {
                    "index": chapter_idx,
                    "title": line_stripped,
                    "pages": [page_num],
                    "paragraphs": [],
                }
            else:
                if line_stripped not in current_chapter["pages"]:
                    if page_num not in current_chapter["pages"]:
                        current_chapter["pages"].append(page_num)
                    current_chapter["paragraphs"].append({
                        "index": len(current_chapter["paragraphs"]),
                        "text": line_stripped,
                    })

    if current_chapter["paragraphs"]:
        chapters.append(current_chapter)

    return chapters


def build_flat_paragraphs(chapters: list[dict]) -> list[dict]:
    flat = []
    for ch in chapters:
        for para in ch["paragraphs"]:
            flat.append({
                "chapter_index": ch["index"],
                "chapter_title": ch["title"],
                "paragraph_index": para["index"],
                "text": para["text"],
            })
    return flat


# ── 主入口 ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="提取书籍文本并分章分段")
    parser.add_argument("input", help="输入文件路径 (PDF/EPUB/DOCX/TXT)")
    parser.add_argument("--output", "-o", default=None, help="输出 JSON 路径")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"错误: 文件不存在: {args.input}", file=sys.stderr)
        sys.exit(1)

    print(f"正在提取文本: {args.input}")
    pages = extract(args.input)
    print(f"提取完成，共 {len(pages)} 个页面/段落")

    chapters = detect_chapters(pages)
    print(f"检测到 {len(chapters)} 个章节")

    flat = build_flat_paragraphs(chapters)
    total_chars = sum(len(p["text"]) for p in flat)

    result = {
        "source": os.path.basename(args.input),
        "total_chars": total_chars,
        "total_paragraphs": len(flat),
        "total_chapters": len(chapters),
        "chapters": chapters,
        "flat_paragraphs": flat,
    }

    if args.output is None:
        base = os.path.splitext(args.input)[0]
        args.output = base + "_parsed.json"

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"输出: {args.output}")
    print(f"总字数: {total_chars}")
    print(f"总段落: {len(flat)}")
    print(f"总章节: {len(chapters)}")


if __name__ == "__main__":
    main()
