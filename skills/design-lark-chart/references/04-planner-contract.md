# 04 · Planner Contract

Planner 是**唯一由 LLM 驱动**的阶段。它把语义输入转成"不含坐标、但结构完整"的 plan。坐标完全由 Layout 阶段用纯函数决定。

## Table of Contents

- 输入
- 输出 Schema
- 必须遵守
- system-architecture Planner 补充约束
- matrix-quadrant Planner 补充约束
- sketch-architecture Planner 补充约束
- lark-style-architecture Planner 补充约束
- 失败模式与回退

## 输入

Planner 的输入只有三件事：

1. `normalized.json` — 来自用户输入的结构化语义（节点、分组、关系、注释）
2. `selection.json` — 已选定的图型 id（如 `flowchart`）
3. 对应 `assets/style-tokens/<id>.json` 的全部内容
4. 对应 `assets/previews/<id>.png` 的**描述**（如果你是多模态模型，可以直接看图；否则读 token 文件的聚合字段）

> 不允许把 `assets/raw/<id>.json` 传给 Planner。

## 输出 Schema

Planner **必须**输出一份符合以下 JSON Schema 的 plan。schema 严格（additionalProperties: false）。

```jsonc
{
  "version": "1.0",
  "chart_type": "flowchart",         // 与 selection.json 一致
  "title": "string, 必填",
  "subtitle": "string, 可选",

  // 语义节点。Planner 决定有几个，Layout 决定它们摆在哪。
  "nodes": [
    {
      "id": "n1",                    // 内部唯一 id，Layout/Render 通过它引用
      "label": "string",             // 节点显示文字
      "role": "start | end | step | decision | group-header | actor | milestone | ...",
      "semantic": "normal | emphasis | danger | success | external | hint",
      "group": "string | null",      // 所属分组 id（Layout 用来做泳道/分层）
      "notes": "string | null"       // 辅助文字，位置由 Layout 决定
    }
  ],

  // 语义分组，用于泳道/分层/分区。Layout 阶段决定怎么排版。
  "groups": [
    {
      "id": "g1",
      "label": "string",
      "axis": "row | column | cluster",   // row=泳道横行, column=垂直分层, cluster=自由聚簇
      "order": 0
    }
  ],

  // 节点之间的关系。不写坐标。
  "edges": [
    {
      "from": "n1",
      "to":   "n2",
      "label": "string | null",
      "kind":  "sequence | branch-yes | branch-no | async | feedback | dependency",
      "semantic": "normal | emphasis | danger | success"
    }
  ],

  // 取自 style-tokens 的结算值。Render 只认这里的值。
  "style_budget": {
    "primary_fill":    "#....",
    "primary_border":  "#....",
    "accent_border":   "#....",
    "danger_border":   "#....",
    "success_border":  "#....",
    "body_font_size":  14,
    "title_font_size": 20,
    "label_color":     "#....",
    "connector_shape":     "straight | right_angled_polyline | curve",   // 必填
    "connector_arrow_end": "none | line_arrow | solid_arrow",            // 必填
    "connector_color":     "#....",                                       // 必填
    "layer_fill":          "#....",                                       // 分层容器填充（system/business/link 架构必填）
    "layer_border":        "#....",                                       // 分层容器描边（system/business/link 架构必填）
    "module_fills":        ["#...."],                                     // lark-style-architecture 必填：模块列浅色填充
    "module_borders":      ["#...."],                                     // lark-style-architecture 必填：模块列描边
    "card_fill":           "#....",                                       // lark-style-architecture 必填：模块内白色卡片
    "muted_text_color":    "#....",                                       // lark-style-architecture 必填：说明/要点文字
    "highlight_fill":      "#...."                                        // lark-style-architecture 必填：胶囊或终态强调
  },

  // 强视觉图型必填。描述 preview 里的版式气质，不含业务文案和坐标。
  "style_profile": {
    "route_preference": "svg-openapi | dsl | mermaid | plantuml",
    "visual_anchor": "system-architecture | matrix-quadrant | sketch-architecture | ...",
    "layout_signature": ["string"],
    "must_have": ["string"],
    "must_not": ["string"]
  },

  // freeform-drawing 必填。固定图型为空或省略。
  "freeform_brief": {
    "mode": "sankey | roadmap | prototype | illustration | custom",
    "visual_metaphor": "string, 说明主视觉或空间隐喻",
    "composition": "string, 说明画面骨架，如 左到右流向 / 时间轴 / 前中后景",
    "editable_elements": ["string, 需要尽量转成可编辑节点的元素"],
    "svg_constraints": ["string, 平台兼容约束，如 no filter / text as text"],
    "content_limits": ["string, 哪些内容不能补造"]
  },

  // 自检字段：Planner 自己先算一遍复杂度，Layout 按这个分配画布
  "density_hint": {
    "node_count": 12,
    "max_depth":  4,
    "has_branches": true
  }
}
```

