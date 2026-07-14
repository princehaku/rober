# Tech Done

- `sprint_type: epic`
- Owner：`robot-algorithm-engineer`
- 状态：实施与单次现场验证已完成；post-write clean gate 保守失败，按 `blocked_with_root_cause` 交 Product 验收。
- 现场窗口：`2026-07-14T21:30:04Z` 至 `2026-07-14T21:31:49Z`（Asia/Shanghai 为 `2026-07-15 05:30:04` 至 `05:31:49`）。
- 目标：`root@192.168.1.11:37878`，canonical map `/root/rober/onboard/runtime/maps/trashbot_map.yaml`。

## 实际改动

### `onboard/scripts/o10_amcl_nav2_runtime_proof.py`

- 新增 persisted pose 审计，明确区分仓库 `set_initial_pose: true`、helper 临时参数/runtime effective `false`、startup log 与 current live `/amcl_pose` / `map->odom`；静态配置 presence 不再被当作 live consumption。
- 新增 canonical map YAML/PGM SHA256、尺寸、threshold/mode、确定性 free cell 与 image-to-world 换算；同时兼容 inline 和 map_saver 三行 YAML `origin`，字段、PGM 或 free cell 不可审计时 fail-closed。
- 新增 `--initialpose-canonical-free-cell-opt-in` 与完整写前门禁：map_server/AMCL lifecycle、fresh `/scan`、只归属 `/amcl` 的 `/initialpose` subscriber、persisted audit 与 TF authority 必须全部 clean。
- 将 `/initialpose` 实际发布总次数硬限制为 `<=1`：rclpy 路径最多 publish 一条；只有 rclpy attempt 仍为 `0` 时才允许 CLI `--once` fallback；实际 attempt 已为 `1` 后禁止任何 fallback/重发。
- `/initialpose` endpoint inventory 进入最终 TF source diagnostics，避免 rclpy 已观测 subscriber 但写前 ownership audit 丢失该 topic。
- 新增 post-write gate，要求 fresh `/scan`、fresh `/amcl_pose`、parsed stamp、dynamic `map->odom`、`attributed_unique_amcl` 与 fresh TF。
- cleanup 只作用于 helper `start_new_session=True` 创建的 PGID；信号前核对 PID/PGID/members identity，记录 remaining processes 与 residual。
- 所有控制、路径、履约和 HIL 字段保持 false；proof boundary 固定为 `robot_runtime_o3_strict_no_motion_controlled_initialpose_localization_proof_only`。

### `onboard/tests/test_nav2_runtime_proof_helper.py`

- 更新既有 gate/status 断言，并新增 canonical free cell/world pose、多行 `origin`、无 free cell fail-close、persisted config 不等于 live consumption、persisted live skip、rclpy attempt 后禁止 CLI、写前失败保持 attempt `0`、`/initialpose` subscriber 保留与 cleanup identity mismatch 拒绝信号等回归。
- 最终 targeted suite 为 `155` 项。

### `docs/navigation/field_route_evidence_preflight.md`

- 同步 controlled initialpose 的 opt-in、persisted/canonical/pre-write/post-write/attempt/cleanup 合同。
- 将 TF 归因值统一为更严格的 `attributed_unique_amcl`，并明确本证据不证明真实物理位姿、路径、路线、履约、HIL 或 safe-to-control。

### Sprint artifacts

- 首轮预检失败证据保留为 `artifacts/algorithm/attempt1-*`；最终现场 artifact 为 `artifacts/algorithm/runtime-proof.json` 与 `runtime-proof.pretty.json`。
- 新增 local validation、SHA/readback、graph before/after、结构断言、clean-gate 失败、forbidden scan、stable process readback 与运行时间记录。

## 失败定位与修复链

### 首轮：写前 fail-closed，实际发布 0 次

- 初始 helper SHA：`57b9c69c35934fd747d28bdda19f9d78b8edc3bb6dba64bfcb74cde57f04a38f`。
- 首轮窗口：`2026-07-14T21:23:11Z` 至 `21:24:48Z`；runtime exit `2`。
- `initialpose_publish_attempts=0`、`initialpose_publish_attempted=false`、`initialpose_published=false`，因此没有消费单次发布额度。
- 写前 blocker 1：现场 map_saver YAML 使用三行 `origin`，初版 parser 只接受 inline list。
- 写前 blocker 2：rclpy probe 已采到 `/initialpose` subscriber `/amcl`、count `1`，但最终 `topic_endpoint_summaries` 只保留 localization signal topics，ownership audit 因此误得 count `0`。
- 修复后补回归并重新跑本地围栏；没有改 launch/config、硬件参数或运动链路。

