# PC 自动扫图 runtime 地图标记

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 在普通首屏地图画面叠加只读 `自动扫图` runtime 标记，显示上车端状态机最近判断，例如避障换向、低速直行、找新覆盖。
  - 有机器人 map-frame 位姿时标记贴近小车；没有位姿时固定在地图角落，并通过 aria 明确“不代表坐标”。
  - 标记只读 `safe_command_boundary.free_roam_autonomy_runtime`，不启动自动扫图、不生成路线、不发送任何运动命令。
- `pc-tools/workstation/src/styles.css`
  - 新增 runtime marker 样式，并按 running/avoiding/turning/locked/stopping 区分颜色。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展首屏测试，验证地图上的自动扫图 runtime 标记、state 和 aria。
- `docs/product/pc_tools_workstation.md`、`docs/product/pc_free_roam_mapping_design.md`
  - 同步地图标记的 WYSIWYG 口径和安全边界。

## 验证结果

- 已通过：`npm test -- --testNamePattern "renders Robot Control V1|free roam|free-roam"`，`4 passed / 165 skipped`。
- 通过：`npm run lint`。
- 通过：`npm test`，`169 passed`。
- 通过：`npm run build`。
- 通过：`curl -s http://127.0.0.1:7001/api/robot-control/summary`，确认默认 `source_base_url=http://192.168.1.11:8787`、`safe_to_control=false`、`free_roam_autonomy=locked`、`free_roam_autonomy_runtime.cmd_vel_publish_enabled=false`。
- 待本轮收口继续执行：`git diff --check`。

## 剩余风险

- 本轮没有触发真实自动扫图、Nav2 execute、manual、keyboard pulse、delivery complete、stop 或 `/cmd_vel`。
- 地图标记只证明 PC 能把上车端 runtime 状态叠到地图画面；真车自由跑动建图仍需 HIL 验证后才能解锁运动发布。
