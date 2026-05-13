# matrix-quadrant example

- scenario: 产品功能 价值 x 成本 四象限
- style_tokens: `assets/style-tokens/matrix-quadrant.json`
- verify_session: `data/design-lark-chart/verify_matrix-quadrant/`
- feishu_doc: https://www.feishu.cn/docx/G0C8dnTGIoAuJkxGcdAcv2A5nbg
- style_budget:
  - connector_shape: `straight`
  - connector_arrow_end: `none`
  - connector_color: `#98a2b3`
  - primary_border: `#98a2b3`
  - label_color: `#1f2329`
  - layer_fill: `#eaf7ee`
  - layer_border: `#98a2b3`

- verification_note:
  - 已完成 Gate A、飞书写入与真实导出图回收，Gate B 可执行。
  - 该 JSON 样例只代表 DSL 兜底路径；强视觉验收必须按 `references/07-premium-style-contracts.md` 生成 2×2 坐标矩阵，禁止退化成横向四列卡片，并执行 `lint_premium_style.py matrix-quadrant`。
