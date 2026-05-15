# Sprint 2026.05.15_13-14 Elevator Field Rehearsal Execution Pack - Pre Start

sprint_type: epic

## 1. 启动依据

- 当前 `OKR.md` 4.1 显示 Objective 5 最低，约 66%，但第 6 节明确要求只有拿到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 worker/migration 证据时才继续推进 O5 completion。本机只有 Docker，没有这些外部材料，因此本轮不继续叠本地 O5 metadata depth。
- 最新 sprint `2026.05.15_12-13_elevator-field-run-review-decision` 已完成 `software_proof_docker_elevator_field_review_decision_gate`，能把电梯现场材料 validation 转成 review decision、blocked categories、operator next steps、commands to rerun 和 capture checklist。
- 最新 final 的下一步明确要求围绕 O2/O3 做真实现场材料回填或上车复账；在当前 Docker-only 主机上，可行动的软件下一步是把 review decision 整理成可交给现场同学执行的受控电梯演练执行包，并继续保持 `not_proven`、`delivery_success=false` 和只读控制边界。
- 本轮继续遵守用户约束：“本机没有真实硬件，只有docker”。不访问真实电梯、真实串口、WAVE ROVER、Nav2 runtime、外部云或真实手机设备。

## 2. 本轮目标

把 Objective 2/O3 的电梯 assisted delivery 现场补证链，从“复核决策”推进到“受控现场演练执行包”：

- Autonomy/PC 侧新增 `elevator_field_run_execution_pack` CLI，读取上一轮 review artifact/summary，输出 `trashbot.elevator_field_run_execution_pack.v1` 和 summary。
- Robot diagnostics 侧只读消费 execution pack artifact/summary，继续固定 `delivery_success=false`、`primary_actions_enabled=false`，不触发 collect/dropoff/cancel、ACK、Nav2、HIL 或真实送达。
- Mobile 侧新增只读“电梯演练执行包” panel，展示 safe evidence ref、执行包状态、现场采集清单、首跑/复跑命令和 not_proven，不改变 Start/Confirm/Cancel gating。
- Product 侧在工程结果后更新 sprint closeout、`OKR.md` 和 `docs/process/okr_progress_log.md`，只按 Docker/local software proof 保守更新 O2/O3，不上调 O5。

## 3. Owner 与并行方式

- `autonomy-engineer`：主责 PC execution pack CLI/schema/test/docs，文件范围限 `pc-tools/evidence/`、`pc-tools/README.md`、`docs/product/elevator_assisted_delivery.md`，必要时补 `docs/navigation/fixed_route_workflow.md`。
- `robot-software-engineer`：主责 operator diagnostics metadata-only consumption，文件范围限 `onboard/src/ros2_trashbot_behavior/` 相关 diagnostics/test 与 `docs/interfaces/ros_contracts.md`。
- `full-stack-software-engineer`：主责 `mobile/web` 只读 panel/fixture/test 与 `docs/product/mobile_user_flow.md`。
- `product-okr-owner`：工程线完成后主责 closeout、OKR 和 progress log。

## 4. 边界

- 不访问真实 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、真实喇叭/TTS、外部云、OSS/CDN、DB/queue 或 4G。
- 不新增真实手机设备/browser、production app、真实 PWA prompt/user choice 证据。
- 不把 execution pack 写成真实送达、真实投放、真实取消完成、HIL 或 O5 external proof。
- 只跑本轮 touched files 的 py_compile、focused unittest、node check、required rg 和 scoped diff check。

## 5. Blocker 扫描

- O5 外部材料 blocker 已连续多轮存在，本轮按 `OKR.md` 第 6 节和最新 final 继续切换到可行动的 O2/O3。
- O1 硬件/HIL blocker 在本机仍不可解，本轮不消费真实串口或 WAVE ROVER。
- O2/O3 仍有 Docker/local 可推进项：把上一轮 review decision 转成现场执行包、diagnostics 只读摘要和手机安全展示，让现场同学下一次能按同一 `evidence_ref` 补真实材料。
