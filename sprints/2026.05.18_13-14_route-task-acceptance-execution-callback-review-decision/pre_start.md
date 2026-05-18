# Sprint 2026.05.18_13-14 Route Task Acceptance Execution Callback Review Decision - Pre Start

## 1. Sprint 类型

- sprint_type: epic
- 时间：2026-05-18 13:14 Asia/Shanghai
- 本轮主题：`route_task_field_retest_acceptance_execution_callback_review_decision`
- 证据边界：`software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_decision_gate`
- 固定安全标记：`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`

## 2. 背景证据

上一轮 sprint `sprints/2026.05.18_12-13_route-task-acceptance-execution-callback-intake/final.md` 已完成 acceptance execution callback intake：PC gate、Robot diagnostics safe alias、mobile/web 只读 panel 都能把 execution pack 后的 callback packet 摄取为 received / missing / rejected 状态。

下一步必须进入 callback review decision：基于 callback intake 的材料状态，判断：

- `ready_for_controlled_field_rerun`
- `needs_material_backfill`
- `evidence_ref_mismatch_rerun`
- owner handoff 和 next required evidence

## 3. OKR rerank 依据

- Objective 5 当前约 68%，是 `OKR.md` 4.1 的数值最低 Objective；但本机没有公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 外部材料，O5 stop rule 继续成立。
- Objective 1 当前约 81%，仍缺真实 WAVE ROVER、UART、HIL packet、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery` 和 operator HIL report；最近 `wave_rover_hil_packet_*` 已反复消费同一缺真实硬件 blocker，本轮不能继续本地包装同一 blocker。
- PR #4 已把 elevator-assisted delivery 设为主链必须能力；PR #5 review 指出 hardware baseline / vendor source / 2D LiDAR / ToF 风险，但真实硬件材料仍不可用。
- 因此本轮从 O5/O1 rerank 到 Objective 2 / Objective 3 的 route/elevator acceptance execution callback review decision，继续把真实现场复跑前的材料复核链补齐。

## 4. 用户价值和产品北极星

用户价值：现场 owner 回传 callback packet 后，产品和工程团队不再只看到 received / missing / rejected 的材料清单，而是得到下一步明确决策：能否进入受控现场复跑、需要谁补哪些材料、是否因为同一 `evidence_ref` 不一致必须重跑。

产品北极星：继续服务“普通手机用户可完成低成本 trash delivery”的主线，但本轮只推进现场材料复账和执行决策，不声称真实送达、真实电梯运行或真实手机验收完成。

## 5. 本轮核心抓手

把上一轮 callback intake 产物提升为 review decision gate，并同步在 Robot diagnostics 与 mobile/web 只读展示中保留同一证据边界。

必须保持：

- `software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_decision_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- 不写成真实 route/elevator field pass、Nav2/fixed-route proof、task record/completion signal、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## 6. 并行 owner 和文件范围

### Autonomy Algorithm Engineer

- 目标：新增 PC gate，读取上一轮 acceptance execution callback intake artifact / summary，输出 review decision。
- 文件范围：`pc-tools/evidence/`、`tests/` 中与 `route_task_field_retest_acceptance_execution_callback_review_decision` 直接相关的新文件或测试。

### Robot Platform Engineer

- 目标：在 diagnostics 中新增 safe alias，保持 schema/boundary/status/phone-safe whitelist。
- 文件范围：`onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py` 与对应 diagnostics focused tests。

### User Touchpoint Full-Stack Engineer

- 目标：在 `mobile/web` 增加只读 review decision panel，不改变 Start Delivery、Confirm Dropoff、Cancel gating。
- 文件范围：`mobile/web/`、`mobile/fixtures/` 与 mobile focused tests。

### Product Manager / OKR Owner

- 目标：implementation 完成后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和必要的 `docs/` / process progress 文档。
- 文件范围：后续 closeout 阶段再限定，不在本轮 planning 文件中提前改动。

## 7. 阻塞和风险

- O5 外部材料仍不可用，不能把本轮 Docker/local software proof 写成公网云、4G、OSS/CDN、production DB/queue、worker/cutover 或真实手机/browser proof。
- O1 真实硬件材料仍不可用，不能把本轮写成 WAVE ROVER、UART 或 HIL 进展。
- PR #5 hardware baseline / vendor source / 2D LiDAR / ToF 风险仍待真实 source、receipt、采购、安装、接线、电源、标定和 HIL-entry 材料。
- 如果 callback intake 输入缺失、schema/boundary 不支持、unsafe copy、`evidence_ref` mismatch、`delivery_success=true` 或 `primary_actions_enabled=true`，review decision 必须 fail closed。

## 8. 本轮需要创建或更新的 sprint 文档

- 当前已创建规划文档：`pre_start.md`、`prd.md`、`tech-plan.md`
- 实现完成后必须更新：`tech-done.md`
- Epic 验收和复盘必须更新：`side2side_check.md`、`final.md`
