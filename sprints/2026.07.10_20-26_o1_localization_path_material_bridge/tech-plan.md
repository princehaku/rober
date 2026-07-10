# O1 Localization Path Material Bridge Tech Plan

## sprint_type

sprint_type: epic

## 目标

规划一次 O1 hardware material bridge：由 `robot-hardware-engineer` 在后续 implementation 中扩展现有 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`，消费 `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/38_pc_summary_after_map_fix.json` 的 same-run localization/material readback，并可选引用 June 11 clean-baseline path evidence 作为 cross-run comparator。

本 sprint 的语义是 `localization_path_material_bridge`：material bridge / localization readiness proof only。它不是 current live HIL，不是真实 safe-to-control，不是真实 delivery success，不是真实 Nav2 route execution success。

必须固定：

- `proof_scope=software_proof_o1_motion_map_hil_material_bundle_only`
- `hil_pass=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`
- `same_run_path_proven=false`
- `nav2_route_execution_success=false`

本 planning 阶段不修改产品代码、测试、`OKR.md` 或 `docs/process/okr_progress_log.md`。

## 用户价值和产品北极星

用户需要最终可安全送达的机器人。这个 sprint 的价值是把“已有 free-cell map material”继续接到 localization/path readiness material，让执行团队下一步知道当前卡在 same-run path 未生成，而不是继续围绕历史 free-cell intake 做同层包装。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节里完成度最低的 Objective 是 O5，约 `85%`。
2. 本 sprint 不针对最低 Objective O5，而是转向 O1，约 `89%`。
3. 不继续 O5 的理由：
   - `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/final.md` 明确 O5 `okr_credit_allowed=false`。
   - O5 当前缺真实 external production evidence，包括公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic 和真实 phone/browser 材料。
   - 没有这些真实材料时，O5 readiness / probe / support-only packet 只能作为回归守护，不应继续计主 OKR 增量。
4. 转向 O1 的理由：
   - O1 最近两轮已消费 historical same-run motion/map/free-cell materials，当前约 `89%`。
   - 上一轮 `final.md` 要求下一步把 free-cell material 接到 current/live localization/path proof。
   - `38_pc_summary_after_map_fix.json` 中存在新的 same-run localization/path readback：`map_once_observed=true`、`amcl_pose_observed=true`、localization TF map-to-odom / map-to-base-link 为 true。
   - 同一 artifact 的 path 字段仍明确失败：`path_generation_succeeded=false`、`path_generated=false`、`path_point_count=0`。因此本轮可推进 localization readiness material bridge，但必须 fail-closed 标明 same-run path 仍未证明。

## Owner 和执行方式

- 主责 owner：`robot-hardware-engineer`
- 执行方式：单 owner 单线闭环。
- Product / 主节点只负责 planning、验收和收口，不直接写产品代码或运行 implementation 验证命令。

## 后续 implementation 文件范围

允许 `robot-hardware-engineer` 后续修改：

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_motion_map_hil_material_bundle.py`
- `onboard/src/ros2_trashbot_hardware/test/test_wave_rover_motion_map_hil_material_bundle.py`
- `docs/hardware/wave_rover_motion_map_hil_material_bundle.md`
- `sprints/2026.07.10_20-26_o1_localization_path_material_bridge/tech-done.md`

只读输入材料：

- `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/38_pc_summary_after_map_fix.json`
- `sprints/2026.06.11_11-15_clean_baseline_nav2_path_refresh/artifacts/nav2_latest_after_success.json`
- `sprints/2026.06.11_11-15_clean_baseline_nav2_path_refresh/artifacts/nav2_retry_summary.json`
- `sprints/2026.06.11_11-15_clean_baseline_nav2_path_refresh/tech-done.md`

禁止后续 implementation 修改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- 本 sprint `pre_start.md`、`prd.md`、`tech-plan.md`，除非 Product 明确要求修正 planning
- O5/O6/O7、PC UI、cloud relay、Nav2 execution 或无关业务文件

## Vendor 和事实来源

