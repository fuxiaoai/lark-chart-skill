# 飞书画图 Skill

`design-lark-chart` 是一个面向 Agent 的飞书画板生成技能。它把自然语言说明、参考截图、或飞书文档中的业务内容，转成可继续编辑的飞书画板图表，而不是只能观看的静态图片。

给它一个业务背景、期望图表类型和输出位置，Agent 会读取材料、规划图表结构、生成画板内容、写入飞书文档，并导出真实飞书画板图用于验收。

## 一句话安装

把下面这句话发给你的 Agent 即可：

> 请从 GitHub 仓库 https://github.com/fuxiaoai/lark-chart-skill 安装路径为 `skills/design-lark-chart` 的技能。

## 它解决什么问题

很多文档配图工具只能生成一张图片。这个 Skill 的目标更明确：把图真正落到飞书画板中，让用户可以继续改节点、改文字、调连线、改颜色，并保留飞书文档里的协作体验。

适合这些场景：

- 给已有飞书文档补架构图、流程图、泳道图、时序图、矩阵图等专业配图。
- 新建一份说明文档，并自动插入一个或多个飞书画板。
- 把复杂业务材料转成可演示、可评审、可二次编辑的结构化图表。
- 在固定图表类型覆盖不到时，进入自由画图模式，生成产品原型、桑基图、地图、技术原理图、插画风格画板等。

## 为什么它不是普通截图生成器

下面所有示例图都来自飞书文档中的真实 `<whiteboard>` 画板块，README 中展示的是通过飞书画板导出的预览图。源对象仍然是飞书画板：打开原始飞书文档后，可以进入画板继续编辑里面的节点、形状、文字和连线。

