# O3 Live Localization Sensor Smoke Tech Plan

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 最低 Objective：O5，约 `~85%`。
2. 本 sprint 不直接针对 O5，而是切到 O3 的真实上位机 localization smoke lane。
3. 不针对理由：`sprints/2026.07.11_03-40_o5_external_evidence_or_field_execution_pivot/final.md` 已明确 O5 当前没有新的真实 external production evidence，也没有新的 field execution material；继续 O5 readiness、probe、wrapper、support packet 或 checklist 不会产生新的 `external_artifact_delta`。同时 `sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/final.md` 已把当前最短下一步收敛到 live `/scan`、`/amcl_pose`、`map->odom`、`map->base_link` 和 `localization_not_ready_for_path_generation`。因此本轮应优先解决 localization 前置条件，而不是重复消费 O5/O1 support-only。

## 用户价值和方向判断

### 用户价值

用户需要的是一条真实上位机、当前同窗、可复验、不会触发运动的 smoke 命令链，用来判断定位前置条件是否 ready。只有这样，`/api/nav2/proof/refresh` 的结果才有当前轮意义，后续 O3/O6/O7 才能消费新的现场材料，而不是继续读历史 latest 或 support-only 摘要。

### 方向判断

- O5：**暂停**
- O1 historical / HIL-support-only lane：**暂停**
- O3 live localization smoke lane：**继续**
- O6/O7 surface / readback / checklist 新切片：**暂停，等待本轮新材料**

## 证据边界

本轮 proof boundary 固定为 no-motion localization smoke，只允许落在以下边界内：

- `software_proof_real_board_live_localization_smoke_only`
- `blocked_live_localization_chain_not_ready`
- `software_proof_real_board_no_motion_refresh_readback_only`

无论 smoke 成功还是 fail-closed，顶层都必须保持：

- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `hil_pass=false`
- `robot_control_executed=false`
- `route_execution_success=false`

## 文件范围

主责任 `robot-software-engineer` 执行时允许改动：

- `onboard/scripts/o11_nav2_goal_execution_proof.py`
- `onboard/scripts/field_route_evidence_preflight.py`
- `onboard/tests/test_o11_nav2_goal_execution_proof.py`
- `onboard/tests/test_field_route_evidence_preflight.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/tech-done.md`
- `sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/robot_software_worker_report.md`

