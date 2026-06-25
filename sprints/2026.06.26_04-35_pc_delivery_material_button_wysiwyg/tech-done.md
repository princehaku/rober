# 2026-06-26 04:35 PC 送达材料按钮按缺口显示

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏送达材料按钮从固定 `准备送达材料` 改为按当前缺口显示：
    - 已有行程材料但缺画面时显示 `补送达画面`。
    - 视频和行程材料都已存在时显示 `重新准备材料`。
    - 默认仍显示 `准备送达材料`，pending 时显示 `准备中`。
  - 按钮动作不变，仍只读取最近 Nav2/latest、固定 camera first-frame probe 和 delivery latest，不提交送达确认。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 Nav2 执行后 route ref 自动预填测试，覆盖 `补送达画面`。
  - 扩展送达材料修复测试，覆盖材料齐全后的 `重新准备材料`。
- `docs/product/pc_tools_workstation.md`
  - 记录普通首屏送达材料按钮的 WYSIWYG 文案。

## 验证结果

- 通过：`npm test -- -t "syncs latest readbacks and pre-fills delivery route material after visible-route trip execution"`
  - `Test Files 1 passed | 1 skipped (2)`
  - `Tests 1 passed | 178 skipped (179)`
- 通过：`npm test -- -t "blocks final delivery when a restored draft route ref does not match the fresh Nav2 result"`
  - `Test Files 1 passed | 1 skipped (2)`
  - `Tests 1 passed | 178 skipped (179)`
- 通过：`npm run lint`
- 通过：`npm run build`
  - `vite v7.3.3 building client environment for production`
  - `dist/assets/index-CoCQFSH0.js 474.27 kB`
- 通过：`npm test`
  - `Test Files 2 passed (2)`
  - `Tests 179 passed (179)`
- 通过：`git diff --check`
  - 无输出，未发现空白或 diff 格式问题。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - `node ... TCP *:7001 (LISTEN)`

## 剩余风险

- 本轮只覆盖 PC 前端按钮文案和 mock 组件测试，不触发真实 camera probe、operator report、delivery complete、Nav2、manual、stop 或 `/cmd_vel`。
- 真实现场仍需在 `0.0.0.0:7001` 上完成一次 Nav2 到达和送达材料预填，确认按钮文案与实际缺口一致。
