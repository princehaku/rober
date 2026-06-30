# Live WYSIWYG Refresh Always Available Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `live_wysiwyg_needs_refresh` 改为由 `live_wysiwyg_missing_surface_ids.length > 0` 决定。
  - 即使主卡点是 `needs_wheel_rerun`，只要 camera/map/radar 当前所见缺口存在，summary API 也会声明可做只读 WYSIWYG 刷新。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 更新 API 断言：轮速复验状态下仍暴露 `live_wysiwyg_needs_refresh=true`。
- `pc-tools/workstation/test/App.test.ts`
  - 更新普通首屏断言：`needs_wheel_rerun` 时仍显示 `plain-live-closure-wysiwyg-refresh`，并验证点击只调用 radar proof refresh 与 camera first-frame probe，不执行 Nav2/manual/free-roam。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录 WYSIWYG refresh gate 新口径。

## 验证结果

- `npm test -- robotControlSummary.test.ts`：通过，1 个测试文件、3 个测试通过。
- `npm test -- App.test.ts`：通过，1 个测试文件、225 个测试通过。
- `npm test -- --run`：通过，3 个测试文件、402 个测试通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-DAuYzPy_.js` 与 `dist/assets/index-BCQK7HRw.css`。
- `git diff --check`：通过。
- 7001 重启：已停止旧 `node` PID `44418`，新监听进程为 `node` PID `55717`，地址 `TCP *:7001`。
- live 只读 smoke：`GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `status=needs_wheel_rerun`、`live_wysiwyg_missing_surface_ids=camera,radar_map_points`、`live_wysiwyg_needs_refresh=true`、`next_action_source_card_id=nav2_route`、固定 radar refresh 与 camera probe endpoint。本 smoke 未发送任何运动请求。

## 剩余风险

- 本轮只改变 no-motion 刷新入口可见性，不自动点击刷新、不启动雷达 lifecycle、不执行 Nav2、不发送 manual/keyboard/free-roam/stop 或 `/cmd_vel`。
- 真实 camera/radar WYSIWYG 仍需要现场用只读刷新和实屏观察验证。
