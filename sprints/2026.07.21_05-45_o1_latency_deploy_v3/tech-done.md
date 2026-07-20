# O1 Latency Deployment v3 - Tech Done

## Sprint metadata

- `sprint_type: micro`
- Owner：`full-stack-software-engineer`
- 授权：`goal_20260721_latency_deploy_v3_exact_unit_bounded_migration`
- 状态：`blocked_before_ssh_due_frozen_input_hash_mismatch`
- 证据边界：`local_read_only_input_gate_only_no_remote_or_control_action`
- `fresh_nonzero_authorization=none`
- `zero_speed_request_count=0`
- `live_nonzero_request_count=0`
- `physical_latency_not_measured=true`
- `hil_pass=false`
- `safe_to_control=false`

## 实际改动

本轮只新增当前 sprint 的 `tech-done.md` 与 `artifacts/local_input_gate.json`。没有修改 worktree 产品源码、测试、
接口文档、OKR 或其它 sprint；没有 SSH、远端 staging、替换、service stop/restart、PC 7001 restart、zero/stop/nonzero
请求，也没有 commit、push、reset、checkout 或 stash。

## Vendor 与输入复核

按 `docs/vendor/VENDOR_INDEX.md` 复核了 WAVE ROVER 控制事实：UART 是 newline-delimited JSON，项目现场设备名必须
实机确认，`T=11` 为 direct PWM、`T=13` 为 ROS control、`T=130` 为 feedback request。本轮没有调用这些命令，
也没有把本地软件检查包装成 UART、ESP32、轮子或 HIL 证据。

冻结 Upper candidate_v3 与 manifest 通过：

- candidate SHA256：`ceaf8f610eb5c1e4d1666fd8c5bce375986f2d18625d8bc29ce98c163d6e08d4`，与授权值一致；
- manifest SHA256：`fe79f530ad1ce12b7a3c2a0f04a6e4d661d4d1cf7a65c25d46a3a7c4384897ee`；
- manifest JSON parse、AST/sentinel audit 与 candidate `py_compile` 通过。

## 本地硬停止

部署前 byte-for-byte gate 发现两个未经本授权接受的漂移：

1. bridge 冻结期望为 `ff7871ffceb907bda65f442ced079df782a850135c604b169b6aa8a7234c114f`，当前 worktree
   为 `4f369ef66793ac018eee3e0b7431c823f6a1e300fcb9c33e0e3abf9bc2ef08a2`；
2. 04-31 manifest 中 workstation `src/server/index.ts` 期望为
   `92956fc6a67b4a16072c6bf5e438d63552e49115269564f0e5383bfafd7af5db`，当前为
   `555080645216e69e4adb6bcc3b5474dff6752fa718b201a3a42ed58f8cf39dca`。

另两份 workstation 输入仍匹配：latency helper 为 `f082347d...`，Vue 为 `ba55ed08...`。7001 只读观察到旧 listener
PID `21549`，没有重启或替换。Bridge 当前文件 `py_compile` 通过，但“能编译”不能证明它等价于授权冻结的 `ff787...`。

按“任何不符立即停止”和“不得覆盖共享文件”，本轮在第一次 SSH 前硬停止。没有自行选择当前漂移版本，也没有从旧 remote
stage 猜测或恢复授权输入。由于没有产生远端或进程状态变更，`rollback_required=false`。

## 验证结果

- Candidate manifest JSON parse：PASS。
- Candidate AST allowed=actual、c8 sentinel=0：PASS（沿冻结 manifest 复核）。
- Candidate 与当前 bridge `py_compile`：PASS。
- 04-31 workstation 三文件 SHA 复核：2 匹配、1 不匹配。
- Bridge frozen SHA 复核：不匹配。
- 远端 pre/post safety manifest、backup/stage/replacement、旧版迁移、新版 graceful restart、PC build/load、唯一 zero sample
  均未进入，不能报告为 pass 或 fail。

## 现场动作计数与剩余风险

- `SSH=0`、`remote_stage=0`、`remote_replace=0`、`service_stop=0`、`service_restart=0`、
  `forced_exact_unit_sigkill=0`、`PC_restart=0`。
- `zero=0`、`stop=0`、`nonzero=0`、`direct_cmd_vel=0`、`direct_uart=0`、`Nav2/route=0`。
- 远端仍保持本轮开始前状态；本轮没有重新确认其 hash、静止 gate、PID 或 health，因此不沿用历史值冒充当前证据。
- 未获得 PC/Upper/bridge spans 或 network RTT envelope；未观察 physical wheel onset，未测 physical latency。
- 继续部署需要 CEO/主节点重新冻结 `4f369...` 与 `555080...`，或提供 byte-identical 的 `ff787...` 与 `92956...`
  作为明确输入；在此之前不应消费旧 Upper forced-migration 授权。

## Product closeout 与 late reconciliation

- `PRODUCT_CLOSEOUT=ACCEPT_LOCAL_INPUT_GATE_NO_MISSION_PROGRESS`
- Product 接受首次 SSH 前对 bridge/index 冻结 SHA 漂移的 hard stop；它防止把未经本授权接受的组合版本部署到现场，
  但没有产生 remote、restart、zero/nonzero/control、用户动作或 Mission artifact。
- 05-45 当时记录的 candidate manifest SHA `fe79...` 是历史输入，已被随后独立修复 incremental patch 标签并完成最终
  manifest 对齐的 v3 产物 supersede。最终 candidate 仍为 `ceaf8...`，最终 candidate manifest 为 `d31ca5...`，最终
  incremental patch 为 `c0a965...`；`artifacts/local_input_gate.json` 保持历史原样，不回填或改写。
- 证据边界保持 `local_read_only_input_gate_only_no_remote_or_control_action`：remote/restart/zero/nonzero/control=`0/0/0/0/0`，
  `physical_latency_not_measured=true`、`mission_objective_0_satisfied=false`、HIL/safe/route/delivery 均 false。
- O1 保持约 `95%` flat，KR `不归档`，历史区无新增；本 input gate 不计 Mission Objective 0 进展。
- 05-45 authorization 已封存且不得复用。下一入口必须在精确提交后重新读取并冻结 current bridge/index hashes，再连同
  exact unit、静止、唯一 owner、candidate_v3 与 rollback gate 申请新的独立部署授权。
