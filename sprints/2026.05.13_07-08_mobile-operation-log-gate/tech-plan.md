# Sprint 2026.05.13_07-08 Mobile Operation Log Gate - Tech Plan

## 目标

建立 `software_proof_docker_mobile_operation_log_gate`：在手机 PWA 中展示 phone-safe 操作/状态事件日志、异常恢复提示和支持交接摘要入口，并用 robot compatibility fence 证明该 metadata 不触发 robot action、ACK 或 cursor 变化。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 最低 Objective 是 Objective 4：手机用户体验与低成本量产边界，约 58%。
2. 本 sprint 直接针对 Objective 4。选择理由是 O4 低于 Objective 5 约 59%，且在 Docker-only 环境仍可通过 local/mobile software proof 推进"查看状态 -> 处理异常 -> 支持交接"闭环。
3. 不选择 Objective 1：O1 约 75%，主要缺真实 WAVE ROVER、真实串口、`T=1001` feedback、`/odom`、`/imu/data`、`/battery` 实机样本；当前本机无真实硬件，只能继续做软件护栏，优先级低于 O4。
4. 不选择 Objective 2：O2 约 77%，主要缺真实 Nav2/fixed-route、同一 `evidence_ref` 任务复盘、真实送达和失败恢复实测；当前 Docker-only 无法证明真实任务闭环。
5. 不选择 Objective 3：O3 约 77%，主要缺真实路线采集、Nav2 waypoint/fixed-route 实跑、关键帧实景证据；当前不具备实景路线证据。
6. 不选择 Objective 5：O5 约 59%，虽然仍可做 production DB/queue 或公网/TLS dry-run，但 live OKR 显示 O4 更低，且最新 cloud sprint 已建议按最低可推进目标重排。
7. Docker-only 边界：本 sprint 只能声明 Docker/local software proof。不得声明真实手机设备/浏览器、production app、真实 PWA install prompt、真实云、真实 HTTPS/TLS、公网入口、4G/SIM、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

## 技术方案

### 全栈手机端方案

- 在 `mobile/web/` 中消费既有 phone-safe status/diagnostics 字段，生成 operation log 面板。
- operation log 只展示安全摘要：状态事件、用户操作 gate、blocked reason、pending ACK、offline/recovering、manual takeover、support handoff。
- 若 fixture 中提供 `operation_log`，优先展示；若没有，则从现有 `phone_readiness`、`command_safety`、`phone_task_flow_readiness`、`phone_offline_resume_readiness`、`phone_support_bundle`、`voice_prompt_readiness` 中派生最小事件列表。
- Start/Confirm/Cancel 的启用逻辑不得因为 operation log 增加新路径；仍以 `command_safety.actions.<action>.enabled=true` 和 legacy `can_*` 为最终 gate。
- `mobile/fixtures/mobile_web_status.fixture.json` 增加 operation log / blocked / support handoff 示例，并继续标注 fixture only。
- `mobile/test_mobile_web_entrypoint.py` 增加静态 smoke，覆盖面板可见、恢复提示可见、支持入口可见、Start fail-closed、敏感字段不出现在渲染路径。

### Robot compatibility 方案

- 在 `test_remote_bridge.py` 和 `test_remote_bridge_protocol.py` 中增加 metadata-only operation log response / command metadata 样例。
- 验证 operation-log metadata 不触发 backend action。
- 验证不 POST ACK。
- 验证不推进或持久化 cursor。
- 验证 protocol normalization 剥离 command envelope 外的 operation-log metadata。
- 文档中明确 operation log 是 phone/support metadata，不属于 `trashbot.remote.v1` action 语义。

## 并行 owner 拆分

### Task A：full-stack-software-engineer

文件范围：

- `mobile/web/`
- `mobile/fixtures/`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`

实现要求：

- 增加手机端 operation log 面板，中文优先展示最近事件、恢复提示和支持交接入口。
- 保持 dependency-free PWA，不引入 npm/build step。
- 保持 API consumer 边界：mobile 端消费 phone-safe JSON，不发明 robot state。
- 保持 Start/Confirm/Cancel fail-closed。
- 更新 fixture 与 smoke tests。
- 更新 mobile README 与 product doc，写清 `software_proof_docker_mobile_operation_log_gate` 和非证明边界。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
git diff --check -- mobile/web mobile/fixtures mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md
```

