# O6 Artifact Access Probe Pre Start

## Sprint 声明

- sprint_type: epic
- round: 2026.07.09_10-58_o6_artifact_access_probe
- start_time: 2026-07-09 10:58 CST
- product_owner: product-okr-owner
- target_objective: O6 云端核心后端
- secondary_objective: O7 PC 端运营调试与数据训练平台 consumer readiness only
- primary_owner: robot-software-engineer
- secondary_owner: full-stack-software-engineer
- evidence_boundary: planned_local_mock_artifact_access_probe_only
- safe_to_control: false
- delivery_success: false
- primary_actions_enabled: false
- robot_control_executed: false

## 上轮事实和触发原因

最近两轮相关 epic sprint 已通过软件侧验收，但都明确留下同一产品判断：不能继续只堆 local/mock wrapper、summary 或 readiness surface。

- `sprints/2026.07.09_08-56_o6_artifact_bundle_ingest/final.md` 证明 O6 已能接收 `trashbot.o6.artifact_bundle.v1` 摘要，并回读 `artifact_bundle` / `artifact_bundle_consumer_ingest`，但不证明真实 `route.csv`、replay JSONL、keyframe、rosbag 或 evidence 文件存在、可读、可播放或可下载。
- `sprints/2026.07.09_09-57_o7_artifact_bundle_consumer_readiness/final.md` 证明 O7 已能展示 `artifact_bundle_readiness`，但下一步必须让真实或离线 artifact 进入 O6 archive，并由 O7 主路径消费，而不是继续只展示字符串引用。

当前 `OKR.md` 4.1 节显示 O6 约 39%，是 active Objective 中最低进度；O7 约 40%，紧随其后。本轮必须优先推动 O6 的真实/离线 artifact 可访问性证据链。

## 本轮目标

本轮目标是让 O6 archive/read model 在安全、受限、本地/mock 条件下支持 artifact access probe 摘要：对 artifact bundle 或 field evidence 中的本地 refs 做可复现的存在性、大小、sha256 和类型摘要。

本轮只证明“ref 是否能在受限本地范围内被安全探测并形成可回读摘要”，不证明生产云、OSS/CDN、真实机器人运动、真实媒体播放或送达成功。

## 范围边界

必须 fail-closed：

- 不连接生产云、生产 DB/queue、OSS/CDN、TLS/4G 或公网隧道。
- 不读取 token URL、credential URL、绝对路径、父目录逃逸路径、串口设备、ROS topic 或机器人控制入口。
- 不保存原始媒体内容、raw/base64 payload、token、完整敏感路径或大文件内容。
- 不执行机器人控制、不启动 ROS2 runtime、不下发 `/cmd_vel` 或任何 motion command。

允许的软件侧能力：

- 在本地/mock file-backed archive 中，对受限 artifact root 下的本地相对 refs 做只读 probe。
- 对每个 ref 记录安全摘要：normalized ref、exists、size_bytes、sha256、detected_type、blocked_reason。
- 将 probe 结果挂到同一 `task_id` 的 O6 archive task detail / consumer detail。
- O7 仅作为 secondary consumer 读取 probe 结果并展示 readiness，不改变 O6 主线优先级。

## Owner 分工

- `robot-software-engineer`：主责 O6 artifact access probe 合同、archive/read model、fail-closed 校验、单元测试、接口文档和 `tech-done.md`。
- `full-stack-software-engineer`：在 O6 probe 字段稳定后，secondary 消费 probe 结果并展示 readiness；不得抢先扩展新 wrapper 或绕过 O6。
- `robot-algorithm-engineer`：仅在需要时补充 route.csv、replay JSONL、keyframe、rosbag 或离线 evidence seed 的字段事实；本轮不要求新建真实路线材料。
- `product-okr-owner`：维护本 sprint 计划、验收边界、OKR 方向判断和最终收口。

## 验收口径

- O6 至少能用本地/mock fixture 证明一个安全相对 ref 的 `exists/size_bytes/sha256/detected_type` 摘要可写入并回读。
- 至少覆盖一个 blocked ref：token URL、绝对路径、父目录逃逸、raw/base64 或缺失文件中的一种，并返回明确 `blocked_reason`。
- O7 如参与，只能展示 O6 probe 派生 readiness，不允许把 `local_mock/not_proven` 文案改成真实可用。
- 所有危险能力字段继续保持 false：`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。

## 风险和阻塞

- 如果当前仓库没有任何可安全读取的离线 artifact seed，工程实现必须用 repo 内测试 fixture 构造最小 `route.csv` 或 JSONL 样本，并明确 `fixture_only` 边界。
- 如果真实 artifact 路径存在但位于受限 root 外，必须 blocked，不得为推进进度放宽路径限制。
- 本轮完成后仍不等于真实生产云、真实 OSS/CDN、真实视频、真实 annotation API、真实 dataset export 或长期路线验收完成。
