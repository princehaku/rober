# Field Evidence Material Blocker Escalation Pack PRD

Run time: 2026-05-22 02:03 Asia/Shanghai

## Product Problem

最新 OKR 与 sprint final 已经说明：当前 repo 在 Docker-only 主机上已经把 O5 command/status/ACK、O1 PR #5 材料 pending、O2/O3/O4 field material follow-up 做成多轮 software-proof 入口，但真实材料仍没有出现。继续加同类 wrapper 会让进度看起来在动，实际没有补齐 delivery proof、HIL proof、external cloud proof 或 phone/browser proof。

本轮产品问题是：当所有真实材料都缺失时，field owner / CEO 需要一个明确、可转派、可复跑、phone-safe 的 blocker escalation pack，而不是再读一串本地 pending 状态。

## User Value And Product North Star

用户价值：

- CEO 能看到当前卡点到底属于 O5、O1、O2/O3/O4 哪类真实材料，而不是看到泛化 blocked。
- Field owner 能拿到 `next_required_evidence` 和 target owner，知道下一次现场/硬件/云材料应补什么。
- 手机/诊断端只展示安全文案和下一步，不暴露 raw artifact、低层控制、credentials 或硬件细节。

产品北极星：让普通手机用户最终完成低成本垃圾投递闭环。本轮仍是证据链和执行组织能力，不是业务成功证明。

## OKR Mapping

| Objective | Mapping |
| --- | --- |
| Objective 5：云中转 + OSS/CDN 数据通路产品化 | 仍是最低 Objective，约 68%。本轮不提高完成度；它把缺真实 external proof 和 verified terminal result 的阻塞升级为可执行材料请求。 |
| Objective 1：可信底盘控制层 | 约 81%。本轮只把 PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved/material pending 与真实传感器/HIL 材料缺口纳入 blocker pack，不声称 HIL 或 thread resolved。 |
| Objective 2/3/4：送达、电梯、路线、手机体验 | 约 99%。本轮只要求真实 route/elevator/phone field evidence，不声称 route/elevator field pass、真实手机或 delivery success。 |

## KR Breakdown

KR-P1：生成 `field_evidence_material_blocker_escalation_pack` artifact/summary，必须包含：

- `schema=trashbot.field_evidence_material_blocker_escalation_pack.v1`
- `evidence_boundary=software_proof_docker_field_evidence_material_blocker_escalation_pack_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `next_required_evidence`
- `owner_escalation_level`
- `blocked_reason`
- `target_owner`
- `field_safe_copy`

KR-P2：Robot diagnostics 暴露安全别名，手机/Web 只读消费，不改变 Start Delivery、Confirm Dropoff、Cancel 授权。

KR-P3：Hardware read-only consultation 明确采用 `docs/vendor/VENDOR_INDEX.md` 作为硬件事实入口，并确认当前仍没有真实 2D LiDAR/ToF/WAVE ROVER/HIL 材料可用于提升 O1。

KR-P4：Product closeout 必须把本轮结果写入 sprint `tech-done.md`、`side2side_check.md`、`final.md`，并在允许范围内同步相关 docs/OKR；若真实材料仍缺失，OKR 百分比不得提高。

## Core Lever

本轮核心抓手是“从 local metadata wrapper 转向 owner escalation”：把上一轮 owner ack review decision / material followup chain 的 blocked 状态汇总成单一升级包，让下一次行动变成补材料，而不是继续写 pending wrapper。

## Functional Requirements

1. PC gate 只读上一轮安全 summary 或 artifact reference；不读取 raw field files，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、真实云、OSS/CDN、DB/queue 或 4G。
2. 输出必须按 Objective 分类缺口，且每个缺口包含 `next_required_evidence`、`target_owner`、`blocked_reason` 和 `owner_escalation_level`。
3. Robot diagnostics 只暴露 phone-safe summary，不暴露 raw artifacts、complete local paths、checksums、credentials、tracebacks、serial/UART、baudrate、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。
4. Mobile panel 只读展示“材料升级包”，可复制 field-safe copy；缺 summary 时显示 `not_proven` / blocked，不自动 fetch raw diagnostics，不发命令。
5. Hardware consultation 必须写明 PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved/material pending，comment `3269642220` 是 software-proof reply publication，不是 reviewer resolution。

## Priority And Acceptance

P0:

- 能在 Docker-only 环境用 fixtures 生成 blocked escalation pack。
- pack 和 diagnostics/mobile summary 全部保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- `rg` 能找到 capability、evidence boundary、Objective 5、PR #5 unresolved thread 和 forbidden success-control 防线。

P1:

- 手机 panel 中文文案清楚区分 O5 external proof、O1 hardware/HIL materials、O2/O3/O4 route/elevator/phone field evidence。
- Product closeout 明确本轮不提高 OKR，除非后续 worker 实际拿到真实材料。

Acceptance:

- Autonomy、Robot、Full-Stack、Hardware read-only consultation 四个 owner 并行执行，Product 负责 closeout。
- 验证只跑 py_compile、对应 unittest、node --check、fixture json.tool、required rg、scoped git diff --check。
- 不跑 broad colcon，不新增大量测试，不声称真实 proof。

## Risks And Evidence Gaps

- 真实 O5 external proof 仍缺：public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser、verified terminal delivery/dropoff/cancel result。
- 真实 O1 proof 仍缺：2D LiDAR / ToF source/receipt/procurement/installation/wiring/power/calibration/HIL-entry、WAVE ROVER powered bench/UART/HIL logs、operator HIL report、PR #5 reviewer resolve。
- 真实 O2/O3/O4 proof 仍缺：task record、Nav2/fixed-route runtime log、route completion signal、电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result、真实手机/browser 和 route/elevator field pass。
- 当前主机只有 Docker，本轮所有结果最多是 `software_proof_docker_field_evidence_material_blocker_escalation_pack_gate`。

## Sprint Docs To Create Or Update

- 已创建本 sprint planning docs：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 实现后必须更新：`tech-done.md`、`side2side_check.md`、`final.md`。
- 若 worker 修改功能或产品行为，必须同步相关 `docs/` 文档；Product closeout 负责核对。

