# O3/O1 Current Readiness + Bounded Route - Tech Done

## Sprint metadata

- `sprint_type: epic`
- Engineer owner：`robot-software-engineer`
- 状态：`phase_a_no_go_owned_cleanup_complete_offline_absolute_deadline_integrated`
- `authorization_ref=ceo_20260720_2025_operator_watch_route_clear_physical_limit_v1`
- `READINESS_GO=false`
- proof boundary：`current_strict_no_motion_partial_timeout_owned_cleanup_only`
- `physical_motion=false`
- `route_execution_success=false`
- `hil_pass=false`
- `delivery_success=false`
- `safe_to_control=false`

## 实际改动

本轮 live 窗口内没有修改产品代码、测试代码或业务文档，也没有利用同一授权重跑。live NO-GO 与 owned cleanup 完成后，Algorithm 离线确认 parent/helper monotonic clock origin mismatch，Robot Software 随后在禁止 SSH/live/control 的独立离线阶段修改 `onboard/scripts/upper_robot_api.py`、`onboard/tests/test_upper_robot_api.py` 与 `docs/navigation/field_route_evidence_preflight.md`，补齐 parent absolute-deadline producer、回归和合同说明。Algorithm 的 helper consumer、测试与 workflow 文档由 Algorithm owner 修改，Robot Software 只读消费，没有越权编辑。

实际新增文件均位于本 Epic：

- `artifacts/robot-software/frozen_identity.json`
- `artifacts/robot-software/frozen_requests.json`
- `artifacts/robot-software/phase0_deployment_manifest.json`
- `artifacts/robot-software/phase0_health.raw.json`
- `artifacts/robot-software/phase0_status.raw.json`
- `artifacts/robot-software/phase0_nav2_status.raw.json`
- `artifacts/robot-software/phase0_remote_sha.txt`
- `artifacts/robot-software/phase_a_nav2_start.raw.json`
- `artifacts/robot-software/phase_a_nav2_start.transport.json`
- `artifacts/robot-software/phase_a_nav2_proof_refresh.transport.json`
- `artifacts/robot-software/phase_a_nav2_proof_latest.raw.json`
- `artifacts/robot-software/phase_a_nav2_proof_latest.transport.json`
- `artifacts/robot-software/phase_a_nav2_status_after_proof.raw.json`
- `artifacts/robot-software/phase_a_nav2_status_after_proof.transport.json`
- `artifacts/robot-software/phase_a_status_after_proof.raw.json`
- `artifacts/robot-software/phase_a_status_after_proof.transport.json`
- `artifacts/robot-software/phase_a_nav2_owned_stop.raw.json`
- `artifacts/robot-software/phase_a_nav2_owned_stop.transport.json`
- `artifacts/robot-software/phase_a_nav2_status_after_stop.raw.json`
- `artifacts/robot-software/phase_a_nav2_status_after_stop.transport.json`
- `artifacts/robot-software/phase_a_owned_cleanup_residual.json`
- `artifacts/robot-software/phase_a_owned_cleanup_residual_final.json`
- `artifacts/robot-software/phase_a_invocation_manifest.json`
- `artifacts/robot-software/readiness_assertion.json`
- `artifacts/robot-software/structure_assertion.json`
- `artifacts/robot-software/local_verification.json`
- `artifacts/robot-software/deadline_integration.json`
- 本文件 `tech-done.md`

远端只部署了两份已经通过本地测试的脚本，没有直接编辑远端：

- `/root/rober/onboard/scripts/upper_robot_api.py`
- `/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py`

## Phase 0 与部署一致性

部署前后事实：

| 文件 | 本地 SHA256 | 远端部署前 SHA256 | 远端部署后 SHA256 |
|---|---|---|---|
| `upper_robot_api.py` | `df7a71c662a074c6e9eecb1523f7daf7ce78a33507193e3779192fc61a71461a` | `1503193fb05309c630448fa723ae90f4acd0f70d332e5673ab307e8b2c4836e1` | `df7a71c662a074c6e9eecb1523f7daf7ce78a33507193e3779192fc61a71461a` |
| `o10_amcl_nav2_runtime_proof.py` | `2ecdbb977ae1a211e4f6af3555d7f623f12f1bf2a161d10cf9443c3538af3fa2` | `4cad938e91cb3e19317ef0b9e058e24df7665268ad8fb6d00423d19980b15341` | `2ecdbb977ae1a211e4f6af3555d7f623f12f1bf2a161d10cf9443c3538af3fa2` |

远端临时文件与目标文件 `python3 -m py_compile` 均 exit `0`；`trashbot-upper-robot-api.service` 重启后 active，MainPID 从 `684106` 变为 `689027`。重启组合命令首个 health curl exit `7`，定位为服务在 systemd active 后约 4 秒才监听 8787；只读复核显示监听建立、journal 出现 `upper_robot_api_started`，随后 health HTTP `200`、JSON parse 成功。该失败不涉及代码修复或第二次 live 窗口。

