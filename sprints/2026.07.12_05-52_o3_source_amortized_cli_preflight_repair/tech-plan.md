# Tech Plan - O3 Source-Amortized CLI Preflight Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_05-52_o3_source_amortized_cli_preflight_repair/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Target: put helper source, ROS2 path lookup, CLI readiness checks, and target CLI invocation into one amortized shell so the helper can move past `board_source_preflight_ros2_cli_which_timeout` / `workspace_source_or_env_mismatch` or report a narrower fail-closed blocker.

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节里完成度最低的 Objective：Objective 5，约 `85%`。
2. 本 sprint 不直接针对 Objective 5。
3. 不针对 Objective 5 的理由：Objective 5 当前缺真实公网 HTTPS/TLS、4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence；近期 O5 readiness packet 和 credit gate 已明确 `okr_credit_allowed=false` / support-only。继续做 O5 wrapper、readback、probe 或 readiness packet 会重复消费同一 external production blocker，不能产生主 OKR 增量。本轮转向 O3/O1 no-motion helper preflight repair，是因为上一轮 manual graph readback 已成功，但 helper 主路径仍 blocked 在 `board_source_preflight_ros2_cli_which_timeout` / `workspace_source_or_env_mismatch`；修复该 blocker 是当前环境里回到 same-run path generation、route execution、delivery/operator acceptance、current live HIL 或 production external evidence 前最短的可执行前置动作。

## OKR 映射和方向判断

- 用户价值和产品北极星：让 true-board 现场诊断重新朝固定路线送垃圾闭环推进，而不是停在 support-only surface。北极星仍是一键固定路线送达垃圾点。
- 方向判断：`继续` O3/O1 strict no-motion runtime lane。
- O5 判断：`暂停` support-only/readback/wrapper 计分动作。
- O6/O7 判断：`暂停` 新 archive/readback/consumer-only surface。
- KR 历史归档：本轮计划阶段 `不归档`。没有 mission-grade evidence 时，执行收口也不得归档 KR。
- OKR 百分比：本轮不应调整 OKR 百分比，除非执行阶段出现 same-run path generation success、route execution、delivery/operator acceptance、current live HIL 或 production external evidence。

## KR 拆解

1. KR-A：修复 helper source/CLI preflight，使 source、path lookup、`command -v` / `which` / `type -a ros2` 和目标 CLI invocation 在同一个 amortized shell 中完成或返回结构化 fail-closed detail。
2. KR-B：helper preflight ready 后继续尝试读取 `/map_server`、`/amcl_pose`、dynamic `map->odom` 和 planner path gate。
3. KR-C：本地 dry-run 和 true-board run 均保留 no-motion false fields，不允许任何运动或底盘 UART。
4. KR-D：把实际改动、验证命令、artifact 结论、失败定位和剩余风险写入本 sprint `tech-done.md`。

## 本轮核心抓手

### 1. Source-Amortized ROS2 CLI Preflight

Robot Software 应把 helper 当前分散的 source、path lookup 和 CLI readiness 逻辑合并到一个 bounded shell 中，至少在同一个 sourced environment 内采集：

- source command return code、elapsed time、stdout/stderr tail；
- `command -v ros2`；
- `which ros2`；
- `type -a ros2`；
- minimal ROS2 CLI readiness command；
- 后续 helper 需要执行的目标 CLI invocation。

输出必须能区分：

- source 本身失败；
- source 成功但 ROS2 executable 不可见；
- executable 可见但 CLI invocation timeout；
- CLI ready 但 runtime graph/lifecycle/localization gate 失败。

### 2. Path / Env Mismatch Root-Cause Detail

artifact 中继续保留上一轮 blocker 字段，并在修复后用更窄分类替代泛化结论：

- `board_source_preflight_ros2_cli_which_timeout`
- `workspace_source_or_env_mismatch`
- `skipped_without_sourced_ros2_cli_ready`

如果仍命中这些字段，`tech-done.md` 必须解释为什么 single-shell amortization 未消除它，并给出下一条命令或下一跳 owner。

### 3. Return to Runtime and Path Gate

只有 helper preflight ready 后，才继续读取：

- `/map_server` lifecycle；
- `/amcl_pose` sample；
- dynamic `map->odom`；
- `map->base_link` 是否仍 blocked by missing `map->odom`；
- planner path generation gate。

不得因为 graph topic 可见而跳过 localization readiness。

### 4. Strict No-Motion Boundary

所有 helper、dry-run、true-board run 和 artifact 必须保持：

- `path_generation_attempted=false`，除非只是在 no-motion planner gate 内请求 path proof 且没有 route execution；
- `path_generated=false`，除非同 run planner path 确实生成；
- `safe_to_control=false`；
- `publishes_cmd_vel=false`;
- `calls_base_manual=false`;
- `robot_control_executed=false`;
- `route_execution_success=false`;
- `delivery_success=false`;
- `hil_pass=false`;
- `uses_base_uart=false`;

严禁 NavigateToPose、`/cmd_vel`、`/api/base/manual`、WAVE ROVER UART。

## Engineer Assignment

主责：`robot-software-engineer`

原因：当前任务集中在 ROS2 helper source/CLI preflight、targeted unit tests、navigation docs 和 sprint artifact，同一 owner 可以单线闭环完成实现、验证、修复和 `tech-done.md`，不需要并行拆给其他角色。

## 允许工程文件范围

