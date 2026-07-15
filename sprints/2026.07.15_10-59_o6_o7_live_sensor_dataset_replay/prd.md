# O6/O7 真实传感器数据集回放 Epic - PRD

## 状态

- 阶段：`prd_complete`
- 前置：`pre_start.md` 已完成
- 目标：把真实上位机已有 publisher 的短时 current-run 传感器流，转化为可校验、可归档、可离线消费的数据集证据。

## 产品问题

O6/O7 已有大量 local/mock archive、route bag、semantic replay、consumer read 和 UI 合同，但 OKR 仍明确缺少真实机器人数据、真实回放/标注数据流和长期现场回灌。继续新增 wrapper、readback 或 fixture 不能验证真实数据能否穿过这条链。

同时，O5 虽是约 85% 的最低 Objective，但 `provider_runtime_preflight` 已连续消费两轮；第三轮继续做 provider wrapper 或 rerun 违反 blocker 去重红线。本轮应把现有上位机条件转化为一个不需要新增运动授权的真实数据增量。

## 用户与场景

- 主要用户：Robot Algorithm Engineer、数据/标注运营人员、Product 验收人。
- 场景：机器人保持静止，既有 ROS2 publisher 正常运行；工程师只订阅短时传感器 topic，形成 current-run rosbag，并在开发机离线完成语义摘要、O6 archive 和 O7 consumer 验证。
- 用户最终要回答的问题：这份数据是否来自本轮真实上位机、是否完整可读、是否能被既有 O6/O7 链消费、哪里仍未证明。

## 用户价值和产品北极星

产品北极星为 `current_live_robot_dataset_consumed=true`，其成立必须同时满足：

1. 本轮新 rosbag 来自 `root@192.168.1.11:37878` 上已经存在的 publisher；
2. capture 前后没有启动、停止或改变 ROS runtime，没有 topic write 或机器人控制；
3. rosbag 中 `/scan` message count `>0`，且至少一个 LaserScan 样本可离线语义解码；
4. O6 archive 和 O7 consumer 对同一 `task_id` 的 DB3 SHA-256、topic/message/timestamp lineage 回读一致；禁止新增 `dataset_id` wrapper；
5. `safe_to_control=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false` 始终固定。

manifest、readback、UI 或文档本身不构成北极星达成；它们只能消费和解释真实数据主产物。

## OKR 映射和方向判断

- O5：`暂停` 当前 provider lane。最近两轮已分别完成失败 live preflight 和离线 stage diagnostics；本轮不允许第三轮消费。
- O6：`继续`。直接补“真实机器人数据”缺口，并验证 archive/readback 能保留数据 lineage。
- O7：`继续`。直接补“真实回放/标注数据流”缺口中的真实回放输入与 PC consumer 验证；标注质量与长期回灌仍不在本轮宣称范围。
- KR 状态：规划期 `不归档`，不预调百分比。验收后 Product 依据 current-run rosbag、semantic decode 和 O6/O7 一致性再判断。

## 成功口径

### P0：真实数据主产物

- 先完成一次 read-only inventory；inventory 不得写 topic、启停 runtime 或创建控制任务。
- live capture 调用最多一次，录制时长上限 8 秒，必须传 `--max-bag-size 16777216`；capture 后整个 rosbag 目录必须 `<=16 MiB`。
- rosbag topic allowlist：
  - 必需：`/scan`，类型必须是 `sensor_msgs/msg/LaserScan`；
  - 可选：`/odom`（`nav_msgs/msg/Odometry`）、`/tf`/`/tf_static`（`tf2_msgs/msg/TFMessage`）；
  - 可选：`/diagnostics`（`diagnostic_msgs/msg/DiagnosticArray`）；
  - `/camera/image_raw` 只有 inventory 已证明 publisher 存在、类型为 `sensor_msgs/msg/Image`、磁盘 gate 通过时才可纳入；默认不纳入，避免无必要资源压力。
