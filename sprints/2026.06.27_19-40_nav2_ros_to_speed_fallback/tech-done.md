# Nav2 ROS To Speed Fallback Micro Sprint

## sprint_type

micro

## 实际改动

- PC summary 在 Nav2 最近执行 `goal_succeeded`、已发非零底盘命令、但同窗口 `T1001 L/R=0/0` 时，会根据上一轮控制面选择下一次复验模式：
  - `pwm -> ros`：保留既有“旧 PWM 结果，等待 ROS 复验”策略。
  - `ros -> speed`：新增 vendor `T=1` 差速回退，避免 ROS/T=13 零轮速后无限重复 ROS。
- 普通 PC 首屏仍复用 `next_execution_base_command_mode` 作为实际 Nav2 execute 请求体里的 `base_command_mode`，所以显示 `用 SPEED 重跑图上路线` 时，后端请求也会发送 `base_command_mode=speed`。
- 更新 `docs/product/pc_free_roam_mapping_design.md`，记录该策略来自 `docs/vendor/VENDOR_INDEX.md` 的 WAVE ROVER `T=13` 未闭环时可回退 `T=1` 规则。

## 验证结果

- `curl http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 只读 live 复核：当前最新 Nav2 artifact 为旧 `pwm` 执行，action succeeded、非零底盘命令 49 条、反馈样本 239 条，但 wheel raw L/R 仍为 `0/0`；summary 下一步仍正确指向 `ros` 复验。
- `npm test -- --run test/catalog.test.ts`：131 tests passed。
- `npm test -- --run test/App.test.ts`：177 tests passed。
- `npm test -- --run`：308 tests passed。
- `npm run build`：通过；仅保留既有 Vite chunk >500 kB warning。
- `npm run lint`：通过。
- `git diff --check`：通过。

## 剩余风险

- 本轮没有触发 Nav2 execute、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`，因此只证明下一次显式确认后的复验模式选择更合理，还没有证明真车已完成路线。
- 若现场 `speed/T=1` 复验仍出现 wheel raw L/R=0/0，仍需要继续查 ESP32 固件模式、电机使能、供电、UART 实际命令日志和底盘反馈链路。
