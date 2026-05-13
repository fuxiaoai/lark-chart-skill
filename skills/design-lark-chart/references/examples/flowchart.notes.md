# flowchart example

- scenario: 订单退款审批流程
- style_tokens: `assets/style-tokens/flowchart.json`
- render_route: `mermaid(flowchart)`
- example_source: `examples/flowchart.mmd`
- verify_session: `data/design-lark-chart/reverify_20260428/`
- feishu_doc: https://www.feishu.cn/docx/ET9Td10tvo5l8AxG8G3co7OTnqe
- style_budget:
  - title_color: `#1f2329`
  - primary_border: `#98a2b3`
  - decision_border: `#c8a33e`
  - danger_border: `#e86868`
  - connector_arrow_end: `arrow`

- verification_note:
  - 2026-04-28 已改为 Mermaid 标准流程图，去掉无意义外框，主流程与异常分支在飞书端可读性显著提升。
  - 已完成 `+update --input_format mermaid`、`+query --output_as code` round-trip 和真实飞书导图回收。
