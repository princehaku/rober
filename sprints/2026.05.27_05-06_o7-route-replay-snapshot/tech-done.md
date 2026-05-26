# O7 Route Replay Snapshot Micro Sprint

sprint_type: micro

## 实际改动

- 在 `cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py` 新增 `route_replay_snapshot` cloud-side fail-closed contract，固定 `source=software_proof`、`snapshot_status=blocked_not_proven`、`safe_to_control=false`、`primary_actions_enabled=false`、`playback_available=false`、`real_archive_connected=false`。
- 在 `pc-tools/workstation/src/shared/contracts.ts` 和 `pc-tools/workstation/src/server/o7OperatorConsole.ts` 增加 O7-KR3 route replay snapshot 类型与 PC API 响应，展示 task selector、selected task、trajectory、playback cursor、keyframe/evidence refs、state transition gaps 和 next required evidence。
- 在 `pc-tools/workstation/src/components/O7OperatorConsolePanel.vue` 增加 Route replay snapshot 面板，只读展示缺口，不提供播放器、选择器控制或任何机器人动作入口。
- 更新 `pc-tools/workstation/test/App.test.ts` 与 `pc-tools/workstation/test/catalog.test.ts`，覆盖 UI/API fail-closed 字段和禁止真实回放外推。
- 更新 `docs/interfaces/o7_realtime_operator_console.md` 与 `docs/product/pc_tools_workstation.md`，同步说明 O7-KR3 仍未接真实 O6 cloud archive / trajectory API。

## 验证结果

- 通过：`cd pc-tools/workstation && npm run build`
  - 关键日志：`vite v7.3.3 building client environment for production...`，`✓ built in 1.88s`
- 通过：`cd pc-tools/workstation && npm run test`
  - 关键日志：`Test Files  2 passed (2)`，`Tests  16 passed (16)`
- 通过：`cd pc-tools/workstation && npm run lint`
  - 关键日志：ESLint 无输出，退出码 0。
- 通过：`python3 -m py_compile cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py`
  - 关键日志：无输出，退出码 0。
- 通过：`git diff --check -- cloud-relay pc-tools docs/product/pc_tools_workstation.md docs/interfaces/o7_realtime_operator_console.md sprints/2026.05.27_05-06_o7-route-replay-snapshot`
  - 关键日志：无输出，退出码 0。

## 剩余风险

- 当前仅是 software proof contract 和 PC 展示，不连接真实 O6 cloud task archive，不证明真实任务列表、真实轨迹帧、真实关键帧截图、真实状态转移或真实历史回放。
- 本轮不修改 `OKR.md`，不提升 O7 百分比。
