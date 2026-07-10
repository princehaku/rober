# O1 Free-Cell Map Material Bundle Tech Plan

## sprint_type

sprint_type: epic

## 目标

规划一次 O1 hardware material bundle 扩展：由 `robot-hardware-engineer` 在后续 implementation 中扩展现有 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`，消费同一 2026-06-22 field run 的 free-cell map materials 33-38，输出安全字段并保留严格证据边界。

建议输出字段：

- `free_cell_map_material_present=true`
- `free_cell_map_lifecycle_present=true`
- `free_cell_map_list_present=true`
- `free_cell_map_yaml_present=true`
- `free_cell_map_pgm_present=true`
- `free_cell_pixel_review_present=true`
- `free_cell_pixel_count=394`
- `free_cell_has_free_cells=true`
- `free_cell_usable_map_count=1`
- `map_navigation_material_ready=true`

必须固定：

- `proof_scope=software_proof_o1_motion_map_hil_material_bundle_only`
- `hil_pass=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

本 planning 阶段不修改产品代码、测试、`OKR.md` 或 `docs/process/okr_progress_log.md`。

## 用户价值和产品北极星

用户需要最终可安全送达的机器人。这个 sprint 的价值是把“同 run 地图已修复出 free cells”变成后续 HIL / Nav2 路线验证可引用的 material summary，让执行团队下一步可以对照明确缺口：地图 material 有 free cells，但 HIL、安全控制和送达闭环仍未证明。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节里完成度最低的 Objective 是 O5，约 `85%`。
2. 本 sprint 不针对最低 Objective O5，而是转向 O1，约 `88%`。
3. 不继续 O5 的理由：
   - `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/final.md` 明确 O5 `okr_credit_allowed=false`。
   - O5 当前缺真实 external production evidence，包括公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic 和真实 phone/browser 材料。
   - 没有这些真实材料时，O5 readiness / probe / support-only packet 只能作为回归守护，不应继续计主 OKR 增量。
4. 转向 O1 的理由：
   - O1 下一步缺口仍包括 current live HIL、轮速方向、IMU/battery 标定、可用路线地图和现场 acceptance。
   - 上一轮 O1 已消费同 run `22-24` / `30-32`，但两组 map review 都是 `has_free_cells=false`。
   - 同一 artifact 目录还存在未消费的 `33-38` free-cell map materials：`34` 显示 `has_usable_map`、`usable_map_count=1`、`map_usable_for_navigation=true`，`37` 显示 `free_pixel_count=394`、`has_free_cells=true`。
   - 本轮是新同 run field material delta，不是重复上一轮 historical wrapper；目标是把 free-cell map materials 作为 additive safe summary 接入现有 bundle。

## Owner 和执行方式

- 主责 owner：`robot-hardware-engineer`
- 执行方式：单 owner 单线闭环。
- Product / 主节点只负责 planning、验收和收口，不直接写产品代码或运行 implementation 验证命令。

## 后续 implementation 文件范围

