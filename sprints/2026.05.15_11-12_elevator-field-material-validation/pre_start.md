# Sprint 2026.05.15_11-12 Elevator Field Material Validation - Pre Start

sprint_type: epic

## 1. 启动依据

- 当前 `OKR.md` 4.1 显示 Objective 5 最低，约 66%，但 `OKR.md` 第 6 节明确写明：没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 材料时，不应继续堆本地 O5 metadata depth。
- 最新 sprint `2026.05.15_10-11_elevator-assist-default-mainline` 已把 Objective 2 电梯 assisted delivery 从默认关闭推进到默认 dry-run 主链路，收口边界是 `software_proof_docker_elevator_assist_default_mainline_gate`，不是现实电梯、真实 Nav2/fixed-route、WAVE ROVER/HIL 或 delivery success。
- 用户本轮明确约束“本机没有真实硬件，只有docker”，因此不能消费 `no_real_hardware_or_serial` blocker 作为实机收口；本轮只做下一次受控楼宇实测前的材料接收/校验/只读展示能力。

## 2. 本轮目标

把 Objective 2 的“受控楼宇现场补证”从口头缺口推进为可机器校验的软件材料链：

- PC/Autonomy 侧生成 `elevator_field_run_material_validation` artifact，校验门状态、目标楼层、人工协助、路线运行日志、task record、completion signal 和 mobile/support summary 是否同一 `evidence_ref`、是否仍是模板、是否越界宣称成功。
- Robot diagnostics 侧只读消费该 artifact/summary，保持 `delivery_success=false`、`primary_actions_enabled=false`、`not_proven` 和 phone-safe redaction。
- Mobile 侧只读展示“电梯现场材料校验”，让普通用户/支持人员知道下一次现场实测还缺哪些材料，但不放行 Start/Confirm/Cancel。
- Product 侧更新 sprint closeout、`OKR.md` 与 `docs/process/okr_progress_log.md`，把本轮归类为 Docker/local software proof。

## 3. Owner 与并行方式

- `autonomy-engineer`：主责 PC material validation CLI/schema/test/docs，文件范围限 `pc-tools/evidence/`、`pc-tools/README.md`、`docs/navigation/` 或 `docs/product/elevator_assisted_delivery.md` 的相关小节。
- `robot-software-engineer`：主责 operator diagnostics metadata-only consumption，文件范围限 `onboard/src/ros2_trashbot_behavior/` 相关 diagnostics/test 与 `docs/interfaces/ros_contracts.md`。
- `full-stack-software-engineer`：主责 `mobile/web` 只读 panel/fixture/test 与 `docs/product/mobile_user_flow.md`。
- `product-okr-owner`：主责 closeout、OKR 和 progress log。产品只在工程结果返回后更新，不替代工程交付。

## 4. 边界

- 不访问真实 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、真实喇叭/TTS、外部云、OSS/CDN、DB/queue 或 4G。
- 不新增真实手机设备/browser、production app、真实 PWA prompt/user choice 证据。
- 不新增广泛回归测试；只跑本轮 touched files 的 py_compile、unittest、node check、required rg 和 scoped diff check。

## 5. Blocker 扫描

- 最近两轮的主要缺口不是同一条可由 Docker 解决的 blocker：`10-11` 缺真实电梯/硬件/现场材料；`09-10` 缺真实 route/task field run 材料。
- 本轮不把这些 blocker 写成已解决，只把现场材料校验能力向前推进，避免第三轮重复消费真实硬件/现场不可用的 blocker。
