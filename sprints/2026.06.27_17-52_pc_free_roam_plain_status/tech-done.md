# PC 自由移动状态文案收口

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 将普通首屏自由移动/建图卡片里的 free-roam start、stop、失败、运行中状态文案改为跟随当前模式。
  - 当前是自由移动时显示“自由移动状态”，只有满足自动扫图/建图模式时才显示“扫图状态”。
  - 该改动只影响前端展示，不改变安全确认、停止兜底、free-roam start/stop 请求体或任何运动控制边界。
- `pc-tools/workstation/test/App.test.ts`
  - 精确锁定摄像头缺首帧但自由移动可启动的场景：启动后状态行必须显示“自由移动状态：自由移动状态机已启动...”。
- `docs/product/pc_tools_workstation.md`
  - 同步记录自由移动状态命名规则，明确不触发 free-roam、manual、keyboard、Nav2、delivery、stop 或 `/cmd_vel`。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run App.test.ts -t "allows low-speed free-roam recording while marking mapping degraded when camera has no first frame"`
  - 结果：`1 passed | 170 skipped`
- 通过：`cd pc-tools/workstation && npm test -- --run`
  - 结果：`2 passed` test files，`300 passed`
- 通过：`cd pc-tools/workstation && npm run build`
  - 结果：TypeScript 与 Vite build 通过；保留既有 chunk size warning。
- 通过：`cd pc-tools/workstation && npm run lint`
  - 结果：`eslint .` 通过。
- 通过：`git diff --check`

## 剩余风险

- 本轮不触发真实 free-roam start/stop，不验证小车实际运动；真实移动仍需现场在 PC 上勾选安全确认后人工点击启动。
- 当前 live 摄像头仍是 UVC 无首帧，不是页面独占；本轮不改硬件摄像头链路。
- Nav2 仍需用 ROS 模式重跑并证明执行窗口 wheel raw L/R 非零；本轮只修正自由移动普通状态文案。
