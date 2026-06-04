# PRD: Runtime Material Runtime Hooks

## 背景

当前 O3/O7 的主要问题不是缺更多 UI 或 runbook，而是 operator 无法通过 8787/PC 触发 fresh ROS2 runtime material 采集。上一轮只有旧 scan proof artifact，live hook 仍是 `dry_run_stub/no_command_configured`。

## 用户价值

现场 operator 不应靠 SSH 手工拼命令判断雷达/ROS2 是否真的有 `/scan`。PC 工作站应该能触发一个明确的只读 proof refresh，并把结果展示为 fresh material、blocked root cause 或 stale artifact。

## 需求

1. 上位机提供只读 LiDAR/ROS2 scan proof refresh 入口。
2. PC direct-upper 能代理该入口，并展示 refresh 结果、artifact freshness 和 not_proven 边界。
3. 硬件文档明确该链路不等于底盘 ACK、HIL、`safe_to_control=true` 或 Nav2 可用。
4. Sprint 留档必须按 evidence type 区分 `robot_runtime_material`、`blocked_with_root_cause` 和 `software_guard`。

## 非目标

- 不启动底盘运动。
- 不执行 PC WASD 或 stop-first pulse。
- 不把旧 artifact 或 dry-run stub 写成 O3/O7 完成。
- 不继续 O5/O6 production URL/token blocker。

## 验收

- 代码和 PC UI/API 测试通过。
- 至少完成一次上位机 8787 非运动验证，或写清为什么无法部署/刷新。
- 产出 owner notes，并在 final 中明确 OKR 是否涨分。