> [!IMPORTANT]
> **想验证它不是静态截图？**
> 打开原始飞书文档后，可以直接进入对应飞书画板，继续编辑 **节点、文字、形状和连线**。
> **验证入口：** [查看原始飞书画板文档](https://my.feishu.cn/wiki/SvZqwLfcSi3zw8kFIbwcEZFgnRc)

## 自由画图 Showcase

自由画图模式适用于固定模板无法覆盖的表达。它会先理解意图，再用 SVG/OpenAPI 或画板 DSL 路径生成可编辑画板。

| 示例 | 飞书画板导出图 |
|---|---|
| 山湖日出 · 油画风场景图 | <img src="assets/showcase/freeform/01-landscape-oil-painting.jpg" alt="山湖日出 · 油画风场景图" width="420"> |
| 将任意页面截图转为可编辑产品原型图 | <img src="assets/showcase/freeform/02-product-prototype-from-screenshot.jpg" alt="将任意页面截图转为可编辑产品原型图" width="420"> |
| 流量归因桑基图 | <img src="assets/showcase/freeform/03-traffic-attribution-sankey.jpg" alt="流量归因桑基图" width="420"> |
| RoadMap 演进路线图 | <img src="assets/showcase/freeform/04-roadmap-evolution.jpg" alt="RoadMap 演进路线图" width="420"> |
| RAG 原理可视化 · 量子物理科研面板风格 | <img src="assets/showcase/freeform/05-rag-quantum-research-panel.jpg" alt="RAG 原理可视化 · 量子物理科研面板风格" width="420"> |
| 微信 · 移动 App 产品原型 | <img src="assets/showcase/freeform/06-wechat-mobile-app-prototype.jpg" alt="微信 · 移动 App 产品原型" width="420"> |
| 塞尔达海拉鲁地图 · 复古制图风格 | <img src="assets/showcase/freeform/07-hyrule-vintage-map.jpg" alt="塞尔达海拉鲁地图 · 复古制图风格" width="420"> |

## 17 类专业图表示例

以下示例以“评测系统”为业务背景，覆盖常见的技术文档、产品方案和运营分析图表类型。每张图都来自飞书画板导出，不是手工贴到 README 的静态截图。

| 图表类型 | 飞书画板导出图 |
|---|---|
| 业务架构图：评测系统能力分层 | <img src="assets/showcase/chart/01-business-architecture.jpg" alt="业务架构图：评测系统能力分层" width="420"> |
| 系统架构图：评测平台技术拓扑 | <img src="assets/showcase/chart/02-system-architecture.jpg" alt="系统架构图：评测平台技术拓扑" width="420"> |
| 流程图：评测任务创建与校验 | <img src="assets/showcase/chart/03-flowchart.jpg" alt="流程图：评测任务创建与校验" width="420"> |
| 泳道图：用户、平台与服务协作 | <img src="assets/showcase/chart/04-swimlane.jpg" alt="泳道图：用户、平台与服务协作" width="420"> |
| ER 图：用户域和评测任务关联关系 | <img src="assets/showcase/chart/05-er-diagram.jpg" alt="ER 图：用户域和评测任务关联关系" width="420"> |
| 思维导图：评测平台能力 | <img src="assets/showcase/chart/06-mindmap.jpg" alt="思维导图：评测平台能力" width="420"> |
| 时序图：评测任务执行调用顺序 | <img src="assets/showcase/chart/07-sequence.jpg" alt="时序图：评测任务执行调用顺序" width="420"> |
| 组织架构图：评测平台团队职责 | <img src="assets/showcase/chart/08-org-chart.jpg" alt="组织架构图：评测平台团队职责" width="420"> |
| 状态机图：评测任务生命周期 | <img src="assets/showcase/chart/09-state-machine.jpg" alt="状态机图：评测任务生命周期" width="420"> |
| 漏斗图：评测任务转化与流失 | <img src="assets/showcase/chart/10-funnel.jpg" alt="漏斗图：评测任务转化与流失" width="420"> |
| 甘特图：评测平台建设排期 | <img src="assets/showcase/chart/11-gantt.jpg" alt="甘特图：评测平台建设排期" width="420"> |
| 里程碑图：评测系统版本路线图 | <img src="assets/showcase/chart/12-milestone.jpg" alt="里程碑图：评测系统版本路线图" width="420"> |
| 矩阵象限图：评测需求优先级判断 | <img src="assets/showcase/chart/13-matrix-quadrant.jpg" alt="矩阵象限图：评测需求优先级判断" width="420"> |
| 链路架构图：评测任务端到端调用链 | <img src="assets/showcase/chart/14-link-architecture.jpg" alt="链路架构图：评测任务端到端调用链" width="420"> |
| 飞书画板风格架构图：评测运营策略承接 | <img src="assets/showcase/chart/15-lark-style-architecture.jpg" alt="飞书画板风格架构图：评测运营策略承接" width="420"> |
| 手绘风格架构图：评测方案早期草图 | <img src="assets/showcase/chart/16-sketch-architecture.jpg" alt="手绘风格架构图：评测方案早期草图" width="420"> |
| 复杂业务泳道图：评测任务全链路履约 | <img src="assets/showcase/chart/17-complex-swimlane.jpg" alt="复杂业务泳道图：评测任务全链路履约" width="420"> |

## 支持的图表类型

固定图表类型包括：业务架构图、系统架构图、流程图、泳道图、复杂业务泳道图、时序图、组织架构图、状态机图、ER 图、思维导图、漏斗图、甘特图、里程碑图、矩阵象限图、链路架构图、飞书画板风格架构图、手绘风格架构图。

自由画图模式覆盖：产品原型、页面截图还原、桑基图、路线图、地图、游戏画面、技术原理图、插画风格画板，以及其他无法用固定图表类型表达的视觉需求。

## 工作方式

Skill 内部按一条闭环管道工作：

```text
Normalize -> Select -> Plan -> Layout -> Render -> StaticCheck -> VQA -> Deliver
```

它不会把某几张图硬编码成模板，而是从用户输入中抽取业务结构，再结合 `assets/style-tokens/` 中的飞书画板风格指纹进行设计。交付前会按路由执行质量门：

- DSL 路径：`whiteboard-cli --check` 检查布局、文字溢出和节点问题。
- SVG 路径：`whiteboard-cli -f svg --check`、SVG 质量 lint、OpenAPI 转换。
- Mermaid / PlantUML 路径：写入飞书后回读源码，并导出真实飞书画板图。
- 所有路径：最终都要基于飞书端真实导出图做视觉验收。

## 仓库结构

```text
.
├── README.md
├── assets/showcase/                 # README 展示用的飞书画板导出图
└── skills/design-lark-chart/
    ├── SKILL.md                     # Agent 读取的技能入口
    ├── assets/                      # 飞书画板参考图、raw 结构、style tokens
    ├── references/                  # 管道、图表分类、质量门、自由画图说明
    └── scripts/                     # 本地校验、预览、SVG 自由模式门禁脚本
```

## 使用示例

安装后可以直接对 Agent 说：

```text
读取这个飞书文档，给“系统设计”章节补一张飞书画板风格的系统架构图，并写回原文档。
```

```text
新建一份飞书文档，主题是“评测平台方案说明”，帮我自动配一张业务架构图和一张端到端链路架构图。
```

```text
参考这张产品截图，把它画成可编辑的飞书画板产品原型图。
```

## 本地依赖

运行这个 Skill 的 Agent 环境需要能够调用 `lark-cli` 和 `whiteboard-cli`。首次写入用户飞书文档时，按 Agent 提示完成飞书授权即可。

## License

Apache License 2.0. See [LICENSE](LICENSE).
