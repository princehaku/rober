# O7 Direct Upper Live Route Action - PRD

## 文档状态

- `sprint_type: epic`
- 状态：`approved_for_implementation_after_planning_acceptance`
- 唯一主责：`full-stack-software-engineer`
- 目标 Objective：O7/O6；O1 supporting；O5 paused

## 1. 用户问题

上一轮已经证明 workstation 的 action receipt 合同能够在 handler 内对 forwarded/rejected/failed/timeout/unsafe 结果做安全表达，但真实序列被本机 7072 loopback interceptor 挡在 handler 前，用户没有得到上位机动作、Nav2 terminal、stop 或底盘反馈。继续增加 wrapper、readback surface 或 mock receipt 不会缩短用户从“确认发车”到“知道小车是否真实执行并已停住”的路径。

本轮用户需要一次受控、唯一、可停止的真实 route action：operator 在场、路线清空、小车物理位置受限，先确认上位机本机 API 可读，再执行固定 28-pose lineage 的目标一次，随后停住并读回结果。

## 2. 产品目标与非目标

### 2.1 产品目标

1. 在 `ssh root@192.168.1.11 -p 37878` 提供的非 loopback-interceptor 环境中，确认上位机 `127.0.0.1:8787` 的 health、status 与 Nav2 latest 可读。
2. 在 pre-gate 通过且 fresh authorization 仍有效时，对固定 `/api/nav2/goal/execute` 发起 exactly-one 请求；请求必须包含 `confirm_navigation_execution=true`。
3. 以新 run/action/authorization identity 绑定同一 28-pose task/route lineage，但 identity 只进入本 sprint artifact/manifest，不伪装成上位机已支持的 request 字段。
4. execute 后最多一次调用 `/api/base/stop`，然后只读 Nav2 latest 与 base feedback latest。
5. 用 artifacts 和 JSON 断言区分 user action、live control、route terminal、wheel/HIL 与 delivery；不因 HTTP 200 或 SSH 可达自动计分。

### 2.2 非目标

- 不新增或修改 endpoint、wrapper、UI、route readiness、preflight、browser artifact、O6 intake 或 O5 provider 工具。
- 不执行 manual、keyboard、free-roam、direct `/cmd_vel`、`/initialpose`、delivery complete 或 UART 命令。
- 不修改 goal、mode 或 route lineage 进行补跑；任何结果都不允许第二次 execute。
- 不把 health、SSH、HTTP reachability、status/latest、规划文档或 stop intent 本身当 route/delivery 业务结果。
- 不宣称 `delivery_success=true`；本轮没有 delivery/operator acceptance action。

## 3. 冻结动作合同

### 3.1 Identity envelope

```text
task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402
route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path
run_id=run_o7_direct_upper_live_route_20260720_02
action_id=action_o7_direct_upper_nav_20260720_02
authorization_ref=ceo_20260720_1220_bounded_motion_operator_watch_route_clear_v2
```

旧 run/action/authorization 已消费，不得复用。identity envelope 与 request body 的 SHA256 必须写入 invocation manifest，证明本轮 artifact 同属一个 action window。

### 3.2 固定 request body

```json
{
  "confirm_navigation_execution": true,
  "goal_frame_id": "map",
  "goal_x": 0.8,
  "goal_y": 0.25,
  "goal_yaw": 0.0,
  "base_command_mode": "ros",
  "managed_runtime_opt_in": true,
  "result_timeout_s": 8,
  "server_timeout_s": 12,
  "route_preview_point_count": 28,
  "route_preview_source_point_count": 28,
  "route_preview_frame_id": "map",
  "route_start_x": 0.07615115310756959,
  "route_start_y": 0.2500000037252903,
  "route_goal_x": 0.8,
  "route_goal_y": 0.2500000037252903
}
```

request body 沿用上一轮已冻结的目标、mode、timeout 与 28/28 route metadata，唯一新增是 direct upper 必需且必须显式存在的 `confirm_navigation_execution=true`。不得把 workstation-only identity 字段发给上位机。

## 4. 用户旅程与验收场景

### 场景 A：pre-gate fail closed

如果 SSH、health、status、latest 任一无法形成可解析/可归因的只读 JSON，或读回显示已有运动、授权/看护/清场条件失效、明确 unsafe blocker，则动作阶段不启动：execute=`0`、stop=`0`。保存原始 body、HTTP/SSH 元数据和 `pre_gate_decision.json` 后收口；不得以换 endpoint、wrapper、mock 或 product code 修改绕过。

### 场景 B：动作请求被上位机接收但未成功

pre-gate 通过后 execute 必须 `exactly-one`、`no.retry=true`。无论 HTTP non-2xx、timeout、disconnect、goal reject、cancel 或 terminal failure，保存原始响应并最多一次 stop；之后只读 latest/feedback。本场景可在存在直接上位机调用证据时形成 `user_action_delta=true`，但 `live_control_delta`、route success、HIL 与 OKR credit 由真实字段决定。

### 场景 C：动作与读回成功

