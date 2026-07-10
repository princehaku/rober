# O1 Motion Map HIL Material Bundle Tech Plan

## sprint_type

sprint_type: epic

## 目标

规划一个当前可复验、脱敏、fail-closed 的 O1 `motion_map_hil_material_bundle`。该 bundle 消费同一历史现场 run 中的 first jog command、WAVE ROVER feedback sample、LiDAR scan delta、map output / pixel review、operator report，并固定输出：

- `proof_scope=software_proof_o1_motion_map_hil_material_bundle_only`
- `hil_pass=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

本轮只完成 planning，不修改产品进度和代码。

## 用户价值和产品北极星

用户需要的是“哪些硬件现场事实已经被材料链补强，哪些还没有”，而不是再多一个抽象 summary。`motion_map_hil_material_bundle` 的价值在于把同一历史现场 run 的 motion + map 证据收束到一个可回归的合同里，让后续 current live HIL 执行时能直接替换输入材料，而不是重新手工解释散落 JSON、YAML、PGM 和 operator report。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节里完成度最低的 Objective 是 O5，约 `85%`。
2. 本 sprint 不针对最低 Objective O5，而是转向 O1，约 `87%`。
3. 不推进 O5 的具体理由：
   - `2026.07.10_17-22_o5_production_cutover_readiness_packet/final.md` 已明确 `okr_credit_allowed=false`。
   - 当前仓库没有新的真实 external production evidence，继续做 O5 readiness/support-only 工作不会产生新的可计分材料。
   - O5 现在必须接真实 production cloud、production DB/queue、真实 live endpoint、真实 browser/手机或 production worker/cutover evidence；这些输入当前都缺失。
4. 转向 O1 的理由：
   - O1 仍有明确缺口：current live HIL pass、轮速方向、IMU/battery 标定和 HIL 准入。
   - 仓库里存在尚未成包消费的更强历史现场材料，适合推进 `motion_map_hil_material_bundle`。
   - 本轮会明确把输出锁在 `software_proof_o1_motion_map_hil_material_bundle_only`，不会把历史材料冒充成 current live HIL pass 或 delivery success。

## Owner

- 主责 owner：`robot-hardware-engineer`
- 执行方式：单线闭环。
- `robot-hardware-engineer` 负责后续实现、测试、修复和 `tech-done.md`。
- Product / 主节点只负责验收、`side2side_check.md` 和 `final.md` 收口，不直接写代码、不运行实现命令、不修改硬件配置。

## 后续 implementation 文件范围

允许 `robot-hardware-engineer` 后续修改：

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/**/*motion*map*hil*`
- `onboard/src/ros2_trashbot_hardware/test/**/*motion*map*hil*`
- `onboard/scripts/**/*motion*map*hil*`
- `docs/hardware/**/*.md`
- `sprints/2026.07.10_18-24_o1_motion_map_hil_material_bundle/tech-done.md`

只读输入材料：

- `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/10_pc_first_jog_for_scan_delta.json`
- `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/12_pc_feedback_samples_after_scan_delta_jog.json`
- `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/14_scan_delta_metrics.json`
- `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/18_operator_report_lidar_delta_response.json`
- `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/22_field_first_jog_map.yaml`
- `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/23_field_first_jog_map.pgm`
- `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/24_field_first_jog_map_pixel_review.json`
- `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/30_manual_motion_map.yaml`
- `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/31_manual_motion_map.pgm`
- `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/32_manual_motion_map_pixel_review.json`

禁止后续 implementation 修改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- 本 sprint `pre_start.md`、`prd.md`、`tech-plan.md`，除非 Product 明确要求修正 planning
- O5/O6/O7、PC UI、Nav2 或无关产品文件

## 接口影响

- 仅新增 O1 历史现场材料的只读 software-proof bundle，不改变控制策略、串口配置、launch 默认值或真实硬件动作。
- bundle 只服务 O1 材料链补强；若后续要给 O6/O7 消费，应另起 sprint 明确接口范围。
- map output 只作为 artifact presence 和 pixel review summary 被消费，不作为导航成功接口输入。

## 计划任务

### 1. Vendor 与历史材料事实对齐

- 复核 `docs/vendor/VENDOR_INDEX.md` 指向的 WAVE ROVER 本地资料，采用 UART newline-delimited JSON、`T=1` speed command、`T=130` feedback request、`T=1001` base feedback 等事实。
- 读取历史 artifact，确认同一 run 至少包含：
  - `10`：first jog command forwarded
  - `12`：`t1001_observed_count=3`、`observed_feedback_types=[130,1001]`
  - `14`：`median_abs_diff_m=1.735...`、`changed_bin_ratio=1.0`、`field_pack_pass=true`
  - `18`：`physical_motion_lidar_delta_proven=true`、`wheel_feedback_lr_nonzero_proven=false`、`real_route_map_proven=false`
  - `22-24`：field first jog map output present, `has_free_cells=false`
  - `30-32`：manual motion map output present, `has_free_cells=false`