条件咨询 `rober-hardware-engineer` 默认只读，可读范围：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/**`
- `docs/hardware/**`
- 当前 sprint artifacts

条件咨询 `robot-algorithm-engineer` 默认只读，可读范围：

- `onboard/scripts/o11_nav2_goal_execution_proof.py`
- `onboard/scripts/field_route_evidence_preflight.py`
- `docs/navigation/**`
- 当前 sprint artifacts

禁止改动：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `onboard/**` 之外未列出的文件
- `pc-tools/**`
- `docs/**` 之外未列出的文件
- 其他 sprint 目录
- 任何默认运动参数、硬件控制默认值或底盘执行入口

## 接口边界

### 允许触达的只读 / no-motion 接口

- `ssh root@192.168.1.11 -p 37878`
- `/api/nav2/proof/refresh`
- `ros2 topic list`
- `ros2 topic echo --once /scan`
- `ros2 topic echo --once /amcl_pose`
- `ros2 run tf2_ros tf2_echo map odom`
- `ros2 run tf2_ros tf2_echo map base_link`
- 与 localization smoke 直接相关的只读 preflight / summary 命令

### 明确禁止的接口与动作

- 禁止发送 `/cmd_vel`
- 禁止调用 `/api/base/manual`
- 禁止执行 Nav2 `NavigateToPose`
- 禁止启动真实底盘运动
- 禁止调用任何会让 `robot_control_executed=true` 的入口
- 禁止把 `safe_to_control`、`delivery_success`、`hil_pass`、`route_execution_success` 写成 true

### 为什么允许 `/api/nav2/proof/refresh`

`/api/nav2/proof/refresh` 在本轮只允许作为 no-motion proof refresh / readback 入口使用。它的唯一用途是复验在 live localization smoke 之后，planner/path 证明是否仍被定位链 blocker 拦住。若该接口会隐式触发运动控制、goal execution 或 managed Nav2 execution，本轮必须直接 fail-closed，保留 no-motion 边界，不得继续执行。

## 技术方案

### 路径 A：真实上位机 live localization smoke

`robot-software-engineer` 在真实上位机 no-motion 环境按固定顺序执行：

1. 确认 SSH 连通；
2. 只读检查 `/scan` 是否 once 可观测；
3. 只读检查 `/amcl_pose` 是否 once 可观测；
4. 只读检查 `map->odom` TF；
5. 只读检查 `map->base_link` TF；
6. 把 smoke 结果写成 ready / blocked 摘要。

允许的正向结果：

- `/scan` ready；
- `/amcl_pose` ready；
- `map->odom` ready；
- `map->base_link` ready；
- 输出 `localization_ready_for_no_motion_refresh=true|false` 的安全摘要。

### 路径 B：smoke 后重跑 `/api/nav2/proof/refresh`

只有在路径 A 完成后才允许重跑 `/api/nav2/proof/refresh`。重跑目标不是执行任务，而是确认在 live localization smoke 后，proof 是否仍然卡在：

- `/scan_once_not_observed`
- `/amcl_pose_once_not_observed`
- `map_to_odom_not_observed`
- `map_to_base_link_blocked_by_missing_map_to_odom`
- `localization_not_ready_for_path_generation`

如果 blocker 改变或消失，要记录新的 blocker 层级；如果 blocker 不变，要明确说明下一轮应落在哪个 localization 子链路。

### 路径 C：fail-closed 分层

若 live smoke 任一步失败，必须明确输出以下分层之一，而不是继续做 wrapper：

- `blocked_scan_not_observed`
- `blocked_amcl_pose_not_observed`
- `blocked_map_to_odom_not_observed`
- `blocked_map_to_base_link_not_observed`
- `blocked_localization_chain_not_ready_for_refresh`
- `blocked_refresh_invokes_motion_or_goal_execution`

## KR 拆解和本轮核心抓手

### KR 拆解

1. 定义一条真实上位机当前同窗 localization smoke 命令链；
2. 将上一轮 refresh blocker 与 live `/scan`、`/amcl_pose`、TF 事实绑定；
3. 在 no-motion 边界内重跑 `/api/nav2/proof/refresh`；
4. 给出下一条现场命令和后续 owner 分工。

### 本轮核心抓手

不再围绕 O5 external readiness 或 O1 historical packet 扩写材料，而是把当前 no-motion proof 的前置条件直接实测一遍。只有这样，后续执行同学才知道是去修雷达/AMCL/TF，还是继续看 planner proof。

## 任务分工

### 主责任务：robot-software-engineer

目标：在不触发任何真实运动的前提下，完成 live localization smoke，并在 smoke 后重跑 `/api/nav2/proof/refresh`。

文件范围：

- `onboard/scripts/o11_nav2_goal_execution_proof.py`
- `onboard/scripts/field_route_evidence_preflight.py`
- `onboard/tests/test_o11_nav2_goal_execution_proof.py`
- `onboard/tests/test_field_route_evidence_preflight.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/tech-done.md`

实现要求：

- 只允许 no-motion、只读 smoke 和 refresh readback；
- 输出必须包含 `/scan`、`/amcl_pose`、`map->odom`、`map->base_link` 的观测结果；
- 输出必须固定 `safe_to_control=false`、`delivery_success=false`；
- 若 refresh 实际会触发 motion / goal execution，必须立即 fail-closed；
- 所有新增技术注释必须使用中文。

验收命令：

```bash
python3 -m py_compile onboard/scripts/o11_nav2_goal_execution_proof.py onboard/scripts/field_route_evidence_preflight.py
python3 -m unittest onboard.tests.test_o11_nav2_goal_execution_proof onboard.tests.test_field_route_evidence_preflight
git diff --check -- onboard/scripts/o11_nav2_goal_execution_proof.py onboard/scripts/field_route_evidence_preflight.py onboard/tests/test_o11_nav2_goal_execution_proof.py onboard/tests/test_field_route_evidence_preflight.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke
```

### 条件咨询：rober-hardware-engineer

仅当 `/scan` 缺失、雷达不上线、串口/供电/驱动事实需要确认时介入。

文件范围：

- 默认只读咨询，不改文件

验收命令：

```bash
rg -n "/scan|lidar|laser|uart|serial|tty" docs/vendor docs/hardware onboard
```

### 条件咨询：robot-algorithm-engineer

仅当 refresh summary 需要判断 path/localization blocker 演化时介入。

文件范围：

- 默认只读咨询，不改文件

验收命令：

```bash
rg -n "/api/nav2/proof/refresh|localization_not_ready_for_path_generation|map_to_odom|map_to_base_link|amcl_pose|/scan" onboard/scripts docs/navigation
```

## 优先级和验收口径

优先级从高到低：

1. `/scan`
2. `/amcl_pose`
3. `map->odom`
4. `map->base_link`
5. `/api/nav2/proof/refresh`
6. blocker 分层与下一条命令

验收通过最低标准：

- 有一份明确的 live localization smoke 计划；
- 文档清楚写出 `/scan`、`/amcl_pose`、`map->odom`、`map->base_link`、`/api/nav2/proof/refresh`；
- 文档清楚写出 `safe_to_control=false`、`delivery_success=false`；
- 文档清楚写出禁止 `/cmd_vel`、`/api/base/manual`、`NavigateToPose` 和真实底盘运动；
- 文档为主责 Engineer 给出文件范围、接口边界、验收命令和 fail-closed proof boundary。

## 验收命令

本轮计划文档验收：

```bash
test -f sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/pre_start.md && test -f sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/prd.md && test -f sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/tech-plan.md
```

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|O5|/scan|/amcl_pose|map->odom|map->base_link|/api/nav2/proof/refresh|safe_to_control=false|delivery_success=false|禁止|验收命令|文件范围|接口边界" sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke
```

```bash
git diff --check -- sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke
```

## 风险、阻塞和需要补齐的证据链

- 风险 1：`/scan` 不可观测，说明问题还在 live sensor / bringup 入口，不能继续把 refresh 失败解释成 planner 单点问题。
- 风险 2：`/amcl_pose` 或 `map->odom` 缺失，说明 localization lifecycle 仍未 ready，后续要转 AMCL/map/TF 修复，而不是重复读 latest。
- 风险 3：`map->base_link` 缺失可能只是继发于 `map->odom` 缺失；要保持 blocker 因果顺序，不要错误归因为底盘运动或 delivery。
- 风险 4：若 refresh 接口隐式触发运动控制，本轮必须立即停在 no-motion 边界，并升级为接口安全问题。

需要补齐的后续真实证据链：

- 当前同窗 `/scan` 观测结果；
- 当前同窗 `/amcl_pose` 观测结果；
- 当前同窗 `map->odom` 与 `map->base_link` TF 结果；
- 当前同窗 refresh summary；
- 若仍 blocked，对应 root cause 的更细分链路。

## 需要创建或更新的 sprint 文档

- `pre_start.md`
- `prd.md`
- `tech-plan.md`
- 后续执行完成后由主责 Engineer 更新 `tech-done.md`
- 若形成可验收结果，再补 `side2side_check.md` 与 `final.md`
