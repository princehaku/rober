# PC 键盘连续 pulse DOM 合同

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 键盘面板新增连续验收 DOM 字段：
    - `data-current-hold-pulse-count`
    - `data-best-continuous-pulse-count`
    - `data-verified-min-forwarded-pulses`
    - `data-same-hold-window-required`
    - `data-stop-required-after-hold`
    - `data-stop-settled-after-pulse`
  - 四个屏幕方向键同步暴露当前按住 pulse 数、最佳连续 pulse 数、验收阈值、同一次按住窗口要求和松开后 stop 收口要求。
  - 行为逻辑未改变：启用键盘不发车，按住方向键/WASD 才按固定间隔发送短 pulse，松开/失焦/切页/移出/取消走固定 stop。
- `pc-tools/workstation/test/App.test.ts`
  - 默认首屏断言键盘连续验收阈值为 `2`，初始计数为 `0/2`，且要求同一次按住窗口和 stop 收口。
  - 按住态断言 pulse 计数从 `1/2` 到 `2/2`，并在松开后确认 `data-stop-settled-after-pulse=true`。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录 PC 键盘连续手控的结构化 DOM 合同和安全边界。

## 验证结果

- `npm test -- test/App.test.ts -t "keeps keyboard pulses continuous when summary refresh stalls during hold"`
  - 结果：通过，`Test Files 1 passed (1)`，`Tests 1 passed | 218 skipped (219)`。
- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`
  - 结果：通过，`Test Files 1 passed (1)`，`Tests 1 passed | 218 skipped (219)`。
- `npm run build`
  - 结果：通过，Vite 产物包含 `dist/assets/index-vcytDwrL.js`。
- `npm test -- --run`
  - 首轮结果：失败 1 项，原因是测试断言把松开后的 `data-current-hold-pulse-count` 错写成 `2`；实际松开后当前按住计数应回到 `0`，连续验证应看 `data-best-continuous-pulse-count=2` 和 `data-stop-settled-after-pulse=true`。
  - 修正后结果：通过，`Test Files 2 passed (2)`，`Tests 389 passed (389)`。
- `npm test -- test/App.test.ts -t "enables non-stop motion only after complete operator material and still uses the fixed workstation proxy"`
  - 结果：通过，覆盖上述断言修正。
- `git diff --check`
  - 结果：通过，无空白错误。
- PC Node 重启与 HTTP smoke
  - `npm run api -- --host 0.0.0.0 --port 7001` 已重新监听，`lsof` 显示 `node` 监听 `TCP *:7001`。
  - `GET http://127.0.0.1:7001/` 返回新 bundle：`index-vcytDwrL.js`。
  - JS bundle 已包含 `data-current-hold-pulse-count`、`data-best-continuous-pulse-count`、`data-verified-min-forwarded-pulses`、`data-same-hold-window-required`、`data-stop-required-after-hold` 和 `data-stop-settled-after-pulse`。

## 剩余风险

- 本轮只补 PC Web DOM 合同和测试，不自动启用键盘、不主动发送 manual/stop/Nav2/free-roam/delivery 或 `/cmd_vel`。
- 真实连续手控是否让车轮实际转动仍依赖上车 `/api/base/manual` 回包和同一次按住窗口内 wheel raw L/R 非零；PC 侧现在能把连续 pulse 计数和 stop 收口状态直接暴露给现场验收脚本。
