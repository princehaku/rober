# PC Nav2 服务启动/恢复 Pending 所见即所得

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 自动驾驶服务启动/恢复请求未返回时，普通首屏 `当前事实` 明确显示“正在启动/恢复自动驾驶服务，不会发车；返回前不把旧服务状态当作已恢复”。
  - 行程卡摘要、行程状态和执行按钮 pending 文案按本次请求模式区分“启动服务中 / 恢复服务中”。
- `pc-tools/workstation/test/App.test.ts`
  - 增加延迟 `/api/robot-control/nav2/start` 回归，覆盖 pending 阶段只显示启动中，不提前调用 Nav2 proof refresh、Nav2 goal execute、manual 或 `/cmd_vel`。
- `pc-tools/README.md`、`docs/product/pc_free_roam_mapping_design.md`
  - 同步记录自动驾驶服务 lifecycle pending 的 WYSIWYG 行为和安全边界。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "Nav2"`：通过，25 个相关用例通过。
- `cd pc-tools/workstation && npm test -- --run`：通过，2 个文件，357 个用例通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍提示单 chunk 大于 500 kB，这是既有体积提示，不影响构建。
- `git diff --check`：通过。

## 剩余风险

- 本轮未连接真实上车机，也未发送真实 Nav2 goal、manual、free-roam、delivery、stop 或 `/cmd_vel`；验证范围是 PC 前端 mock 回归、静态检查和生产构建。
- 该改动只解决 PC 首屏对 Nav2 lifecycle pending 的所见即所得展示；真实自动驾驶能否行驶仍依赖上车端 Nav2 服务、地图、定位、路线和底盘反馈闭环。
