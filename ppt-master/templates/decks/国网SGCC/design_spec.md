---
deck_id: 国网SGCC
kind: deck
summary: 国家电网 SGCC 品牌模板 — 青绿色系 + 方正细黑标题，适合能源/电力/央企汇报
canvas_format: ppt169
page_count: 5
primary_color: "#2B9574"
replication_mode: standard
---

# 国家电网 SGCC - Design Specification

## I. Template Overview

**用途**：国家电网（State Grid Corporation of China, SGCC）品牌汇报模板，适用于能源、电力、央企内部汇报场景。

**设计意图**：逆向工程自 SGCC 官方 PPTX 模板（28 页 16:9），提取品牌身份（青绿色系 + 方正细黑标题 + SGCC Logo）与页面结构（封面/目录/章节/内容/封底），重建为 5 页含 `{{PLACEHOLDER}}` 占位符的可复用 SVG 模板。

**适用内容**：电力行业分析、综合能源汇报、新能源板块经营分析、央企年度总结等。

**源文件**：`国网SGCC模版.pptx`（17.85 MB，28 页，2024-08-31 修改）

---

## II. Canvas Specification

| 属性 | 值 |
|------|-----|
| **格式** | PPT 16:9 |
| **画布尺寸** | 1280×720 px |
| **viewBox** | `0 0 1280 720` |
| **安全边距** | 左右 60px，上下 50px |
| **内容区** | 1160×620（安全区） |

---

## III. Color Scheme

品牌色提取自源 PPTX 形状实际填充色（非 OOXML 主题，主题为标准 Office 配色）。

| 角色 | HEX | 用途 | 出现频次 |
|------|-----|------|---------|
| **primary** | `#2B9574` | 主色 — 标题栏、装饰条、图标 | 73 次 |
| **primary_dark** | `#00706B` | 深色 — 章节页装饰、强调 | 39 次 |
| **primary_alt** | `#187A79` | 深色变体 — 辅助装饰 | 43 次 |
| **primary_bright** | `#009882` | 亮色 — 高亮、激活态 | 21 次 |
| **primary_light** | `#ACE7D4` | 浅色 — 背景、描边 | 5 次 |
| **accent_red** | `#C00000` | 强调红 — 警示、负向指标 | 13 次 |
| **background** | `#FFFFFF` | 页面背景（内容页/目录页） |
| **text** | `#333333` | 正文文字 |
| **text_secondary** | `#666666` | 注释、说明 |
| **text_on_primary** | `#FFFFFF` | 主色块上的白字 |
| **border** | `#E0E0E0` | 分隔线、边框 |

---

## IV. Typography

| 角色 | 字体栈 | 权重 | 备注 |
|------|--------|------|------|
| **标题** | `"方正细黑", "FZXiHei", "Microsoft YaHei", sans-serif` | Bold | 方正细黑需安装或 PPTX 嵌入；fallback 微软雅黑 |
| **正文** | `"Microsoft YaHei", "PingFang SC", sans-serif` | Regular | 微软雅黑，Windows 预装 |
| **英文** | `"Franklin Gothic Medium", "Arial", sans-serif` | Medium | 英文标题/数字 |
| **强调** | `"方正细黑", "FZXiHei", "Microsoft YaHei", sans-serif` | Bold | 与标题同族 |

---

## V. Logo

| 文件 | 用途 | 尺寸 |
|------|------|------|
| `logo_white.png` | SGCC Logo（白色版），封面左上 + 封底居中 | 42KB |

**使用规则**：
- 封面：左上角，距边 60px，高度约 50px
- 封底：水平居中，高度约 60px
- 保持 Logo 比例，不拉伸变形
- Logo 下方留 20px 间距

---

## VI. Page Structure

### 通用结构
- **顶部标题栏**（内容页）：高 80px，`#2B9574` 色块 + 白字标题
- **右上角装饰**（内容页）：几何线条组，`#00706B` 描边
- **内容区**：顶部标题栏下方，高 540px
- **底部页码**：右下角，`#666666` 小字

