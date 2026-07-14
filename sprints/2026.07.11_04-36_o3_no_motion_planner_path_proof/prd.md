# O3 No-Motion Planner Path Proof PRD

## 用户价值

在真实 production external evidence 不可得时，用户需要一个更接近现场、但仍然安全的验证抓手：确认真实上位机是否至少能在 no-motion 条件下生成 planner/path 相关证据，或者明确知道它卡在哪个分层 blocker。这样后续 O6/O7 才能消费新的真实材料，而不是继续围绕旧 packet、旧 readback 或 support-only gate 原地打转。

## 产品北极星

北极星不变：机器人最终要完成可复验的现场路线、垃圾收集与送达闭环。本轮只补其中最前面的“planner/path readiness”证据段，给后续 route execution、delivery result、operator confirmation 提供真实材料入口。

## OKR 映射和方向判断

- O5：当前最低，约 `~85%`，但继续 O5 readiness/support-only 不会获得新 external production evidence，方向判断为 **暂停本轮推进**。
- O3 现场验证 lane：本轮临时激活，方向判断为 **继续**，因为它是当前环境里最可能产出新真实材料的低风险入口。
- O6/O7：本轮不直接做 surface 开发，方向判断为 **等待消费新 O3 材料**。
- O1：当前 live HIL blocker 已连续被消费，不应在本轮再用 historical/support-only 变体重复包装。

## 范围

本轮只做 sprint 计划，计划中的执行范围限定为：

- 真实上位机 `HTTP/SSH` 的 no-motion planner/path proof 尝试
- `/api/nav2/proof/refresh` 只读或 refresh 型证明接口
- `ssh root@192.168.1.11 -p 37878` 的只读预检、proof 收集或 fail-closed 分层
- 本地 mock fallback

## 非目标

- 不承诺 `delivery_success=true`
- 不承诺 `safe_to_control=true`
- 不承诺 `hil_pass=true`
- 不承诺真实 fixed-route execution success
- 不触发 `/cmd_vel`
- 不调用 `/api/base/manual`
- 不执行 `NavigateToPose`
- 不声称 current live route execution success

## 计划产物

本轮执行后，允许出现的有效产物只有三类：

1. `no_motion_planner_path_ready_not_route_execution_proof` 类 ready/blocked 摘要；
2. API/SSH/ROS2/topic/map/planner 分层失败证据；
3. 本地 mock fallback proof。

理想情况下，后续可供 O6/O7 消费的新真实材料应指向：

- `task_id`
- `map.yaml`
- `route.csv`
- keyframes
- planner/path summary
- replay JSONL 或等价 no-motion proof artifact

## 成功标准

- 计划明确指派 `robot-algorithm-engineer` 为主责。
- 计划写清真实路径与 fallback 路径的验收命令。
- 计划把接口边界、安全边界、失败分层和 proof boundary 写清。
- 整个计划中所有控制字段都保持保守预期：`safe_to_control=false`、`delivery_success=false`。
