# Sprint 2026.05.15_12-13 Elevator Field Run Review Decision - Pre Start

sprint_type: epic

## 1. 启动依据

- 当前 `OKR.md` 4.1 显示 Objective 5 最低，约 66%，但第 6 节明确要求：只有拿到真实外部材料（公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration）才继续推进 O5 completion。本机只有 Docker，因此本轮不继续堆 O5 本地 metadata depth。
- 最新 sprint `2026.05.15_11-12_elevator-field-material-validation` 已完成 `software_proof_docker_elevator_field_material_validation_gate`，能校验电梯现场材料目录，但 final 明确下一步仍需要人工复核和现场材料回填；它不是真实电梯、HIL、Nav2/fixed-route 实跑或 delivery success。
- 最近两轮 review/final 反复出现的问题是：材料 gate 能生成 blocked/not_proven 摘要，但现场同学还缺一个可执行的“复核决策 + 复跑清单”，把 missing/template/mismatch/unsafe/success-claim 状态转成下一步动作。
- 用户本轮约束“本机没有真实硬件，只有docker”，因此本轮只做 Docker/local software proof，不碰真实串口、WAVE ROVER、真实电梯或外部云。

## 2. 本轮目标

把 Objective 2/O3 的电梯 assisted delivery 现场补证链，从“材料校验 artifact”推进到“人工复核决策和复跑指令”：

- Autonomy/PC 侧新增 `elevator_field_run_review` CLI，读取上一轮 validation artifact，输出 `trashbot.elevator_field_run_review.v1` 和 summary。
- Robot diagnostics 侧只读消费 review artifact/summary，继续固定 `delivery_success=false`、`primary_actions_enabled=false` 和 metadata-only 边界。
- Mobile 侧新增只读“电梯现场复核决策” panel，展示 review decision、safe evidence ref、blocked categories、operator next steps 和 not_proven，不改变 Start/Confirm/Cancel gating。
- Product 侧在工程结果后更新 sprint closeout、`OKR.md` 和 `docs/process/okr_progress_log.md`，只按软件证明保守更新 O2/O3，不上调 O5。

## 3. Owner 与并行方式

- `autonomy-engineer`：主责 PC review decision CLI/schema/test/docs，文件范围限 `pc-tools/evidence/`、`pc-tools/README.md`、`docs/navigation/`、`docs/product/elevator_assisted_delivery.md` 的相关小节。
- `robot-software-engineer`：主责 operator diagnostics metadata-only consumption，文件范围限 `onboard/src/ros2_trashbot_behavior/` 相关 diagnostics/test 与 `docs/interfaces/ros_contracts.md`。
- `full-stack-software-engineer`：主责 `mobile/web` 只读 panel/fixture/test 与 `docs/product/mobile_user_flow.md`。
- `product-okr-owner`：主责 closeout、OKR 和 progress log，在三条工程线完成后收口。

## 4. 边界

- 不访问真实 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、真实喇叭/TTS、外部云、OSS/CDN、DB/queue 或 4G。
- 不新增真实手机设备/browser、production app、真实 PWA prompt/user choice 证据。
- 不把 validation/review decision 写成真实送达、真实投放、真实取消完成、HIL 或 O5 external proof。
- 只跑本轮 touched files 的 py_compile、focused unittest、node check、required rg 和 scoped diff check。

## 5. Blocker 扫描

- O5 外部材料 blocker 已在最近多轮被记录，本轮按 `OKR.md` 第 6 节明确切换到可行动的 O2/O3。
- O1 硬件/HIL blocker 在本机仍不可解，本轮不尝试消费真实串口或 WAVE ROVER。
- O2/O3 仍有 Docker/local 可推进项：把上一轮 validation artifact 转成现场复核决策、复跑清单和手机/diagnostics 只读解释。
