# Owner A Report - Dynamic TF Source Inventory

## 自主能力目标和抓手

本 lane 只修并采集 strict no-motion dynamic `map->odom` source inventory：把 `/tf` edge、
transform timestamp/freshness、`/tf` publisher endpoint 与 `/amcl` node publisher inventory
关联起来。没有运行 planner wrapper、initialpose、managed runtime、NavigateToPose、controller/BT、
LiDAR start/stop、`/cmd_vel`、`/api/base/manual` 或底盘 UART。

最终 current-window 结论是 fail-closed：现有 ROS graph 没有 `/map_server`、`/amcl` 或 AMCL
`/tf` endpoint；`/tf` 的可见 publisher endpoint 是 `/esp32_bridge`。因此不能把当前 `/tf`
动态流归因为 AMCL `map->odom`，也不能复用上一轮 tf2 buffer/path success 洗白。

## 实际改动和接口影响

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 新增 `/amcl` node publisher 与 `/tf` endpoint 唯一交集归因；输出
    `publisher_attribution_status/reason`、`publisher_endpoint`、candidates、source topic、stamp 和
    freshness。
  - 多 `/tf` publisher 时只匹配唯一 `/amcl` endpoint；多个同名 AMCL endpoint 保守标 ambiguity。
  - source probe 等待目标 dynamic `map->odom`，不因先收到 `odom->base_link` 提前退出。
  - strict-no-motion source-only 模式跳过 package/signal/planner 扩展；rclpy graph/TF probe 改在
    sourced child Python 中执行。
  - child 输出新增 endpoint/edge/latest-stamp 压缩，避免超过 parent 的 8KB stdout 保留上限。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 覆盖 dynamic attributed、multiple-AMCL ambiguity、stale/missing timestamp、static 不冒充
    dynamic，以及 sourced child JSON 回读。
- `docs/navigation/field_route_evidence_preflight.md`
  - 同步 attribution/freshness 合同、fail-closed 状态和 no-motion 边界。
- `artifacts/algorithm/**`
  - 保存四个有界 capture 窗口、exit/SHA/log/raw JSON、最终 fail-closed 归因摘要与本报告。

没有修改 planner/route、launch/Nav2/AMCL 参数、地图、LiDAR 配置、`OKR.md` 或 `tech-done.md`。

## 本地验证

```text
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
exit=0

python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
Ran 145 tests in 2.270s
OK

required rg
match lines=578

dynamic_tf_source_inventory.raw.json json.tool
exit=0

current_window_attribution_fail_closed.json json.tool
exit=0

structural assertion
algorithm_live_fail_closed_contract_ok

scoped git diff --check
exit=0
```

结构断言确认：

- `collector_mode=read_only_existing_ros_graph_no_motion`；
- path requested/attempted 均为 `false`；
- raw、proof 与 derived summary 的八个 safety/control/delivery/HIL 字段全部为 `false`；
- derived attribution 为 `unavailable_amcl_tf_publisher_not_observed_in_node_graph`；
- candidate 仅为 `/esp32_bridge` `/tf` endpoint，不是 AMCL；
- SSH capture exit `2` 为自然 fail-closed final，SCP pull exit `0`。

## Live Capture、失败定位与复验

目标固定为 `root@192.168.1.11:37878`，remote hostname 为 `op-z3-b6.home`。

1. Attempt 1：deploy/SCP 成功，helper exit `2`。定位为 existing graph 中
   `/map_server`、`/amcl` 均 absent；同时旧 gating 在 lifecycle 不 clean 时跳过 source inventory。
2. Attempt 2：修复 gating 后 source probe 执行，但无关 `ros2 pkg list` 消耗剩余窗口，outer exit
   `124`。新增 strict source-inventory fast path。
3. Attempt 3：仍 exit `124`。定位为 SSH parent 未 source ROS Python，direct rclpy import 失败后
   串行执行多条 sourced CLI。改为单个 sourced child probe。
4. Final：`2026-07-14T16:14:28Z` 至 `16:15:41Z`，helper 在 `68562ms` 内自然写 final；
   deploy SCP `0`、install SSH `0`、capture SSH `2`、pull SCP `0`。`status=blocked_with_root_cause`，
   不再是 timeout/partial。

Final raw 的 sourced child 已观察：

```text
/tf publisher_count=1
publisher=/esp32_bridge
topic_type=tf2_msgs/msg/TFMessage
QoS=RELIABLE/VOLATILE
/tf_static publisher=/static_transform_publisher_IQ8q3xoF0rfVrijI
visible dynamic edge=odom->base_link
latest visible stamp epoch_ms=1784045738126
/amcl node info observed=false
AMCL publishers=[]
```

child JSON 包含高频重复 transform，超过 parent `run_bash` 的 8KB stdout tail，导致 final raw
将 child boundary 写成 `sourced_rclpy_child_probe_failed`，未能把 `/tf` endpoint 自动提升到顶层；
因此 `dynamic_tf_source_inventory.raw.json` 顶层的 `/tf_topic_missing` 不能作为 current graph truth。
`current_window_attribution_fail_closed.json` 只从同一 raw 内嵌 child tail 提取当前 endpoint 事实，
明确保留该解析边界，没有宣称 clean source。后续代码已经压缩 child endpoint/edge/latest stamp，
但遵照本轮停止 retry 指令未再次部署。

## SHA 与证据边界

Final capture 时双端 SHA 一致：

```text
local_capture_helper_sha256=638abe142175a0b797852421321ed48c1caa9517c8088de0236ce9b8686b8318
remote_capture_helper_sha256=638abe142175a0b797852421321ed48c1caa9517c8088de0236ce9b8686b8318
match=true
```

Final capture 后仅在本地增加 child payload 压缩修复，当前本地 SHA 为
`f4f0b668cc796b81732836147b41f60da3a826f12ab8a1fe4961f2e7dab0100e`；该版本未在本轮再次部署，
不能把本地测试结果写成 live 远端验证。

Proof boundary：
`robot_runtime_o3_strict_no_motion_dynamic_tf_source_inventory_fail_closed_only`。不证明 dynamic
`map->odom` clean、AMCL active、planner/path、route execution、delivery/operator acceptance、HIL、
safe-to-control 或 O5 production cloud。

## 剩余风险和下一步

1. Current existing graph 没有 AMCL/map_server，无法得到 AMCL `map->odom` endpoint attribution；
   需要现场 runtime owner 先让既有 localization runtime 出现在 graph，再做同一只读命令。
2. 本轮 final raw 暴露 8KB child JSON 截断；本地已压缩修复并通过 145 tests，但未做远端复验。
3. 下一轮只应部署当前 SHA 后复验 source inventory；若 `/amcl` 仍 absent，继续按同一 exact cause
   fail closed，不得重跑 planner wrapper或启动 managed runtime冒充 existing-graph evidence。