## 必须遵守

1. **每个 node.id 唯一，且只使用 `[a-z0-9_-]`**。
2. **所有 edge.from / edge.to 必须在 nodes[] 里有定义**。
3. **不允许新增 style_budget 之外的颜色或字号**。
4. **不允许在 plan 里写 x/y/width/height**。坐标是 Layout 的事。
5. **Planner 不能补造内容**：用户没提到的层级/节点不得凭空加入（除非是技术上必须的 start/end 节点，且要在 notes 里标注"auto-added: entry sentinel"）。
6. **style_budget 必须从 `assets/style-tokens/<chart_type>.json` 结算**：
   - `connector_shape` = token 里 `connector.shapes[0].value`
   - `connector_arrow_end` = token 里 `connector.arrow_styles[0].value`
   - `connector_color` 取 token 里连线色号 top1，若无则使用 `#b8bec8`
   - `primary_border` 取 `palette.border_colors[0].value`
   - `label_color` 取 `palette.text_colors[0].value`
   - `layer_fill/layer_border` 分别取 `palette.fill_colors` 中出现次数 >= 3 的浅色 / `palette.border_colors` 中出现次数 >= 3 的中性色
7. **连线密度下限**：`edges.length >= max(⌈nodes.length / 8⌉, groups.length - 1)`。低于此值视为信息缺失，必须回到 Planner 补齐真实业务关系（不是凑数）。
8. **强视觉图型必须写 style_profile**：`system-architecture` / `matrix-quadrant` / `sketch-architecture` 必须把 `07-premium-style-contracts.md` 中的图型契约落到 `layout_signature/must_have/must_not`。这不是可选描述；缺失时 Route 阶段应打回 Plan。
9. **自由模式必须写 freeform_brief**：`freeform-drawing` 必须读 `08-freeform-svg-mode.md`，并把用户意图转换成 `mode / visual_metaphor / composition / editable_elements / svg_constraints / content_limits`。缺失时 Route 阶段应打回 Plan。

## system-architecture Planner 补充约束

系统架构图必须先判断输入是否足够形成 preview 级架构表达：

1. **主架构区**：至少 3 个分层或分区，且每层有 2 个以上可归纳模块；否则降级成 `link-architecture`。
2. **侧栏 / 外部依赖**：如果输入提到 IAM、观测、Runtime、基础设施、三方系统等，必须放入独立侧栏或底座，而不是混进主层。
3. **图例与优先级**：只有用户输入出现 P0/P1、优先级、阶段建设等语义时才画图例；不要凭空补造。
4. **style_profile.must_not** 必须包含：`flat three-lane boxes`、`all-white cards only`、`missing dependency sidebar`。

## matrix-quadrant Planner 补充约束

矩阵象限图必须先结算两个轴：

1. 横轴与纵轴必须来自用户语义；若用户只说"四象限"但没有轴，默认可用 `价值` × `复杂度/成本`，并在 `normalized.json` 标注 `assumed-axis`。
2. `groups` 必须正好表达四个象限（或用户明确要求的 3×3），每个象限保留顺序和标题。
3. 象限内容优先是 bullet item；除非用户明确要求卡片，否则不要给每个 item 画独立大卡。
4. **style_profile.must_not** 必须包含：`four horizontal columns`、`missing axis labels`、`card wall instead of matrix`。

