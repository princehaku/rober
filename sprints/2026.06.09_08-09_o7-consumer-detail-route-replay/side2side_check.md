# O7 Consumer Detail Route Replay Side-by-Side Check

## 1. 对照结论

本轮目标是把 O7 route replay 从 fixture preview 主导改为 O6 consumer detail 主导。对照结果：已完成。

## 2. 需求对照

| PRD / Tech Plan 要求 | 当前实现 |
| --- | --- |
| route replay 主数据源切到 O6 consumer detail | `routeReplayFrames` 来自 `consumerTaskDetailResult.trajectory.sample_frames` |
| 支持逐帧检查 | Consumer player 支持 Play/Pause、Previous、Next、Reset、range cursor |
| 证据/事件/tunnel 摘要浏览 | UI 展示 events/evidence/labeling/inference/tunnel summary |
| fixture preview 只能是次路径 | 旧 player 拆为 `fixtureRouteReplay*`，与 consumer cursor 隔离 |
| local-only / fail-closed | browser-only cursor；缺 detail、unknown task、轨迹缺失、blocked 状态均关闸 |
| 不声明真实控制或真实运动 | UI 和文档固定 `safe_to_control=false`、`robot_control_executed=false` |

## 3. 验收证据

- `npm run build`：通过。
- `npm run test`：通过，`42 passed`。
- `npm run lint`：通过。
- `git diff --check`：通过。

## 4. 未提升的能力

本轮没有证明真实云归档、真实地图叠加、真实 ROS2 `/tf`、真实机器人运动、真实 production O6/O7、真实 route replay latency 或真实上车验收。
