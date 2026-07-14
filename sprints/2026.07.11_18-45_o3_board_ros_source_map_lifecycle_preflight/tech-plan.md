# O3 Board ROS Source Map Lifecycle Preflight Tech Plan

## 方案

在 `onboard/scripts/o10_amcl_nav2_runtime_proof.py` 增加一个短窗口、只读的 board source preflight 层。它在进入长 `/scan` attempt 或 path generation 前，单独记录 sourced shell 中 `command -v ros2`、`python3 -c 'import rclpy'`、Python executable、`rclpy.__file__`、`sys.path` 前几项，并把结果分类为 source/CLI/runtime/lifecycle 的具体 blocker。

如果 `ros2` 和 `rclpy` 均可用，再继续检查 `map_server` / `amcl` lifecycle 或保留现有 managed runtime readback；如果不可用，artifact 必须 fail-closed，明确跳过 `/scan` attempt 与 path generation。

## 用户价值和产品北极星

本轮服务于固定路线 current-run path generation 的最前置条件：让现场不能生成路线的问题可以被下一条命令直接修复，而不是继续在 `/scan` QoS、O5 packet 或历史材料之间漂移。

## OKR 映射和方向判断

- O5：当前最低，约 `85%`；不推进。原因是缺真实 production external evidence，继续 support-only packet 会重复消费 blocker。
- O1/O3：推进。board ROS source 与 `map_server` lifecycle 是 current same-run path generation / Nav2 no-motion proof 前置项。
- O6/O7：不直接推进。只有后续拿到 current-run route/delivery/operator material 才允许消费。

## 文件范围

Planning 阶段主节点已创建：

- `sprints/2026.07.11_18-45_o3_board_ros_source_map_lifecycle_preflight/pre_start.md`
- `sprints/2026.07.11_18-45_o3_board_ros_source_map_lifecycle_preflight/prd.md`
- `sprints/2026.07.11_18-45_o3_board_ros_source_map_lifecycle_preflight/tech-plan.md`

Implementation 阶段允许 `robot-algorithm-engineer` 修改：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_18-45_o3_board_ros_source_map_lifecycle_preflight/tech-done.md`
- `sprints/2026.07.11_18-45_o3_board_ros_source_map_lifecycle_preflight/artifacts/*`

禁止修改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- O5 relay / cloud production readiness 代码
- O6 archive / readback schema
- O7 workstation UI
- WAVE ROVER、串口、引脚、电压、波特率、机械或 `docs/vendor/` 文档
- 其他 sprint 目录

## 对应责任 Engineer

- Implementation owner: `robot-algorithm-engineer`
- Product closeout: `product-okr-owner`

这是单 owner 任务，按 AGENTS 规则由 Algorithm 单线闭环实现、测试、修复和 `tech-done.md` 留档。

## 实施步骤

1. 读取上轮 `final.md`、`tech-done.md` 和 live artifact，确认最新 blocker 为 board ROS source / map lifecycle。
2. 在 helper 中新增 source preflight 摘要函数，短 timeout 执行：
   - `command -v ros2`
   - `python3 -c 'import rclpy,sys; print(sys.executable); print(rclpy.__file__); print(sys.path[:8])'`
3. 将 preflight 结果写入 `proof.board_source_preflight`，并参与 root cause 分类。
4. 若 preflight 失败，跳过 `/scan` attempt、initialpose 和 path generation，保留 no-motion false safety fields。
5. 若 preflight 成功，沿用现有 lifecycle / managed runtime 检查，但 `map_server` failure 要有可读 classification。
6. 增加单测覆盖：CLI OK + rclpy fail、CLI timeout、两者 OK 但 lifecycle fail、preflight failure 跳过 scan/path。
7. 更新导航文档，说明 18:45 后读取顺序：source preflight -> map lifecycle -> `/scan` attempts -> AMCL/TF/path。
8. 运行本地验证、真实板短 preflight/helper（可达时）、拉回 artifact，并更新 `tech-done.md`。

## 验收命令

Implementation owner 必须运行并记录：

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --output sprints/2026.07.11_18-45_o3_board_ros_source_map_lifecycle_preflight/artifacts/local_o10_board_ros_source_map_lifecycle_preflight.raw.json
```

本地 Mac 没有 ROS 时允许 exit `2`，但必须 fail-closed 并落盘 artifact，且 artifact 包含 `board_source_preflight`。

真实板可达时必须运行：

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && python3 scripts/o10_amcl_nav2_runtime_proof.py --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --path-generation-opt-in --output /root/rober/onboard/runtime/nav2_lifecycle_latest.json'
```

```bash
ssh -p 37878 root@192.168.1.11 \
  'cat /root/rober/onboard/runtime/nav2_lifecycle_latest.json' \
  > sprints/2026.07.11_18-45_o3_board_ros_source_map_lifecycle_preflight/artifacts/live_o10_board_ros_source_map_lifecycle_preflight.raw.json
```

```bash
rg -n "board_source_preflight|ros2_cli_ok|rclpy_import_ok|map_server|lifecycle|safe_to_control|robot_control_executed|delivery_success|hil_pass" \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.11_18-45_o3_board_ros_source_map_lifecycle_preflight
```

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.11_18-45_o3_board_ros_source_map_lifecycle_preflight
```

## 优先级和验收口径

P0：

- `board_source_preflight` 能拆分 `ros2` CLI 与 `rclpy` import；
- lifecycle / map failure 不再被笼统归为 ROS source；
- 顶层 safety / control / delivery / HIL false 字段保持不变。

P1：

- 文档更新能指导下一条现场命令；
- `tech-done.md` 包含 actual files、verification、artifact key fields、remaining risks。

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：O5，约 `85%`。
- 本 sprint 是否针对该最低 Objective：否。
- 理由：O5 当前仍缺真实 external production evidence，继续本地 readiness/wrapper/probe packet 只会重复 support-only blocker。本轮切到 O3/O1 live no-motion lane，因为它能在当前环境通过真实板或本地 fail-closed helper产生更具体的 current-run path 前置证据；若真实板不可达或只得到 source/lifecycle blocked，本轮不调整 OKR 百分比。

## 输出要求

子 agent 必须返回：

1. 实际改动的文件列表；
2. 验证命令输出结果；
3. local/live artifact 关键字段，尤其是 `board_source_preflight`、`ros2_cli_ok`、`rclpy_import_ok`、`classification`、`map_server_active`、`amcl_active`、`path_generated` 和顶层 false safety fields；
4. 失败定位；
5. 剩余风险；
6. 下一条现场执行命令。
