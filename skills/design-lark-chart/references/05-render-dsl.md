# 05 · Render DSL

本文件主要描述 **DSL 路径** 的 Render 规则，但 `design-lark-chart` 现已采用**按图型分路由**的渲染策略：

- **代码原生路径**：`sequence` / `state-machine` / 标准 `flowchart` / `gantt` 优先走 Mermaid 或 PlantUML
- **DSL 路径**：架构图、泳道图、漏斗图、矩阵、复杂流程等继续走 `@larksuite/whiteboard-cli` DSL v2
- **SVG 高保真路径**：`system-architecture` / `matrix-quadrant` / `sketch-architecture` 在用户要求贴近 preview 或"更高级"时优先走 SVG，再由 `whiteboard-cli -f svg --to openapi` 转写飞书画板
- **SVG 自由绘画路径**：`freeform-drawing` 永远走 SVG -> OpenAPI，不走 DSL 模板化渲染

只有当图型明确落到 DSL 路径时，才生成 `<session>/board.json`。

本文只覆盖 `design-lark-chart` 需要的**最小子集**。完整 schema 以 `@larksuite/whiteboard-cli` 官方为准（package README、npm 包），或直接查阅 `larksuite/cli` 仓库的 `skills/lark-whiteboard/references/{schema,layout,connectors,style}.md`。

## Table of Contents

- DSL 顶层
- 我们会用到的节点类型
- 最小可运行示例
- 路由选择
- 代码原生图契约
- 两种布局路径（仅 DSL）
- 强制规则
- 本地验证流程
- 上传到飞书

## DSL 顶层

```typescript
interface WBDocument {
  version: 2;
  nodes: WBNode[];   // connector 必须写在最顶层，不能嵌进 frame.children
}
```

## 我们会用到的节点类型

| type | 用途 | 关键字段 |
|---|---|---|
| `frame`   | 分组 / 泳道 / 分层容器       | `layout: 'horizontal' \| 'vertical' \| 'dagre'`；`gap`；`padding`；`children` |
| `rect`    | 常规节点（步骤、模块、能力） | `width`/`height`；`borderRadius`；`text`；`fillColor`/`borderColor`/`textColor`；`textAlign`/`verticalAlign` |
| `ellipse` | 起止节点（圆 / 胶囊）        | 同 rect |
| `diamond` | 决策点                       | 同 rect |
| `trapezoid` | 漏斗节点                   | `topWidth` |
| `cylinder`| 数据 / 存储节点              | 固定宽度（不用 `fill-container`） |
| `text`    | 纯文字标题 / 说明 / 侧注     | `fontSize`；`textColor` |
| `stickyNote` | 标注                      | `fillColor` ∈ 规定 9 色 |
| `connector` | 连线（顶层节点）           | `connector.from`/`to`（id 或 `{x,y}`）；`lineShape: 'straight'\|'rightAngle'\|'curve'`；`startArrow`/`endArrow`；`waypoints`；`label` |

`WBSizeValue` 可为数值、字符串 `"fit-content"`、或 `"fill-container"`。`cylinder` 不能用 `fill-container`。

## 最小可运行示例

```json
{
  "version": 2,
  "nodes": [
    {
      "type": "frame",
      "id": "root",
      "layout": "vertical",
      "gap": 24,
      "padding": 24,
      "width": "fit-content",
      "height": "fit-content",
      "children": [
        { "type": "rect", "id": "n1", "width": 200, "height": 56, "borderRadius": 8,
          "text": "校验请求", "fillColor": "#ffffff", "borderColor": "#5b8ff9",
          "textColor": "#1f2329", "fontSize": 14 },
        { "type": "rect", "id": "n2", "width": 200, "height": 56, "borderRadius": 8,
          "text": "处理业务", "fillColor": "#ffffff", "borderColor": "#5b8ff9",
          "textColor": "#1f2329", "fontSize": 14 }
      ]
    },
    {
      "type": "connector",
      "connector": {
        "from": "n1", "to": "n2",
        "fromAnchor": "bottom", "toAnchor": "top",
        "lineShape": "straight", "lineColor": "#98a2b3", "lineWidth": 1,
        "endArrow": "arrow"
      }
    }
  ]
}
```

## 路由选择

