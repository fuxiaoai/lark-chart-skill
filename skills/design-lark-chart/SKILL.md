---
name: design-lark-chart
metadata:
  version: "1.2"
description: |
  当用户要求“画架构图/流程图/泳道图/时序图/组织架构图/状态机/漏斗/甘特/里程碑/矩阵象限/链路架构/手绘风格架构/复杂业务泳道图/ER 图/思维导图”等任一类型并落地到飞书，或用户给出飞书文档 URL 要求在其中画图，或用户说“同步到飞书/写到飞书画板”时，必须使用本技能。除上述 17 类内置模板外，本技能还提供「自由画图模式（freeform-drawing）」：当用户要求绘制油画/手绘插画/移动端 App 产品原型/地图/游戏画面/桑基图/任意参考图还原等模板覆盖不到的图，或显式说“自由绘图/自由发挥/不要套模板”时，同样必须使用本技能（输出依旧是可二次编辑的飞书画板）。生成路径严格遵循 Normalize → Select → Plan → Layout → Render → StaticCheck → VQA → Deliver 八步，禁止硬编码模板、禁止硬编码坐标、禁止补造用户未提到的业务内容。所有样式都从 assets/style-tokens/ 里读取（代码原生图、自由画图模式除外）。交付前必须通过质量门（按路由执行）与双 reviewer 视觉复核（任一评分低于 9 或出现 blocker 即失败）。
---

# design-lark-chart

把用户输入转化为合规、可读、可上传的飞书画板图。本 skill **不是**一个模板集，而是一条**内容驱动 + 样式注入 + 闭环质检**的管道。

## 定位

- **输入**：自然语言需求 / 飞书文档 URL / 结构化业务清单
- **中间产物**：按路由落盘到 `data/design-lark-chart/<session>/`
- **最终产物**：
  - DSL 路径：`board.json`（`@larksuite/whiteboard-cli` DSL v2）
  - SVG 高保真路径：`diagram.svg` + `board.openapi.json`（由 `whiteboard-cli -f svg --to openapi` 生成）
  - 代码原生路径：`diagram.mmd` / `diagram.puml`
  - 二者都必须附带飞书真实导出图与质量门证据

## 格式边界说明

本 skill 会同时接触 **代码语法** 与三种 JSON，但它们**不是同一层东西**：

- **`diagram.mmd` / `diagram.puml`**：Mermaid / PlantUML 源码。仅用于飞书原生支持代码图的场景，例如时序图、状态机图、标准流程图。

- **`assets/raw/<id>.json`**：从参考飞书画板导出的**官方原始结构**，信息最全，含节点细节与底层字段；只用于审查和抽取风格，**禁止直接传给 Planner**。
- **`assets/style-tokens/<id>.json`**：从 raw 抽出来的**风格指纹**，只保留色板 / 字号 / 形状 / 连线偏好；这是 Planner 结算 `style_budget` 的依据。
- **`<session>/board.json`**：`@larksuite/whiteboard-cli` 支持的 **DSL v2**，是 Render 阶段写出的声明式画板描述；它不是飞书 raw 协议本身，而是一个更高层、对布局更友好的输入格式。

关系如下：

```text
参考飞书画板
  -> raw/<id>.json
  -> style-tokens/<id>.json

用户语义输入
  + style-tokens/<id>.json
  -> plan.json
  -> board.json (DSL v2)
  -> whiteboard-cli --to openapi
  -> board.openapi.json / 飞书可写入的原始结构
  -> lark-cli whiteboard +update
```

必须明确：

1. **DSL v2 不是飞书官方 raw 协议的完整镜像**。它是 `whiteboard-cli` 支持的一层高阶输入格式，我们在本 skill 里又只使用其中一个**最小可验证子集**（见 `references/05-render-dsl.md`）。
2. **不能假设任意 DSL 都能无损覆盖 raw 的全部能力**。像复杂装饰、自定义细节、某些特殊连线行为，raw 可能能表达，但 DSL 未必有等价写法。
3. **不是所有图型都必须走 DSL**。对于飞书画板原生支持的代码图，优先走 `diagram.mmd` / `diagram.puml` -> `lark-cli whiteboard +update --input_format mermaid|plantuml` -> 飞书回读代码与导图验收。对于 `system-architecture` / `matrix-quadrant` / `sketch-architecture` 这类强依赖 preview 气质的图型，优先走 SVG 高保真路径，再转 OpenAPI 写入画板。
4. **本 skill 的保障方式不是“口头上认为可转”**，而是每次都实际走一遍对应路由的检查链。DSL 路径必须过 `whiteboard-cli --check`；SVG 路径必须过 `whiteboard-cli -f svg --check`、OpenAPI 转换和专项 lint；代码路径必须过 `+query --output_as code` round-trip 和真实飞书导图验收。
5. **只有落在当前 DSL / SVG / Mermaid / PlantUML 已验证子集内，并且经过实际写入和飞书回收验证的图型，才算支持**。未验证的图型不能因为“理论上应该能转”就对外承诺。

## 什么时候触发