后续 Hardware owner 必须继续采用 `docs/vendor/VENDOR_INDEX.md` 指向的本地 WAVE ROVER 资料。当前现有 module 已引用：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`

本 sprint 不新增串口、引脚、电压、波特率、速度映射或固件假设；只扩展历史 artifact safe summary。

## 接口影响

- 继续使用现有 schema：`trashbot.wave_rover_motion_map_hil_material_bundle.v1`。
- 只新增 additive fields，不改变控制策略、串口配置、launch 默认值、真实硬件动作或 `/cmd_vel` 行为。
- `localization_path_material_bridge_present=true` 只表示 same-run localization/path readback 被安全 intake。
- `same_run_path_proven=false` 必须保留，因为当前 `38` 中 path 未成功。
- `cross_run_clean_baseline_path_comparator_present=true` 只表示 June 11 comparator 被安全引用，不代表 same-run path proof。
- 若未来要给 O6/O7 消费这些字段，需要另起 sprint 明确 archive/readback/UI 范围。

## 计划任务

### 1. 扩展默认输入路径

在 `DEFAULT_PATHS` 中新增或复用：

- `free_cell_pc_summary_json` 指向 `38_pc_summary_after_map_fix.json`
- 可选 `clean_baseline_nav2_path_latest_json`
- 可选 `clean_baseline_nav2_path_retry_summary_json`

CLI 应支持逐项覆盖，方便 negative smoke 和 comparator 禁用。

### 2. 新增 localization/path bridge parser

解析 `38` 的 allowlisted endpoints：

- `status` / `/api/status`
- `map_proof_latest` / `/api/map/proof/latest`
- `localize_proof_latest` / `/api/localize/proof/latest`
- `nav2_status` / `/api/nav2/status`
- `nav2_proof_latest` / `/api/nav2/proof/latest`

必须提炼并校验：

- `map_once_observed=true`
- `amcl_pose_observed=true`
- `localization_tf_observed.map_to_odom=true`
- `localization_tf_observed.map_to_base_link=true`
- `path_generation_requested=true` 从 `nav2_proof_latest`
- `path_generation_succeeded=false`
- `path_generated=false`
- `path_point_count=0`
- `planner_server_active=true` 可作为 same-run path attempt context，但不能变成成功证明

`localization_tf_observed` 在 `38` 中可能是 JSON 字符串，implementation 必须结构化解析，解析失败要 fail-closed，不能用字符串包含判断替代结构校验。

### 3. 可选 cross-run comparator

若引用 June 11 clean-baseline path evidence，只能消费安全摘要：

- `schema`
- `evidence_ref`
- `status`
- `path_generated=true`
- `path_generation_succeeded=true`
- `path_point_count=31`
- `amcl_pose_observed=true`
- `localization_tf_observed.map_to_odom=true`
- `localization_tf_observed.map_to_base_link=true`
- fixed false safety fields

Comparator 输出必须命名为 `cross_run_clean_baseline_*`，不能覆盖 `same_run_*` 字段。

### 4. Summary 输出规则

Positive output 必须包含：

- `localization_path_material_bridge_present=true`
- `same_run_localization_material_present=true`
- `same_run_map_once_observed=true`
- `same_run_amcl_pose_observed=true`
- `same_run_localization_tf_map_to_odom=true`
- `same_run_localization_tf_map_to_base_link=true`
- `same_run_path_generation_requested=true`
- `same_run_path_generation_succeeded=false`
- `same_run_path_generated=false`
- `same_run_path_point_count=0`
- `same_run_path_proven=false`
- `localization_path_bridge_ready_not_route_execution_proof=true`
- `map_navigation_material_ready=true` 保持上一轮语义：free-cell material ready only
- `map_navigation_ready=false`
- 全部 fixed false safety fields

Status 建议保持现有保守命名 `motion_map_hil_material_bundle_ready_not_hil_pass`，避免误导为 HIL pass 或 route execution pass。

### 5. Fail-closed 和脱敏规则

以下情况必须 fail-closed：

- `38` 缺失、不可读或 schema 不是 `trashbot.pc_tools_workstation.robot_control_summary.v1`。
- required endpoint 缺失或 request/http status 不可用。
- `map_once_observed`、`amcl_pose_observed` 或 localization TF 两个关键边任一不是 true。
- `localization_tf_observed` 无法结构化解析。
- same-run path 字段试图声称 `path_generation_succeeded=true`、`path_generated=true` 或 `path_point_count>0`，除非未来另起 sprint 明确 current/same-run path proof 输入；本 sprint 必须保持 path not proven。
- `38` 或 comparator 试图把 `safe_to_control`、`delivery_success`、`primary_actions_enabled`、`robot_control_executed`、`hil_pass`、`nav2_route_execution_success` 置 true。
- 被消费字段出现 URL、token、secret、password、absolute path、`/dev/tty`、baudrate、raw frame、base64 或 traceback。
- June 11 comparator 缺 fixed false safety fields 或清理边界时，comparator section 必须 disabled / blocked，而不是影响 same-run localization readiness。

Fail-closed 输出必须保留 `blocked_reasons` 和 `next_required_evidence`，同时保持全部 fixed false fields。

### 6. 测试与文档

新增或更新测试覆盖：

- positive historical same-run localization/path bridge from `38`。
- `localization_tf_observed` JSON string 结构化解析。
- missing `localize_proof_latest` blocked。
- missing TF map-to-base-link blocked。
- same-run path 被篡改为 generated/succeeded/point_count>0 blocked。
- optional June 11 comparator 正例只进入 `cross_run_*` 字段。
- unsafe URL/path/token/traceback 不外泄。
- dangerous true fields blocked。
- CLI default ready 和 negative override exit `4`。

同步 `docs/hardware/wave_rover_motion_map_hil_material_bundle.md`，说明 localization_path_material_bridge 是 historical same-run software proof，不是 current live HIL、安全控制、Nav2 route execution 或 delivery success。

## 验收命令

后续 implementation 必须至少运行：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/*.py
python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*motion*map*hil*.py'
PYTHONPATH=onboard/src/ros2_trashbot_hardware python3 -m ros2_trashbot_hardware.wave_rover_motion_map_hil_material_bundle
rg -n "localization_path_material_bridge|same_run_path_proven|path_point_count|software_proof_o1_motion_map_hil_material_bundle_only" onboard/src/ros2_trashbot_hardware docs/hardware sprints/2026.07.10_20-26_o1_localization_path_material_bridge
git diff --check -- onboard/src/ros2_trashbot_hardware docs/hardware sprints/2026.07.10_20-26_o1_localization_path_material_bridge
```