### 页面网格
- 内容区采用 12 列网格，列宽 88px，间距 16px
- 卡片间距 24px
- 段落间距 16px

---

## VII. Page Types

### 01_cover（封面）
- 全幅背景图 `cover_bg.png`
- 半透明深色遮罩（底部 40% 高度）
- SGCC Logo 左上角
- 大字标题（方正细黑，白色）居中偏下
- 副标题 + 日期底部

### 02_toc（目录）
- 白色背景
- 左侧青绿色装饰竖条（`#2B9574`，宽 8px，通栏）
- "目录 / CONTENTS" 标题顶部
- 4 个章节条目（编号 + 标题），每条含青绿色编号块

### 02_chapter（章节分隔）
- 白色背景
- 右上角圆形装饰（`#00706B` 实心圆 + `#ACE7D4` 描边环）
- 左侧横幅条（`#2B9574`，宽 120px）
- 大编号（方正细黑，`#2B9574`）
- 章节标题（方正细黑，深色）

### 03_content（内容页）
- 白色背景
- 顶部标题栏（`#2B9574` 色块，高 80px，白字标题）
- 右上角装饰组（几何线条，`#00706B`）
- 内容区（标题 + 正文占位符）
- 底部右下页码

### 04_ending（封底）
- 全幅背景图 `ending_bg.jpeg`
- 半透明深色遮罩
- SGCC Logo 水平居中
- "感谢聆听"大字（方正细黑，白色）
- 联系信息小字底部

---

## VIII. SVG Page Roster

| 文件 | 页型 | 用途 |
|------|------|------|
| `01_cover.svg` | cover | 封面 — 全幅背景 + Logo + 标题 |
| `02_toc.svg` | toc | 目录 — 4 章节条目 |
| `02_chapter.svg` | chapter | 章节分隔 — 圆形装饰 + 横幅 |
| `03_content.svg` | content | 内容页 — 标题栏 + 内容区 |
| `04_ending.svg` | ending | 封底 — 背景 + Logo + 致谢 |

---

## IX. Placeholder Convention

模板使用 `{{PLACEHOLDER}}` 标记可替换内容：

| 占位符 | 用于 | 示例 |
|--------|------|------|
| `{{TITLE}}` | 封面主标题 | "2024年度经营分析报告" |
| `{{SUBTITLE}}` | 封面副标题 | "综合能源板块" |
| `{{DATE}}` | 封面日期 | "2024.12" |
| `{{CHAPTER_01}}` ... `{{CHAPTER_04}}` | 目录章节标题 | "一、行业概览" |
| `{{CHAPTER_NUMBER}}` | 章节页编号 | "01" |
| `{{CHAPTER_TITLE}}` | 章节页标题 | "行业概览" |
| `{{PAGE_TITLE}}` | 内容页标题 | "市场规模分析" |
| `{{CONTENT_HEADING}}` | 内容区小标题 | "核心发现" |
| `{{CONTENT_BODY}}` | 内容区正文 | "..." |
| `{{PAGE_NUMBER}}` | 页码 | "03" |
| `{{THANK_YOU}}` | 封底致谢 | "感谢聆听" |
| `{{CONTACT_INFO}}` | 封底联系信息 | "联系方式" |

---

## X. SVG Technical Constraints

- viewBox: `0 0 1280 720`
- 纯 HEX 颜色，禁 `rgba()`
- 禁 `<style>`、`class`、`<foreignObject>`、`mask`、`textPath`、`@font-face`、`<script>`
- 文字用 raw Unicode（`—`、`→`），禁 HTML 实体（`&mdash;` 等）
- XML 保留字转义：`&` → `&amp;`、`<` → `&lt;`、`>` → `&gt;`
- `<image>` 用相对路径 `href="cover_bg.png"`
- 字体栈含 fallback：方正细黑 → 微软雅黑
