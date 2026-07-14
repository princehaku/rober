# Tech Done - O3 Current Localization Runtime Recovery

## Sprint Metadata

- `sprint_type: epic`
- Sprint: `sprints/2026.07.15_00-53_o3_current_localization_runtime_recovery/`
- Owner: `robot-algorithm-engineer`
- Target: `root@192.168.1.11:37878`
- Technical status: `implemented_and_live_verified_fail_closed_on_missing_initial_pose_outputs`
- Product acceptance: `not_ready_for_clean_acceptance`
- Proof boundary:
  `robot_runtime_o3_strict_no_motion_localization_runtime_active_but_initial_pose_pose_sample_dynamic_map_to_odom_fail_closed_only`

本轮没有发布 `/initialpose`，没有请求 path generation，也没有调用 planner、controller、
NavigateToPose、`/cmd_vel`、`/api/base/manual` 或底盘 UART。现场结果把旧的“没有
map_server/AMCL runtime”推进为“runtime 已 active，但 safety scope 禁止 initialpose，AMCL 因缺
定位初值不能输出 `/amcl_pose` 与 dynamic `map->odom`”的同窗精确 blocker。

## 自主能力目标和本轮抓手

- 目标：在 strict no-motion 边界内恢复 localization-only runtime，并同窗读取 `/scan`、
  `/amcl_pose` 与 AMCL dynamic `map->odom`。
- 抓手：复用既有 LiDAR lifecycle，不启动第二 driver；helper 只拉起 map_server、AMCL、
  lifecycle manager 和 helper 自有 static TF process group。
- 地图：按 helper canonical 规则对 16 个 map proof candidates 计算
  `(free_cells, mtime_ms, path)` 逆序排名，唯一 top 为
  `/root/rober/onboard/runtime/maps/trashbot_map.yaml`，free cells `425`；次项 free cells `394`。
  `find` 共看到 17 个 YAML，因此这里明确是“规则唯一 top”，不是文件系统唯一 YAML。

## 实际改动

### `onboard/scripts/o10_amcl_nav2_runtime_proof.py`

- managed graph fallback 改为 `ros2 node list --no-daemon`，避免 ROS daemon discovery 把
  70 秒预算耗尽。
- 两层 graph probe blocked、但 helper 自有 lifecycle 日志已经证明 map_server/AMCL active
  与 bond clean 时，以 `managed_lifecycle_log_active_graph_probe_blocked` 有界提前收口；graph
  timeout 仍保留为 secondary diagnostic，下游继续执行 compact endpoint/TF probe。
- compact child 新增 `/amcl_pose` read-only subscription，输出 sample count、frame、接收时间、
  header stamp 与 freshness；该订阅不发布 initialpose。
- strict managed localization 即使不发布 initialpose，也必须验收 pose 与 dynamic TF 输出。
  当两者均缺失时输出
  `amcl_requires_initial_pose_but_initialpose_forbidden_in_current_safety_scope`，不再把 lifecycle
  active 或 graph wrapper 误报成 localization ready。

### `onboard/tests/test_nav2_runtime_proof_helper.py`

- 新增/更新 no-daemon fallback、lifecycle-log bounded closeout、read-only pose sample/freshness、
  strict managed output gate 与 no-initialpose root-cause 测试。
- 最终 targeted suite 从 145 tests 增至 148 tests。

### `docs/navigation/field_route_evidence_preflight.md`

- 同步 graph wait、pose read-only sample、reuse LiDAR requested/reference 语义和 static TF
  duplicate authority 风险。
- 记录本轮真实上位机窗口、SHA、cleanup、fresh `/scan` 与 AMCL initial-pose blocker。

### `artifacts/algorithm/**`

- 保存本地 validation、三次 attempt、local/remote SHA、map candidates/ranking/resolution、
  graph before/after、run timestamps、stdout/stderr/exit、pull exit、runtime raw/pretty JSON、
  acceptance summary、process-group cleanup 与 existing process readback。

## 接口与数据影响

- `amcl_pose_sample` 是 additive 字段；包含 `observed`、`sample_count`、`received_at_ms`、
  `frame_id` 与 `stamp`，不改变已有 top-level safety 字段。
- managed wait 新增 `early_closeout=managed_lifecycle_log_active_graph_probe_blocked`；它只表示
  lifecycle 日志允许继续下游 read-only probe，不等于 ROS graph clean 或 localization ready。
- `--reuse-existing-lidar-lifecycle` 下 helper 默认 `230400` 只是未使用的 requested/reference
  配置，`driver_started_by_helper=false`。现场 current holder/driver 仍是
  `/dev/ttyACM0@150000`，PID/PGID `550914/550851`；本轮未重启或重配 LiDAR。
- `/tf_static` 同窗有既有 publisher 和 `managed_static_tf_broadcaster`，同时 ESP32 动态发布
  `odom->base_link`；因此只接受 AMCL dynamic `map->odom`，不能用 static 或其他 endpoint 替代。

## 本地验证

```text
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
exit=0

python3 -m unittest onboard/tests/test_nav2_runtime_proof_helper.py
Ran 148 tests in 2.260s
OK

required helper/test/doc rg
passed

scoped git diff --check
exit=0
```

`runtime-proof.json` 与 `acceptance_summary.json` 均通过 `python3 -m json.tool`。结构断言输出：

```text
final_fail_closed_contract_ok
```

最终 live command 单独做 forbidden flag 检索，`rg` exit `1`，证明命令不含
`--path-generation-opt-in`、initialpose、NavigateToPose、`cmd_vel`、base/manual、planner_server
或 controller_server。

## 现场验证与失败修复链

### Attempt 1 - 外层 timeout 后按自有 PGID 清理

