# O7 Full-stack live route 用户动作回执 - Tech Done

## Sprint metadata

- `sprint_type: epic`
- 状态：`contract_complete_live_attempt_blocked_before_workstation_handler`
- 主责 owner：`full-stack-software-engineer`
- Sprint：`sprints/2026.07.20_11-20_o7_full_stack_live_route_user_action_receipt/`
- 最终 Proof boundary：`blocked_live_attempt_no_receipt_no_remote_action`
- 本阶段只完成 `tech-done.md`；未创建 `side2side_check.md` / `final.md`，未修改 `OKR.md` 或 progress log。

## 用户旅程变化和触点收益

既有 `POST /api/robot-control/nav2/goal/execute` 现在能把用户动作绑定到安全、限长的
`task_id/run_id/route_intent_id/authorization_ref/action_id`，并在本机 URL/preflight reject、上游 non-2xx、
timeout/transport、schema drift、危险 true response 与 forwarded 路径统一返回 `user_action_receipt`。用户不再只能看
“请求已发出”：回执能区分是否实际调用 fixed upstream、上游 HTTP、terminal/result 安全摘要、是否需要 stop 和失败原因。

本轮 live 用户旅程没有完成：localhost 执行隔离层在 workstation handler 前返回 header-only HTTP 400，因而没有拿到
receipt，也没有触达真实上位机。遵守 exactly-once / no-retry 后，未补第二个 execute、未切 mock、未改目标、未发 manual、
free-roam、direct `/cmd_vel`、`/initialpose` 或 UART。

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - execute request 增加五项可选 audit identity。
  - 新增 `trashbot.pc_tools_workstation.o7_route_user_action_receipt.v1` 合同。
  - receipt 固定 `route_execution_success/hil_pass/safe_to_control/delivery_success=false`。
- `pc-tools/workstation/src/server/index.ts`
  - 增加 identity 限长、控制字符清理和 credential/SSH target/URL/绝对路径整体脱敏。
  - 增加统一 receipt builder，覆盖 rejected/failed/timeout/unsafe/forwarded。
  - 上游 200 非 JSON object 或 schema drift 改为 fail closed。
  - 保留 fixed upstream `/api/nav2/goal/execute`、goal clamp、base URL allowlist、minimal preflight、危险 true guard；identity
    不转发上位机，不改变现有动作 body。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增 success lineage、hostile identity、preflight reject、remote 500、schema drift/绝对路径脱敏、timeout/no retry/no manual
    matrix。
- `docs/product/pc_tools_workstation.md`
  - 同步 identity、receipt、stop rule、schema drift 和 Proof boundary。
- `artifacts/full-stack/live_action_request.json`
  - 保存 tech-plan 冻结 request body，未改目标、mode 或路线 metadata。
- `artifacts/full-stack/live_sequence_invocation_manifest.json`
  - 保存真实 invocation count、HTTP 结果、空 body 边界、PID cleanup 和 no-retry 事实。
- `artifacts/full-stack/pre_action_summary.json`、`live_action_receipt.json`、`post_action_stop_receipt.json`、
  `post_action_latest.json`、`post_action_base_feedback.json`、`post_action_summary.json`
  - 保留 curl 收到的原始空 body（每份 `0 bytes`），没有用 synthetic/mock JSON 覆盖。

## 接口影响

- endpoint 和 remote path 不变：workstation `/api/robot-control/nav2/goal/execute` -> upper
  `/api/nav2/goal/execute`。
- 五项 identity 是 additive audit metadata，只进入 workstation response receipt；旧 caller 可继续省略。
- receipt 的 `request_forwarded=true` 只表示 fixed upstream POST 已尝试，不表示 goal accepted/succeeded。
- `robot_control_executed` 只消费上游明确 true；route/HIL/safe/delivery 四项不由 Full-stack 推导。
- 不新增 endpoint，不修改 package dependencies/lockfile、upper API、ROS2、Algorithm、Hardware 或 UART。

## 验证结果

### Contract 与 workstation

1. Targeted 首轮：
   - 命令：`npm run test -- test/catalog.test.ts -t "Nav2 goal execution"`
   - exit `0`；最小 patch 时 `Test Files 1 passed (1)`、`Tests 3 passed | 254 skipped (257)`。
2. Targeted 最终：
   - 同命令，exit `0`；`Test Files 1 passed (1)`、`Tests 5 passed | 254 skipped (259)`。
3. 全量测试：
   - 命令：`npm run test`
   - exit `0`；`Test Files 4 passed (4)`、`Tests 532 passed (532)`、duration `49.29s`。
   - 全量测试生成器仅刷新两个范围外历史 DOM artifact 的 `checked_at`；已用精确 patch 恢复 HEAD 内容，最终 worktree 不含
     这两个范围外文件。
4. Build：
   - 命令：`npm run build`
   - exit `0`；`34 modules transformed`、`built in 1.88s`；仅保留既有 `>500 kB` chunk warning。
5. Lint：
   - 首轮 exit `1`，仅两处 `no-control-regex`；根因是控制字符正则。
   - 已改为逐字符 code-point 过滤；最终 `npm run lint` exit `0`。
6. Scoped diff check：
   - tech-plan 原命令 exit `0`，无输出。
