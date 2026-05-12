# Sprint 2026.05.12_24-25 Phone Voice Prompt Readiness Gate - Tech Plan

## 状态

- 阶段：tech-plan
- Product Owner：`product-okr-owner`
- 主线 Objective：O5 手机体验与量产边界
- Evidence boundary：`software_proof_docker_phone_voice_prompt_readiness_gate`
- 执行模式：tech-plan 完成后进入 implementation，由对应 worker 执行；主节点不直接改产品代码或测试代码。

## 总体方案

在现有 operator gateway phone readiness 之上新增 voice prompt readiness gate。它是 phone-safe prompt contract readiness，不是真实喇叭/TTS 播放证明：

- API 层：新增 `voice_prompt_readiness` helper，复用已有 status、phone_copy、speaker_prompt、elevator_assist、phone_readiness、command_safety、ACK 和 support handoff 语义。
- 状态层：`/api/status` 顶层、`phone_readiness.voice_prompt_readiness` 和 `/api/diagnostics.voice_prompt_readiness` 使用同一 schema。
- UI 层：首屏新增 voice prompt readiness 区域，显示当前应播报/朗读的中文提示、触发状态、人工接管要求和未证明边界。
- 兼容层：remote bridge command/status/ack envelope、cursor、ACK 语义、robot action 触发不变。

## 接口 contract

新增对象：

```text
schema=trashbot.voice_prompt_readiness.v1
schema_version=1
evidence_boundary=software_proof_docker_phone_voice_prompt_readiness_gate
```

必备字段：

- `current_prompt`：当前应该播报或朗读的提示词，中文优先；无提示时给出 safe fallback。
- `prompt_language`：例如 `zh-CN` 或 `en-US`。
- `trigger_state`：来源状态，例如 `waiting_for_trash`、`requesting_floor_help`、`target_floor_unconfirmed`、`unsafe_to_exit`、`failed`、`needs_human_help`。
- `trigger_reason`：普通用户可读原因，例如等待装载、电梯求助、目标楼层未确认、需要人工接管。
- `requires_human_help`：是否需要用户或旁人介入。
- `playback_ready`：本地 Docker proof 中必须保持 false 或等价 blocked/unknown，避免暗示真实喇叭/TTS 已验证。
- `safe_phone_copy`：首屏显示文案，说明当前提示和下一步。
- `ack_semantics`：ACK 只代表 accepted/processing evidence，不等于 delivery success，也不等于 prompt 已真实播放。
- `support_refs`：脱敏引用，例如状态、failure code、task id、安全诊断 key；不得包含 local path、token 或完整 artifact。
- `not_proven`：real speaker、TTS playback、microphone, real phone device、production app、real cloud/4G、OSS/CDN live traffic、Nav2/fixed-route、WAVE ROVER、HIL、delivery success 等未证明能力。

## Task A - Full-Stack Voice Prompt Readiness

Owner：`full-stack-software-engineer`

允许改动文件范围：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_static.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_static.py`
- `docs/product/mobile_user_flow.md`
- `docs/interfaces/ros_contracts.md`
- `sprints/2026.05.12_24-25_phone-voice-prompt-readiness-gate/tech-done.md`

实现要求：

- 新增 `trashbot.voice_prompt_readiness.v1` summary builder，尽量复用已有 phone readiness / diagnostics helper，避免 `/api/status` 和 `/api/diagnostics` 口径漂移。
- `/api/status` 顶层新增 `voice_prompt_readiness`，并在 `phone_readiness.voice_prompt_readiness` 中引用同口径对象。
- `/api/diagnostics` 新增 `voice_prompt_readiness`。
- 本地 fallback HTML 首屏加入 voice prompt readiness 区域；展示 `current_prompt`、`trigger_state`、`requires_human_help`、`playback_ready`、`safe_phone_copy` 和 not_proven 边界。
- 覆盖 elevator assisted delivery 的 `requesting_floor_help` 提示：`你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯,`。
- `safe_phone_copy` 文案中文优先，且明确 ACK 不是送达成功，prompt readiness 不是实际播放证明。
- 过滤敏感字段：token、Authorization、OSS AK/SK、root password、DB/queue URL、raw ROS topic、`/cmd_vel`、serial device、baudrate、WAVE ROVER 参数、local path、traceback、checksum、完整 artifact。
- 文档同步 `docs/product/mobile_user_flow.md` 和 `docs/interfaces/ros_contracts.md`。
- 代码新增或修改的技术注释必须使用中文，并保持注释比例满足项目规范。
- 不改 remote bridge 生产行为；不新增硬件参数；不触碰 OKR。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_static.py
git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_static.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py docs/product/mobile_user_flow.md docs/interfaces/ros_contracts.md sprints/2026.05.12_24-25_phone-voice-prompt-readiness-gate/tech-done.md
```

