# PC Tools Node/Vue Workstation Side2Side Check

## sprint_type

epic

## 对照范围

对照本轮 PRD 和补充只读边界，检查新增工作站是否满足第一阶段：

- 统一入口包含 Route Debug、Evidence Tools、Training/Labeling、Proof Boundary。
- 保留 `pc-tools/evidence/**` 和 `pc-tools/route/**` Python gate，不删除、不重命名、不改变 CLI 语义。
- 所有 API/UI fail closed。
- 不证明真实 ROS2、硬件、Nav2、HIL、真实手机或云端链路。

## 对照结果

- Route Debug：通过。API 返回旧 `schema=trashbot.pc_route_debug_console.v1` 映射字段、`evidence_boundary=software_proof_docker_pc_route_debug_console_gate`、`console_controls=read_only` 和 fail-closed 条件；UI 只显示只读字段与原 gate 命令说明。
- Evidence Tools：通过。只扫描 `pc-tools/evidence` 文件名、分类、测试配对和 docstring 摘要；不执行 Python gate。
- Training/Labeling：通过。明确 `placeholder_not_connected` 和 `real_pipeline_connected=false`。
- Proof Boundary：通过。集中展示 `can_prove` 与 `not_proven`，并固定控制策略为 `workstation_executes_control=false`、`workstation_executes_python_gate=false`。
- 旧 route Python gate：通过。`python -m unittest discover pc-tools/route -p "test_*.py"` 仍为 7 tests OK。

## 禁止项核对

- 未调用 ROS2，未 import ROS2，未访问 ROS graph。
- 未打开串口，未写硬件配置，未写 `pc-tools/route/**` 或 `pc-tools/evidence/**`。
- UI/API 不提供 `/cmd_vel`、Start、Confirm、Cancel、dropoff、collect 或真实控制入口。
- UI/API 固定 `source=software_proof`、`proof_status=not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`pc_only=true`。

## 验收结论

第一阶段 PC-only Node/Vue 工作站满足软件证明边界。验收范围止于本地软件 proof，不外推到真实机器人、硬件、HIL、手机或云端。