- 禁止使用 `-a` 或录制 allowlist 外 topic；明确不录 `/map`、`/amcl_pose`。
- 产物至少包含 `metadata.yaml` 和一个非空 DB3；topic/message/time range/size/hash 可校验。
- `/scan` message count 必须大于 0；否则保留 partial/blocked artifact，不得重采。

### P0：离线 replay 与消费

- 不执行 `ros2 bag play`；只用 SQLite/现有安全 CDR decoder 读取 DB3。
- bag-only `trashbot.field_evidence_manifest.v1` 总 gate 会因缺 map/route/keyframes fail closed，不能作为 Phase C 写入载体。只消费其独立 ready sections：`route_bag_evidence`、`route_bag_payload_replay`、`route_bag_semantic_replay`、`route_bag_full_semantic_decode_matrix` 和可选 `route_bag_pose_progress_replay`。
- 上述独立 sections 至少对 `/scan` 形成安全摘要；不输出 raw BLOB、base64、完整本机绝对路径、credential 或控制字段。
- 将独立 ready sections 组装进既有 `trashbot.o6.artifact_bundle.v1`，使用同一 `task_id` POST `/api/o6/archive/artifact-bundle` 并完成 O6 本机 loopback readback；禁止 POST `/api/o6/archive/field-evidence`。
- O7 consumer 必须消费 O6 artifact-bundle readback，并回显一致的 `task_id`、DB3 SHA-256、topic/message/timestamp counts 和 proof boundary；稳定身份不包含 `dataset_id`。
- 若既有 O6/O7 合同仅因缺 current-live source 分类而拒绝，允许最小合同修复；修复后必须使用同一份已捕获 bag 验证，不能重采。

### P0：安全与清理

- 禁止 `/initialpose`、`/cmd_vel`、`/api/base/manual`、NavigateToPose、WAVE ROVER UART、route execution、delivery、HIL；不得录制 `/map`、`/amcl_pose`。
- 禁止 `ros2 launch`、`ros2 lifecycle set`、systemd/service restart、kill 既有 ROS publisher。
- capture helper 必须记录其 own PID/PGID；结束或失败时只清理 helper-owned recorder。
- 清理后 helper-owned recorder residual count 必须为 `0`；关键既有 publisher/runtime 的 pre/post inventory 不得因本轮消失。
- 任何 fail-closed 分支都固定所有控制/成功字段为 false。

## 非目标

- 不定位或修复 O5 provider runtime。
- 不重复 O3 AMCL、TF receipt、`map->odom` 或 `/initialpose` 工作。
- 不执行导航、路线回放发布、机器人运动、送达或人工 dropoff。
- 不证明真实 RTC/视频、ASR/TTS、生产云、production DB/queue、OSS/CDN、4G/TLS。
- 不证明完整标注流水线、模型训练质量或长期数据回灌。
- 不为本轮安装 ROS package、storage plugin 或系统依赖。

## 产品流程

1. Algorithm 用离线 fixture 完成 helper 与 fail-closed 测试。
2. Algorithm 执行一次 SSH read-only inventory，记录 topic/type/publisher、rosbag availability、disk、conflict recorder 和 runtime snapshot。
3. Gate 不通过：产出 blocked inventory，`live_capture_invocation_count=0`，结束 live 阶段。
4. Gate 通过：执行唯一一次 8 秒内、`--max-bag-size 16777216` 的 allowlist rosbag record；capture 后总目录必须 `<=16 MiB`。无论成功、timeout、partial、oversize 或 pull failure，都不再次 record。
5. Algorithm 拉回并冻结 bag，记录 SHA/size/topic/message/timestamp counts，离线生成 independent ready sections 与 cleanup 证据；不把 blocked 的 bag-only manifest 总 gate 当消费输入。
6. Full-stack 将 frozen sections 组装进既有 artifact bundle，POST `/api/o6/archive/artifact-bundle`，再做 O6/O7 same-task readback；如遇合同 bug，只修消费侧并重跑离线验证。
7. Algorithm 汇总 `tech-done.md`；Product 做 side-to-side、OKR 计分与 final closeout。

## 数据与接口合同

### Algorithm -> Full-stack

必须交付以下稳定字段：

