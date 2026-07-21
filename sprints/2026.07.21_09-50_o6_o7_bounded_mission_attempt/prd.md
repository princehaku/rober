# PRD：O6/O7 current bounded mission attempt

## 用户价值与产品北极星

用户需要的不是另一个 readiness 面板，而是一次可追溯、可停止、失败可解释的真实路线任务：用户动作被上位机接收，机器人在 operator 看护下执行一个受限目标，最终能看到 goal terminal result、路线进度、停止状态与证据边界。

## OKR 映射与方向判断

- O5 约 `85%`：provider/runtime `2/2`，继续暂停。
- O6 约 `93%`：本轮消费 current task/route execution material，若形成 bounded mission attempt 可产生比 archive/readback 更高的证据等级。
- O7 约 `93%`：本轮必须产生 current `user_action` receipt 与 terminal result，不用 loopback UI 证据替代。
- O1 约 `95%`：pre/post stop 与 T=1001 是 safety/support evidence；没有 wheel HIL acceptance 就不调整 O1。
- 方向：继续 O6/O7，停止 wrapper/readback-only 迭代。KR 默认 `不归档`，百分比由 Product 基于冻结证据保守判断。

## 需求

### R1：只读 Phase 0

必须在目标机当前服务不变的前提下检查：

- target SHA、Upper health、既有 base/LiDAR service active 与 holder identity；
- `/scan` current、canonical map、current/persisted pose、dynamic `map->odom` 与 `map->base_link`；
- planner/controller lifecycle、planner-only path、current obstacle clear；
- `NavigateToPose` action server、base stop endpoint、feedback-samples endpoint；
- route/task window 无并发任务，所有 run-owned residual 为 `0`。

任一失败必须 `READINESS_GO=false`，不得进入 live action pipe，不得换 wrapper 重跑。

### R2：唯一 live action pipe

Phase 0 全绿后，Robot owner 在一个冻结脚本/manifest 中按固定顺序执行：

1. pre-stop；
2. 写入唯一 `user_action` / task receipt；
3. exactly-one `NavigateToPose map (0.8, 0.25, yaw=0)`；
4. 采集 goal accepted、feedback/route progress、terminal result 与同窗 T=1001；
5. post-stop；
6. cancel（仅当 goal 仍 active）与 run-owned cleanup；
7. 冻结 final manifest 和原始响应。

进入第 1 步即消费本轮授权。不得 retry、第二 goal、manual、direct `/cmd_vel`、`/initialpose`、UART/firmware/service mutation。

### R3：证据合同

最终 `mission_attempt_manifest.json` 至少包含：

- `schema=trashbot.o6_o7.current_bounded_mission_attempt.v1`；
- `task_id`、`action_id`、target pose/frame、authorisation id 与 consumed state；
- Phase 0 九门或更严格门禁、`READINESS_GO`；
- pre-stop/goal/post-stop/cancel 的 invocation counts、HTTP/action status、timestamps；
- `user_action_receipt`、goal accepted、feedback count、route progress、terminal status；
- same-window T=1001 counts/latest L/R、final base status；
- service/UART/firmware/manual/direct-cmd_vel/initialpose mutation counts；
- cleanup state、residual processes、所有 safety/mission/delivery/HIL 字段。

Artifact 可记录 NO-GO、attempt、success 或 terminal failure，但不能用字段缺失冒充 false，也不能用历史材料补 current gap。

## 验收口径

- Planning：三文档结构检查和 `git diff --check` 通过。
- Software：目标脚本/Upper/O11 单测、py_compile、JSON assertions、中文注释比例和 scoped diff 全绿。
- Live Phase 0：只读、service mutation `0`、UART open/write `0`；GO 才能执行。
- Live action：pre-stop=`1`、goal=`1`、post-stop=`1`，retry=`0`、second goal=`0`，并有 frozen current artifacts。
- Cleanup：goal 非 active、run-owned residual=`0`、既有 services/holders 保持、最终 stop 可核查。
- Product：Algorithm frozen review 后再判 `mission_attempt` / `route_execution_success`；`delivery_success`、`hil_pass`、`safe_to_control` 默认 false。

## Owner 与协作

- `robot-software-engineer`：唯一实现、测试、部署与 live owner，负责 stop/goal/evidence/cleanup 单线闭环和 `tech-done.md`。
- `robot-algorithm-engineer`：不得并行调用 live endpoint；仅在 primary manifest 冻结后做只读 GO/NO-GO、target/path/terminal semantics 复核，并写 review artifact。
- `product-okr-owner`：side-to-side、OKR/进度日志与 final conservative closeout。

## 风险

- 当前服务复用可能仍缺 planner/controller/action readiness；按 Phase 0 NO-GO 收口，不动 service。
- goal 执行可能 timeout/reject/abort；必须 post-stop、cancel active goal 并保留 terminal failure，禁止 retry。
- T=1001 可能仍为 L/R=0；只作为同窗 safety material，不因此声称 HIL。
- SSH、网络或 Upper 响应中断时，只允许 cleanup 路径；无法确认 stop 时必须显式 `stop_confirmation_missing`，不得宣称安全完成。