允许 `robot-hardware-engineer` 后续修改：

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_motion_map_hil_material_bundle.py`
- `onboard/src/ros2_trashbot_hardware/test/test_wave_rover_motion_map_hil_material_bundle.py`
- `docs/hardware/wave_rover_motion_map_hil_material_bundle.md`
- `sprints/2026.07.10_19-25_o1_free_cell_map_material_bundle/tech-done.md`

只读输入材料：

- `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/33_pc_map_start_after_free_pixel_fix.json`
- `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/34_pc_map_list_after_free_pixel_fix.json`
- `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/35_fixed_free_cells_map.yaml`
- `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/36_fixed_free_cells_map.pgm`
- `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/37_fixed_free_cells_map_pixel_review.json`
- `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/38_pc_summary_after_map_fix.json`

禁止后续 implementation 修改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- 本 sprint `pre_start.md`、`prd.md`、`tech-plan.md`，除非 Product 明确要求修正 planning
- O5/O6/O7、PC UI、Nav2 或无关业务文件

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
- `map_navigation_material_ready=true` 仅表示 free-cell map material 可支持后续定位/路径 proof 输入，不表示 Nav2 route execution 已成功。
- 若未来要给 O6/O7 消费这些字段，需要另起 sprint 明确 archive/readback/UI 范围。

## 计划任务

### 1. 扩展默认输入路径

在 `DEFAULT_PATHS` 中加入 33-38：

- `free_cell_map_start_json`
- `free_cell_map_list_json`
- `free_cell_map_yaml`
- `free_cell_map_pgm`
- `free_cell_pixel_review_json`
- `free_cell_pc_summary_json`

CLI 也应支持逐项覆盖，方便 negative smoke。

### 2. 新增 free-cell map group parser

解析目标：

- `33`：确认 map lifecycle start after free pixel fix，且 safety fields 均为 false。
- `34`：确认 `map_quality_summary.status=has_usable_map`、`usable_map_count=1`、`map_usable_for_navigation=true`、`robot_control_executed=false`。
- `35` / `36`：确认 YAML image basename 与 PGM basename 配对。
- `37`：确认 `schema=trashbot.map_pgm_pixel_review.v1`、PGM header 匹配、`free_pixel_count=394`、`has_free_cells=true`。
- `38`：只消费 allowlisted status/material fields，不能回显 `source_base_url`、endpoint、absolute path、camera refs、raw runtime context 或 secret-like text。

### 3. Summary 输出规则

Positive output 必须包含：

- `free_cell_map_material_present=true`
- `free_cell_map_summary`
- `free_cell_pixel_review_summary`
- `free_cell_pixel_count=394`
- `free_cell_has_free_cells=true`
- `map_navigation_material_ready=true`
- `map_navigation_ready=false` 或保留原字段不变，并明确它不等于 route execution
- 全部 fixed false safety fields

建议 status 保持现有保守命名 `motion_map_hil_material_bundle_ready_not_hil_pass`，避免误导为 HIL pass。

### 4. Fail-closed 和脱敏规则

以下情况必须 fail-closed：

- 任一 33-38 核心 artifact 缺失、不可读或 schema mismatch。
- `34` 没有 `has_usable_map`、`usable_map_count != 1` 或 `map_usable_for_navigation` 不是 true。
- `35` YAML image 与 `36` PGM basename 不匹配。
- `37` PGM header/counts 不匹配、`free_pixel_count != 394` 或 `has_free_cells` 不是 true。
- `33`、`34`、`38` 试图把 `safe_to_control`、`delivery_success`、`primary_actions_enabled`、`robot_control_executed` 或 `hil_pass` 置 true。
- 被消费字段出现 URL、token、secret、password、absolute path、`/dev/tty`、baudrate、raw frame、base64 或 traceback。

Fail-closed 输出必须保留 `blocked_reasons` 和 `next_required_evidence`，同时保持全部 fixed false fields。

### 5. 测试与文档

新增或更新测试覆盖：

- positive historical free-cell map materials 33-38，期望 `free_cell_pixel_count=394`、`map_navigation_material_ready=true`。
- missing free-cell pixel review blocked。
- map list `usable_map_count=0` blocked。
- pixel review `free_pixel_count` 不等于 `394` blocked。
- YAML/PGM basename mismatch blocked。
- unsafe URL/path/token/traceback 不外泄。
- dangerous true fields blocked。
- CLI default ready 和 negative override exit `4`。

同步 `docs/hardware/wave_rover_motion_map_hil_material_bundle.md`，说明 free-cell material 是 historical same-run software proof，不是 current live HIL、安全控制或 delivery success。

## 验收命令

后续 implementation 必须至少运行：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/*.py
python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*motion*map*hil*.py'
PYTHONPATH=onboard/src/ros2_trashbot_hardware python3 -m ros2_trashbot_hardware.wave_rover_motion_map_hil_material_bundle
git diff --check -- onboard/src/ros2_trashbot_hardware docs/hardware sprints/2026.07.10_19-25_o1_free_cell_map_material_bundle
```

本 planning 阶段验收命令：

```bash
test -f sprints/2026.07.10_19-25_o1_free_cell_map_material_bundle/pre_start.md && test -f sprints/2026.07.10_19-25_o1_free_cell_map_material_bundle/prd.md && test -f sprints/2026.07.10_19-25_o1_free_cell_map_material_bundle/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|O5|O1|free-cell|free_cell|has_usable_map|394|software_proof_o1_motion_map_hil_material_bundle_only|robot-hardware-engineer" sprints/2026.07.10_19-25_o1_free_cell_map_material_bundle
git diff --check -- sprints/2026.07.10_19-25_o1_free_cell_map_material_bundle
```

## 证据边界

本 sprint 可以证明：

- 同一 2026-06-22 field run 存在 free-cell map fix materials 33-38。
- free-cell map material 可被当前软件安全 intake。
- `free_pixel_count=394` 和 `has_usable_map` 可进入 O1 bundle 的脱敏摘要。

本 sprint不能证明：

- current live HIL
- hardware safe-to-control
- delivery success
- wheel direction
- IMU/battery calibration
- production cloud
- Nav2 route execution success
- route delivery completion

## 风险和阻塞

- 这是 historical same-run software proof，不是当前上车实时 HIL。
- `map_navigation_material_ready=true` 容易被误读，必须在代码、文档和 closeout 中反复限定为 material readiness。
- 仍缺 `feedback_T1001.log`、motion command、operator/external observation、HIL acceptance、wheel direction、IMU/battery calibration 和 delivery record。
- 如果实现没有真正消费 33-38，而只是硬编码字段或复用上一轮 wrapper，则不满足本 sprint 目标。

## 下一步派发摘要

派给 `robot-hardware-engineer`：

- 文件范围：`wave_rover_motion_map_hil_material_bundle.py`、对应 `test_wave_rover_motion_map_hil_material_bundle.py`、`docs/hardware/wave_rover_motion_map_hil_material_bundle.md`、本 sprint `tech-done.md`。
- 核心任务：扩展现有 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`，消费 33-38 free-cell materials，输出 `free_cell_map_material_present=true`、`free_cell_pixel_count=394`、`map_navigation_material_ready=true` 等安全字段，并保持所有 safety/delivery/production/HIL 字段 false。
- 验收命令：`py_compile`、motion-map-HIL unittest、默认 CLI smoke、scoped `git diff --check`。
