# state-machine example

- scenario: 订单状态机：待支付到完成/退款
- style_tokens: `assets/style-tokens/state-machine.json`
- render_route: `mermaid(stateDiagram-v2)`
- example_source: `examples/state-machine.mmd`
- verify_session: `data/design-lark-chart/reverify_20260428/`
- feishu_doc: https://www.feishu.cn/docx/IyhBdYOBXoHUpWxGaeacltkwnfg
- style_budget:
  - title_color: `#1f2329`
  - neutral_border: `#6b7280`
  - success_border: `#4e9d6d`
  - danger_border: `#c94c4c`
  - start_end_fill: `#111827`

- verification_note:
  - 2026-04-28 已改为 Mermaid 原生状态机图，解决 DSL 手工连线易融合、回退边难读的问题。
  - 已完成 `+update --input_format mermaid`、`+query --output_as code` round-trip 和真实飞书导图回收。
