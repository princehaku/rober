# O3 Nav2 Map AMCL TF Runtime Repair Tech Plan

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节完成度最低的主 Objective 是 O5，约 `~85%`。
2. 本 sprint 不直接推进 O5。
3. 转向理由：`sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/final.md` 与 `sprints/2026.07.11_03-40_o5_external_evidence_or_field_execution_pivot/final.md` 已连续证明 O5 缺真实 production external evidence，继续 readiness/probe/support packet 会重复消费同一 blocker，且 `okr_credit_allowed=false`。当前真实板已经暴露新的 O3 runtime 根因，优先级应切到能产生现场 runtime / path 前置事实的 no-motion Nav2 repair。

## Owner 与分工

- `robot-software-engineer` 单线闭环：
  - 修复或确认 `o11_nav2_lifecycle.sh -> autonomous.launch.py nav2_stack_only:=true -> upper_robot_api.py -> o10_amcl_nav2_runtime_proof.py -> field_route_evidence_preflight.py` 的 no-motion runtime 调用链；
  - 运行本地静态检查、单测、local dry-run 和 live ssh 预检；
  - 如首轮验证失败，继续定位并修复；
  - 更新 `tech-done.md` 与本 sprint artifacts。
- 主节点：
  - 只负责派单、验收和后续收口文档；
  - 不直接改产品代码，不直接跑实现验证命令。

## 文件范围

允许修改：

- `onboard/scripts/o11_nav2_lifecycle.sh`
- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/scripts/field_route_evidence_preflight.py`
- `onboard/scripts/upper_robot_api.py`
- `onboard/tests/test_o11_nav2_lifecycle_script.py`
- `onboard/tests/test_map_lifecycle_proof_helper.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `onboard/tests/test_field_route_evidence_preflight.py`
- `onboard/tests/test_upper_robot_api.py`
- `onboard/src/ros2_trashbot_bringup/launch/autonomous.launch.py`
- `onboard/src/ros2_trashbot_bringup/test/**`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_10-39_o3_nav2_map_amcl_tf_runtime_repair/tech-done.md`
- `sprints/2026.07.11_10-39_o3_nav2_map_amcl_tf_runtime_repair/artifacts/**`

不得修改：

- O5/O6/O7 relay、archive、PC workstation、cloud readiness、support packet 文件；
- WAVE ROVER 底盘协议、串口速度映射、默认运动控制入口；
- 本 sprint 目录外的其他 sprint 文档，除非只读引用。

## 接口影响

- `/api/nav2/start` 允许受管启动 Nav2 runtime，但只能停留在 no-motion runtime 层，不允许 goal execution。
- `/api/nav2/proof/refresh` 允许在 `managed_runtime_opt_in=true` 前提下读取同轮 runtime / localization / planner proof，但不得把 `starts_nav2=true` 误写成 `safe_to_control=true`。
- `o11_nav2_lifecycle.sh` 与 `autonomous.launch.py` 若有调整，必须继续保持 `nav2_stack_only:=true` 跳过 waypoint、固定路线、云中转、底盘手动控制等非本轮需要的链路。
- summary-facing artifact 不得回显敏感 token、连接串、完整 traceback、危险原始输出或与本轮无关的长路径细节。

## 技术方案

1. 先审计受管启动链：
   - `o11_nav2_lifecycle.sh` 的 start/status/stop 逻辑；
   - `autonomous.launch.py nav2_stack_only:=true` 的节点裁剪；
   - `upper_robot_api.py` 对 lifecycle proof 和 refresh proof 的读取映射；
   - `o10_amcl_nav2_runtime_proof.py` 对 map server / AMCL / planner / TF / initialpose 的 no-motion proof 逻辑。
2. 围绕上一轮 live artifact 的明确根因做修复：
   - `map_server_not_active`
   - `amcl_not_active`
   - `tf_missing`
   - `/map topic_type=null`
   - `/amcl_pose publisher_count=0`
3. 优先修“runtime 未拉起或未进入 lifecycle”这一层，再判断 AMCL pose / TF 是否自然恢复；不要先继续包装 refresh timeout。
4. `field_route_evidence_preflight.py` 如需改动，目标应是把新的 runtime 事实完整收敛进 artifact，而不是新建 another wrapper。若 refresh 仍失败，必须让 artifact 能明确区分：
   - lifecycle 没起来；
   - map topic 未建立；
   - AMCL 无 publisher；
   - `map->odom` 缺失；
   - `map->base_link` 仅因上游 TF 缺失而 blocked。
5. 文档同步更新导航 runbook，说明本轮 no-motion runtime repair 的前提、禁止命令和 proof boundary。

## 风险边界

- 严禁 `/cmd_vel`、`/api/base/manual`、NavigateToPose goal 和任何真实底盘运动。
- 严禁把 historical 或 cross-run 的已有 map/path/TF 材料覆盖本轮 same-run false 结论。
- 允许 `starts_nav2=true`，但必须持续固定：
  - `safe_to_control=false`
  - `robot_control_executed=false`
  - `delivery_success=false`
  - `hil_pass=false`
- 如果真实板不可达，或 live proof 仍旧失败，只能收口为新的 runtime blocker，不得上调 OKR。

## 验收命令

子 agent 必须运行并汇报结果：

```bash
bash -n onboard/scripts/o11_nav2_lifecycle.sh
```

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/field_route_evidence_preflight.py onboard/scripts/upper_robot_api.py
```

```bash
python3 -m unittest onboard.tests.test_o11_nav2_lifecycle_script onboard.tests.test_map_lifecycle_proof_helper onboard.tests.test_nav2_runtime_proof_helper onboard.tests.test_field_route_evidence_preflight onboard.tests.test_upper_robot_api
```

```bash
python3 -m unittest discover -s onboard/src/ros2_trashbot_bringup/test
```

```bash
python3 onboard/scripts/field_route_evidence_preflight.py --mode local --dry-run --output sprints/2026.07.11_10-39_o3_nav2_map_amcl_tf_runtime_repair/artifacts/local_preflight.raw.json
```

```bash
python3 onboard/scripts/field_route_evidence_preflight.py --mode ssh --ssh-target root@192.168.1.11 --ssh-port 37878 --timeout-s 12 --output sprints/2026.07.11_10-39_o3_nav2_map_amcl_tf_runtime_repair/artifacts/live_nav2_map_amcl_tf.raw.json
```

```bash
git diff --check -- onboard/scripts/o11_nav2_lifecycle.sh onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/field_route_evidence_preflight.py onboard/scripts/upper_robot_api.py onboard/tests/test_o11_nav2_lifecycle_script.py onboard/tests/test_map_lifecycle_proof_helper.py onboard/tests/test_nav2_runtime_proof_helper.py onboard/tests/test_field_route_evidence_preflight.py onboard/tests/test_upper_robot_api.py onboard/src/ros2_trashbot_bringup/launch/autonomous.launch.py onboard/src/ros2_trashbot_bringup/test docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.11_10-39_o3_nav2_map_amcl_tf_runtime_repair
```

## 交付判断

- 通过：
  - 本地检查通过；
  - live artifact 给出新的 runtime 事实；
  - 没有运动命令。
- 高价值通过：
  - lifecycle 可读；
  - `/map` 建立；
  - `/amcl_pose` 有 publisher；
  - `map->odom` 或 `map->base_link` 至少有一个推进到 observed；
  - refresh 不再停在上一轮同类 timeout。
- 不通过：
  - 只改文档或只复述旧 artifact；
  - 继续把 generic blocker 包成新 summary；
  - 打开任何运动相关 true 字段；
  - 没有 live artifact 却宣称现场修复成功。
