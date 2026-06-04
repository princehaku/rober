# Pre Start: O9 PC + SLAM Runtime Epic

## sprint_type

sprint_type: epic

## 启动时间

2026-06-05 06:04 CST

## 用户价值和北极星

本轮继续服务 O9：让普通用户未来能把垃圾交给小车后，小车靠可验证的雷达、建图和 PC 运营证据安全送达，而不是停在接口/readback 文字状态。

## O9 最低优先级核对

- 当前 `OKR.md` 4.1 完成度最低 Objective：O9，约 18%。
- 本 sprint 是否针对最低 Objective：是，直接推进 O9 的 PC 同源 fresh proof 展示与 SLAM `/map` / continuous radar runtime root cause。
- 方向判断：继续，不调整北极星；本轮只接受新 runtime evidence 或明确 root cause，不重复 05-06 状态/readback。

## 最近两轮 blocker 扫描

- `2026.06.05_04-05_okr-six-sprint-state-rewrite`：明确 02-03 只是 status/readback contract，下一轮不得继续 Micro-only 接口/readback。
- `2026.06.05_05-06_o9-narrow-runtime-material-epic`：PC 只完成最小护栏，缺 hz、TF、`runtime_summary_fallback`、continuous not_proven 全字段展示和 PC live smoke；Robot Software 关闭远端 restart/curl 缺口，但 continuous radar 仍 `scan_continuity_not_observed`，SLAM `/map` 仍缺 artifact / `runtime/map_lifecycle_latest.json`。

## 防重复规则

- 不再重复 curl latest proof 或 `/api/radar/status` 字段存在性证明。
- Full-stack 必须扩展 PC same-origin 消费与展示，并尽量跑 PC 本机 API live smoke 到 upper 8787。
- Robot Software 必须通过 SSH 推进 continuous radar 或 SLAM `/map` lifecycle，至少产出新的 map/radar runtime evidence 或明确 root cause。

## Owner

- Full-stack Software Engineer：PC same-origin fresh proof 全字段解析/展示与 live smoke。
- Robot Software Engineer：远端 upper 8787 / ROS2 SLAM `/map` / continuous radar runtime root cause。

## 禁区

- Product/主节点不改产品代码、不运行 SSH、不运行构建/测试。
- 本阶段不改 `OKR.md`；OKR 只在最终收口有证据后更新。
