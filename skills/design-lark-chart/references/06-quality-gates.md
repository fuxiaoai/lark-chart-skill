# 06 · Quality Gates

两道门，缺一不可。

## Table of Contents

- Gate A: 路由级静态门（必过）
- Gate B: 视觉评审门（必过）
- 连续失败的熔断
- 交付前的最终核验清单

## Gate A: 路由级静态门（必过）

Gate A 必须**按渲染路由**执行，不能再默认所有图都用 `whiteboard-cli --check`。

### A1. DSL 路径

由 `whiteboard-cli --check` 执行，纯规则，不依赖 LLM。

```bash
npx -y @larksuite/whiteboard-cli@^0.2.0 -i <session>/board.json --check \
  > <session>/check.json
```

失败（退出码 != 0 或报告内容非空）→ **禁止继续**。按下表定位回退：

| check 类型 | 典型根因 | 回退到 |
|---|---|---|
| `node-overlap` | 节点间距不足或 Layout 宽度估算太小 | Layout：放大画布 / 扩宽列间距 |
| `text-overflow` | 文本超出节点边界 | Render：加 `measure_text` 预算；必要时 Plan 缩文案 |
| `connector-disconnected` | connector 起止点未对准节点锚点 | Layout：重新计算锚点 |
| `unknown-shape` | `composite_shape.type` 非法 | Render：回到合法 enum |

### A2. 代码原生路径（Mermaid / PlantUML）

由飞书实际写入与回读能力判定，最少包含 2 个检查：

1. `lark-cli whiteboard +update --input_format mermaid|plantuml` 成功
2. `lark-cli whiteboard +query --output_as code` 成功，且：
   - `syntax_type` 与预期一致
   - 回读代码不是空字符串
   - 关键语义未丢失（参与者 / 状态 / 决策节点仍在）

若代码路径通过 Gate A，还必须补飞书导出图：

```bash
lark-cli whiteboard +query \
  --whiteboard-token <token> \
  --output_as image \
  --output <session>/
```

失败回退：

| 失败现象 | 典型根因 | 回退到 |
|---|---|---|
| `no code blocks found` | 实际写入的不是代码图；走错路由或被覆盖成普通节点 | Route：改回 Mermaid / PlantUML / DSL |
| `syntax_type` 不符 | 路由选错或语法不被当前接口识别 | Render：修正代码语法；必要时切换 PlantUML |
| 导图成功但图法不标准 | 用代码画错了图，而不是布局问题 | Render：重写代码，不要用本地截图自我安慰 |

### A3. SVG 高保真 / 自由绘画路径

`system-architecture` / `matrix-quadrant` / `sketch-architecture` 在强视觉验收时必须执行：

```bash
whiteboard-cli -i <session>/diagram.svg -f svg --check > <session>/svg_check.json
whiteboard-cli -i <session>/diagram.svg -f svg --to openapi --format json > <session>/board.openapi.json
skills/design-lark-chart/scripts/lint_premium_style.py <chart_type> <session>/diagram.svg \
  > <session>/lint_premium.json
```

`freeform-drawing` 必须通过 `scripts/render_freeform.sh` 一体化执行（**禁止只手跑其中一步**）：

```bash
# 前置条件：会话目录下已有 diagram.svg / freeform_brief.json / plan.json
skills/design-lark-chart/scripts/render_freeform.sh <session> [--strict-budget]
# 产出：<session>/board.openapi.json
#       <session>/render_freeform.report.json （含 brief schema、whiteboard --check、lint、convert 四步状态）
```

`render_freeform.sh` 内部按序执行：

1. brief schema 校验：`freeform_brief.json` 必须含 `chart_type=freeform-drawing`、`freeform_mode`、`intent`、`visual_anchor`、`deliverables`；`plan.json` 必须含 `style_budget`
2. `whiteboard-cli -f svg --check`：errors==0；warnings 必须落在 `freeform_brief.allowed_check_warnings` 白名单内（如 illustration 模式可显式允许 `node-overlap`），否则视为 disallowed
3. `lint_svg_quality.py --mode <mode> --plan <plan> [--style-seed <id>] [--strict-budget]`：默认优先用 `plan.style_budget`，其次 style-seed，再降级到 catalog
4. `whiteboard-cli -f svg --to openapi`：产出 `board.openapi.json`

