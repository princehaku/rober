# O1 Upper Bounded Shutdown - Tech Done

## Sprint metadata

- `sprint_type: micro`
- Owner：`robot-software-engineer`
- 状态：`software_contract_verified_product_accepted_deployment_pending`
- proof boundary：`offline_bounded_shutdown_candidate_v3_software_proof_only`
- `zero_speed_request_count=0`
- `live_nonzero_request_count=0`
- `control_invocation_count=0`
- `physical_latency_not_measured=true`
- `hil_pass=false`
- `safe_to_control=false`

## 实际改动

- Upper 将 rclpy init/spin/publish/destroy/shutdown 串行到同一 owner 锁；SIGTERM/SIGINT 只唤醒 asyncio event，
  runner、watchdog、active-hold stop 与 ROS context 分层有界收口。
- shutdown 在第一次 `await` 前关闭 manual 准入；排队请求零 publish/零串口 fail-closed。
- watchdog 在进入 stop worker 前认领并冻结 hold，避免 runtime shutdown 重复补 stop；release、watchdog、runtime
  stop 共用独立 stop-owner 锁，不进入 nonzero keydown 热路径。
- rclpy teardown worker 退出但 destroy/shutdown 报错时返回 `shutdown_failed`、`shutdown_succeeded=false`，不再误报 clean。
- 同步更新 runtime contract；candidate_v2 保留为中间历史，最终部署输入为重新冻结的 candidate_v3 及其两级 patch/manifest。

## 验证结果

- `py_compile`：PASS。
- Current Upper 全量：`Ran 141 tests ... OK (skipped=1)`。
- shutdown/realtime_hold/watchdog/runner-cleanup targeted：`Ran 15 tests ... OK`。
- candidate_v2 同一 targeted：`Ran 15 tests ... OK`。
- candidate_v2 应用于冻结 85ba 后的原始回归：`Ran 119 tests ... OK (skipped=1)`。
- generator 第二次输出 candidate/two patches/manifest 全部 byte-identical。
- 85ba full patch 与 adadb0 incremental patch 均完成 dry-run/apply/reverse/rollback/reapply/hash 验证。
- candidate_v2 SHA：`cc9bd3218a474a56236e78704b0e47133455e878c484475a1bb178161639f855`。
- 85ba patch SHA：`bb9b486d8f239b63a924bf8cceacca025ea6d1bb1cc1fb02c561c5180363de4b`。
- adadb0 incremental patch SHA：`82784f44619b0ceb84ad84638372bafb490e3198393bb40d0a1313e3939e7579`。
- candidate incremental 新增非空行中文注释比例：`99/473=20.93%`，严格大于 `20%`。

## 失败定位与修复

1. 交接产物的 source/candidate/two-patch SHA 与 manifest 不一致，且目录残留 `__pycache__`；修复代码后从精确
   85ba + adadb0 基线重新生成并清理临时 bytecode。
2. 原 tests 未覆盖 signal 后排队 manual、watchdog to-thread stop 与 shutdown 重复 stop、release stop 未共享锁、
   teardown error 被误报 clean；补四类合同与回归后 full/targeted 全部通过。
3. 注释补强后的第一次重生成误用了仍处于 reapply 状态的临时 85ba worktree，manifest 自检返回
   `ast_and_sentinel_audit_pass=false`；删除并重建精确 85ba worktree后最终 manifest 恢复 true，失败产物已覆盖。

## 剩余风险

- 05-08 的旧 Upper `deactivating/stop-sigterm` blocker 只在新 candidate 的软件合同层修复；本轮没有部署、重启或
  Linux/systemd SIGTERM smoke，不能证明旧进程可自行退出，也不能证明首次迁移无需 exact-unit SIGKILL runbook。
- daemon worker 超时会允许进程退出，但真实 rclpy/native teardown、aiohttp cleanup、串口 stop 的现场耗时仍未知。
- 本轮未运行 SSH、curl、service restart、ROS publish、串口、zero/nonzero/manual/stop 或任何控制；05-08 没有 retry。
- 不证明 physical wheel onset、HIL、safe-to-control、route execution 或 delivery success。

## 协同与提交判断

Robot Software 同意该 software-only Micro 进入 Product closeout，并与已通过 owner 验收的精确 O1 文件统一提交；
任何部署或首次迁移仍需独立授权、精确 unit 边界和新的 no-retry 现场验证。

## Late-writer reconciliation

- 本节是追加式冻结，不修改以上 Robot Software owner 的实现、验证或风险记录；本次也没有覆盖产品源码、测试或接口文档。
- late writer 最终仅补充中文原因注释，AST 语义保持为已验收的 additive fixes：
  `shutdown_succeeded` clean gate、signal 后 manual 零执行拒绝、watchdog stop 预认领，以及 release/watchdog/runtime 共用 stop owner。
