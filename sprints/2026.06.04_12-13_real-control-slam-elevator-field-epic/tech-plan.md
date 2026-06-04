# Tech Plan: Real Control, SLAM, Elevator Field Epic

## sprint_type

sprint_type: epic

## 执行原则

本计划完成后默认进入实现阶段，由四个 L2 IC Engineer 并行执行。主节点只负责派发、等待、验收和后续 sprint 留档；不得直接修改产品代码、测试代码、硬件配置、launch 参数或业务实现。

功能必须往前走，测试只做护栏。允许 mock/stub/fixture 先建立接口、状态和 artifact，但每个 owner 都必须保留真实数据/真实硬件切换入口，并在输出中写明 `not_proven`。上位机 SSH 可作为运行通道：`ssh root@192.168.1.11 -p 37878`；如果 SSH 或现场条件临时不可用，继续推进本地/容器/fixture 开发，不把无法上车作为本轮 blocker 主线。

## 文件范围

本轮 Product/OKR Owner 已改或可改：

- `OKR.md`
- `sprints/2026.06.04_12-13_real-control-slam-elevator-field-epic/pre_start.md`
- `sprints/2026.06.04_12-13_real-control-slam-elevator-field-epic/prd.md`
- `sprints/2026.06.04_12-13_real-control-slam-elevator-field-epic/tech-plan.md`
- `docs/product/elevator_assisted_delivery.md`

后续 L2 Engineer 允许范围由 coordinator 派发时按 owner 切分，建议如下：

| Owner | 允许改动范围 | 接口边界 |
| --- | --- | --- |
| full-stack-software-engineer | `pc-tools/workstation/**`、`docs/product/pc_tools_workstation.md`、必要接口说明 | Browser 只走 PC/upper HTTP API；不直连 ROS graph；不绕过 stop/人工报告 |
| robot-software-engineer | `onboard/scripts/upper_robot_api.py`、`onboard/scripts/test_upper_robot_api.py`、`onboard/src/ros2_trashbot_bringup/**`、`onboard/src/ros2_trashbot_nav/**`、`onboard/src/ros2_trashbot_behavior/**`、相关 docs | 负责 upper API 到 ROS2 glue、SLAM/AMCL/Nav2 lifecycle、电梯状态链接入 |
| robot-algorithm-engineer | `onboard/src/ros2_trashbot_vision/**`、`onboard/src/ros2_trashbot_nav/**`、`pc-tools/evidence/**`、算法/电梯 docs | 负责 OpenCV taxonomy、ROI/rule baseline、offline eval、Nav2/map quality，不改硬件协议 |
| robot-hardware-engineer | `onboard/scripts/*wave_rover*`、`onboard/scripts/*lidar*`、`onboard/scripts/*ttyS5*`、HIL/operator evidence docs、vendor-readback 相关 docs | 真实集成前必须读 `docs/vendor/VENDOR_INDEX.md`，负责 HIL 安全、底盘 pulse、LiDAR start/stop/udev/长稳 |

禁止 Product/OKR Owner 在本阶段改动：

- `onboard/**`
- `pc-tools/**`
- `cloud-relay/**`
- `scripts/**`
- `.codex/**`
- 除本计划列明外的 `docs/**`

## OKR 最低优先级核对

当前 `OKR.md` 4.1 节完成度最低的 Objective 是：

1. O2：送垃圾任务 + 电梯 assisted delivery，约 72%。
2. O3：建图、定位、Nav2 与固定路线，约 73%。

本 sprint 直接针对最低 Objective。O2 由 OpenCV 电梯识别、offline eval 和 ROS2 状态链推进；O3 由 SLAM map lifecycle、AMCL reset、Nav2 consumption 和 map quality 推进。O7/O1 同步推进是因为 PC operator 和底盘 HIL 是 O2/O3 现场采证的入口和安全底座，不是抢占低优先级。

## 并行执行切分

### Worker A: full-stack-software-engineer

