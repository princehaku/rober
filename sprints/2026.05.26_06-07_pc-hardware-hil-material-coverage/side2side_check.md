# PC Hardware HIL Material Coverage Side2Side Check

## 1. 对照结论

本轮对照 PRD / tech-plan / worker 结果，结论为：PC 工作站 material coverage 能力已满足本 sprint 的 software-proof 验收边界，可以收口；但不能升级为真实 WAVE ROVER/UART/HIL 通过。

## 2. 需求对照

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| Node-native scanner/API | 通过 | 新增 `GET /api/tools/hardware-materials` 和 `waveRoverMaterialCoverage.ts`。 |
| 扫描 `pc-tools/evidence/fixtures/wave_rover_*` | 通过 | Scanner 识别 wave rover fixture groups。 |
| 五件套 required materials | 通过 | 识别 `feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`、`operator_hil_report` / `.json`。 |
| UI 展示 coverage 和缺口 | 通过 | Vue `Hardware Materials` tab/panel 已展示 WAVE ROVER material coverage。 |
| 边界文案 | 通过 | UI/API 明确 `coverage is not HIL pass`。 |
| Fail-closed flags | 通过 | 保持 `source=software_proof`、`proof_status=not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`pc_only=true`。 |
| 不恢复旧 Python gate | 通过 | `find pc-tools -path 'pc-tools/workstation/node_modules' -prune -o -type f -name '*.py' -print` 无输出。 |
| 文档同步 | 通过 | `docs/product/pc_tools_workstation.md` 已更新。 |

## 3. OKR 对照

- Objective 1：材料 coverage 从散落 fixture 变成 PC 工作站可视、可排序、可补齐的清单，因此从约 81% 小幅提升到约 83%。
- Objective 2：不涉及真实任务状态机、路线、电梯、投放或送达，不提升。
- Objective 3：不涉及真实 Nav2/fixed-route runtime 或路线采集，不提升。
- Objective 4：PC 工具体验间接受益，但不是普通手机端或 true phone/browser proof，不提升。
- Objective 5：不涉及云中转、公网、4G、OSS/CDN 或 production queue，不提升。

## 4. 明确不证明

本轮不证明：

- 真实 WAVE ROVER 上电或真实 UART link。
- serial path、baudrate link、wheel direction、feedback frequency、IMU/battery calibration。
- 真实 HIL pass。
- 真实 2D LiDAR / ToF source、receipt、安装、接线、电源、标定。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved。
- 真实 Nav2/fixed-route、电梯现场、投放、dropoff/cancel completion、delivery result 或 `delivery_success=true`。

## 5. Product 验收判断

本轮不再把“缺真实硬件材料”作为唯一 blocker 消费；已经把缺口转成 PC 工作站可见的 material coverage 和 follow-up 清单。下一步应由 Hardware 按 coverage 缺口补真实材料，再由 reviewer 复核，而不是继续叠加 local-only metadata wrapper。
