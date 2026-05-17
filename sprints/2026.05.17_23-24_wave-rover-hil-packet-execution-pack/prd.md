# Sprint 2026.05.17_23-24 Wave Rover HIL Packet Execution Pack - PRD

sprint_type: epic

## 1. 用户价值

硬件同学拿到真实 WAVE ROVER 和串口环境时，需要一份不会误导、不会泄漏本机路径、不会把软件 fixture 冒充 HIL 的执行包。执行包应明确采集哪些材料、每份材料的用途、采集顺序、失败回填路径、owner handoff 和复跑命令，让 Objective 1 的真实 HIL 补证从“聊天里知道缺什么”变成可执行操作包。

## 2. OKR 映射

- 主目标：Objective 1，可信底盘控制层和 HIL packet 补证准备。
- 支撑目标：Objective 4，手机端只读展示硬件执行包状态，但不改变 Start Delivery / Confirm Dropoff / Cancel gating。
- 不推进：Objective 5。缺真实外部云/4G/DB/queue/OSS/CDN/手机 proof，本轮不写成 production proof。

## 3. 产品需求

新增 `wave_rover_hil_packet_execution_pack` contract：

- 输入：上一轮 `wave_rover_hil_packet_review_decision` artifact 或 summary。
- 输出：`trashbot.wave_rover_hil_packet_execution_pack.v1` 和 `trashbot.wave_rover_hil_packet_execution_pack_summary.v1`。
- 边界：`software_proof_docker_wave_rover_hil_packet_execution_pack_gate`。
- 必须包含：
  - safe `evidence_ref`
  - execution readiness / pack status
  - required material templates
  - collection sequence
  - owner handoff
  - rerun commands
  - failure/backfill guidance
  - vendor source list
  - `not_proven`
  - `delivery_success=false`
  - `primary_actions_enabled=false`

## 4. 验收口径

- PC gate 能消费 review decision summary，缺失、unsupported schema、unsupported boundary、unsafe success claim、unsafe path、`evidence_ref` mismatch 都 fail closed。
- Robot diagnostics 只读消费 summary，不开启 ACK、Start、Cancel、dropoff 或底盘控制。
- mobile/web 只读展示 execution pack，不展示本机绝对路径、serial device、baudrate、raw ROS topic、traceback、checksum、credential、`/cmd_vel` 或 full raw feedback。
- docs 同步更新 `docs/hardware/`、`docs/interfaces/`、`docs/product/`。
- 验证只跑围栏：`py_compile`、focused unittest、`node --check`、必要 `rg` 和 scoped `git diff --check`。

## 5. 非目标

- 不跑真实 WAVE ROVER。
- 不打开串口或扫描 `/dev/*`。
- 不调用 ROS graph。
- 不声明 `hil_pass`。
- 不提升 Objective 5。
