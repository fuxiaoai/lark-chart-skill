# Coverage Report

本文件用于定义 `design-lark-chart` 的“覆盖面口径”和“发布判定口径”，避免把本地验收产物（`data/`）提交进仓库。

## Table of Contents

- 覆盖面口径
- 发布判定口径
- 当前覆盖图型
- 验收证据位置

## 覆盖面口径

本 skill 的“覆盖”指：该图型已经形成了明确的路由（Mermaid/PlantUML/DSL/SVG-OpenAPI 之一），并且存在可复用的最小样例输入用来走通端到端流程（不等于每次都能一次生成即过 Gate B）。

## 发布判定口径

对外承诺“支持”的图型，必须满足：

1. Gate A（按路由静态门禁）可通过
2. Gate B（基于真实飞书导出图的双 reviewer 视觉评审）可通过

任一门禁未通过，视为“不可发布”，不得对外承诺。

## 当前覆盖图型

以下固定图型在 `SKILL.md` 中已列出，并在 `references/02-chart-taxonomy.md` 中有路由与选择规则：

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

另外新增：

- `freeform-drawing`：非模板化 SVG 自由绘画模式，覆盖固定图型外的产品原型、游戏页面、插画、自定义信息图、桑基图、路线图等需求。发布判定仍以 Gate A/B 为准，不因本地 SVG 能渲染就自动算可发布。

## 验收证据位置

- 可复用样例：`references/examples/`
- 每次运行的会话产物：`data/design-lark-chart/<session>/`（本地生成，不入 git）
- 门禁规则：
  - Gate A/B：`references/06-quality-gates.md`
  - DSL Render：`references/05-render-dsl.md`
  - Premium 风格契约：`references/07-premium-style-contracts.md`
  - Freeform SVG 契约：`references/08-freeform-svg-mode.md`
