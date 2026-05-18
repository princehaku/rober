# Sprint 2026.05.18_20-21 OKR Evidence Rerank Real Material Escalation - PRD

## 1. 用户价值

当前项目已经把 O2/O3/O4 的 route/elevator、手机、安全摘要和材料流推进到很深的 Docker-local software proof。继续追加本地 metadata wrapper 对真实用户没有新增价值，因为普通用户真正缺的是可验收的现场材料：小车是否真的进出电梯、是否真的能固定路线送达、手机是否真的能在真实设备和生产入口上使用、云链路是否真的有公网和 4G 证据。

本轮用户价值是停止消耗同一 blocker，把“下一步需要谁提供什么真实材料”变成可执行清单，让后续 sprint 要么带真实材料推进最低 OKR，要么明确改道到不依赖该 blocker 的功能。

## 2. OKR 映射

- Objective 5：仍是数字最低，但只能由真实 external proof 推进：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 材料。
- Objective 1：下一低项，但只能由真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report 或 PR #5 真实 2D LiDAR / ToF 材料推进。
- Objective 2 / 3：PR #4 已要求电梯 assisted delivery 进入主链；后续需要真实 route/elevator field materials、task record、completion signal、dropoff/cancel completion 或 delivery result。
- Objective 4：若没有 O5/O1/O2/O3 真实材料，可推进真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice 的现场验收材料，而不是继续只跑桌面浏览器 proof。

## 3. PR / Review 证据对应需求

### PR #4：电梯主链不是文档口号

需求：把真实 route/elevator 现场材料作为下一次 O2/O3 验收入口。材料必须至少覆盖门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record、completion signal、dropoff/cancel completion 或 delivery result，并共享同一 safe `evidence_ref`。

### PR #5：硬件 baseline 不能凭空成立

需求：2D LiDAR / ToF 相关材料必须来自真实 SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry，且需要引用 `docs/vendor/VENDOR_INDEX.md` 的边界。没有真实材料时只允许 `hardware_material_pending` 和 `not_proven`。

### OKR routing 漂移：最低项叙述必须由表格和证据决定

需求：每轮 sprint planning 必须从 `OKR.md` 4.1 数字排序开始；如果最低项因真实材料缺失不可推进，要在 `tech-plan.md` 里写明 stop rule、改道理由和下一可执行 owner。

## 4. 本轮验收口径

本轮可验收结果不是代码功能，而是一个可执行升级包：

- 明确 O5 / O1 / PR #4 / PR #5 / O4 的真实材料恢复条件。
- 明确本机 Docker-only 下不能继续重复哪些 blocker。
- 明确下一轮如果有材料该派给哪个 owner、改哪些文件、跑哪些围栏命令。
- 保持 `source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 5. 非目标

- 不新增 route/elevator 本地 wrapper。
- 不新增硬件假设、SKU、UART、波特率或接线结论。
- 不把已有 Docker-local summary 写成 HIL、真实手机、真实现场、真实投放或 O5 external proof。
- 不上调 `OKR.md` 完成度。
