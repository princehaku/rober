# 雷达贴图刷新后地图延迟重读

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `refreshRadarProof({ mapPreviewAfter: true })` 改为 proof/status 刷新后调用专用 `refreshMapPreviewAfterRadarProof()`。
  - 当第一轮 map preview 仍是 stale/not_current 且原因指向 scan stale/refresh required 时，按 750ms、1500ms 最多两次重读固定 map preview，避免 proof 刚刷新成功但地图 artifact 慢半拍导致假失败。
  - 重试只读 map preview/radar status，不启动雷达 lifecycle、建图、Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 测试桩支持同一 endpoint 顺序返回多个 fixture。
  - 升级 stale 雷达贴图刷新用例，覆盖“第一次 map preview stale，延迟重读后 loaded”的 no-motion 时序。
- `docs/product/pc_tools_workstation.md`
  - 同步雷达贴图刷新后的地图延迟重读合同。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "no-motion map radar refresh action|direct map screen|map preview itself marks overlay not-current"`，3 tests passed，227 skipped。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`，6 tests passed。
- 通过：`git diff --check`。
- 现场 no-motion 读回：`POST /api/robot-control/radar/scan-proof/refresh` 返回 `latest_scan_proof_fresh=true`、`scan_once_observed=true`、`scan_hz_observed=true`、`raw_packet_once_observed=true`、`tf_observed=true`、`robot_control_executed=false`；随后 summary 读回地图雷达层恢复 `radar_overlay_status=loaded`、当前雷达点 34 个。

## 剩余风险

- 本轮只改 PC 端雷达贴图刷新后的只读 map preview 重读节奏，不执行真实 Nav2、manual、keyboard、free-roam、map start、delivery、stop 或 `/cmd_vel`。
- 如果雷达 lifecycle 未运行、定位缺失或 map preview 真实无法投影雷达点，延迟重读不会把状态伪造成 loaded，仍会保留 not_current/blocked。
- 相机首帧仍受当前 UVC/USB 传输问题影响，建图启动仍缺 `camera_first_frame`。
