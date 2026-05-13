# 02 · Chart Taxonomy

当前支持 17 种固定图表类型，另有 1 个非模板化自由绘画模式。大部分固定图型一一对应 `assets/previews/<id>.png` 与 `assets/style-tokens/<id>.json`；少数图型为**代码原生图**（仅 Mermaid / PlantUML），不依赖 style-tokens。`freeform-drawing` 不绑定单张 preview，它从 `_catalog.json.house_style` 和用户意图动态结算风格。表中 **signals** 用于选图型（Select 阶段），**structure** 用于 Plan 阶段约束拓扑，**route** 指定优先渲染路径，**fallback** 指定该类型不适用时最可能的替代。

> 对 DSL 图型：`id` 与 `assets/` 下文件名一一对齐。对代码原生图：不要求补 preview/raw/style-tokens，但必须补 examples 与飞书回读验证证据。
>
> 当前验证状态：17 种固定图型均已有可运行样例并完成飞书端验证；其中 `sequence` / `state-machine` / `flowchart` 已在 2026-04-28 重新按 Mermaid 路由复核，`funnel` 已在同日按彩色 DSL 路由复核。`freeform-drawing` 的验收 prompt 已落到 `references/examples/freeform-drawing.prompts.md`，每次发布仍要按实际会话跑 Gate A/B。图型能力是否可对外发布，以 `COVERAGE_REPORT.md` 为准，而不是只看本表。

| # | id | 中文名 | signals（触发语义） | structure（拓扑约束） | route（优先渲染路径） | fallback |
|---|---|---|---|---|---|---|
| 1  | `business-architecture`     | 业务架构图          | "能力分层""平台组成""业务域" | N 行 × 多列，带左侧侧栏或顶部标题 | `dsl` | system-architecture |
| 2  | `system-architecture`       | 系统架构图          | "技术组件""服务拓扑""外部依赖" | 垂直 N 层 + 右侧外部依赖侧栏 | 强视觉验收优先 `svg-openapi`；低复杂度可 `dsl` | link-architecture |
| 3  | `flowchart`                 | 流程图              | "先做 A 再做 B""如果 X 则 Y" | 主流程走中轴，异常分支走侧线 | 标准审批/判断流优先 `mermaid(flowchart)`；复杂复合卡片流走 `dsl` | state-machine |
| 4  | `swimlane`                  | 泳道图              | "用户""运营""平台"等**多角色**协作 | 横向泳道 + 角色列头 | `dsl` | flowchart |
| 5  | `complex-swimlane`          | 复杂业务泳道图      | 多系统多节点端到端履约 | 多泳道 + 跨泳道跳转 + 分支 | `dsl` | swimlane |
| 6  | `sequence`                  | 时序图              | "A 调用 B""返回""回调" | 顶部角色头 + 垂直生命线 + 水平消息 | 优先 `mermaid(sequenceDiagram)`；必要时 `plantuml` | flowchart |
| 7  | `org-chart`                 | 组织架构图          | "团队""汇报""职责" | 自顶向下树 | `dsl` | business-architecture |
| 8  | `state-machine`             | 状态机图            | "状态""流转""失败重试" | 有向图 + 自环 | 优先 `mermaid(stateDiagram-v2)`；仅样式增强需求明显时回 `dsl` | flowchart |
| 9  | `funnel`                    | 漏斗图              | "阶段转化""流失" | 从上到下宽度递减 | `dsl`，且必须彩色分层、禁止无意义外框 | — |
| 10 | `gantt`                     | 甘特图              | "排期""周期""进度" | 时间轴 + 任务条 | `mermaid(gantt)` | milestone |
| 11 | `milestone`                 | 里程碑图            | "版本路线""阶段目标""关键节点" | 水平时间线 + 节点 | `dsl` | gantt |
| 12 | `matrix-quadrant`           | 矩阵象限图          | "优先级""价值 vs 成本" | 2×2 或 3×3 象限 | 强视觉验收优先 `svg-openapi`；低复杂度可 `dsl` | — |
| 13 | `link-architecture`         | 链路架构图          | "端到端链路""数据流转""系统依赖" | 从左到右串联组件，带分支 | `dsl` | system-architecture |
| 14 | `lark-style-architecture`   | 飞书画板风格架构图  | "策略到模块""承接关系""产品运营汇报""高级飞书风格架构图" | 顶部核心逻辑横幅 + 4-6 个彩色模块列 + 模块内二级卡片/要点 + 跨模块右角连接 | `dsl` | business-architecture |
| 15 | `sketch-architecture`       | 手绘风格架构图      | "草图""早期方案""低保真" | 任意拓扑，视觉带手绘笔触 | 强视觉验收优先 `svg-openapi`；低复杂度可 `dsl` | — |
| 16 | `mindmap`                   | 思维导图            | "思维导图""脑图""要点整理""发散" | 单根节点 + 多层分支 | 优先 `mermaid(mindmap)`；必要时 `plantuml` | — |
| 17 | `er-diagram`                | ER 图               | "ER 图""实体关系""表结构""主键""外键" | 实体 + 字段 + 基数关系 | 优先 `mermaid(erDiagram)`；必要时 `plantuml` | — |
| 18 | `freeform-drawing`          | 自由绘画 / 自定义信息图 | "自由画""产品原型""游戏页面""桑基图""路线图""插画""不是模板里的图" | 由用户意图决定：可为流量带宽、时间轴、UI 画面、场景插画或组合图解 | `svg-openapi`，必须读 `08-freeform-svg-mode.md` | 必要时向用户一次性确认视觉目标 |

