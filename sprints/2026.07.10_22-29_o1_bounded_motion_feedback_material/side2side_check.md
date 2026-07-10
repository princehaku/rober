# O1 Bounded Motion Feedback Material Side-to-Side Check

## sprint_type

sprint_type: epic

## Product 验收结论

Product 验收通过，但只按 `software_proof_o1_motion_map_hil_material_bundle_only` 计入 O1 material delta。Hardware owner 已把 2026-06-10 历史真实上位机 bounded motion / T1001 / IMU-battery / odom readback 材料接入既有 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`，并保持所有安全、HIL、delivery 和 wheel proof 字段 fail-closed。

本轮可以把 O1 从约 90% 保守上调到约 91%。不归档 KR；O5 保持约 85%，因为 `2026.07.10_17-22_o5_production_cutover_readiness_packet` 仍为 `okr_credit_allowed=false` 且缺真实 external production evidence。

## 用户价值和产品北极星

用户价值是把一次历史上位机受控短动、feedback readback、IMU/battery sample 和 odom sample 整理成可审计 O1 bundle，下一轮现场 HIL 可以直接对照缺口执行。产品北极星仍是普通手机用户可安全、可验证地完成垃圾送达；本 sprint 只补强底盘可信证据链，不声称小车已经可安全发车或送达成功。

## OKR 映射和方向判断

- O1：继续，约 90% -> 约 91%。理由是本轮消费了新的 bounded motion / T1001 / IMU-battery / odom material delta，并通过 fail-closed 测试。
- O5：暂停计分，保持约 85%。理由是最低 Objective 仍缺真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic 和真实 phone/browser 材料，上一轮 O5 已固定 `okr_credit_allowed=false`。
- O6/O7：保持约 92%。本轮没有新增 archive/readback/UI 消费链路，后续如需展示本 O1 材料应另起跨 owner sprint。

方向判断：继续 O1，但下一步必须转 current live HIL / feedback_T1001 / motion command / operator observation / route execution proof；不能继续靠 historical bundle wrapper 重复上调。

## 核心抓手对照

| 验收项 | 结果 | Product 判断 |
| --- | --- | --- |
| `bounded_motion_feedback_material_present=true` | 通过 | 接入了 bounded motion feedback material |
| `base_feedback_samples_latest_present=true` | 通过 | 接入了 T1001 readback sample material |
| `t1001_observed_count=2` | 通过 | 只证明 readback sample count，不证明 motion-window L/R 非零 |
| `bounded_motion_lr_nonzero_proven=false` | 通过 | 保持 L/R 非零未证明 |
| `wheel_direction_proven=false` | 通过 | 保持轮向未证明 |
| `imu_battery_calibration_proven=false` | 通过 | sample present 不等于标定 |
| `hil_pass=false` | 通过 | 不是 current live HIL |
| `safe_to_control=false` | 通过 | 不打开安全控制口径 |
| `delivery_success=false` | 通过 | 不声明送达成功 |

## 验证证据

Hardware `tech-done.md` 记录：

```text
python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/*.py
passed
```

```text
python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*motion*map*hil*.py'
Ran 29 tests in 0.173s
OK
```

```text
PYTHONPATH=onboard/src/ros2_trashbot_hardware python3 -m ros2_trashbot_hardware.wave_rover_motion_map_hil_material_bundle
exit 0
status=motion_map_hil_material_bundle_ready_not_hil_pass
bounded_motion_feedback_material_present=true
base_feedback_samples_latest_present=true
t1001_observed_count=2
bounded_motion_lr_nonzero_proven=false
wheel_direction_proven=false
imu_battery_calibration_proven=false
hil_pass=false
safe_to_control=false
delivery_success=false
blocked_reasons=[]
```

Product closeout 验证命令和输出记录在 `artifacts/product_worker_report.md`。

## KR 拆解、更新或历史归档

- O1 KR3：补强 `T=1001` feedback readback、IMU/battery sample 和 odom readback material，但不证明标定、实测里程计闭环或 HIL。
- O1 KR4：新增 fail-closed 单测覆盖 bounded motion 正例、T130 request 误升格、dangerous true、文本泄露和 diagnostic 非零 L/R。
- O1 KR5：未改 launch 参数、串口参数、速度映射或硬件配置。
- 已完成 KR：无。
- 历史记录位置：不移动 KR；只在 `OKR.md`、`docs/process/okr_progress_log.md` 和本 sprint closeout 文档记录本轮证据。

## 风险和剩余证据链

- 这是 historical upper-computer software proof，不是 current live HIL。
- bounded motion 证明短时 pulse 和 stop material 被记录，不证明 safe-to-control。
- T1001 readback 证明 feedback material observed，不证明 bounded-run L/R 非零、wheel direction 或 HIL pass。
- `/odom`、`/imu/data`、`/battery` 只证明 sample/readback present，不证明 dynamic odom、IMU/battery calibration、Nav2 route execution 或 delivery success。
- 仍缺 current live same-run `feedback_T1001.log`、motion command record、operator/external observation、HIL acceptance、wheel direction confirmation、IMU/battery calibration record 和 live Nav2 route execution result。

