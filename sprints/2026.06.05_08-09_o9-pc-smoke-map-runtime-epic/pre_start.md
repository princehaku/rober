# Pre Start: O9 PC Smoke + Map Runtime Epic

## sprint_type

sprint_type: epic

## 启动时间

- Automation ID: `daily-bug-scan`
- 当前时间：2026-06-05T08:06:30+08:00
- Sprint 目录：`sprints/2026.06.05_08-09_o9-pc-smoke-map-runtime-epic/`

## 本轮目标

本轮继续 O9，不再做 Micro-only status/readback。目标是让功能往前走，测试只作为护栏：

1. Full-stack 修 PC `npm run api` live smoke 启动问题，优先验证上一轮 root cause `tsx_ipc_pipe_enotsup` 是否可由 `TMPDIR=/tmp` 规避，并完成 `8788 -> 8787` same-origin scan-proof refresh curl 证据。
2. Robot Software + Algorithm 执行 no-motion LiDAR+SLAM `/map` lifecycle proof，目标是 `/map` once、map artifact、metadata、`runtime/map_lifecycle_latest.json` 和 `/api/map/proof/latest` readback。

## 上轮事实入口

上一轮 `sprints/2026.06.05_06-07_o9-pc-slam-runtime-epic/final.md` 已收口：

- PC API/UI/test/docs 已能表达 fresh proof 的 hz、TF、runtime fallback 和 continuous not_proven 边界。
- PC live smoke blocked at `tsx_ipc_pipe_enotsup`，导致 8788 API 未启动。
- 远端 SSH 发现 ROS graph 只有 `/parameter_events` 和 `/rosout`，没有常驻 `/scan`、`/map`、SLAM、Nav2；`/api/map/proof/latest` 404，map proof artifact missing。
- O9 仍是最低 Objective，约 18%；没有新增 field/HIL/continuous radar/SLAM map/user acceptance material。

## 最近两轮 blocker 防重复

| Sprint | blocker/root cause | 本轮防重复动作 |
| --- | --- | --- |
| `2026.06.05_05-06_o9-narrow-runtime-material-epic` | PC 只有最小 same-origin guard，缺 live API smoke；Robot 缺 continuous radar 和 SLAM `/map` artifact。 | 本轮不再只补字段；Full-stack 必须拿 8788 live curl，Robot/Algorithm 必须拿 `/map` lifecycle material 或更具体 root cause。 |
| `2026.06.05_06-07_o9-pc-slam-runtime-epic` | PC live smoke blocked at `tsx_ipc_pipe_enotsup`；远端无常驻 LiDAR/SLAM runtime，map artifact missing。 | 本轮直接验证 `TMPDIR=/tmp` 或替代启动方式，并直接执行 no-motion LiDAR+SLAM proof；失败必须给出新 root cause，而不是复述旧 blocker。 |

判断：尚未触发“同一根因第 3 轮重复消费”红线，因为本轮不是继续消费旧结论，而是针对两个已定位 root cause 执行修复/证明。

## Owner 与职责

| Owner | 主责目标 | 交付边界 |
| --- | --- | --- |
| Full-stack Software Engineer | 修 PC `npm run api` live smoke 启动，完成 8788 same-origin 调 8787 refresh/latest 证据。 | 只碰 PC workstation/API smoke 相关文件和必要 docs，不扩 UI 功能面。 |
| Robot Software Engineer | 远端 no-motion ROS2 runtime、upper API map proof 写入和 readback。 | 不发 `/cmd_vel`，不控制底盘，保持 `safe_to_control=false`。 |
| Robot Algorithm Engineer | SLAM `/map` lifecycle proof 的算法/SLAM 运行事实、map artifact 和 metadata 质量边界。 | 只做 no-motion 建图 proof，不宣称 AMCL/Nav2 可用。 |
| Product Manager / OKR Owner | 本阶段只产出计划和验收口径；收口时再更新 `OKR.md`。 | 不改产品代码、测试代码、硬件配置；本阶段不得上调完成度。 |

## 安全边界

- 必须保持 no base motion。
- 禁止发布 `/cmd_vel`。
- 所有 proof 必须保留 `safe_to_control=false`、`sends_base_motion_commands=false`、`robot_control_executed=false`。
- 本轮不做 PC WASD、WAVE ROVER ACK、HIL、低速 pulse、真实电梯图片采集或送达闭环。

## 启动结论

可以进入实现阶段，并且必须并行启动 Full-stack 与 Robot Software + Algorithm 两条真实功能抓手。任何失败都要产出 root cause、日志片段和下一步修复入口，不能把测试失败直接交差。
