# O7 Route Replay Trajectory Minimap

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`：在 Cloud Archive Tasks 的 route replay inspector / local route replay player 附近新增只读 `Route replay trajectory minimap`。前端只消费 `route_replay_inspector.sample_frames` 的有效数值型 `x_m/y_m`，忽略 `null`、非 number 和非 finite 值；用固定 `viewBox="0 0 100 100"` SVG 归一化轨迹，处理单点、水平线和垂直线，避免 NaN。当前 marker 绑定本地 `routeReplayCursor`，当前帧坐标无效时显示 unknown，不画误导 marker。面板显式展示 `trajectory_points`、`map_frame`、`current_marker`、`safe_to_control=false`、`playback_available=false`、`robot_control_executed=false`。
- `pc-tools/workstation/test/App.test.ts`：补充 O7 Previews UI 断言，覆盖 minimap 渲染、有效轨迹点状态、当前 marker 随本地 cursor 从 `frame_index=0` 切到 `frame_index=1`，并确认本地 cursor 切换不新增 API 调用。
- `docs/interfaces/o7_cloud_archive_task_api.md`、`docs/product/pc_tools_workstation.md`、`pc-tools/README.md`：同步说明 minimap 的 fixture-only 数据来源、SVG 归一化规则、blocked/unknown 条件和真实能力边界。

## 验证结果

- `cd pc-tools/workstation && npm run build`：通过。关键输出：`✓ 31 modules transformed.`、`✓ built in 2.25s`。
- `cd pc-tools/workstation && npm run test`：通过。关键输出：`Test Files  2 passed (2)`、`Tests  38 passed (38)`。
- `cd pc-tools/workstation && npm run lint`：通过，无 eslint 报错输出。
- `git diff --check -- pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/App.test.ts docs/interfaces/o7_cloud_archive_task_api.md docs/product/pc_tools_workstation.md pc-tools/README.md sprints/2026.05.27_33-34_o7-route-replay-trajectory-minimap/tech-done.md`：通过，无 whitespace/error 输出。

## 剩余风险

- 本轮只新增 PC-only 本地 fixture 的只读轨迹检查视图，不接真实地图、不接 O6 真实云 archive、不发送控制命令、不证明机器人已运动。
- O7 仍缺真实 RTC/视频、真实历史路线回放、真实标注提交、真实 ASR/TTS、真实手控/寻路、机器人 ACK 和硬件 HIL 证据。