- Window: `2026-07-14T17:11:04Z` - `17:13:35Z`。
- Runtime exit `124`，pull exit `0`；partial artifact 最窄诊断为 managed wait 的
  `ros2_node_list_timeout`。
- 外层 timeout 绕过尾部 cleanup，helper 自有 PGID `637809` 残留。先验证
  `rober_nav2_localization_*` 与 `no_motion_localization_only` marker，再只调用 helper
  `cleanup_process_group(637809)`；SIGINT 后 residual `0`，未使用 `pkill`/`killall`。
- 根因：wait 反复执行 sourced child 与 daemon-backed CLI timeout，70 秒后继续下游 probe，
  超过 150 秒围栏。

### Attempt 2 - 首次自然 fail-closed

- 修复后 147 tests 通过，local/remote SHA `217b6db8...`。
- Runtime natural exit `2`、pull exit `0`、elapsed `97.619s`；PGID `641413` residual `0`。
- 已证明 map_server/AMCL active、`/scan` fresh、AMCL `/amcl_pose` 与 `/tf` endpoints 可见。
- 复核发现 read-only pose sample 只进入 source detail，未进入 freshness 汇总；同时 raw
  root cause 排序仍被 graph timeout 抢占，因此继续做一次短语义修复与 live 复验。

### Final Attempt - 现场 blocker 收紧完成

- Window: `2026-07-14T17:24:46Z` - `17:26:25Z`。
- Local/remote helper SHA 均为
  `75e5722f1a050df5174d52fffa7df40302dbbb31bb498bab1550a297d0a1e9b2`。
- Runtime natural exit `2`，pull exit `0`，elapsed `97.743s`；不是 outer timeout。
- map_server/AMCL active；managed wait 由 clean lifecycle log 有界放行下游 probe。
- `/scan`：publisher `/lidar_driver`，sample observed，stamp age `22ms`，fresh threshold `3000ms`。
- `/amcl_pose`：topic 与 AMCL publisher endpoint 可见，read-only subscriber 可见；但
  `sample_count=0`、timestamp `parsed=false`、freshness `not_observed`。
- `/tf`：AMCL 与 `/esp32_bridge` 两个 publisher endpoints 可见；当前 dynamic sample 只有
  `odom->base_link`。target `map->odom` 为 `source_class=missing`、timestamp `parsed=false`、
  `publisher_attribution_status=not_attributed_dynamic_map_to_odom_not_observed`。
- AMCL runtime log 明确输出 `Please set the initial pose`；本轮 safety scope 又明确禁止
  initialpose，因此 exact downstream blockers 为：
  - `amcl_requires_initial_pose_but_initialpose_forbidden_in_current_safety_scope`
  - `/amcl_pose_once_not_observed`
  - `map_to_odom_dynamic_source_missing`
  - `map_to_base_link_blocked_by_missing_map_to_odom`
- raw `root_causes` 仍把 `ros2_node_list_timeout` 作为 secondary diagnostic 排在前面；
  `acceptance_summary.json` 明确保留 secondary 并按 live lifecycle/endpoint/log 事实列出上述
  exact blockers，未把 graph timeout 冒充物理定位根因。
- Helper 自有 PGID `643654` cleanup 先发 SIGINT、grace 后只对该 PGID 发 SIGKILL，最终
  residual `0`；graph after 与 stable process readback 均无 `/amcl`、`/map_server`、
  `/lifecycle_manager` 或 `/managed_static_tf_broadcaster` 残留。既有 LiDAR、ESP32 bridge 与
  upper API 进程仍在。

## Safety / False Flags

最终 artifact 固定：

```text
safe_to_control=false
publishes_cmd_vel=false
calls_base_manual=false
uses_base_uart=false
robot_control_executed=false
route_execution_success=false
delivery_success=false
hil_pass=false
path_generation_requested=false
path_generation_attempted=false
path_generated=false
initialpose_publish_attempted=false
initialpose_published=false
```

本轮没有发送 motion/底盘命令；没有打开 `/dev/ttyS5`，没有调用 WAVE ROVER UART/HTTP
控制，也没有修改 launch/config 或硬件配置。硬件资料入口已核对
`docs/vendor/VENDOR_INDEX.md`；本轮只复用现有 LiDAR 并读取现场进程事实。

## Product / OKR 判断

- 技术上接受 runtime recovery、fresh `/scan`、endpoint inventory、精确 initial-pose blocker
  和 clean helper-owned cleanup 作为新的真实上位机材料。
- 不接受 clean localization：没有 `/amcl_pose` current sample，也没有 AMCL dynamic
  `map->odom` timestamp/freshness。
- Proof boundary 仅为 strict-no-motion live fail-closed；不证明 path generation、route
  execution、delivery/operator acceptance、HIL 或 safe-to-control。
- 建议 OKR 主百分比保持不变，OKR credit=false，本轮 KR `不归档`。

## 剩余风险与下一步

1. 下一步需要 Product/CEO 明确选择一个不运动的定位初始化口径：允许受控发布一次
   `/initialpose`，或配置/验证 AMCL persisted initial pose。当前 sprint 明确禁止 initialpose，
   Algorithm 不应绕过该安全边界。
2. 获准后只复用同一 localization-only collector；先要求 `/amcl_pose` fresh 与唯一 AMCL
   dynamic `map->odom` endpoint/stamp clean，仍不进入 planner/controller。
3. graph CLI/rclpy child 偶发 timeout 仍存在，但 lifecycle log、compact endpoint probe 和
   final cleanup 已能在 150 秒内自然收口；该 secondary diagnostic 不应覆盖 initial-pose
   blocker。
4. helper-managed static TF 与既有 TF authority 有重复风险。后续若要清除此风险，需要单独
   读取现有 TF source 后决定是否跳过 managed broadcaster；本轮没有修改 launch/config。
