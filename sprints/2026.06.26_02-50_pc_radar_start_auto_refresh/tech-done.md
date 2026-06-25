# PC 雷达启动后自动刷新地图 Marker

sprint_type: micro

## 目标

普通首屏点击“启动雷达”后，地图 marker 不能长期停在“雷达已启动，待刷新”。当上位机 lifecycle 明确返回 `ok=true`，PC 应自动做一次只读雷达 proof refresh，让地图尽快显示真实运行读回。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `startPlainRadarLifecycle()` 在 radar start 成功后自动调用 `refreshRadarProof()`。
  - 如果自动刷新后仍未读到 `雷达已运行`，焦点回到 `刷新雷达`；启动失败仍停在 `启动雷达`。
- `pc-tools/workstation/test/App.test.ts`
  - 更新普通雷达启动测试，模拟 start 成功后 summary 变成运行态。
  - 断言 PC 自动调用 radar proof refresh，地图 marker 更新为 `雷达已运行，位置未读到`。
  - 断言不发送 base manual。
- `docs/product/pc_tools_workstation.md`
  - 记录雷达 start 成功后自动只读刷新地图 marker 的 WYSIWYG 行为边界。

## 验证结果

- `npm test -- -t "auto-refreshes radar proof after plain radar start reports ok"`：通过，1 个定向用例通过。
- `npm run lint`：通过。
- `npm run build`：通过，Vite 生产构建完成。
- `npm test`：通过，2 个测试文件、178 个用例全部通过。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：确认 `node` 正在监听 `TCP *:7001`。

## 剩余风险

- 本轮是 PC 端 mock/单元验证；不等价于真实雷达 lifecycle、真实 scan 数据或真车 HIL。
