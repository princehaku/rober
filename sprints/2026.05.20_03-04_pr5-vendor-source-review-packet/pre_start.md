# Sprint 2026.05.20_03-04 PR5 Vendor Source Review Packet - Pre Start

## 1. Sprint 类型

- sprint_type: epic
- 启动时间：2026-05-20 03:04 Asia/Shanghai
- 自动化：`skill-progression-map`
- 目标：把 PR #5 未解决 review thread `PRRT_kwDOSWB9286CJ3tX` 从“缺材料”推进成可执行、可复核、fail-closed 的 vendor/source review packet 软件能力。

## 2. 证据化 rerank

### Live OKR

- `OKR.md` 4.1 当前最低是 Objective 5，约 68%。
- `OKR.md` 6 明确：只有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 等外部材料到位，才继续提高 O5；否则不要重复本地 O5 metadata depth。
- 最新 O5 sprint `2026.05.20_02-03_cloud-command-expiry-safety-guard` 的 final 明确 Objective 5 保持约 68%，证据边界仅 `software_proof_docker_cloud_command_expiry_safety_guard`。

### 最近 PR / review

- GitHub PR #5 已 merged，但 review threads 当前状态为：
  - `PRRT_kwDOSWB9286CJ3tQ` resolved。
  - `PRRT_kwDOSWB9286CJ3tU` resolved。
  - `PRRT_kwDOSWB9286CJ3tX` unresolved。
- 未解决 thread 的 review 内容是：mandatory sensor baseline 引入 2D LiDAR / ToF channel assumptions，但没有引用 `docs/vendor/` evidence；项目规则要求硬件相关决策必须本地 vendor source 可追溯。
- `sprints/2026.05.19_15-16_pr5-github-thread-resolution/final.md` 已把 X 判为 `blocked_pending_real_materials`，不得把 local docs/gate 写成真实 procurement、installation、calibration、HIL 或 O1 进度提升。

### 最近 blocker 消费

- 最近 O5 finals：
  - `2026.05.20_00-01_cloud-ack-outage-replay-guard`
  - `2026.05.20_01-02_cloud-pending-ack-status-guard`
  - `2026.05.20_02-03_cloud-command-expiry-safety-guard`
- 三轮都推进 local/Docker cloud ACK/status guard，均未提高 O5。
- `sprints/2026.05.19_23-24_real-material-followup-escalation-status/final.md` 已完成 real-material follow-up，不应继续堆同一 wrapper。

## 3. 本轮方向

本轮不继续 O5 local metadata。选择 Objective 1 / Objective 4 的交叉风险：PR #5 hardware baseline 的 vendor/source 可追溯性。

核心抓手是新增 `pr5_vendor_source_review_packet`：

- 从 `docs/vendor/VENDOR_INDEX.md` 和 `docs/product/production_hardware_boundary.md` 生成 review packet。
- 明确哪些 hardware baseline 条目有本地 vendor source boundary，哪些仍是 product target / hardware_material_pending。
- 对 `2D LiDAR` / `ToF` assumptions 保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 输出可给 GitHub review thread 使用的安全摘要，但不自动关闭 `PRRT_kwDOSWB9286CJ3tX`。

## 4. 为什么不是继续 O5

- O5 数值最低，但下一步真实进度依赖公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser。
- 当前主机只有 Docker，没有这些外部材料。
- 连续三轮 O5 ACK/status guard 已证明本地 metadata 继续深入不会提高 O5，也会重复消费同一材料 blocker。

## 5. 为什么不宣称真实硬件 / 外部证明

- 本轮只做 repo-local `software_proof` packet，不读取真实串口、不访问 WAVE ROVER、不运行 HIL、不采购或安装 2D LiDAR / ToF。
- `docs/vendor/VENDOR_INDEX.md` 只能证明本地 vendor source boundary 覆盖 Orange Pi Zero 3、WAVE ROVER、UART/JSON、firmware/vendor app 和 camera/tutorial material；不能证明项目已选型、购买、安装、接线、供电、标定或 HIL 通过 2D LiDAR / ToF。
- 所有 Robot/mobile 消费面必须保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 6. Owner

- `hardware-engineer`：主责 vendor/source review packet gate。
- `robot-software-engineer`：主责 diagnostics metadata-only safe alias。
- `full-stack-software-engineer`：主责 mobile/web 只读 review packet panel。
- `product-okr-owner`：主责 sprint closeout、OKR 边界、review evidence language。

## 7. 风险与阻塞

- `PRRT_kwDOSWB9286CJ3tX` 仍可能保持 unresolved，直到真实 vendor/source/procurement/materials 到位或 reviewer 接受当前 `not_proven` packet。
- 本轮不能提高 Objective 1 或 Objective 5 完成度，除非真实材料进入并通过独立验收；当前计划默认不提高。
- 如果发现 repo 已有等价 `hardware_baseline_source_alignment` 能力完全覆盖本轮目标，worker 应复用并补齐缺口，而不是新增重复 gate。
