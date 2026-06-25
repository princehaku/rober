# 2026.06.26 07:05 PC delivery prefill camera stable gate

- sprint_type: micro
- status: done
- owner: User Touchpoint Full-Stack Engineer

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `canFillDeliveryVideoRefFromCameraProbe` 和 `canPrefillDeliveryMaterialRefs`。
  - 普通 `准备送达材料 / 补送达画面` 在实时画面打开/关闭 pending 时显示 `等待画面稳定` 并禁用。
  - `fillDeliveryVideoRefFromCameraProbe()` 与 `prefillDeliveryMaterialRefs()` 入口同步早退，避免画面未稳定时写入送达视频 ref。
  - 高级 `使用最近画面 ref` 也复用同一画面稳定 gate。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展实时画面关闭 pending 用例，覆盖送达材料按钮等待画面稳定、点击不触发 camera probe、不写送达视频 ref。
- `docs/product/pc_tools_workstation.md`
  - 同步记录送达材料预填的实时画面 WYSIWYG gate 行为边界。

## 验证结果

- `npm test -- -t "shows camera closing state while peer cleanup is still pending"`：通过，1 passed / 191 skipped。
- `npm run lint`：通过。
- `npm run build`：通过。
- `npm test`：通过，2 files / 192 tests passed。
- `git diff --check`：通过。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN || true`：确认 PC Node 仍监听 `*:7001`。

## 剩余风险

- 本轮只验证 PC 前端 mock 行为，不触发真实小车运动，不覆盖真车 HIL、Nav2 实车执行或 WAVE ROVER 串口反馈。
- 未修改 Clash、系统代理或端口策略；本轮仅确认现有 Node 服务仍在 `0.0.0.0:7001` 等效监听。
