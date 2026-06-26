# PC 静止轮速 0/0 试动引导

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏不再把静止只读 T1001 的 `L/R=0/0` 直接当成轮速故障卡点。
  - 当 first-jog 已 ready 时，主进度按钮显示 `去低速试动`，轮速按钮保持可用并提示 `低速试动读非零 L/R`。
  - 只有 first-jog 运动窗口已经发出且回读仍为 `0/0` 时，才进入电机使能、供电、模式和现场空间排障卡点。
- `pc-tools/workstation/test/App.test.ts`
  - 更新普通首屏轮速进度测试，锁定“静止 0/0 -> 低速试动”而不是“静止 0/0 -> 先查卡点”。
- `docs/product/pc_tools_workstation.md`
  - 同步记录普通首屏轮速引导的新口径和接口边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation run test -- -t "shows current wheel L/R and frame count in plain goal progress from summary|refreshes plain goal progress with read-only endpoints only"`。
- 第一轮误用了 Vitest 不支持的 `--runInBand`，只得到 CLI 参数错误；已改用 Vitest 支持的 `-t` 过滤并通过。
- 通过：`npm --prefix pc-tools/workstation run test -- -t "shows raw wheel L/R from base feedback samples without treating T1001 count as nonzero proof|restores first-jog material from delivery latest draft refs when operator latest is missing|keeps static zero wheel readback as a trial prompt even when voltage is missing|keeps wheel trial blocked when motion was forwarded but L/R stayed zero"`。
- 通过：`npm --prefix pc-tools/workstation run test`，结果 `2 passed (2)`、`211 passed (211)`。
- 通过：`npm --prefix pc-tools/workstation run lint`。
- 通过：`npm --prefix pc-tools/workstation run build`；Vite 保留既有 chunk size warning。
- 通过：`git diff --check`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，`node` 监听 `TCP *:7001 (LISTEN)`。
- 本轮暂未触发真实运动、Nav2、delivery、keyboard pulse、base stop 或 `/cmd_vel`。

## 剩余风险

- 还需要继续推进真实 wheel raw L/R 非零材料；本轮只修正 PC 首屏在静止 0/0 时的下一步引导。
- Node 工作站仍要求使用本项目端口 `7001`；本轮未修改 Clash、系统代理或系统网络配置。
