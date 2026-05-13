# lark-style-architecture example

- scenario: 飞书高级风格评测架构
- style_tokens: `assets/style-tokens/lark-style-architecture.json`
- verify_session: `data/design-lark-chart/verify_lark-style-architecture/`
- feishu_doc: https://www.feishu.cn/docx/VM0md8nFXousGMxFv3BchtAPnHg
- style_budget:
  - connector_shape: `rightAngle`
  - connector_arrow_end: `arrow`
  - connector_color: `#dadde3`
  - primary_border: `#dadde3`
  - label_color: `#1f2329`
  - card_fill: `#ffffff`
  - muted_text_color: `#4e5969`
  - module_fills: `#eef3ff`, `#f3eeff`, `#eaf7ee`, `#fff8e6`, `#fdebec`
  - module_borders: `#2f69a5`, `#6e56b5`, `#2e7d4f`, `#b57918`, `#b7444a`
  - highlight_fill: `#2e7d4f`, `#b7444a`

- verification_note:
  - 本样例用于约束 lark-style-architecture 的高级视觉形态：顶部核心逻辑横幅、彩色模块列、模块内二级卡片/要点、右角跨模块连接。
  - 本地已通过 `lint_lark_style_architecture.py`、`check_board.sh` 和 `render_preview.sh`；飞书写入与真实导出图回收需在目标白板会话内执行。
