# PC Free Roam Coverage Guidance

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏“扫图覆盖”新增画面口径提示；未开始记录时说明当前是最近地图画面，记录中提示可边扫边刷新，保存后提示刷新检查覆盖效果。
- `pc-tools/workstation/test/App.test.ts`：补充默认态和地图记录启动后的扫图覆盖提示断言。
- `docs/product/pc_tools_workstation.md`：同步记录扫图覆盖提示的只读边界。

## 验证结果

- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm test -- App.test.ts -t "keeps free-roam keyboard locked until map recording starts"`：通过，1 passed / 68 skipped。
- `cd pc-tools/workstation && npm test`：通过，160 tests。
- `cd pc-tools/workstation && npm run build`：通过。
- PC 7001 只读 summary smoke：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`，`keyboard_control_mode=bounded_repeating_manual_pulse`，`free_roam_autonomy=locked`，当前路线 proof 为 `path_generated=false`、`path_generation_succeeded=false`、`path_point_count=0`，`pose=null`；本轮没有调用 map preview、map start、manual、keyboard、Nav2、delivery 或 `/cmd_vel`。

## 剩余风险

- 本轮只改善扫图覆盖状态解释；真实自由跑动建图仍需要现场 operator 启动地图记录、按住键盘低速移动、刷新画面并保存地图。
- 当前只读 smoke 仍显示 `free_roam_autonomy=locked`、`pose=null` 且 Nav2 路线未生成，完整自主扫图、完整 Nav2 路线执行和地图坐标下机器人位置仍未完成。