| 触发信号 | 说明 |
|---|---|
| 用户明说"画 XX 架构图 / 流程图 / 时序图 / 泳道图 / 状态机 / ER 图 / 思维导图..." | 命中 `02-chart-taxonomy.md` 17 种固定图型之一即触发 |
| 用户要求"自由画 / 产品原型 / 游戏页面 / 桑基图 / 路线图 / 插画"，且固定图型覆盖不到 | 触发 `freeform-drawing`，走 SVG -> OpenAPI -> 飞书画板 |
| 用户提供飞书 docx / wiki URL 并要求"配图 / 画个图 / 给我画出来" | 先读文档，抽语义，再走完整管道 |
| 用户说"同步到飞书 / 写到画板 / 生成飞书画板" | 最后一步走 `lark-cli whiteboard +update` |

当前已补齐结构验证样例的固定图型（共 17 种）：

- `business-architecture`
- `system-architecture`
- `flowchart`
- `swimlane`
- `sequence`
- `mindmap`
- `org-chart`
- `state-machine`
- `er-diagram`
- `funnel`
- `gantt`
- `milestone`
- `matrix-quadrant`
- `link-architecture`
- `lark-style-architecture`
- `sketch-architecture`
- `complex-swimlane`

另外支持 1 个非模板化自由模式：

- `freeform-drawing`：当用户需求不属于上述固定图型，但明确需要飞书画板中的视觉表达、产品原型、复杂信息图、图解插画或自定义图表时触发。该模式必须走 `svg-openapi`，用 SVG 作为设计源，再转 OpenAPI 写入飞书画板；不得新增硬编码渲染器或把某个验收样例固化成模板。

注意：17 类图型都已补齐可复用 examples，但**不再要求全部是 JSON**。其中：

- `sequence` / `state-machine` / 标准 `flowchart` 优先使用 `.mmd`
- `mindmap` / `er-diagram` 优先使用 `.mmd`（必要时可切换 `.puml`）
- `funnel` 继续使用 DSL JSON，但必须满足颜色分层与去外框约束
- 其余图型是否走 DSL，以 `02-chart-taxonomy.md` 与 `05-render-dsl.md` 的路由规则为准

发布状态与覆盖面定义见 [`references/COVERAGE_REPORT.md`](references/COVERAGE_REPORT.md)。

## 什么时候不触发

- 一两句话就能说清的概念（不需要图）
- 用户要的是 Markdown 表格、代码片段、流程清单（不是视觉图）
- 用户明确要"内联 SVG 写入 markdown 文档"（那是另一回事，别和飞书画板混淆）

## 硬约束（出错就回退）

这些约束优先级高于"画得好看"：

1. **禁止硬编码模板**：不得为任何图型写"固定 N 层 + 固定颜色 + 固定文案"的渲染器。所有结构都由 Planner 阶段根据用户输入动态产出。
2. **禁止硬编码坐标**：所有几何由 `whiteboard-cli` 的 flex / dagre 布局引擎决定，或由 Layout 阶段的纯函数根据节点数计算。不允许代码里出现 `x=340` 这种魔法常量。
3. **禁止硬编码样式**：所有颜色 / 字号 / 圆角 / 线宽必须来自 `assets/style-tokens/<id>.json`。新颜色 / 新字号不允许在 Render 阶段临时引入。
4. **禁止内容补造**：Normalizer / Planner **不得**补充用户原文未出现的层级、模块、角色或节点。允许补技术性哨兵节点（如流程图的 start/end），但必须显式标注 `auto-added`。
5. **禁止跳过质量门**：`whiteboard-cli --check` errors > 0 或 VQA 任一评分 < 9 或出现 blocker，不得交付。

## 管道

见 [`references/01-pipeline.md`](references/01-pipeline.md)。

```
Normalize → Select → Plan → Layout → Render → StaticCheck → VQA → Deliver
```

每一步的**输入/输出/失败回退**都在 01 里给了表格，按里面做。

## 参考素材

从飞书官方"飞书画板.skill"文档（`Lww3d2rfwoE1SYxHtHicurYUn5d`）拉下来的 15 张标准画板作为**风格参考**，三件套沉淀：

```
assets/
├── previews/<id>.png          # 视觉锚，给多模态 LLM 看
├── raw/<id>.json              # 原始节点结构，审查时查阅；禁止传给 LLM
└── style-tokens/<id>.json     # 抽取出的风格指纹（色板/字号/形状/连线）
    _catalog.json              # 跨图聚合的 house_style
```

**只参考样式**（色板、字号、圆角、连线偏好），**不**套模板、**不**抄业务文案、**不**抄坐标。详见 [`references/02-chart-taxonomy.md`](references/02-chart-taxonomy.md) 与 [`references/03-style-system.md`](references/03-style-system.md)。

## references 索引

按职责组织，按需读取：