Implementation owner 允许修改：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.12_05-52_o3_source_amortized_cli_preflight_repair/tech-done.md`
- `sprints/2026.07.12_05-52_o3_source_amortized_cli_preflight_repair/artifacts/`

Implementation owner 不允许修改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- 其他 sprint 目录
- O5/O6/O7 support-only code path
- 硬件配置、launch 参数或 WAVE ROVER UART 接线/串口路径

## 接口影响

- helper artifact 允许 additive 扩展，但必须保持旧字段读取兼容。
- 新增字段应优先描述 source/CLI readiness 的 bounded shell 事实，不回显敏感路径、token 或完整 traceback。
- 文档同步仅限 `docs/navigation/field_route_evidence_preflight.md` 与 `docs/navigation/fixed_route_workflow.md` 中的 no-motion helper/preflight 读法。
- Safety contract 保持 fail-closed。

## 验收命令

Implementation owner 必须执行并在 `tech-done.md` 记录以下命令和结果。

### Static / Unit

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

### Local Fail-Closed Helper Dry-Run

本地 dry-run 必须不触发运动，并在缺 true-board runtime 时 fail-closed。Robot Software 可按实现后的 CLI 参数调整 map/pose 路径，但必须保留 no-motion 语义和 artifact 输出：

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --strict-no-motion \
  --no-base-uart \
  --output-json sprints/2026.07.12_05-52_o3_source_amortized_cli_preflight_repair/artifacts/local_source_amortized_cli_preflight_dry_run.raw.json
```

验收要点：

- exit code 可以是 fail-closed 非零；
- artifact 必须说明 missing runtime / missing board / env mismatch 的边界；
- 不得发布 `/cmd_vel`、不得调用 `/api/base/manual`、不得打开 WAVE ROVER UART。

### True-Board Strict No-Motion Push / Run / Pull

若 true board SSH 可达，执行 strict no-motion helper push/run/pull。以下命令是推荐骨架，Robot Software 可按现场路径修正，但不得改变 no-motion 边界：

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && /usr/bin/timeout 240s /usr/bin/python3.10 scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --output-json /tmp/live_o10_source_amortized_cli_preflight.raw.json'
```

```bash
scp -P 37878 root@192.168.1.11:/tmp/live_o10_source_amortized_cli_preflight.raw.json \
  sprints/2026.07.12_05-52_o3_source_amortized_cli_preflight_repair/artifacts/live_o10_source_amortized_cli_preflight.raw.json
```

如果 SSH 不可达，`tech-done.md` 必须写清不可达原因，例如 network timeout、auth failure、host unreachable 或 board path missing；不得用旧 artifact 冒充本轮 true-board run。

### Scoped Diff Check

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.12_05-52_o3_source_amortized_cli_preflight_repair
```

## Product 计划文档验收命令

Product planning 完成后仅运行文档级检查：

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|board_source_preflight_ros2_cli_which_timeout|workspace_source_or_env_mismatch|robot-software-engineer|python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper|git diff --check" sprints/2026.07.12_05-52_o3_source_amortized_cli_preflight_repair
```

```bash
git diff --check -- sprints/2026.07.12_05-52_o3_source_amortized_cli_preflight_repair
```

## No-Motion Boundary

graph/lifecycle/localization ready 前不得尝试：

- NavigateToPose；
- `/cmd_vel`；
- `/api/base/manual`；
- WAVE ROVER UART；
- 任何 robot motion、route execution 或 delivery action。

如果 artifact 或日志显示上述动作发生，本轮直接判为越界，不可验收。

## Product Closeout 口径

closeout 时必须按下面规则判断：

1. 只有出现 same-run path generation success、route execution、delivery/operator acceptance、current live HIL 或 production external evidence，才允许调整 `OKR.md` 百分比。
2. 如果只得到 helper preflight/runtime/localization supporting artifact，则 `OKR.md` 百分比继续 `不调整`。
3. 如果没有 mission-grade evidence，则 `不归档` KR，仍只记录为 O3/O1 supporting diagnostic delta。
4. 如果仍停留在同一个 `board_source_preflight_ros2_cli_which_timeout` / `workspace_source_or_env_mismatch` 且没有更窄原因，closeout 必须按接近同一 blocker 重复消费处理，并要求同 owner 返工或升级下一跳决策。

## 风险、阻塞和要补齐的证据链

- 风险 1：single-shell amortization 后仍因 true-board IO 慢导致 CLI invocation timeout。
- 风险 2：helper preflight ready 后暴露新的 lifecycle/localization blocker，例如 `/map_server` inactive、`/amcl_pose` timeout 或 dynamic `map->odom` missing。
- 风险 3：本地 dry-run 只能证明 fail-closed 行为，不能替代 true-board artifact。
- 风险 4：manual graph readback 成功可能诱导过度计分；Product closeout 必须坚持 no-motion supporting boundary。
- 缺失证据链：same-run path generation success、route execution、delivery/operator acceptance、current live HIL、production external evidence。

## 需要创建或更新的 sprint 文档

本轮 Product planning 创建：

- `sprints/2026.07.12_05-52_o3_source_amortized_cli_preflight_repair/pre_start.md`
- `sprints/2026.07.12_05-52_o3_source_amortized_cli_preflight_repair/prd.md`
- `sprints/2026.07.12_05-52_o3_source_amortized_cli_preflight_repair/tech-plan.md`

执行阶段由 `robot-software-engineer` 继续更新：

- `sprints/2026.07.12_05-52_o3_source_amortized_cli_preflight_repair/tech-done.md`
- `sprints/2026.07.12_05-52_o3_source_amortized_cli_preflight_repair/artifacts/`

验收/收口阶段后续补：

- `side2side_check.md`
- `final.md`
