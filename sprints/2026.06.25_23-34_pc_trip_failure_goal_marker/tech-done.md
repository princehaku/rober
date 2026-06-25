# PC 行程失败目标点保留

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 记录本次点击执行的图上路线终点。
  - Nav2 execute 响应失败或拒绝且缺少 `goal_x/goal_y` 时，地图使用本次尝试终点显示 `行程未通过`。
  - 该兜底只影响 PC 地图 marker，不改变 Nav2 execute gate、delivery、manual、keyboard、stop 或 `/cmd_vel` 行为。
- `pc-tools/workstation/test/App.test.ts`
  - 新增失败响应缺 goal 坐标时的地图 marker 测试，断言仍显示 `行程未通过` 且不调用 delivery/manual/`/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录失败目标点保留的 WYSIWYG 口径。

## 验证结果

- 通过：`npm test -- -t "attempted visible route goal"`（1 passed，173 skipped）
- 通过：`npm run lint`
- 通过：`npm test`（174 passed）
- 通过：`npm run build`
- 通过：`git diff --check`
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`（`node` 监听 `*:7001`，未使用 Clash 端口）

## 剩余风险

- 本轮仍是 PC/mock 层，没有执行真实 Nav2 route。
- 真实失败原因和坐标质量仍以真实上位机 execute/latest readback 为准；PC 兜底只保留本次点击的图上终点。
