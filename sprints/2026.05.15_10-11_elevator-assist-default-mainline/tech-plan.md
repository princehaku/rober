# Sprint 2026.05.15_10-11 Elevator Assist Default Mainline - Tech Plan

sprint_type: epic

## 1. 目标

交付 `software_proof_docker_elevator_assist_default_mainline_gate`：把电梯 assisted delivery 从默认关闭的可选 dry-run 推进为默认启用的安全 dry-run 主链路，并让 diagnostics / task record / `mobile/web` 能只读解释该状态。

本轮仍是 Docker/local software proof only，not real elevator, not real TTS/speaker, not real Nav2/fixed-route, not HIL, 不证明 delivery success。

## 2. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective：Objective 5（约 66%）。
2. 本 sprint 是否针对最低 Objective：不针对 Objective 5，转向 Objective 2。
3. 理由：`OKR.md` 和最近两轮 final 均明确，Objective 5 只有拿到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 等外部材料时才应继续推进。本机只有 Docker，无真实外部云/4G/OSS/CDN/DB/queue 材料，继续做本地 O5 metadata 会重复消费同一 blocker。Objective 2 KR7 现在有明确、可本机软件推进的差距：`elevator_assist_enabled` 在 behavior 和 launch 仍默认 `false`，与“跨楼层任务默认启用电梯状态链”不一致。

## 3. 文件范围与 owner

### Robot Platform Engineer

允许修改：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py`
- `onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py`
- `onboard/src/ros2_trashbot_bringup/launch/autonomous.launch.py`
- 需要同步的 Robot 文档，例如 `docs/interfaces/ros_contracts.md`

职责：

- 将 behavior 默认 `elevator_assist_enabled` 改为启用。
- 将 launch 默认 `elevator_assist_enabled` 改为 `true`。
- 保持 `elevator_assist_mode=dry_run` 为默认安全模式。
- 显式关闭时输出告警、恢复建议和 `not real` / `不证明` 边界。
- task record / diagnostics 保留 evidence_ref、mode、target_floor、状态链、失败原因、人工接管原因。

### User Touchpoint Full-Stack Engineer

允许修改：

- `mobile/web/app.js`
- `mobile/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

职责：

- 在 `mobile/web` 只读展示默认电梯 assisted delivery dry-run 状态。
- 文案必须中文优先，解释等待开门、进入电梯、请求人工按目标楼层、等待目标楼层、开门后驶出、继续送达或需要人工接管。
- 不暴露 raw ROS topic、raw JSON、`cmd_vel`、底盘协议字段。
- 不改变 Start/Confirm/Cancel gating，不把 dry-run complete / ACK / artifact pass 写成 delivery success。

### Product Manager / OKR Owner

允许后续 closeout 修改：

