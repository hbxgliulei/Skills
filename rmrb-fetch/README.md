# rmrb-fetch — 人民日报数字报抓取技能

抓取人民日报数字报（人民网 paper.people.com.cn）历史报纸全文，按日保存为 Markdown 文件。数据源实测覆盖 2023–2025 全年，脚本自动适配新旧两版 URL 结构。

## 功能

- **单日抓取**：`fetch_rmrb.py 2025-08-10` → `人民日报_2025-08-10.md`
- **批量抓取**：`batch_fetch.py 2023-01-01 2023-12-31` → 逐日生成 md，支持**断点续传**与失败重试
- **词频统计**：按日统计任意词出现次数（如"习近平"），产出与 Excel 兼容的 CSV
- **零依赖**：仅用 Python 标准库

## 快速开始

```bash
# 单日
python scripts/fetch_rmrb.py 2025-08-10

# 批量（可中断后重跑续传）
python scripts/batch_fetch.py 2023-01-01 2023-12-31

# 加速：按月份分段并行运行多个批量进程，日志分开
```

## 输出格式

```
# 人民日报 2025年8月10日（星期日）
> 来源：人民日报数字报（paper.people.com.cn）
> 共 20 个版面，收录文章 108 篇

## 第01版：要闻
### 1. 文章标题
*副标题*
正文全文……
```

## URL 结构（脚本自动检测）

| | 旧版（≤2024） | 新版（≥2025） |
|---|---|---|
| 版面页 | `rmrb/html/YYYY-MM-DD/nbs.D110000renmrb_0N.htm` | `rmrb/pc/layout/YYYYMM/DD/node_0N.html` |
| 文章页 | `rmrb/html/.../nw.D110000renmrb_YYYYMMDD_X-Y.htm` | `rmrb/pc/content/YYYYMM/DD/content_XXXX.html` |

## 目录结构

```
rmrb-fetch/
├── SKILL.md              # 技能说明与详细使用方法
└── scripts/
    ├── fetch_rmrb.py     # 单日抓取（新旧URL自动检测）
    └── batch_fetch.py    # 批量抓取（断点续传、失败重试）
```

## 免责声明

本技能抓取的数据仅供个人阅读、学习研究使用，请遵守人民网版权声明，勿用于商业用途。