## Task B - Remote Bridge / Operator Compatibility Fence

Owner：`robot-software-engineer`

允许改动文件范围：

- `src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`
- `sprints/2026.05.12_24-25_phone-voice-prompt-readiness-gate/tech-done.md`

实现要求：

- 增加或调整最小兼容性围栏，确认新增 `voice_prompt_readiness` metadata 不污染 `trashbot.remote.v1` command/status/ack envelope。
- 确认 metadata-only blocked response 不触发 robot action、不 ACK、不推进或持久化 cursor。
- 确认 ACK 文案/字段仍不等于 delivery success，也不等于 voice prompt 已真实播放。
- 确认 diagnostics voice prompt readiness 不暴露 raw ROS topic、serial、baudrate、token、Authorization、OSS/DB/queue URL 或 local path。
- 如果无需生产代码改动，只新增/调整围栏测试和 docs；不改 production remote bridge 行为，除非测试暴露真实兼容性 bug 且在本范围内能修。
- 代码新增或修改的技术注释必须使用中文，并保持注释比例满足项目规范。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
git diff --check -- src/ros2_trashbot_behavior/test/test_remote_bridge.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md sprints/2026.05.12_24-25_phone-voice-prompt-readiness-gate/tech-done.md
```

## Product Closeout

Owner：`product-okr-owner`

允许改动文件范围：

- `OKR.md`
- `sprints/2026.05.12_24-25_phone-voice-prompt-readiness-gate/side2side_check.md`
- `sprints/2026.05.12_24-25_phone-voice-prompt-readiness-gate/final.md`

收口要求：

- 对照本 PRD 和 tech-plan 核查 Task A / Task B 证据。
- 确认 `docs/product/mobile_user_flow.md` 和 `docs/interfaces/ros_contracts.md` 已同步，且引用路径真实存在。
- 确认 O5 进度只按 `software_proof_docker_phone_voice_prompt_readiness_gate` 保守更新；不得声明真实喇叭/TTS、真实手机设备、production app、真实云/4G、OSS/CDN 实流量、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- 写入 `side2side_check.md` 和 `final.md`。
- 更新 automation memory，并在 durable work 完成后提交和推送。

验收命令：

```bash
git diff --check -- OKR.md sprints/2026.05.12_24-25_phone-voice-prompt-readiness-gate/side2side_check.md sprints/2026.05.12_24-25_phone-voice-prompt-readiness-gate/final.md
```

## 并行派发规则

Task A 与 Task B 文件范围局部耦合在 `docs/interfaces/ros_contracts.md`，implementation 阶段必须指定 `full-stack-software-engineer` 主责实现和接口文档更新；`robot-software-engineer` 只做 remote bridge/operator compatibility fence，并在必要时对同一接口文档补充不变性说明。若两个 worker 同时修改 `docs/interfaces/ros_contracts.md`，以 Task A 的 schema contract 为主，Task B 只追加兼容边界。

建议同一条消息里并行派发：

- `full-stack-software-engineer` 执行 Task A。
- `robot-software-engineer` 执行 Task B。

Product closeout 必须等待 Task A / Task B 返回实际改动和验证结果后执行。

## 本阶段验收

本阶段只创建 sprint 前三份文档，不创建 `tech-done.md`、`side2side_check.md` 或 `final.md`。

```bash
git diff --check -- sprints/2026.05.12_24-25_phone-voice-prompt-readiness-gate/pre_start.md sprints/2026.05.12_24-25_phone-voice-prompt-readiness-gate/prd.md sprints/2026.05.12_24-25_phone-voice-prompt-readiness-gate/tech-plan.md
```
