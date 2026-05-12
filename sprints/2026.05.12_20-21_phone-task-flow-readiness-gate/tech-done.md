# Sprint 2026.05.12_20-21 Phone Task Flow Readiness Gate - Tech Done

## Task A：Phone task-flow readiness gate

Owner：`full-stack-software-engineer`

状态：implemented，等待 Task B 兼容性围栏追加。

实际改动：

- `operator_gateway_http.py` 新增 `trashbot.phone_task_flow_readiness.v1` / `phone_task_flow_readiness`，并把 `/api/status.phone_readiness.evidence_boundary` 推进到 `software_proof_docker_phone_task_flow_readiness_gate`。
- `/api/status` 顶层和 `phone_readiness` 内同时暴露任务步骤 metadata：连接/就绪、目的地、装载确认、一键发车、状态解释、求助/诊断。
- `/api/diagnostics` 追加同一份 `phone_task_flow_readiness` 摘要，便于支持人员复现首屏阻塞点；Diagnostics 仍不代表主任务 ready。
- 首屏步骤从工程状态条调整为普通用户任务流程，并保留 Start/Confirm/Cancel 的 `command_safety` gate；ACK 文案继续说明只代表 command accepted/processing evidence，不等于 delivery success。
- `docs/product/mobile_user_flow.md` 同步新增 task-flow readiness gate 能力、字段、证据边界和未证明范围。

验证结果：

- Passed：`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py`
  - 输出：`Ran 46 tests in 20.115s` / `OK`
- Passed：`PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
  - 输出：exit 0
- Passed：`git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py docs/product/mobile_user_flow.md sprints/2026.05.12_20-21_phone-task-flow-readiness-gate/tech-done.md`
  - 输出：exit 0

失败定位和修复：

- 首轮实现前发现 `tech-done.md` 尚不存在；按本 sprint 文档契约创建，并只写 Task A 段落。
- 暂无验证失败。

剩余风险：

- 当前证据边界仅为 `software_proof_docker_phone_task_flow_readiness_gate`。
- 未证明真实手机设备 Safari/Chrome、production app、真实云、真实 4G/SIM、OSS/CDN 实流量、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达成功。

## Task B：Remote command/status/ack compatibility fence

Owner：`robot-software-engineer`

状态：implemented。

实际改动：

- `test_remote_bridge.py` 新增 phone task-flow metadata 兼容性围栏，覆盖 `status_response`、`command_response`、`ack_response` 携带 `phone_task_flow_readiness` 时，robot ACK envelope 仍保持 `trashbot.remote.v1` command/status/ack 语义。
- 新增 metadata-only response 围栏，确认只有 `phone_task_flow_readiness` / preflight metadata、没有 command envelope 时，不触发本地 robot action、不提交 ACK、不推进 `last_ack_id`、不持久化 cursor。
- 未修改 `remote_bridge.py` 行为；本轮只补 targeted unittest，未扩大为 broad regression。

验证结果：

- Passed：`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py`
  - 输出：`Ran 33 tests in 16.314s` / `OK`
- Passed：`PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
  - 输出：exit 0
- Passed：`git diff --check -- src/ros2_trashbot_behavior/test/test_remote_bridge.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py sprints/2026.05.12_20-21_phone-task-flow-readiness-gate/tech-done.md`
  - 输出：exit 0

失败定位和修复：

- 未发现 remote bridge 行为回归；不需要修改生产代码。

剩余风险：

- 当前证据仅证明 local unittest 级别的 compatibility fence，不证明真实云、真实 4G/SIM、生产队列/数据库、多实例一致性、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达成功。
- ACK 仍只表示 command accepted/processing evidence；不等于 delivery success。
