# PC Hardware HIL Material Coverage Final

## 1. 收口结论

本 sprint 完成。`pc-tools/workstation` 已新增 Node-native `Hardware Materials` 入口，能读取本地 WAVE ROVER fixture materials，展示 required materials coverage、缺口和 `not_proven` 边界。

本轮是 PC 工具 software-proof 能力，不是 HIL pass。OKR 上只允许 Objective 1 小幅提升到约 83%，Objective 2/3/4/5 不提升。

## 2. 实际交付

- API：`GET /api/tools/hardware-materials`。
- Scanner：`waveRoverMaterialCoverage.ts`。
- UI：Vue `Hardware Materials` tab/panel。
- Required materials：`feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`、`operator_hil_report` / `.json`。
- 安全边界：`coverage is not HIL pass`、`source=software_proof`、`proof_status=not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`pc_only=true`。
- 文档：`docs/product/pc_tools_workstation.md` 已同步。
- Python gate：未恢复；`pc-tools` 下无 tracked Python evidence gate。

## 3. 验证结果

Worker 已验证：

- `PATH=/tmp/rober-node-v24.11.1-linux-x64/bin:$PATH npm run test`：2 test files passed，11 tests passed。
- `PATH=/tmp/rober-node-v24.11.1-linux-x64/bin:$PATH npm run build`：vite built successfully，27 modules transformed。
- `PATH=/tmp/rober-node-v24.11.1-linux-x64/bin:$PATH npm run lint`：exit 0。
- `git diff --check -- pc-tools/workstation docs/product/pc_tools_workstation.md docs/hardware/wave_rover_feedback_replay_gate.md sprints/2026.05.26_06-07_pc-hardware-hil-material-coverage`：exit 0。
- `find pc-tools -path 'pc-tools/workstation/node_modules' -prune -o -type f -name '*.py' -print`：无输出。

Product closeout 已验证 sprint closeout 文件、OKR/log 关键词和 scoped whitespace。

## 4. OKR 进度

| Objective | 收口判断 |
| --- | --- |
| Objective 1 | 从约 81% 提升到约 83%；原因是 WAVE ROVER/HIL material coverage 从散落 fixture 变成 PC 工作站可读、可复核、可补齐的清单。 |
| Objective 2 | 保持约 99%；本轮不证明任务闭环、真实电梯、dropoff/cancel completion 或 delivery success。 |
| Objective 3 | 保持约 99%；本轮不证明 Nav2/fixed-route runtime、路线采集或 route completion signal。 |
| Objective 4 | 保持约 99%；PC 工具间接受益，但不是普通手机端验收或 true phone/browser proof。 |
| Objective 5 | 保持约 76%；本轮不涉及公网、4G、OSS/CDN、production DB/queue 或 cloud command lifecycle。 |

## 5. 剩余风险和下一步

剩余风险：

- 真实 WAVE ROVER/UART/HIL 仍未证明。
- 2D LiDAR / ToF 真实 source、receipt、安装、接线、电源和标定仍未证明。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`。
- `delivery_success=false` 仍是正确边界；本轮不证明真实送达、真实投放或真实 cancel/dropoff completion。

下一步：

- Hardware 按 `Hardware Materials` coverage 缺口补齐真实 powered bench、UART/HIL、operator report、LiDAR/ToF material 和 reviewer-follow-up 证据。
- Reviewer 复核同一 safe `evidence_ref` 下的真实材料后，再判断 PR #5 是否可 resolved。
- 不再用 another local-only metadata wrapper 冒充 Objective 1 进展。
