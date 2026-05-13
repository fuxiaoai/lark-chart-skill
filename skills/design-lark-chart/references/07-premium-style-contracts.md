# 07 · Premium Style Contracts

本文件只约束三类用户已明确指出“和示例图差距大”的图型：

- `system-architecture`
- `matrix-quadrant`
- `sketch-architecture`

触发条件：用户要求“更高级”“贴近示例图”“飞书画板风格”“不要太简单”，或 Gate B 指出画面退化成普通盒子图。

## Table of Contents

- 总原则
- system-architecture
- matrix-quadrant
- sketch-architecture
- 专项 lint

## 总原则

1. **优先 SVG 高保真路径**：三类图在强视觉验收时走 `diagram.svg -> whiteboard-cli -f svg --to openapi -> lark-cli whiteboard +update`。DSL 只能作为 SVG 两轮失败后的兜底，并必须记录降级原因。
2. **只借风格，不借业务**：可以复用 preview 的画布比例、层级密度、弱网格、标签、图例、分区方式、线条气质；不得复用 raw 坐标或示例业务文案。
3. **用 tokens 上色**：颜色/字号必须来自目标图型 `style-tokens/<id>.json` 或 `_catalog.json.house_style`。缺色时从同一 token 的完整 palette 往后取，不在 SVG 临时发明新色。
4. **留白是风格的一部分**：高级感来自大画布、清晰主次和弱边框，不来自堆装饰。宁可减少节点，也不要把所有文字塞满画面。
5. **禁止绘图脚本化**：不要为这三类图新增 `diagram.gen.*`、固定 SVG 模板、固定坐标表或按图型写死的渲染器。每次都由模型根据 `normalized.json + plan.json + style_profile` 当次动态设计；脚本只允许做 lint / check / render / upload，不允许负责画图。

## system-architecture

视觉锚：`assets/previews/system-architecture.png`

必须具备：

- 大画布弱点阵背景；背景只做低对比纹理，不抢文字。
- 顶部大标题，右上角可有图例；图例只有在输入有优先级/阶段语义时出现。
- 主区在左，侧栏在右；侧栏承载外部依赖、观测、Runtime、模型、三方系统等非主链路组件。
- 主区至少 3 个水平架构层，每层有浅色容器、左上小号层标签、内部白色服务卡。
- 底座层可用虚线框表达基础设施、中间件、模型或数据底座。
- 连线以正交折线为主，线条少而关键；避免穿过服务卡正文。

禁止：

- 只有三排横向框，没有侧栏/底座/图例。
- 所有节点都是白底蓝边，没有语义浅填充。
- 把外部依赖混进主链路，导致架构边界不清。
- 为了显得复杂而补造用户没给的系统。

Gate B 下限：

- 主区层数 `< 3` 失败。
- 侧栏缺失且输入存在外部依赖语义失败。
- 节点全是同一种卡片样式失败。

## matrix-quadrant

视觉锚：`assets/previews/matrix-quadrant.png`

必须具备：

- 一个清晰的 2×2 坐标矩阵；四个象限共享同一外边界和中心分割线。
- 横轴、纵轴标签必须出现；轴名来自输入，缺省时可标注为 `assumed-axis`。
- 四个象限使用低饱和浅色块，边框色与填充色成对来自 tokens。
- 象限标题醒目，内容以 bullet list 为主，保留空白；不要每条都画成大卡片。
- 象限位置必须符合轴含义：高价值/低复杂在右下或用户指定位置，不可随机排列。

禁止：

- 四个竖向卡片横排。
- 没有轴标签，只剩四个分类框。
- 象限内部堆满独立卡片，坐标关系弱化。

Gate B 下限：

- 不是 2×2 或用户指定的矩阵结构失败。
- 缺任一轴标签失败。
- 四象限背景无法区分失败。

## sketch-architecture

视觉锚：`assets/previews/sketch-architecture.png`

必须具备：

- 低保真草图语义：标题可直说“草图 / 方案讨论 / 低保真”。
- 2-4 个虚线阶段分区，阶段标签采用 `01 / xxx` 的序号感。
- 卡片以方形或轻圆角为主，边框有双线、偏移线、下划线或轻微手绘笔触。
- 每个阶段 2-4 个短卡片；不同阶段使用不同描边色。
- 少量关键跨阶段连线即可；连线可直线或轻微斜线，但不能压住正文。

禁止：

- 普通圆角卡片 + 普通实线分层，完全没有草图笔触。
- 阶段分区缺失，只是节点散排。
- 连线过多，变成难读的流程图。

Gate B 下限：

- 虚线阶段区 `< 2` 失败。
- 缺双线/下划线/偏移笔触失败。
- 跨阶段关键关系缺失失败。

## 专项 lint

三类图渲染后必须运行：

```bash
skills/design-lark-chart/scripts/lint_premium_style.py <chart_type> <session>/diagram.svg \
  > <session>/lint_premium.json
```

`ok=false` 时不得上传。lint 只覆盖可机器检查的结构下限；即使 lint 通过，仍必须基于真实飞书导出图做 Gate B 视觉复核。
