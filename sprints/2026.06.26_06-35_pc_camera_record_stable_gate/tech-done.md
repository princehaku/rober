# PC Camera Record Stable Gate

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- status: done

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：新增 `canSubmitPlainVisualFromCamera`。实时画面打开/关闭 pending
  时，普通首屏 `用当前画面记录` 显示 `等待画面稳定` 并禁用。
- `submitPlainVisualMaterialFromCameraProbe()` 入口同步 fail-closed，避免 camera probe 样张在屏幕仍处于连接中/关闭中时被提交为
  当前画面记录。
- `pc-tools/workstation/test/App.test.ts`：扩展相机关闭 pending 回归测试，覆盖关闭中点击 `用当前画面记录` 不会发
  camera first-frame probe 或 operator report。
- `docs/product/pc_tools_workstation.md`：同步 2026-06-26 06:35 行为说明。

## 验证结果

- `npm test -- -t "shows camera closing state while peer cleanup is still pending"`：通过，1 passed / 190 skipped。
- `npm test -- -t "camera|画面|preview"`：通过，29 passed / 162 skipped。
- `npm run lint`：通过。
- `npm run build`：通过。
- `npm test`：通过，191 passed。
- `git diff --check`：通过。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：确认 `node` 监听 `*:7001`。

## 剩余风险

- 本轮只做 PC 前端 gate 和 mock/DOM 回归验证，没有触发真实上位机 camera probe、operator report、manual、Nav2、delivery、stop 或
  `/cmd_vel`；真实现场仍需在 `0.0.0.0:7001` 工作台确认。
