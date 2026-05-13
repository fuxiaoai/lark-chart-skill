# 01 · Pipeline 总览

`design-lark-chart` 是一个**由内容驱动、由样式 token 约束**的飞书画板生成管道。它不做模板匹配，不走硬编码坐标，不预设模块名。所有结构都从用户输入中派生，所有样式都从 `assets/style-tokens/` 里派生。

注意：并非所有图型都应该落到 DSL。对于飞书画板**原生支持代码语法**且标准样式强于手工排版的图型，应优先走 Mermaid / PlantUML 路径，避免生成"像图但不标准"的伪时序图或伪状态机图。对于 `system-architecture` / `matrix-quadrant` / `sketch-architecture` 这类用户明确要求贴近 `assets/previews/` 气质的图型，优先走 SVG 高保真路径，再由 `whiteboard-cli` 转成 OpenAPI 写入画板。对于固定图型覆盖不到的产品原型、游戏页面、插画、桑基流量图等需求，选择 `freeform-drawing`，读 `08-freeform-svg-mode.md` 后走同一条 SVG -> OpenAPI 路径。

本文是主干流程图，告诉调用方：**每一步要做什么、不做什么、产物落在哪里、失败怎么回退。**

## Table of Contents

- 管道形态
- 每一步的硬约束
- 产物落盘
- 回退矩阵

## 管道形态

```
用户输入（自然语言 / 飞书文档 URL / 结构化业务清单）
        │
        ▼
(1) Normalize  ─────────── 统一语义对象：nodes / groups / edges / annotations
        │                    落地：data/design-lark-chart/<session>/normalized.json
        ▼
(2) Select     ─────────── 选图表类型 + 选风格模板
        │                    输入：normalized.json + 用户显式指定（可选）
        │                    输出：chart_type ∈ 02-chart-taxonomy.md（含 freeform-drawing）
        │                    落地：data/.../selection.json
        ▼
(3) Plan       ─────────── LLM 动态产出结构化 plan（见 04-planner-contract.md）
        │                    输入：normalized.json + 该类型的 style-tokens + 预览 PNG 描述
        │                    输出：plan.json（仍然是语义的，不含坐标）
        ▼
(4) Route      ─────────── 判断走哪条渲染路径
        │                    A. 代码原生路径：Mermaid / PlantUML
        │                    B. DSL 路径：whiteboard-cli DSL v2
        │                    C. SVG 高保真路径：SVG -> OpenAPI
        ▼
        ├─ A. Code-native
        │    (5A) Render Code ───── 生成 `diagram.mmd` / `diagram.puml`
        │    (6A) Round-trip Check ─ 写入飞书后 `+query --output_as code`
        │                           必须能回读代码，且语法类型正确
        │    (7A) Export Preview ─── 飞书导出真实 PNG 至 data/.../feishu.png
        │
        ├─ B. DSL
             (5B) Layout      ───── 根据 plan 推导尺寸 / 连线路径
             │                  纯函数，不依赖 LLM；按图类型分发
             │                  输出：layout.json（包含逻辑布局结果）
             (6B) Render DSL  ───── 把 layout + style-tokens 拼成 Lark whiteboard DSL
             │                  输出：<session>/board.json
             (7B) Static Check ──── whiteboard-cli --check：几何门禁
             │                  失败 → 回到 (5B) Layout；屡次失败回到 (3) Plan
             (8B) Export Preview ── 本地 preview.png + 飞书导出 feishu.png
        │
        └─ C. SVG High-fidelity / Freeform
             (5C) Layout      ───── 模型根据 plan 动态设计画布、分区、网格和卡片轨道
             │                  输出：layout.json（不写死业务坐标，所有尺寸由节点数/分组数推导）
             (6C) Render SVG  ───── 模型当次输出 diagram.svg；颜色/字号只取 style_budget
             (7C) Static Check ──── whiteboard-cli -f svg --check + 对应 SVG lint
             │                  失败 → 回到 (5C)/(6C)；若两轮失败再回 DSL
             (8C) Convert/Export ─ whiteboard-cli -f svg --to openapi，写入后导出 feishu.png
        ▼
(9) VQA Loop  ─────────── 双 reviewer 基于**真实飞书导出图**评审（见 06-quality-gates.md）
        │                    任一 <9 或出现 blocker → 回到 (3) / (4) / (5B)
        ▼
(10) Deliver   ─────────── 交付飞书链接、回收图、验证结论
```