任一步失败 → 包装器 exit=1，且 `render_freeform.report.json` 内对应 gate `ok=false`；调试时再单独跑对应原子脚本定位问题。

失败（命令退出码 != 0，或 `lint_premium.json.ok != true`）→ **禁止写入飞书**。回退规则：

| 失败现象 | 典型根因 | 回退到 |
|---|---|---|
| `text-overflow` | SVG 文本预算不足，CJK 宽度估算偏小 | Layout：加宽容器或缩短标签 |
| `node-overlap` | 分区/卡片轨道间距不足 | Layout：增大 gap / padding |
| premium lint 失败 | 退化成普通盒子图，缺少 preview 版式指纹 | Plan / Render：重读 `07-premium-style-contracts.md` |
| freeform lint 失败 | SVG 使用不支持元素、缺少自由模式指纹、颜色越过 token | Plan / Render：重读 `08-freeform-svg-mode.md` |
| OpenAPI 转换失败 | SVG 使用了 parser 不稳定的元素或 transform | Render：简化为 rect/text/path/polyline 基础元素 |

## Gate B: 视觉评审门（必过）

仅在 Gate A 通过后执行。

### 执行协议

1. 取得**真实飞书导出图** `<session>/feishu.png`。
2. 若走 DSL，可额外保留本地 `preview.png` 作为辅助证据；若走代码路径，`preview.png` 不是必需品。
3. **并行**启动 2 个 reviewer：

   - Reviewer A：`subagent_type: ui-designer`，任务：对比 `preview.png` 与 `plan.json` 的意图是否一致，按 rubric 评分。
   - Reviewer B：`subagent_type: ui-designer`，独立评审（不得看到 A 的结论）。

4. 两份结果分别落到 `<session>/vqa/reviewer_a.json` 和 `reviewer_b.json`。

如果飞书图片回收链路异常，例如 `lark-cli whiteboard +query --output_as image` 返回统一占位图、空图或明显不是当前白板内容：

- 立即记为 blocker
- 可以继续保留 `preview.png`、`board.openapi.json` 与 `whiteboard +query --output_as raw|code` 的 round-trip 证据
- **不得**把本地 `preview.png` 冒充 Gate B 结果，也不得伪造 reviewer 评分
- 会话应写明 `vqa.md` / `COVERAGE_REPORT.md`，等待导出链路恢复后重跑 Gate B

飞书白板在 `+update` 后可能短暂返回：

- `doc is applying`
- `doc data is not ready`

这不等于写入失败，而是最终一致性窗口。处理方式：

- `sleep 2` 后重试 `whiteboard +query --output_as raw`
- raw 成功后再执行 `whiteboard +query --output_as image`
- 只有重试后仍返回占位图或异常，才记为真正的 Gate B blocker

### Rubric（每项 0-10）

| 维度 | 关注点 |
|---|---|
| 颜色       | 是否全部落在 `plan.style_budget` 里的色；语义色（danger / success / external）映射是否正确 |
| 字体       | 字号层级（title > section > body > hint）是否清晰；是否有文字挤压/换行过多 |
| 形状与圆角 | 是否与该图型 style-tokens 里的 composite_types 和 border_styles 匹配 |
| 箭头       | 方向、箭头头型、起止点是否对齐节点边界；**头型必须与 `style_budget.connector_arrow_end` 一致** |
| 连线       | 是否出现相交、覆盖、穿过无关节点；**折线/直线/曲线形态必须与 `style_budget.connector_shape` 一致** |
| 连线密度   | 连线数是否 ≥ `max(⌈节点数/8⌉, 分组数-1)`；关键穿层/跨分组关系是否表达出来 |
| 图型契约   | 是否匹配 05-render-dsl.md `图型风格契约` 表（层级容器背景、文本色主调） |
| 布局可读性 | 留白是否均匀；视觉主路径是否一眼可见；是否"一张图能讲完一件事" |

