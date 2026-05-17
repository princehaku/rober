# Sprint 2026.05.18_01-02 Route Task Result Review Intake - Pre Start

sprint_type: epic

## 1. 本轮定位

本轮能力命名：`route_task_field_retest_result_review_intake`。

目标：承接上一轮 `route_task_field_retest_result_callback_review_handoff`，把 result review 前 handoff 消费为 result review intake / metadata gate。该 gate 只做软件侧材料入口、跨面 summary、只读手机面板和 fail-closed 复核入口，不宣称真实 route/elevator field pass、真实 Nav2/fixed-route、真实手机/browser、HIL 或 Objective 5 external proof。

证据边界必须固定为：`software_proof_docker_route_task_field_retest_result_review_intake_gate`。

## 2. 用户价值和产品北极星

用户价值：现场支持和后续评审人员能在真正 result review 前看到同一 `evidence_ref` 的材料入口是否可进入复核、哪些字段缺失、哪些 owner 要补材料、哪些情况必须 rerun，而不是把 handoff 文件误当成交付成功。

产品北极星：把 `rober` 推进到“低成本 ROS2 垃圾投递机器人可验证地可靠交付垃圾”。本轮只推进 PR #4 route/elevator result chain 的可复核证据链，不越过真实路线、真实电梯、真实硬件、真实手机和真实公网云证据边界。

## 3. 开工证据

- `OKR.md` 4.1 当前快照：Objective 5 约 68%，数值最低；但继续推进需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover 或真实手机/browser external proof，本 Docker-only 主机不能推进。
- `OKR.md` 4.1 当前快照：Objective 1 约 81%，次低；但最近三轮已围绕 WAVE ROVER HIL packet intake/review/execution-pack 消费同一真实硬件 blocker，本轮不能第三次包装同一 blocker。
- `OKR.md` 4.1 当前快照：Objective 2 / Objective 3 / Objective 4 均约 99%，但 PR #4 的真实 route/elevator field materials 仍缺，尤其是真实电梯门状态、真实楼层确认、人工协助记录、Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion 和 delivery result。
- GitHub PR #4：把 elevator-assisted delivery 写入 agents、registry 和 `OKR.md`，推动 O2/O3 route/elevator 证据链；该 PR 明确未执行 runtime integration tests。
- GitHub PR #5：把 elevator assisted delivery 设为 required MVP，并提出 monocular camera + 2D LiDAR + ToF safety ring、参数化传感器配置和硬件材料边界；近期 sprint 已多次指出真实 2D LiDAR / ToF SKU/source/receipt/install/wiring/calibration/HIL-entry 材料缺失。
- 最新 sprint `sprints/2026.05.18_00-01_route-task-result-callback-review-handoff/final.md`：上一轮完成 `software_proof_docker_route_task_field_retest_result_callback_review_handoff_gate`，把 callback review decision 转成 result review 前 handoff；下一步需要把 handoff 消费为 result review intake。

## 4. Blocker 重复消费核对

- Objective 5 blocker：真实公网、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser external proof 不在本 Docker-only 主机可完成范围内。本轮不继续堆本地 O5 metadata depth。
- Objective 1 blocker：真实 WAVE ROVER、UART、串口日志、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery` 和 operator HIL report 仍缺，且最近三轮已经消费同一 HIL packet blocker。本轮不重复包装。
- 本轮切换到 Objective 2 / Objective 3 的原因：PR #4 route/elevator result chain 仍有可本地推进的 result review intake / metadata gate，能把上一轮 handoff 变成可执行 intake 入口，并为真实现场材料回填留出严格边界。

## 5. 本轮核心抓手

建立 `route_task_field_retest_result_review_intake` 三面 contract：

1. Autonomy 生成 PC gate，校验上一轮 handoff summary，输出 result review intake artifact / summary。
2. Robot diagnostics 只读消费该 summary，保持 metadata-only、fail-closed。
3. mobile/web 只读展示 review intake panel，不改变 Start Delivery、Confirm Dropoff、Cancel gating。
4. Product closeout 只在实现和验证完成后更新 `OKR.md`、`docs/process/okr_progress_log.md` 与 sprint closeout 文档。

## 6. 责任分工

- Autonomy Algorithm Engineer：主责 PC gate、focused unittest、`docs/interfaces/evidence_contracts.md`。
- Robot Platform Engineer：主责 `operator_gateway_diagnostics.py` metadata-only consumer、diagnostics test、`docs/interfaces/ros_contracts.md`。
- User Touchpoint Full-Stack Engineer：主责 `mobile/web/app.js` read-only panel、fixture/test、`docs/product/mobile_user_flow.md`。
- Product Manager / OKR Owner：closeout 阶段核对证据边界，更新 `OKR.md`、`docs/process/okr_progress_log.md`、本 sprint `tech-done.md` / `side2side_check.md` / `final.md`。

## 7. 计划文档链路

本轮为 Epic sprint，必须按顺序维护：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`
- `tech-done.md`
- `side2side_check.md`
- `final.md`

本任务只创建前三个计划文件，不修改产品代码、测试、`OKR.md` 或 `docs/process/`。
