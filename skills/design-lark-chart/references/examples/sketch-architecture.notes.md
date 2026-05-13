# sketch-architecture example

- scenario: 数据湖手绘风架构
- style_tokens: `assets/style-tokens/sketch-architecture.json`
- verify_session: `data/design-lark-chart/verify_sketch-architecture/`
- feishu_doc: https://www.feishu.cn/docx/G0C8dnTGIoAuJkxGcdAcv2A5nbg
- style_budget:
  - connector_shape: `straight`
  - connector_arrow_end: `none`
  - connector_color: `#5b7fcb`
  - primary_border: `#5b7fcb`
  - label_color: `#1f2329`
  - layer_fill: `#fbfcfd`
  - layer_border: `#5b7fcb`

- verification_note:
  - 已完成 Gate A、飞书写入与真实导出图回收，Gate B 可执行。
  - 该 JSON 样例只代表 DSL 兜底路径；强视觉验收必须按 `references/07-premium-style-contracts.md` 保留虚线阶段分区、双线/下划线笔触和关键跨阶段连线，并执行 `lint_premium_style.py sketch-architecture`。
