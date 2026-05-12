# Sprint 2026.05.12_24-25 Phone Voice Prompt Readiness Gate - Tech Done

## 状态

- 阶段：tech-done
- Evidence boundary：`software_proof_docker_phone_voice_prompt_readiness_gate`
- Task A Owner：`full-stack-software-engineer`
- Task B Owner：`robot-software-engineer`
- Product closeout：Task A 与 Task B 均完成，进入 side2side/final 收口。

## Task A - Full-Stack Voice Prompt Readiness

### 实际改动

- `operator_gateway_http.py`
  - 新增 `trashbot.voice_prompt_readiness.v1` summary builder。
  - `/api/status.voice_prompt_readiness`、`/api/status.phone_readiness.voice_prompt_readiness` 和 `/api/diagnostics.voice_prompt_readiness` 使用同一口径。
  - voice prompt summary 复用 `speaker_prompt`、`elevator_assist`、`phone_readiness.command_safety`、support handoff 和 ACK 语义。
  - `playback_ready=false`，明确本轮不是真实喇叭/TTS 播放证明。
  - 对 token、Authorization、OSS AK/SK、root password、DB/queue URL、raw ROS topic、`/cmd_vel`、serial、baudrate、WAVE ROVER、local path、traceback、checksum 和完整 artifact 做 phone-safe 过滤。
- `operator_gateway_static.py`
  - 新增 voice prompt readiness 首屏锚点，防止 fallback HTML 入口后续被误删。
- `test_operator_gateway_http.py`
  - 覆盖 `/api/status` 顶层、`phone_readiness` 嵌套和 `/api/diagnostics` 的 voice prompt readiness shape。
  - 覆盖 elevator `requesting_floor_help` 提示：`你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯,`。
  - 覆盖 ACK 不是送达成功、prompt readiness 不是实际播放证明、敏感字段过滤。
- `test_operator_gateway_static.py`
  - 覆盖 HTML 首屏和静态锚点包含 voice prompt readiness 区域。
- `docs/product/mobile_user_flow.md`
  - 增补 voice prompt readiness 用户流程、首屏显示、not_proven 和脱敏边界。
- `docs/interfaces/ros_contracts.md`
  - 增补 `trashbot.voice_prompt_readiness.v1` schema contract、字段语义、三处 API 暴露和 remote envelope 不变性边界。

### 用户旅程变化

- 手机首屏现在能直接看到当前应该朗读/播报的提示词、触发状态、是否需要人工帮助、是否具备播放证明，以及中文安全文案。
- 电梯协助场景进入 `requesting_floor_help` 时，用户能看到固定求助提示，而不是只看到散落的 `speaker_prompt` 字段。
- ACK 文案保持保守：只代表 accepted/processing evidence，不代表送达成功，也不代表提示已真实播放。

### 接口影响

- 新增兼容字段：
  - `/api/status.voice_prompt_readiness`
  - `/api/status.phone_readiness.voice_prompt_readiness`
  - `/api/diagnostics.voice_prompt_readiness`
- 新 schema：
  - `schema=trashbot.voice_prompt_readiness.v1`
  - `schema_version=1`
  - `evidence_boundary=software_proof_docker_phone_voice_prompt_readiness_gate`
- 旧客户端可忽略新增字段；本轮不修改 remote bridge 生产行为，不触碰 `trashbot.remote.v1` command/status/ack envelope。

### 验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py`
  - `Ran 50 tests in 21.150s`
  - `OK`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_static.py`
  - exit 0
- `git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_static.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py docs/product/mobile_user_flow.md docs/interfaces/ros_contracts.md sprints/2026.05.12_24-25_phone-voice-prompt-readiness-gate/tech-done.md`
  - exit 0

### 剩余风险

- 本轮仍不是真实喇叭/TTS 播放、真实手机设备浏览器、production app、真实云/4G、OSS/CDN 实流量、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达证明。

## Task B - Remote Bridge / Operator Compatibility Fence

### 实际改动

- `test_remote_bridge.py`
  - 新增 voice prompt readiness metadata 兼容性围栏，确认新增 metadata 不污染 `trashbot.remote.v1` command/status/ack envelope。
  - 覆盖 metadata-only blocked response 不触发 robot action、不 ACK、不推进或持久化 cursor。
  - 覆盖 ACK 仍只是 accepted/processing evidence，不等于 delivery success，也不等于 voice prompt 已真实播放。
- `test_operator_gateway_diagnostics.py`
  - 覆盖 `/api/diagnostics.voice_prompt_readiness` 脱敏边界。
  - 确认 diagnostics 不暴露 raw ROS topic、serial、baudrate、token、Authorization、OSS/DB/queue URL 或 local path。
- `docs/interfaces/ros_contracts.md`
  - 补齐 voice prompt readiness 与 remote envelope 不变性边界。
  - 明确读取 diagnostics 或 prompt readiness 不触发 robot action，不改变 `trashbot.remote.v1` command/status/ack 语义。

### 接口影响

- Task B 未改生产 `remote_bridge.py` 行为。
- `voice_prompt_readiness` 只作为 operator/status/diagnostics metadata 暴露；旧 remote command/status/ACK envelope 继续保持兼容。
- ACK 语义不升级：ACK 不是送达成功，也不是提示词真实播放成功。

### 验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - `Ran 82 tests in 20.943s`
  - `OK`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - exit 0
- `git diff --check -- src/ros2_trashbot_behavior/test/test_remote_bridge.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md sprints/2026.05.12_24-25_phone-voice-prompt-readiness-gate/tech-done.md`
  - exit 0

### 剩余风险

- 本轮仍不是真实喇叭/TTS 播放、真实手机设备浏览器、production app、真实云/4G、OSS/CDN 实流量、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达证明。
- 当前证据只证明 local/Docker prompt contract readiness、operator 首屏/API/diagnostics 同口径、remote envelope 不变性和 metadata-only blocked safety。

## Product 收口核对

- `docs/product/mobile_user_flow.md` 已同步 voice prompt readiness 用户流程、首屏显示、ACK 语义和 not_proven 边界。
- `docs/interfaces/ros_contracts.md` 已同步 `trashbot.voice_prompt_readiness.v1` schema、字段语义、三处 API 暴露和 remote envelope 不变性。
- Product closeout 后续只允许保守更新 O5 到约 52%，证据边界为 `software_proof_docker_phone_voice_prompt_readiness_gate`；O6 保持约 51%，O1/O2/O3/O4 不提升。
