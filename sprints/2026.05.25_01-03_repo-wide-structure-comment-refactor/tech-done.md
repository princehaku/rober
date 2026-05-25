# Repo-wide Structure and Comment Refactor Tech Done

sprint_type: epic

## 实际改动

本轮按 4 owner 并行完成 repo-wide structure/comment refactor，目标是目录化、职责拆分、兼容入口保留和中文注释治理，不改变 ROS2 topic/action/service 契约，不新增真实硬件或真实外部证据结论。

### Robot Platform Engineer

- 新增 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_contracts.py`，集中 `RobotState`、`NavigationResult` 和 fixed-route 进度字段。
- 新增 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_elevator_assist.py`，承接电梯 assisted delivery dry-run / artifact proof gate、not-proven 边界和 artifact 校验。
- 新增 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_remote_status.py`，承接 remote bridge pending ACK / operator status 安全过滤。
- 精简 `task_orchestrator.py` 与 `remote_bridge.py`，保留原导入与行为兼容。
- 更新 `docs/behavior/behavior_structure_boundaries.md` 与 `docs/interfaces/ros_contracts.md`。

### Hardware Infra Engineer

- 将 `esp32_bridge.py` 拆成兼容 facade，新增：
  - `bridge_config.py`
  - `esp32_bridge_node.py`
  - `wave_rover_protocol.py`
  - `wave_rover_feedback.py`
- `hardware_diagnostics_proof.py` 改为复用纯协议/反馈模块，不再把 ROS node facade 当工具库。
- 更新 `docs/hardware/wave_rover_json_bridge.md`，写明 vendor 来源和未验证边界。
- 已读 vendor 来源包括 `docs/vendor/VENDOR_INDEX.md`、WAVE ROVER `base_ctrl.py`、`json_cmd.h`、`uart_ctrl.h`、`movtion_module.h`、`ugv_advance.h`、`IMU.cpp`。

### Autonomy Algorithm Engineer

- 新增 nav helper：
  - `route_contracts.py`
  - `route_parsers.py`
  - `elevator_assist.py`
  - `visual_gate_runtime.py`
- 精简 `route_utils.py`、`fixed_route_autonomy.py`、`route_csv_to_yaml.py`、`visual_gate_proof.py`，保留兼容门面。
- 新增 `vision_detection_models.py`，承接 vision sample schema、ROI、detector config、sample context 和 detection payload。
- 精简 `trash_detector.py` 为 ROS runtime adapter。
- 更新 `docs/navigation/fixed_route_workflow.md`、`docs/vision/trash_status_contract.md`、`docs/vision/perception_upgrade_evaluation.md`。

### User Touchpoint Full-Stack Engineer

- 精简 `remote_cloud_relay.py`，抽出 cloud/mobile phone-safe summary 构造、历史 alias 展开和 mobile web 状态归一化 helper。
- 精简 `operator_gateway_diagnostics.py`，增加 stale/raw alias cleanup helper。
- 扩展本机 `/mnt/<drive>/...` 路径脱敏，避免 diagnostics payload 泄露本地路径。
- 更新 `docs/interfaces/operator_gateway_diagnostics.md` 与 `docs/product/mobile_user_flow.md`。

## 验证结果

Owner 级验证：

- Robot 指定 pytest 因当前环境缺 `pytest` 降级；`compileall` 通过；`unittest` 显式组合通过：`Ran 94 tests in 38.005s OK`，额外 `test_remote_bridge.py`：`Ran 139 tests in 74.609s OK`。
- Hardware 指定 pytest 因当前环境缺 `pytest` 降级；`compileall` 通过；标准库同批测试通过：`Ran 24 tests in 0.195s OK`。
- Autonomy 指定 pytest 因当前环境缺 `pytest` 降级；`compileall` 通过；同批 unittest 通过：`Ran 39 tests in 3.565s OK`；`git diff --check` 通过。
- Full-stack 指定 pytest 因当前环境缺 `pytest` 降级；`compileall` 通过；等价 unittest 触点链路通过：`Ran 498 tests in 212.223s OK`。

集成验收：

- `cd /mnt/e/rober/onboard && python3 -m compileall -q src`：退出状态 0。
- `cd /mnt/e/rober/onboard && python3 -m unittest discover src/ros2_trashbot_behavior/test`：退出状态 0，`Ran 797 tests in 290.612s OK`。有 1 条 socket `ResourceWarning`，未导致失败。
- `cd /mnt/e/rober/onboard && python3 -m unittest discover src/ros2_trashbot_hardware/test`：退出状态 0，`Ran 24 tests in 0.154s OK`。
- `cd /mnt/e/rober/onboard && python3 -m unittest discover src/ros2_trashbot_nav/test`：退出状态 0，`Ran 49 tests in 3.924s OK`。
- `cd /mnt/e/rober/onboard && python3 -m unittest discover src/ros2_trashbot_vision/test`：退出状态 0，`Ran 13 tests in 0.594s OK`。
- `cd /mnt/e/rober && git diff --check`：退出状态 0。
- `cd /mnt/e/rober && bash onboard/scripts/docker_humble_build.sh`：退出状态 1，失败根因是当前环境找不到 `docker` 命令，输出包含 `The command 'docker' could not be found in this WSL 2 distro.`。本轮没有进入 Docker image build，也没有进入容器内 `colcon build --symlink-install`。

## 偏差与剩余风险

- 本轮未完成 Docker/Humble/colcon 构建验证，原因是当前运行环境无 Docker CLI。需要在启用 Docker Desktop/Engine 的目标环境补跑 `bash onboard/scripts/docker_humble_build.sh`。
- 本轮不证明真实手机浏览器、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、ROS2 实机、WAVE ROVER/UART、HIL、真实 Nav2/fixed-route、真实电梯、真实投放、dropoff/cancel completion 或 delivery success。
- 当前 index 里仍存在 unrelated staged 删除：`docs/superpowers/plans/2026-05-08-codex-subagents.md`、`docs/superpowers/plans/2026-05-08-project-completion.md`、`docs/superpowers/specs/2026-05-08-project-completion-design.md`。本轮未恢复、未覆盖、未纳入验收；提交本轮重构前必须把这些删除与本 sprint 分离，或由 CEO 明确确认另行处理。
- 本轮不调整 OKR 完成度数字。

## Code Review 结果

只读 code review 未发现 import path、entry point、runtime crash、硬件事实口径或 `safe_to_control` / `not_proven` 语义方面的阻塞问题。

唯一 P1 是 unrelated staged 删除位于 `docs/superpowers/`，不属于本轮 tech-plan 文件范围。主节点未擅自恢复或 unstage 这些删除，因为它们可能是用户既有改动；本轮收口明确将其排除在 sprint 交付范围之外。
