# life-decision-guide — 人生决策，按《高性价比人生指南》查了再答

WorkBuddy 技能包：把开源书《高性价比人生指南》（[eternity4719/HowToLiveBetter](https://github.com/eternity4719/HowToLiveBetter)，Unlicense 公有领域）整本内置为本地知识库，让 AI 助手回答具体人生决策时**先查书再回答**，每条结论注明出自第几节第几条。

## 它能回答什么

- 该不该做、值不值、划不划算：胃镜筛查、低钠盐、烟雾报警器、房租押金……
- 出事了先做什么：火灾、触电、卒中、误食毒蘑菇、被人讹……
- 能领哪笔钱：失业金、低保、创业担保贷款、培训补贴……
- 这么干犯不犯法：替人担保、转卖账号、电动车进电梯、网上代抢票……

全书 34 节、630 条建议，每条写明**花掉什么、换回什么、证据多硬**（A/B/C 分级），来源只引期刊论文和官方文件，共 1300+ 条文献链接。

## 目录结构

```
life-decision-guide/
├── SKILL.md                    # 工作流：检索 → 算性价比 → 排序 → 按结构作答
├── scripts/
│   └── search_entries.py       # 条目检索（纯标准库，离线可用）
└── references/
    ├── book/                   # 全书 34 节正文（630 条，含成本标签与文献）
    └── docs/                   # 长文专题与核实记录
```

## 检索脚本用法

```bash
python scripts/search_entries.py --list              # 全部条目目录（含证据等级）
python scripts/search_entries.py 担保 借条           # 关键词检索，整条输出，按命中数排序
python scripts/search_entries.py --and 胃镜 筛查     # AND：须同时命中
python scripts/search_entries.py --section 08 担保   # 限定某一节内检索
```

## 与上游 skill 的差异

上游仓库自带 [skills/life-decision-guide](https://github.com/eternity4719/HowToLiveBetter/tree/main/skills/life-decision-guide)（回答前需现场克隆上游仓库取正文）。本技能在其基础上：

1. **整本正文内置**（references/book/，3MB）——离线可用，无需联网
2. **新增检索脚本** search_entries.py——一条命令拿到整条条目（出处 + 成本标签 + 高亮命中），OR/AND/限节检索
3. **固化性价比算法**（从上游 index.html 抠出的 COST_W 权重与档位映射）——不依赖现场读源码
4. 适配 WorkBuddy 技能规范（agent_created、触发词、progressive disclosure）

## 安装

将整个文件夹放入 WorkBuddy 技能目录 `~/.workbuddy/skills/`，重启会话即可。书内容随上游更新，同步方法见 SKILL.md 末尾。

## 授权

书内容 Unlicense（公有领域），本技能包同样不作任何权利保留。