### 修复后唯一一次现场运行：发布 1 次，不再复跑

- 修复版 local/remote SHA 均为 `8212a95c89a5d4626df3e418867e7bb265199f7d0e9404280136a6022d50f2f7`。
- 预部署只读 canonical 审计：`free_cell_verified=true`、`world_pose_auditable=true`。
- deterministic free cell 为 `row=30,column=125,pixel=254`；world pose 为 `frame_id=map,x=0.8011511639109115,y=4.12500006146729,yaw=0.0`。
- persisted audit clean：仓库 config presence 不算 live consumption；helper/runtime `set_initial_pose=false`，发布前没有 fresh pose/TF live consumption。
- 写前 gate 全绿：map_server/AMCL active、`/initialpose` subscriber count `1` 且只归属 `/amcl`、fresh `/scan`、canonical pose 与 TF authority clean。
- 实际 `initialpose_publish_attempts=1`、`initialpose_publish_attempted=true`、`initialpose_published=true`，method=`ros2_topic_pub_once_cli_fallback`。从这一刻起严格禁止本 sprint 第二次发布或第三次 live run。
- 发布后观测到 fresh `/amcl_pose`：frame `map`、stamp parsed、age `96ms`；fresh `/scan` age `22ms`。
- 发布后观测到 dynamic `map->odom`，stamp parsed，publisher attribution=`attributed_unique_amcl`；但最终 freshness age=`5090ms`，超过 `3000ms` 门槛。
- post-write gate 唯一 blocker 为 `map_to_odom_fresh`；因此 runtime exit `2`，clean assertion exit `1`，不得宣称 localization clean acceptance。
- 当前 artifact 不能区分“AMCL 在静止窗口没有继续刷新 TF”与“collector 在早期采样后到统一 freshness 判定之间消耗了约 5 秒”；发布额度已用尽，本轮不再通过重发或复跑消除此歧义。

## 验证结果

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_nav2_runtime_proof_helper.py`：PASS。
- `python3 -m unittest onboard/tests/test_nav2_runtime_proof_helper.py`：`Ran 155 tests in 2.279s`，`OK`。
- required field `rg` 与 scoped `git diff --check`：PASS。
- `runtime_structural_assertions.log`：PASS；确认 canonical/pre-gate/attempt/fresh pose/dynamic unique AMCL TF/cleanup/false boundaries 的已观察结构事实。
- `runtime_clean_gate.exit`：`1`，预期且必须保留；唯一失败为 `map_to_odom_fresh`。
- `forbidden_runtime_scan.log`：PASS；runtime stdout/stderr 未出现 planner/controller/path/NavigateToPose/cmd_vel/base manual/UART/`pkill`/`killall` 命令。
- helper cleanup：identity verified，expected PID=PGID=`648519`，`residual_count=0`，`managed_runtime_cleanup_ok=true`。
- `graph_cleanup.diff`：`0` 行；运行前后 ROS graph 清单一致。
- stable process readback：既有 `lidar_driver`、`esp32_bridge` 与 `upper_robot_api` 仍在；本轮未修改其参数或清理其进程。
- Safety boundaries：`safe_to_control=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`。

## 剩余风险与下一步建议

- 本轮形成了 current live initialpose consumption、fresh `/amcl_pose` 与 AMCL dynamic `map->odom` 的新现场材料，但 TF freshness 未过 clean gate；不得提升为定位 ready、路线或履约证据。
- canonical free cell 只证明地图栅格可通行，不证明机器人真实物理位置就是该坐标；本轮没有物理位姿 ground truth。
- 下一轮不得通过另一个 wrapper 重发同一 `/initialpose`。优先新增严格 read-only 的 TF receipt-time/arrival-time 采样，把每条 `map->odom` 的接收时刻与 header stamp 同时记录，先区分 collector 判定延迟与 AMCL 静止停更；只有获得 fresh current TF 后再讨论后续路径材料。
- 仍未执行 planner/controller/path、NavigateToPose、机器人运动、真实路线、delivery、HIL 或 safe-to-control 验证。
