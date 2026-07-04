# gongwen-paiban — 公文自动排版

WorkBuddy 技能包，按行文基本格式标准对 Word 文档进行格式化（字体使用方正系列：小标宋/仿宋/黑体/楷体_GBK）。

## 功能

- **Reformat 模式**：已有 docx 文件 → 自动识别标题层级 → 按标准重排
- **Create 模式**：从 Markdown/文本 → 直接生成符合标准的公文

## 排版标准

| 层级 | 字体 | 字号 | 加粗 | 缩进 | 对齐 |
|------|------|------|------|------|------|
| 大标题 | 方正小标宋_GBK | 二号 22pt | 是 | 居中 | 段前段后各一空行 |
| 一级标题 | 方正黑体_GBK | 三号 16pt | 是 | 2字符 | 左对齐 |
| 二级标题 | 方正楷体_GBK | 三号 16pt | 是 | 2字符 | 左对齐 |
| 三级标题 | 方正仿宋_GBK | 三号 16pt | 否 | 2字符 | 左对齐 |
| 正文 | 方正仿宋_GBK | 三号 16pt | 否 | 2字符 | 两端对齐 |

页边距：上 3.7cm / 下 3.5cm / 左 2.8cm / 右 2.6cm，28pt 固定行距。

## 安装

### 1. 复制文件

将整个文件夹放入 WorkBuddy 技能目录：

```
~/.workbuddy/skills/gongwen-paiban/
├── SKILL.md
├── scripts/
│   └── create_official.js
└── references/
    └── gb9704-spec.md
```

### 2. 安装依赖

```bash
# Python 依赖（Reformat 模式）
pip install lxml defusedxml

# Node.js 依赖（Create 模式）
cd ~/.workbuddy/binaries/node/workspace
npm install docx
```

### 3. 确保 docx skill 已安装

Reformat 模式依赖 WorkBuddy 内置的 `docx` skill（提供 unpack/pack 工具链）。

## 使用

```
/gongwen-paiban @"中国碳市场发展历程.docx"
```

触发词：公文排版、公文格式化、按标准排版、行文格式

## 字体说明

依赖方正系列字体（方正小标宋_GBK、方正仿宋_GBK、方正黑体_GBK、方正楷体_GBK）。Windows 部分自带，小标宋可能需单独安装。字体缺失时 Word/WPS 会回退为默认宋体。
