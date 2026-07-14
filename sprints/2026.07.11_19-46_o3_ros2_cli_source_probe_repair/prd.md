# O3 ROS2 CLI Source Probe Repair PRD

## 背景

O5 仍是当前最低 Objective，约 `85%`，但真实公网 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN、真实手机/browser 证据缺失已经被多轮证明，继续 O5 support-only/readback 不应再计分。O1/O6/O7 约 `93%`，当前最接近 mission path generation 的可执行链是 O3/O1 no-motion localization/path readiness。

`17-43` sprint 把 latest blocker 从 `/scan` attempt 前移到 `map_lifecycle_proof_not_clean` 与 `ros2_command_unavailable_after_bash_source`。`18-45` sprint 又证明 `rclpy_import_ok=true`，但 `ros2_cli_ok=false`，且 `map_lifecycle_preflight` 因无 ROS2 CLI 被跳过。本轮要把这个分裂变成可修复合同。

## 用户价值和产品北极星

普通用户不会关心 `command -v ros2`。但如果真实板无法稳定进入 ROS2 CLI/lifecycle 读数，后续手机一键发车、固定路线 path generation、route execution、delivery result 和 operator acceptance 都没有可信证据链。本轮价值是缩短从现场失败到下一条修复命令的距离。

产品北极星保持：固定路线送垃圾闭环。当前本 sprint 只验收 path generation 前置诊断，不验收送达成功。

## 目标

1. 把 `board_source_preflight_ros2_cli_unavailable` 拆成 source、PATH/which、CLI invocation、Python/rclpy 四层。
2. 修复 helper 中可能导致 `command -v ros2` 被误判或被过短 timeout 吞掉的合同问题。
3. 保持 no-motion fail-closed：任何失败都必须自然写出 artifact，并保留危险字段 false。
4. 为下一轮进入 `map_server`/`amcl` lifecycle、`/scan`、`/amcl_pose`、`map->odom` 和 path generation 提供明确门槛。

## 非目标

- 不执行 `/cmd_vel`、`/api/base/manual` 或 `NavigateToPose`。
- 不打开或修改 WAVE ROVER、ESP32、UART、串口、速度映射或底盘协议。
- 不把 `managed_runtime_started=true` 解释成运动、HIL、route execution 或 delivery success。
- 不更新 `OKR.md`，不归档 KR，不调整 Objective 百分比。
- 不创建 `tech-done.md`、`side2side_check.md`、`final.md`。

## OKR 映射和方向判断

- O5：`暂停 support-only 推进`。缺真实 external production evidence，不继续靠 readiness/readback 包装计分。
- O1/O3：`继续`。本轮修 path generation 前置 blocker，但只有出现 current same-run path generation success 或 route execution success 才可能触发后续 OKR 调整。
- O6/O7：`等待可消费 mission artifact`。只有同轮 route/path/delivery/operator/production material 产生后才继续消费链。
- 方向判断：继续 O3 no-motion source probe repair；不替换 Objective，不归档 KR。

## KR 拆解、更新或历史归档

当前 KR 处理：

- O5 KR：保持当前推进区，缺真实公网/生产/手机证据，不归档。
- O1 path generation / Nav2 route execution 缺口：保持当前推进区，本轮只修前置 CLI/source probe。
- O6/O7 mission artifact 消费：保持等待状态，不新增 wrapper-only KR。

历史归档：无。本轮没有已完成 KR，也没有取消或替换 KR 的证据。

## 本轮核心抓手

主抓手是 `onboard/scripts/o10_amcl_nav2_runtime_proof.py` 的 `board_source_preflight` 合同。Artifact 需要能回答：

- source 阶段是否执行、是否超时、哪个 setup 文件命中或缺失。
- `PATH` 是否含 ROS2 CLI 目录，`AMENT_PREFIX_PATH`/`PYTHONPATH`/`LD_LIBRARY_PATH` 是否能解释 Python 与 CLI 分裂。
- `command -v ros2`、`type -a ros2`、`which ros2` 的结果分别是什么。
- 最小 `ros2` invocation 是不存在、超时、返回非 0，还是可执行。
- `rclpy` import 成功路径是否继续存在。

## 需要做什么

Algorithm owner 需要：

1. 修改 helper 的 source/which/CLI invocation/rclpy 分层输出。
2. 补充单元测试，覆盖 `ros2_cli_ok=false` 但 `rclpy_import_ok=true`、source timeout、PATH missing、CLI invocation timeout 等场景。
3. 本地运行 helper，确认 fail-closed artifact 形状稳定。
4. scp 到真实板运行 helper，拉回 live artifact。
5. 同步 `docs/navigation/field_route_evidence_preflight.md` 和 `docs/navigation/fixed_route_workflow.md` 的读取顺序与 proof boundary。

## 优先级和验收口径

P0 验收：

- `board_source_preflight` 不能再只给单个 `ros2_cli_ok=false`，必须有可执行分层字段。
- 下游 skipped 必须说明是 source、PATH/which、CLI invocation 还是 rclpy 层阻断。
- 如果 live artifact 仍为 `ros2_cli_ok=false`，但能清楚指向新的更窄层级，本轮可作为 fail-closed diagnostic progress；不得涨 OKR 百分比。
- 如果 live artifact 仍只是同一泛化 `ros2_cli_ok=false`，`final.md` 必须升级 CEO 决策，不得包装成第三轮可计分进展。

## 对应责任 Engineer

- 主责：`robot-algorithm-engineer`
- Product 验收：`product-okr-owner`
- 不需要 Hardware owner，除非实现阶段发现必须修改真实硬件/串口/底盘配置；本轮计划禁止此类改动。
- 不需要 Robot Software 或 Full-stack owner，除非后续 API/readback/UI 需要消费新的 artifact 字段；本轮不安排。

## 风险、阻塞和证据链

- 真实板 SSH、shell、ROS daemon 或 managed runtime 可能临时抖动，导致本轮只能拿到 timeout 分层。
- Helper source prefix 可能和人工 SSH 命令不完全一致，需要 artifact 保留 `ros_setup_source_boundary`、cwd、Python executable 和短环境摘要。
- 即使修复 ROS2 CLI，后续仍可能被 lifecycle、`/scan`、AMCL、TF 或 planner action 阻塞。
- 证据链仍缺：same-run `path_generated=true`、Nav2 route execution result、delivery record、operator acceptance、current live HIL、production external evidence。

## 计划阶段产物

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

本 PRD 不更新 `OKR.md`，不创建实现/验收/收口文档。