## sketch-architecture Planner 补充约束

手绘风格架构图不是"边框换成绿色/黄色"：

1. 必须把语义组织成 2-4 个阶段、泳道或模块区；没有阶段语义时，用用户输入中的主流程顺序生成阶段标签。
2. 每个阶段建议 2-4 个短节点；长句要压缩为卡片标题，说明放 notes。
3. 关系只保留关键跨阶段链路，避免满屏连线。
4. **style_profile.must_not** 必须包含：`plain rounded rectangles`、`no dashed zones`、`no hand-drawn strokes`。

## lark-style-architecture Planner 补充约束

这个图型不是普通分层架构图的换皮。Planner 选择它时，必须把输入语义归成以下结构：

1. **核心逻辑横幅**：1 个全局主题，下面承接 2-4 个核心判断/策略点。
2. **模块列**：4-6 个主模块，每个模块对应一个 `group`，`axis="column"`，并保留模块顺序。
3. **模块内细节**：每个模块至少 2 个二级节点；能形成列表的内容放进同一 detail card，不要拆成一排孤立小盒子。
4. **跨模块关系**：至少表达核心逻辑到模块、模块到模块的真实依赖；不得只画父子垂直箭头。
5. **风格预算**：`module_fills/module_borders/card_fill/muted_text_color/highlight_fill` 必须从 `assets/style-tokens/lark-style-architecture.json` 里取，允许使用低频但在 preview 中关键的浅蓝/浅紫/浅黄/浅红/浅绿。

输入不满足 4 个模块或模块内细节不足时，不能靠补造节点凑数；应回退到 `business-architecture` / `system-architecture`，或一次性向用户要补充信息。

## freeform-drawing Planner 补充约束

自由模式不是“不知道画什么就随便画”。Planner 必须先判断用户意图属于哪一类：

1. **`sankey`**：有来源、去向、占比、流量、归因或贡献度语义。`nodes` 表示来源/中间桶/结果，`edges` 必须带权重或相对强弱。没有数值时可用相对粗细，但要在 `notes` 标注 `assumed-weight-order`。
2. **`roadmap`**：有时间、版本、阶段、里程碑、依赖或优先级语义。`groups` 表示阶段/泳道，`nodes` 表示里程碑，`edges` 只表达真实依赖。
3. **`prototype`**：用户要产品原型、游戏页面、页面状态或 UI 布局。`groups` 表示屏幕区域，`nodes` 表示控件/卡片/状态；不得把界面画成纯说明文档。
4. **`illustration`**：用户要视觉场景、隐喻图或纯 SVG 插画。`nodes` 可是视觉对象，`edges` 可为空；必须在 `freeform_brief.composition` 说明前景/中景/背景或主次层次。
5. **`custom`**：以上都不匹配但仍有明确视觉目标。必须说明为什么固定 17 类不合适。

所有自由模式都必须：

- 从 `_catalog.json.house_style` 和可选 `style_seed` 结算颜色，不临时发明色板。
- 在 `style_profile.must_not` 写入：`fixed template mimicry`、`hardcoded example coordinates`、`png-only delivery`。
- 把验收重点写清楚：信息是否表达准确、SVG 是否平台兼容、飞书导出是否仍然美观。

## 失败模式与回退

| 现象 | 根因 | 处理 |
|---|---|---|
| nodes 数 > style-tokens 里该图型的 node_count × 2 | Planner 把文字碎片都变节点了 | 退回让它按二级标题聚合 |
| 出现 role 不在枚举里 | Planner "创造"了角色 | 拒绝，要求回到 enum |
| edge 指向不存在的 node | 引用错 | 拒绝 |
| 同一 edge 出现 >= 2 次 | 冗余 | 去重 |

任一失败都必须在当前会话内修正，不允许带到 Layout。
