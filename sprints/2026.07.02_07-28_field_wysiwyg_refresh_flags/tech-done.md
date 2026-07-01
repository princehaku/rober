# Field WYSIWYG Refresh Flags

sprint_type: micro

## 实际改动

- 补齐 PC `GET /api/robot-control/summary` 顶层现场验收 WYSIWYG 刷新能力标记，明确当前 refresh 序列是否刷新相机首帧、相机 MJPEG、雷达 scan proof、雷达状态和地图预览。
- 同步 TypeScript 合同、summary 单测和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `npm test -- --run robotControlSummary.test.ts App.test.ts catalog.test.ts`：通过，3 个测试文件、428 个测试通过。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 保留既有 large chunk 提醒。
- `git diff --check`：通过。
- 已重启 PC Node，`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` PID 30177 监听 `TCP *:7001`。
- 只读 smoke `GET http://127.0.0.1:7001/api/robot-control/summary`：当前 `field_acceptance_wysiwyg_refresh_mode=all_wysiwyg`，
  顶层相机首帧、相机 MJPEG、雷达 scan proof、雷达状态、地图预览刷新标记均为 `true`，且
  `field_acceptance_wysiwyg_refresh_sends_motion=false`、`field_acceptance_wysiwyg_refresh_starts_radar_lifecycle=false`、
  `field_acceptance_wysiwyg_refresh_starts_map_runtime=false`。
- `/map` HTTP smoke：`200 text/html; charset=utf-8`。

## 剩余风险

- 本轮没有新的现场安全确认，因此没有执行 Nav2、键盘 manual、free-roam、delivery complete、stop 或 `/cmd_vel`。
- 当前真实卡点仍是 motion 缺同窗口 wheel L/R 非零，WYSIWYG/建图缺相机首帧和当前雷达地图点；本轮只把现场验收刷新能力标记变成顶层可读合同。
