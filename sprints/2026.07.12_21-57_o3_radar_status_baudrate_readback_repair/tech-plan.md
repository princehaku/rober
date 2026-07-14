# Tech Plan - O3 Radar Status Baudrate Readback Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/`
- Product owner: `product-okr-owner`
- Primary owner: `robot-software-engineer` / Robot Software
- Conditional owner: `robot-algorithm-engineer` / Algorithm
- Plan status: ready for implementation dispatch

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 / 当前最高优先级里最低进度 Objective 是 O5，约 `85%`。
2. 本 sprint 不直接针对 O5。
3. 不针对 O5 的理由：O5 缺真实 external production evidence；继续 support/readiness 包、review、handoff 或 surface readback 不计分。按最低可推进规则，本轮转向当前可推进且不重复消费 O5 blocker 的 O3/O1 strict no-motion lane。
4. 本轮若只修复 `/api/radar/status` baudrate readback，或只产出 blocker narrowing，没有 same-run path generation、route execution、delivery/operator acceptance、current live HIL 或 production external evidence，则 OKR 百分比 `不调整`，KR `不归档`。

## 最近两轮 Blocker 扫描结论

- `2026.07.12_19-56_o3_scan_qos_endpoint_readback_split/final.md`: `/scan` publisher endpoint visible/stable，QoS compatible but no samples，runtime split 观察到 `serial.serialutil.SerialException`；仍 `path_generation_attempted=false`、`path_generated=false`、`safe_to_control=false`。
- `2026.07.12_20-57_o3_lidar_runtime_hardware_probe/final.md`: 现有 `150000` lifecycle 已观察 `/scan` once/hz、`/lidar/raw_packet` 和 TF；holder PID `550922` owns `/dev/ttyACM0`；实际 start/scan-proof commands 使用 `--serial-baudrate 150000`；但 `/api/radar/status` top-level 仍为 `baudrate=230400`。
- 结论：本轮新 blocker 是 radar status / lifecycle config drift，不是继续包装旧 `/scan_reliable_and_best_effort_timeout`，也不是第三次消费同一根因。

## 技术方案

### Gate 1 - Robot Software: 修复 radar status baudrate readback

目标：`/api/radar/status` 的 top-level `baudrate` 反映 current lifecycle/status command 或 diagnostics，而不是 stale default `230400`。

建议实现：

- 在 `UpperRobotApi.radar_status()` 中新增稳定的 baudrate 选择逻辑。
- 优先级建议：
  1. `lifecycle_status_readback.baudrate`。
  2. `lifecycle_status_readback.latest_result.baudrate`。
  3. `driver_diagnostics_latest.runtime.serial_baudrate` 或同等 current diagnostics 字段。
  4. `controls.start.command.argv` / `controls.scan_proof_refresh.runtime_command.argv` 中解析出的 `--serial-baudrate`，仅作为 readback fallback，并标注 source。
  5. 都缺失时返回 fail-closed status，不把 `230400` 当作 current readback。
- 输出字段建议包含：
  - `baudrate`
  - `baudrate_readback_source`
  - `baudrate_readback_status`
  - `baudrate_candidates`
  - `vendor_reference_baudrate=230400`
  - `historical_field_baudrate_candidate=150000`
- 继续保留 `controls.start` 和 `controls.scan_proof_refresh` 的 command readback，方便 Product 验收 `150000` 一致性。

Robot Software 文件范围：

- `/Users/m1/apps/rober/onboard/scripts/upper_robot_api.py`
- `/Users/m1/apps/rober/onboard/tests/test_upper_robot_api.py`
- `/Users/m1/apps/rober/docs/hardware/board_sensor_stack_smoke.md`
- `/Users/m1/apps/rober/sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/tech-done.md`

Robot Software 接口影响：

- `GET /api/radar/status` top-level `baudrate` 语义从 static/reference default 改为 current readback。
- 新增 readback provenance 字段必须向后兼容；不得删除既有 `controls.*`、`driver_diagnostics_latest`、`lifecycle_status_readback`、no-motion false fields。
- PC/手机消费者看到的 `baudrate=150000` 代表 current runtime readback，不代表 vendor clean exclusive `230400` 被否定。

Robot Software 验收命令：

```bash
python3 -m py_compile onboard/scripts/upper_robot_api.py
python3 -m unittest onboard.tests.test_upper_robot_api onboard.tests.test_lidar_lifecycle_script
git diff --check -- onboard/scripts/upper_robot_api.py onboard/tests/test_upper_robot_api.py docs/hardware/board_sensor_stack_smoke.md sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/tech-done.md
```

Robot Software true-board/readback 验收命令（由 owner 在实现后执行或明确说明环境不可达）：

