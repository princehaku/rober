# Tech Done - O3 Live TF Receipt Capture

## Sprint Metadata

- `sprint_type: epic`
- Sprint: `sprints/2026.07.15_08-06_o3_live_tf_receipt_capture/`
- Engineering owner: `robot-algorithm-engineer`
- Completed: `2026-07-15 08:17 Asia/Shanghai`
- Result: `blocked_with_root_cause`
- Proof boundary: `live_strict_no_motion_localization_receipt_artifact_blocked_missing_map_to_odom`

## 自主能力目标和本轮抓手

本轮把 05:55 sprint 已离线修复的 TF callback receipt-time 合同带入真实上位机的 current managed
localization-only 窗口。抓手是一次 helper-owned `strict-no-motion`、`no-base-uart` capture：只启动
map_server、AMCL、lifecycle manager 与必要 static TF，复用现有 LiDAR lifecycle，采集 `/scan`、
`/amcl_pose`、`/tf`、`/tf_static` 和 cleanup 事实；不发布 `/initialpose`，不启动 planner/controller，
不做 path、NavigateToPose、底盘控制、UART、route、delivery 或 HIL。

## 资料与远端前置

- 已完整核对 `docs/vendor/VENDOR_INDEX.md`。WAVE ROVER base 的厂商事实是 newline-delimited UART
  JSON；本轮用 `--no-base-uart` 明确禁止打开 base serial，也没有发送任何 `T=1/T=13/T=130/T=131`。
- `/dev/ttyACM0@150000` 不是 vendor 通用事实，只引用项目既有现场 lifecycle 当前 readback。本轮前置
  再次确认 holder、PID-matched status 与 diagnostics 均为 current `150000`，并使用
  `--reuse-existing-lidar-lifecycle`，helper 没有启动第二个 LiDAR driver。
- `2026-07-15T08:11:36+08:00` 只读 SSH 前置确认：ROS setup、onboard setup、`ros2`、Python、canonical
  map YAML 均可读；map SHA256 为
  `1b54312162c67b74f4c67294e287c4f1b2c2df9e12b7008d39660b26134810f4`；未发现已有 map_server、AMCL、
  planner/controller 或旧 helper runtime。既有 ESP32 bridge、Upper API 与 LiDAR 未被停止或修改。

## 实际改动

### 代码与接口

- 未修改 `onboard/scripts/o10_amcl_nav2_runtime_proof.py` 或测试。现场未暴露新的 helper bug，因此没有
  为了改变 live 结果扩展代码。
- 未修改 ROS topic/message/launch/config/hardware 接口；没有新增控制入口。

### 文档与本轮 artifacts

- `docs/navigation/field_route_evidence_preflight.md`
  - 新增 08:12 live capture、三类 age 复算、exact blocker 与 cleanup 边界。
- `sprints/2026.07.15_08-06_o3_live_tf_receipt_capture/artifacts/algorithm/runtime-proof.json`
  - 从远端拉回的原始 final runtime artifact，SHA256
    `2674af26a84a4e9ebd40327c742d1f83bc7916c83d5deaf83658a064810204c2`。
- `artifacts/algorithm/runtime.stdout`、`runtime.stderr`、`runtime.exit`
  - 保留自然退出摘要；exit=`2`，stderr 为空。
- `artifacts/algorithm/live-command.txt`
  - 保留唯一 final capture 命令；不含 initialpose/path opt-in。
- `artifacts/algorithm/capture-envelope.json`
  - 汇总前置、local/remote SHA、final run count、runtime、age、cleanup、四 delta 与 proof boundary。
- `artifacts/algorithm/structure-assertion.log`
  - 保留结构断言的关键输出。

## 唯一 Final Live Capture

- local helper SHA256：
  `78fd2e88aa6e272db52a45db8d8f5eef07108a4a010e73c50119bb23c18ca368`。
- remote `/tmp/rober_o3_live_tf_receipt_capture.py` SHA256：相同；`sha_match=true`。
- final live run count：`1`。运行窗口 `08:12:16.849-08:14:09.320 CST`，约 `112.471s`。
- 运行参数显式包含：`--strict-no-motion --no-base-uart --managed-runtime-opt-in`
  `--reuse-existing-lidar-lifecycle --managed-lidar-serial-port /dev/ttyACM0`
  `--managed-lidar-serial-baudrate 150000 --managed-map-yaml ... --managed-timeout-s 70 --timeout-s 4`。
- 命令不包含 `--initialpose-opt-in` 或 `--path-generation-opt-in`。
- 自然 exit=`2`，不是外层 `timeout`；status=`blocked_with_root_cause`。runtime 已进入后没有重跑。

## 现场结果与数据变化

### 已证明

