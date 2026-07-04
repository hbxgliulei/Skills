/**
 * create_official.js — 按行文基本格式标准创建公文
 *
 * 用法：
 *   node create_official.js <output.docx>
 *
 * 或作为模块引入：
 *   const { createOfficialDoc, FORMAT } = require('./create_official');
 *   createOfficialDoc({ title: '通知', sections: [...], outputPath: 'output.docx' });
 */

const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun,
  Header, Footer, AlignmentType, PageNumber,
  LineRuleType, TabStopType, TabStopPosition,
  BorderStyle, ShadingType
} = require('docx');

// ═══════════════════════════════════════════
// 行文基本格式 排版常量
// ═══════════════════════════════════════════

const FORMAT = {
  PAGE: {
    width: 11906,  // A4
    height: 16838,
  },
  MARGIN: {
    top: 2097,     // 3.7cm
    bottom: 1984,  // 3.5cm
    left: 1587,    // 2.8cm
    right: 1474,   // 2.6cm
  },
  LINE_SPACING: {
    line: 560,     // 28pt 固定行距
    lineRule: LineRuleType.EXACT,
  },
  FONTS: {
    TITLE: {
      font: '方正小标宋_GBK',
      size: 44,      // 二号 (22pt)
      bold: true,
      alignment: AlignmentType.CENTER,
    },
    SPACER: {
      font: '方正仿宋_GBK',
      size: 32,      // 三号 (16pt)
      bold: false,
      alignment: AlignmentType.CENTER,
    },
    SUBTITLE: {
      font: '方正仿宋_GBK',
      size: 32,      // 三号 (16pt)
      bold: true,
      alignment: AlignmentType.CENTER,
    },
    ORG: {
      font: '楷体',
      size: 32,
      bold: true,
      alignment: AlignmentType.CENTER,
    },
    SALUTATION: {
      font: '方正仿宋_GBK',
      size: 32,
      bold: false,
      alignment: AlignmentType.LEFT,
    },
    H1: {
      font: '方正黑体_GBK',
      size: 32,      // 三号 (16pt)
      bold: true,
      alignment: AlignmentType.LEFT,
      indent: 640,   // 缩进 2 字符
    },
    H2: {
      font: '方正楷体_GBK',
      size: 32,
      bold: true,
      alignment: AlignmentType.LEFT,
      indent: 640,
    },
    H3: {
      font: '方正仿宋_GBK',
      size: 32,
      bold: false,
      alignment: AlignmentType.LEFT,
      indent: 640,
    },
    BODY: {
      font: '方正仿宋_GBK',
      size: 32,      // 三号 (16pt)
      alignment: AlignmentType.JUSTIFIED,
      indent: 640,   // 首行缩进 2 字符
    },
    PAGE_NUM: {
      font: '宋体',
      size: 28,      // 四号 (14pt)
    },
  },
};

// ═══════════════════════════════════════════
// 辅助函数
// ═══════════════════════════════════════════

/**
 * 创建带标准样式的一段文本
 */
function makeParagraph(text, style, extraProps = {}) {
  return new Paragraph({
    alignment: style.alignment,
    spacing: FORMAT.LINE_SPACING,
    indent: style.indent ? { firstLine: style.indent } : undefined,
    ...extraProps,
    children: [
      new TextRun({
        text,
        font: style.font,
        size: style.size,
        bold: style.bold || false,
      }),
    ],
  });
}

/**
 * 根据层级标记创建对应样式的段落
 * @param {{ text: string, level: string | number }} item
 * @returns {Paragraph}
 */
function makeLeveledParagraph(item) {
  const text = item.text;
  const level = String(item.level || 'body');

  switch (level) {
    case 'title':
      return makeParagraph(text, FORMAT.FONTS.TITLE);
    case 'spacer':
      return makeParagraph(' ', FORMAT.FONTS.SPACER);
    case 'subtitle':
      return makeParagraph(text, FORMAT.FONTS.SUBTITLE, { spacing: { after: 200 } });
    case 'org':
      return makeParagraph(text, FORMAT.FONTS.ORG, { spacing: { after: 200 } });
    case 'salutation':
      return makeParagraph(text, FORMAT.FONTS.SALUTATION, { spacing: { after: 120 } });
    case 'h1':
    case '1':
      return makeParagraph(text, FORMAT.FONTS.H1);
    case 'h2':
    case '2':
      return makeParagraph(text, FORMAT.FONTS.H2);
    case 'h3':
    case '3':
      return makeParagraph(text, FORMAT.FONTS.H3);
    case 'body':
    default:
      return makeParagraph(text, FORMAT.FONTS.BODY);
  }
}