- `sprints/2026.05.15_10-11_elevator-assist-default-mainline/tech-done.md`
- `sprints/2026.05.15_10-11_elevator-assist-default-mainline/side2side_check.md`
- `sprints/2026.05.15_10-11_elevator-assist-default-mainline/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

职责：

- 核对工程证据和边界语言。
- 只在验证通过后更新 OKR 进度。
- 确认 `docs/` 已随实际代码改动同步。

## 4. 实施任务

### Task A - Robot 默认主链路

Owner：Robot Platform Engineer

步骤：

1. 在 `task_orchestrator.py` 中把 `declare_parameter("elevator_assist_enabled", False)` 调整为默认启用。
2. 保持 `elevator_assist_mode` 默认 `dry_run`，不引入真实电梯、真实 TTS、真实 Nav2/fixed-route 或硬件控制。
3. 在 disabled/status 输出中加入明确 `disabled_by_operator` 或等价原因、恢复建议和 `not real` / `不证明` 边界。
4. 更新 `test_task_orchestrator_collection_execution.py`，覆盖默认启用 dry-run、显式关闭告警、失败 dry-run reason、task record / diagnostics 字段。
5. 同步 `autonomous.launch.py` 默认参数为 `true`，description 写明 dry-run 是软件证明默认主链路。

### Task B - Full-stack 只读解释

Owner：User Touchpoint Full-Stack Engineer

步骤：

1. 在 `mobile/web/app.js` 使用现有 status / diagnostics 数据源展示 elevator assist 状态摘要。
2. 展示状态时优先显示中文用户文案，避免 raw schema 泄漏给普通用户。
3. 增加 forbidden success wording 围栏：不得出现真实完成、已送达、真实电梯完成、真实 TTS 完成等文案。
4. 更新 `mobile/test_mobile_web_entrypoint.py`，覆盖默认 dry-run 状态、disabled warning、failure/takeover reason、no raw ROS/hardware copy。
5. 更新 `docs/product/mobile_user_flow.md`，说明该面板是 software proof only。

### Task C - Product closeout

Owner：Product Manager / OKR Owner

步骤：

1. 读取 Robot / Full-stack worker 的实际改动与验证结果。
2. 补齐 `tech-done.md`、`side2side_check.md`、`final.md`。
3. 只在证据满足后更新 `OKR.md` Objective 2；Objective 5 不因本轮上调。
4. 更新 `docs/process/okr_progress_log.md`。
5. commit 并 push，显式排除无关本地 churn。

## 5. 后续工程验收命令

Robot / Full-stack worker 必须运行以下围栏命令，并在输出中给出日志片段：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py
PYTHONDONTWRITEBYTECODE=1 python3 onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py
PYTHONDONTWRITEBYTECODE=1 python3 mobile/test_mobile_web_entrypoint.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "elevator_assist_enabled|dry_run|software_proof_docker_elevator_assist_default_mainline_gate|not real|不证明|delivery success|真实电梯|真实喇叭|真实 Nav2|HIL" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py onboard/src/ros2_trashbot_bringup/launch/autonomous.launch.py mobile/web/app.js mobile/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py onboard/src/ros2_trashbot_bringup/launch/autonomous.launch.py mobile/web/app.js mobile/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

如果 Robot 文档或接口文档也被修改，worker 必须把对应 docs 路径加入 required `rg` 和 scoped `git diff --check`。

## 6. 本规划阶段验收命令

```bash
test -f sprints/2026.05.15_10-11_elevator-assist-default-mainline/pre_start.md && test -f sprints/2026.05.15_10-11_elevator-assist-default-mainline/prd.md && test -f sprints/2026.05.15_10-11_elevator-assist-default-mainline/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|Objective 2|elevator_assist_enabled|software_proof_docker_elevator_assist_default_mainline_gate|not real|不证明" sprints/2026.05.15_10-11_elevator-assist-default-mainline
git diff --check -- sprints/2026.05.15_10-11_elevator-assist-default-mainline
```

## 7. 风险边界

- 本轮不证明真实电梯、真实喇叭/TTS、真实 Nav2/fixed-route、WAVE ROVER、真实串口/UART、HIL、真实手机设备/browser、dropoff/cancel completion 或 delivery success。
- 如果默认启用导致旧测试大量失败，Robot worker 先定位默认值假设，不扩大到无关重构。
- 如果 `mobile/web` 没有现成 elevator assist fixture，Full-stack worker 用最小 fixture 补齐，不新建大测试堆。
- 任何涉及 WAVE ROVER、UART、底盘协议、引脚、电压、波特率或机械尺寸的判断，必须先读 `docs/vendor/VENDOR_INDEX.md`；本轮计划不要求修改硬件事实。

## 8. 交付判定

完成后可说：

- 默认电梯 assisted delivery dry-run 主链路已在 Docker/local 软件围栏中通过。
- 手机端能只读解释电梯 assisted delivery 状态和人工接管原因。
- `software_proof_docker_elevator_assist_default_mainline_gate` 具备 task record / diagnostics / mobile proof。

完成后不可说：

- 真实电梯可用。
- 真实语音/喇叭已播报。
- 真实 Nav2/fixed-route 通过。
- WAVE ROVER/HIL 通过。
- 送达成功。
- Objective 5 external proof 已补齐。