```bash
curl -s http://127.0.0.1:8787/api/radar/status | python3 -m json.tool
curl -s http://127.0.0.1:8787/api/radar/status | rg '"baudrate": 150000|"baudrate_readback_source"|"--serial-baudrate"|safe_to_control'
```

Robot Software 接受标准：

- `/api/radar/status.baudrate=150000`，且 provenance 指向 lifecycle/status command 或 diagnostics。
- `/api/radar/status.controls.start.command.argv` 和 `.controls.scan_proof_refresh.runtime_command.argv` 仍能读出 `--serial-baudrate 150000`。
- 旧 `230400` 只能作为 vendor/reference/default candidate，不再作为 current lifecycle readback。
- `safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false` 保持 false。

### Gate 2 - Algorithm: 复用 150000 lifecycle 做 strict no-motion path proof

进入条件：Gate 1 已通过，且 Product/Robot Software 确认 `/api/radar/status` readback 不再 stale。

目标：不启动第二个 LiDAR driver，复用现有 `150000` lifecycle，重跑 `/scan` -> `/amcl_pose` -> dynamic `map->odom` -> planner-only path proof。

Algorithm 文件范围：

- `/Users/m1/apps/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `/Users/m1/apps/rober/onboard/tests/test_nav2_runtime_proof_helper.py`
- `/Users/m1/apps/rober/docs/navigation/field_route_evidence_preflight.md`
- `/Users/m1/apps/rober/docs/navigation/fixed_route_workflow.md`
- `/Users/m1/apps/rober/sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/tech-done.md`
- `/Users/m1/apps/rober/sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/artifacts/`

Algorithm 接口影响：

- 不新增运动接口。
- 不调用 NavigateToPose。
- 不发布 `/cmd_vel`。
- 不调用 `/api/base/manual`。
- 不打开 WAVE ROVER UART。
- proof artifact 必须继续声明 `strict no-motion` 和 no-motion false fields。

Algorithm 验收命令：

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
git diff --check -- onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_nav2_runtime_proof_helper.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/tech-done.md
```

Algorithm true-board strict no-motion 验收命令（owner 根据当前板端路径调整 output，但不得改变安全边界）：

```bash
python3 /root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --strict-no-motion \
  --no-base-uart \
  --managed-runtime-opt-in \
  --managed-lidar-serial-port /dev/ttyACM0 \
  --managed-lidar-serial-baudrate 150000 \
  --initialpose-opt-in \
  --path-generation-opt-in \
  --output /root/rober/onboard/runtime/o3_radar_status_baudrate_readback_repair.raw.json
```

Algorithm artifact 验收 `rg`：

```bash
rg -n '"baudrate"|150000|"/scan"|"/amcl_pose"|map_to_odom|path_generation_attempted|path_generated|safe_to_control|publishes_cmd_vel|calls_base_manual|uses_base_uart|route_execution_success|delivery_success|hil_pass' \
  sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/artifacts
```

Algorithm 接受标准：

- 同 run artifact 明确 `/scan` sample/readiness 事实。
- 同 run artifact 明确 `/amcl_pose` 是否 observed，并给出 frame/timing。
- 同 run artifact 明确 dynamic `map->odom` 是否 observed。
- 若 `path_generation_attempted=true`，必须是 planner-only path proof，且 `route_execution_success=false`。
- 若 `path_generated=false`，必须输出下一最窄 blocker，不能回退到 stale radar status 或 generic `/scan` wrapper。

## 派单顺序

1. 先派 Robot Software 单线闭环。
2. Product 验收 Robot Software readback gate。
3. 只有 readback gate 通过后，再派 Algorithm。
4. Hardware 不并行进入，除非需要 exclusive-holder USB/power/baud check；该检查必须另立边界并读 vendor docs。

## 安全边界

本 sprint 全程 strict no-motion：

- no `/cmd_vel`
- no `/api/base/manual`
- no NavigateToPose
- no WAVE ROVER UART
- no `/dev/ttyS5`
- no route execution
- no delivery claim
- no current live HIL claim

所有实现、测试、文档和 artifact 必须保留：

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

## Product 验收命令

计划文档验收命令：

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|radar status|baudrate|150000|230400|Robot Software|Algorithm|strict no-motion|safe_to_control=false|不调整|不归档" sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/pre_start.md sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/prd.md sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/tech-plan.md
git diff --check -- sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/pre_start.md sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/prd.md sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/tech-plan.md
```

## 收口规则

- 如果只证明 `/api/radar/status` readback 一致，但没有 same-run path/route/delivery，则 Product closeout 写 `不调整`、`不归档`。
- 如果 Algorithm 证明 planner-only path generated，也只能计为 O3/O1 no-motion path proof；仍不得声明 route execution、delivery、HIL 或 safe-to-control。
- 只有新增 same-run path generation success、route execution success、delivery/operator acceptance、current live HIL 或 production external evidence，Product 才能考虑 OKR 增量或 KR 归档。
