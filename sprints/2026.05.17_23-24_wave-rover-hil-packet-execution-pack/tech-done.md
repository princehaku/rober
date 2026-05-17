# Sprint 2026.05.17_23-24 Wave Rover HIL Packet Execution Pack - Tech Done

sprint_type: epic

## 1. 用户价值和产品北极星

本轮把上一轮 WAVE ROVER HIL packet review decision 继续推进为可交给硬件现场执行的 HIL packet execution pack。用户价值不是证明小车已经上车跑通，而是让 Hardware 在拿到真实 WAVE ROVER、真实 UART 和真实 topic sample 环境后，有一份可复跑、可补证、可回填、不会把 software fixture 冒充 HIL 的操作包。

产品北极星保持不变：普通手机用户最终只看到可解释、可恢复的送垃圾状态；工程侧必须先把底盘协议、证据包和复核路径做成可追溯链路，才能进入真实 HIL、真实路线和真实送达。

## 2. OKR 映射与 KR 拆解

- 主目标：Objective 1。新增 `software_proof_docker_wave_rover_hil_packet_execution_pack_gate`，把真实 HIL packet 所需材料、采集顺序、owner handoff、backfill guidance 和 rerun commands 固化。
- 支撑目标：Objective 4。mobile/web 新增只读 execution-pack panel，让手机/支持界面能解释还缺哪些硬件材料，但不放开 Start Delivery、Confirm Dropoff 或 Cancel。
- 不推进：Objective 5。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser external proof。
- 不推进为完成：Objective 2 / Objective 3。本轮没有 route/elevator field pass、Nav2/fixed-route 实跑、真实 task record、dropoff/cancel completion 或 delivery result。

## 3. 本轮实际改动

### Hardware Task A

- 新增 `pc-tools/evidence/wave_rover_hil_packet_execution_pack.py`。
- 新增 `pc-tools/evidence/test_wave_rover_hil_packet_execution_pack.py`。
- 新增 `pc-tools/evidence/fixtures/wave_rover_hil_packet_execution_pack/`。
- 新增 `docs/hardware/wave_rover_hil_packet_execution_pack.md`。
- 采用的硬件资料来源：`docs/vendor/VENDOR_INDEX.md`，以及其指向的 WAVE ROVER `json_cmd.h`、`uart_ctrl.h`、`ugv_rpi/base_ctrl.py`、`ugv_rpi/config.yaml`。
- 证据边界：只证明 `software_proof_docker_wave_rover_hil_packet_execution_pack_gate`，不打开 serial、不探测 `/dev/*`、不调用 ROS graph。

### Robot Task B

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 更新 `docs/interfaces/ros_contracts.md`。
- 新增 diagnostics metadata-only consumer，支持 execution-pack summary 只读消费，并对 unsupported schema/boundary、unsafe success/control claim、`delivery_success=true`、`primary_actions_enabled=true` 等 fail closed。
- 修复了 unsafe blocked copy 仍保留 success 文案的问题。

### Full-stack Task C

- 更新 `mobile/web/app.js`。
- 更新 `mobile/fixtures/mobile_web_status.fixture.json`。
- 更新 `mobile/web/test_mobile_web_entrypoint.py`。
- 更新 `docs/product/mobile_user_flow.md`。
- 新增 mobile/web 只读 execution-pack panel，只展示 safe `evidence_ref`、required material templates、collection sequence、owner handoff、rerun commands、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。
- Start Delivery、Confirm Dropoff、Cancel gating 未改变。

### Product Task D

- 创建本文件、`side2side_check.md`、`final.md`。
- 更新 `OKR.md` 当前快照。
- 更新 `docs/process/okr_progress_log.md`。

## 4. 独立复验结果

运行时间：2026-05-17 23:16 Asia/Shanghai。

```text
python3 -m py_compile pc-tools/evidence/wave_rover_hil_packet_execution_pack.py pc-tools/evidence/test_wave_rover_hil_packet_execution_pack.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
exit 0
```

