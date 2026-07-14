# Tech Plan - O3 Lightweight CLI Readiness Gate

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Target: replace `ros2 --help` as the sole hard readiness gate with a lighter structured CLI readiness plan, so the helper can enter downstream map/AMCL/TF/planner path gates or emit a narrower fail-closed blocker under strict no-motion.

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节里完成度最低的 Objective：Objective 5，约 `85%`。
2. 本 sprint 不直接针对 Objective 5。
3. 不针对 Objective 5 的理由：Objective 5 当前仍缺真实 production external evidence，近期 O5 readiness、credit、readback 都已被 Product 定性为 support-only，继续消费只会重复同一 external blocker。相反，最新 true-board artifact 已把 O3/O1 runtime blocker 收窄到 `board_source_preflight_ros2_cli_invocation_timeout`，其中 `source_stage_ok=true`、`ros2_cli_path_ok=true`、`rclpy_import_ok=true`，说明当前环境里最短的可执行动作，是让 helper 从 `ros2 --help` 单点硬阻塞切到 lightweight CLI readiness gate，再回到 `map_lifecycle_proof_not_clean`、AMCL、TF 和 planner path gate。

## OKR 映射和方向判断

- 用户价值和产品北极星：让 true-board no-motion 诊断重新朝固定路线送垃圾闭环推进，而不是停在 support-only surface。北极星仍是一键固定路线送达垃圾点。
- 方向判断：`继续` O3/O1 strict no-motion runtime lane。
- O5 判断：`暂停` support-only/readback/wrapper 计分动作。
- O6/O7 判断：`暂停` 新 archive/readback/consumer-only surface。
- KR 历史归档：本轮计划阶段 `不归档`。执行收口若无 mission-grade evidence 也不得归档。
- OKR 百分比：本轮不应调整 OKR 百分比，除非执行阶段出现 same-run path generation success、route execution、delivery/operator acceptance、current live HIL 或 production external evidence。

## KR 拆解

1. KR-A：为 helper 设计轻量 CLI readiness gate，比较 heavy help、lightweight readiness、`rclpy` import 三层信号，不再把 `ros2 --help` 作为唯一硬门槛。
2. KR-B：当 source/path/rclpy 已通过时，尽量让 `cli_ready=true` 进入 `/map_server`、`/amcl_pose`、dynamic `map->odom` 和 planner path gate。
3. KR-C：如果仍 fail-closed，artifact 必须把 blocker 收窄到具体的 lightweight CLI / daemon / runtime 分类，而不是回退成泛化 source mismatch。
4. KR-D：local dry-run 与 true-board run 全程 strict no-motion，所有安全和运动字段保持 false，并把结果写入 `tech-done.md` 与 `artifacts/`。

## 本轮核心抓手

### 1. Lightweight CLI Readiness Layering

`robot-software-engineer` 需要把 helper readiness 至少分成三层事实：

- heavy help：保留 `ros2 --help` 或等价重型命令作为观察项，而不是唯一硬阻塞；
- lightweight readiness：例如 `ros2 --version`、`ros2 daemon status`、或其他更轻的可执行调用，具体由工程判断，但必须是 strict no-motion 且能更快反映 CLI 可用性；
- `rclpy` import：保留 Python 侧导入和 runtime graph/lifecycle 需要的依赖事实。

artifact 应能区分：

- source 失败；
- path lookup 失败；
- heavy help 超时；
- lightweight readiness 通过/失败；
- `rclpy` import 通过/失败；
- `cli_ready` 与 `runtime_ready` 的最终判断。

### 2. Preserve Previous Artifact Facts

实现不应丢失上一轮关键读数，而应以 additive 方式保留或兼容：

- `board_source_preflight_ros2_cli_invocation_timeout`
- `ros2 --help`
- `source_stage_ok=true`
- `ros2_cli_path_ok=true`
- `rclpy_import_ok=true`
- `cli_ready=false`
- `runtime_ready=false`
- `map_lifecycle_proof_not_clean`

如果新 artifact 不再以 `ros2 --help` 为 primary blocker，`tech-done.md` 必须解释新的 primary 判定为何更可靠。

### 3. Return to Runtime and Path Gate

只有 readiness 足够放行后，才继续读取：

- `/map_server` lifecycle；
- `/amcl_pose` sample；
- dynamic `map->odom`；
- `map->base_link` 是否仍 blocked by missing `map->odom`；
- planner path generation gate。

