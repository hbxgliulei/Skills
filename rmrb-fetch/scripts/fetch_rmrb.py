# -*- coding: utf-8 -*-
"""Fetch 人民日报 for a given date and assemble Markdown.

Usage: python fetch_rmrb.py [YYYY-MM-DD]   (default: 2025-08-10)

Supports both URL generations (auto-detect per 版面):
  OLD (<=2024): nbs.D110000renmrb_0N.htm / nw.D110000renmrb_YYYYMMDD_X-Y.htm
  NEW (>=2025): pc/layout/YYYYMM/DD/node_0N.html / pc/content/YYYYMM/DD/content_XXXX.html
Body lives in <!--enpcontent--> inside hidden div#articleContent (both gens).
"""
import urllib.request, re, sys, time, datetime, os

DATE = sys.argv[1] if len(sys.argv) > 1 else "2025-08-10"
_y, _m, _d = DATE.split("-")
YM = _y + _m
BASE_OLD = "http://paper.people.com.cn/rmrb/html/%s-%s/%s/" % (_y, _m, _d)
BASE_NEW = "http://paper.people.com.cn/rmrb/pc/layout/%s/%s/" % (YM, _d)
ARTICLE_PREFIX = "nw.D110000renmrb_%s%s%s" % (_y, _m, _d)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

def fetch(url, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read()
            for enc in ("utf-8", "gbk", "gb18030"):
                try:
                    return raw.decode(enc)
                except UnicodeDecodeError:
                    continue
            return raw.decode("utf-8", errors="replace")
        except Exception as e:
            if i == retries - 1:
                return None
            time.sleep(1.0)

def clean_text(s):
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"</p>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = (s.replace("&nbsp;", " ").replace("&ensp;", " ")
           .replace("&ldquo;", "\u201c").replace("&rdquo;", "\u201d")
           .replace("&lsquo;", "\u2018").replace("&rsquo;", "\u2019")
           .replace("&middot;", "\u00b7").replace("&hellip;", "\u2026")
           .replace("&mdash;", "\u2014").replace("&amp;", "&"))
    lines = [re.sub(r"[ \t\u3000]+", " ", ln).strip() for ln in s.split("\n")]
    return "\n".join(ln for ln in lines if ln)

def sec_name(html, n):
    """提取第 n 版版面名（新/旧版通用）。"""
    for m in re.finditer(r"0?%d版[：:]\s*([^<\"&]{1,20})" % n, html):
        nm = m.group(1).strip()
        if nm and not any(c in nm for c in "\r\n\t"):
            return nm
    return None

# ---- Step 1: per-版面 index pages -> article list + 版面 name ----
sections = {}  # n(int) -> {"name":str, "articles":[(key,url)]}
for n in range(1, 30):
    html = fetch(BASE_NEW + "node_%02d.html" % n)
    if html is not None:
        # 新版：版面页即该版文章列表
        ids = sorted(set(re.findall(r"content_(\d+)\.html", html)))
        arts = [("c%s" % i, "http://paper.people.com.cn/rmrb/pc/content/%s/%s/content_%s.html" % (YM, _d, i))
                for i in ids]
        name = sec_name(html, n)
        if not arts:
            break
        sections[n] = {"name": name or "（未命名）", "articles": arts}
        print("版面%02d %s: %d 篇 [NEW]" % (n, name, len(arts)), file=sys.stderr)
        continue
    # 旧版
    html = fetch(BASE_OLD + "nbs.D110000renmrb_%02d.htm" % n)
    if html is None:
        break  # no more 版面
    name = sec_name(html, n)
    links = re.findall(r'href=(' + re.escape(ARTICLE_PREFIX) + r'_(\d+)-(\d+)\.htm)', html)
    if not links:
        break
    arts = []
    seen = set()
    for _, xs, ys in links:
        x = int(xs); y = int(ys)
        if y != n:
            continue
        if x in seen:
            continue
        seen.add(x)
        arts.append((x, BASE_OLD + ARTICLE_PREFIX + "_%d-%02d.htm" % (x, y)))
    if not arts:
        break
    sections[n] = {"name": name or "（未命名）", "articles": arts}
    print("版面%02d %s: %d 篇 [OLD]" % (n, name, len(arts)), file=sys.stderr)

n_sections = len(sections)
total_urls = sum(len(s["articles"]) for s in sections.values())
print("共 %d 个版面，%d 篇文章" % (n_sections, total_urls), file=sys.stderr)

# ---- Step 2: fetch each article ----
for y in sorted(sections):
    sec = sections[y]
    fetched = []
    for x, url in sorted(sec["articles"]):
        html = fetch(url)
        if html is None:
            fetched.append((x, "(抓取失败)", "", ""))
            continue
        tm = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
        title = clean_text(tm.group(1)).strip() if tm else "(无标题)"
        sm = re.search(r"<h2[^>]*>(.*?)</h2>", html, re.S)
        subtitle = clean_text(sm.group(1)).strip() if sm else ""
        body = ""
        em = re.search(r"<!--enpcontent-->(.*?)</div>\s*</div>", html, re.S)
        if em:
            body = clean_text(em.group(1)).strip()
        else:
            em = re.search(r'id="articleContent"[^>]*>(.*?)</div>', html, re.S)
            if em:
                body = clean_text(em.group(1)).strip()
        fetched.append((x, title, subtitle, body))
        time.sleep(0.1)
    sec["fetched"] = fetched
    print("  版面%02d 抓取完成" % y, file=sys.stderr)

# ---- Step 3: assemble markdown ----
dt = datetime.date(int(_y), int(_m), int(_d))
weekday = ["星期一","星期二","星期三","星期四","星期五","星期六","星期日"][dt.weekday()]
total_arts = sum(len(s["fetched"]) for s in sections.values())

out = []
out.append("# 人民日报 %d年%d月%d日（%s）" % (dt.year, dt.month, dt.day, weekday))
out.append("")
out.append("> 来源：人民日报数字报（paper.people.com.cn）")
out.append(">")
out.append("> 共 **%d** 个版面，收录文章 **%d** 篇" % (n_sections, total_arts))
out.append("")
out.append("---")
out.append("")

for y in sorted(sections):
    sec = sections[y]
    out.append("## 第%02d版：%s" % (y, sec["name"]))
    out.append("")
    for idx, (x, title, subtitle, body) in enumerate(sorted(sec["fetched"]), 1):
        out.append("### %d. %s" % (idx, title))
        out.append("")
        if subtitle:
            out.append("*%s*" % subtitle)
            out.append("")
        out.append(body if body else "（图片报道或内容暂缺）")
        out.append("")
    out.append("")

text = "\n".join(out)
outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "人民日报_%s.md" % DATE)
with open(outpath, "w", encoding="utf-8") as f:
    f.write(text)
print("WROTE", outpath, "bytes=", len(text.encode("utf-8")), file=sys.stderr)
