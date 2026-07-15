# O6/O7 真实传感器数据集回放 Epic - Pre Start

## Sprint 声明

- `sprint_type: epic`
- 状态：`planning_complete_waiting_engineer_dispatch`
- 创建时间：`2026-07-15 10:59 CST`
- 目标 Objective：O6、O7
- 暂停 Objective：O5 当前 `provider_runtime_preflight` lane
- 上位机入口：SSH `root@192.168.1.11 -p 37878`
- 本阶段边界：仅完成 `pre_start.md -> prd.md -> tech-plan.md`；不执行 SSH、实现、测试或 live capture。

## 用户价值与产品北极星

本轮服务的用户是需要判断机器人真实传感器链是否可用于回放、归档和后续标注的研发/运营人员。产品北极星不是再多一个状态页或 readback，而是：**从真实上位机已有 publisher 得到一份本轮新产生、可校验、可离线消费的机器人数据集，并证明 O6/O7 能沿同一 `task_id` 识别其 rosbag 与语义摘要。**

如果没有新的 current-run rosbag、replay JSONL、keyframe 或等价真实数据，本 sprint 不得以 manifest、合同、UI 或 readback 完成收口。

## OKR 映射与方向判断

| Objective | 当前进度 | 本轮判断 | 证据与理由 |
| --- | ---: | --- | --- |
| O5 云中转控制面 | 约 85% | **暂停当前 lane** | `2026.07.15_09-04` 的真实 provider preflight 与 `2026.07.15_10-00` 的离线 stage diagnostics 已连续两轮消费同一 `provider_runtime_preflight` blocker；禁止第三轮 wrapper/diagnostic/readback/live rerun。 |
| O6 数据存档、模型推理与打标平台 | 约 93% | **继续** | 主要缺口明确包含真实机器人数据与现场长期回灌；真实上位机可达，可在无运动条件下产生新数据。 |
| O7 PC 运营调试与数据训练平台 | 约 93% | **继续** | 主要缺口明确包含真实回放/标注数据流与长期上车验证；既有 rosbag independent sections / O6 artifact-bundle / O7 consumer 能力可消费本轮真实数据。 |

方向选择为“调整”：从最低 O5 暂时切换到并列次低 O6/O7。切换原因是 blocker 重复消费红线，不是降低 O5 优先级。只有出现已配置且获授权的公网 provider/runtime/credential 新事实时，O5 才可重新进入候选。

## 最近三轮事实与去重

1. `sprints/2026.07.15_08-06_o3_live_tf_receipt_capture/` 已产生 current-run true-board TF/scan artifact，但目标是定位 freshness 与 `map->odom` blocker；不得再运行同一无 initial pose 的 localization wrapper，也不得把其旧 artifact 当成本轮新数据。
2. `sprints/2026.07.15_09-04_o5_public_health_tunnel_external_evidence/` 的一次 live provider preflight 在 runtime staging/provenance gate 前失败。
3. `sprints/2026.07.15_10-00_o5_provider_runtime_preflight_stage_diagnostics/` 已补齐离线七阶段诊断合同，成为相同 blocker 的第二轮、最后一轮消费。

本轮不做第三轮 O5，也不做 O3 localization、`/initialpose`、TF freshness 或 another receipt wrapper。新产物必须来自本轮独立短时传感器订阅窗口。

## 本轮核心抓手

复用真实上位机**已存在**的 ROS2 publisher，在严格无运动、只订阅、不启停 runtime 的前提下：

1. 先做一次 read-only remote inventory，确认 ROS2/rosbag 工具、磁盘余量、无冲突 recorder、topic 类型和 publisher count。
2. 只有 gate 通过时，执行最多一次、最长 8 秒、`--max-bag-size 16777216` 的 allowlist topic rosbag capture；capture 后整个 rosbag 目录不得超过 16 MiB。
3. 拉回 rosbag 后只做离线 SQLite/语义解码，生成 `route_bag_evidence`、`route_bag_payload_replay`、`route_bag_semantic_replay`、`route_bag_full_semantic_decode_matrix` 和可选 `route_bag_pose_progress_replay` 独立 section；不使用 `ros2 bag play` 向任何 graph 发布。
4. bag-only `field_evidence_manifest` 总 gate 会因缺 map/route/keyframes fail closed，因此不把它作为 Phase C 写入载体。由 Full-stack 把独立 ready sections 组装进既有 `trashbot.o6.artifact_bundle.v1`，POST `/api/o6/archive/artifact-bundle`，再由 O6/O7 回读同一 `task_id` 的 DB3 SHA-256、topic/message/timestamp lineage。

## 范围

### 必须完成

- 新 current-run rosbag：至少包含 `/scan`，并可按 inventory 追加 `/odom`、`/tf`、`/tf_static`、`/diagnostics`；只接受 topic 当前已有 publisher 且类型在 allowlist 内。明确不录 `/map`、`/amcl_pose`。
- rosbag 自描述证据：`metadata.yaml`、DB3、topic/type/message counts、时间跨度、size 与 SHA-256。
- 离线安全语义消费：至少一个 `sensor_msgs/msg/LaserScan` 样本成功解码；若 `/odom` 或 `/tf` 存在则保留其安全摘要。
- O6 artifact-bundle 写入/回读与 O7 consumer 结果使用同一 `task_id`，并与 DB3 SHA-256、topic/message/timestamp counts 对齐；禁止新增 `dataset_id` wrapper。
- `tech-done.md` 记录实际改动、命令结果、live 调用次数、cleanup、失败定位和剩余风险。