**目标**：把 PC operator workflow 推进到能触发真实/fixture 控车、雷达 start/stop、建图定位控制和 operator report。

**文件范围**：

- `pc-tools/workstation/src/**`
- `pc-tools/workstation/test/**`
- `pc-tools/workstation/scripts/**`
- `docs/product/pc_tools_workstation.md`
- 本 sprint `tech-done.md` 中属于 full-stack 的段落

**验收命令**：

```bash
cd pc-tools/workstation && npm test -- --run
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run lint
```

**输出证据**：

- WASD/Space/X 到 manual/stop/status/operator report 的同一 `evidence_ref`。
- `POST /api/radar/start`、`POST /api/radar/stop`、status 的 UI/API 证据。
- 建图/重置/保存/加载/定位按钮只走 HTTP API 的证据。
- 明确哪些是 `software_guard`，哪些等待 HIL 或 ROS runtime。

### Worker B: robot-software-engineer

**目标**：打通 upper API 到 SLAM Toolbox、map lifecycle、AMCL localization、Nav2 lifecycle 和电梯状态链。

**文件范围**：

- `onboard/scripts/upper_robot_api.py`
- `onboard/scripts/test_upper_robot_api.py`
- `onboard/src/ros2_trashbot_bringup/**`
- `onboard/src/ros2_trashbot_nav/**`
- `onboard/src/ros2_trashbot_behavior/**`
- `docs/product/elevator_assisted_delivery.md`
- 本 sprint `tech-done.md` 中属于 robot-software 的段落

**验收命令**：

```bash
python3 -m unittest onboard.scripts.test_upper_robot_api
python3 -m compileall -q onboard/scripts onboard/src
bash onboard/scripts/docker_humble_build.sh
```

如 Docker/Humble 或 ROS runtime 不可用，必须先定位失败原因；若确认为环境缺口，保留 targeted unittest/compileall 证据并写明剩余风险。

**输出证据**：

- `/api/map/start|reset|save|load|list` 或等价 upper API 设计与执行结果。
- `/api/localize/reset` 或等价 `/initialpose` 入口。
- `/map` once、map file、metadata、AMCL pose、TF、Nav2 lifecycle 的 runtime 或 fixture artifact。
- OpenCV evidence 接入电梯状态链的 task record/not_proven 边界。

### Worker C: robot-algorithm-engineer

**目标**：建立 OpenCV 电梯识别 taxonomy、ROI/rule baseline、offline eval，并给 Nav2/map quality 输出可验收指标。

**文件范围**：

- `onboard/src/ros2_trashbot_vision/**`
- `onboard/src/ros2_trashbot_nav/**`
- `pc-tools/evidence/**`
- `docs/product/elevator_assisted_delivery.md`
- 本 sprint `tech-done.md` 中属于 algorithm 的段落

**验收命令**：

```bash
python3 -m compileall -q onboard/src/ros2_trashbot_vision onboard/src/ros2_trashbot_nav pc-tools/evidence
python3 -m unittest discover -s onboard/src/ros2_trashbot_vision -p 'test*.py'
python3 -m unittest discover -s onboard/src/ros2_trashbot_nav -p 'test*.py'
```

如果对应测试目录不存在，必须改用实际新增的 targeted unittest 或 offline eval smoke，并在 `tech-done.md` 写清替代原因。

**输出证据**：

- 电梯门线/门缝、轿厢内外、楼层显示屏 ROI、目标楼层、安全驶出的 taxonomy。
- 样本 manifest，包含正例、负例、最低数量、采集要求和失败边界。
- OpenCV ROI/rule baseline 的 artifact、阈值、不可判定策略、FP/FN 和混淆项。
- Nav2/map quality 指标：覆盖区域、未知区比例、waypoint 可达性、保存/加载一致性和失败样例。

### Worker D: robot-hardware-engineer

**目标**：为真实 PC 控车和 LiDAR 一键开关建立现场安全、vendor source、HIL 和证据边界。

