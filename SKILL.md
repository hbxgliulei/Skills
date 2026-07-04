---
name: gongwen-paiban
agent_created: true
description: 公文自动排版。按行文基本格式标准对 Word 文档进行格式化（字体使用方正系列：小标宋/仿宋/黑体/楷体_GBK）。支持从 Markdown/文本创建新公文，也支持对已有 docx 文件重新排版。触发词：公文排版、公文格式化、按标准排版、行文格式、公文标准排版。如需 GB/T 9704-2012 国标版，引用 references/gb9704-spec.md 切换。
---

# 公文自动排版

按行文基本格式标准对 Word 文档进行自动排版（字体使用方正系列）。如需 GB/T 9704-2012 国标版本，见 `references/gb9704-spec.md`。

## 工作流决策树

```
用户输入 →
├─ 提供了 docx 文件？ → Reformat 模式
│   1. unpack → 读取 document.xml
│   2. 分析现有内容结构（按字号/加粗/序号模式智能识别标题层级）
│   3. 列出识别结果请用户确认（同时提示空白段落数量）
│   4. 修改 XML（页边距、字体、行距、缩进）
│   4.5 删除空白段落（没有文本内容的 <w:p> 元素）
│   4.6 在大标题段落前、后各插入一个空行段落（方正仿宋_GBK 三号）
│   5. pack → 输出排版后的 docx
│
└─ 没给 docx（文字/Markdown）？ → Create 模式
   1. 收集标题和内容（请用户确认层级结构）
   2. 调用 scripts/create_official.js
   3. 输出符合规范的 docx
```

## 排版参数速查

| 元素    | 字体        | 字号      | 半磅  | 加粗  | 行距      | 缩进   | 对齐   |
| ----- | --------- | ------- | --- | --- | ------- | ---- | ---- |
| 大标题   | 方正小标宋_GBK | 二号 22pt | 44  | 是   | 28pt 固定 | 无    | 居中   | 段前段后各一空行（方正仿宋_GBK 三号） |
| 标题空行  | 方正仿宋_GBK  | 三号 16pt | 32  | 否   | 28pt 固定 | 无    | 居中  | 标题前后的空白分隔行 |
| 副题/日期 | 方正仿宋_GBK  | 三号 16pt | 32  | 是   | 28pt 固定 | 无    | 居中   | — |
| 单位名称  | 楷体        | 三号 16pt | 32  | 是   | 28pt 固定 | 无    | 居中   | — |
| 称呼    | 方正仿宋_GBK  | 三号 16pt | 32  | 否   | 28pt 固定 | 无    | 左对齐  | — |
| 一级标题  | 方正黑体_GBK  | 三号 16pt | 32  | 是   | 28pt 固定 | 2 字符 | 左对齐  | — |
| 二级标题  | 方正楷体_GBK  | 三号 16pt | 32  | 是   | 28pt 固定 | 2 字符 | 左对齐  | — |
| 三级标题  | 方正仿宋_GBK  | 三号 16pt | 32  | 否   | 28pt 固定 | 2 字符 | 左对齐  | — |
| 正文    | 方正仿宋_GBK  | 三号 16pt | 32  | 否   | 28pt 固定 | 2 字符 | 两端对齐 | — |
| 页码    | 宋体        | 四号 14pt | 28  | —   | —       | —    | 居中   | — |

页面设置：A4（210mm × 297mm），上 3.7cm / 下 3.5cm / 左 2.8cm / 右 2.6cm。

> 旧 GB/T 9704-2012 标准保留在 `references/gb9704-spec.md`，可通过引用该文件切换。

---

## Create 模式：从零创建公文

### 步骤

1. 向用户确认：标题 + 内容段落及其层级（title/h1/h2/h3/body/date）
2. 构造 sections 数组
3. 运行：

```bash
cd C:\Users\hbxgl\.workbuddy\skills\gongwen-paiban
C:\Users\hbxgl\.workbuddy\binaries\node\versions\22.22.2\node.exe \
  -e "
const { createOfficialDoc } = require('./scripts/create_official');
createOfficialDoc({
  title: '标题',
  sections: [
    { text: '一、背景', level: 'h1' },
    { text: '正文段落...', level: 'body' },
    { text: '2026年7月4日', level: 'date' },
  ],
  outputPath: 'C:/Users/hbxgl/Desktop/科学/公文.docx',
});
"
```

### 要求

- `docx` npm 包需已安装在 `C:\Users\hbxgl\.workbuddy\binaries\node\workspace\node_modules\`
- 如未安装：`cd C:\Users\hbxgl\.workbuddy\binaries\node\workspace && C:\Users\hbxgl\.workbuddy\binaries\node\versions\22.22.2\node.exe -m npm install docx`

---

## Reformat 模式：已有文档重新排版

### 步骤

**1. Unpack**

```bash
C:/Users/hbxgl/.workbuddy/binaries/python/versions/3.13.12/python.exe \
  C:/Users/hbxgl/.workbuddy/skills/docx/scripts/office/unpack.py \
  <input.docx> /tmp/reformat_unpacked
```

**2. 分析结构**

读取 `/tmp/reformat_unpacked/word/document.xml`，智能识别标题层级：

- **看字号**：`<w:sz w:val="...">`, val 值越大（如 44+）越可能是标题
- **看加粗**：`<w:b/>` 存在 → 可能是 h2/h3
- **看序号模式**：文本以"一、"/"二、"开头 → h1；"（一）"/"（二）"→ h2；"1."/"2."→ h3
- **看对齐**：`<w:jc w:val="center">` + 大字号 → title

列出识别结果：

```
检测到以下结构，请确认：
  标题：关于印发XX的通知
  H1：一、工作背景
  H1：二、具体要求
  H2：（一）时间安排
  Body：[6段正文]
  Date：2026年7月4日