### 明确禁止

- `/initialpose`
- `/cmd_vel`
- `/api/base/manual`
- NavigateToPose
- 录制 `/map`、`/amcl_pose`
- `ros2 bag play`
- WAVE ROVER UART、底盘运动、串口写入
- route execution、delivery、HIL、safe-to-control 声明
- `ros2 launch`、`ros2 lifecycle set`、启动/停止/重启现有 ROS runtime
- 为凑齐 topic 而启动 camera、LiDAR、AMCL、Nav2 或任何 publisher
- 失败后再次执行 `ros2 bag record`

## Owner 与协作

- 主责：`robot-algorithm-engineer`。负责只读 inventory、安全 capture helper、最多一次 live rosbag、离线 semantic ready sections、cleanup 及最终技术整合。
- 下游消费：`full-stack-software-engineer`。只在 Algorithm 交付 rosbag/independent sections 后，将其组装为既有 O6 artifact-bundle，再做 O6/O7 selected-task 回读；必要时只修真实数据分类/消费的最小合同缺口。
- 调度方式：接口强依赖，不做假并行。可在 Algorithm 实现期间并行安排 Full-stack **只读咨询**，确认既有 O6/O7 入参和断言；实际消费必须在 Algorithm 产物冻结后开始。
- Product：只做计划、验收、OKR 判断和 closeout，不执行 SSH、capture、实现或测试。
- Hardware：本轮不涉及 UART、电压、引脚、波特率、底盘协议或机械尺寸，不派硬件实现；若 inventory 意外涉及这些事实，立即停止并转查 `docs/vendor/VENDOR_INDEX.md` 后另立任务。

## 预期产物

- `artifacts/algorithm/read_only_inventory.json`
- `artifacts/algorithm/live_capture_envelope.json`
- `artifacts/algorithm/rosbag/metadata.yaml`
- `artifacts/algorithm/rosbag/*.db3`
- `artifacts/algorithm/artifact_bundle_input.json`
- `artifacts/algorithm/semantic_replay_summary.json`
- `artifacts/algorithm/cleanup_readback.json`
- `artifacts/full-stack/o6_archive_write_receipt.json`
- `artifacts/full-stack/o6_archive_readback.json`
- `artifacts/full-stack/o7_consumer_readback.json`
- `tech-done.md`、`side2side_check.md`、`final.md`

## 进入实现的 Gate

规划完成后，主节点必须按 `tech-plan.md` 派发对应 Engineer。Algorithm 必须先用 fixture/临时 DB3 完成离线测试；再做 read-only inventory。只有 inventory 同时证明以下条件才允许一次 live capture：

- SSH 可达且 ROS2/`ros2 bag` 可用；
- `/scan` 类型为 `sensor_msgs/msg/LaserScan` 且 publisher count `>=1`；
- 目标 topic 全部来自 allowlist 且 publisher count `>=1`；
- 没有既存 `ros2 bag record` 冲突；
- 临时目录可创建且 remote disk available `>=64 MiB`；
- 不需要启动、停止、重启或改变任何 runtime。

任一条件不满足，必须 `blocked_fail_closed`，live capture 调用次数保持 `0`。

## 风险、阻塞与证据缺口

1. 上位机可能没有 `ros2 bag`、DB3 storage plugin、足够磁盘或当前 publisher；这些都只允许形成 blocked inventory，不允许安装软件或启停 runtime。
2. rosbag timeout/信号收口、`--max-bag-size` 或总目录超过 16 MiB 可能留下 partial/oversize DB3；必须保留失败证据、清理 helper-owned recorder、禁止重采。
3. bag-only field manifest 总 gate 必然缺 map/route/keyframes；这不是本轮要修的 blocker。Phase C 必须消费其独立 ready sections，通过既有 artifact-bundle 主路径完成 O6/O7 回读。
4. O6/O7 既有合同可能把 current-live 数据仍标成 fixture/local mock；可做最小分类修复，但不得新增 `dataset_id` wrapper，也不得让合同开发取代真实 rosbag 主产出。
5. 本轮即使成功，也只证明严格无运动的真实传感器数据采集与离线消费；不证明路线执行、送达、HIL、控制安全、生产云或长期数据回灌。
6. O6/O7 KR 在规划阶段不归档，主百分比不预调；只有 Product 验收新 current-run 数据与跨层消费后才判断是否调整。

## 当前 KR 历史记录

本阶段没有已完成 KR，不移动 `OKR.md` 当前区或历史区。后续若验收通过，证据位置以本 sprint 的 `tech-done.md`、`side2side_check.md`、`final.md` 和上述 artifacts 为准；长期现场回灌仍作为剩余风险保留。