Phase 0 最终状态：Upper API healthy，Nav2 owned lifecycle 初始 `stopped`，当前旧状态读回包含 `lidar_min_distance_m=0.03500000014901161`，不能作为 obstacle-clear 证据。

## Phase A live 结果

### 调用计数与传输结果

| endpoint | 方法 | count | exit | HTTP | parse | 语义 |
|---|---:|---:|---:|---:|---|---|
| `/api/nav2/start` | POST | `1` | `0` | `200` | true | `started_strict_no_motion` |
| `/api/nav2/proof/refresh` | POST | `1` | `0` | `200` | true | `blocked_with_root_cause` |
| `/api/nav2/proof/latest` | GET | `1` | `0` | `200` | true | `not_proven` |
| `/api/nav2/status` after proof | GET | `1` | `0` | `200` | true | lifecycle running before cleanup |
| `/api/status` after proof | GET | `1` | `0` | `200` | true | current unified readback |
| `/api/nav2/stop` | POST | `1` | `0` | `200` | true | `stopped_owned_process_group` |
| `/api/nav2/status` after stop | GET | `1` | `0` | `200` | true | lifecycle stopped |

Start 生效合同为 `strict_no_motion=true`、`base_enabled=false`、`lidar_enabled=false`、`reuse_existing_scan=true`；base UART 与 LiDAR serial new-open 都是 `0`。Start 自身没有发布 `/initialpose`、goal、manual、direct `/cmd_vel` 或 UART 指令。

Proof helper 运行 `80395ms` 后仍触发 Upper API `process_timeout_s=80` 的 `TimeoutExpired`。current artifact 只达到：

- `artifact_kind=partial`
- `final=false`
- `natural_completion=false`
- `last_phase=interrupted`
- `last_successful_phase=initialpose`
- `current_command=null`
- `partial_artifact_preserved=true`
- `initialpose_publish_attempts=0`
- path requested/attempted/succeeded/generated=`true/false/false/false`
- path point count=`0`
- planner/controller current active=`false/false`
- current AMCL pose、dynamic `map->odom`、`map->base_link`、persisted pose audit 均未证明

虽然 phase history 的 read-only lifecycle recovery 记录了 map/amcl preflight active，但 final artifact 不存在且 planner/controller/localization/path 均不绿；再叠加 current obstacle clear 未证明，因此严格裁决 `READINESS_GO=false`。

### NO-GO cleanup

NO-GO 后只调用一次 owned `/api/nav2/stop`：cleanup scope=`o11_owned_pid_process_group_only`，不调用 `/api/base/stop`，不访问 base UART。最终 readback 为 lifecycle `stopped`、PID `null`；owned PID file 不存在，lifecycle PID `689975` 与 helper process group PID `690233` 均不存在，严格前缀扫描 `residual_count=0`。

第一版通用 residual 扫描错误地把扫描器自己的命令行计为 `1`；定位后只收紧只读匹配前缀并复验，没有发第二次 stop。最终有效事实以 `phase_a_owned_cleanup_residual_final.json` 为准。

## Phase B 明确未进入

- `pre_base_stop=0`
- `goal_invocation=0`
- `post_base_stop=0`
- Phase B goal latest/feedback/status GET=`0/0/0`
- Phase B owned Nav2 stop=`0`
- `phase_b_invocation_manifest.json` absent
- `no_retry=true`
- `/initialpose`、manual、free-roam、direct `/cmd_vel`、UART、`T=1`、`T=11`、`T=13`、`T=1001`、delivery 全部 invocation=`0`
- `physical_motion=false`

因此本轮不证明 route execution、current HIL、delivery 或 safe-to-control：`route_execution_success=false`、`hil_pass=false`、`delivery_success=false`、`safe_to_control=false`。

## 验证结果

本地 pre-live 与 post-live 都执行了同一组合回归：

```text
python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py
exit 0

python3 -m unittest onboard/tests/test_upper_robot_api.py onboard/tests/test_nav2_runtime_proof_helper.py
Ran 285 tests in 2.715s
OK (skipped=1)
exit 0
```

首次 pre-live 组合单测同样为 `Ran 285 tests in 2.724s`、`OK (skipped=1)`。后续离线 deadline integration 的最终回归见下节；live 与离线两阶段的证据边界不混写。

JSON parse 与结构断言：

- `phase_a_invocation_manifest.json`：`python3 -m json.tool` exit `0`
- `readiness_assertion.json`：`python3 -m json.tool` exit `0`
- identity、`READINESS_GO`、start/proof/latest/stop、Phase B、forbidden invocation、no-retry 与 cleanup 结构断言 exit `0`，输出 `structure_assertion=ok`
- `phase_b_invocation_manifest.json` 明确 absent，且 manifest 中所有 Phase B count=`0`

## 失败定位、修复与复验