```text
python3 -m unittest pc-tools/evidence/test_wave_rover_hil_packet_execution_pack.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py mobile/web/test_mobile_web_entrypoint.py
.........................................................................................................................................................................................................................................
Ran 233 tests in 0.587s
OK
```

```text
python3 pc-tools/evidence/wave_rover_hil_packet_execution_pack.py --help
usage: wave_rover_hil_packet_execution_pack.py [-h] [--review-summary REVIEW_SUMMARY] [--evidence-ref EVIDENCE_REF] [--output OUTPUT] [--summary-output SUMMARY_OUTPUT] [--once-json]
Generate WAVE ROVER HIL packet execution-pack software-proof artifact.
exit 0
```

```text
node --check mobile/web/app.js
exit 0
```

```text
rg "software_proof_docker_wave_rover_hil_packet_execution_pack_gate|Objective 1|Objective 5|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false|hil_pass" ...
exit 0，命中 OKR、progress log、sprint 文档、hardware doc、ROS contract 和 mobile product doc 中的边界字段。
```

```text
rg "wave_rover_hil_packet_execution_pack|software_proof_docker_wave_rover_hil_packet_execution_pack_gate|required_material_templates|collection_sequence|owner_handoff|rerun_commands|not_proven" ...
exit 0，命中 PC gate、Robot diagnostics、mobile/web、fixtures、hardware/interface/product docs 中的 contract 字段。
```

最终 closeout 后已通过：

```text
test -f sprints/2026.05.17_23-24_wave-rover-hil-packet-execution-pack/tech-done.md && test -f sprints/2026.05.17_23-24_wave-rover-hil-packet-execution-pack/side2side_check.md && test -f sprints/2026.05.17_23-24_wave-rover-hil-packet-execution-pack/final.md
exit 0
```

```text
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_23-24_wave-rover-hil-packet-execution-pack
exit 0
```

## 5. 偏差与失败定位

- 无产品代码重试需求。A/B/C 的复验命令均通过。
- 初始 closeout 文件不存在是本 Task D 的预期输入状态，已通过创建 `tech-done.md`、`side2side_check.md`、`final.md` 收口。
- 未运行真实 Docker/Humble `colcon build`、真实 WAVE ROVER HIL、真实 UART、真实手机/browser 或真实路线验证；这些超出本轮文件范围和当前 Docker-only 环境。

## 6. 剩余风险

- 仍缺真实 WAVE ROVER、真实 UART、真实 `/dev/ttyUSB*`、真实 `feedback_T1001.log`、真实 `/odom`、真实 `/imu/data`、真实 `/battery`、真实 operator HIL report 和 `hil_pass`。
- 仍缺 PR #5 相关真实 2D LiDAR / ToF SKU/source、receipt、采购、安装、接线、电源、标定和 HIL-entry 材料。
- 仍缺 PR #4 route/elevator field materials：真实门状态、真实楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record、completion signal、dropoff/cancel completion 和 delivery result。
- 仍缺真实手机设备/browser、production app、真实 PWA prompt/user choice。
- 仍缺 Objective 5 external proof：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover。

## 7. 责任 Engineer 与下一步

- Hardware Infra Engineer：带 execution pack 到真实 WAVE ROVER 主机采集同一 safe `evidence_ref` 的 HIL packet。
- Robot Platform Engineer：在真实 packet 进入 review decision 前，继续只读消费 software-proof summary，不能放开 primary actions。
- User Touchpoint Full-Stack Engineer：保持 mobile execution-pack panel 只读，不能展示本机路径、serial、baudrate、raw topic、traceback、checksum、credential 或完整 raw feedback。
- Product Manager / OKR Owner：OKR 只保守记录 software proof，不把本轮写成 `hil_pass`、真实送达或 Objective 5 production proof。