7. 新增中文注释比例（按 `git diff -U0` 新增行统计）：
   - `contracts.ts = 10/43 = 23.26%`
   - `server/index.ts = 44/217 = 20.28%`
   - `catalog.test.ts = 60/297 = 20.20%`

### Exactly-once live/fail-closed 用户动作

本轮 `npm run api` 两次在打印 listening 后退出且未留下 listener；随后用同一 `createWorkstationApp()` 在受控 PID 生命周期内
启动 7072。不同 exec 会话之间 localhost listener 不可见，因此最终冻结序列把 API 和所有 curl 放在同一 shell；仍然由
exec 网络隔离层在 handler 前统一返回 header-only HTTP 400。

- 受控本地 API PID：`5380`；序列末 `SIGINT + wait`，`api_pid_cleanup=done`；未触碰长期旧 API 进程。
- pre-action summary：总 curl attempt `2`（第一次跨 exec 诊断、第二次冻结序列），成功 JSON `0`；HTTP `400`、空 body。
- 本地 execute curl invocation count：`1`；curl exit `0`、HTTP `400`、空 body。
- workstation execute handler invocation count：`0`（在 handler 前被拦截）。
- remote `/api/nav2/goal/execute` invocation count：`0`。
- mock fallback invocation count：`0`。
- 本地 base stop curl invocation count：`1`；curl exit `0`、HTTP `400`、空 body。
- workstation stop handler / remote stop invocation count：`0 / 0`。
- latest / base feedback / post summary：各 curl invocation `1`，均 exit `0` / HTTP `400` / 空 body。
- receipt：`absent`；terminal/result/readback：`unknown_not_reached`。
- no retry：`true`；没有第二次 execute 或 stop。

这些计数的机器可读记录位于 `artifacts/full-stack/live_sequence_invocation_manifest.json`，该文件
`python3 -m json.tool` exit `0`。

### Artifact 结构断言

- `python3 -m json.tool .../live_action_receipt.json >/dev/null`：exit `1`，
  `Expecting value: line 1 column 1 (char 0)`。
- `python3 -m json.tool .../post_action_stop_receipt.json >/dev/null`：exit `1`，同一空 body 原因。
- tech-plan 原样 Python receipt 断言：exit `1`，在 `json.loads` 抛 `JSONDecodeError`；未输出
  `o7_live_route_user_action_receipt_acceptance_ok`。
- 失败是本轮真实验收结果；未用 mock/synthetic receipt 伪造通过。

## 失败定位

### Repo / contract / test

- 无未修复失败；targeted、全量、build、lint、scoped diff 均通过。
- lint 首轮控制字符正则问题已修复并复验通过。

### Live localhost / 8787 runtime

- 精确 blocker：`localhost_exec_network_interception_before_workstation_handler`。
- 7072 curl 返回 `HTTP/1.1 400 Bad Request`、`Connection: close`、`Content-Length: 0`，没有 Express JSON body；相同结果发生在
  health、summary、execute、stop 和三条 readback。
- 因 workstation handler 未进入，本轮不能推导 `192.168.1.11:8787` 可达或不可达，也不能归因 Nav2、定位、controller、
  WAVE ROVER 或真实路线。
- `docs/vendor/VENDOR_INDEX.md` 已读；本轮没有改硬件协议、UART、波特率、JSON 指令或硬件配置。

## Proof boundary、delta 建议与 OKR 口径

- Contract proof：`software_proof_o7_route_user_action_receipt_contract_only`。
- Live attempt proof：`blocked_live_attempt_no_receipt_no_remote_action`。
- `current_run_artifact_delta=true` 仅表示本轮新增 contract/test/attempt manifest。
- `external_artifact_delta=false`、`live_control_delta=false`。
- `user_action_delta` 建议：`false`。虽然本地 curl POST invocation 为 1，但没有进入 workstation handler、没有 receipt、没有 remote
  action；不满足本 sprint 对有效用户动作回执的验收。
- `okr_credit_allowed=false`，百分比应保持 flat，KR `不归档`。
- 不证明 `request_forwarded=true`、`robot_control_executed=true`、`route_execution_success=true`、`hil_pass=true`、
  `safe_to_control=true` 或 `delivery_success=true`。

## 剩余风险与下一步配合

1. 当前 live artifact 没有 JSON receipt，结构验收明确失败；Product 不应创建成功 closeout 或上调 O7/O6/O1。
2. 本 sprint 已消费 exactly-one execute 和最多一次 stop；不得在本 sprint 内补跑。
3. 下一轮只有在运行时能让同一进程的 `127.0.0.1:7072` 请求真实进入 Express handler，并由 CEO/Product 明确重开一次新 action
   window 后，才可复用冻结 body重新执行；不应新增 wrapper/canary/mock receipt。
4. 若重开，应先用只读 `/api/health` 证明 JSON handler 可达，再读取 pre-action summary；execute 仍只允许一次，随后最多 stop 一次。
5. 即使未来 receipt forwarded 或 terminal succeeded，仍需 Algorithm/Hardware/Product 分别审计 route terminal、同窗口轮速/HIL 和
   delivery/operator acceptance，receipt 本身不能替代这些证据。
