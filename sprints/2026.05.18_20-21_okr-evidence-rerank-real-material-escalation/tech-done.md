# Sprint 2026.05.18_20-21 OKR Evidence Rerank Real Material Escalation - Tech Done

## 1. Sprint 声明

- sprint_type: epic
- 收口时间：2026-05-18 20:38 Asia/Shanghai
- 本轮类型：PR / review / OKR evidence rerank 与真实材料升级决策。
- 证据边界：`source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. 实际完成

- 主会话读取 `OKR.md`、最新 18-19 / 19-20 sprint final、20-21 planning docs、GitHub PR #4 / PR #5 metadata 与 PR #5 review comments。
- 并行派发三个只读 owner fact-check worker：
  - Hardware Infra Engineer：核对 `docs/vendor/VENDOR_INDEX.md` 与 `docs/product/production_hardware_boundary.md`。
  - Autonomy Algorithm Engineer：核对最近两轮 PR #4 route/elevator 真实现场材料缺口。
  - User Touchpoint Full-Stack Engineer：核对 O4 真机 / production app / PWA prompt 材料边界和 Start / Confirm / Cancel fail-closed 规则。
- 本轮没有新增产品代码、测试代码、硬件配置或本地 route/elevator wrapper。
- 本轮不上调 `OKR.md` 完成度。

## 3. 证据结论

### Objective 5

`OKR.md` 4.1 当前最低仍为 Objective 5，约 68%。本机没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser external proof。O5 stop rule 继续成立，不应继续堆本地 metadata depth。

### Objective 1 / PR #5

Hardware worker 只读确认：本地 vendor tree 能证明 Orange Pi Zero 3、WAVE ROVER、ESP32 firmware、UART newline-delimited JSON、机械资料和 vendor app reference coverage；不证明项目 2D LiDAR 或 ToF SKU/source、receipt、procurement、mounting、wiring、power、calibration、HIL-entry、Nav2/SLAM field pass、near-field safety pass 或 delivery result。

O1 / PR #5 保持 `hardware_material_pending`、`not_proven`。下一步真实材料最小包包括 WAVE ROVER/UART/HIL packet、`feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`、operator HIL report，以及 2D LiDAR / ToF SKU、vendor/source、receipt/procurement、installation、wiring、power budget、calibration、HIL-entry evidence。

### Objective 2 / Objective 3 / PR #4

Autonomy worker 只读确认：18-19 和 19-20 已连续消费同一 PR #4 route/elevator 真实现场材料缺口。下一步最小现场材料包必须包括真实电梯门状态、真实目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion 或 delivery result、diagnostics/mobile safe summary，并共享同一 safe `evidence_ref`。

继续新增 `route_task_field_retest_acceptance_execution_rerun_result_*` 本地 wrapper 只会证明 repo 内 fail-closed 流转，不会产生真实电梯、真实路线、真实投放或真实送达证据。

### Objective 4

Full-stack worker 只读确认：O4 下一步可执行改道是进入真实手机材料链路，最小材料包包括真实 iPhone/Android device behavior、production app URL 或 release summary、真实 PWA install prompt / user choice 观察结果、截图或 observer note、browser metadata。材料完整只代表可以进入真实手机材料评审，不代表 `safe_to_control=true`，Start Delivery / Confirm Dropoff / Cancel 仍由 command safety、readiness、action feedback / ACK fail-closed。

## 4. 验证结果

Owner workers 已运行各自只读围栏命令：

- Hardware：`rg -n "Orange Pi Zero 3|WAVE ROVER|UART|newline-delimited JSON|2D LiDAR|ToF|not prove|hardware_material_pending" docs/vendor/VENDOR_INDEX.md docs/product/production_hardware_boundary.md`，exit 0。
- Autonomy：`rg -n "真实电梯门状态|真实楼层确认|人工协助记录|Nav2/fixed-route runtime log|task record|completion signal|dropoff/cancel completion|delivery result|same.*evidence_ref|software_proof" ...`，exit 0。
- Full-stack：`rg -n "mobile_real_device|production app|PWA install prompt|user choice|safe_to_control=false|not_proven|Start Delivery|Confirm Dropoff|Cancel" docs/product/mobile_user_flow.md mobile/web/app.js`，exit 0。

主会话保留后续集成围栏给 `final.md` 复跑。

## 5. 偏差与剩余风险

- 本轮按同一 Blocker 红线停止第三次本地 route/elevator wrapper，因此没有产品代码改动。
- Objective 5、Objective 1、Objective 2 / 3 的真实材料均未在本机出现，不能上调完成度。
- 为响应“功能往前走”，下一轮应启动不依赖 O5/O1/PR #4/PR #5 真实材料的新功能切口：O4 `mobile_real_device_field_trial_acceptance_review_decision`，只做真机验收会话后的 fail-closed 评审决策，不放开主操作。