**文件范围**：

- `onboard/scripts/hardware_smoke_wave_rover.py`
- `onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py`
- `onboard/scripts/o1_wave_rover_serial_feedback_probe.py`
- `onboard/scripts/o1_lidar_scan_proof_collector.py`
- `onboard/scripts/o1_lidar_raw_packet_proof_collector.py`
- `onboard/scripts/*test*o1*`
- 必要 HIL/operator evidence docs
- 本 sprint `tech-done.md` 中属于 hardware 的段落

**验收命令**：

```bash
python3 -m compileall -q onboard/scripts
python3 -m unittest onboard.scripts.test_o1_ttyS5_safe_pulse_acceptance
python3 -m unittest onboard.scripts.test_o1_lidar_scan_proof_collector
python3 -m unittest onboard.scripts.test_o1_lidar_raw_packet_proof_collector
```

真实硬件阶段还必须先读 `docs/vendor/VENDOR_INDEX.md` 及其指向资料，再执行受控命令；现场命令必须低速、短 pulse、有人看护、有 stop 路径。

**输出证据**：

- vendor 来源说明，包含采用的本地资料路径。
- PC/manual HIL 所需安全前提、operator report 模板、low-speed pulse、stop/post-status。
- `T=1001` 只作为 vendor feedback material，不单独声明 robot ACK。
- LiDAR start/stop/udev/长稳证据，且明确不触碰底盘 UART。

## 子 Agent Prompt 固定结构

后续 coordinator 派发四个 L2 时必须使用以下结构，并从 `.codex/agents/<role>.toml` 完整复制 `developer_instructions`：

```text
[角色 System Prompt]
（从对应 .codex/agents/<role>.toml 的 developer_instructions 字段完整复制，不裁剪）

[本轮任务]
执行 sprints/2026.06.04_12-13_real-control-slam-elevator-field-epic/tech-plan.md 中对应 Worker 的任务。目标是推进真实 PC 控车、雷达一键开关、SLAM/定位、OpenCV 电梯识别之一；测试只做护栏，mock/stub/fixture 不得写成真实完成。

[文件范围]
（复制本 tech-plan 对应 Worker 的文件范围；范围外不得改动。）

[验收命令]
（复制本 tech-plan 对应 Worker 的验收命令；失败必须先定位并修复，确属环境限制时写清影响和剩余风险。）

[输出要求]
必须返回：
1. 实际改动的文件列表
2. 验证命令输出结果（截图或日志片段）
3. 失败定位（如有）
4. 剩余风险
```

## 统一验收命令

Product/OKR 文档验证：

```bash
git diff --check -- OKR.md sprints/2026.06.04_12-13_real-control-slam-elevator-field-epic docs/product/elevator_assisted_delivery.md
```

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|O2|O3|O7|O1|验收命令|文件范围|ssh root@192.168.1.11" sprints/2026.06.04_12-13_real-control-slam-elevator-field-epic OKR.md
```

集成收口建议：

```bash
git diff --check -- OKR.md sprints/2026.06.04_12-13_real-control-slam-elevator-field-epic docs/product pc-tools onboard
```

```bash
rg -n "not_proven|software_guard|robot_runtime_material|field_hil_material|evidence_ref|safe_to_control|delivery_success" sprints/2026.06.04_12-13_real-control-slam-elevator-field-epic docs/product pc-tools onboard
```

## 风险和边界

- 不得把本轮计划或 mock 结果写成 OKR 完成度提升。
- 不得让 PC 浏览器直接访问 ROS graph 或底盘串口；所有控制必须经过后端 API 和 stop/report 护栏。
- 硬件真实集成必须以 `docs/vendor/` 本地资料为准，最终说明写明来源。
- OpenCV 电梯识别必须有不可判定策略；不能只写 happy path。
- 若 Docker/Humble build、SSH 或现场 HIL 失败，L2 必须先定位并重试；确认为环境限制后，记录影响和下一步，不得直接交差。
