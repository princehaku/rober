# PRD：O5 SQLite shadow same-task gate

## 用户价值和产品北极星

产品北极星仍是普通手机用户可验证地完成垃圾送达。本轮不宣称送达成功；它减少 O5 控制面从本地 in-process smoke 走向 production-like store 的缺口，让 command/result/reconciliation 不只存在于一次进程内运行，而能跨 SQLite relay restart 被同一 `task_id` 消费。

## OKR 映射

- O5 / KR1：云中转 commands/status/ack/result 主链路继续使用 bearer-gated HTTP API 与 outbound polling 语义。
- O5 / KR6：将网络/存储故障边界继续 fail-closed，区分“本地 shadow store 可恢复”和“真实生产 DB/queue 未证明”。
- O6 / KR2/KR6：复用既有 archive/readback same-task gate，不新增 O6 完成度主张。

## 需求

1. smoke 支持 `--state-backend file|sqlite` 或等价入口，默认保持现有 file 行为兼容。
2. SQLite 模式必须使用同一 SQLite state path 重启 relay 后再读取 reconciliation。
3. summary 必须暴露 `relay_state_backend=sqlite`、`relay_restart_readback=true`、`sqlite_state_store_reopened=true`、`result_state=terminal_result_recorded`、`same_task_mission_gate_ready_not_success_proof`。
4. summary 必须固定 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`connects_cloud_production=false`。
5. 单元测试覆盖 file 兼容路径和 sqlite restart/readback 路径。
6. 文档同步说明该能力只是 production-like SQLite shadow proof，不等于 production DB/queue。

## 非目标

- 不连接真实公网、TLS、4G/SIM、production DB/queue、OSS/CDN。
- 不启动 ROS2、Nav2、WAVE ROVER、串口或 `/cmd_vel`。
- 不把 local SQLite store 说成 production cloud。

## 验收口径

验收以 worker 实际运行命令为准；最小通过标准是 py_compile、目标 unittest、relay unittest 和 scoped `git diff --check` 均通过。若验证失败，Robot Software owner 必须定位、修复并复验。
