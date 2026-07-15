# O7 真实相机关键帧标注流 Epic - Pre Start

## Sprint 声明
- `sprint_type: epic`
- 状态：`planning_complete_waiting_parallel_engineer_dispatch`
- 创建时间：`2026-07-15 11:58 CST`
- 目标：O6/O7；真实上位机 `root@192.168.1.11:37878`。
- 本轮只创建三份规划文档，不运行 SSH、live、实现或产品测试。

## 用户价值和北极星
- 用户需要一份来自本轮既有 ROS Image publisher、可用 `task_id + sha256 + topic + stamp` 复核、能进入 O6 archive/O7 annotation-ready 展示的真实单帧。
- 北极星：不启停 camera runtime、不写 topic、不控制/运动，最多捕获一帧并贯通 O6/O7 lineage。
- fixture 只验证合同，必须标 `fixture_contract_only`，不得计 live keyframe。

## OKR 映射和方向
- O5 约 85% 最低，但 `2026.07.15_09-04` 与 `10-00` 已两轮消费 `provider_runtime_preflight`；禁止第三轮，暂停 O5 lane。
- O6/O7 各约 93%，缺真实机器人数据、真实 RTC/视频与真实回放/标注数据流；本轮直补真实 keyframe material。
- `2026.07.15_10-59` `/scan` dataset inventory 已 blocked 并退役；不重跑 scan/rosbag/Full-stack Phase C。
- 规划期百分比不变、KR 不归档。

## 两个 owner 并行
- `robot-algorithm-engineer`：fixture 测 helper；最多一次 `ROS2CLI_NO_DAEMON=1` 只读 inventory；publisher gate clean 后最多订阅一帧；生成 PNG、manifest、receipt。
- `full-stack-software-engineer`：用冻结 fixture 并行实现既有 O6 artifact-bundle/task-detail 与 O7 consumer-detail 的 annotation material；fixture 不得升级 live。
- 文件范围不重叠；Full-stack 先并行做合同，live manifest 冻结后只读消费同一 artifact；Algorithm 后续集成 `tech-done.md`。

## Live gate
- 首选 `/camera/image_raw`；必须是 `sensor_msgs/msg/Image` 且 publisher count `>=1`。canonical 不可用时仅允许唯一无歧义的兼容 Image topic。
- inventory SSH 最多一次、全程 daemon-off，pre/post daemon process 无新增；remote `rclpy`/`sensor_msgs.msg.Image` 可导入。
- 不启动、停止、重启 camera/ROS runtime；不执行 launch/lifecycle/service mutation、topic write、action/control/UART。
- 任一 gate 失败：capture count `0`；capture 一旦启动则 count 固定 `1`，timeout/坏编码/转换失败也不得重试。

## 隐私、二进制和安全边界
- raw pixels 只允许进入 sprint 本地 keyframe artifact；不得进入 JSON/API/log/base64/data URL/UI state。
- O6/O7 只消费安全 basename、size、hash、topic/stamp/dimensions/encoding 与 `redaction_boundary`；UI 本轮 metadata-only。
- 固定 `safe_to_control=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`。

## Mission Objective 0 四 delta
- fixture、blocked inventory、partial capture：`current_run_artifact_delta=false`，其他三 delta 也 false。
- 真实单帧 + media/hash/manifest + O6/O7 lineage 全 clean：仅 `current_run_artifact_delta=true`。
- `external_artifact_delta=false`、`live_control_delta=false`、`user_action_delta=false` 始终固定，因此 Mission Objective 0 仍未满足。

## 禁止重用、风险与留档
- 禁止 provider/preflight/readback/export/status/browser/voice/packet/mock wrapper；禁止旧 camera/keyframe/fixture 冒充本轮 live。
- 可能 blocked 于无 publisher、graph 歧义、near-black/隐私、encoding/layout 或 conversion；不得启动 camera 补齐。
- 真实 RTC/video、visible content、隐私批准、production annotation/cloud/OSS、route/delivery/HIL 均不在本轮证明范围。
- 当前只创建 `pre_start.md`、`prd.md`、`tech-plan.md`；实现后写 `tech-done.md`，Product 再写 `side2side_check.md`/`final.md` 并按事实更新 OKR/log。
