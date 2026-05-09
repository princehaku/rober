# Sprint 2026.05.10 07-08 Side-to-side Check

## 对照检查

- 对照 OKR：本轮直接推进 Objective 4 KR3，同时补强 Objective 3 学习数据复盘和 Objective 5 远程诊断证据。
- 对照用户要求：功能往前走优先，测试只做护栏；本轮新增的是学习阶段可诊断产物，不是单纯测试扩展。
- 对照硬件纪律：未修改 WAVE ROVER、ESP32、Orange Pi、UART、GPIO、电压、波特率或底盘协议；无新增硬件事实假设。
- 对照 sprint 留档：已创建并更新本轮 `pre_start.md`、`prd.md`、`tech-plan.md`、`tech-done.md`、`side2side_check.md`。

## 待验收

- 真实机器人上运行 `learn.launch.py route_recorder:=true route_id:=trash_station_route` 后，检查 `route.csv`、`keyframes/*.jpg`、`keyframes/*.json` 和 `manifest.json` 是否同步生成。
- 下一轮建议按 Product/Robot Platform 复查处理 Objective 2 的 patrol 学习 proof-gate。
