---
name: rmrb-fetch
description: 抓取人民日报数字报（人民网 paper.people.com.cn）历史报纸全文并按日保存为 Markdown。支持任意日期单篇抓取、日期范围批量抓取（断点续传）、正文词频统计。当用户要求抓取人民日报、下载人民日报历史数据、建立人民日报语料库/文本库、统计某个词在人民日报的出现次数（如"习近平"词频）时使用。Fetch People's Daily (Renmin Ribao) digital newspaper archive from paper.people.com.cn and save daily issues as Markdown files; supports single-day fetch, batch range fetch with resume, and word-frequency statistics.
agent_created: true
---

# 人民日报数字报抓取（rmrb-fetch）

## 概述

抓取人民日报数字报历史档案（paper.people.com.cn）全文，按日生成 Markdown 文件。数据源页面标题为"人民日报图文数据库(1946-2026)"，实测 2023-2025 全年均可访问。脚本无第三方依赖（仅 Python 标准库），跨平台可运行。

## 环境要求

- Python 3（脚本只用 `urllib.request`、`re`、`os`、`sys`、`datetime` 等标准库，无需 pip 安装任何包）

## 快速开始

### 1. 抓取单日（生成一个 md 文件）

```bash
python scripts/fetch_rmrb.py 2025-08-10
```

- 输出：`人民日报_2025-08-10.md`（与脚本同目录，自动命名 `人民日报_YYYY-MM-DD.md`）
- 每个文件包含：日期标题（含星期）、来源说明、版面数/文章数统计、按版面分节（`## 第01版：要闻`）、按篇排列（`### 1. 标题` + 斜体副标题 + 正文全文）
- 图片类报道正文为空时自动以"（图片报道或内容暂缺）"占位

### 2. 批量抓取日期范围（支持断点续传）

```bash
python scripts/batch_fetch.py 2023-01-01 2023-12-31
```

- 逐日调用 `fetch_rmrb.py`，每天生成一个 md 文件
- **断点续传**：已存在且有效（≥1个版面且≥1篇文章）的文件自动跳过（日志标记 `SKIP(已有)`），中断后直接重跑同一命令即可续传，不会重复抓取
- 单日失败自动重试 3 次，全部失败该日标记 `FAIL`（可稍后单独补抓该日）
- 批量前可先单日测试确认数据源可访问

### 3. 词频统计（如统计"习近平"出现次数）

统计口径：`txt.count("习近平")`（子串计数），按日读取 md 文件统计。产出 CSV（UTF-8 BOM + `日期,习近平出现次数`），与 Excel 直接兼容：

```python
import os, datetime
WORD = "习近平"
d = datetime.date(2023, 1, 1)
while d <= datetime.date(2023, 12, 31):
    ds = d.strftime("%Y-%m-%d")
    txt = open("人民日报_%s.md" % ds, encoding="utf-8").read()
    print(ds, txt.count(WORD))
    d += datetime.timedelta(days=1)
```

跨年份对比注意：按月对比时用月份 `ds[5:7]` 作键，勿用完整年月（"2023-01" 与 "2024-01" 键不同）。若某年档案缺失月份（如2024年12月），统一用同期口径（如1-11月）对比。

## URL 结构（新旧两版，脚本自动检测）

人民网数字报约在 2025 年改版，`fetch_rmrb.py` 对每个版面先试新版 URL，404 则自动回退旧版：

| | 旧版（≤2024） | 新版（≥2025） |
|---|---|---|
| 版面页 | `rmrb/html/YYYY-MM/DD/nbs.D110000renmrb_0N.htm` | `rmrb/pc/layout/YYYYMM/DD/node_0N.html` |
| 文章页 | `rmrb/html/YYYY-MM/DD/nw.D110000renmrb_YYYYMMDD_X-Y.htm` | `rmrb/pc/content/YYYYMM/DD/content_XXXX.html` |
| 版面页内容 | 列出全报各版文章链接 | 只列本版文章（content_ID） |

- 文章 ID 规则（旧版）：`nw.D110000renmrb_YYYYMMDD_X-Y.htm`，**X=该版面内文章序号，Y=版面号**（易错点：勿把 X 当版面号）
- 正文提取：标题取 `<h1>`，副标题取 `<h2>`，正文在隐藏 `div#articleContent` 内的 `<!--enpcontent-->` 注释块中（新旧版通用）

## 批量抓取性能与加速

- 单日约 18~40 秒（旧版版面页需跨版解析，新版更快），全年 365 天串行约 2~3.5 小时
- **加速方法**：将日期范围拆成多段并行运行（每段一个后台 `batch_fetch.py` 进程，日志分开），如 4 路并行可提速约 4 倍。实测 4 路并行（每天每路约 20 秒）无封禁问题
- 建议每段覆盖 2 个月左右，避免单进程过长

## 常见问题与故障排查

| 现象 | 原因 | 处理 |
|---|---|---|
| 某日 0 版面 0 文章，文件仅 159 字节 | 该日期档案不存在（404）或 URL 改版未适配 | 用浏览器/curl 直接访问版面页确认 HTTP 状态；新版 URL 用 `pc/layout` 格式 |
| 全文抓取后文件只有标题无正文 | 图片报道/导读类条目，enpcontent 为空 | 正常现象，脚本以占位文本标注 |
| 批量中断后想续跑 | — | 直接重跑 `batch_fetch.py` 同一命令，已有有效文件自动跳过 |
| Windows 下停止后台抓取任务 | Git Bash 的 `taskkill //PID` 语法易失败 | 用 PowerShell `Stop-Process -Id <真实PID> -Force`；ps 显示的 msys PID 与 Windows 真实 PID 不同，先用 `tasklist` 确认真实 PID |
| 大量并发请求被限流 | 请求速率过高 | 控制并行路数（≤6 路），脚本本身已内置失败重试 3 次 |

## 档案边界注意事项

- 实测 2023 全年、2025 全年均可访问；2024 年档案至 11-30（12 月 404，疑似当年年末未入库）
- 工作区若有其他来源的既有 md 文件（非本站抓取），勿覆盖
- 站点版权声明：内容仅供阅读、学习研究使用，勿用于商业用途

## 资源

### scripts/
- `fetch_rmrb.py` — 单日抓取脚本（含新旧版 URL 自动检测）
- `batch_fetch.py` — 日期范围批量抓取（断点续传、失败重试）