不得因为 CLI 可执行就跳过 localization/path 事实，也不得越过 no-motion 边界去做 route execution。

### 4. Strict No-Motion Boundary

所有 helper、dry-run、true-board run 和 artifact 必须保持：

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`

并且严禁：

- NavigateToPose；
- `/cmd_vel`；
- `/api/base/manual`；
- WAVE ROVER UART。

`path_generation_attempted` 与 `path_generated` 只有在 planner-only no-motion path gate 真正触发时才允许变化；未进入该 gate 时必须继续 false。

## Engineer Assignment

主责：`robot-software-engineer`

原因：任务集中在 helper readiness、unit tests、navigation docs、artifact 和本 sprint `tech-done.md`，文件范围集中，单 owner 可以闭环实现、验证和修复。

## 文件范围

Product 本轮仅修改：

- `sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate/pre_start.md`
- `sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate/prd.md`
- `sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate/tech-plan.md`

Implementation owner 允许修改：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate/tech-done.md`
- `sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate/artifacts/`

Implementation owner 不允许修改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- 产品代码范围外文件
- 任何历史 sprint 目录
- 硬件配置、launch 参数、WAVE ROVER UART 相关接线或控制路径

## 接口影响

- helper artifact 允许 additive 扩展，但必须保持旧字段读取兼容，避免下游消费者因为字段替换而失真。
- readiness 字段应同时保留 heavy help 与 lightweight readiness 的观测，不回显敏感路径、token 或完整 traceback。
- 文档同步仅限 `docs/navigation/field_route_evidence_preflight.md` 与 `docs/navigation/fixed_route_workflow.md` 的 no-motion helper/preflight 读法。
- safety contract 保持 fail-closed。

## 验收命令

Implementation owner 必须执行并在 `tech-done.md` 记录以下命令和结果：

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

local dry-run 与 true-board strict no-motion 命令可由工程按实现后的 artifact 命名调整，但必须满足：

- local run 产生 fail-closed 或 ready artifact；
- true-board run 若可达，必须产出当前 sprint `artifacts/` 下的新 raw artifact；
- 全程 no-motion，不得 NavigateToPose、不得发布 `/cmd_vel`、不得调用 `/api/base/manual`、不得打开 WAVE ROVER UART。

scoped diff check：

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate
```

## No-Motion 边界

graph/lifecycle/localization ready 前不得尝试：

- NavigateToPose；
- `/cmd_vel`；
- `/api/base/manual`；
- WAVE ROVER UART；
- 任何 route execution、delivery action 或真实控制执行。

如果 artifact 或日志显示发生上述动作，本轮直接判定越界，不可验收。

## Product Closeout 口径

closeout 时必须按下面规则判断：

1. 只有出现 same-run path generation success、route execution、delivery/operator acceptance、current live HIL 或 production external evidence，才允许调整 `OKR.md` 百分比。
2. 如果只得到 helper readiness / lifecycle / localization supporting artifact，则 `OKR.md` 百分比继续 `不调整`。
3. 如果没有 mission-grade evidence，则 `不归档` KR，仍只记录为 O3/O1 supporting diagnostic delta。
4. 如果本轮只是把 `ros2 --help` timeout 文案换皮，没有形成 heavy/light/rclpy 分层事实，也没有更窄 blocker，closeout 不通过。

## 风险、阻塞和要补齐的证据链

- 风险 1：true-board 上 lightweight readiness 也可能受 CLI plugin discovery、daemon 状态或首次调用冷启动影响。
- 风险 2：`cli_ready=true` 后仍可能立刻暴露 `map_lifecycle_proof_not_clean`、`/amcl_pose` timeout、dynamic `map->odom` missing 或 planner path gate blocker。
- 风险 3：local dry-run 只能证明 fail-closed 或结构化分类，不替代 true-board artifact。
- 风险 4：O5 support-only lane 仍可能诱导回流；Product closeout 必须继续禁止用 wrapper/readback 充当 mission progress。
- 缺失证据链：same-run path generation success、route execution、delivery/operator acceptance、current live HIL、production external evidence。

## 需要创建或更新的 sprint 文档

本轮 Product planning 创建：

- `sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate/pre_start.md`
- `sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate/prd.md`
- `sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate/tech-plan.md`

执行阶段由 `robot-software-engineer` 继续更新：

- `sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate/tech-done.md`
- `sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate/artifacts/`

验收/收口阶段后续补：

- `side2side_check.md`
- `final.md`
