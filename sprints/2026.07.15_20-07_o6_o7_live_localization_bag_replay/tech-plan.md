# Tech Plan - O6/O7 Live Localization Bag Replay

## OKR 最低优先级核对

1. `OKR.md` 4.1 当前最低 Objective 是 O5，约 `85%`；其次是并列 O6/O7，均约 `93%`。
2. 本 sprint 不针对 O5，针对 O6/O7。
3. 原因：O5 `provider_runtime_preflight` 已由 `09-04` 真实失败与 `10-00` 离线 stage contract 连续消费两轮，
   按同 blocker 红线必须暂停；O6/O7 可在当前上位机以不依赖 `/scan`/camera 的 localization bag 产生新
   current-run mission-input artifact。

## 方案与阶段 gate

### Phase A - Algorithm 单 owner live gate 与 capture

`robot-algorithm-engineer` 先实现可离线测试的 helper。唯一 live 执行分两段记账：一次 inventory invocation；
只有 inventory clean 才允许一次 capture invocation。使用 `ROS2CLI_NO_DAEMON=1` 或等效 daemon-off 同 shell，
不得调用 `ros2 daemon start/stop`。inventory 必须验证 rosbag/sqlite3、磁盘、无冲突 recorder、topic type 与 publisher。

录制 allowlist 仅 `/tf`、`/tf_static`、`/odom`、`/amcl_pose`；必需 `/tf` 加 `/odom|/amcl_pose` 至少一个。
时长 `<=8s`、`--max-bag-size 16777216`、目录 `<=16 MiB`。record 命令本身是只读订阅；禁止任何 topic pub、
service/action、launch、lifecycle、kill/restart、planner/controller、control 或 UART 命令。无论 partial、timeout、pull、
decode 或 replay 失败都不得第二次 capture。

Algorithm 输出 schema：

- `trashbot.o6_o7.live_localization_bag_manifest.v1`
- `trashbot.o6_o7.live_localization_bag_replay_event.v1`
- status 成功为 `current_live_localization_bag_replay_ready_not_route_execution_proof`；失败使用固定枚举并 fail closed。
- stable lineage：`task_id`、`source_id`、DB3 SHA-256、topic/type/message counts、first/last timestamp、replay event count。
- 固定 false：`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`、
  `robot_control_executed=false`、`live_control_delta=false`、`user_action_delta=false`。

### Phase B - Full-stack conditional consumption

只有 Algorithm frozen manifest 通过结构断言且 live DB3/replay 文件存在时，主节点才派
`full-stack-software-engineer`。Phase B 复用既有 O6 artifact-bundle/task-detail 和 O7 consumer-detail，不新增 endpoint；
增加一个 section/readback card，保留同源 lineage，unsafe/raw/path/URL/credential/dangerous true 按 section fail closed。
若 Phase A blocked，Phase B 标记 `skipped_no_live_manifest`，不得写 fixture 或消费侧产品代码。

## 文件范围

### robot-algorithm-engineer

- `onboard/scripts/o6_o7_live_localization_bag_capture.py`
- `onboard/tests/test_o6_o7_live_localization_bag_capture.py`
- `docs/navigation/o6_o7_live_localization_bag_replay.md`
- `sprints/2026.07.15_20-07_o6_o7_live_localization_bag_replay/artifacts/algorithm/**`
- 本 sprint `tech-done.md` 的 Phase A、实际命令、失败定位、风险段；不得修改 Full-stack 文件。

### full-stack-software-engineer（仅 Phase A clean 后）

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `docs/interfaces/o6_cloud_archive_api.md`
- `docs/interfaces/o7_cloud_archive_task_api.md`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.07.15_20-07_o6_o7_live_localization_bag_replay/artifacts/full-stack/**`
- 本 sprint `tech-done.md` 的 Phase B 与集成验证段；开始前必须重读 Phase A，追加时不得覆盖 Algorithm 记录。

范围外文件禁止修改。所有新增技术注释使用中文且注释比例严格 `>20%`。

## 验收命令

### Algorithm 离线与 live

```bash
python3 -m py_compile onboard/scripts/o6_o7_live_localization_bag_capture.py onboard/tests/test_o6_o7_live_localization_bag_capture.py
python3 onboard/tests/test_o6_o7_live_localization_bag_capture.py
python3 onboard/scripts/o6_o7_live_localization_bag_capture.py --help
# helper 自己执行唯一 SSH inventory，并仅在 gate clean 时执行唯一 capture；不得手工补跑 SSH/rosbag。
python3 -m json.tool sprints/2026.07.15_20-07_o6_o7_live_localization_bag_replay/artifacts/algorithm/live_localization_bag_manifest.json >/dev/null
python3 -m json.tool sprints/2026.07.15_20-07_o6_o7_live_localization_bag_replay/artifacts/algorithm/live_localization_bag_inventory.json >/dev/null
git diff --check -- onboard/scripts/o6_o7_live_localization_bag_capture.py onboard/tests/test_o6_o7_live_localization_bag_capture.py docs/navigation/o6_o7_live_localization_bag_replay.md sprints/2026.07.15_20-07_o6_o7_live_localization_bag_replay
```

Algorithm 还必须运行结构断言：inventory invocation `=1`；capture invocation `<=1`；成功时 DB3/metadata/replay
存在且非空、目录 `<=16 MiB`、TF 与动态定位 message count 均 `>0`、hash/count/timestamp/task lineage 一致；
blocked 时 capture 按 gate 保持 `0` 或唯一 attempt，且不得生成伪 live ready。

### Full-stack（仅 Phase A clean）

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
cd pc-tools/workstation && npm run test && npm run build && npm run lint
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/App.test.ts pc-tools/workstation/test/catalog.test.ts docs/interfaces/o6_cloud_archive_api.md docs/interfaces/o7_cloud_archive_task_api.md docs/product/pc_tools_workstation.md sprints/2026.07.15_20-07_o6_o7_live_localization_bag_replay
```

Full-stack 还必须对真实 frozen manifest 做 O6 write/readback 与 O7 consumer 结构断言，证明同一 `task_id`、hash prefix、
topic/message/timestamp/replay counts；hostile fixture 只用于 fail-closed tests，不得标记 live。

## 风险与 proof boundary

- Publisher 可能因 runtime 窗口不可见而 fail closed；这不会授权重跑或启停 runtime。
- rosbag metadata/storage 版本可能与开发机解码工具不兼容；可修离线 parser/test，但不得第二次 live capture。
- 成功 proof boundary 为 `current_live_robot_localization_bag_consumed_not_route_execution_proof`；blocked 使用更保守边界。
- 即使成功，`external_artifact_delta=false`、`live_control_delta=false`、`user_action_delta=false`；最多形成
  `current_run_artifact_delta=true` / `credit_tier=mission_input`，不证明 route execution、delivery、HIL、
  safe-to-control、production cloud 或 Mission Objective 0 完成。
