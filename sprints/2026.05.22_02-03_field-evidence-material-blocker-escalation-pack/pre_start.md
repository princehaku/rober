# Field Evidence Material Blocker Escalation Pack Pre-start

Run time: 2026-05-22 02:03 Asia/Shanghai

## Sprint Declaration

- sprint_type: epic
- capability: `field_evidence_material_blocker_escalation_pack`
- evidence_boundary: `software_proof_docker_field_evidence_material_blocker_escalation_pack_gate`
- target status: `not_proven`
- fixed safety fields: `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`
- latest prior sprint: `sprints/2026.05.22_01-02_cloud-terminal-result-verification-guard`

## User Value And Product North Star

本轮用户价值不是继续增加一个本地状态包装层，而是在真实材料全部缺失时，把阻塞项变成 field owner / CEO 能执行的升级包：谁需要补什么材料、为什么阻塞、下一份 evidence 应该是什么、该交给哪个 owner、手机/诊断端能展示什么安全文案。

北极星仍是低成本 ROS2 自主垃圾投递机器人。普通手机用户最终只关心能否可靠发车、送达、投放、失败时知道该找谁；本轮只把证据缺口转成可执行升级，不声称真实云、真实手机、真实路线、电梯、HIL 或 delivery success。

## Evidence Read Before Start

- Live `OKR.md` 4.1：Objective 5 约 68% 最低，Objective 1 约 81%，Objective 2/3/4 约 99%。
- 最新 final `sprints/2026.05.22_01-02_cloud-terminal-result-verification-guard/final.md`：O5 不应再堆本地 metadata wrapper；下一步应拉取真实 terminal delivery/dropoff/cancel result，或 O1 PR #5 真实传感器/HIL 材料，或 O2/O3/O4 route/elevator/phone field evidence。
- 前一轮 final `sprints/2026.05.21_23-24_field-evidence-real-material-owner-ack-review-decision/final.md`：不要再做同一 ack layer wrapper；下一步要么消费真实 owner materials，要么显式升级仍缺材料集。
- GitHub PR #5：`PRRT_kwDOSWB9286CJ3tQ` 和 `PRRT_kwDOSWB9286CJ3tU` resolved；`PRRT_kwDOSWB9286CJ3tX` unresolved/material pending；comment `3269642220` 只是 software-proof reply publication。
- PR #6 是 README docs-only，不提供 runtime、hardware、cloud、phone 或 field proof。
- 当前主机只有 Docker，没有真实硬件、真实串口、真实手机、外部 O5 proof 或现场 route/elevator 材料。

## Why This Is The Next Sprint

同一 blocker 已经连续多轮被本地 metadata 消费：O5 需要真实公网/4G/OSS/CDN/DB/queue/terminal result；O1 需要真实 2D LiDAR / ToF / WAVE ROVER / HIL 材料；O2/O3/O4 需要同一 safe `evidence_ref` 的真实 task record、route/elevator、dropoff/cancel、phone/browser 证据。继续添加局部 pending/ack/review wrapper 不会提高 OKR。

本轮转为 blocker escalation pack：消费上一轮 owner ack review decision 或 material followup/review chain，只输出 safe `next_required_evidence`、owner escalation level、blocked_reason、target owner 和 field-safe copy。它不读取 raw artifact，不发布控制命令，不关闭 PR #5 thread，不把 comment `3269642220` 当 resolved。

## Scope Boundary

In scope:

- 生成 PC 侧 field evidence material blocker escalation pack gate。
- 生成 Robot diagnostics safe summary alias。
- 在 mobile/web 增加只读升级包 panel，保持主操作禁用。
- Hardware 只读核对 `docs/vendor/VENDOR_INDEX.md` 与 PR #5 material pending 边界。
- Product closeout 更新 sprint evidence、OKR 边界和 docs 同步情况。

Out of scope:

- 不运行 broad colcon。
- 不声明 HIL、真实 WAVE ROVER/UART、真实 2D LiDAR/ToF、真实公网 HTTPS/TLS、真实 4G/SIM、OSS/CDN live traffic、production DB/queue、真实手机/browser、route/elevator field pass、dropoff/cancel completion 或 delivery success。
- 不关闭 `PRRT_kwDOSWB9286CJ3tX`，不把 PR #6 写成 runtime proof。
- 不消费 raw artifacts、完整本地路径、credentials、checksums、tracebacks、serial/UART 细节或 `/cmd_vel`。

## Owners

- Autonomy Engineer：PC evidence gate 主责，产出 escalation artifact 与 summary。
- Robot Platform Engineer：diagnostics safe alias 与行为/接口边界主责。
- User Touchpoint Full-Stack Engineer：mobile/web 只读 panel 与 fail-closed copy 主责。
- Hardware Infra Engineer：read-only consultation，核对 vendor/PR #5 material pending 边界，不改硬件文件。
- Product Manager / OKR Owner：closeout，核对 OKR、docs、sprint 留档和证据边界。

## Blockers To Escalate

- Objective 5：缺真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser 或 verified terminal delivery/dropoff/cancel result。
- Objective 1：缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry，缺 WAVE ROVER powered bench/UART/HIL logs，PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved/material pending。
- Objective 2/3/4：缺真实 task record、Nav2/fixed-route runtime log、route completion signal、电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result、真实手机/browser 证据和 route/elevator field pass。

