# O1 Latency Deployment v4 - Tech Done

## Sprint metadata

- `sprint_type: micro`
- Owner：`full-stack-software-engineer`
- 授权：`goal_20260721_latency_deploy_v4_exact_frozen_inputs`
- 状态：`deployment_aborted_and_complete_rollback_verified`
- 证据边界：`software_deploy_attempt_rolled_back_no_control_sample_no_physical_latency`
- `fresh_nonzero_authorization=none`
- `zero_speed_request_count=0`
- `live_nonzero_request_count=0`
- `physical_latency_not_measured=true`
- `hil_pass=false`
- `safe_to_control=false`

## 实际改动

本轮只新增当前 sprint 的两份 artifact 与本 `tech-done.md`。没有修改产品源码、测试、接口文档、OKR 或其它 sprint。
现场曾对两个精确 canonical 文件完成独立备份、同目录 stage 和原子替换；Upper 迁移遇到目标 systemd CLI 差异后立即
中止，随后从独立备份原子恢复两个 canonical 文件并恢复旧服务。PC 7001 未重启，未发送 zero、stop 或 nonzero 请求。

## Vendor、冻结输入与测试

按 `docs/vendor/VENDOR_INDEX.md` 复核了 WAVE ROVER 控制事实：newline-delimited JSON，`T=11` 为 direct PWM，
`T=13` 为 ROS control，`T=130` 为 feedback request。本轮未直接写 UART、发布 `/cmd_vel` 或调用 Nav2/route。

部署前冻结输入全部 byte-for-byte 匹配：Upper candidate v3 `ceaf8f61...`、bridge `4f369ef6...`、workstation server
`55508064...`、latency helper `f082347d...`、Vue `ba55ed08...`。范围审计确认 bridge 只改 HTTP keep-alive、连接复用、
失败关闭且不重放命令和 timing/debug；workstation 只改 trace/hold 绑定、fail-closed 校验及本地 monotonic spans。未改
serial/PWM/speed mapping/default timeout/command mode/launch 参数，也未改 goal/Nav2/route/base URL/speed limit/safety
confirmation contract。

验证结果：

- Bridge 测试：`32 passed`（授权文本预估 31，实际 suite 为 32）。
- Workstation latency 测试：`3 passed`。
- Workstation keyboard/manual/stop/watchdog/latency 定向测试：`70 passed, 465 skipped`。
- Workstation 全量测试：`535 passed`。
- Workstation build、lint：PASS；仅有既存 Vite large-chunk warning。
- `git diff --check`：PASS；测试后 frozen hash/mtime 保持稳定。

完整冻结与测试清单见 `artifacts/freeze_and_test_manifest.json`。

## 现场部署尝试与硬停止

远端 preflight 通过：旧 Upper `8c0f6eeb...`、旧 bridge source/build alias `6e82e493...`，两服务 active，health
ready，最新 T1001 `L=0/R=0`、最后 bridge T11 `L=0/R=0`，`/cmd_vel` 为 1 publisher / 1 subscription，Nav2
lifecycle 未运行且无 Nav2 节点。Upper PID `27616`；bridge wrapper `27827`，串口 owner `28276`。

独立备份、同目录 stage、stage `py_compile`、权限 owner 核对与两个 canonical 原子替换均通过。Bridge 重启后 wrapper
PID `29917`、唯一串口 owner PID `30418`；`/cmd_vel` 仍为 1/1。旧 bridge 退出日志出现
`ExternalShutdownException` 与 duplicate `rclpy shutdown` warning，但新实例 active 且 owner gate 通过。

Upper 精确 unit 收到 stop 后，在 5 秒轮询窗口结束时仍为 `deactivating/stop-sigterm`、旧 PID 仍为 `27616`。预定命令
中的 `systemctl kill --kill-whom=all` 被目标 systemd 以 unsupported option 拒绝。这是未授权的现场变体，因此没有重试
部署；新版 Upper 未启动、graceful restart 未进入、PC 未 load、样本未发送。

## Rollback 验收

