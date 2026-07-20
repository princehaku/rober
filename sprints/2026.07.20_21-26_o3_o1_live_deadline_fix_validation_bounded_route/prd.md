# O3/O1 Live Deadline Fix Validation + Bounded Route - PRD

## 用户价值和产品北极星

用户价值是把“离线 absolute-deadline 修复已通过测试”升级为一次真实板、当前上下文、可审计的 natural-final 判定；如果 readiness 真正全绿，再把同一个 owner、同一个 runtime、同一个 identity 延伸为 exactly-one bounded route 与同窗停止/反馈证据。失败同样有价值，但必须表现为可归因 NO-GO、零重试和 clean cleanup，而不是另一个 wrapper。

产品北极星：`85ba7308785aa3c4033180a097e3d388358a97de deployment -> remote SHA verified -> current natural final -> READINESS_GO -> exactly-one authorized mission attempt -> terminal -> stop/T=1001 -> operator/HIL review`。

## OKR 映射与方向判断

- O5 约 `85%`：`暂停`。provider/runtime blocker 已 `2/2`，本轮不得消费第三次 support surface。
- O3：`继续 supporting`。本轮只验证 current localization/path readiness 与 deadline fix 的真实板行为；单独 GO/NO-GO 不自动抬主百分比。
- O1 约 `94%`：`继续但保持 flat 起步`。只有 Phase B 后 same-window pre/post stop、有效 `T=1001`、motion/post-stop 隔离和 operator outcome 才形成 HIL 候选。
- O6/O7 各约 `93%`：`继续但保持 flat 起步`。只有 direct-upper current action 与 terminal lineage 才形成 user-action/route 候选；Full-stack receipt contract 不在没有 terminal 时重复消费。
- KR：本轮不预先完成、不归档。历史完成区无新增；最终位置只能由 future `final.md` 引用 current artifact、terminal/HIL/operator evidence 后决定。

## 冻结 lineage

任何 remote POST 前必须写入并冻结：

- `authorization_ref=ceo_20260720_2124_operator_watch_route_clear_physical_limit_v2`
- `run_id=run_o3_o1_current_readiness_route_20260720_2124_01`
- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- `action_id=action_o3_o1_bounded_nav_20260720_2124_01`
- `source_host=root@192.168.1.11:37878`
- `goal=map (0.8, 0.25, yaw=0)`
- `target_commit=85ba7308785aa3c4033180a097e3d388358a97de`
- `no_retry=true`

所有 raw/manifest 必须携带生成时间、source endpoint、SSH/curl/HTTP exit、JSON parse、SHA256、identity 与 invocation count；artifact 先保存原始响应，再做语义断言。

## 功能需求

### FR0 - Phase 0 HEAD 部署与远端硬门

`robot-software-engineer` 必须先证明本地 `HEAD` 等于目标 commit，目标 commit 中 Upper API 与 O10 helper 的内容 SHA 分别固定为：

- `onboard/scripts/upper_robot_api.py`: `8c0f6eebb786e1cd6b1cb5d17485e59972140bf76a94e7669773ef438228b4c3`
- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`: `d9f92d708bdac6feec35798e4acfcd50b58349a3de3315a24a605cf5c82307eb`

先运行离线 targeted/full 回归，再部署目标 commit 的这两份脚本到 `/root/rober/onboard/scripts/`，远端 `py_compile`、SHA、service restart、health/status/nav2 status 必须全部 clean。远端 commit identity 能读取时必须等于目标 HEAD；如远端工作区不承载相同 Git commit，则 deployment manifest 必须明确 `remote_git_commit_unavailable_or_not_authoritative`，并以“两份目标 commit 内容 SHA 均匹配 + remote py_compile + service health”作为实际部署硬门。两份脚本任一 SHA 不匹配时，Phase A invocation 必须保持 `0`。

### FR1 - Phase A exactly-once strict-no-motion validation

在 remote loopback `http://127.0.0.1:8787` 严格串行：

