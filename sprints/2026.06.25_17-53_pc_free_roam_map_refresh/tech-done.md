# PC Free Roam Map Refresh

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏“扫地式建图”卡片新增 `刷新扫图画面` 按钮；只有地图记录已启动或本轮已保存后启用，点击只调用既有只读地图预览刷新。
- `pc-tools/workstation/test/App.test.ts`：补充默认禁用态和记录启动后的回归断言，证明点击 `刷新扫图画面` 只增加 `/api/robot-control/map/preview` 调用，不触发手控 manual。
- `docs/product/pc_tools_workstation.md`：同步记录扫图卡片内 WYSIWYG 刷新入口和只读边界。

## 验证结果

- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm test -- App.test.ts -t "keeps free-roam keyboard locked until map recording starts"`：通过，1 passed / 68 skipped。
- `cd pc-tools/workstation && npm test`：通过，160 tests。
- `cd pc-tools/workstation && npm run build`：通过。
- PC 7001 只读 summary smoke：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`，当前路线 proof 为 `path_generated=false`、`path_generation_succeeded=false`、`path_point_count=0`，`pose=null`；本轮没有调用 map preview 刷新、map start、manual、keyboard、Nav2、delivery 或 `/cmd_vel`。

## 剩余风险

- 本轮只把扫图卡片内的 WYSIWYG 地图刷新入口补齐；真实自由跑动建图仍需要现场 operator 勾选安全确认、启动地图记录后按住键盘低速移动并保存地图。
- 当前只读 smoke 仍显示 `pose=null` 且 Nav2 路线未生成，完整 Nav2 路线执行和地图坐标下的机器人位置证明仍未完成。
