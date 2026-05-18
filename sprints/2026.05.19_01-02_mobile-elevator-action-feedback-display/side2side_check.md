# Sprint 2026.05.19_01-02 Mobile Elevator Action Feedback Display - Side2Side Check

Run time: 2026-05-19 01:17:04 CST

## 对照结论

本轮 Product closeout 对照 `prd.md` / `tech-plan.md` / Owner A-B `tech-done.md` 后，确认本 sprint 已完成 Objective 4 / Objective 2 的 software-proof 可观测性目标：`current_step=elevator:<phase>` 从 Robot action feedback contract 贯通到 mobile/web 只读“电梯实时阶段”展示。

该结果支撑 PR #4 的电梯主链路可解释性：用户侧能看到等待电梯开门、进入电梯、请求帮忙按楼层、等待目标楼层、驶出电梯、继续送往垃圾站等阶段。它不解决 PR #5 暴露的 2D LiDAR / ToF SKU/vendor/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 和 vendor source/materials 缺口。

## 用户价值和产品北极星

用户价值：普通手机用户在任务进行时可以理解小车正处于哪个电梯辅助阶段，以及下一步为什么需要等待或人工协助，而不需要理解 ROS action、raw JSON、diagnostics summary 或底层硬件参数。

产品北极星：低成本 ROS2 垃圾投递机器人以手机为普通用户唯一入口；本轮只推进“状态可解释、可观测”，不把 software_proof 写成真实手机、真实电梯、真实送达或 delivery success。

## 验收口径对照

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| mobile/web 识别 `current_step=elevator:<phase>` 并渲染只读阶段 | 通过 | Owner A 更新 `mobile/web/app.js`、fixture 和测试；`python3 mobile/web/test_mobile_web_entrypoint.py` -> `Ran 100 tests ... OK`。 |
| unknown/missing/non-elevator fail closed | 通过 | Owner A 测试覆盖白名单、缺失/未知阶段、phone-safe 过滤和 offline/diagnostics refresh 渲染链路。 |
| Start Delivery / Confirm Dropoff / Cancel gating 不变 | 通过 | Owner A required `rg` 命中主按钮 gating；`primary_actions_enabled=false` 仍不放行。 |
| Robot contract 保持 phone-safe、只读、metadata-only | 通过 | Owner B 更新 `docs/interfaces/evidence_contracts.md` 与 `docs/product/elevator_assisted_delivery.md`；未改主链状态机或 operator gateway 语义。 |
| 证据边界保留 `software_proof` / `not_proven` | 通过 | Owner A/B 均保留 `delivery_success=false`、`primary_actions_enabled=false`，Product closeout 同步 OKR 和 progress log。 |

## OKR 映射

- Objective 2：可送垃圾任务 + 电梯 assisted delivery 必达闭环。PR #4 电梯主链路的 action feedback 已具备手机可读展示入口，提升电梯阶段可观测性；仍不证明真实 route/elevator field pass。
- Objective 4：手机用户体验与低成本量产边界。手机端能只读解释电梯辅助阶段；仍不证明真实 iPhone/Android device behavior、production app 或真实 PWA prompt/user choice。
- Objective 1：保持约 81%。本轮未新增 WAVE ROVER、UART、HIL、`feedback_T1001.log`、`/odom`、`/imu/data` 或 `/battery` 实机材料。
- Objective 5：保持约 68%。本轮没有公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 external proof。

## 明确不证明

本轮不证明真实手机、真实电梯、真实 Nav2/fixed-route、WAVE ROVER/UART/HIL、O5 external proof、dropoff/cancel completion、真实投放、真实 delivery success、真实 2D LiDAR、真实 ToF 或 PR #5 vendor source/materials 已补齐。

## 责任 Engineer 与后续证据

- Full-Stack：后续需在真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice 中复验该展示，不得只用 local browser/fixture 宣称真实手机通过。
- Robot：后续需把 PR #4 的真实电梯门状态、楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record/completion signal 和 delivery result 回填到同一 `evidence_ref`。
- Hardware：后续需补 PR #5 的真实 2D LiDAR / ToF SKU/vendor/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。
