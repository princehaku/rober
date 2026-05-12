# Sprint 2026.05.12_20-21 Phone Task Flow Readiness Gate - Tech Plan

## 状态

- 阶段：tech-plan
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 兼容性围栏：`robot-software-engineer`
- 目标 evidence boundary：`software_proof_docker_phone_task_flow_readiness_gate`

## 技术目标

把本地/Docker phone/operator entry 从 PWA/installability shell 推进到普通用户任务流程 readiness gate。实现后，手机首屏和 diagnostics 应以用户任务步骤为组织方式：连接/就绪、目的地、装载确认、发车、状态解释、失败/人工接管/诊断入口。

本轮不证明真实手机设备、真实生产 app、真实云、真实 4G、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

## 任务拆分

### Task A：Phone task-flow readiness gate

Owner：`full-stack-software-engineer`

允许改动范围：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_static.py`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.12_20-21_phone-task-flow-readiness-gate/tech-done.md`

实现要求：

- 增加 `trashbot.phone_task_flow_readiness.v1` 或等价 phone-safe metadata，表达任务步骤、阻塞原因、下一步动作和未证明范围。
- 首屏/状态/diagnostics 展示覆盖连接/就绪、选择或确认目的地、确认已放入垃圾、一键发车、状态解释、失败/人工接管/诊断入口。
- 用户可见 copy 只用普通用户语言；不得展示 raw ROS topic、串口、baudrate、JSON payload、token、Authorization header、cloud secret、WAVE ROVER 参数或硬件配置。
- Start/Confirm/Cancel 继续由既有 action permissions + command safety 控制；Diagnostics 可访问但不代表主任务 ready。
- ACK copy 必须说明 command accepted/processing evidence，不等于 delivery success。
- 同步更新 `docs/product/mobile_user_flow.md`，记录 `software_proof_docker_phone_task_flow_readiness_gate` 的能力和未证明范围。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py
git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py docs/product/mobile_user_flow.md sprints/2026.05.12_20-21_phone-task-flow-readiness-gate/tech-done.md
```

输出要求：

1. 实际改动的文件列表。
2. 验证命令输出结果。
3. 失败定位和修复说明，如有。
4. 剩余风险。

### Task B：Remote command/status/ack compatibility fence

Owner：`robot-software-engineer`

允许改动范围：

- `src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
- `sprints/2026.05.12_20-21_phone-task-flow-readiness-gate/tech-done.md`

实现要求：

- 只做兼容性围栏；除非测试发现真实回归，不主动改 remote bridge 行为。
- 确认新增 phone task-flow metadata 不改变 remote command/status/ack envelope。
- 确认 ACK 不被解释为 delivery success。
- 确认新增 metadata 不触发额外 robot action。
- 确认新增 metadata 不推进 cursor。
- 若需补测试，保持 targeted unittest，不扩成 broad regression。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
git diff --check -- src/ros2_trashbot_behavior/test/test_remote_bridge.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py sprints/2026.05.12_20-21_phone-task-flow-readiness-gate/tech-done.md
```

输出要求：

1. 实际改动的文件列表。
2. 验证命令输出结果。
3. 失败定位和修复说明，如有。
4. 剩余风险。

## 接口影响

- 允许新增 phone-safe metadata 或 UI copy。
- 不允许改变 remote command/status/ack envelope 的现有语义。
- 不允许把 ACK、command accepted、queue persisted 或 diagnostics ready 写成 delivery success。
- 不允许发起额外 robot action、隐藏发车阻塞或推进 remote cursor。
- 老客户端应可忽略新增 metadata。

## 验证计划

本轮验证只做围栏，不新增大套测试。

Full-stack 验证：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py
git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py docs/product/mobile_user_flow.md sprints/2026.05.12_20-21_phone-task-flow-readiness-gate/tech-done.md
```

Robot compatibility 验证：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
git diff --check -- src/ros2_trashbot_behavior/test/test_remote_bridge.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py sprints/2026.05.12_20-21_phone-task-flow-readiness-gate/tech-done.md
```

Product planning 文档验证：

```bash
git diff --check -- sprints/2026.05.12_20-21_phone-task-flow-readiness-gate/pre_start.md sprints/2026.05.12_20-21_phone-task-flow-readiness-gate/prd.md sprints/2026.05.12_20-21_phone-task-flow-readiness-gate/tech-plan.md
```

## 风险边界

- 当前环境 Docker-only，不能做真实手机、真实硬件、真实云、真实 4G 或 HIL 验证。
- 本轮只提升 O5 的 local/Docker phone task-flow readiness，不提升 O6 或硬件/导航 Objective。
- 若需要真实用户验收，下一轮必须使用 physical phone device 和生产/准生产入口。
- 若工程实现改动涉及硬件细节、串口、WAVE ROVER 或底盘协议，必须先查 `docs/vendor/VENDOR_INDEX.md`；本轮计划不要求触碰硬件事实。

## 交付后文档同步

- Task A 必须更新 `docs/product/mobile_user_flow.md`。
- Task A 和 Task B 必须把实际改动、验证结果、偏差和剩余风险写入 `tech-done.md`。
- Product 收口必须更新 `side2side_check.md`、`final.md` 和 `OKR.md`，并保持 `software_proof_docker_phone_task_flow_readiness_gate` 与真实手机/真实云/真实 4G/HIL/送达成功的边界。
