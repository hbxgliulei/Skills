# WorkBuddy Skills 技能库

本仓库是 WorkBuddy 个人技能集合，每个子目录为一个独立技能。技能以 SKILL.md 为核心（含元数据与使用说明），可附带脚本、参考资料与资源文件。

## 技能列表

| 技能 | 说明 |
|------|------|
| [book-character-network](book-character-network/) | 书籍人物关系网络分析与可视化（人物识别、共现分析、关系网络图） |
| [gongwen-paiban](gongwen-paiban/) | 公文自动排版（方正小标宋/仿宋/黑体/楷体，符合行文格式标准） |
| [ppt-master](ppt-master/) | 源文档（PDF/DOCX/URL/Markdown）转多格式 SVG 内容演示系统 |
| [rmrb-fetch](rmrb-fetch/) | 人民日报数字报抓取：单日/批量/断点续传/词频统计 |

## 安装方式

将技能目录复制到用户级技能目录（跨项目可用）：

```bash
cp -r <skill-name> ~/.workbuddy/skills/
```

或复制到项目级技能目录（随项目共享给协作者）：

```bash
cp -r <skill-name> .workbuddy/skills/
```

## 技能目录结构

```
skill-name/
├── SKILL.md          # 必需：YAML frontmatter（name/description）+ 使用说明
├── README.md         # 可选：项目介绍
├── scripts/          # 可选：可执行脚本（Python/Bash 等）
├── references/       # 可选：参考资料（按需加载进上下文）
└── assets/           # 可选：输出用资源（模板、图标、字体等）
```

SKILL.md 的 YAML frontmatter 必须包含：

- `name`：技能名（小写连字符）
- `description`：技能用途与触发场景，第三人口吻（"This skill should be used when..."）
- `agent_created: true`：标记为可被 SkillManage 管理维护

## 维护约定

- 每个技能独立一个子目录，仓库根目录不放置散文件
- 新增技能时补齐 SKILL.md 与 README.md
- 技能升级后重新打包（zip）并同步更新
- 遵守各技能数据源的版权声明，抓取类数据勿用于商业用途