为释放已经卡在 stop 的旧 exact unit，只使用目标支持的等价精确命令
`systemctl kill --kill-who=all --signal=SIGKILL trashbot-upper-robot-api.service`；未使用 broad kill。确认 exact cgroup 无残留
后，从独立备份恢复两个 canonical 文件，并启动旧 Upper、重启旧 bridge。

最终只读核验：

- Upper hash `8c0f6eeb...`、mode/owner `644:0:0`，service active，MainPID/cgroup PID `30857`，health `ready`。
- Bridge source/build alias hash 均为 `6e82e493...`，两者同 realpath，mode/owner `644:501:50`；service active，wrapper
  PID `30869`，唯一串口 owner PID `31428`，两者都在 exact bridge cgroup。
- 最新 T1001 `L=0/R=0`，最后 bridge T11 `L=0/R=0`；Nav2 无节点；精确 `.v4.stage`/`.v4.rollback` 临时文件为空。
- `/cmd_vel` 最终为 0 publisher / 1 subscription。这是恢复后的旧 `8c0f...` Upper 冷启动行为：它只在 manual 请求时
  懒创建 publisher，不预热 rclpy。preflight 的 1 publisher 来自旧进程此前的懒初始化；为保持零动作边界，本轮没有发送
  请求强制恢复 1/1。
- 本地 7001 仍为 PID `21549`，未重启；所有本地冻结输入 hash 保持不变。

完整现场动作与 rollback 清单见 `artifacts/deployment_and_rollback_manifest.json`。

## 剩余风险与结论

- 部署没有完成，优化代码当前仍只在本地 worktree；现场已完整恢复旧版本。
- 本轮没有 PC/Upper/bridge spans、network RTT envelope 或 physical wheel onset，不能报告物理延迟改善。
- 目标 systemd 使用 `--kill-who` 而非 `--kill-whom`；下一次独立授权部署必须预先冻结目标兼容命令，并重新做全部静止、
  exact-unit、owner、hash 与 rollback gates，不得复用本轮授权。
- Bridge 退出期 `ExternalShutdownException`/duplicate shutdown warning 尚未造成恢复失败，但应作为后续独立软件清洁项处理，
  不能与现场延迟部署混在同一授权中。
- `zero=0`、`stop=0`、`nonzero=0`、`direct_cmd_vel=0`、`direct_uart=0`、`Nav2/route=0`。
- `robot_control_executed=false`、`hil_pass=false`、`safe_to_control=false`、`route_execution_success=false`、
  `delivery_success=false`；O1 不因本轮提升，KR 不归档。

## Product closeout

- `PRODUCT_CLOSEOUT=ACCEPT_DEPLOYMENT_ATTEMPT_COMPLETE_ROLLBACK_ONLY`
- Product 接受最终 inputs 冻结、旧版本静止/health preflight、两个 canonical replacement、bridge 新实例与唯一串口 owner，
  以及异常后 exact-unit 释放和旧 Upper/bridge 完整 rollback；拒绝把 target replacement 或 bridge 短暂新实例解释为
  全链部署、用户体验改善或 Mission 进展。
- 旧 Upper 仍卡 `deactivating/stop-sigterm`，预定 `--kill-whom=all` 被目标 systemd 拒绝；新版 Upper 未启动，PC 未重启，
  zero/stop/nonzero/control=`0/0/0/0`，Nav2/route=`0/0`。
- rollback 最终证据为旧 Upper `8c0f6eeb...`、旧 bridge source/build `6e82e493...`、两服务 active、Upper health
  `ready`、T1001 与最后 T11 均 `L=0/R=0`、临时文件为空。恢复后的 `/cmd_vel=0 publisher/1 subscription` 是旧 Upper
  冷启动懒创建行为，本轮没有发送请求去改变它。
- O1 保持约 `95%` flat，KR `不归档`，`mission_objective_0_satisfied=false`；physical latency、HIL、safe-to-control、
  route、delivery 均未证明。
- v4 authorization 已封存，不得复用。下一入口需要新的独立授权，并在执行前冻结目标 systemd 实际支持的 exact-unit
  命令、current hashes、静止/owner/health 与 rollback gate。bridge 退出期 warning 仅登记为后续软件清洁项，本轮不新开 sprint。
