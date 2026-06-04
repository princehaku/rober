# Pre Start: Runtime Material Runtime Hooks

## sprint_type

sprint_type: epic

## 上轮状态

上一轮 `sprints/2026.06.04_20-21_runtime-material-followup/` 已形成完整 owner notes，但尚未提交到 git。本轮在该工作树基础上继续推进，不回滚 20-21 的未提交代码和文档。

## 本轮目标

继续 O2/O3/O7/O1 runtime-material 主线，但优先处理能让功能往前走的 O3/O7 runtime hook：

- O3/O7：把 8787 从只能回放旧 scan proof，推进到可以通过只读 HTTP 入口刷新 LiDAR/ROS2 scan proof artifact。
- O7：PC workstation 接上该只读 refresh 工作流，让 operator 能触发并看懂 fresh/stale/blocker 边界。
- O1：硬件侧复核该链路不触碰底盘运动、不混淆 `T=1001`、ACK 与 HIL。

## Owner

- Robot Software Engineer：上位机 8787 read-only scan proof refresh 入口、测试、部署/验证尝试。
- User Touchpoint Full-Stack Engineer：PC direct-upper refresh 代理、UI 状态和用户可读失败边界。
- Hardware Infra Engineer：vendor-sourced 安全边界、fresh/stale feedback 口径和 HIL 禁区复核。
- Product Manager / OKR Owner：IC 返回后收口 OKR、证据类型和剩余 blocker。

## 验收口径

- 允许：读取 8787 `/health`、`/api/status`、`/api/radar/status`、`/api/radar/scan-proof/latest`，运行只读 scan proof collector。
- 禁止：`/api/base/manual`、`/cmd_vel`、`T=1/T=13/T=131`、底盘 pulse、HIL、任何运动命令。
- 若上位机无法部署或 runtime 无 ROS2 topic，必须形成明确 blocker，不得把 software guard 写成 O3/O7 涨分材料。

## 重复 blocker scan

- 17-18：O3 blocked 在上位机无应用 ROS graph；O2 blocked 在无真实电梯图片。
- 20-21：O3 进一步收敛为 live hooks `dry_run_stub/no_command_configured`，且 scan proof collector 修复未同步到上位机。
- 本轮只处理 O3/O7 hook/refresh 这一条，不重复 O2 找图和 O5/O6 collector 配置 blocker。
