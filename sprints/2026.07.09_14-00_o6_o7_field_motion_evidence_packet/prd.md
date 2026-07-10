# O6/O7 Field Motion Evidence Packet PRD

## 用户价值和产品北极星

用户真正需要的不是更多 local/mock surface，而是能把已经采到的现场运动材料复用成可回放、可标注、可复盘的一条证据链。只有这样，O6 才能把同一 `task_id` 的现场材料归档成长期数据资产，O7 才能把历史路线回放、标注和运营排障推进到接近真实工作流。

本轮仍不追求真实控制或送达闭环。产品北极星保持为“普通手机用户可验证地把垃圾交给机器人完成投递”，而 field motion evidence packet 只是把这条北极星需要的现场运动证据整理成下一轮工程可直接消费的输入。

## OKR 映射和方向判断

- 目标 Objective：O6、O7。
- 当前最低 active Objective：O6 与 O7，均约 47%。
- 方向判断：继续推进 O6/O7，但必须从“继续堆本地 wrapper”调整为“消费已有 6 月现场运动材料”。
- 不调整 O1/O2/O3/O4/O5：本轮不涉及真实底盘闭环、真实公网云、真实电梯或手机验收。

## 问题定义

已有事实：

1. 6 月现场 capture 已经留下 `map.yaml/.pgm`、`route.csv`、`manifest.json`、keyframes 和 remote_capture motion 日志。
2. O6 已经具备 local/mock archive ingest、field evidence ingest、artifact bundle ingest、artifact access probe、offline seed smoke、route-root seed gate 等软件侧主路径。
3. O7 已经具备 route replay、labeling、artifact readiness、probe readiness 的 consumer detail 主路径。

当前缺口：

1. 这些现场材料还没有被统一整理成同一 `task_id` 的 field motion evidence packet。
2. O6/O7 还没有一条明确计划，要求后续实现直接消费这批材料，而不是继续增加新的 wrapper 层。
3. `route_bag` 与 live Nav2 运动日志仍是增强证据，但当前需要在计划里把它们定义为 `route_bag_or_live_nav2_log`，避免重新变成硬 gate。

## 本轮核心抓手

定义一条可执行 sprint：

- 由 `robot-algorithm-engineer` 把 6 月现场材料归一成 packet 语义。
- 由 `robot-software-engineer` 把 packet 接到 O6 archive ingest / consumer detail。
- 由 `full-stack-software-engineer` 把 packet 摘要接到 O7 replay / labeling workspace。
- 所有控制字段保持 false，所有结论保持 not proven，直到真实路线执行与送达闭环另行补证。

## 需求范围

### In scope

- 同一 `task_id` 的 field motion evidence packet 计划。
- `map.yaml`、`route.csv`、keyframes、manifest、remote_capture motion 日志、derived replay 的最小证据集合。
- `route_bag_or_live_nav2_log` 作为可选增强证据的边界定义。
- O6 ingest / readback 与 O7 consumer replay 的 owner、文件范围和验收命令。
- false safety flags 和 fail-closed 原则。

### Out of scope

- 新增 local/mock wrapper、review surface 或纯 handoff 产物。
- 真实生产云、TLS/4G、OSS/CDN、真实 annotation API、真实 dataset export。
- 真实底盘控制、真实送达成功、真实电梯闭环、真实 wheel raw 非零证明。

## 验收口径

本轮验收是计划文档验收，不是代码能力验收。计划必须满足：

1. 明确写出 `sprint_type: epic`。
2. 明确写出 O6/O7 最低优先级判断。
3. 明确禁止继续新增 wrapper，要求消费已有 6 月现场材料。
4. 明确 `route_bag_or_live_nav2_log` 是可选增强证据，而不是本轮硬 gate。
5. 明确列出 `robot-algorithm-engineer`、`robot-software-engineer`、`full-stack-software-engineer` 的 owner 分工。
6. 明确列出允许改动范围、验收命令和 false safety flags。

## 风险与阻塞

- 6 月现场材料可能存在命名不统一、时间线不连续或缺少同一 `task_id` 的问题。
- `route_bag` 若缺失，后续实现必须保证 packet 仍能以离线 replay + manifest + route/keyframes 收口。
- 若 remote_capture motion 日志无法稳定映射到 O6/O7 现有 contract，后续实现需要先补 additive contract，而不是退回再造 wrapper。

## 需要创建或更新的 sprint 文档

- `sprints/2026.07.09_14-00_o6_o7_field_motion_evidence_packet/pre_start.md`
- `sprints/2026.07.09_14-00_o6_o7_field_motion_evidence_packet/prd.md`
- `sprints/2026.07.09_14-00_o6_o7_field_motion_evidence_packet/tech-plan.md`