### 路由专项 blocker

- `sequence`：缺生命线、返回虚线缺失、消息顺序错乱、被画成普通横向流程
- `state-machine`：起止态缺失、回退边与主路径缠在一起、失败/重试关系表达不清
- `flowchart`：无意义外框、分支标签压线、主路径过窄导致所有线聚成一束
- `system-architecture`：没有右侧外部依赖/运行时侧栏、主区不是多层容器、缺图例或层标签、只有白色服务卡片堆叠、弱网格背景缺失
- `matrix-quadrant`：四象限被画成横向四列、缺横纵轴标签、象限背景无颜色区分、象限内项目被过度卡片化导致坐标关系不明显
- `sketch-architecture`：没有虚线阶段分区、没有手绘双线/下划线笔触、普通圆角卡片替代草图卡片、关键跨阶段连线缺失
- `mindmap`：根节点不清晰、层级错乱、分支密度过高导致不可读
- `er-diagram`：缺关系基数、字段挤压不可读、仅罗列表未表达关系
- `funnel`：阶段全白无颜色层次、宽度递减不明显、主标题和漏斗主体关系分离
- `lark-style-architecture`：退化成三层横向框图、模块列少于 4 个、模块内没有二级卡片/要点、色彩只有白底描边、没有顶部核心逻辑横幅、未通过 `lint_lark_style_architecture.py`
- `freeform-drawing`：固定图型能表达却偷换成自由模式、缺少主视觉隐喻、只是一堆卡片、SVG 使用 `filter/radialGradient/pattern/clipPath/mask/foreignObject`、未通过 `lint_svg_quality.py`、最终只交付 PNG 而非飞书画板节点

### 通过条件（从严）

- **任一 reviewer 总分 `< 9`** → 失败
- **任一 reviewer 列出 blocker（箭头缺失 / 连线断开 / 色彩明显错位 / 文字裁切 / 连线形态与 style_budget 不一致 / 连线密度不足 / 路由专项 blocker）** → 失败
- **禁止取平均分放宽**：用最差视角兜底。
- **禁止把 `whiteboard-cli` 的 `quality.connectorStyle / connectorRefs` 分数当 Gate B 结论**：该指标在 0.2.x 存在已知计算偏差，仅作参考。Gate B 只认 subagent 视觉评审与本文件 Rubric。

### 失败回退

- 颜色/字号错 → Render
- 对齐/留白/交叉错 → Layout
- 角色/节点缺 → Plan
- 输入层面缺 → Normalize（必要时向用户追问）

## 连续失败的熔断

- 同一会话连续 **3 次** VQA 失败 → 停止自动迭代
- 给用户汇报：
  1. 当前 plan 摘要
  2. VQA 的 blocker 清单
  3. 候选修复方向（建议 2-3 个，让用户一次性选）

## 交付前的最终核验清单

交付（写入飞书）之前，必须满足**全部**：

- [ ] 若走 DSL：`check.json` 无 issue
- [ ] 若走 SVG：`svg_check.json` 无 issue，并存在 `board.openapi.json`
- [ ] 若走强视觉固定图型 SVG：`lint_premium.json.ok == true`
- [ ] 若走自由模式 SVG：`<session>/render_freeform.report.json.ok == true`（该报告内部聚合 brief schema / whiteboard --check / lint / convert 四步；禁止绕过包装器只保留其中一步的 json）
- [ ] 若走代码图：`roundtrip.code.json` 成功回读源码，且 `syntax_type` 与预期一致
- [ ] `vqa/reviewer_a.json.score_total` ≥ 9 且无 blocker
- [ ] `vqa/reviewer_b.json.score_total` ≥ 9 且无 blocker
- [ ] 若走 DSL：`board.json` 里出现的所有颜色都能在 `plan.style_budget` 里回查
- [ ] 会话目录下同时存在路由对应的关键产物（DSL: `layout.json / board.json / check.json / feishu.png`；代码图: `diagram.mmd|diagram.puml / roundtrip.code.json / feishu.png`）

任一未满足，停。