1. 只读 `/api/health`、`/api/status`、`/api/nav2/status`，确认 Upper API healthy、owned lifecycle 初始 stopped、无 existing motion。
2. 恰好一次 `POST /api/nav2/start`：`strict_no_motion=true`、base/LiDAR=`false/false`、reuse existing scan。
3. 恰好一次 `POST /api/nav2/proof/refresh`：不启动第二 runtime、不发布 `/initialpose`，固定 goal `map (0.8, 0.25, 0)`，使用已部署 absolute monotonic deadline fix。
4. 恰好一次读取 proof latest，并读取 nav2/status；形成 `readiness_assertion.json` 与 `phase_a_invocation_manifest.json`。
5. Phase A 未 frozen 前不得派 Algorithm；Phase A GO 时保持当前 lifecycle 给同一 live owner 进入 Phase B，NO-GO 时立即一次 owned Nav2 stop/cleanup。

`READINESS_GO=true` 必须同时满足：

- proof 为 current、natural final、`artifact_kind=final`、`last_phase=final`、`current_command=null`，且不是 partial/fallback/timeout；
- absolute deadline source、parent/helper shared deadline 与 remaining-wait 字段可审计，未扩大 80 秒外层预算；
- current AMCL pose 与 persisted pose audit fresh、无 current/reference conflict；
- dynamic `map->odom` observed、timestamp parsed、fresh、unique AMCL attribution，且 `map->base_link=true`；
- map_server、amcl、planner_server、controller_server active；
- path requested/attempted/succeeded/generated=true，point count `>0`，目标严格为 `(0.8, 0.25, 0)`；
- current obstacle clear 已由 current sensor/status gate 证明，不能把旧 `0.035m` 或 unknown 当 clear；
- existing motion=false、operator/route/physical-limit authorization current；
- `initialpose_publish_attempts=0`、base/LiDAR new-open=`0/0`；
- start/proof/latest=`1/1/1`，goal/manual/free-roam/direct cmd_vel/UART/delivery=`0`。

任一字段 missing/unknown/stale/conflict/timeout/non-final 都是 `READINESS_GO=false`。

### FR2 - Algorithm frozen review

Phase A raw、manifest、readiness assertion 和 cleanup/continuity 状态冻结后，才派 `robot-algorithm-engineer`。它只读复核 absolute deadline、natural-final、pose/persisted-pose、TF freshness/attribution、planner/controller、path 与 exact blockers；不得 SSH、不得调用 live endpoint、不得 start/proof/stop/goal、不得同窗 retry。若发现代码 bug，只能在自己的 helper/test/doc 范围修复并完成离线验证；本授权不重开。

### FR3 - Conditional Phase B exactly-one bounded route

只有 `READINESS_GO=true` 且 Algorithm 接受 frozen Phase A，原 `robot-software-engineer` 才继续：

1. 恰好一次 pre-base-stop；要求 HTTP、semantic stop、feedback/readback、lineage 全 clean。
2. pre-stop 任一失败：goal invocation=`0`，立即 owned Nav2 cleanup，封存且禁止 retry。
3. pre-stop clean：恰好一次 `POST /api/nav2/goal/execute`，固定 `map (0.8, 0.25, yaw=0)` 与冻结 identity。
4. 不论 execute success/fail/timeout/unknown，最多一次 post-base-stop；随后只读 execution latest、feedback samples latest、status。
5. 最后恰好一次 owned `/api/nav2/stop` 清理；remote owned residual 必须为 `0`。

Phase B 进入时必须形成 `phase_b_invocation_manifest.json`，记录 pre/post base stop 与 Nav2 lifecycle stop 为不同 endpoint/count。Phase A NO-GO 或 pre-stop fail 时不得创建 route terminal success artifact；Phase A manifest/tech-done 必须记录 Phase B counts=`0`、no-retry=true 与缺席原因。

### FR4 - Conditional Hardware same-window T=1001/HIL review