- 上述 `candidate_v2` 仅是中间历史，不是部署输入；`artifacts/candidate_v3/` 是本 sprint 唯一部署输入。
- current Upper source SHA256：`52c99ca3b63480e841884aed7fca5f0d0b8350a028b0186af86a264bb4f2c272`。
- current Upper test SHA256：`0e03348d5c2fa94a44bd354ae215940735b4e77aa1bfb27c2b2ba70b173b63d7`。
- candidate_v3 SHA256：`ceaf8f610eb5c1e4d1666fd8c5bce375986f2d18625d8bc29ce98c163d6e08d4`。
- 85ba -> candidate_v3 patch SHA256：`c2eb76596a75f232acdd0bbb542c283f7db253a66ee7c033b3476214038155c4`。
- adadb0 -> candidate_v3 incremental patch SHA256：`c0a965b4610047bb36eb756c68a07bdcd0911740c0ef6634a90274f0e173c021`。
- candidate_v3 generator SHA256：`fb1d3b250a61c595ce16d23b2562d48dbd2fd7ed695e6e230eeaa739f4bd9dea`。
- candidate_v3 manifest SHA256：`d31ca5eae51f70fe1b86d047f96aa679ce1005d18edd49f32b86b4389770ddbb`。
- candidate_v3 的 AST `allowed_changed_symbols` 与 `actual_changed_symbols` 完全相等，共 18 项；7 个 c8 sentinel 计数全部为零，`ast_and_sentinel_audit_pass=true`。
- candidate_v3 相对冻结 adadb0 latency-only 输入的新增非空行中文注释比例为 `99/466=21.24%`，严格大于 `20%`。
- 独立第二次生成的 candidate、85ba patch、incremental patch 与 manifest 全部 byte-identical。
- 85ba patch 完成 apply/reverse/reapply/hash 验证；reverse 后恢复 base SHA
  `8c0f6eebb786e1cd6b1cb5d17485e59972140bf76a94e7669773ef438228b4c3`，临时 worktree 最终保持 clean。
- 最终复验：current targeted `17/17`、current Upper full `141/141 (skipped=1)`、shared
  `337/337 (skipped=1)`、candidate_v3 targeted `17/17`、85ba original regression
  `119/119 (skipped=1)`；current、test、generator、candidate `py_compile` 均通过。
- 开始、生成、验证与结束时 source/test SHA 保持一致，没有再次发生产品文件漂移。
- 独立验收发现原 incremental patch 使用不同 before/after 文件标签，`git apply` 无法解析目标；generator 已改为
  两侧共同绑定 `onboard/scripts/upper_robot_api.py`，保留 adadb0 input SHA gate，修复后 dry-run/apply/reverse/reapply/hash 全通过。
- 顶层 `artifacts/verification_manifest.json` 已更新为 v3 最终事实；旧 v2 计数和 SHA 不再作为 machine-readable 当前值。
- 本次仍为纯离线软件证据：`SSH=0`、`deploy=0`、`service_restart=0`、`control=0`、
  `zero=0`、`nonzero=0`；`physical_latency_not_measured=true`、`hil_pass=false`、`safe_to_control=false`。

## Product closeout

- `PRODUCT_CLOSEOUT=ACCEPT_OFFLINE_BOUNDED_SHUTDOWN_CANDIDATE_V3_DEPLOYMENT_PENDING`
- 用户价值：关闭合同已从“旧 Upper 可能无限卡在 stop-sigterm”推进为可测试、可回滚、单 stop owner 的 bounded shutdown
  candidate；但用户仍没有获得已部署的低延迟控制或真实 wheel-onset 体验。
- OKR 方向：O1 保持约 `95%`，继续但受独立部署 gate 约束；O5 约 `85%` 且 provider/runtime blocker `2/2` 继续暂停；
  O6/O7 各约 `93%`。本轮纯离线软件证据不提升百分比。
- KR：没有完成、取消、替换或过期项，`不归档`，历史区无新增。Mission Objective 0 未满足。
- Product 只读核对最终 manifests 与留档，没有重跑工程测试、SSH、部署、restart、ROS、串口或 control。
- 接受证据：current targeted `17`、Upper full `141/1 skip`、shared `337/1 skip`、candidate_v3 targeted `17`、冻结
  85ba regression `119/1 skip`；source/candidate/base-patch/incremental-patch=`52c99.../ceaf8.../c2eb.../c0a965...`，
  AST/sentinel、可复现生成、两级 patch 可逆与中文注释 `99/466=21.24%` 均通过。
- 拒绝边界：`zero/nonzero/control=0/0/0`、`physical_latency_not_measured=true`、`hil_pass=false`、
  `safe_to_control=false`；不证明真实 SIGTERM、新 health、route、delivery 或 Mission success。
- 下一唯一入口：取得新独立部署授权，冻结 exact unit/current old hashes/静止/唯一 owner/rollback gate，只部署 candidate_v3；
  先验证正常 SIGTERM、旧进程退出和新 health，失败 no-retry/rollback。只有另获完整 physical-latency authorization 与外部
  observer 才可发送非零样本。
