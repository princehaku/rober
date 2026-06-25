# 2026-06-26 01:34 PC 行程失败 marker 显示原因

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏地图上的行程失败终点 marker 会显示短失败原因，例如 `行程未通过：规划失败`。
  - 常见后端英文原因会翻译成普通用户可判断的短词：规划失败、等待超时、被障碍挡住、控制失败、条件未通过、已中止或执行失败。
  - marker 的 `data-state` 仍保持 `行程未通过`，避免样式状态被长文案污染。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展失败响应缺 goal 坐标时的地图 marker 测试，覆盖 `规划失败` 文案和 aria。
- `docs/product/pc_tools_workstation.md`
  - 记录失败终点 marker 的 WYSIWYG 口径和安全边界。

## 验证结果

- 通过：`npm test -- -t "attempted visible route goal"`
  - `Test Files 1 passed | 1 skipped (2)`
  - `Tests 1 passed | 178 skipped (179)`
- 通过：`npm run lint`
- 通过：`npm run build`
  - `vite v7.3.3 building client environment for production`
  - `dist/assets/index-CuYznUWR.js 475.83 kB`
- 通过：`npm test`
  - `Test Files 2 passed (2)`
  - `Tests 179 passed (179)`
- 通过：`git diff --check`
  - 无输出，未发现空白或 diff 格式问题。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - `node ... TCP *:7001 (LISTEN)`

## 剩余风险

- 本轮只覆盖 PC 前端失败态展示和 mock 组件测试，不触发真实 Nav2 execute、manual、keyboard、delivery、stop 或 `/cmd_vel`。
- 真实现场仍需要在 `0.0.0.0:7001` 上跑一次失败/拒绝场景，确认上位机返回的失败原因能被正确翻译或保守显示为 `执行失败`。