- 在实现和文档中明确：这些是历史真实现场材料，不是 current live HIL pass。

### 2. `motion_map_hil_material_bundle` 合同

- 新增一个 O1 bundle 输出，schema 名必须含 `motion_map_hil_material_bundle`。
- 输出字段建议包括：
  - `schema`
  - `status`
  - `proof_scope`
  - `source_refs`
  - `same_run_material_present`
  - `first_jog_command_present`
  - `feedback_sample_present`
  - `feedback_types_summary`
  - `scan_delta_present`
  - `scan_delta_summary`
  - `operator_report_present`
  - `operator_claim_summary`
  - `field_first_jog_map_present`
  - `manual_motion_map_present`
  - `pixel_review_summary`
  - `map_output_present`
  - `map_navigation_ready=false`
  - `blocked_reasons`
  - `next_required_evidence`
  - `hil_pass=false`
  - `safe_to_control=false`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
- 建议 status 使用保守命名，例如 `motion_map_hil_material_bundle_ready_not_hil_pass`。

### 3. 脱敏与 fail-closed 规则

- 只输出 safe summary；不得输出 raw payload、绝对路径、token、URL、base64、traceback、完整 endpoint、source base URL 或设备敏感上下文。
- 以下情况必须 fail-closed：
  - 任一核心 artifact 缺失；
  - run 关联关系无法证明；
  - `14` 与 `18` 的 scan delta / operator claim 对不上；
  - `22-24`、`30-32` 的 map / pixel review 配对不完整；
  - 输入尝试把 `hil_pass`、`safe_to_control`、`delivery_success`、`primary_actions_enabled` 置为 true；
  - map pixel review 结论与实际 `has_free_cells=false` 不一致；
  - JSON / YAML / PGM review 解析失败或字段类型异常。
- fail-closed 时仍应保留安全的 blocked reason 和 next required evidence，方便下一轮现场补证。

### 4. 测试与文档

- 增加单元测试覆盖：
  - positive historical run：成功汇总 `10`、`12`、`14`、`18`、`22-24`、`30-32`
  - missing feedback sample blocked
  - scan delta / operator report mismatch blocked
  - map / pixel review mismatch blocked
  - unsafe path / url / token / traceback 不外泄
  - dangerous true fields blocked
- 同步最小硬件文档，说明采用的 vendor 来源、历史材料来源、证据边界和仍未满足的 current live HIL 条件。
- implementation 完成后更新本 sprint `tech-done.md`，记录实际改动、验证结果、失败定位和剩余风险。

## 验收命令

后续 implementation 必须至少运行：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/*.py onboard/scripts/*.py
python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*motion*map*hil*.py'
git diff --check -- onboard/src/ros2_trashbot_hardware onboard/scripts docs/hardware sprints/2026.07.10_18-24_o1_motion_map_hil_material_bundle
```

本 planning 阶段验收命令为：

```bash
test -f sprints/2026.07.10_18-24_o1_motion_map_hil_material_bundle/pre_start.md && test -f sprints/2026.07.10_18-24_o1_motion_map_hil_material_bundle/prd.md && test -f sprints/2026.07.10_18-24_o1_motion_map_hil_material_bundle/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|O5|O1|motion_map_hil_material_bundle|software_proof_o1_motion_map_hil_material_bundle_only|robot-hardware-engineer" sprints/2026.07.10_18-24_o1_motion_map_hil_material_bundle
git diff --check -- sprints/2026.07.10_18-24_o1_motion_map_hil_material_bundle
```

## 证据边界

必须固定：

- `proof_scope=software_proof_o1_motion_map_hil_material_bundle_only`
- `hil_pass=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

不能宣称：

- current live HIL pass
- hardware safe-to-control
- delivery success
- usable navigation map proven
- Nav2 route execution success
- production cloud / endpoint / DB success

## 风险和阻塞

- 历史材料能补强 O1 motion + map 材料链，但不是 current live HIL。
- `12` 只有反馈采样观察摘要，没有轮速方向或 IMU/battery 标定结论。
- `24` 和 `32` 都显示 `has_free_cells=false`，说明当前 bundle 只能承认 map artifact 存在，不能承认导航可用。
- 如果后续实现只做 wrapper/checklist，而没有真正消费历史 artifact 并生成 `motion_map_hil_material_bundle`，则不满足本轮目标。
- 后续仍需要新的同 run live HIL 记录、轮速方向确认、IMU/battery 标定、HIL acceptance record 和可用路线地图材料，Product 才能考虑继续上调 O1。
