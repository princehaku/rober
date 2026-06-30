# PC Live WYSIWYG Readback Gap Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `plain-live-closure-summary` 新增 `data-live-wysiwyg-readback-gap-surface-ids` 与 `data-live-wysiwyg-primary-readback-gap-surface-id`。
  - `plain-live-closure-wysiwyg-refresh` 同步暴露同一组 readback gap 字段。
  - readback gap 专门表示当前 WYSIWYG 缺口中哪些 surface 是上车读数 `fetch_failed`、`not_loaded` 或 `not_proven`，用于区分“页面没显示”和“上车读数没回来”。
- `pc-tools/workstation/test/App.test.ts`
  - 默认首屏测试锁定 camera readback gap。
  - 新增 camera/map/radar 三路读数不可用的 live WYSIWYG 场景，验证 gap 字段和 no-motion 刷新边界。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步 live WYSIWYG readback gap 合同。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default|exposes live WYSIWYG readback gaps|keeps live closure wheel rerun as a focus-only Nav2 action"`：通过，3 个目标测试通过。
- `npm test -- --run`：通过，2 个测试文件、399 个测试全部通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-Q7ojBxrt.js` 与 `dist/assets/index-BBcFFzNr.css`。
- `git diff --check`：通过。
- 7001 重启：旧 `node` PID `21307` 已停止，新监听进程为 `node` PID `33712`，地址 `TCP *:7001`。
- 只读 smoke：`GET http://127.0.0.1:7001/` 已引用新 bundle；bundle 内命中 readback gap 字段、missing surface 字段、live WYSIWYG refresh 按钮和 no-motion 边界字段；`GET /api/robot-control/summary` 返回当前 `live_status=needs_wysiwyg`、missing/readback gap 均为 `camera,map,radar_map_points`，本轮未发送任何 motion POST。

## 剩余风险

- 本轮只改 PC Web 显示和只读 DOM 合同；没有恢复真实 camera/radar/map 上车读数。
- 当前 live 现场仍是 `needs_wysiwyg`，readback gap 显示三路都未闭合，后续需要继续恢复上车 API/读数链路或执行只读刷新排查。
