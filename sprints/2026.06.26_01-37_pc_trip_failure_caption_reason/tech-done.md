# 2026-06-26 01:37 PC 行程失败 caption 显示原因

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 地图 caption 的 `行程执行` 行在失败时复用短失败原因，显示为 `行程执行：未通过（规划失败）`。
  - 该原因与行程失败终点 marker 使用同一翻译函数，避免 marker 和 caption 口径不一致。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展失败响应缺 goal 坐标时的地图测试，覆盖 `plain-map-trip-execution-label` 的失败原因。
- `docs/product/pc_tools_workstation.md`
  - 记录失败 caption 的 WYSIWYG 口径和安全边界。

## 验证结果

- 通过：`npm test -- -t "attempted visible route goal"`
  - `Test Files 1 passed | 1 skipped (2)`
  - `Tests 1 passed | 178 skipped (179)`
- 通过：`npm run lint`
- 通过：`npm run build`
  - `vite v7.3.3 building client environment for production`
  - `dist/assets/index-DcZ2B4vt.js 475.94 kB`
- 通过：`npm test`
  - `Test Files 2 passed (2)`
  - `Tests 179 passed (179)`
- 通过：`git diff --check`
  - 无输出，未发现空白或 diff 格式问题。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - `node ... TCP *:7001 (LISTEN)`

## 剩余风险

- 本轮只覆盖 PC 前端 caption 和 mock 组件测试，不触发真实 Nav2 execute、manual、keyboard、delivery、stop 或 `/cmd_vel`。
- 真实现场仍需在 `0.0.0.0:7001` 上复核失败场景下 marker 与 caption 的失败原因是否都符合现场理解。
