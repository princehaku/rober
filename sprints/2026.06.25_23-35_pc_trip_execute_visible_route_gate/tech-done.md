# PC 图上路线执行 gate

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `执行图上路线` 按钮新增当前路线可见 gate。
  - 安全确认已勾但路线未画到地图时，执行按钮禁用并显示 `先刷新地图画面` 或 `先准备图上路线`。
  - 当前路线已画到地图时，执行按钮仍可用，文案保持 `执行图上路线`。
  - 本轮进度和验收卡点同步改为先刷新地图画面确认图上路线。
- `pc-tools/workstation/test/App.test.ts`
  - 更新旧测试：未显示地图路线时不能触发 Nav2 execute。
  - 增加正向断言：地图上已画出当前路线且安全确认已勾时，`执行图上路线` 可点击。
- `pc-tools/workstation/src/shared/robotDefaults.ts`
  - 抽出固定上位机默认地址 `http://192.168.1.11:8787`，供前端和 Node route 共用。
- `pc-tools/workstation/src/server/index.ts`
  - `GET /api/robot-control/summary` 缺少 `baseUrl` query 时默认读取固定小车地址；控制类代理仍保持显式 baseUrl gate。
- `pc-tools/workstation/test/catalog.test.ts`
  - 增加后端 summary 默认地址契约测试。
- `docs/product/pc_tools_workstation.md`
  - 记录执行按钮的 WYSIWYG gate、后端默认小车地址和安全边界。

## 验证结果

- `npm test -- -t "plain trip|prepared trip|Nav2 goal|no-motion route|allows plain trip|visible route"`：通过，2 files / 10 passed / 156 skipped。
- `npm test -- -t "no-motion route|prepared trip|visible route"`：通过，1 file / 3 passed / 163 skipped。
- `npm test -- -t "defaults Robot Control summary|plain trip|prepared trip|Nav2 goal|no-motion route|allows plain trip|visible route|shared safety|running lidar proof|radar start configuration"`：通过，2 files / 13 passed / 154 skipped。
- `npm run lint`：通过。
- `npm test`：通过，2 files / 167 passed。
- `npm run build`：通过，Vite production build 和 server TypeScript build 均完成。
- 7001 只读 summary：`source_base_url=http://192.168.1.11:8787`、`normalized_base_url=http://192.168.1.11:8787`、`console_status=loaded_fail_closed_summary`、`safe_to_control=false`、`keyboard_control_mode=bounded_repeating_manual_pulse`、`free_roam_autonomy=locked`、`path_preview_point_count=36`、`path_generated=true`、`path_generation_succeeded=true`。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：`node` 监听 `TCP *:7001`。

## 剩余风险

- 本轮没有触发真实 Nav2 execute、manual、keyboard pulse、delivery complete、stop、map start、radar start 或 `/cmd_vel`。
- 完整 Nav2 路线执行仍需要现场显式确认后，在地图路线已可见时点击执行并读取成功结果。