只有同一 action window 同时出现可归因的 execute response/latest、`goal_accepted=true`、`result_received=true`、`result_status=succeeded`、`robot_control_executed=true`，并由 latest/feedback 支持，才可把 route terminal 作为 Product acceptance 候选。`nav2_goal_execution_proven`/`hil_pass` 还必须满足合同中的 current wheel L/R 条件；stop 需要独立响应/readback。delivery 仍固定未证明。

## 5. 功能需求

- `FR-1`：先远端只读 `GET http://127.0.0.1:8787/health`；因仓库 canonical route 为 `/api/health`，若 `/health` 不存在，只允许再做一次只读 `/api/health` 合同探测并分别留档。
- `FR-2`：读取 `GET /api/status` 与 `GET /api/nav2/goal/execution/latest`，生成机器可读 pre-gate decision。
- `FR-3`：pre-gate 不通过时动作端点调用数必须为 `0`。
- `FR-4`：pre-gate 通过后只调用一次 `POST /api/nav2/goal/execute`，body 与 3.2 完全一致。
- `FR-5`：execute 之后最多一次 `POST /api/base/stop`；stop 不得 retry。
- `FR-6`：随后只读 `GET /api/nav2/goal/execution/latest` 与 `GET /api/base/feedback-samples/latest`。
- `FR-7`：manifest 必须记录每个 endpoint 的 method、invocation count、curl/SSH exit、HTTP status、response SHA256、JSON parse 状态、时间顺序和 `no.retry=true`；不得记录 credential 或 raw SSH 配置。
- `FR-8`：保存真实失败 body，不以 synthetic/mock JSON 覆盖；结构化 metadata 可以单独包裹失败事实。
- `FR-9`：运行 workstation Nav2 contract targeted/full regression、build、lint；即使 run-only 也要证明既有合同未漂移。
- `FR-10`：更新本 sprint `tech-done.md`，随后由 Product 做 `side2side_check.md` 与 `final.md`。

## 6. 验收口径

### 6.1 序列与安全

- pre-gate 前 motion POST=`0`。
- pre-gate pass 时 direct upper execute invocation=`1`；pre-gate fail 时=`0`。
- 全序列 execute `<=1` 且不得重试；manifest 必须为 `no.retry=true`。
- stop invocation `<=1`；禁止第二次 stop。
- manual/free-roam/keyboard/direct `/cmd_vel`/`/initialpose`/UART/delivery invocation 全为 `0`。

### 6.2 Artifact 与 identity

- identity 五字段逐字匹配 3.1，request `confirm_navigation_execution is True`。
- task/route 保持 28-pose lineage，route preview/source counts 均为 `28`，目标与起终点不漂移。
- health/status/latest/execute/stop/feedback 原始事实与 request/manifest 均可追溯；JSON response 不可解析时原始 body 仍保留。

### 6.3 业务结论

- `user_action_delta=true`：必须证明 pre-gate 后 direct upper execute 确实调用一次且上位机 handler 给出可归因 response/latest；单纯 SSH/curl invocation 或 transport failure 不足。
- `live_control_delta=true`：必须有 current response/latest 明确 `robot_control_executed=true`，且和本 action 的 terminal/时间窗一致。
- `external_artifact_delta=true`：artifact 必须来自真实上位机 8787，而非本地 fixture/mock/synthetic。
- `route_execution_success=true`：必须同时满足 accepted、result received、succeeded 与上位机合同 proof；否则 false。
- `hil_pass=true`：只能消费 current upper latest/feedback 的明确 true，且 wheel L/R 同窗口条件成立；否则 false。
- `delivery_success=false`：本轮固定，不调用 delivery complete。
- `safe_to_control` 不因本轮成功永久置 true；只做本 action 的有界 acceptance，不扩大未来授权。

## 7. 优先级、owner 与风险

- P0：Full-stack 先执行 read-only pre-gate 和唯一 action window。
- P1：同 owner 固化 artifacts、运行 regression、写 `tech-done.md`。
- P2：Product 在事实出现后做 acceptance；需要 Algorithm/Hardware 判读时再单独只读咨询，不回头修改本 action。

主要风险：SSH 连接中断、canonical health 路径与 CEO shorthand 不同、API 响应慢或非 JSON、execute 后连接断开导致 stop 只能在新 SSH 会话尝试一次、latest 可能是旧 artifact、goal succeeded 但 wheel L/R 为零、stop response 不足以证明底盘已停。所有风险均用 invocation count、时间戳、response SHA 与 conservative delta 判定收口，不追加第二动作。

## 8. KR 更新与历史归档规则

开工时不调整 OKR 百分比、不归档 KR。若只有 health/SSH/pre-gate 或 transport failure，O7/O6/O1 全 flat。若形成新 current live user action、control、route/HIL 证据，由 Product 在 `side2side_check.md` / `final.md` 中按 delta 分级决定是否提升；只有对应 KR 的完整验收条件满足才移动到 `OKR.md` 历史区，并记录完成时间、本 sprint 证据链接、验收结论、剩余 delivery/operator 风险和后续影响。