| chart_type | 优先路径 | 说明 |
|---|---|---|
| `sequence` | `mermaid(sequenceDiagram)` | 必须呈现标准参与者、生命线、消息箭头；禁止退化成"顶部卡片 + 文字列表" |
| `state-machine` | `mermaid(stateDiagram-v2)` | 必须呈现标准起止状态、状态节点、自环/回退关系；禁止手工拼线导致连线融成一团 |
| `flowchart` | `mermaid(flowchart)` 或 `dsl` | 标准审批流、判断流优先 Mermaid；只有多段复合卡片、复杂嵌套分组时才走 DSL |
| `mindmap` | `mermaid(mindmap)` | 标准脑图优先 Mermaid，避免用 DSL 画成树状流程 |
| `er-diagram` | `mermaid(erDiagram)` | 标准 ER 图优先 Mermaid；关系基数与字段必须可读 |
| `funnel` | `dsl` | 飞书代码图暂无高质量漏斗语法；必须保留多层颜色梯度与递减宽度 |
| `system-architecture` | `svg-openapi` / `dsl` | 强视觉验收、汇报图、用户要求贴近 preview 时优先 SVG；普通低复杂度可 DSL |
| `matrix-quadrant` | `svg-openapi` / `dsl` | 强视觉验收时必须保留 2×2 坐标矩阵与轴标签，优先 SVG |
| `sketch-architecture` | `svg-openapi` / `dsl` | 需要草图笔触、虚线分区、双线卡片时优先 SVG |
| `freeform-drawing` | `svg-openapi` | 产品原型、游戏页面、插画、自定义图表、桑基/路线图等固定表覆盖不到的视觉表达 |
| 其他图型 | `dsl` | 按本文件后续规则执行 |

## 代码原生图契约

### `sequence`

- 必须使用 `sequenceDiagram`
- 参与者数建议 `<= 8`
- 消息数建议 `<= 12`
- 允许同步箭头 `->>`、响应虚线 `-->>`、失败箭头 `-x`
- Gate B blocker：
  - 缺失生命线
  - 返回消息与请求消息不可区分
  - 把时序图画成普通流程卡片或文案清单

### `state-machine`

- 必须使用 `stateDiagram-v2`
- 必须显式出现起始状态 `[ * ]` 与终止状态 `[ * ]`
- 失败 / 重试 / 取消等回退边必须直接表达在代码里，禁止靠装饰性说明补语义
- Gate B blocker：
  - 起止状态缺失
  - 回退边与主路径互相遮挡到不可读
  - 把状态机画成流程节点串

### `flowchart`

- 标准判断流使用 `flowchart TD` 或 `flowchart LR`
- 不允许再套一层装饰性外矩形框
- 判断节点使用 `{}`，起止节点使用 `([开始]) / ([结束])`
- 节点文本保持简洁，避免一张图堆满大段说明
- Gate B blocker：
  - 外框抢视觉主次
  - 分支标签与主线挤在一起
  - 画面过窄导致所有线集中在一列

代码原生路径的静态验证与回读要求见 `06-quality-gates.md`。

### `mindmap`

- 必须使用 `mindmap`
- 分支层级建议 `<= 4`，每层节点数建议 `<= 8`
- 文本节点避免超长句，必要时拆分为子节点
- Gate B blocker：
  - 根节点不明确或层级错乱
  - 线条/分支密度过高导致阅读失败
  - 被画成"树形流程图"而不是脑图

### `er-diagram`

- 必须使用 `erDiagram`
- 实体必须有主键字段（用 `PK` 标注）
- 必须显式表达至少 1 条关系，并带基数（如 `||--o{`）
- Gate B blocker：
  - 关系基数缺失或表达错误
  - 字段列表不可读（过长、挤压、裁切）
  - 只有表清单没有关系

## 两种布局路径（仅 DSL）

| 场景 | 推荐 layout | 备注 |
|---|---|---|
| 分层架构 / 业务架构 / 对比 / 矩阵 | `vertical` / `horizontal` | Flex 心智，gap/padding 必须显式 |
| 链路 / 有向拓扑 / 复杂流程图 | `dagre` | `layoutOptions.edges` 提供邻接表，引擎自动排连线 |
| 跨子图连线（如泳道穿越） | 父级 `dagre` + 子 `frame` 声明 `isCluster: true` | 子图内部节点参与外层拓扑 |

## 强制规则

