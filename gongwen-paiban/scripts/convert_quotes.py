"""convert_quotes.py — 将 docx 文本中的成对英文双引号转换为中文引号

用法：
    python convert_quotes.py <文件.docx> [文件2.docx ...]   # 直接处理 docx
    python convert_quotes.py <document.xml>                # 处理已 unpack 的 XML

规则：
    按出现顺序交替配对——第 1、3、5…个英文双引号替换为“（U+201C），
    第 2、4、6…个替换为”（U+201D）。前提是原文引号成对且左先右后。
    仅处理 <w:t> 文本节点内的引号（docx npm 包会将 " 存为 &quot; 实体），
    不触碰 XML 属性值中的引号。英文单引号不处理，避免与撇号（如 90's）混淆。

依赖：仅 Python 标准库。处理前后自动校验 zip 完整性。
"""
import os
import re
import shutil
import sys
import tempfile
import zipfile

# 仅匹配文本节点，避免误伤 XML 属性中的引号
W_T = re.compile(r'(<w:t[^>]*>)([^<]*)(</w:t>)')
DOCX_PARTS = re.compile(r'word/(document|header\d*|footer\d*)\.xml$')
COUNT = {'n': 0}


def _convert_text(text):
    """将单个 <w:t> 文本节点内的英文双引号交替转换为中文引号"""
    # 解码常见转义形式（docx npm 包写入 " 时存为 &quot;）
    text = text.replace('&quot;', '"').replace('&#34;', '"')
    if '"' not in text:
        return text
    out = []
    for ch in text:
        if ch == '"':
            COUNT['n'] += 1
            ch = '\u201c' if COUNT['n'] % 2 else '\u201d'
        out.append(ch)
    return ''.join(out)


def convert_xml(xml):
    """对一段 OOXML 全文执行引号转换，返回转换后的字符串"""
    return W_T.sub(lambda m: m.group(1) + _convert_text(m.group(2)) + m.group(3), xml)


def process_docx(path):
    """对整个 docx 的 document/header/footer 部件执行转换并重打包"""
    with zipfile.ZipFile(path) as zin:
        targets = [n for n in zin.namelist() if DOCX_PARTS.match(n)]
        if not targets:
            print(f'{path}: 未找到可处理的 XML 部件，跳过')
            return
        contents = {n: zin.read(n) for n in zin.namelist()}
        infos = zin.infolist()

    total = 0
    for n in targets:
        COUNT['n'] = 0  # 各部件独立计数，避免跨文件错位配对
        contents[n] = convert_xml(contents[n].decode('utf-8')).encode('utf-8')
        print(f'  {n}: 替换 {COUNT["n"]} 处')
        total += COUNT['n']

    fd, tmp = tempfile.mkstemp(suffix='.docx')
    os.close(fd)
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
        for info in infos:
            zout.writestr(info, contents[info.filename])
    shutil.move(tmp, path)

    # 自检：zip 完整性 + 无残留英文引号实体
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None, f'{path}: zip 校验失败'
        residual = sum(z.read(n).decode('utf-8').count('&quot;') for n in targets)
    print(f'{path}: 完成，共替换 {total} 处'
          + (f'，警告：仍残留 {residual} 处 &quot;' if residual else ''))


def process_xml(path):
    """对已 unpack 的 XML 文件（如 document.xml）执行转换"""
    with open(path, 'r', encoding='utf-8') as f:
        xml = f.read()
    COUNT['n'] = 0
    converted = convert_xml(xml)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(converted)
    print(f'{path}: 完成，替换 {COUNT["n"]} 处')


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    if not args:
        print(__doc__)
        sys.exit(1)
    for p in args:
        if p.lower().endswith('.xml'):
            process_xml(p)
        elif zipfile.is_zipfile(p):
            process_docx(p)
        else:
            print(f'跳过（不是 docx/xml）: {p}')


if __name__ == '__main__':
    main()
