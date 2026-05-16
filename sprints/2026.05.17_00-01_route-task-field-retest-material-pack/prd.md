# Sprint 2026.05.17_00-01 Route Task Field Retest Material Pack - PRD

sprint_type: epic

## 1. 用户价值和产品北极星

本轮产品价值是把现场复测材料从“聊天里说缺什么”升级为“现场人员可按目录提交、PC 可校验打包、Robot/mobile 可只读解释”的材料包闭环。它服务于普通现场人员和支持同学：他们不需要理解 ROS2、Nav2、fixed route、task record、raw JSON、串口或云链路，只需要按八类材料填充目录并运行一个 dependency-free 工具。

产品北极星保持不变：`rober` 要成为普通手机用户可以理解、现场支持人员可以复账、工程团队可以追溯的低成本 ROS2 自主垃圾投递机器人。本轮不是追求更多 UI 或更多 wrapper，而是让同一 `evidence_ref` 的真实现场材料可以进入后续 `result_intake` / `result_reconciliation`，为 Objective 2 / Objective 3 的真实路线/任务材料补证打基础。

## 2. OKR 映射

- Objective 2：可送垃圾任务 + 电梯 assisted delivery 必达闭环。本轮补齐真实 field retest material pack 的入口，直接服务 `door_state`、`target_floor_confirmation`、`human_assistance_note`、dropoff/cancel completion、delivery_result 的同一 `evidence_ref` 回填。
- Objective 3：可验证导航与固定路线。本轮要求现场目录包含 `nav2_or_fixed_route_runtime_log`、`route_completion_signal`、`task_record`，让 fixed-route / Nav2 运行材料可被打包、校验、复账。
- Objective 4：手机用户体验与低成本量产边界。本轮让 mobile/web 只读解释 material completeness、same evidence ref、missing/rejected 和 operator next steps，不改变控制授权。
- Objective 5：当前数值最低但本轮不推进。原因是没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration；继续堆 Docker-only Objective 5 metadata 不会形成真实 O5 completion。

## 3. KR 拆解或更新

本轮不直接更新 `OKR.md` 数值；实现阶段完成后由 Task D 在 closeout 根据证据保守判断。

计划拆解：

- KR-O2-field-material：八类现场材料必须以同一 `evidence_ref` 进入 material pack summary；缺失、placeholder-only、unsafe success phrasing、raw path、credential 均 fail closed。
- KR-O3-route-material：Nav2/fixed-route runtime log、route completion signal、task_record 必须作为一组可复账材料被检测和汇总。
- KR-O4-phone-safe-material：手机端只读展示 material completeness、same evidence ref、八类材料状态、missing/rejected、operator next steps，并保留 `delivery_success=false`、`primary_actions_enabled=false`。
- KR-boundary：证据边界固定为 `software_proof_docker_route_task_field_retest_material_pack_gate`，没有真实材料时只能是 fixture/software proof。

## 4. 本轮核心抓手

核心抓手是一个现场人员可执行的 route/task field retest material pack：

1. Autonomy 提供 dependency-free PC CLI，读取 material dir，校验八类材料和同一 `evidence_ref`。
2. Robot diagnostics 只读消费 material pack summary，让 operator gateway 可以 fail closed 显示材料包状态。
3. Full-stack 在 mobile/web 增加只读 panel，解释哪些材料已齐、哪些缺失或被拒绝、下一步怎么补。
4. Product 在三方返回后收口 sprint、更新 OKR 进度和 process log，但不得把软件证明写成真实通过。

## 5. 范围边界

必须做：

- 输出 schema `trashbot.route_task_field_retest_material_pack.v1` 与 summary。
- 覆盖八类材料：
  - `nav2_or_fixed_route_runtime_log`
  - `route_completion_signal`
  - `task_record`
  - `door_state`
  - `target_floor_confirmation`
  - `human_assistance_note`
  - `dropoff_or_cancel_completion`
  - `delivery_result`
- 校验同一 `evidence_ref`。
- 拒绝 placeholder-only、raw path、credential、unsafe success phrasing、`delivery_success=true`、`primary_actions_enabled=true`。
- 保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

不得做：

- 不改变 collect/dropoff/cancel/ACK/Nav2/HIL/delivery success 语义。
- 不把 fixture、summary、ACK、completion signal 或 software proof 宣称为 field pass。
- 不引入真实硬件假设，不新增 WAVE ROVER、UART、波特率、引脚、电压或硬件配置结论。
- 不暴露 raw path、credential、完整 artifact、traceback、checksum、raw ROS topic、`/cmd_vel` 或串口/UART 细节到 phone-safe surface。

## 6. 优先级和验收口径

P0：

- PC CLI 能在无外部依赖环境读取 material dir、输出 artifact/summary，并 fail closed。
- Robot diagnostics 和 mobile/web 均只读消费 summary，不扩大控制权限。
- `software_proof_docker_route_task_field_retest_material_pack_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false` 在 PC/Robot/mobile/docs 中一致。

P1：

- 文档同步 `pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md`。
- 测试围栏只跑 focused unittest、`py_compile`、`node --check`、required `rg` 和 scoped `git diff --check`。

P2：

- 如果现场真实材料仍缺，fixture 必须明确是 fixture；operator next steps 要指导如何补齐真实八类材料。

## 7. 对应责任 Engineer

- Task A：Autonomy Algorithm Engineer。
- Task B：Robot Platform Engineer。
- Task C：User Touchpoint Full-Stack Engineer。
- Task D：Product Manager / OKR Owner。

Task A、B、C 文件范围互不重叠，实施阶段应并行派发 3 个 Engineer workers；Task D 在三方完成后执行 closeout。

## 8. 风险、阻塞和证据链

- Docker-only 环境不能证明真实 field pass、真实 Nav2/fixed-route、真实电梯、真实 phone/browser、HIL、WAVE ROVER 或 Objective 5 external proof。
- PR #4 的真实 `door_state`、`target_floor_confirmation`、`human_assistance_note` 仍是核心证据缺口；本轮只能提供材料包入口和 fail-closed 校验。
- PR #5 的硬件/source/procurement/install/wiring/power/calibration/HIL-entry 缺口仍存在；但最近两轮已消费同一 blocker，本轮不继续硬件 wrapper。
- 如果后续拿到真实材料，必须用同一 `evidence_ref` 重新跑 material pack、result intake 和 result reconciliation，才能讨论 Objective 2 / Objective 3 的真实进度。
