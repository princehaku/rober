# PRD：O6/O7 corrected Phase 0 bounded mission

## 用户价值与产品北极星

本轮要把用户的当前授权变成一次可追溯、可停止、失败可解释的真实路线任务，而不是再产出 readiness 包装。用户应能看到 current task/user-action receipt、goal accepted/terminal、路线进度、同窗底盘反馈、最终停止与 cleanup 的同一证据链。

## OKR 映射与方向判断

- O5 约 `85%`：provider/runtime `2/2`，继续暂停。
- O6/O7 各约 `93%`：继续；本轮只以 current bounded mission attempt 或更强现场证据计增量。
- O1 约 `95%`：pre/post stop 和 T=1001 只作安全支撑；没有合格轮速/HIL 不提升。
- Mission Objective 0：只有 current goal attempt、route progress 与 stop/cleanup 对齐才可进入 `C2 bounded_mission_attempt`；Phase 0 NO-GO、代码、测试或历史 latest 均不计。
- KR 默认 `不归档`；Product 只能按冻结证据保守调整百分比。

## R1：corrected Phase 0

必须恰好执行一次，并满足：

1. source `/opt/ros/humble/setup.bash`，如存在则 source `/root/rober/onboard/install/setup.bash`；证明 `ros2` 可用。
2. 以当前进程事实探测 Upper：PID、命令行、监听 `8787`、`GET /api/health`、current task/goal/latest 状态与所需 endpoint/capability。`trashbot-upper-api.service` inactive 本身不是 NO-GO；只有 PID/listener/health/capability/ownership 任一不一致才 NO-GO。
3. Upper local/remote SHA mismatch 不得被忽略，也不得靠 deploy 修复。必须从远端当前 source/route registration、GET readback 或安全的 HTTP capability response 证明本轮依赖的 health、nav2 latest/execute、base stop、feedback sample 合同存在；证据不足即 NO-GO。
4. 既有 ESP32/LiDAR services 与 `/dev/ttyS5`、`/dev/ttyACM0` holders 不变；本轮新开/写 UART 为 `0`。
5. current task/goal 无并发，map、scan、pose、dynamic TF、planner/controller lifecycle、planner-only path、obstacle clear、NavigateToPose action、stop 与 feedback readback 门全部为 current 且全绿。
6. Phase 0 禁止 service mutation、远端写文件/deploy、action goal、topic pub、manual、direct `/cmd_vel`、UART/firmware 和 `/initialpose`。

## R2：唯一 live action pipe

Phase 0 全绿后，冻结 request body、target、task/action ID、authorization ID 和 pre-state，并在一个不可重入的执行器中按顺序完成：

1. pre-stop `1`，同时标记授权已消费；
2. current user-action/task receipt `1`；
3. exactly-one `NavigateToPose` 到 `map (0.8, 0.25, yaw=0)`；
4. bounded 采集 goal accepted、feedback、route progress、terminal result 与同窗 T=1001；
5. post-stop `1`；
6. 仅当 goal 仍 active 时 cancel，然后做 run-owned cleanup；
7. 冻结 raw responses 与 final manifest。

`retry_count=0`、`second_goal_count=0`。网络、action 或 readback 失败后不能重新进入 pipe。

## R3：证据合同

最终 artifact 至少显式记录：

- schema、task/action/authorization、target、时间窗、current remote SHA/capability 摘要；
- Phase 0 每个 gate、命令类别、exit/HTTP status、freshness 与 first failure；
- pre-stop/user receipt/goal/post-stop/cancel/feedback 的 invocation count；
- goal accepted、feedback count、route progress、terminal status；
- same-window T=1001 observed/nonzero/latest L/R 与 final base readback；
- service mutation、remote write/deploy、UART open/write、firmware、initialpose、manual、direct cmd_vel、retry、second goal 全部计数；
- cleanup、goal active、run-owned residual、existing holder preservation；
- `mission_attempt`、`route_execution_success`、`delivery_success`、`hil_pass`、`safe_to_control`，禁止用字段缺失代表 false。

## 验收口径

- 离线：py_compile、目标单测、manifest assertions、中文技术注释比例 `>20%`、scoped diff 全绿。
- Phase 0 NO-GO：`phase0=1`，pre-stop/receipt/goal/post-stop=`0/0/0/0`，授权未消费，危险计数全 `0`。
- Attempt：pre-stop/receipt/goal/post-stop=`1/1/1/1`，goal 有 current accepted/feedback/terminal 材料，retry/second goal=`0/0`，cleanup clean。
- Success 候选：除 attempt 条件外，还需 terminal success、route progress 与 final stopped 一致。
- `delivery_success`、`hil_pass`、`safe_to_control` 默认 false；由 Product 仅在独立 current 材料充分时复核。

## 风险与 2/2 停止规则

- 当前进程可能缺少本轮依赖 endpoint，Nav2/localization/path/action 也可能不绿；按 NO-GO 封存，禁止临场部署或 service 修复。
- 同一 endpoint/ROS env/SHA/service ownership 根因若再次导致 NO-GO，即达到 `2/2`；下一轮必须切 Objective 或升级 CEO。
- SSH 中断且无法确认动作后 stop 时，写 `stop_confirmation_missing` 并由 operator 现场接管；不得声称 clean completion。
