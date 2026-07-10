# O6/O7 Offline Artifact Seed Smoke PRD

## Sprint 类型

sprint_type: epic

## 用户价值与产品北极星

产品北极星不变：普通用户把垃圾交给小车后，小车可验证地完成投递。

本 sprint 的直接用户价值不是“更强控制”，而是“更可信的数据入口”。把已有离线路线材料接成可复用的 offline artifact seed smoke，可以让 O6/O7 在没有真实现场、没有生产云、没有真实机器人动作的情况下，先把数据链路、回放链路和阅读链路打通，减少后续现场验收时的手工拼接成本。

## OKR 映射

当前最低 active Objective 为 O6 与 O7 并列，均约 42%。本 sprint 直接针对 O6/O7 的软件侧证据链，目标是把离线路线材料接入同一 `task_id` 的读写/消费路径，而不是转去更高进度的 Objective。

本 sprint 不归档任何 KR，不把离线 seed smoke 误报为真实生产云、真实媒体、真实 annotation API、真实 dataset export 或真实机器人运动完成。

## 产品需求

1. O6 必须支持从既有离线路线材料构造可读的 seed smoke 输入，至少能追踪到 `route.csv`、`manifest.json` 和 `derived_replay.jsonl` 的关联关系。
2. O6 的输出必须是摘要和状态，不得泄露绝对路径、token、原始大对象、base64 媒体或串口/控制细节。
3. O7 必须消费 O6 同一 `task_id` 的结果，并展示 ready / blocked / next evidence 的运营可读信息。
4. 缺文件、坏格式、schema 不匹配、ref 不在 allowlist、或任何危险 true 诉求，都必须 fail-closed。
5. 所有页面、接口和文档必须继续显式保留安全边界，不得把 seed smoke 解释成真实投递或真实控制成功。

## 验收口径

- 计划文档中明确给出离线材料来源、owner 分工、接口边界、验收命令和安全旗标。
- 后续实现阶段可以基于这些计划，把同一离线 seed 串到 O6/O7 的软件链路。
- 任一高风险输入都应返回明确 blocked reason，而不是静默成功。

## 责任工程师

- `robot-software-engineer`
- `robot-algorithm-engineer`
- `full-stack-software-engineer`
- `product-okr-owner`

## 需要创建或更新的文档

本轮只创建并完善以下 sprint 启动文档：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续实现、验证、收口时再按 Epic 流程补齐 `tech-done.md`、`side2side_check.md` 和 `final.md`。