## 选型原则

1. **语义优先，形状其次**：用户说"多个角色协作"就选 swimlane，哪怕结构可以用 flowchart 表达。
2. **代码原生优先**：只要目标图型已被飞书代码图原生支持，且用户要的是标准图法，优先 Mermaid / PlantUML，不要先用 DSL 硬拼。
3. **固定图型优先，表达自由其次**：语义明确落在 17 种固定图型时先用固定图型；只有固定图型表达会明显损失用户意图（例如产品原型、游戏页面、插画、桑基流量带宽）时才选 `freeform-drawing`。
4. **不确定时问一次**：如果 `business-architecture` 和 `system-architecture` 两种候选都合理，一次性给出 2-3 个选项让用户选，**不连环问**。
5. **不"兜底到 flowchart"**：如果固定图型没有清晰匹配，但用户明确想要视觉表达，选 `freeform-drawing`；如果只是概念含糊且无法判断视觉目标，才一次性追问。

## 边缘选型 Dispatcher（强制判据）

"语义优先"在边缘案例上会摇摆。下面 D0 是总兜底；D1-D4 是具体边缘判据：**任意一条不满足就必须升级到自由路径**，不再凭感觉。判据的设计目标是：让"模板路径"和"自由路径"在同一类语义上有清晰分界，下游执行者不需要再揣测。

### D0. 模板匹配度门槛（总兜底，最先评估）

在进入 D1-D4 之前，先评估"用户诉求 vs 候选模板"的匹配度。**只要命中以下任意一条，直接走 `freeform-drawing` 通用 SVG 路径，让 LLM 自己构图，不再尝试模板**：

- 用户参考图明显不属于 17 类固定图型（例如：插画/手绘场景/桑基带宽/产品原型/游戏 UI/复合信息图/单页叙事图/带氛围光照的视觉化）
- 用户描述里出现"参考这张图""按这个画风""像这样的视觉感觉"，并附图，而该图与任何固定 preview 都不同源
- 用户要的视觉元素（曲线带宽、放射状、自由几何拼贴、非笛卡尔布局、手绘笔触+插画、UI 控件+流程混排）无法被任意单一固定 token 覆盖
- 模板 preview 与用户预期之间存在**结构级不匹配**（不是"颜色不一样"或"再加几个节点"能修的差距）
- 用户已经说过"模板不像""差太远""能不能不要那个模板感"

落到 freeform-drawing 时必须显式：

```jsonc
{
  "chart_type": "freeform-drawing",
  "freeform_mode": "custom",            // 或 illustration / roadmap / prototype / sankey
  "style_seed": null,                    // 不借用模板时为 null；借用则填 token id
  "dispatcher_reason": "D0：用户参考图为雨后山林插画，结构上与所有 17 类固定模板不同源（无分层/无连线/无节点卡片），改走通用 SVG 自由构图"
}
```

**反例（禁止）**：

- ❌ "用户给了张架构图但有点特殊，我硬套 system-architecture token 改色试试"——不许，命中 D0 直接走 freeform-drawing。
- ❌ "freeform-drawing 太自由，先用 milestone 凑一下"——不许，先用 D0 判，再用 D1 兜。
- ✅ "参考图是雨后山林插画 → D0 命中 → mode=illustration → style_seed=null → LLM 自己设计 SVG → 走 lint + check + openapi 通用门禁"。

D0 的精神：**模板是加速器，不是唯一答案**。固定模板用得上就用，用不上就让模型自己画 SVG，下游门禁（whiteboard-cli check / lint_svg_quality / 飞书回看）保证下限。

### D1. milestone DSL ↔ freeform-drawing/roadmap

走 `milestone` DSL 模板需要**全部满足**：

- 里程碑数量 ≤ 8
- 视觉只需"圆点 + 单层卡片 + 直线轴"，无阶段横幅 / 泳道 / 当前节点高亮
- 卡片间无依赖线，节点只按时间排列
- 不需要底部趋势条 / 关键指标摘要 / 当前节点强调

任意一条不满足 → 切 `freeform-drawing`，`mode=roadmap`，并在 `plan.style_seed` 声明借用 `milestone` token。

### D2. business-architecture ↔ system-architecture

走 `system-architecture` 需要**全部满足**：

- 输入包含技术服务/组件名（不是纯业务能力名）
- 至少能形成 3 层主架构 + 1 个侧栏（外部依赖 / 运行时 / 基础设施 / 监控）
- 用户语境包含"系统拓扑 / 服务依赖 / 部署 / 调用链"

