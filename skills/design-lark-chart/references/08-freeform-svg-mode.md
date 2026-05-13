# 08 · Freeform SVG Mode

`freeform-drawing` 解决的问题：用户想在飞书画板里画的东西不属于固定 17 类图型，或者固定图型会把视觉意图压扁。例如流量归因桑基图、产品路线图、游戏页面、产品原型、纯 SVG 场景插画。

这不是模板库。它是一条更自由但更严格的 SVG 设计路径：用户意图 -> `freeform_brief` -> `diagram.svg` -> `whiteboard-cli -f svg --check` -> OpenAPI -> 飞书真实导出 -> 双 reviewer。

## 为什么之前画得弱

常见弱点不是底层工具不行，而是技能实现把模型逼进了“安全但平庸”的输出：

- 过度依赖 DSL 固定盒子，导致任何需求都变成矩形卡片阵列。
- 只约束语法正确，没有约束构图、视觉隐喻、前后景、流量宽度、时间节奏、UI 状态等设计语言。
- 没有自由模式，固定 taxonomy 覆盖不到时只能硬塞到流程图或架构图。
- 缺少 SVG 专项质量门，导致“能转 OpenAPI”被误当成“好看且可交付”。

SVG 能画得更漂亮，前提是：把 SVG 当设计源，而不是当 DSL 的另一种语法；同时用 lint 和飞书导出图兜住平台兼容性。

## 参考文档的可复用启发

从用户给出的飞书示例文档可抽出的是“视觉方法”，不是可复制模板：

- **桑基图**：三列节点表达来源、承接页、最终行为；流带宽度表达贡献，曲线按目标排序减少交叉。可复用的是“带宽 + 平滑流向 + 分列归因”，不是具体业务文案。
- **产品路线图**：水平时间轴建立主节奏，事件卡片围绕轴上下或分泳道展开，节点圆点和引导线把日期与事件绑定。可复用的是“时间节奏 + 卡片层次 + 依赖线”，不是固定年份或产品名。
- **雨后山林清晨插画**：用多层 polygon 表达远中近景，用 circle 和透明叠层表达太阳光晕，用简化树形和飞鸟点缀氛围。可复用的是“前中后景 + 低饱和叠色 + 几何化自然物”，不是某一组坐标。

这些启发只能进入 `freeform_brief.composition` 和 `style_profile.layout_signature`，禁止进入渲染脚本。

## 触发

命中以下任一信号时，Select 可选 `freeform-drawing`：

- 用户明确说“自由画 / 自己发挥 / 不在模板里 / 画得更漂亮 / 像示例文档那种”
- 用户要求产品原型、游戏页面、运营大图、故事图、图解插画、场景插画
- 用户要求桑基图、鱼骨图、飞轮图、地图式图解等当前 taxonomy 未覆盖的复杂信息图
- 固定 17 类可以勉强表达结构，但会明显损失主视觉或空间隐喻

不触发：

- 标准时序图、状态机、ER、甘特、流程图等代码图法更准确的场景
- 用户只是要列表、表格或一段文字解释
- 需求没有任何视觉目标，且选错会导致大返工；此时按提问纪律一次性确认

## Plan 必填：freeform_brief

Planner 必须输出：

```jsonc
{
  "freeform_brief": {
    "mode": "sankey | roadmap | prototype | illustration | custom",
    "visual_metaphor": "主视觉隐喻",
    "composition": "画面骨架",
    "editable_elements": ["尽量保持为可编辑节点的元素"],
    "svg_constraints": [
      "text must stay as <text>",
      "avoid filter/radialGradient/pattern/clipPath/mask/foreignObject",
      "prefer rect/circle/ellipse/polygon/path/polyline"
    ],
    "content_limits": ["不得补造用户未给出的业务模块、比例或功能"]
  }
}
```

## SVG 创作约束

必须：

- `diagram.svg` 是唯一设计源；后续 JSON、PNG、飞书画板都由它派生。
- 文本使用 `<text>` / `<tspan>`，不要把文字转 path。
- 使用平台稳定元素：`rect`、`circle`、`ellipse`、`polygon`、`line`、`polyline`、`path`、`text`、`g`、`defs/marker`。
- 为关键对象加 `data-role`，让 lint 能识别画面意图。
- 颜色从 `_catalog.json.house_style` 和选定 `style_seed` 结算；允许用 `opacity` 叠层，不允许临时发明色板。
- 画布留白要足；核心信息区与装饰区分层。

禁止：

- 新增“桑基图生成器”“路线图生成器”“雨后山林模板”这类硬编码渲染器。
- 使用 `filter`、`radialGradient`、`pattern`、`clipPath`、`mask`、`foreignObject`。
- 只画卡片墙，用标题解释“这是桑基 / 路线图 / 插画”。
- 只交付 PNG 或截图。

## mode 指纹

### sankey

适合流量归因、渠道贡献、成本去向、用户路径。

必须具备：

- 左中右或左到右流向。
- 至少 4 条 `data-role="sankey-flow"` 的宽路径；线宽表达权重或相对强弱。
- 来源、中间归因桶、结果至少 3 组文本标签。
- 流带不能全部等宽；无数字时用相对排序并标注 `assumed-weight-order`。

### roadmap

适合产品路线图、版本规划、项目阶段。

必须具备：

- 时间轴或阶段轴，`data-role="roadmap-axis"`。
- 至少 3 个阶段/泳道，`data-role="roadmap-track"`。
- 至少 5 个里程碑，`data-role="roadmap-milestone"`。
- 依赖线只表达真实依赖，不为装饰乱连。

### prototype

适合产品原型、游戏页面、界面状态。

必须具备：

- 画面外框或设备框，`data-role="prototype-screen"`。
- 主要区域分区，`data-role="prototype-surface"`。
- 交互控件/卡片/状态，`data-role="prototype-control"`。
- 视觉上像可用页面，而不是说明文档。

### illustration

适合“雨后山林清晨”这类场景图或抽象概念插画。

必须具备：

- 前景/中景/背景层，至少 5 个 `data-role="landscape-layer"` 或等价层。
- 氛围元素，至少 3 个 `data-role="atmosphere"`。
- 主视觉对象，至少 1 个 `data-role="hero-object"`。
- 可以少文字，但必须有 `<title>` / `<desc>`。

### custom

必须在 `freeform_brief.visual_metaphor` 和 `composition` 里说明为什么不是上述四类。lint 只检查通用兼容性、颜色、角色密度和非卡片墙退化。

## 质量门

自由模式的 Gate A 必须通过 `scripts/render_freeform.sh` 一体化执行（不要再手跑下面三条命令的拼接）：

```bash
# 前置：<session>/ 下已有 diagram.svg / freeform_brief.json / plan.json
skills/design-lark-chart/scripts/render_freeform.sh <session> [--strict-budget]
# 产出：<session>/board.openapi.json
#       <session>/render_freeform.report.json （ok=true 才允许进 Gate B）
```

`render_freeform.sh` 内部串联 brief schema 校验、`whiteboard-cli -f svg --check`（按 `freeform_brief.allowed_check_warnings` 白名单判定）、`lint_svg_quality.py --plan/--style-seed`、`whiteboard-cli -f svg --to openapi`。详见 `06-quality-gates.md`。

Gate B 仍只认真实飞书导出图，不认本地 PNG。

## 验收参考案例

`references/examples/freeform-drawing.prompts.md` 只保存验收 prompt，不保存可复用 SVG 模板。每次验证都应重新按 prompt 生成 SVG，避免把某次样例固化成技能能力。
