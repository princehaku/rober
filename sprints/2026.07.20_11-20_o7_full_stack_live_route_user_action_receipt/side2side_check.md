# O7 Full-stack live route 用户动作回执 - Side-by-side Check

## Sprint metadata

- `sprint_type: epic`
- Product status：`accepted_contract_delivery_blocked_live_acceptance`
- 主责 owner：`full-stack-software-engineer`
- Product owner：`product-okr-owner`
- Contract Proof boundary：`software_proof_o7_route_user_action_receipt_contract_only`
- Live Proof boundary：`blocked_live_attempt_no_receipt_no_remote_action`
- Live blocker：`local_loopback_interceptor_header_only_http_400`
- Runtime failure class：`localhost_exec_network_interception_before_workstation_handler`

## Product side-by-side 结论

本轮把“既有固定 Nav2 execute endpoint 是否能产生 same-task 用户动作回执”拆成两个独立验收面：软件合同通过，
真实 live acceptance 未通过。两者不得相互替代。

| 验收项 | 计划口径 | 实际证据 | Product 裁决 |
| --- | --- | --- | --- |
| 既有 endpoint 增量 | 不新增 endpoint；在 `/api/robot-control/nav2/goal/execute` 增加五项 identity 与统一 receipt | `contracts.ts`、`server/index.ts` 与产品文档已实现；fixed remote path、goal clamp、base URL allowlist、preflight 与 dangerous true guard 保留 | 接受 |
| receipt 安全合同 | forwarded/rejected/failed/timeout/unsafe 都保留安全 lineage，禁止 raw payload、credential、SSH target、绝对路径 | Targeted 最终 `5 passed`；hostile identity、preflight reject、remote 500、schema drift、timeout/no retry、dangerous true matrix 已覆盖 | 接受 |
| 全量质量门 | 全量 test/build/lint/diff 通过，中文注释严格 `>20%` | `Tests 532 passed (532)`；build exit `0`、lint 修复后 exit `0`、scoped diff exit `0`；新增注释比例 `23.26%/20.28%/20.20%` | 接受 |
| exactly-once execute | 本地 execute curl=`1`，不得 retry；必须进入 workstation handler 才能形成 receipt | manifest 为 local execute curl=`1`、`no_retry_observed=true`，但 HTTP `400`、空 body、workstation handler=`0`、remote execute=`0` | 不接受为有效用户动作 |
| stop rule | execute 后 stop 最多一次并保存回执 | local stop curl=`1`，HTTP `400`、空 body；workstation stop handler=`0`、remote stop=`0`；没有第二次 stop | 接受 no retry/调用上限；拒绝 stop 已到达真车 |
| live receipt/readback | action、stop、latest、feedback、post summary 应为可解析 JSON | 六个 response artifact 均为 `0 bytes`；receipt absent，terminal/readback=`unknown_not_reached` | 拒绝 live acceptance |
| cleanup | 本地 7072 PID 必须清理 | PID `5380`，`local_api_pid_cleanup=clean`；tech-done 记录 `SIGINT + wait` | 接受 |
| mock 边界 | live 失败后不得以 fixture/mock 替代 | `mock_fallback_invocation_count=0`；空文件按原始事实保留 | 接受 |

## 实际代码交付验收

Product 接受以下交付为软件合同完成：

1. 请求增加 `task_id/run_id/route_intent_id/authorization_ref/action_id`；identity 清洗删除控制字符，限制长度，
   并对 credential、URL、SSH target 和绝对路径整体脱敏。
2. `trashbot.pc_tools_workstation.o7_route_user_action_receipt.v1` 在 reject、remote failure、schema drift、timeout、
   unsafe 和 forwarded 分支统一生成；`request_forwarded` 与 `robot_control_executed` 不再和 route/delivery/HIL 混为一谈。
3. Receipt 固定 `route_execution_success=false`、`hil_pass=false`、`safe_to_control=false`、
   `delivery_success=false`，且 identity 不转发上位机，不改变现有动作 body。
4. Engineer 已同步 `docs/product/pc_tools_workstation.md`，没有新增 endpoint、依赖、lockfile、上车 API、ROS2、
   Algorithm、Hardware 或 UART 变更。

Product 没有在本阶段重跑 npm test/build/lint；验收复用 `tech-done.md` 的 Engineer 证据，并只做 artifacts、diff、
OKR 和文档结构检查。

## Live acceptance 与用户动作裁决

`live_sequence_invocation_manifest.json` 是本轮唯一可信的 live 序列清单：

- `local_execute_curl_invocation_count=1`
- `workstation_execute_handler_invocation_count=0`
- `remote_execute_invocation_count=0`
- `local_stop_curl_invocation_count=1`
- `workstation_stop_handler_invocation_count=0`
- `remote_stop_invocation_count=0`
- execute/stop/latest/feedback/summary `http_status=400`
- `response_body_boundary=header_only_empty_body_before_workstation_handler`
- `no_retry_observed=true`
- `local_api_pid_cleanup=clean`

因此 `user_action_delta=false`。虽然本地 curl 确实发起一次 POST，但它没有进入 workstation handler、没有形成
`user_action_receipt`、没有调用真实 upper endpoint；这不满足 PRD 对有效 live/fail-closed 用户动作回执的定义。
同理，HTTP 400 不能归因到 `192.168.1.11:8787`、Nav2、定位、controller、WAVE ROVER、路线或现场 operator。

## Mission / OKR / KR 对照

- `current_run_artifact_delta=true`：仅指 receipt contract、tests、tech-done 与 invocation manifest 的本轮工程增量；
  不属于 mission-grade artifact，也不允许 OKR credit。
- `external_artifact_delta=false`
- `live_control_delta=false`
- `user_action_delta=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `safe_to_control=false`
- `mission_objective_0_satisfied=false`
- `okr_credit=false`

O5 保持约 `85%`、O6/O7 各保持约 `93%`、O1 保持约 `94%`，主百分比不调整。没有完成 KR 可进入历史区，
KR `不归档`。本轮只在 `OKR.md` O7 段和 `docs/process/okr_progress_log.md` 追加 flat closeout note。

## Anti-repeat 与 reopen signal

本 blocker 不同于此前 Algorithm/Hardware 的 `business_subagent_runtime_stalled_before_business_file_or_command_execution`：
本轮 Full-stack 已真实落代码并通过产品验证，失败发生在 live exec loopback 隔离层、workstation handler 之前。

但本 sprint 的 execute/stop 调用额度已消费，禁止再次执行 live POST，也不得创建 wrapper/canary/mock receipt。只允许以下
任一 reopen signal 后另开新 action window：

1. runtime owner 提供可复核证据，证明同一进程的 `127.0.0.1:7072` 请求已能进入 Express handler，且只读
   `/api/health` 返回 workstation JSON；随后 CEO/Product 给出新的 fresh bounded-motion authorization；或
2. CEO/Product 明确批准一个不经过当前 loopback interceptor 的执行环境，并先以只读 health/summary 证明该环境连接
   workstation/upper endpoint，再给出新的 fresh authorization。

下一轮不得重复本 sprint sequence、不得只开 network wrapper，也不得用 mock/synthetic artifact替代 receipt。