否则走 `business-architecture`。**不要**因为节点多就选 system，关键是有没有"侧栏 + 多层主区"。

### D3. sketch-architecture ↔ freeform-drawing/illustration ↔ freeform-drawing/prototype

- 用户要"草图/低保真/早期方案" → `sketch-architecture`，需 ≥ 2 个虚线阶段分区 + 手绘双线笔触
- 用户要"插画/场景图/概念图解/自然/抽象画面" → `freeform-drawing` mode=`illustration`
- 用户要"产品页面/游戏界面/UI 原型/可点击感" → `freeform-drawing` mode=`prototype`

判据顺序：先看"是不是 UI 画面" → 是则 prototype；再看"是不是叙事/场景" → 是则 illustration；最后才是 sketch-architecture。**不要**把场景插画硬塞进 sketch-architecture。

### D4. lark-style-architecture ↔ freeform-drawing/custom

走 `lark-style-architecture` DSL 需要**全部满足**：

- 输入包含明确"核心逻辑 / 策略 / 北极星"作为顶部横幅
- 至少 4 个承接模块，每个模块至少 2 个二级能力点
- 模块色板可由 `lark-style-architecture` token 直接覆盖（4-6 色分区）
- 不需要画板风格之外的特殊视觉（手绘 / 插画 / 流量带宽 / 游戏 UI）

任意一条不满足 → `freeform-drawing` mode=`custom`，并显式说明为何不用模板。

### Dispatcher 输出契约

Select 阶段的产物 `selection.json` 必须包含：

```jsonc
{
  "chart_type": "freeform-drawing",     // 或 17 类固定 id 之一
  "freeform_mode": "roadmap",           // 仅 chart_type=freeform-drawing 时必填
  "style_seed": "milestone",            // 借用哪张 token；可空
  "dispatcher_reason": "里程碑数=12（>8）且需要阶段横幅、当前节点高亮、底部趋势条，命中 D1 升级条件"
}
```

`dispatcher_reason` 必须引用上述 D1-D4 的具体不满足条件，不接受"感觉更合适"。

## 参考素材的正确用法

- ✅ **允许**：把 `assets/style-tokens/<id>.json` 作为 style 软约束，把 `assets/previews/<id>.png` 描述给多模态 LLM 当视觉锚。
- ✅ **必须**：当用户评价"不够高级 / 太简单 / 和示例差距大"，对 `system-architecture` / `matrix-quadrant` / `sketch-architecture` 读取 `07-premium-style-contracts.md`，并优先用 SVG 高保真路径还原 preview 的版式气质。
- ❌ **禁止**：把 `assets/raw/<id>.json`（节点级坐标）作为 few-shot 喂给 LLM，会诱导它抄坐标和抄文案。
- ❌ **禁止**：按"这张图上写了'用户入口/核心能力/数据底座'，那我也这么分层"——这是参考素材里的**业务内容**，不是"样式"。

## 自由绘画模式的边界

`freeform-drawing` 是能力兜底，不是偷懒兜底：

- ✅ 适用：桑基/鱼骨/飞轮/产品原型/游戏界面/手绘插画/复杂运营图解/单页视觉故事等固定表无法准确表达的需求。
- ✅ 必须：先写 `freeform_brief`，明确画面隐喻、主视觉、信息层级、可编辑元素、不可补造内容。
- ✅ 必须：用 `diagram.svg` 作为唯一设计源，执行 `whiteboard-cli -f svg --check`、`--to openapi`、`lint_svg_quality.py`，再写入飞书。
- ❌ 禁止：为“桑基图”“路线图”“雨后山林”写专门生成器、固定坐标表或固定 SVG 模板。
- ❌ 禁止：把自由模式当作固定图型失败后的低质截图路径；最终仍必须是可写入飞书画板的 OpenAPI 节点结构。

## 三类强视觉图型的选型下限

- `system-architecture`：输入必须能形成主架构区和外部依赖/运行时/基础设施等侧栏或底座。只给 3-5 个服务名时，不要强行画成参考图级复杂系统架构；应先降级为 `link-architecture` 或一次性要求补模块分层。
- `matrix-quadrant`：必须有两个明确评价轴，默认 2×2。禁止把四个象限渲染成横向四列卡片；没有坐标轴标签和象限边界时视为选型失败。
- `sketch-architecture`：必须表达阶段/泳道/模块组与少量关键连线。禁止只画普通圆角卡片；没有虚线分区、手绘双线/下划线或草图式弱网格时视为风格失败。

## lark-style-architecture 选型下限

只有当输入本身包含**核心逻辑/策略**、**至少 4 个承接模块**，且大多数模块有可归纳的二级能力或要点时，才选 `lark-style-architecture`。如果用户只给出 2-3 层线性分层，应该选 `business-architecture` 或 `system-architecture`，不要把 `lark-style-architecture` 画成"三排白色盒子 + 少量箭头"。
