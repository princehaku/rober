# Side-to-Side Check: Runtime Material Epic

## 对照对象

- `pre_start.md`：要求从 software guard 切到 `robot_runtime_material` / `field_hil_material` / 明确 blocker。
- `prd.md`：接受 `robot_runtime_material`、`field_hil_material`、`blocked_with_root_cause` 三类结果；拒绝用 mock、fixture、runbook 包装涨分。
- `tech-plan.md`：四个 IC owner 分工，Product 负责 evidence type gate、OKR 涨分判断和 Epic 收口。

## PRD 验收对照

| PRD 验收项 | 实际结果 | 通过判断 |
| --- | --- | --- |
| 每个 owner 写 owner note，包含动作、命令输出、证据类型、not_proven 边界 | 已有 Robot Software、Full-Stack、Robot Algorithm、Hardware owner notes；Robot Software 另有 operator report fix/deploy notes；Full-Stack 另有 operator report PC proxy retest note。 | 通过 |
| `tech-done.md` 区分 `software_guard`、`robot_runtime_material`、`field_hil_material`、`blocked_with_root_cause` | 已在 `tech-done.md` owner 聚合和 OKR 映射中标注。 | 通过 |
| `side2side_check.md` 对照 PRD 验收项 | 本文件完成。 | 通过 |
| `final.md` 判断 OKR 是否涨分；没有真实材料时明确不涨分 | `final.md` 判定 O7、O8 小幅上涨，O1/O2/O3 保持，O5/O6 保持。 | 通过 |
| 不把 UI 文案、runbook、fixture、collector 或 mock 写成产品涨分 | O2 fixture eval 明确不涨分；O3 missing topics 明确 blocked；O1 非运动 feedback 不写成 HIL；O7 operator report 不写成控车完成。 | 通过 |
| 不继续消费 O5/O6 production blocker | 本轮没有推进 O5/O6；OKR 仍保持支线打回。 | 通过 |
| 没有安全准入时不执行底盘运动 | Hardware 明确未执行 forward/back/left/right/stop pulse，`safe_to_control=false`。 | 通过 |

## Objective Side-to-Side

| Objective | 计划目标 | 本轮证据 | Product 验收 |
| --- | --- | --- | --- |
| O2 | 找真实/受控电梯图片 manifest，跑 OpenCV field eval；没有则明确 blocker。 | 本地和上位机无 manifest，fixture eval `field_eval.pass=false`，状态 `needs_real_image_manifest`。 | 保持约 72%；下一步采集 manifest。 |
| O3 | 上位机 ROS2/8787 radar/map/localize runtime，采 fresh `/scan`、map/localize/Nav2 材料。 | SSH/8787/ROS2 packages/launch parseable；ROS graph topics 缺失，map/localize/Nav2 artifact 缺失。 | 保持约 73%；主结论 `blocked_with_root_cause`。 |
| O7 | PC/browser/operator workflow 连真实 8787 并形成 evidence ref。 | 真实 upper 8787 operator report POST/GET HTTP 200；PC 同源代理 POST HTTP 200，`accepted_by_workstation=true`、`upper_request.ok=true`、`failure_reason=none`，evidence_ref=`2026.06.04_17-18_operator_report_pc_same_origin_retest`。 | 约 88% -> 约 89%；只计 operator report route 和 PC proxy runtime 材料，不计 PC WASD 控车或 HIL。 |
| O1 | stop-first HIL 或非运动 vendor feedback 同场证据；安全不足时 fail closed。 | `/dev/ttyS5 @115200` 非运动 `T=130 -> T=1001` 3/3；没有 motion pulse、HIL、ROS feedback，`safe_to_control=false`。 | 保持约 95%；材料增强但不涨 HIL。 |
| O8 | 完整 Epic governance evidence：owner notes、evidence type、blocker scan、owner health、final。 | 本轮完成跨 owner evidence 聚合、side-to-side、final、OKR/log 更新和旧 blocker 收口。 | 约 35% -> 约 40%；只涨治理 Objective。 |
| O5/O6 | 本轮不继续消费 production blocker。 | 没有 production live material。 | 保持 O5 约 84%、O6 约 82%。 |

## 用户价值检查

本轮没有让普通用户直接完成送垃圾、跨楼层、电梯识别、SLAM 建图或 PC 控车；但它把“哪些入口已经真实接上上位机、哪些仍只是 software guard、哪些被材料 blocker 卡住”变成 CEO 和下一轮 owner 可以执行的证据清单。`upper_http_405` 解除后，operator report 可以从 PC 同源代理写入真实 8787 并回放同一 `evidence_ref`，这是现场采证链的必要前置，但不是运动或送达闭环。

## not_proven 边界

- 不证明真实送垃圾闭环、真实跨楼层、真实电梯识别、楼层 OCR 或用户验收。
- 不证明真实 SLAM map、AMCL 定位恢复、Nav2 消费 `/scan+map` 或固定路线实跑。
- 不证明 PC WASD 真实控车、急停演练、robot ACK、`T=1001` 同场 operator workflow 或 HIL。
- 不证明底盘 HIL、`safe_to_control=true`、ROS `/odom`/`/imu/data`/`/battery`。
- 不证明生产云、4G/SIM、production DB/queue、OSS/CDN 或真实上车数据回放。

## 验收结论

本 Epic 达成本轮 PRD 的“真实材料或明确 blocker”要求。可涨分项仅限 O7 的真实 8787 operator report route/PC 同源代理进展和 O8 的治理证据；O1 非运动 `/dev/ttyS5` feedback runtime material 只作为材料增强记录，不涨 O1 完成度。O2/O3 因关键产品材料未达门槛保持不变。
