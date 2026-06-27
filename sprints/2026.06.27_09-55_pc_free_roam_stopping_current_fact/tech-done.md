# PC 自由移动停止请求当前事实

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `当前事实` 的自由移动行新增 record-only `stopping` 分支。
  - 当上车 runtime 为 `artifact_only=true/cmd_vel_publish_enabled=false/state=stopping/reason=现场请求停止` 时，显示
    `自由移动：上次记录停在停止请求：现场请求停止；当前没有运动发布，可启动。`
  - 该行只读 summary，不启动或停止 free-roam，不发送 manual、keyboard、Nav2、delivery、stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 更新两处 live 形态断言，锁定自由移动 current facts 与 runtime 卡片/地图 marker 的 record-only stopping 口径一致。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 stopping 分支的 WYSIWYG 文案和安全边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- App.test.ts --testNamePattern "free-roam|自由移动|当前事实"`
  - `Test Files 1 passed`
  - `Tests 19 passed | 142 skipped`
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`
  - Vite 仍提示单 chunk 超过 500 kB，这是既有打包体积 warning，不影响本轮功能。
- 通过：`cd pc-tools/workstation && npm test`
  - `Test Files 2 passed`
  - `Tests 282 passed`
- 通过：`git diff --check`
- 通过：确认 `0.0.0.0:7001` 仍监听。
  - `node ... TCP *:7001 (LISTEN)`
- live 只读确认：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`
  - `free_roam_autonomy_runtime.status=loaded`
  - `free_roam_autonomy_runtime.state=stopping`
  - `free_roam_autonomy_runtime.reason=现场请求停止`
  - `free_roam_autonomy_runtime.artifact_only=true`
  - `free_roam_autonomy_runtime.cmd_vel_publish_enabled=false`
  - `readback_summary.free_roam.state_machine_observed=true`
  - `readback_summary.camera.status=source_first_frame_failed`

## 剩余风险

- 本轮只修 PC 首屏事实表达，不执行真实自由移动 start/stop。
- live 仍需要现场勾安全确认后才能实际启动自由移动；当前 camera 首帧仍失败，不能按可验收建图收口。