1. 部署重启首个 health curl exit `7`：根因是 systemd active 到 8787 listener ready 约有 4 秒启动差；随后 read-only status/journal/listener/health 复核 exit `0`。没有修改代码。
2. live proof NO-GO：根因是 helper 仍在板端慢 ROS CLI 路径耗尽 80s 外层预算，触发 `helper_process_timeout_after_partial_artifact` 与 `sigint_before_final_artifact`。依照 no-retry 合同不允许在本授权窗口修复后重跑，直接 fail closed 与 owned cleanup。
3. 第一版 residual 扫描 `count=1`：根因是扫描器命令行包含搜索 token，自匹配；收紧只读前缀后复验 `residual_count=0`，没有新增任何控制调用。

## Offline parent absolute-deadline integration

Algorithm 对 live timing 的离线复核固定了 `parent_elapsed_ms=80395`、
`helper_start_to_sigint_ms=76764` 与约 `3631ms` 的 parent startup gap；这段 gap 先前不在 helper 相对
deadline 内，却消费了 4 秒 final reserve。根因分类为
`parent_helper_monotonic_clock_origin_mismatch`。

Robot Software 完成以下 producer 集成：

- 在 helper argv 构造与 `Popen` 前使用同机 `time.monotonic()` 冻结 parent absolute deadline；
- 同时传递兼容 relative timeout 与 `--outer-process-deadline-monotonic-s`；
- `communicate()` 只取得 absolute deadline 的 remaining，不在进程创建后重置完整 80 秒；
- deadline 在 `Popen` 前耗尽时不创建子进程；在 `Popen` 后耗尽时沿用既有 owned process-group
  SIGINT/cleanup/fallback；
- 未传 absolute deadline 的旧 helper 调用保持原 relative timeout 行为。

精确回归模拟 parent startup 消费 `3.6s`，断言 `communicate(timeout=76.4)`；随后关键探针模拟消费
`72s`，helper 仍在 parent absolute deadline 前自然写出 blocked final，没有读取 partial fallback、没有
写 timeout fallback，也没有发送 timeout signal。另两条回归分别锁定 deadline 在 `Popen` 前耗尽和
`Popen` 后耗尽的 fail-closed 路径。

最终离线验证：

```text
python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py
exit 0

python3 -m unittest onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_nav2_runtime_proof_parent_absolute_deadline_starts_before_popen
Ran 1 test in 0.002s
OK

python3 -m unittest onboard/tests/test_upper_robot_api.py
Ran 119 tests in 0.263s
OK (skipped=1)

python3 -m unittest onboard/tests/test_nav2_runtime_proof_helper.py
Ran 170 tests in 2.456s
OK

python3 -m unittest onboard/tests/test_upper_robot_api.py onboard/tests/test_nav2_runtime_proof_helper.py
Ran 289 tests in 2.689s
OK (skipped=1)
```

使用统一 strict added-nonblank-line audit 复算新增代码：Robot Software 为中文技术注释
`75 / 317 = 23.66%`，Algorithm 为 `36 / 163 = 22.09%`，两者均严格大于 `20%`。Robot 补充的
注释只解释 absolute deadline 的时钟域、Popen 前预算所有权、communicate remaining、pre-Popen
fail-closed 与 post-Popen owned cleanup/no-budget-reset 等安全不变量，没有修改功能。

第一轮精确回归曾因测试在 `TemporaryDirectory` 退出后才读取 artifact 而得到
`FileNotFoundError`；测试 fixture 改为在 context 内读取后，同一精确目标和所有全量回归均通过。
该失败不来自 deadline runtime contract。

本阶段没有执行 SSH、ROS live、Nav2 action、控制 endpoint、UART 或运动。proof boundary 是
`software_proof_o3_o10_parent_absolute_deadline_end_to_end_contract_only`；Product 可以据此完成本
Epic 的离线工程 closeout，但不能把它升级为 current localization、route execution、HIL、delivery、
safe-to-control 或 Mission Objective 0 完成证据。

## 剩余风险与后续 owner gate

- Algorithm/Robot Software：root cause、helper consumer 与 parent producer 已完成离线集成并通过组合回归；仍不得复用本轮授权重跑 Phase A。未来现场验证必须取得新的 current authorization，并继续保持 Phase A exactly once。
- Hardware：本轮 Phase B 没有进入，`T=1001=0`，无需且不得把本轮判为 HIL；只有未来 execute=`1` 的冻结同窗 artifact 才进入 Hardware 只读专业验收。
- Full-stack：没有 Phase B action receipt 上游，不需要创建 endpoint/wrapper/mock success；可等待未来 clean upstream artifact。
- Robot Software：当前 lifecycle 已安全停止且 residual 为 `0`。若 Algorithm 修复离线预算合同，下一次 live proof 必须重新取得新的 current authorization，仍保持 Phase A exactly once。
- 原始 proof refresh wrapper 已在 client stream 中完整解析，但该 streamed body 没有再次复制为独立 raw 文件；canonical current artifact 已完整保存到 `phase_a_nav2_proof_latest.raw.json`，传输与精确语义摘要保存在 `phase_a_nav2_proof_refresh.transport.json`。这是 artifact 完整性剩余风险，不允许通过第二次 refresh 补采。

本文件只完成 Engineer `tech-done.md`；没有创建 `side2side_check.md` / `final.md`，也没有修改 `OKR.md` 或 progress log。