```

**3. 修改 XML**

拿到用户确认后，编辑 `/tmp/reformat_unpacked/word/document.xml`：

核心修改项：

- 页边距：修改 `<w:sectPr>` 中的 `<w:pgMar w:top="2097" w:bottom="1984" w:left="1587" w:right="1474"/>`（3.7/3.5/2.8/2.6cm）
- 对应层级的 run 属性：修改 `<w:rPr>` 中的 `<w:rFonts w:eastAsia="黑体"/>` 等信息
- 首行缩进：正文段落 `<w:ind w:firstLine="640"/>`
- 行间距：所有段落 `<w:spacing w:line="560" w:lineRule="exact"/>`
- **标题空行**：格式化完成并删除空段后，在大标题段前、段后各插入一个空行段落（方正仿宋_GBK 三号，含一个空格 `xml:space="preserve"` 避免被删除）
- **删除空白段落**：移除所有文本内容为空的 `<w:p>` 元素（见下方"删除空白段落"一节）

字体设置 XML 对照：

| 层级         | w:rFonts w:eastAsia | w:sz | w:b | w:ind |
| ---------- | ------------------- | ---- | --- | ----- |
| title      | 方正小标宋_GBK           | 44   | 有   | —     | 段前560 段后560 |
| subtitle   | 方正仿宋_GBK            | 32   | 有   | —     |
| org        | 楷体                  | 32   | 有   | —     |
| salutation | 方正仿宋_GBK            | 32   | —   | —     |
| h1         | 方正黑体_GBK            | 32   | 有   | 640   |
| h2         | 方正楷体_GBK            | 32   | 有   | 640   |
| h3         | 方正仿宋_GBK            | 32   | —   | 640   |
| body       | 方正仿宋_GBK            | 32   | —   | 640   |
| page       | 宋体                  | 28   | —   | —     |

**4. Pack**

```bash
C:/Users/hbxgl/.workbuddy/binaries/python/versions/3.13.12/python.exe \
  C:/Users/hbxgl/.workbuddy/skills/docx/scripts/office/pack.py \
  /tmp/reformat_unpacked <output.docx> --original <input.docx> --validate false
```

---

## Reformat 模式的实用 XML 编辑技巧

### 正文段落模板

```xml
<w:p>
  <w:pPr>
    <w:spacing w:line="560" w:lineRule="exact"/>
    <w:ind w:firstLine="640"/>
    <w:jc w:val="both"/>
  </w:pPr>
  <w:r>
    <w:rPr>
      <w:rFonts w:eastAsia="方正仿宋_GBK"/>
      <w:sz w:val="32"/>
    </w:rPr>
    <w:t>段落文字</w:t>
  </w:r>
</w:p>
```

### 标题段落模板

```xml
<w:p>
  <w:pPr>
    <w:spacing w:line="560" w:lineRule="exact"/>
    <w:jc w:val="center"/>
  </w:pPr>
  <w:r>
    <w:rPr>
      <w:rFonts w:eastAsia="方正小标宋_GBK"/>
      <w:sz w:val="44"/>
      <w:b/>
    </w:rPr>
    <w:t>公文标题</w:t>
  </w:r>
</w:p>
```

### 标题前后空行模板
```xml
<w:p>
  <w:pPr>
    <w:spacing w:line="560" w:lineRule="exact"/>
  </w:pPr>
  <w:r>
    <w:rPr>
      <w:rFonts w:eastAsia="方正仿宋_GBK"/>
      <w:sz w:val="32"/>
    </w:rPr>
    <w:t xml:space="preserve"> </w:t>
  </w:r>
</w:p>
```

---

## 删除空白段落

在 Reformat 模式中，**排版完成后必须删除所有空白段落**（即文本内容为空的 `<w:p>` 元素）。公文要求内容紧凑连续，不允许存在无意义的空行。

### 判断标准

一个段落被视为"空白"当且仅当——其所有 `<w:r>` 内的 `<w:t>` 文本（含空格和空白字符）拼接后为空字符串。

### 执行方法

在已完成其他排版修改的 `document.xml` 上，用正则删除空白 `<w:p>` 块：

```python
import re

with open('document.xml', 'r', encoding='utf-8') as f:
    content = f.read()

# 删除无文本内容的 <w:p> 元素
content = re.sub(
    r'<w:p[ >](?:(?!</w:p>).)*?</w:p>',
    lambda m: '' if not re.findall(r'<w:t[^>]*>([^<]*)</w:t>', m.group()) or
                    ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', m.group())).strip() == ''
              else m.group(),
    content,
    flags=re.DOTALL
)

with open('document.xml', 'w', encoding='utf-8') as f:
    f.write(content)

print('空白段落已删除')
```

### 注意事项

- 此操作**在应用完页边距/字体/行距/缩进之后**执行，确保不会误删正在被修改的段落

- 标题和正文之间的自然空行也会被删除——公文标准中标题与正文之间不需要额外空行

- 如果用户明确要求保留某些空行（如红头文件的分隔），需在确认环节标注

- **第一期**：仅正文排版（标题、h1/h2/h3、正文、日期、页码）

- **第二期**（待开发）：红头文件（红色发文机关 + 分隔线 + 发文字号）、附件格式、抄送格式、版记

- 依赖系统安装对应字体（方正小标宋_GBK、方正仿宋_GBK、方正黑体_GBK、方正楷体_GBK、楷体_GB2312、楷体、宋体）

- 字体未安装时文档仍可打开，但 WPS/Word 会使用系统默认字体替代