// ═══════════════════════════════════════════
// 主函数
// ═══════════════════════════════════════════

/**
 * 创建一份符合行文基本格式的公文
 * @param {Object} options
 * @param {string} [options.title]     — 公文标题
 * @param {string} [options.subtitle]  — 副题或日期行
 * @param {string} [options.org]       — 单位名称
 * @param {Array}  options.sections    — 内容段落列表
 *   [{ text: '一、背景情况', level: 'h1' },
 *    { text: '正文段落...', level: 'body' }]
 * @param {string} options.outputPath  — 输出文件路径
 * @param {boolean} [options.showPageNum=true] — 是否显示页码
 */
async function createOfficialDoc({ title, subtitle, org, sections, outputPath, showPageNum = true }) {
  const children = [];

  const allSections = [];
  // Spacer before title
  if (title) allSections.push({ text: ' ', level: 'spacer' });
  if (title) allSections.push({ text: title, level: 'title' });
  // Spacer after title
  if (title) allSections.push({ text: ' ', level: 'spacer' });
  if (subtitle) allSections.push({ text: subtitle, level: 'subtitle' });
  if (org) allSections.push({ text: org, level: 'org' });
  allSections.push(...sections);

  for (const item of allSections) {
    children.push(makeLeveledParagraph(item));
  }

  const doc = new Document({
    sections: [{
      properties: {
        page: {
          size: FORMAT.PAGE,
          margin: FORMAT.MARGIN,
        },
      },
      headers: {
        default: new Header({
          children: [new Paragraph({ spacing: FORMAT.LINE_SPACING, children: [] })],
        }),
      },
      footers: {
        default: showPageNum ? new Footer({
          children: [
            new Paragraph({
              alignment: AlignmentType.CENTER,
              children: [
                new TextRun({
                  children: [PageNumber.CURRENT],
                  font: FORMAT.FONTS.PAGE_NUM.font,
                  size: FORMAT.FONTS.PAGE_NUM.size,
                }),
              ],
            }),
          ],
        }) : undefined,
      },
      children,
    }],
  });

  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(outputPath, buffer);
  console.log(`公文已生成: ${outputPath}`);
  return outputPath;
}

// ═══════════════════════════════════════════
// CLI 入口
// ═══════════════════════════════════════════

if (require.main === module) {
  const outputPath = process.argv[2] || 'official_document.docx';

  // 默认测试内容
  const testDoc = {
    title: '关于印发行文格式标准测试的通知',
    subtitle: '（2026年7月4日）',
    org: 'XX单位办公室',
    sections: [
      { text: '各单位领导、同志们：', level: 'salutation' },
      { text: '一、测试目的', level: 'h1' },
      {
        text: '为验证公文自动排版系统的功能是否符合行文基本格式标准，特编写本测试文档。',
        level: 'body',
      },
      { text: '二、排版要求', level: 'h1' },
      {
        text: '公文排版应严格按照标准执行。标题使用方正小标宋_GBK二号字加粗居中。一级标题使用方正黑体_GBK三号字加粗，缩进2字符。二级标题使用方正楷体_GBK三号字加粗，缩进2字符。正文使用方正仿宋_GBK三号字，首行缩进两个字符，行距固定28磅。',
        level: 'body',
      },
      { text: '（一）页面设置', level: 'h2' },
      {
        text: '公文用纸采用A4型纸，页边距上3.7cm、下3.5cm、左2.8cm、右2.6cm。',
        level: 'body',
      },
      { text: '（二）字体字号', level: 'h2' },
      {
        text: '公文正文统一使用方正仿宋_GBK字体三号。各级标题依次使用方正黑体_GBK、方正楷体_GBK、楷体_GB2312。',
        level: 'body',
      },
      { text: '1. 三级标题示例', level: 'h3' },
      {
        text: '三级标题使用楷体_GB2312三号字，不加粗，缩进2字符。',
        level: 'body',
      },
      { text: '2. 行距要求', level: 'h3' },
      {
        text: '全文行距固定28磅，段落间不留空行，内容紧凑连续。空白段落应在排版时自动删除。',
        level: 'body',
      },
      { text: '三、注意事项', level: 'h1' },
      {
        text: '如系统中缺少指定字体（方正系列），文档打开时系统会使用默认字体替代，样式可能偏移。建议在安装了方正字体的机器上查看最终效果。',
        level: 'body',
      },
    ],
    outputPath,
  };

  createOfficialDoc(testDoc).catch(console.error);
}

// ═══════════════════════════════════════════
// 导出
// ═══════════════════════════════════════════

module.exports = { createOfficialDoc, FORMAT, makeParagraph, makeLeveledParagraph };