只有 Phase B 完全 frozen 且 execute=`1` 后才派 `robot-hardware-engineer`。Hardware 必须先读 `docs/vendor/VENDOR_INDEX.md` 及其指向的 `WAVE_ROVER_V0.9/json_cmd.h`、`uart_ctrl.h`、`ugv_rpi/base_ctrl.py`；本地 vendor source 规定 `FEEDBACK_BASE_INFO=1001`，但 `T=1001` 存在本身不等于 L/R 非零、轮向正确或 HIL pass。

Hardware 只读校验同一 `run_id/action_id` 的 pre-stop、motion window、post-stop、`T=1001` 与 `L/R/r/p/y/v`、operator outcome、时间窗和隔离；不得发送 goal、stop、manual、`/cmd_vel`、UART 或任何补采命令。

### FR5 - Full-stack 默认不派

本轮不派 `full-stack-software-engineer`。只有 Phase B 产生 current route terminal、既有 action receipt consumer 被真实输入触发且出现可复现 contract bug 时，才允许最小修复现有 contract/test/doc；不得新建 endpoint、wrapper、readback surface 或 mock success，也不得调用机器人。

## 非功能与安全要求

- live owner 唯一、严格串行；Algorithm/Hardware 不得并行接触上位机。
- remote SHA 是 Phase A 前硬门；不得直接在远端交互式编辑脚本，不得用旧部署 SHA 冒充目标 commit。
- 所有控制请求 exactly-once；NO-GO、pre-stop fail、terminal fail/timeout/unknown 都不得同窗重试。
- raw-first、parse-second、fail-closed；HTTP `200`、测试通过、path success、operator 文本、`T=1001` frame identity 均不能单独升级 route/HIL/delivery/safe。
- 新增/修改产品与测试代码的技术注释全部中文，有意义中文注释比例严格 `>20%`；相关功能变更必须同步 `docs/`。
- 验证失败先由 owner 定位、最小修复、重跑 targeted/full；若涉及 live 行为，修复后只能离线验收并申请下一 fresh authorization，不能重开本窗口。

## 验收与 proof/credit tiers

- Tier 0 `deployment_verified`：目标 commit 内容 SHA + remote compile/service health 通过；不计 Mission。
- Tier 1 `current_readiness_no_go`：自然 final 或诚实 NO-GO + owned cleanup；只算 current diagnostic delta，route/HIL/user action false。
- Tier 2 `mission_attempt`：GO + clean pre-stop + exactly-one execute 被 direct handler 归因；user-action candidate，不等于 route success。
- Tier 3 `route_terminal`：same-lineage current terminal success + latest/readback；route success candidate。
- Tier 4 `current_hil_operator_candidate`：Tier 3 + same-window pre/post stop + valid `T=1001` motion/post-stop + operator outcome。
- `delivery_success=false` 固定；`safe_to_control` 默认 false。Product 只能在 `side2side_check.md`/`final.md` 按冻结证据决定 OKR 增量或 KR 历史归档。

## 风险、阻塞与需补证据

- 真实板调度、ROS CLI、filesystem atomic write 可能仍使 absolute-deadline fix NO-GO；这是本轮要验证的首要风险。
- current pose/persisted pose、TF freshness、planner/controller、path、obstacle clear 任一不绿都会阻断 Phase B。
- remote Git commit 可能不是部署事实的权威；因此同时冻结目标 commit、两份精确内容 SHA 与 service health。
- Phase B 未发生则 `T=1001`/HIL/operator/route terminal 全缺，不得用历史 artifact 补 credit。
- Full-stack receipt 只有真实 route terminal 输入后才有资格复核，避免再次消费 support-only surface。

## 责任与后续留档

- P0/P1：`robot-software-engineer`，Phase 0/A/B、修复、raw/manifest、cleanup、`tech-done.md`。
- P1 条件：`robot-algorithm-engineer`，Phase A frozen 后只读 readiness review。
- P2 条件：`robot-hardware-engineer`，Phase B frozen 后只读 T=1001/HIL review。
- P3 例外：`full-stack-software-engineer`，仅真实 terminal 触发现有 receipt contract bug。
- 本轮先创建 `pre_start.md`、`prd.md`、`tech-plan.md`；不得预生成 `tech-done.md`、`side2side_check.md`、`final.md`。