## 每一步的硬约束

| 步骤 | 允许 | 禁止 |
|---|---|---|
| Normalize | 提取原文中的层级/模块/角色/动作 | 自行补齐用户没写的层 |
| Select | 按语义匹配 chart_type；必要时让用户选 | 默认退回某一种图型"兜底" |
| Plan | 引用 style-tokens 作为软约束 | 从参考画板 raw JSON 抄坐标 |
| Route | 根据图型与飞书能力选择 Mermaid / PlantUML / DSL / SVG | 为了统一流程，强行把时序图或状态机图降级成 DSL 拼图；或在强视觉图型上忽略 preview 契约 |
| Layout | 仅 DSL 路径需要，基于 plan 动态计算 | 使用魔法常量（`x=340`、`viewBox=680xN` 等固定值） |
| Render | 尊重 style-tokens、代码语法或 DSL 约束 | 擅自引入 tokens 之外的颜色；把代码图伪装成普通节点拼图；为强视觉图型新增绘图脚本或固定 SVG 模板 |
| Check | DSL 看 `whiteboard-cli --check`；代码图看 code round-trip + 飞书导图 | 看图"觉得还行"就跳过 |
| VQA | 要求 reviewer 说出失分项 | 用平均分稀释 blocker |
| Deliver | 在 VQA 通过后写入 | 未通过提前上传 |

## 产物落盘

全部产物落在 `data/design-lark-chart/<session_id>/`，不进 git：

```
data/design-lark-chart/<session>/
├── normalized.json
├── selection.json
├── plan.json
├── route.json        # code-native / dsl / svg
├── layout.json       # DSL / SVG 路径存在
├── board.json        # 仅 DSL 路径存在
├── diagram.svg       # 仅 SVG 路径存在
├── diagram.mmd       # 仅 Mermaid 路径存在
├── diagram.puml      # 仅 PlantUML 路径存在
├── preview.png       # 本地渲染（DSL / SVG 路径）
├── feishu.png        # 飞书真实导出图
├── check.json        # 仅 DSL 路径：--check 结果
├── svg_check.json    # 仅 SVG 路径：-f svg --check 结果
├── lint_premium.json # 仅高级风格专项门禁存在
├── roundtrip.code.json  # 仅代码路径：+query --output_as code 结果
└── vqa/
    ├── reviewer_a.json
    └── reviewer_b.json
```

## 回退矩阵

- **DSL Check 失败（节点重叠/文字溢出）**：回到 Layout；连续 2 次失败 → 回到 Plan 缩减节点密度。
- **SVG Check / premium lint 失败**：先回 Render/Layout 修复预览契约；连续 2 次失败 → 回 DSL，但必须在 `vqa.md` 说明降级原因。
- **Code round-trip 失败（无法回读代码 / 语法类型不符）**：回到 Route；必要时从 Mermaid 切 PlantUML，或改回 DSL。
- **VQA 任一 <9**：按 reviewer 的失分维度定位：
  - 颜色/字体/圆角错 → Render
  - 对齐/留白/层级错 → Layout（DSL）或 Route/Code（代码图）
  - 信息缺失/层级错 → Plan
  - 输入没有该语义 → Normalize（必要时向用户追问）
- **连续 3 次未通过**：停止自动迭代，向用户说明当前阻塞点与候选方案，请用户裁定。