- `managed_runtime_started=true`，boundary=`explicit_opt_in_managed_localization_runtime_no_motion`。
- helper runtime log 证明 `map_server_active=true`、`amcl_active=true`。
- `/scan` observed 且 fresh，`age_ms=21`、threshold=`3000ms`。
- `/tf` 与 `/tf_static` 可见；本次 inventory 的 `3/3` transforms 都带整数 `received_at_ms`。
- dynamic `odom->base_link` 的 receipt-time 合同可复算：
  - `1784074406732 - 1784074406726 = 6ms = header_age_at_receipt_ms`；
  - `1784074446409 - 1784074406732 = 39677ms = receipt_age_at_evaluation_ms`；
  - `1784074446409 - 1784074406726 = 39683ms = header_age_at_evaluation_ms`；
  - `6 + 39677 = 39683`，decision basis=`header_age_at_receipt_ms`，threshold=`3000ms`，status=`fresh`。
- 这证明 collector 后续约 39.7 秒的评估延迟没有被错误追加到 dynamic freshness gate。

### Exact blocker / 失败定位

- `/amcl_pose` publisher endpoint 可见，但本轮 sample 未观测，`amcl_pose_observed=false`。
- 目标 dynamic `map->odom` 未出现，`dynamic_source_observed=false`、`source_class=missing`；因此它的
  `received_at_ms` 和三类 age 均保持 `null`，没有从相邻 dynamic edge 伪造。
- exact blockers：
  - `amcl_requires_initial_pose_but_initialpose_forbidden_in_current_safety_scope`；
  - `/amcl_pose_probe_timeout`；
  - `map_to_odom_dynamic_source_missing`；
  - `map_to_base_link_blocked_by_missing_map_to_odom`。
- `ros2_node_list_timeout` 仍是 secondary graph diagnostic；helper-owned lifecycle log 已独立证明
  map_server/AMCL active，因此它没有覆盖更强的 AMCL/TF blocker。
- 这是预期的安全 fail-closed 结果，不是 helper bug；本轮禁止 `/initialpose`，所以不修复、不重跑。

## Safety 与 Cleanup 断言

- `initialpose_publish_attempts=0`、`initialpose_published=false`。
- `path_generation_requested=false`、`path_generation_attempted=false`、`path_generated=false`。
- managed process inventory 中没有 planner_server、controller_server 或 bt_navigator。
- `uses_base_uart=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、
  `robot_control_executed=false`。
- `route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`。
- helper-owned PGID=`651190`，identity verified；先 SIGINT、必要时 SIGKILL 后 residual=`0`、
  `group_present_after_cleanup=false`。
- `08:14:27 CST` post process inventory 未发现 map_server/AMCL/lifecycle/static-TF/helper 残留；既有
  LiDAR/ESP32/Upper API 保持。

## 验证结果

1. `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_nav2_runtime_proof_helper.py`
   - exit `0`。
2. `python3 -m unittest onboard/tests/test_nav2_runtime_proof_helper.py`
   - `Ran 160 tests in 2.267s`，`OK`。
3. `python3 -m json.tool .../artifacts/algorithm/runtime-proof.json >/dev/null`
   - exit `0`。
4. live structure assertions
   - `live_tf_receipt_capture_structure_assertions_ok`；覆盖 local/remote SHA、final run count=`1`、固定
     false/zero 字段、`3/3 received_at_ms`、observed dynamic age 三式、missing `map->odom` exact blocker、
     helper-owned cleanup residual=`0` 与 post inventory residual=`0`。
5. required `rg` 与 scoped `git diff --check`
   - 见最终验收；必须通过后才交给 Product closeout。

## Mission Objective 0 与 OKR 边界

- `current_run_artifact_delta=true`：本轮确有新的 true-board live sensor/localization receipt artifact。
- `external_artifact_delta=false`。
- `live_control_delta=false`。
- `user_action_delta=false`。
- Mission Objective 0 未满足，`okr_credit=false`；本文件不修改 OKR 百分比或归档 KR。
- 该 artifact 不证明 physical localization ground truth、route execution、delivery、HIL、
  safe-to-control、production cloud 或 operator acceptance。

## 完成前反思与剩余风险

- 需求满足度：完成了唯一 live receipt capture、artifact 拉回、age 复算、exact blocker 与 clean cleanup；
  没有用重跑追求 clean 结果。
- 范围自检：只新增/修改计划允许的导航文档、当前 sprint `tech-done.md` 与 algorithm artifacts；没有修改
  helper、测试、旧 sprint、launch/config、vendor/hardware、OKR、process log、side2side 或 final。
- TODO 自检：本轮范围内没有新增 TODO；代码没有改动。
- 剩余风险：未发布 `/initialpose` 时 AMCL 没有 current pose，dynamic `map->odom` 不存在，所以本轮只能
  验证其他 live transform 的 receipt-time 合同，不能直接验证目标 edge 的三类 age。
- 下一步建议：Product 应先保守接受本轮 current-run artifact 但保持主百分比 flat。若要得到目标
  `map->odom` receipt age，必须开启新的 sprint 并获得新的 explicit authorization；不能复用或重放本轮
  `/initialpose` 权限，也不能把再次启动相同无初始位姿 runtime 当成新进展。更强下一步应直接消费
  current persisted pose，或在独立授权下产生一次新的 controlled localization input，然后只读采目标
  edge；route/controller/control 仍需另行授权与 HIL gate。
