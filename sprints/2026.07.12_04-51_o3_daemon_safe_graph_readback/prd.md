# PRD - O3 Daemon-Safe Graph Readback

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`

## 用户价值和产品北极星

用户需要的不是新的 readback surface，而是能在真实板上继续推进现场诊断的下一条命令及其结果。产品北极星仍是普通手机用户一键发车完成固定路线送垃圾；本轮的产品任务是把 O3/O1 no-motion lane 从“daemon 可能有问题”推进到“daemon-safe graph readback 已复验，并明确下一跳”。

## 背景

上一轮 final 结论已经明确：

- `daemon_dds_split.primary_candidate=ros2_daemon_state_timeout`
- `daemon_status_timed_out_and_daemon_reset_not_confirmed`
- `ros2_topic_list_ok`
- `path_generation_attempted=false`
- `path_generated=false`
- `safe_to_control=false`

这意味着当前最有价值的动作不是回到 O5 support-only，也不是尝试 motion/path，而是先把 daemon-safe stop/start + 8s graph readback 做成 same-run 可复验 artifact，确认 graph 层是否恢复，或者把 blocker 继续缩窄。

## 问题定义

当前缺的不是“有没有更多摘要”，而是：

1. daemon-safe stop/start 后，`ros2 daemon status`、`ros2 node list`、`ros2 topic list` 在 8s budget 内的真实结果；
2. graph readback 后，managed lifecycle / localization 是否进入下一跳；
3. 若仍失败，失败点是否已经足够支撑下一轮继续收敛，而不是重复消费同一 blocker。

## 本轮不做什么

- 不做 O5 support-only/readback/wrapper/probe-only 计分工作。
- 不改 `OKR.md`、`docs/process/okr_progress_log.md` 或历史 sprint 文档。
- 不做 motion/path，不发送 `/cmd_vel`、不调用 `/api/base/manual`、不尝试 NavigateToPose。
- 不把 graph 可读误判成 localization ready、path ready、safe-to-control 或 HIL pass。

## 成功标准

本轮计划阶段定义的成功标准如下：

1. Implementation owner 执行 daemon-safe stop/start + 8s graph readback，并把结果写入本 sprint artifact。
2. artifact 必须保留严格 no-motion false 字段，包括：
   - `path_generation_attempted=false`
   - `path_generated=false`
   - `safe_to_control=false`
   - `robot_control_executed=false`
   - `route_execution_success=false`
   - `delivery_success=false`
   - `hil_pass=false`
3. closeout 时，只有出现 same-run path generation、route execution、delivery/operator acceptance、HIL 或 production external evidence，才允许调整 OKR 百分比；否则继续不调整、不归档。

## 责任划分

- Product：定义用户价值、方向判断、验收口径和 closeout 边界。
- `robot-software-engineer`：实现 helper/readback/artifact/test/doc 同步，执行验证并记录结果。

## 验收口径

Product 接受本轮的前提：

1. sprint 文档清楚写出 O5 最低优先级不直接推进的原因；
2. tech-plan 明确了 implementation owner、工程文件范围、验收命令、no-motion 边界和 closeout 规则；
3. 后续执行如果未产生 mission-grade evidence，只能按 supporting diagnostic delta 收口。

## 需要同步的 sprint 文档

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续执行完成后，应继续补：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
