# O2 Elevator OpenCV State Integration Micro Sprint

## sprint_type

micro

## 本轮目标

主攻当前最低 Objective O2：把 `ros2_trashbot_vision.elevator_opencv_baseline`
产出的 `trashbot.elevator_opencv_baseline.v1` JSON artifact 接入
`task_orchestrator` 电梯 assisted delivery 状态链。

本轮只做 software guard：没有真实图片 manifest、ROS2 runtime、真实电梯、Nav2
实跑或 HIL 材料，因此不提升 OKR 百分比。

## 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_elevator_assist.py`
  - 新增 OpenCV baseline schema、proof gate 和最小置信度常量。
  - 新增 `validate_opencv_baseline_artifact()`，校验 schema、`proof_status=not_proven`、
    必要字段、枚举值和 `not_proven` 边界。
  - 新增 `opencv_baseline_to_phase_evidence()`，把 `door_state`、
    `inside_outside`、`target_floor_candidate`、`safe_to_exit`、`confidence` 和
    `uncertain_reasons` 映射为行为层 `phase_evidence`、`manual_takeover_reason`、
    phone-safe summary 和 task record snapshot。
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py`
  - 新增 `elevator_assist_mode=opencv_baseline` 分支。
  - 复用 `elevator_assist_evidence_file` 读取 OpenCV baseline artifact。
  - 成功路径驱动 `waiting_elevator_open`、`entering_elevator`、
    `requesting_floor_help`、`waiting_target_floor`、`exiting_elevator` 和
    `resume_delivery` action feedback / task record trace。
  - 失败路径 fail closed：artifact 缺失、坏 JSON、schema 不符、门未开、未确认在轿厢、
    目标楼层不匹配、`safe_to_exit` 非 safe、低置信度或 uncertain reason 都会要求人工接管。
- `onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py`
  - 新增 OpenCV baseline happy-path 回归。
  - 新增 OpenCV baseline unsafe/low-confidence fail-closed 回归。
- `docs/product/elevator_assisted_delivery.md`
  - 补充 2026-06-04 16-17 micro 的 OpenCV baseline 状态链接入口径和 not-proven 边界。

## 验证结果

已运行：

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_task_orchestrator_collection_execution
```

结果：

```text
Ran 17 tests in 1.887s
OK
```

已运行：

```bash
python3 -m compileall -q onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_elevator_assist.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py
```

结果：退出码 0，无输出。

已运行：

```bash
PYTHONDONTWRITEBYTECODE=1 bash onboard/scripts/run_smoke_tests.sh
```

结果：

```text
Ran 6 tests in 0.121s
OK

Ran 68 tests in 3.775s
OK

Ran 54 tests in 5.227s
OK

Ran 11 tests in 0.087s
OK

Ran 843 tests in 576.606s
OK

Ran 18 tests in 1.490s
OK
```

说明：full smoke 中 Python `ast.py` 输出 1 条 `ResourceWarning: unclosed <socket.socket ...>`，
但命令最终退出码为 0，所有 discovery 测试通过。本轮未定位到与 OpenCV adapter 相关的失败。

## 剩余风险

- 没有真实电梯图片 manifest、真实相机 runtime 或受控电梯材料。
- 没有证明真实楼层 OCR、真实 `safe_to_exit`、真实 Nav2/fixed-route、WAVE ROVER/UART/HIL 或跨楼层送达。
- OpenCV baseline 当前是单帧 JSON artifact adapter；后续需要 Robot Algorithm Engineer 提供真实/受控图片 eval artifact，再由 Robot Software Engineer 做 ROS2 runtime 复跑。

## O2 进度判断

本轮只能算 `software_guard`。它推进了 KR-O2-ROS2-State-Integration 的软件护栏，
但没有真实图片、ROS2 runtime 或受控电梯证据，因此不建议上调 O2 百分比。

## 协同需求

- Robot Algorithm Engineer：提供真实或受控电梯图片 manifest、offline eval artifact 和阈值复核。
- Full-Stack Software Engineer：后续消费 `phase_evidence`、`phone_safe_summary` 和
  `manual_takeover_reason`，在手机/PC 端显示安全摘要。
- Hardware Infra Engineer：本轮不涉及硬件配置；真实 HIL 或 WAVE ROVER/UART 证据阶段再介入。
- Product / CEO：不需要本轮决策；后续是否把 OpenCV baseline 纳入可涨分 KR，需要真实材料后由 Product/OKR Owner 归档。
