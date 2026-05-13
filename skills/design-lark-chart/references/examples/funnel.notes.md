# funnel example

- scenario: B 端 SaaS 销售漏斗
- style_tokens: `assets/style-tokens/funnel.json`
- render_route: `dsl`
- example_source: `examples/funnel.json`
- verify_session: `data/design-lark-chart/reverify_20260428/`
- feishu_doc: https://www.feishu.cn/docx/OMHTdcktcoxwetxVPh8ccocvnXe
- style_budget:
  - connector_shape: `straight`
  - connector_arrow_end: `arrow`
  - connector_color: `#dadde3`
  - primary_fill: `#eef3ff`
  - accent_fill: `#f3eeff`
  - success_fill: `#eaf7ee`
  - warning_fill: `#fff4d9`
  - danger_fill: `#fdebec`
  - label_color: `#1f2329`
  - outer_frame: `none`

- verification_note:
  - 2026-04-28 已按参考图重做为彩色分层漏斗，去掉外部装饰框，强化阶段层次。
  - 已完成 `whiteboard-cli --check`、OpenAPI 写入和真实飞书导图回收。