1. **所有颜色 / 字号都来自 `plan.style_budget`**，不得临时引入。
2. **`connector` 放顶层**，不能写进 `frame.children`。
3. **frame 必须显式写 `gap` / `padding`**，默认值容易把节点粘在一起。
4. **等高同排节点需显式 `alignItems: 'stretch'`**（DSL 默认是 `start`）。
5. **需要被 connector 引用的 frame**，必须有可见外观（`fillColor` / `borderColor` / `borderWidth`），否则编译期可能被当成"虚拟容器"优化掉，connector 会悬空。
6. **所有 id 全文档唯一**（connector 引用会失效）。
7. **`style_budget.connector_shape` → DSL `connector.lineShape` 必须一一映射**，禁止 Render 阶段擅自改风格。映射表见下表，违反者视同 Gate A 失败。
8. **`style_budget.connector_arrow_end` → DSL `connector.endArrow` 必须一一映射**。系统架构 / 链路架构类图型，参考样式 95% 无箭头（数据流表达），Plan 定 `none` 时 Render 不得补箭头。
9. **连线密度下限**：`connector` 数量 < `max(⌈节点数/8⌉, 每层至少 1 条穿层连线)` 时视为信息密度不足，Gate B 直接打回。

### style_budget → DSL connector 字段映射

| `style_budget.connector_shape` | DSL `lineShape` | 典型图型 |
|---|---|---|
| `right_angled_polyline`        | `rightAngle`    | system-architecture / org-chart / state-machine / lark-style-architecture |
| `straight`                     | `straight`      | flowchart / swimlane / sequence / link-architecture / business-architecture / 多数线性流程 |
| `curve`                        | `curve`         | 仅当对应 style-token 明确给出 `curve` 时使用 |

| `style_budget.connector_arrow_end` | DSL `endArrow` |
|---|---|
| `none`        | `"none"`       |
| `line_arrow`  | `"arrow"`      |
| `solid_arrow` | `"triangle"`   |

### 图型风格契约（Render 必读）

Render 组装前必须对照下表检查 `plan.chart_type`。对代码原生图，这里记录的是**路由契约**；对 DSL 图，记录的是 DSL 字段契约。任一字段偏离视同违规。

| chart_type | 路由 / DSL connector | DSL arrow | layer_fill / layer_border | 文本色主调 | 实测会话 |
|---|---|---|---|---|---|
| business-architecture | `straight` | `arrow` | `#ffffff` / `#dadde3` | `#1f2329` | `data/design-lark-chart/verify_business-architecture/` |
| system-architecture | `rightAngle` | `none` | `#fbfcfd` / `#dadde3` | `#1f2329` | `data/design-lark-chart/veai_demo/` |
| flowchart | `mermaid(flowchart)` 优先；复杂场景回 `straight` | `arrow` | `#ffffff` / `#98a2b3` | `#1f2329` | `data/design-lark-chart/reverify_20260428/` |
| swimlane | `straight` | `arrow` | `#f8fafc` / `#a9b0ba` | `#1f2329` | `data/design-lark-chart/verify_swimlane/` |
| sequence | `mermaid(sequenceDiagram)` | `n/a` | `n/a` | `#1f2329` | `data/design-lark-chart/reverify_20260428/` |
| org-chart | `rightAngle` | `arrow` | `#ffffff` / `#5b8ff9` | `#1f2329` | `data/design-lark-chart/verify_org-chart/` |
| state-machine | `mermaid(stateDiagram-v2)` | `n/a` | `n/a` | `#1f2329` | `data/design-lark-chart/reverify_20260428/` |
| funnel | `straight` | `arrow` | 多色渐进填充 / `#dadde3` | `#1f2329` | `data/design-lark-chart/reverify_20260428/` |
| gantt | `straight` | `none` | `#e9ebef` / `#d9dee8` | `#1f2329` | `data/design-lark-chart/verify_gantt/` |
| milestone | `straight` | `none` | `#57d7d0` / `#ffffff` | `#1f2329` | `data/design-lark-chart/verify_milestone/` |
| matrix-quadrant | `straight` | `none` | `#eaf7ee` / `#98a2b3` | `#1f2329` | `data/design-lark-chart/verify_matrix-quadrant/` |
| link-architecture | `straight` | `arrow` | `#eef3ff` / `#5b7fcb` | `#1f2329` | `data/design-lark-chart/verify_link-architecture/` |
| lark-style-architecture | `rightAngle` | `arrow` | 多色模块浅填充 / `#dadde3` + 模块语义描边 | `#1f2329` | `data/design-lark-chart/verify_lark-style-architecture/` |
| sketch-architecture | `straight` | `none` | `#fbfcfd` / `#5b7fcb` | `#1f2329` | `data/design-lark-chart/verify_sketch-architecture/` |
| complex-swimlane | `straight` | `arrow` | `#4b74d8` / `#5b7fcb` | `#1f2329` | `data/design-lark-chart/verify_complex-swimlane/` |

补充经验：

