# O1 Latency Deploy Retry v2 - Tech Done

## Sprint metadata

- `sprint_type: micro`
- Owner：`full-stack-software-engineer`
- Authorization：`goal_20260721_latency_deploy_retry_v2`
- 状态：`deployment_rolled_back_after_upper_restart_timeout`
- 证据边界：`verified_candidate_and_atomic_replacement_attempt_rolled_back_not_zero_speed_trace`
- `live_nonzero_request_count=0`
- `zero_speed_request_count=0`
- `physical_latency_not_measured=true`
- `hil_pass=false`
- `safe_to_control=false`

## 实际改动

当前 worktree 的产品源码、测试、OKR/progress、vendor、Nav2、其他 sprint 均未改动。本轮只新增：

- `artifacts/preflight_and_test_manifest.json`
- `artifacts/deployment_and_rollback_manifest.json`
- 本 `tech-done.md`

远端创建独立 backup 目录 `/root/rober/onboard/runtime/latency_deploy_retry_v2_20260721_0508/backup/`。Upper 与
bridge canonical source 曾以同目录 stage+atomic rename 替换为已验证 latency 版本；Upper restart 未完成后，两文件都从
backup 原子恢复为旧版本并重新启动旧服务。PC workstation API 未重启。

## 候选、测试与 alias 复核

- 复用上一 sprint candidate `adadb0...`，其 AST/sentinel audit 仍为 true；未重新手工修改候选。
- Bridge `ff787...`；workstation server/helper/Vue hashes 分别为 `92956...`、`f0823...`、`ba55e...`。
- Candidate/bridge py_compile PASS；bridge 31/31 PASS；workstation latency 3/3 PASS；workstation build PASS，只有既有
  large-chunk warning。
- Remote preflight 证明 build package 目录 realpath 指向 source package 目录；bridge build runtime 与 canonical source
  是同一 realpath、同 inode。v2 只备份和替换 canonical source，没有再建立 build 侧 temp/hardlink/backup。

## 部署前与替换证据

部署前 Upper/bridge/build hashes 为 `8c0f.../6e82.../6e82...`。Upper mode/owner 为 `0644 root:root`；bridge
为 `0644 uid=501:staff`。Nav2 false/stopped，T1001 L/R=0，最后 T11 L/R=0，1 pub/1 sub，串口仅 PID 3765。

独立 backup 的 hashes/mode/owner 与旧目标一致。同目录 stage 继承原 mode/owner，远端 py_compile/hash/Upper c8 sentinel
gate 通过。两个 canonical target 原子替换后 hashes 为 `adadb0.../ff787...`，build resolved hash 也为 `ff787...`，
source/build realpath 仍相等。

## 服务重启、失败定位与 rollback

Bridge 精确 systemd control-group restart 成功，从 wrapper/child `1218/3765` 切换到 `26582/27031`。随后 Upper
精确 `systemctl restart` 时，旧 PID 1221 长时间停在 `deactivating/stop-sigterm`，没有产生新 PID 或 post-restart
health。旧进程 journal 中可见既有 `rclpy ... ValueError: generator already executing` traceback；本轮没有据此猜测轮子或
运动，只把它记录为 Upper 无法正常 shutdown 的运行时上下文。

由于 Upper health gate 未形成，本轮立即停止部署链：未加载 PC，未进入 post-deploy readiness/prewarm，未发 sample。
精确终止本次 deployment orchestration PGID 26560 及其 `systemctl` PID 26588；未使用 broad kill。随后从独立 backup
恢复两个 canonical targets。Upper unit 仍卡 stop 时，只对该 unit main 使用 systemd-scoped SIGKILL，再重新 start；bridge
也以恢复后的旧代码精确 restart。

rollback 后：

- Upper/bridge/build hashes 恢复为 `8c0f.../6e82.../6e82...`，mode/owner 与旧目标一致；
- Upper PID 27616 active 且 health ready；bridge wrapper/child 27827/28276 active；
- Nav2 false/stopped，T1001 L/R=0，最后 T11 L/R=0，1 pub/1 sub，唯一串口 owner PID 28276；
- 本机 PC 仍为原进程链 21515→21548→21549，未加载新 build；目标旁临时名已清理。

## Zero sample、软件 span 与用户旅程

post-deploy gate 未通过，所以 zero sample、immediate stop 与 sample readback 均为 0 次。PC/network/Upper/bridge spans
均为 null；没有跨主机 monotonic 相减。`direction=forward` 的枚举请求也从未发出，因此不存在误发 nonzero 的可能。

用户旅程没有获得现场延迟改善；收益仅是确认 candidate、alias-safe replacement 本身可通过，剩余 blocker 已收敛到旧
Upper 进程的 shutdown 行为。不能把 bridge 新版短暂启动或 target replace ACK 解释为全链路部署成功。

## 剩余风险

- 当前现场仍运行旧 Upper/bridge/PC 版本，没有 latency trace 或 keep-alive 优化。
- 下一次若继续，必须先离线修复或验证 Upper shutdown：rclpy watchdog/request 并发不能让 systemd SIGTERM 卡死；应提供
  bounded shutdown test 和明确的 executor/context teardown，再申请新的独立部署授权。
- 没有 nonzero 请求，没有 physical wheel onset，没有 physical latency、HIL、safe-to-control、robot-control-executed 或
  delivery success 证据。

## Product 边界补记

Product 接受 alias-safe replacement、旧 Upper shutdown blocker 收敛与完整 rollback；拒绝把短暂运行的新 bridge、target
replace ACK 或 unit-scoped recovery 解释为新版本全链路部署。post-deploy health 未形成，zero/nonzero/control=`0/0/0`，
O1 不加分、KR 不归档。05-24 只在离线软件层修复该 blocker，真实 systemd SIGTERM 仍需新的独立部署授权验证。
