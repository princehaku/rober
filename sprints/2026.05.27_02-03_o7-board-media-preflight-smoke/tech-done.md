# O7 Board Media Preflight Smoke Tech Done

## sprint_type: micro

## 实际改动

- 新增 `ros2_trashbot_behavior.operator_media_preflight`，输出
  `trashbot.o7_board_media_preflight.v1` fail-closed JSON summary。
- 扩展 `operator_realtime_status.build_o7_board_realtime_status()`，把
  `media_preflight` 嵌入上一轮 `o7_board_realtime_status`，并合并
  `not_proven` / `next_required_evidence`；外部 source 进入 realtime status
  前会递归 redacted unsafe 文本并降级 blocked。
- 扩展 `operator_gateway_http.status_payload()`，允许显式传入
  `o7_board_media_preflight` 来源，但仍保持 manual/nav control
  `enabled=false`、`safe_to_control=false`、`primary_actions_enabled=false`。
- 新增 focused tests 覆盖默认不碰设备、unsafe input redaction、缺失显式路径
  blocked、可选 shallow probe 不宣称 runtime pass、CLI JSON 稳定、gateway
  fail-closed 集成，以及恶意外部 `media_preflight` 不透传 `/cmd_vel`、
  `/dev/ttyUSB*` 或 credential marker。
- 新增 `docs/interfaces/o7_board_media_preflight.md`，并更新
  `docs/interfaces/o7_board_realtime_status.md`。

## 验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/*.py`
  - 结果：通过，无输出。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s onboard/src/ros2_trashbot_behavior/test -p '*media*preflight*.py'`
  - 结果：通过，关键输出 `Ran 9 tests in 0.242s` / `OK`。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s onboard/src/ros2_trashbot_behavior/test -p '*operator*gateway*.py'`
  - 结果：通过，关键输出 `Ran 394 tests in 120.461s` / `OK`。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m ros2_trashbot_behavior.operator_media_preflight`
  - 结果：通过，默认输出 `schema=trashbot.o7_board_media_preflight.v1`、
    `overall_state=blocked`、`safe_to_control=false`、
    `primary_actions_enabled=false`，并包含 `not_proven`。
- `git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces/o7_board_realtime_status.md docs/interfaces/o7_board_media_preflight.md sprints/2026.05.27_02-03_o7-board-media-preflight-smoke`
  - 结果：通过，无 whitespace error。

失败定位：

- 第一轮 `*media*preflight*.py` 曾失败：`/dev/ttyUSB0` 输入大小写归一后没有命中 unsafe marker，导致原始路径出现在 JSON 中。
- 已修复为小写 forbidden marker 匹配，并在 unsafe path summary 中只输出
  `redacted_unsafe_input`；重新验证通过。
- 主节点验收发现 `operator_realtime_status._normalize_media_preflight()` 对外部
  `media_preflight` 的 `path_checks`、`capabilities`、`blocked`、
  `not_proven` 和 `next_required_evidence` 存在直接透传风险。
- 已补递归 source sanitization：外部 `/cmd_vel`、`/dev/ttyUSB*`、
  Authorization/Bearer/token/secret/password 会被替换为
  `redacted_unsafe_input`，并追加
  `unsafe_media_preflight_source_redacted` blocked 信号；manual/nav control
  仍 fail-closed。

## 剩余风险

- 真实摄像头、麦克风、喇叭、ASR、TTS、CPU 编码、WebRTC、STUN/TURN、云端信令、
  上车 smoke 和 HIL 均未证明。
- 本轮只依据 `docs/vendor/VENDOR_INDEX.md` 与
  `docs/interfaces/o7_realtime_hardware_sources.md` 的边界建立软件 preflight
  contract，不能替代 Orange Pi Zero 3 + WAVE ROVER + 摄像头/音频设备实测。
- 未修改 OKR 百分比。