- 中间容器 `frame` 如果只是做布局分组，不要再叠加可见背景和边框；在 openapi 转换后，这类"父容器描边包住子节点"很容易触发 `node-overlap` warning。
- 对 `swimlane`、`complex-swimlane`、`link-architecture` 这类以阶段移交为核心的信息图，优先采用列式推进或显式阶段箭头；不要用长对角 connector 去硬连跨 lane / 跨层关系，否则飞书端很容易出现可读性崩坏。
- `funnel` 必须有至少 3 层可辨识的阶段色；只有边框变色、填充全白，视同未达成漏斗表达。
- `flowchart` 若已走 Mermaid，就不要再为了"统一样式"回退成 DSL 外框套娃；标准图法优先级高于人造卡片风格。
- 如果未来重新抽取 style-tokens，必须以新 token 重新结算本表，不要沿用旧推断。

### 高保真 SVG Render 形态

当 Route 选择 `svg-openapi`，Render 必须按图型读取契约：

- `system-architecture` / `matrix-quadrant` / `sketch-architecture`：读 `07-premium-style-contracts.md`
- `freeform-drawing`：读 `08-freeform-svg-mode.md`

这条路径允许精确表达弱网格、图例、坐标轴、虚线分区、手绘双线、产品 UI、流量带宽和插画层次等 DSL 难以稳定表达的视觉细节，但仍有三个边界：

- **颜色 / 字号仍受 style_budget 约束**：SVG 中的 `fill` / `stroke` / `color` 必须能回查到目标图型 token 或 `_catalog.json.house_style`。
- **布局由当次模型动态设计**：可以使用 `viewBox`、`x/y`、`width/height`，但这些数值必须来自当次 plan 的节点数、分组数、轨道宽度、间距和画布比例；不要为某个业务样例硬塞坐标，也不要新增生成脚本或复用固定 SVG 模板。
- **写入前必须转 OpenAPI**：`whiteboard-cli -i diagram.svg -f svg --check` 通过后，再执行 `whiteboard-cli -i diagram.svg -f svg --to openapi --format json > board.openapi.json`。

专项命令：

```bash
whiteboard-cli -i <session>/diagram.svg -f svg --check > <session>/svg_check.json
whiteboard-cli -i <session>/diagram.svg -f svg -o <session>/preview.png
whiteboard-cli -i <session>/diagram.svg -f svg --to openapi --format json > <session>/board.openapi.json
skills/design-lark-chart/scripts/lint_premium_style.py <chart_type> <session>/diagram.svg \
  > <session>/lint_premium.json
skills/design-lark-chart/scripts/lint_svg_quality.py <session>/diagram.svg \
  --mode <sankey|roadmap|prototype|illustration|custom> \
  --tokens skills/design-lark-chart/assets/style-tokens/_catalog.json \
  > <session>/lint_svg_quality.json
```

### lark-style-architecture Render 形态

该图型必须对齐 `assets/previews/lark-style-architecture.png` 的视觉锚，而不是退化成分层框图：

- 顶部：一个深色胶囊标签 + 一个浅紫核心逻辑横幅；横幅内有大标题和 2-4 个白色核心策略卡。
- 主体：4-6 个纵向模块容器，容器使用浅蓝/浅紫/浅黄/浅红/浅绿等 token 内浅填充，描边使用对应语义色。
- 细节：模块内使用白色卡片、短胶囊或 bullet cluster 表达二级能力；只有模块标题没有细节，视同信息密度不足。
- 连线：核心横幅到模块、模块之间都使用 `rightAngle + arrow`；跨模块线应避开卡片正文，不允许用一条长横线串完整层。
- 禁止：三层横向 lane、全白盒子、只有外框换色、无模块内卡片、把预览图业务文案当模板抄写。

DSL 输出后必须额外执行：

```bash
skills/design-lark-chart/scripts/lint_lark_style_architecture.py <session>/board.json
```

## 本地验证流程

```bash
# 1. 几何门禁（Gate A）
skills/design-lark-chart/scripts/check_board.sh <session>/board.json

# 2. 渲染 PNG（给 VQA Gate B 用）
skills/design-lark-chart/scripts/render_preview.sh \
  <session>/board.json <session>/preview.png

# 3. 需要导成 OpenAPI 原始结构再上传时：
whiteboard-cli -i <session>/board.json -t openapi -o <session>/board.openapi.json
```

## 上传到飞书

DSL 形态的 `board.json` 可由 `lark-cli whiteboard +update` / `lark-cli docs +whiteboard-update` 接受（底层也是 whiteboard-cli 管道）。具体参数以 `lark-cli` 最新帮助输出为准。**在 06 的质量门未通过前，禁止写入飞书。**
