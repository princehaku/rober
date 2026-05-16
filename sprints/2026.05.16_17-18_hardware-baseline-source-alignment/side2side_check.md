# Sprint 2026.05.16_17-18 Hardware Baseline Source Alignment - Side2Side Check

sprint_type: epic

## 1. 对照对象

- 用户需求：执行 Task D Product closeout，收口 Task A/B/C/D 证据，更新 sprint 留档、`OKR.md` 和 `docs/process/okr_progress_log.md`，不要提交 git。
- PRD 验收：PC gate、Robot diagnostics、mobile/web 能展示同一 source-alignment 状态；默认硬件集与目标传感器基线不互相冒充；`docs/vendor/VENDOR_INDEX.md` 是 source boundary；2D LiDAR / ToF 仍是 pending/not_proven。
- Tech plan 验收：边界固定为 `software_proof_docker_hardware_baseline_source_alignment_gate`，并保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. Side-by-side 验收结论

| 项目 | 预期 | 实际 | 结论 |
| --- | --- | --- | --- |
| 用户价值 | 让 Hardware / Robot / Mobile 对硬件基线缺口给出一致解释 | PC gate、Robot diagnostics、mobile/web 均消费或展示 `hardware_baseline_source_alignment` 摘要 | 通过 |
| OKR 映射 | O1 source alignment 可推进，O5 不继续本地 metadata | O1 约 73% -> 约 74%；O4 约 86% -> 约 87%；O5 保持约 66% | 通过 |
| 证据边界 | 不声明真实硬件、真实手机、真实 field pass 或 O5 external proof | 文档统一写明 `software_proof_docker_hardware_baseline_source_alignment_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false` | 通过 |
| 责任 Engineer | Hardware / Robot / Full-stack / Product 分工明确 | Task A/B/C/D 均有 owner、实际改动和验证摘要 | 通过 |
| 文档同步 | sprint、OKR、进度日志同步 | `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md` 已更新 | 通过 |

## 3. 用户价值回看

本轮没有把“硬件基线来源对齐”包装成业务完成，而是把 PR #5 review 的 P1/P2 风险变成可重复检查和下游只读展示。用户和现场支持获得的是更清晰的硬件缺口解释：默认硬件集不等于目标传感器已装机，local vendor coverage 不等于真实 2D LiDAR / ToF 已采购、安装、接线、标定或 HIL。

## 4. 剩余风险

- Objective 1 仍缺真实 WAVE ROVER `hil_pass`、真实串口日志、`T=1001` feedback、`/odom`、`/imu/data`、`/battery` 实机样本。
- Objective 4 仍缺真实手机设备/browser、production app、真实 PWA prompt/user choice 和量产实物验收。
- Objective 5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、migration、worker 和多实例/队列一致性证明。
- 本轮所有结论仍是 Docker/local software proof，不得写成真实 route/elevator field pass、delivery success 或 HIL。
