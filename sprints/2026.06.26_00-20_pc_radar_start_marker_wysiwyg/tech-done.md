# PC 雷达启动 marker WYSIWYG

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `启动雷达` 返回 ok 后，地图雷达 marker 立即显示 `雷达已启动，位置未读到` 或 `雷达已启动，待刷新`。
  - 扫描范围 aria 同步说明“等待刷新确认”，避免把启动返回误读成实时雷达已验证。
  - 该显示仍只消费已有 lifecycle proxy 结果和 summary，不新增任何自动刷新或运动动作。
- `pc-tools/workstation/test/App.test.ts`
  - 增加断言：雷达启动 ok 后，地图 marker、data-state 和扫描范围 aria 必须照实显示“已启动，等待刷新确认”。
- `docs/product/pc_tools_workstation.md`
  - 记录雷达启动后的地图 marker WYSIWYG 口径和安全边界。

## 验证结果

- `npm test -- -t "radar start|radar marker|running lidar proof|radar freshness|radar local|map radar"`：通过，1 file / 4 passed / 163 skipped。
- `npm run lint`：通过。
- `npm test`：通过，2 files / 167 passed。
- `npm run build`：通过，Vite production build 和 server TypeScript build 均完成。
- 7001 只读 summary：`source_base_url=http://192.168.1.11:8787`、`normalized_base_url=http://192.168.1.11:8787`、`console_status=loaded_fail_closed_summary`、`safe_to_control=false`、`keyboard_control_mode=bounded_repeating_manual_pulse`、`free_roam_autonomy=locked`、`lidar_running=false`、`scan_preview_count=72`、`path_preview_point_count=36`、`path_generated=true`、`path_generation_succeeded=true`。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：`node` 监听 `TCP *:7001`。

## 剩余风险

- 本轮没有触发真实 manual、keyboard pulse、Nav2 execute、delivery complete、stop、map start 或 `/cmd_vel`。
- 点击 `启动雷达` 本身是传感器 lifecycle 动作；地图 marker 只表示 proxy 已返回 ok，仍必须点击 `刷新雷达` 读取实时 proof 才能证明雷达窗口可用。
