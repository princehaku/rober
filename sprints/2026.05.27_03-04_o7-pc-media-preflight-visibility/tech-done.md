# 2026.05.27 03-04 O7 PC Media Preflight Visibility

## sprint_type

micro

## 实际改动

- 扩展 `cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py::build_o7_operator_console_contract()`，新增 `board_media_preflight_required=true`、`board_media_preflight_schema=trashbot.o7_board_media_preflight.v1`、`board_media_preflight_state=blocked` 和静态 fail-closed `board_media_preflight_summary`。
- 扩展 `pc-tools/workstation/src/shared/contracts.ts`、`pc-tools/workstation/src/server/o7OperatorConsole.ts`，让 `GET /api/o7/operator-console` 默认返回 board media preflight blocked/not_proven 摘要。
- 更新 `pc-tools/workstation/src/components/O7OperatorConsolePanel.vue` 和 `pc-tools/workstation/src/styles.css`，在 O7 Console 中展示 Board media preflight 面板，包括 `safe_to_control=false`、`primary_actions_enabled=false`、`device_probe_attempted=false`、blocked reasons、not_proven 和 next evidence。
- 更新 `pc-tools/workstation/test/catalog.test.ts` 与 `pc-tools/workstation/test/App.test.ts`，覆盖 contract schema、页面可见性、禁用控制、无 `/cmd_vel`、无 `/dev/ttyUSB`、无 ready/control 或 success overclaim。
- 更新 `docs/interfaces/o7_realtime_operator_console.md` 和 `docs/product/pc_tools_workstation.md`，说明 PC O7 Console 现在能展示 board media preflight 缺口，但不能替代上车 smoke。

## 验证结果

- `cd pc-tools/workstation && npm run build`：通过。关键输出：`✓ 29 modules transformed.`、`✓ built in 2.05s`。
- `cd pc-tools/workstation && npm run test`：通过。关键输出：`Test Files  2 passed (2)`、`Tests  16 passed (16)`。
- `cd pc-tools/workstation && npm run lint`：通过，`eslint .` 无错误输出。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py`：通过，无错误输出。
- `git diff --check -- cloud-relay pc-tools docs/product/pc_tools_workstation.md docs/interfaces/o7_realtime_operator_console.md sprints/2026.05.27_03-04_o7-pc-media-preflight-visibility`：通过，无 whitespace 错误输出。

第一轮 `npm run test` 曾失败于 `App.test.ts` 文本断言：Vue test-utils 将 `dt/dd` 文本拼接为 `safe_to_controlfalse`，不是 `safe_to_control false`。已修正断言后重跑通过。

## 剩余风险

- 真实 board/cloud/PC media runtime 未证明。
- RTC/STUN/TURN、摄像头、音频、ASR/TTS 和 HIL 仍未证明。
- 当前 PC Console 只消费静态 fail-closed summary，不读取真实板端 JSON，不替代 Orange Pi 上车 media smoke。
