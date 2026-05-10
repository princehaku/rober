# Sprint 2026.05.10 08-09 Pre Start

## 目标

推进 Objective 2 低完成度缺口：`use_saved_map=false` patrol 不再用模拟 learning drive 冒充成功，必须有学习阶段产出的 waypoint 证据后才进入巡逻。

## Owner

- Robot Platform Engineer：主责 `task_orchestrator` 行为闭环和 patrol action 结果。
- Autonomy Algorithm Engineer：补充学习阶段证据口径，确保与 `learn.launch.py` / waypoint 学习流程一致。

## 验收口径

- `use_saved_map=false` 且没有 waypoint 证据时，patrol action abort，不能递增 `learn_count` 或返回 success。
- `use_saved_map=false` 且存在有效 waypoint 文件时，patrol 可以继续访问文件内 waypoint，并把这次作为学习证据计数。
- 相关行为有回归测试，full smoke 作为护栏。

## 风险

- 本轮仍不启动真实 SLAM/Nav2/硬件，只把行为层从模拟成功改成证据门控。
- `Patrol.action` 当前没有 error_code/error_message 字段，失败原因主要通过日志和 abort 结果表达。
