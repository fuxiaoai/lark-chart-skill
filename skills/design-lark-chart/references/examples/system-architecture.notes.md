# system-architecture example

- scenario: EcomEval 自动化评测平台系统架构图
- style_tokens: `assets/style-tokens/system-architecture.json`
- verify_session: `data/design-lark-chart/verify_system-architecture/`
- feishu_doc: https://www.feishu.cn/docx/G0C8dnTGIoAuJkxGcdAcv2A5nbg
- style_budget:
  - connector_shape: `rightAngle`
  - connector_arrow_end: `none`
  - connector_color: `#dadde3`
  - primary_border: `#dadde3`
  - label_color: `#1f2329`
  - layer_fill: `#fbfcfd`
  - layer_border: `#dadde3`

- verification_note:
  - 已完成 Gate A、飞书写入与真实导出图回收，Gate B 可执行。
  - 该 JSON 样例只代表 DSL 兜底路径；当用户要求贴近 `assets/previews/system-architecture.png` 或更高级视觉时，必须按 `references/07-premium-style-contracts.md` 走 SVG 高保真路径，并执行 `lint_premium_style.py system-architecture`。