预期结果：

- unittest 输出 `OK`。
- scoped `git diff --check` 无输出。
- smoke 证明 operation log、恢复提示和支持入口存在，且 primary actions 不被错误启用。

### Task B：robot-software-engineer

文件范围：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`
- `docs/product/remote_4g_mvp.md`

实现要求：

- 增加 operation-log metadata-only compatibility fence。
- 覆盖不触发 action、不 POST ACK、不推进 cursor、不持久化 cursor。
- 覆盖 protocol normalization 剥离 command envelope 外 metadata。
- 更新接口与远程 MVP 文档，明确 operation-log metadata 不改变 `trashbot.remote.v1` command/status/ack 语义。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py
git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md docs/product/remote_4g_mvp.md
```

预期结果：

- targeted unittest 输出 `OK`。
- `py_compile` 无输出。
- scoped `git diff --check` 无输出。
- metadata-only fence 证明 operation log 不产生 robot side effect。

### Task C：product-okr-owner closeout

文件范围：

- `sprints/2026.05.13_07-08_mobile-operation-log-gate/tech-done.md`
- `sprints/2026.05.13_07-08_mobile-operation-log-gate/side2side_check.md`
- `sprints/2026.05.13_07-08_mobile-operation-log-gate/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

收口要求：

- 汇总 Task A 和 Task B 实际改动与验证输出。
- 检查所有引用文档路径真实存在。
- 保守更新 Objective 4 进度；Objective 1/2/3/5 除非有新证据不调整。
- 明确 evidence boundary：`software_proof_docker_mobile_operation_log_gate`。
- 明确不声明真实手机设备/browser、production app、真实云/4G、OSS/CDN live traffic、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

验收命令：

```bash
test -f docs/product/mobile_user_flow.md && test -f docs/product/remote_4g_mvp.md && test -f docs/interfaces/ros_contracts.md && test -f docs/process/okr_progress_log.md
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_07-08_mobile-operation-log-gate
```

## 接口影响

- `mobile/web/` 可增加 operation-log consumer 逻辑，但不改变 robot action/service/topic contract。
- 如果新增 JSON 字段，必须是 phone-safe metadata，如 `operation_log` 或 `phone_operation_log`，且字段值不得包含敏感信息或硬件内部字段。
- `trashbot.remote.v1` command/status/ack envelope 不因本轮改变。
- ACK 继续表示 accepted/processing evidence only，不是 delivery success。

## 安全与隐私边界

operation log、恢复提示和支持摘要不得包含：

- token、Authorization header、OSS AK/SK、root password。
- DB URL、queue URL、credential-bearing URL。
- raw ROS topic、`/cmd_vel`、serial device、baudrate、WAVE ROVER 参数。
- local filesystem path、traceback、checksum、完整 artifact。
- 可被误读为真实送达、HIL、真实云或真实手机验收的文案。

## 验证计划

后续执行阶段必须至少运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py
git diff --check -- mobile/web mobile/fixtures mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md docs/product/remote_4g_mvp.md
```

本 planning 阶段验收命令：

```bash
test -f sprints/2026.05.13_07-08_mobile-operation-log-gate/pre_start.md && test -f sprints/2026.05.13_07-08_mobile-operation-log-gate/prd.md && test -f sprints/2026.05.13_07-08_mobile-operation-log-gate/tech-plan.md
git diff --check -- sprints/2026.05.13_07-08_mobile-operation-log-gate/pre_start.md sprints/2026.05.13_07-08_mobile-operation-log-gate/prd.md sprints/2026.05.13_07-08_mobile-operation-log-gate/tech-plan.md
```

## 风险与回滚

- 如果 mobile smoke 发现 operation log 需要 backend 字段而当前 fixture/status 不具备，Task A 必须先用 fixture-only 示例证明 UI consumer，不得伪造 live robot state。
- 如果 robot fence 发现 metadata 进入 action path，Task B 必须收紧 normalization 或 test expectation，不能用文档解释绕过。
- 如果 validation 只能证明 local static rendering，Product closeout 必须把 OKR 更新控制在 Objective 4 的软件证明增量，不得夸大为真实手机验收。
- 回滚方式是移除 operation-log UI/fixture/test 增量和对应 docs 增量；不得回滚无关 sprint 或其他 worker 改动。