本 plan-stage 验收命令：

```bash
test -f sprints/2026.07.10_20-26_o1_localization_path_material_bridge/pre_start.md && test -f sprints/2026.07.10_20-26_o1_localization_path_material_bridge/prd.md && test -f sprints/2026.07.10_20-26_o1_localization_path_material_bridge/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|O5|O1|localization_path_material_bridge|localization|path|free_cell|software_proof_o1_motion_map_hil_material_bundle_only|robot-hardware-engineer" sprints/2026.07.10_20-26_o1_localization_path_material_bridge
git diff --check -- sprints/2026.07.10_20-26_o1_localization_path_material_bridge
```

## 证据边界

本 sprint 可以证明：

- 同一 2026-06-22 field run 中，free-cell map material 后已有 localization readback material。
- `map_once_observed=true`、`amcl_pose_observed=true`、localization TF map-to-odom / map-to-base-link 可被当前软件安全 intake。
- same-run path attempt context 可被安全读取，并明确 `path_generation_succeeded=false`、`path_generated=false`、`path_point_count=0`。
- June 11 clean-baseline path proof 可作为 cross-run comparator，帮助说明“path proof 的成功形态是什么”。

本 sprint 不能证明：

- current live HIL
- hardware safe-to-control
- delivery success
- wheel direction
- IMU/battery calibration
- production cloud
- current live map navigation readiness
- same-run Nav2 path generation success
- Nav2 route execution success
- route delivery completion

## Closeout 条件

Product closeout 可建议 O1 `89% -> 90%` 的条件：

- implementation 确实消费 `38` 的 same-run localization/path readback。
- positive output 包含 localization readiness true 和 same-run path false。
- fail-closed tests 覆盖 missing TF、missing endpoint、path false 被伪造成 true、unsafe 字段和 dangerous true。
- 文档明确 proof boundary 为 `software_proof_o1_motion_map_hil_material_bundle_only`。
- `tech-done.md` 记录验证输出和剩余风险。

不得上调 O1 的情况：

- 只重复上一轮 `free_cell` fields。
- 只引用 June 11 clean-baseline comparator。
- 未消费 `38` 中的 localization/path readback。
- 输出中出现 `same_run_path_proven=true`、`safe_to_control=true`、`delivery_success=true`、`hil_pass=true` 或 `nav2_route_execution_success=true`。

## 风险和阻塞

- 这是 historical same-run software proof，不是当前上车实时 HIL。
- `path_generation_requested=true` 容易被误读成 path success，必须在代码、文档和 closeout 中固定 `same_run_path_proven=false`。
- June 11 comparator 的 `path_point_count=31` 可能被误读为本 run 结果，字段必须带 `cross_run` 前缀。
- 仍缺 current live `feedback_T1001.log`、motion command、operator/external observation、HIL acceptance、wheel direction、IMU/battery calibration、delivery record 和 route execution result。
- 如果实现没有真正消费 `38`，而只是硬编码 localization fields 或复用上一轮 wrapper，则不满足本 sprint 目标。

## 下一步派发摘要

派给 `robot-hardware-engineer`：

- 文件范围：`wave_rover_motion_map_hil_material_bundle.py`、对应 `test_wave_rover_motion_map_hil_material_bundle.py`、`docs/hardware/wave_rover_motion_map_hil_material_bundle.md`、本 sprint `tech-done.md`。
- 核心任务：扩展现有 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`，消费 `38_pc_summary_after_map_fix.json` 的 same-run localization/path readback，输出 `localization_path_material_bridge_present=true`、`same_run_map_once_observed=true`、`same_run_amcl_pose_observed=true`、`same_run_path_proven=false` 等安全字段，并保持所有 safety/delivery/production/HIL/route execution 字段 false。
- 验收命令：`py_compile`、motion-map-HIL unittest、默认 CLI smoke、anchor `rg`、scoped `git diff --check`。
