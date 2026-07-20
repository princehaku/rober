# O3/O1 Current Readiness + Bounded Route - PRD

## 用户价值与北极星

用户需要的不是又一份“可执行”说明，而是一次可归因、可停止、不可重试的现场任务证据：先证明机器人当前能定位并生成到受限目标的路径，再在 operator 看护与物理限位下执行一次 bounded route，保留真实终态、同窗停止与底盘反馈。

北极星：产生 `current readiness -> exactly-one user-authorized route attempt -> terminal result -> post-stop/T1001 -> operator receipt` 的单一 lineage；失败也必须形成可行动的 NO-GO 或 terminal artifact。

## OKR 映射与方向判断

- O5 约 `85%`：继续暂停，provider/runtime 同根因已 `2/2`，本轮不消费。
- O3：继续 current localization/path readiness supporting；其价值是解锁 route，不单独抬主百分比。
- O6/O7 各约 `93%`：只有 direct-upper handler/current action/terminal/receipt 真实可归因时才形成 user-action 或 route evidence 候选。
- O1 约 `94%`：只有 same-window pre/post stop、T1001 和终态可归因时形成 current HIL supporting 候选。
- KR 不预先归档；百分比只由 Product final 基于现场 evidence 调整。

## 功能需求

### FR1 - 冻结 lineage 与授权

必须在任何 remote POST 前冻结：

- `authorization_ref=ceo_20260720_2025_operator_watch_route_clear_physical_limit_v1`
- `run_id=run_o3_o1_current_readiness_route_20260720_2025_01`
- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- `action_id=action_o3_o1_bounded_nav_20260720_2025_01`

所有 artifact 必须记录生成时间、来源 endpoint、HTTP/SSH/curl exit、JSON parse、SHA256 与 invocation count。

### FR2 - Phase A current no-motion readiness

在上位机 remote loopback `http://127.0.0.1:8787`：

1. 读取 `/api/health`、`/api/status`、`/api/nav2/status`；确认无 existing motion、Upper API healthy。
2. 仅一次 `POST /api/nav2/start`，body 固定 strict-no-motion、base/lidar `false/false`、reuse existing scan。
3. 仅一次 `POST /api/nav2/proof/refresh`，`managed_runtime_opt_in=false`、`initialpose_opt_in=false`、path goal=`map (0.8,0.25,0)`。
4. 读取 `/api/nav2/proof/latest` 与 `/api/nav2/status`，形成 `readiness_assertion.json`。
5. Phase A 结束前不得 stop，以便 GO 时复用同一 current lifecycle；NO-GO 则立即 owned stop/cleanup。

`READINESS_GO=true` 必须同时证明：current/final artifact；map_server/amcl/planner/controller active；fresh persisted pose；fresh/attributed dynamic `map->odom`；`map->base_link=true`；`initialpose_publish_attempts=0`；path attempted/succeeded/generated 且 point count > 0；current obstacle clear；pre-stop ready；base/LiDAR new-open count=`0/0`；所有 forbidden invocation count=`0`。

### FR3 - Phase B exactly-one bounded route

只有 FR2 全绿才允许：

1. 执行一次 `POST /api/base/stop` pre-stop，并要求 semantic stop/readback clean；失败则 route count=`0`。
2. 执行一次 `POST /api/nav2/goal/execute`，目标固定 `map (0.8,0.25,0)`，`confirm_navigation_execution=true`、managed runtime reuse、no retry。
3. 无论 execute 返回 success/fail/timeout/unknown，最多执行一次 post-stop；禁止第二次 execute/stop 补证据。
4. 只读 `/api/nav2/goal/execution/latest`、`/api/base/feedback-samples/latest`、`/api/status`，随后 owned `/api/nav2/stop` 清理 current lifecycle。

### FR4 - Hardware 同窗验收

Hardware 必须先读 `docs/vendor/VENDOR_INDEX.md` 及其指向的 `json_cmd.h`、`uart_ctrl.h`、`ugv_rpi/base_ctrl.py`。只读验证 same-window vendor `T=1001` frame、`L/R/r/p/y/v`、pre/post stop、motion/post-stop 隔离和 lineage；不得发送 goal、manual、`/cmd_vel`、UART 或额外 stop。

### FR5 - 用户动作 receipt

Full-stack 只消费冻结的 Phase A/B artifact 与 identity，验证现有 action receipt/consumer read 能表达 request accepted/rejected、NO-GO/terminal、stop、feedback 与 operator outcome。若没有 clean upstream artifact则 Phase C skipped；不得创建新 endpoint、wrapper 或 mock success。

## 验收层级

- Level 0：Phase A NO-GO final artifact + owned cleanup；只算 current diagnostic，不计 route/HIL。
- Level 1：direct handler 可归因接收一次 action；`user_action_delta=true` 候选，仍不等于 motion/route。
- Level 2：goal accepted、result received、terminal succeeded 且 current latest 可归因；`route_execution_success=true` 候选。
- Level 3：Level 2 + same-window pre/post stop + T1001 motion/post-stop证据 + operator outcome；current HIL/operator acceptance 候选。
- `delivery_success` 本轮固定 false；`safe_to_control` 不因一次成功自动为 true。

## 非功能与安全要求

- 单一 live-control owner、严格串行、调用计数可审计。
- artifact 先落原始响应，再做解析；不可解析时保留 raw 并 fail closed。
- 不修改 vendor/firmware/launch/串口默认值；不猜 UART、波特率或反馈语义。
- 新增/修改代码的技术注释全部中文，且有意义中文注释比例严格 `>20%`。
- 所有代码/测试/文档更改同步对应 `docs/navigation/`、`docs/hardware/` 或 `docs/product/`。
