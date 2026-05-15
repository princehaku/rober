# Sprint 2026.05.15_10-11 Elevator Assist Default Mainline - Tech Done

sprint_type: epic

## 1. 实际改动

Task A - Robot Platform Engineer：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py`
  - 将 `elevator_assist_enabled` 默认值改为 `True`，使跨楼层 assisted delivery dry-run 进入默认主链路。
  - 保持 `elevator_assist_mode=dry_run` 为唯一默认安全模式，不引入真实电梯、真实喇叭/TTS、真实 Nav2/fixed-route 或 WAVE ROVER/HIL 行为。
  - 为 `task_record.elevator_assist` 增加 `software_proof_docker_elevator_assist_default_mainline_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_phone_copy`、`rerun_guidance`、失败原因和人工接管原因。
  - 显式关闭时记录 `reason=disabled_by_operator` 与 warning，并允许非跨楼层 dry-run 继续，避免把 operator disable 误判为真实能力失败。
- `onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py`
  - 覆盖默认电梯 dry-run 主链路、显式关闭告警、失败接管原因和 boundary 字段。
- `onboard/src/ros2_trashbot_bringup/launch/autonomous.launch.py`
  - 将 `elevator_assist_enabled` launch 默认值改为 `true`，description 明确这是 software proof mainline，不是真实电梯/TTS/Nav2/HIL。
- `docs/interfaces/ros_contracts.md`
  - 同步 behavior 参数契约和 task record evidence boundary。

Task B - User Touchpoint Full-Stack Engineer：

- `mobile/web/app.js`
  - 新增只读“电梯辅助状态” panel，兼容消费 `elevator_assist`、`elevator_assist_summary`、`phone_elevator_assist`、`phone_readiness`、`diagnostics.summary` 和嵌套 diagnostics summary。
  - 展示 `dry_run`、phase、target floor、phase chain、human-help request、failure/takeover reason、`delivery_success=false`、`primary_actions_enabled=false`、boundary 和 `not_proven`。
  - 新增 sanitizer，阻止 raw ROS/hardware copy、credentials、local paths、raw artifact 和 misleading success phrases。
  - 未改变 Start Delivery、Confirm Dropoff、Cancel gating。
- `mobile/test_mobile_web_entrypoint.py`
  - 覆盖面板只读、phone-safe 文案、fixture schema、boundary 和 forbidden copy。
- `mobile/fixtures/mobile_web_status.fixture.json`
  - 增加 top-level 与 `phone_readiness` 下的 elevator assist fixture。
- `docs/product/mobile_user_flow.md`
  - 同步说明该面板是 `software_proof_docker_elevator_assist_default_mainline_gate` only。

Task C - Product closeout：

- `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`
  - 补齐本轮实际改动、验收结果、OKR closeout、证据边界和下一步缺口。

## 2. 验证结果

Product closeout 重新运行整合后的 fenced validation：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py
exit 0

PYTHONDONTWRITEBYTECODE=1 python3 onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py
...........
Ran 11 tests in 0.013s
OK

PYTHONDONTWRITEBYTECODE=1 python3 mobile/test_mobile_web_entrypoint.py
.........................................
Ran 41 tests in 0.095s
OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
exit 0

node --check mobile/web/app.js
exit 0

rg -n "elevator_assist_enabled|dry_run|software_proof_docker_elevator_assist_default_mainline_gate|not real|不证明|delivery_success|真实电梯|真实喇叭|真实 Nav2|HIL" ...
exit 0; required Robot, mobile, docs, sprint, OKR, and progress-log terms present.

git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py onboard/src/ros2_trashbot_bringup/launch/autonomous.launch.py mobile/web/app.js mobile/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json docs/interfaces/ros_contracts.md docs/product/mobile_user_flow.md sprints/2026.05.15_10-11_elevator-assist-default-mainline OKR.md docs/process/okr_progress_log.md
exit 0
```

## 3. 偏差

- 本轮没有做真实电梯门识别、真实楼层识别、真实喇叭/TTS 播放、真实 Nav2/fixed-route 驶入驶出、WAVE ROVER 串口控制、HIL、真实手机设备/browser、production app 或 O5 external proof。
- `mobile/web` 为避免扩大静态 HTML 文件范围，采用 JS 注入只读 panel；这符合本轮文件范围和兼容性目标。

## 4. 剩余风险

- `software_proof_docker_elevator_assist_default_mainline_gate` 只证明默认配置、状态链记录、diagnostics/task record metadata 和手机只读解释在本机软件围栏中可验证。
- 仍需同一 `evidence_ref` 的受控楼宇实测材料：真实门状态、楼层证据、人工协助记录、Nav2/fixed-route runtime log、task completion、失败恢复和 WAVE ROVER/HIL。
- Objective 5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、worker/migration 和外部 probe 证据。
