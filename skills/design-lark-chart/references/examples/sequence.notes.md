# sequence example

- scenario: 用户扫码登录时序
- style_tokens: `assets/style-tokens/sequence.json`
- render_route: `mermaid(sequenceDiagram)`
- example_source: `examples/sequence.mmd`
- verify_session: `data/design-lark-chart/reverify_20260428/`
- feishu_doc: https://www.feishu.cn/docx/QNdUdUPREorNNNxXa09cq7Nanmc
- style_budget:
  - title_color: `#1f2329`
  - participant_border: `#6c8dda`
  - message_color: `#1f2329`
  - request_arrow: `->>`
  - response_arrow: `-->>`

- verification_note:
  - 2026-04-28 已改为 Mermaid 原生时序图，不再使用 DSL 拼装的"参与者卡片 + 文本列表"降级方案。
  - 已完成 `+update --input_format mermaid`、`+query --output_as code` round-trip 和真实飞书导图回收。
