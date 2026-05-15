# Sprint 2026.05.16_03-04 PC Route Elevator Console Integration - PRD

sprint_type: epic

## 1. 用户价值

现场调试人员下一次准备真实路线/电梯联跑时，不应在 PC route debug console、Robot diagnostics、mobile 电梯复账 panel 之间手动拼同一 `evidence_ref`。本轮把上一轮电梯路线复账摘要接入 PC route debug console，让 PC 工作站先形成“路线进度 + 最近任务 + 电梯复账”的同屏只读入口。

该能力服务 Objective 3：固定路线与关键帧调试必须可重复、可观测、可解释。它也支持 Objective 2/O4，但不声明真实送达、真实电梯、真实 Nav2/fixed-route 或 HIL 完成。

## 2. OKR 映射

- Objective 3 主目标：PC route debug console 从单一路线/任务摘要升级为 route + elevator reconciliation 同屏复盘入口。
- Objective 2 支撑：电梯 assisted delivery 的 phase evidence 与 route completion signal 更容易被同一 PC 调试入口复核。
- Objective 4 支撑：手机端能看到 PC console 已关联的复账摘要，减少现场沟通成本。
- Objective 5 不推进：没有真实外部云/4G/OSS/CDN/DB/queue 材料。

## 3. 验收标准

1. PC route debug console 支持可选 `--elevator-route-reconciliation` 输入；缺失时 fail closed，不影响原 route/task console。
2. JSON summary 输出 `route_elevator_reconciliation`，包含 safe `evidence_ref`、status/verdict、same-evidence-ref 状态、source states、missing/mismatch、operator next steps、boundary 与 `not_proven`。
3. HTML 页面新增只读 “Elevator Route Reconciliation” section，不暴露 raw artifact、本机路径、token、serial/UART、WAVE ROVER、`/cmd_vel`、checksum 或 traceback。
4. Robot diagnostics 的 `pc_route_debug_console` summary metadata-only 保留该新增字段，仍不触发 collect/dropoff/cancel、ACK、Nav2、HIL 或 delivery success。
5. Mobile PC route debug panel 展示 PC console 关联的电梯复账摘要，并保持 Start / Confirm Dropoff / Cancel gating 不变。

## 4. 不做事项

- 不新增真实 Nav2/fixed-route 运行、不读取 ROS graph、不启动机器人运动。
- 不做硬件、UART、WAVE ROVER、Orange Pi 或 HIL。
- 不做 Objective 5 外部云、4G、OSS/CDN、production DB/queue 或 worker/migration。
- 不新增大测试套件，只运行围栏验证。

## 5. 风险

- PC console 只能证明 Docker/local 软件复盘入口可读，不证明真实 field run。
- 如果输入复账材料包含成功文案或敏感字段，必须 blocked/not_proven，而不是展示为可控或完成。
- 若 mobile panel copy 漂移到 success wording，会误导普通用户；本轮必须保持 read-only 和 not_proven。
