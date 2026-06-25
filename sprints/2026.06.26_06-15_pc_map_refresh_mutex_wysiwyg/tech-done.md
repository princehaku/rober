# PC Map Refresh Mutex WYSIWYG

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- status: done

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：新增 `canRefreshMapProof`、`canRefreshMapPreview`、
  `mapProofRefreshButtonLabel` 和 `mapPreviewRefreshButtonLabel`，让普通首屏 `刷新地图` 与 `刷新地图画面` 在任一地图刷新
  pending 时都显示 `等待地图刷新` 并禁用。
- `refreshMapProof()` 与 `refreshMapPreview()` 入口同步 fail-closed，防止绕过按钮后仍并发刷新 map proof/preview。
- `刷新扫图画面` 复用同一 map preview gate；proof 刷新成功后的自动 preview 刷新仍在 pending 释放后继续执行。
- `pc-tools/workstation/test/App.test.ts`：扩展可见路线地图刷新回归测试，覆盖 map preview pending 时不能再发 map proof，
  以及 map proof pending 时不能再发 map preview。
- `docs/product/pc_tools_workstation.md`：同步 2026-06-26 06:15 行为说明。

## 验证结果

- `npm test -- -t "blocks visible-route execution while the map preview is refreshing"`：通过，1 passed / 190 skipped。
- `npm test -- -t "free roam|扫图|map refresh|map proof"`：通过，2 passed / 189 skipped。
- `npm run lint`：通过。
- `npm run build`：通过。
- `npm test`：通过，191 passed。
- `git diff --check`：通过。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：确认 `node` 监听 `*:7001`。

## 剩余风险

- 本轮只做 PC 前端互斥 gate 和 mock/DOM 回归验证，没有触发真实上位机地图、Nav2、manual、keyboard、delivery、stop 或
  `/cmd_vel`；真实现场仍需在 `0.0.0.0:7001` 工作台确认。
