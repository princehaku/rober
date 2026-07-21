# Pre Start：O6/O7 corrected Phase 0 bounded mission

## Sprint metadata

- `sprint_type: epic`
- 启动时间：`2026-07-21 10:50 CST (+0800)`
- 目标 Objective：O6 / O7（各约 `93%`）
- 主责：`robot-software-engineer`
- 冻结证据评审：`robot-algorithm-engineer`
- Product 收口：`product-okr-owner`
- 状态：`planning_ready_for_engineering_dispatch`

## 上轮事实与 anti-repeat

- O5 约 `85%`，但 production provider/runtime 同根因已消费 `2/2`，继续暂停，禁止再做 provider wrapper、preflight 或本地 receipt。
- `09-50_o6_o7_bounded_mission_attempt` 的唯一只读 Phase 0 因冻结探针错误 NO-GO：Upper 实际进程在 `8787`，探针却访问 `8000`；非登录 shell 未 source Humble；systemd unit inactive 被误当作进程不存在；Upper local/remote SHA mismatch 未按 current capability 解释。
- 上轮 blocker `phase0_frozen_probe_endpoint_ros_env_upper_sha_service_ownership_mismatch` 已消费 `1/2`，授权为 `unconsumed_phase0_no_go`。本轮直接修正这些探针，不新增 review/handoff/wrapper。
- 本轮若 corrected Phase 0 因同一根因再次失败，则计数达到 `2/2`；下一轮必须切换 Objective 或升级 CEO，禁止第三次消费。

## CEO 当前授权

CEO 在本轮自动化消息中明确：上位机 `ssh root@192.168.1.11 -p 37878`；小车运动已授权，物理位置受限，operator 看护，路线清空。

- 授权 ID：`ceo_20260721_1048_corrected_phase0_bounded_mission_v1`
- 只读 corrected Phase 0 NO-GO 不消费授权。
- corrected Phase 0 全绿后，第一条 pre-stop 发出即 `authorization_consumed=true`。
- 授权只覆盖一次 `pre-stop -> user action receipt -> NavigateToPose map(0.8,0.25,0) -> bounded evidence -> post-stop -> conditional cancel/cleanup`。
- 不含第二 goal、retry、`/initialpose`、manual、direct `/cmd_vel`、直接 UART、firmware、service stop/start/restart/kill/replace、远端 deploy/写文件或无人看护运动。

## 本轮核心抓手

在不改变当前 service/UART ownership 的前提下，冻结并执行一次 corrected Phase 0：显式 source ROS2 Humble 与 onboard workspace，探测实际 Upper `8787`，通过 PID/listener/health/capability/current-task 读回来判定 current-process compatibility，并以当前远端能力而不是 local SHA 相等作为执行准入。所有 current readiness 门全绿后才进入 exactly-once live action pipe。

## Owner 与停止条件

- Robot Software 单线负责实现、离线测试、corrected Phase 0、唯一 live pipe、cleanup 和 `tech-done.md`；不得并发派第二个 live owner。
- Algorithm 只能在 final manifest 冻结后只读评审，不得 SSH、ROS、API 或重新执行现场命令。
- Product 只在工程与评审完成后更新 `side2side_check.md`、`final.md`、`OKR.md` 和进度日志。
- Phase 0 任一 current gate 不绿即冻结 NO-GO，动作计数全部为 `0`；动作 pipe 开始后任一失败都禁止 retry，只做 post-stop、必要 cancel、cleanup 和证据冻结。