- `schema`
- `task_id`
- `source_mode=current_live_upper_computer_existing_publishers`
- `capture_started_at_utc` / `capture_finished_at_utc`
- `live_capture_invocation_count`
- `capture_duration_s`
- `topic_summaries[]`: `name`、`type`、`publisher_count_at_inventory`、`message_count`、`first_timestamp_ns`、`last_timestamp_ns`
- `bag_basename`、`bag_size_bytes`、`bag_sha256` 或安全前缀
- `metadata_sha256` 或安全前缀
- `semantic_decode_ok_count`、`semantic_decode_failed_count`
- `cleanup.helper_owned_recorder_residual_count`
- 固定 false fields 与 `not_proven[]`

原始 DB3 可以在 sprint artifact 中保存，但不得经 O6/O7 JSON API 内联传输；API 只接收 basename、size、hash、count 和安全语义摘要。

### Full-stack -> Product

必须交付：

- O6 artifact-bundle write receipt 与同 task readback；
- O7 selected-task consumer readback；
- `task_id` + DB3 SHA-256 + topic/message/timestamp counts 一致性断言；
- 对 source mode 的 current-run/historical/fixture 分类；
- 明确 proof boundary：`current_live_robot_sensor_dataset_consumed_not_route_execution_proof` 或更保守 blocked 状态；
- `delivery_success=false`、`route_execution_success=false`、`hil_pass=false`、`safe_to_control=false`。

## 验收标准

### Clean accept

以下全部满足才可接受为 current-live dataset chain：

- inventory gate clean；
- `live_capture_invocation_count=1` 且没有第二次 `ros2 bag record`；
- rosbag metadata/DB3 非空、可读，整个 rosbag 目录 `<=16 MiB`，`/scan` messages `>0`；
- LaserScan semantic decode `>0` 且 unsafe/raw/control checks clean；
- helper cleanup residual `0`，runtime/publisher safety readback无异常；
- O6/O7 同 `task_id`、DB3 SHA-256、topic/message/timestamp counts 一致；
- 所有危险字段保持 false。

### Blocked accept

出现以下任一情况时可以诚实 blocked 收口，但不能调整 OKR 主百分比：

- SSH/ROS2/rosbag/storage/remote disk `<64 MiB`/topic/publisher gate 不满足，capture count `0`；
- 唯一 capture 产出 partial/empty/corrupt/总目录超过 16 MiB 的 bag；
- `/scan` count 为 0 或 semantic decode 失败；
- O6/O7 无法消费且离线修复仍失败；
- helper-owned process residual 非 0 或 runtime safety readback异常。

Blocked 后禁止 live retry；只允许离线修复、重复 pull/读取同一 bag、或另开新 sprint 申请新授权。

## 优先级

1. P0 安全 gate 与唯一 capture 上限。
2. P0 新 current-run rosbag 与 `/scan` 非零样本。
3. P0 离线 semantic replay 与 O6/O7 lineage 一致性。
4. P1 可选 `/odom`/TF/`/diagnostics` 语义摘要。
5. P2 camera keyframe 或真实标注动作；本轮默认不做，避免扩张 live 风险。

## 风险与剩余证据链

- 短时静止采集可证明真实机器人传感器数据，但不能代替长期多场景回灌。
- `/scan` 静态场景可用于链路证明，不能代表导航/避障质量。
- O6/O7 loopback archive/consumer 仍不是 production DB/queue/OSS。
- 本轮不产生 route execution、delivery/operator acceptance、HIL 或 safe-to-control 证据。
- 若 camera 未运行，不为追求 keyframe 启动 camera；后续独立授权再补真实图像/标注流。

## Sprint 文档要求

- 已完成：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 实现后：主责 Engineer 更新 `tech-done.md`，记录实际文件、验证、live invocation、artifact lineage、cleanup 和剩余风险。
- Product 验收后：更新 `side2side_check.md`、`final.md`、`OKR.md` 与 `docs/process/okr_progress_log.md`。
- 规划阶段不创建后三份完成文档草稿，避免把计划冒充进度。
