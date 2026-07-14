# Tech Done - O3 Dynamic TF Source and LiDAR Status Semantics

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_23-49_o3_dynamic_tf_source_and_lidar_status_semantics/`
- Integration owner: `robot-software-engineer`
- Parallel owners: `robot-algorithm-engineer`, `robot-software-engineer`
- Target: `root@192.168.1.11:37878`
- Technical status: `implemented_with_robot_software_live_clean_and_algorithm_live_fail_closed`
- Product acceptance status: `not_ready_for_clean_acceptance`
- Boundary: strict no-motion、existing ROS graph read-only、LiDAR/API status read-only

本阶段只汇总两位 owner 已完成的实现、验证和 live artifact，不重复任何 live 命令，不修改
`OKR.md` 或 progress log，也不提前创建 `side2side_check.md` / `final.md`。Robot Software lane
达到计划内 live clean；Algorithm lane 已从 timeout 收敛到自然 fail-closed，但 current graph 不满足
dynamic `map->odom` AMCL publisher attribution 的 Product Acceptance。

## 实际改动

### Owner A - Robot Algorithm Engineer

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 增加 `/amcl` node publisher 与 `/tf` endpoint 唯一交集归因。
  - 输出 publisher attribution status/reason、endpoint/candidates、source topic、transform stamp 和
    freshness；多 AMCL endpoint 或缺 target dynamic edge 时 fail closed。
  - source probe 等待目标 dynamic `map->odom`，不再因先看到 `odom->base_link` 提前成功。
  - strict-no-motion source-only 模式跳过 planner/package/signal 扩展，ROS graph/TF 探针改由
    sourced child Python 执行。
  - final live 后在本地增加 child endpoint/edge/latest-stamp compact 修复，避免 parent 8KB
    stdout tail 截断；该增量状态明确为 `local_fix_not_live_verified`。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 覆盖 dynamic attributed、multiple-AMCL ambiguity、stale/missing timestamp、static 不冒充
    dynamic、sourced child JSON 回读与 compact payload。
- `docs/navigation/field_route_evidence_preflight.md`
  - 同步 attribution/freshness 合同、fail-closed reason 和 no-motion 边界。
- `artifacts/algorithm/**`
  - 保存三次 earlier attempts、final capture、双端 SHA、exit/log、final raw、同窗口 fail-closed
    summary 与 owner report。

### Owner B - Robot Software Engineer

- `onboard/scripts/o1_lidar_lifecycle.sh`
  - bare `status` 不再把默认/vendor reference `230400` 合成 current。
  - current 顺序为 running holder argv、PID-matched persisted status、loaded driver diagnostics、
    `start/__run` 显式 current command；holder 冲突时 holder 优先并显式标 conflict。
  - 无 current evidence 时 `baudrate=null` / `unknown_no_current_readback`；vendor reference 独立为
    `vendor_reference_baudrate=230400` / `reference_only_not_current`。
- `onboard/tests/test_lidar_lifecycle_script.py`
  - 覆盖 holder `150000`、holder priority、PID matched/mismatch、diagnostics fallback、无 current
    时不提升 `230400`，以及 safety false。
- `docs/hardware/board_sensor_stack_smoke.md`
  - 同步 lifecycle current/reference 优先级、vendor/current 资料边界和 no-motion 安全边界。
- `artifacts/robot_software/**`
  - 保存 final status/API JSON、exit、stderr、双端 SHA、capture timestamps 与 owner report。

## 接口、数据与兼容性影响

### Dynamic TF source contract

- `tf_source_freshness.edges.map_to_odom` 与
  `tf_readiness_summary.map_to_odom_dynamic` 新增/完善：
  `publisher_attribution_status`、`publisher_attribution_reason`、`publisher_endpoint`、
  `publisher_endpoint_candidates`、`source_topic`、timestamp 和 freshness。
- 归因必须同时看到 target dynamic `map->odom` 和唯一 `/amcl` `/tf` endpoint；只看到其他
  `/tf` publisher 或其他 dynamic edge 不会被提升为 AMCL source。
- 新字段为 additive；既有 top-level proof/safety 字段保留。current live raw 的 parent 解析受 8KB
  child tail 截断影响，因此本轮以同一 raw 派生的 fail-closed summary 明确表达解析边界，不用
  raw 顶层 `/tf_topic_missing` 覆盖 child tail 中真实可见的 `/tf` endpoint。

### LiDAR lifecycle/API contract

- lifecycle top-level `baudrate` 现在只表达 current readback；无 current evidence 时为 `null`。
- 新增/稳定 `baudrate_readback_source`、`baudrate_readback_status`、`baudrate_candidates`、
  `baudrate_conflicts`、`holder`、`vendor_reference_baudrate` 和 `vendor_reference_status`。
- `/api/radar/status` 通过既有 lifecycle consumer 读取 corrected `150000`，无需修改或重启
  `upper_robot_api.py`；vendor `230400` 仍为独立 reference。
- Vendor source 仍是 `docs/vendor/VENDOR_INDEX.md` 指向的
  `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`：它只证明
  `/dev/ttyACM* @ 230400` reference，不证明 current board runtime。

## 验证结果

### Algorithm 本地验证

```text
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
exit=0

python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
Ran 145 tests in 2.270s
OK

required rg: 578 matches
final raw json.tool: exit=0
fail-closed summary json.tool: exit=0
structural assertion: algorithm_live_fail_closed_contract_ok
scoped git diff --check: exit=0
```

Algorithm 本地验收为 145 tests、py_compile、两 JSON、结构断言和 scoped diff 全部通过。
这只验证当前代码/数据合同；final capture 后的 compact child JSON 修复是
`local_fix_not_live_verified`，不能计为远端 live 通过。

### Robot Software 本地验证

```text
bash -n onboard/scripts/o1_lidar_lifecycle.sh
exit=0

python3 -m unittest onboard.tests.test_lidar_lifecycle_script
8/8 passed

UpperRobotApi targeted regressions
2/2 passed

required rg: passed
two JSON json.tool + structural assertions: passed
scoped git diff --check: exit=0
```

新增代码中文注释密度复核：lifecycle script `20.7%`、targeted tests `20.5%`（comment/code）。

## Live 结果

### Robot Software live clean

- Capture window: `2026-07-14T16:09:22Z` - `2026-07-14T16:09:26Z`。
- lifecycle status SSH exit `0`；radar API SSH/curl exit `0`；deploy/status/API stderr 均为空。
- Local/remote script SHA 均为
  `5e65abc31ebc7a08019bf4631c1fd0316956fc216f1456893e285239fbd77cb1`。
- lifecycle `running=true`，PID `550851`，holder argv 明确为
  `/dev/ttyACM0 --serial-baudrate 150000`。
- running holder、PID-matched persisted status、driver diagnostics 三个 current 候选均为
  `/dev/ttyACM0@150000`；lifecycle source 为
  `running_holder.argv.--serial-baudrate`。
- `/api/radar/status` 的 `lifecycle_pid=550851`、`baudrate=150000`，source 为
  `lifecycle_status_readback.latest_result.baudrate`。
- 两端 `vendor_reference_baudrate=230400`；`230400` 仅为 vendor reference，`150000` 仅为
  current live readback，不把二者互相冒充。

该 lane 的技术验收通过，但只证明 lifecycle/API status semantics，不证明 LiDAR HIL、Nav2
execution 或 delivery。

### Algorithm live fail-closed

- Final capture window: `2026-07-14T16:14:28Z` - `2026-07-14T16:15:41Z`；helper 自身
  `elapsed_ms=68562`，即 `68.562s`，自然写出 final artifact。
- deploy SCP `0`、install SSH `0`、capture SSH `2`、pull SCP `0`；capture exit `2` 是
  `blocked_with_root_cause` 的预期自然 fail-closed，不是 timeout 或 SSH transport failure。
- Capture-time local/remote helper SHA 均为
  `638abe142175a0b797852421321ed48c1caa9517c8088de0236ce9b8686b8318`。
- Final capture 后本地 compact 修复 SHA 为
  `f4f0b668cc796b81732836147b41f60da3a826f12ab8a1fe4961f2e7dab0100e`，遵照停止指令未再次
  部署，状态必须保持 `local_fix_not_live_verified`。

同一 final raw 的 sourced child tail 提供 current graph 事实：

```text
/tf publisher_count=1
/tf publisher=/esp32_bridge
topic_type=tf2_msgs/msg/TFMessage
QoS=RELIABLE/VOLATILE
visible dynamic edge=odom->base_link
latest visible stamp epoch_ms=1784045738126
/amcl node info observed=false
/amcl publishers=[]
/map_server active=false
```

因此当前 graph 的唯一 `/tf` publisher 是 `/esp32_bridge`，可见 dynamic edge 仅为
`odom->base_link`；current graph 没有 `/amcl`、没有 `/map_server`，也没有 AMCL `/tf`
endpoint。不能把 `/esp32_bridge` 或 `odom->base_link` 提升为 AMCL dynamic `map->odom` source。
派生 summary 保守输出：

```text
publisher_attribution_status=unavailable_amcl_tf_publisher_not_observed_in_node_graph
publisher_attribution_reason=current_graph_has_only_esp32_bridge_tf_endpoint_and_no_amcl_node_or_amcl_tf_endpoint
map_to_odom_dynamic_source_promoted=false
```

## Algorithm 失败定位与复验链

1. Attempt 1：deploy/pull 均成功，capture SSH exit `2`。existing graph 中 `/map_server`、
   `/amcl` 均 absent；旧 gating 在 lifecycle 不 clean 时跳过 source inventory。
2. Attempt 2：修复 gating 后探针执行，但无关 `ros2 pkg list` 消耗窗口，capture SSH exit
   `124`；随后增加 strict source-inventory fast path。
3. Attempt 3：capture SSH 仍 exit `124`。SSH parent 未 source ROS Python，direct `rclpy`
   import 失败后串行 fallback 多条 sourced CLI；随后合并为单个 sourced child probe。
4. Final：capture SSH exit `2`，`68.562s` 内自然输出 `blocked_with_root_cause`，pull SCP `0`。
   sourced child 确实看到 `/esp32_bridge` `/tf` 和 `odom->base_link`，但 child 高频 JSON 超过
   parent `run_bash` 8KB stdout tail，parent 解析报 `JSONDecodeError: Extra data`。同窗口派生 summary
   只提取可验证 child tail 并保持 fail closed；本地 compact 修复未再次 live 验证。

最终最窄 live root causes：

- `map_server_and_amcl_nodes_absent_in_current_existing_ros_graph`；
- `amcl_tf_publisher_endpoint_not_observed`；
- `sourced_rclpy_child_json_truncated_before_parent_parse`。

前两项阻止 Product Acceptance；第三项已有本地修复但仍需独立 live 部署复验。

## 安全影响与 Proof Boundary

两条 lane 均未执行 planner、initialpose、managed runtime、NavigateToPose、controller/BT、LiDAR
start/stop、upper API restart、WAVE ROVER UART、`/dev/ttyS5`、`/cmd_vel` 或
`/api/base/manual`。本轮固定：

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
```

- Robot Software proof boundary：
  `live_lidar_lifecycle_current_reference_semantics_readback_only`。
- Algorithm proof boundary：
  `robot_runtime_o3_strict_no_motion_dynamic_tf_source_inventory_fail_closed_only`。
- Sprint integration boundary：
  `software_and_live_readback_evidence_only_not_route_execution_not_delivery_not_hil_not_safe_to_control`。

本 sprint 不证明 clean dynamic `map->odom`、AMCL active、planner/path、真实路线执行、
delivery/operator acceptance、HIL、safe-to-control 或 O5 production cloud success；不得据此提升
OKR 百分比或归档 KR。

## 偏差与 Product Acceptance 判断

- Robot Software P1/P2：通过。current `150000` 与 vendor reference `230400` 已在 lifecycle/API
  分层，live SHA/exit/JSON/safety 证据完整。
- Algorithm P1：未通过 clean acceptance。collector 已产生 current-window fail-closed artifact，
  但 current graph 无 `/amcl`、`/map_server`，没有 target dynamic `map->odom`，无法唯一归因
  AMCL publisher endpoint，也无法验证 target transform freshness。
- Algorithm P2：本地验证与 live fail-closed 证据完整；但 compact child fix 为
  `local_fix_not_live_verified`。
- Epic 总体：接受两条 lane 的实现和真实失败诊断作为技术完成材料，但不接受 PRD 的“两条 lane
  同时 clean” Product Acceptance，不形成 route/HIL/delivery 或 OKR mission credit。

## 剩余风险

1. Current existing ROS graph 没有 `/amcl` 和 `/map_server`；即使 child compact 修复部署成功，
   只要 localization runtime 仍 absent，AMCL `map->odom` attribution 仍会 fail closed。
2. 当前本地 compact child JSON 修复只通过 145 tests/py_compile，状态是
   `local_fix_not_live_verified`；远端仍运行 capture-time `638abe...` 版本。
3. Final raw 顶层 `/tf_topic_missing` 受 parent child-tail 解析失败影响，不能作为 current graph
   truth；后续消费者必须使用 fail-closed summary 的明确 boundary，不能忽略 `/esp32_bridge`
   endpoint 事实。
4. Robot Software current `150000` 只证明状态 readback；未进行 LiDAR start/stop、串口重开、
   HIL 或持续稳定性验证。
5. `/api/radar/status` top-level `baudrate_readback_status=current`，vendor difference 由独立
   `vendor_reference_baudrate=230400` 表达；若未来要求 API 同时编码 reference conflict，需要
   单独接口迭代。

## 集成验收建议

建议主节点接受本 `tech-done.md` 作为实现阶段真实记录，并交 Product Owner 做保守
side-by-side 检查：

1. 接受 Robot Software lane 的 live clean current/reference 修复。
2. 接受 Algorithm lane 的自然 fail-closed artifact、三次 earlier root-cause 链和本地修复材料，
   但明确拒绝 clean dynamic `map->odom` attribution claim。
3. 下一轮只在现场 owner 确认 existing localization runtime 已出现 `/amcl`、`/map_server` 后，
   部署当前 compact fix 并复用同一 strict no-motion source-inventory 命令；不得重跑 planner
   wrapper、启动 managed runtime或把 `/esp32_bridge` 冒充 AMCL。
4. Product closeout 保持 OKR 完成度不变、不归档 KR，并把下一证据定义为同一 current window 的
   target dynamic `map->odom`、唯一 `/amcl` `/tf` endpoint、parsed timestamp 与 fresh status。