| 文件 | 什么时候读 |
|---|---|
| `references/01-pipeline.md`          | 每次生成都必读，熟悉八步管道与回退矩阵 |
| `references/02-chart-taxonomy.md`    | Select 阶段选图型时读 |
| `references/03-style-system.md`      | Plan 阶段挑 style_budget、Render 阶段落色时读 |
| `references/04-planner-contract.md`  | Plan 阶段产 plan.json 时必读（schema 严格） |
| `references/05-render-dsl.md`        | Render 阶段选 DSL / Mermaid / PlantUML 路由时读；走 DSL 时必读 |
| `references/06-quality-gates.md`     | Gate A/B 执行 + 按路由校验 + VQA rubric + 熔断规则 |
| `references/07-premium-style-contracts.md` | 生成 `system-architecture` / `matrix-quadrant` / `sketch-architecture`，或用户要求“更高级 / 贴近示例图 / 飞书画板风格”时必读 |
| `references/08-freeform-svg-mode.md` | 固定图型覆盖不到，或用户要求产品原型、游戏页面、桑基/路线图/插画等自由视觉表达时必读 |

## scripts

| 脚本 | 作用 | 什么时候跑 |
|---|---|---|
| `scripts/fetch_reference_boards.sh`  | 从官方 docx 拉 15 张参考画板到 assets/ | 首次部署 / 参考更新时 |
| `scripts/extract_style_tokens.py`    | 从 `assets/raw/` 抽出 style tokens 到 `assets/style-tokens/` | 参考画板变更后 |
| `scripts/check_board.sh`             | `whiteboard-cli --check`，Gate A 门禁 | Render 后每次都跑 |
| `scripts/lint_lark_style_architecture.py` | 检查飞书高级架构图是否退化成简单分层盒子 | `lark-style-architecture` 的 DSL Render 后 |
| `scripts/lint_premium_style.py` | 检查系统架构图 / 矩阵象限图 / 手绘风格架构图是否退化成普通盒子图 | 三类图的 SVG 或 DSL Render 后 |
| `scripts/lint_svg_quality.py` | 检查自由 SVG 的平台兼容性、图型指纹、颜色来源和视觉密度。可选 `--style-seed <id>` 借用某张固定 token 的色板，可选 `--plan <path>` 优先采用 `plan.style_budget` 作为允许色集，并带 `--strict-budget` 拒绝超集 | `freeform-drawing` 和强视觉 SVG Render 后 |
| `scripts/render_freeform.sh`         | 自由模式端到端门禁包装器：校验 `freeform_brief.json` schema → `whiteboard-cli -f svg --check`（按 brief.allowed_check_warnings 白名单判定）→ `lint_svg_quality.py --plan/--style-seed` → `--to openapi` 一体化产出 `board.openapi.json` 和 `render_freeform.report.json` | `freeform-drawing` 路径必须跑（替代手动串接 check + lint + convert） |
| `scripts/render_preview.sh`          | 本地渲染 PNG | Gate A 通过后、VQA 前 |

所有脚本默认把产物写到 `data/design-lark-chart/<session>/`，**不入 git**（`data/` 已在 `.gitignore`）。

## examples

- `references/examples/smoke_board.json`：最小可运行 DSL v2 文件，用于验证 `check_board.sh` 和 `render_preview.sh` 在本机可用。**不是模板**，不要照抄业务。
- `references/examples/<chart-type>.json`：DSL 路径图型的端到端验证样例。
- `references/examples/<chart-type>.mmd` / `references/examples/<chart-type>.puml`：代码原生图型的端到端验证样例。

## 扩展新图型的流程（当 17 种覆盖不到时）

1. 拿到样式参考画板 token，追加到 `data/design-lark-chart/reference_boards.json`。
2. 跑 `scripts/fetch_reference_boards.sh` 拉 png/raw。
3. 跑 `scripts/extract_style_tokens.py` 生成新 `<id>.json` 和刷新 catalog。
4. 把新 id 追加到 `references/02-chart-taxonomy.md` 的表里，补 signals/structure/fallback。
5. **不改任何硬编码模板**——新增图型应优先通过数据与路由扩展解决；只有当飞书代码图能力边界变化时，才允许调整路由规则。

## 交付前最终核验（缺一不可）

- [ ] 若走 DSL：`<session>/board.json` 的所有颜色能在 `plan.style_budget` 里回查
- [ ] 若走 DSL：`<session>/check.json` 的 `errors=0, warnings=0, issues=[]`
- [ ] 若走 SVG：`<session>/svg_check.json` 无 issue，且对应 lint 通过（强视觉固定图型跑 `lint_premium_style.py`；自由模式必须跑 `scripts/render_freeform.sh <session>`，由它统一产出 `render_freeform.report.json` 且 `ok=true`，禁止只手跑其中一步）
- [ ] 若走代码图：`<session>/roundtrip.code.json` 可回读源码，且 `syntax_type` 与预期一致
- [ ] 基于**真实飞书端导出图**完成 Gate B；若更新后立刻回读失败，先等待约 2 秒后重试，再判断是否为真实 blocker
- [ ] 会话目录完整，且包含对应路由的必需产物

任一未满足：停止交付，返回对应阶段修复（见 `06-quality-gates.md` 的回退矩阵）。

## 覆盖面

发布前覆盖面见 [`references/COVERAGE_REPORT.md`](references/COVERAGE_REPORT.md)。每次新增或降级图型，必须同步更新覆盖面定义；若仍存在 Gate B blocker，则不能对外发布。
