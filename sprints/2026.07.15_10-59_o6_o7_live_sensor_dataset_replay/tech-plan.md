# O6/O7 真实传感器数据集回放 Epic - Tech Plan

## 状态与执行规则

- 阶段：`tech_plan_complete_waiting_engineer_dispatch`
- Sprint：`2026.07.15_10-59_o6_o7_live_sensor_dataset_replay`
- 本文件完成后，主节点应按 owner 顺序派单；Product 主节点不得自行实现、测试或 SSH。
- 本规划阶段禁止执行 live inventory/capture。本文件中的 SSH 和 rosbag 命令只供后续 `robot-algorithm-engineer` 派单使用。

## OKR 最低优先级核对

1. `OKR.md` 当前最低 Objective 是 O5，约 `85%`；并列次低是 O6/O7，各约 `93%`；O1 约 `94%`。
2. 本 sprint **不针对数字最低 O5**，而针对 O6/O7。
3. 具体理由：最近两轮 `sprints/2026.07.15_09-04_o5_public_health_tunnel_external_evidence/` 与 `sprints/2026.07.15_10-00_o5_provider_runtime_preflight_stage_diagnostics/` 已连续消费同一 `provider_runtime_preflight` blocker。第一轮是一次真实 provider staging/preflight 失败，第二轮是离线 stage diagnostics 合同；这是允许的第二轮和最后一轮。第三轮 O5 wrapper、diagnostic、readback 或 live rerun 被红线禁止。CEO 已提供真实上位机 SSH，O6/O7 又明确缺真实机器人数据与真实回放数据流，因此转向无需新增控制授权的 current-run 数据集是最低可行动 lane。
4. `final.md` 收口时必须复核上述切换理由是否仍成立；若 O5 出现全新的已配置 provider/runtime/credential 事实，也不得在本 sprint 内扩 scope。

## 最近两轮 blocker 去重理由

- 不复用 `provider_runtime_preflight`：本 sprint 不读取、修改或执行上一轮 O5 helper，不产生 tunnel/provider wrapper。
- 不重复 O3 live TF receipt：`2026.07.15_08-06` 已完成 receipt-time gate 和一次 strict-no-motion localization capture；本轮不启动 localization runtime、不请求 `/initialpose`、不追 `map->odom`，也不把旧 TF artifact 当新数据。
- 不新增 another manifest/readback 作为主结果：manifest 与 O6/O7 readback 只验证 rosbag 消费；若没有本轮新 DB3 或等价 current-run 数据，sprint 必须 blocked，不得用消费合同收口。

## 方案概览

```text
离线 fixture 测试
  -> 一次 read-only SSH inventory
    -> gate fail: blocked，capture count=0
    -> gate pass: 唯一一次 8s / 16MiB allowlist rosbag record
      -> 拉回并冻结 DB3/metadata/hash
        -> 只读 SQLite/CDR semantic replay
          -> independent ready sections -> existing O6 artifact bundle
            -> POST /api/o6/archive/artifact-bundle + readback
            -> O7 selected-task consumer lineage check
              -> Algorithm tech-done + Product acceptance
```

关键设计：remote 阶段只订阅已有 publisher 并写 helper-owned 临时 bag；offline 阶段不执行 `ros2 bag play`，避免将 bag 中 topic 重新发布到任何 ROS graph。

## Owner 主责与并行咨询安排

### 主责：Robot Algorithm Engineer

职责：

1. 实现 fail-closed capture helper 和 fixture tests。
2. 执行一次 read-only inventory。
3. gate 通过时执行最多一次短时 rosbag capture。
4. 拉回、冻结并离线消费 DB3，生成 independent semantic ready sections、artifact-bundle input 和 cleanup 证据。
5. 收齐 Full-stack 证据后更新 `tech-done.md`。

### 下游：User Touchpoint Full-Stack Engineer

职责：

1. Algorithm 实现期间可并行进行**只读咨询**：确认 O6 `/api/o6/archive/artifact-bundle` 与 O7 selected-task consumer 的最小安全 payload 和验证入口。
2. 实际写入和消费必须等待 Algorithm 冻结 independent ready sections、DB3 SHA-256 与 topic/message/timestamp counts。
3. 优先零代码复用既有 O6/O7 能力；只有既有合同错误拒绝安全 current-live 数据，才做最小分类/适配修复。
4. 不得读取 remote SSH、不得执行 capture、不得改 Algorithm artifact。

### 为什么不并行实现

Full-stack 的输入 identity/hash/count 来自唯一 live bag，存在明确数据依赖。并行启动两个写入 owner 会迫使 Full-stack 使用 fixture，形成假并行和 wrapper-first。正确节奏是 Algorithm 主线先冻结真实数据；Full-stack 只读咨询可以并行，实际消费随后进行。

### 已吸收的只读咨询事实

1. bag-only field manifest 缺 map/route/keyframes 时总 gate 必然 fail closed；Phase C 不得 POST `/api/o6/archive/field-evidence`。可用路径是抽取五类 independent ready sections，组装既有 `trashbot.o6.artifact_bundle.v1` 后 POST `/api/o6/archive/artifact-bundle`。
2. O6/O7 不需要新的 dataset wrapper；稳定 lineage 为 `task_id + DB3 SHA-256 + topic/message/timestamp counts`。

## 文件范围

以下为实现阶段允许范围，owner 之间互不重叠。

### Algorithm 允许改动

- `onboard/scripts/o6_o7_live_sensor_dataset_capture.py`（新增）
- `onboard/tests/test_o6_o7_live_sensor_dataset_capture.py`（新增）
- `onboard/scripts/field_route_evidence_manifest.py`（仅当现有安全 decoder 无法表达 current-live dataset source 时做最小修复）
- `onboard/tests/test_field_route_evidence_manifest.py`（与上一项配套）
- `docs/navigation/o6_o7_live_sensor_dataset_replay.md`（新增）
- `docs/navigation/field_route_evidence_manifest.md`（仅当 manifest 合同有实际变化）
- `sprints/2026.07.15_10-59_o6_o7_live_sensor_dataset_replay/artifacts/algorithm/**`
- `sprints/2026.07.15_10-59_o6_o7_live_sensor_dataset_replay/tech-done.md`

Algorithm 不得修改 Full-stack 文件或 Product closeout 文件。

### Full-stack 允许改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`（仅在 O6 existing archive 分类确有合同缺口时）
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`（仅在 O7 existing consumer 分类确有合同缺口时）
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `docs/interfaces/o6_cloud_archive_api.md`（仅随 O6 实改）
- `docs/interfaces/o7_cloud_archive_task_api.md`（仅随 O7 实改）
- `sprints/2026.07.15_10-59_o6_o7_live_sensor_dataset_replay/artifacts/full-stack/**`

Full-stack 不得修改 rosbag、Algorithm helper/tests/docs 或 `tech-done.md`；它以 agent 返回结果和 artifacts 交给 Algorithm 集成。

### Product 后续允许改动

- `sprints/2026.07.15_10-59_o6_o7_live_sensor_dataset_replay/side2side_check.md`
- `sprints/2026.07.15_10-59_o6_o7_live_sensor_dataset_replay/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Product 只在 Engineer 证据齐备后更新；规划阶段不创建后三份完成文档。

## 接口合同

### Capture envelope

建议 schema：`trashbot.o6_o7.live_sensor_dataset_capture.v1`。必需字段：

- `task_id`、`run_id`；禁止新增 `dataset_id` wrapper
- `source_mode=current_live_upper_computer_existing_publishers`
- `target_host`（sprint 原始证据可记录；进入 O6/O7 安全摘要时只保留 host label/hash）
- `inventory_invocation_count`
- `live_capture_invocation_count`
- `capture_duration_requested_s`、`capture_duration_observed_s`
- `topics[]`: `name`、`type`、`publisher_count`、`message_count`、`first_timestamp_ns`、`last_timestamp_ns`
- `rosbag_storage_id=sqlite3`
- `bag_basename`、`bag_size_bytes`、`bag_sha256`
- `metadata_basename`、`metadata_sha256`
- `capture_status`
- `cleanup.helper_owned_recorder_residual_count`
- `runtime_mutation_attempted=false`
- `topic_write_attempted=false`
- `rosbag_play_attempted=false`
- 固定 false：`safe_to_control`、`robot_control_executed`、`route_execution_success`、`delivery_success`、`hil_pass`

### Semantic replay / artifact bundle

bag-only `trashbot.field_evidence_manifest.v1` 的总 gate 会因缺 map/route/keyframes fail closed，因此它只能作为离线 decoder 的中间结果，不能 POST `/api/o6/archive/field-evidence`。Phase C 只抽取并复用以下独立 ready sections：

- `trashbot.route_bag_evidence.v1`
- `trashbot.route_bag_payload_replay.v1`
- `trashbot.route_bag_semantic_replay.v1`
- `trashbot.route_bag_full_semantic_decode_matrix.v1`
- `trashbot.route_bag_pose_progress_replay.v1`（仅在 `/odom` 或 TF 可安全解码时）

Full-stack 必须把这些 sections 组装进既有 `trashbot.o6.artifact_bundle.v1`，使用同一 `task_id` POST `/api/o6/archive/artifact-bundle`，再通过 O6/O7 既有 selected-task readback 验证 lineage。禁止新增 dataset endpoint、dataset wrapper 或 `dataset_id`。

必须新增或明确保留的 classification：

- `source_mode=current_live_upper_computer_existing_publishers`
- `current_run_artifact_delta=true` 仅在 bag 本轮生成、DB3 可读且 `/scan` count/decode 非零时成立；否则 false。
- `proof_boundary=current_live_robot_sensor_dataset_consumed_not_route_execution_proof` 仅在 O6/O7 消费一致性通过时成立；否则使用具体 `blocked_*`。

O6/O7 JSON 不内联 DB3 payload，不回显 raw/base64、完整绝对路径、token、credential、response body 或 traceback。

### Identity 规则

- Algorithm 在 capture 前生成唯一 `task_id`，之后不可重写。
- 稳定身份只由 `task_id + DB3 SHA-256 + topic/message/timestamp counts` 组成；不得新增 `dataset_id` wrapper。
- O6 artifact-bundle write receipt、O6 readback、O7 readback 的上述 identity/lineage 必须完全相同。
- O6/O7 只接收 bag hash prefix/size/topic/message/timestamp summary；最终结构断言必须与 Algorithm 原始 artifact 对照。
- 不得用历史 bag、fixture replay 或旧 08-06 artifact替换本轮 bag。

## 安全边界

### 禁止命令与接口

- `/initialpose`
- `/cmd_vel`
- `/api/base/manual`
- NavigateToPose
- WAVE ROVER UART
- `ros2 bag play`
- `ros2 topic pub`
- `ros2 action send_goal`
- `ros2 lifecycle set`
- `ros2 launch`
- service/systemd runtime start/stop/restart
- route execution、delivery、HIL 或底盘运动

### Topic allowlist

- 必需：`/scan` + `sensor_msgs/msg/LaserScan`
- 可选：`/odom` + `nav_msgs/msg/Odometry`
- 可选：`/tf`、`/tf_static` + `tf2_msgs/msg/TFMessage`
- 可选：`/diagnostics` + `diagnostic_msgs/msg/DiagnosticArray`
- 条件可选：`/camera/image_raw` + `sensor_msgs/msg/Image`，默认关闭
- 禁止 `-a`、regex 全录、未知 topic、控制/goal/action topic；明确不录 `/map`、`/amcl_pose`。

### Runtime 规则

- 只复用已存在 publisher/runtime。
- inventory 未发现 topic 或 publisher 时不启动任何 node 补齐。
- pre/post process/topic publisher inventory 用于判断本轮是否意外影响 runtime。
- cleanup 只作用于 helper-owned rosbag recorder PID/PGID，禁止 broad `pkill ros2`、`killall` 或按 node 名杀既有进程。

## Read-only remote inventory gate

inventory 建议由 helper 在一个 SSH 调用内完成并 JSON 化，至少检查：

1. remote UTC/hostname；
2. ROS setup 可 source；
3. `ros2 bag record --help` 与 sqlite3 storage 可用；
4. `ros2 topic list -t`；
5. allowlist topic 的 `ros2 topic info --verbose`；
6. `/scan` type/publisher count；
7. existing `ros2 bag record` process count；
8. 临时目录可创建、remote available disk `>=64 MiB`；
9. 关键现有 runtime/process snapshot。

允许 capture 的布尔式：

```text
ssh_ok
AND ros2_ok
AND rosbag_record_ok
AND sqlite3_storage_ok
AND disk_available_bytes >= 67108864
AND /scan type == sensor_msgs/msg/LaserScan
AND /scan publisher_count >= 1
AND conflicting_recorder_count == 0
AND every_selected_topic in allowlist with publisher_count >= 1
AND runtime_start_or_stop_required == false
```

任一项 false：`capture_gate=blocked_fail_closed`，`live_capture_invocation_count=0`，停止 remote live 阶段。

## 一次 live capture 调用上限

- `max_live_capture_invocations=1`，统计口径是 `ros2 bag record` 进程启动尝试次数，不是成功次数。
- 时长上限：requested `8s`，外层 hard timeout `16s`；`ros2 bag record` 必须传 `--max-bag-size 16777216`，优先以 SIGINT 收口 metadata。
- capture 完成后整个 remote rosbag 目录必须 `<=16777216` bytes；超过即标记 `blocked_capture_directory_oversize`，保留证据并禁止重录。
- 远端输出只允许 helper-owned sprint 临时目录，命名含 `run_id`。
- 无论 exit code、timeout、partial DB3、0 messages、metadata 缺失、SCP 失败或本地 decode 失败，均不得第二次 `ros2 bag record`。
- pull/SCP 失败可以对**同一已冻结 remote bag**做 read-only retrieval retry，但不得重新采集；retrieval retry 次数和原因必须单独记录。
- 离线 decoder/consumer bug 可以修复并重跑本地测试，始终复用同一 bag。

后续 Engineer 的建议命令形态（helper 实现并通过离线测试后才允许使用）：

```bash
python3 onboard/scripts/o6_o7_live_sensor_dataset_capture.py \
  --ssh-target root@192.168.1.11 \
  --ssh-port 37878 \
  --inventory-only \
  --output sprints/2026.07.15_10-59_o6_o7_live_sensor_dataset_replay/artifacts/algorithm/read_only_inventory.json

python3 onboard/scripts/o6_o7_live_sensor_dataset_capture.py \
  --ssh-target root@192.168.1.11 \
  --ssh-port 37878 \
  --capture-from-inventory sprints/2026.07.15_10-59_o6_o7_live_sensor_dataset_replay/artifacts/algorithm/read_only_inventory.json \
  --duration-s 8 \
  --max-bag-size 16777216 \
  --max-live-capture-invocations 1 \
  --output-root sprints/2026.07.15_10-59_o6_o7_live_sensor_dataset_replay/artifacts/algorithm
```

第二条命令只能由 Algorithm agent 在 gate clean 后调用一次。主节点和 Full-stack 不得调用。

## 失败后的 fail-closed 与清理

### Inventory 失败

- 不进入 capture。
- 输出 exact blocker；所有 success/control fields false。
- 不安装 package、storage plugin，不 source 未验证的用户脚本，不启动 publisher。

### Capture 启动后失败

- 立即记录 `live_capture_invocation_count=1`，永不回退为 0。
- 向 helper-owned PGID 发送 SIGINT，短 grace 后只对同 PGID 发送终止信号。
- 检查 helper-owned recorder residual count；必须为 0 才能结束清理。
- 保留 partial/oversize DB3、metadata、log、hash，不删除失败证据，不重采；总目录超过 16 MiB 不能 clean accept。
- pre/post runtime inventory 若发现既有 publisher 消失或意外新进程，标记 `runtime_safety_readback_failed`，禁止 clean accept。

### Pull / decode / consumer 失败

- remote bag 已生成时先冻结 remote basename/size/hash；只允许 read-only retrieval 同一产物。
- decoder 或 O6/O7 bug 只在本地修复、复验同一 bag。
- 不通过重新 capture 绕开 schema、decoder 或 consumer 问题。
- 最终仍失败则以 `blocked_same_bag_offline_consumption_failed` 收口，OKR 不加分。

### 清理证据

`cleanup_readback.json` 至少包括：

- helper PID/PGID；
- signals sent；
- helper-owned residual count；
- remote temp basename 列表与保留/清理决定；
- pre/post critical runtime process/topic summary；
- `existing_runtime_kill_attempted=false`；
- `runtime_start_stop_attempted=false`；
- `topic_write_attempted=false`。

## 实现步骤

### Phase A：Algorithm 离线实现与测试

1. 新增 capture helper，命令构造使用 argv/固定模板、timeout、allowlist 和安全 JSON。
2. fixture 覆盖 gate pass、SSH fail、missing rosbag、wrong `/scan` type、0 publisher、remote disk `<64 MiB`、conflicting recorder、unknown topic、8 秒/16 MiB/invocation overflow、partial capture 和 cleanup。
3. 技术注释全部中文，新增代码中文注释比例必须 `>20%`。
4. 复用现有 field manifest SQLite/CDR decoder；只有当前 live source classification 不能保留时才最小改动。

### Phase B：Algorithm read-only inventory 与唯一 capture

1. 运行一次 inventory 命令并人工核对 JSON gate。
2. gate blocked 则停止 live 阶段。
3. gate clean 才运行唯一 capture；选题由 inventory 决定，但 `/scan` 必需，其余只从 allowlist 添加；绝不录 `/map`、`/amcl_pose`。
4. 拉回同一 bag，验证总目录 `<=16 MiB`，生成 envelope、DB3 SHA-256、topic/message/timestamp counts、independent ready sections、artifact-bundle input 和 cleanup artifacts。

### Phase C：Full-stack O6/O7 消费

1. 对 Algorithm artifact 做 `task_id + DB3 SHA-256 + topic/message/timestamp counts` / false-field precheck。
2. 丢弃 bag-only manifest 的 blocked 总 gate，只组装五类 independent ready sections 到既有 `trashbot.o6.artifact_bundle.v1`。
3. 用本机 loopback POST `/api/o6/archive/artifact-bundle` 并回读 same task；明确禁止 POST `/api/o6/archive/field-evidence`，禁止 production cloud。
4. 用 O7 consumer 消费 O6 artifact-bundle detail，输出 selected-task readback。
5. 若 source 被误分类为 fixture，只做最小合同修复；不得新增 `dataset_id`、dataset endpoint 或另一个 handoff/review/wrapper endpoint。
6. 写入 `artifacts/full-stack/**` 并返回验证日志，不修改 Algorithm 文件。

### Phase D：集成与 Product 验收

1. Algorithm 对照 O6/O7 与原始 bag metadata，更新 `tech-done.md`。
2. Product 只在 current-run/data-consumed gate 全部通过时考虑 O6/O7 进度调整。
3. 即使 clean，固定 route/delivery/HIL/safe/control claims false，长期回灌继续列风险。

## 验收命令

### 规划阶段（本轮仅运行这些）

```bash
SPRINT=sprints/2026.07.15_10-59_o6_o7_live_sensor_dataset_replay
test -f "$SPRINT/pre_start.md" && test -f "$SPRINT/prd.md" && test -f "$SPRINT/tech-plan.md"
rg -n "sprint_type: epic|OKR 最低优先级核对|provider_runtime_preflight|一次|SSH|rosbag|/initialpose|/cmd_vel|NavigateToPose|WAVE ROVER|验收命令|文件范围" "$SPRINT"/{pre_start,prd,tech-plan}.md
git diff --check -- "$SPRINT"
```

### Algorithm 离线实现验收

```bash
python3 -m py_compile \
  onboard/scripts/o6_o7_live_sensor_dataset_capture.py \
  onboard/scripts/field_route_evidence_manifest.py
python3 -m unittest discover -s onboard/tests -p 'test_o6_o7_live_sensor_dataset_capture.py' -v
python3 -m unittest discover -s onboard/tests -p 'test_field_route_evidence_manifest.py' -v
python3 - <<'PY'
from pathlib import Path
for path in [
    Path('onboard/scripts/o6_o7_live_sensor_dataset_capture.py'),
    Path('onboard/tests/test_o6_o7_live_sensor_dataset_capture.py'),
]:
    lines = [line for line in path.read_text().splitlines() if line.strip()]
    comments = [line for line in lines if line.lstrip().startswith('#')]
    assert comments and len(comments) / len(lines) > 0.20, (path, len(comments), len(lines))
print('algorithm_chinese_comment_ratio_ok')
PY
git diff --check -- \
  onboard/scripts/o6_o7_live_sensor_dataset_capture.py \
  onboard/tests/test_o6_o7_live_sensor_dataset_capture.py \
  onboard/scripts/field_route_evidence_manifest.py \
  onboard/tests/test_field_route_evidence_manifest.py \
  docs/navigation/o6_o7_live_sensor_dataset_replay.md \
  docs/navigation/field_route_evidence_manifest.md
```

### Live artifact 结构验收

```bash
python3 -m json.tool sprints/2026.07.15_10-59_o6_o7_live_sensor_dataset_replay/artifacts/algorithm/read_only_inventory.json >/dev/null
python3 -m json.tool sprints/2026.07.15_10-59_o6_o7_live_sensor_dataset_replay/artifacts/algorithm/live_capture_envelope.json >/dev/null
python3 -m json.tool sprints/2026.07.15_10-59_o6_o7_live_sensor_dataset_replay/artifacts/algorithm/artifact_bundle_input.json >/dev/null
python3 -m json.tool sprints/2026.07.15_10-59_o6_o7_live_sensor_dataset_replay/artifacts/algorithm/semantic_replay_summary.json >/dev/null
python3 -m json.tool sprints/2026.07.15_10-59_o6_o7_live_sensor_dataset_replay/artifacts/algorithm/cleanup_readback.json >/dev/null
test -s sprints/2026.07.15_10-59_o6_o7_live_sensor_dataset_replay/artifacts/algorithm/rosbag/metadata.yaml
test "$(find sprints/2026.07.15_10-59_o6_o7_live_sensor_dataset_replay/artifacts/algorithm/rosbag -maxdepth 1 -name '*.db3' -type f -size +0c | wc -l | tr -d ' ')" -ge 1
test "$(du -sk sprints/2026.07.15_10-59_o6_o7_live_sensor_dataset_replay/artifacts/algorithm/rosbag | awk '{print $1}')" -le 16384
rg -n 'live_capture_invocation_count|current_live_upper_computer_existing_publishers|sensor_msgs/msg/LaserScan|message_count|first_timestamp_ns|last_timestamp_ns|helper_owned_recorder_residual_count|safe_to_control|route_execution_success|delivery_success|hil_pass' \
  sprints/2026.07.15_10-59_o6_o7_live_sensor_dataset_replay/artifacts/algorithm/*.json
```

Algorithm 还必须用 Python 结构断言证明：capture invocation 恰为 1、`/scan` message/decode count 均大于 0、总目录 `<=16777216` bytes、cleanup residual 为 0、所有危险字段 false、DB3 SHA-256/topic/message/timestamp counts 与 artifact-bundle input 一致。若 inventory blocked，则改为断言 invocation 为 0，并跳过 Full-stack 实际消费。

### Full-stack 验收

如未改 O6/O7 代码，至少运行针对实际 artifact 的 O6 write/readback 与 O7 consumer integration，并保存 receipt/断言日志。若有代码改动，必须补跑：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
cd pc-tools/workstation && npm run test && npm run build && npm run lint
```

回到仓库根后执行：

```bash
python3 -m json.tool sprints/2026.07.15_10-59_o6_o7_live_sensor_dataset_replay/artifacts/full-stack/o6_archive_write_receipt.json >/dev/null
python3 -m json.tool sprints/2026.07.15_10-59_o6_o7_live_sensor_dataset_replay/artifacts/full-stack/o6_archive_readback.json >/dev/null
python3 -m json.tool sprints/2026.07.15_10-59_o6_o7_live_sensor_dataset_replay/artifacts/full-stack/o7_consumer_readback.json >/dev/null
rg -n 'task_id|bag_sha256|message_count|first_timestamp_ns|last_timestamp_ns|current_live_robot_sensor_dataset_consumed_not_route_execution_proof|safe_to_control|route_execution_success|delivery_success|hil_pass' \
  sprints/2026.07.15_10-59_o6_o7_live_sensor_dataset_replay/artifacts/full-stack/*.json
! rg -n '"dataset_id"' \
  sprints/2026.07.15_10-59_o6_o7_live_sensor_dataset_replay/artifacts/{algorithm,full-stack}/*.json
git diff --check -- \
  onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py \
  onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py \
  pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts \
  pc-tools/workstation/src/shared/contracts.ts \
  pc-tools/workstation/test/catalog.test.ts \
  docs/interfaces/o6_cloud_archive_api.md \
  docs/interfaces/o7_cloud_archive_task_api.md \
  sprints/2026.07.15_10-59_o6_o7_live_sensor_dataset_replay
```

Full-stack 结构断言必须证明 O6/O7 的 `task_id + DB3 SHA-256 + topic/message/timestamp counts` 与 Algorithm artifact 一致、没有新增 `dataset_id`、真实 source 没有降级为 historical/fixture、危险字段全部 false。

## 验收决策矩阵

| 情况 | current-run artifact | O6/O7 consumed | 结果 |
| --- | --- | --- | --- |
| inventory gate fail，未 capture | false | 跳过 | blocked，OKR flat |
| 唯一 capture partial/0 scan/decode fail | false | 可做失败诊断但不计 | blocked，OKR flat |
| bag clean，consumer fail | true | false | 保留数据，离线修复；仍失败则 OKR 不加分 |
| bag clean，O6/O7 task/SHA/topic/message/timestamp lineage一致 | true | true | 接受真实无运动数据链；Product 再决定 O6/O7 小幅进度调整 |

无论哪种情况，`live_control_delta=false`、`user_action_delta=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`。

## 交付与下一步派单

1. 立即派 `robot-algorithm-engineer`，完整携带角色 System Prompt、上述 Algorithm 文件范围与验收命令；先离线实现/测试，再 inventory，再按 gate 决定唯一 capture。
2. 同时可派 `full-stack-software-engineer` 一个只读咨询任务，返回现有 O6/O7 最小 payload/endpoint/断言和是否需要代码改动，不写文件。
3. Algorithm 冻结 artifacts 后，再触发 Full-stack 实际消费派单，使用同一 bag，禁止 fixture 替代。
4. Full-stack 返回后，要求 Algorithm 集成 `tech-done.md`；Product 再做 `side2side_check.md`、`final.md`、OKR 与 progress log。

## 剩余风险

- 短时静止 rosbag 不是路线执行或长期场景数据。
- O6/O7 本机 loopback 仍不是 production DB/queue/OSS/公网链。
- 如果 camera 当前未运行，本轮不会产生 keyframe；不得启动 camera 补齐。
- 如果上位机缺 rosbag/storage 或磁盘不足，本轮可能以 inventory blocked 收口，且不得安装依赖。
- 唯一 capture 失败不允许重试，因此 helper 的离线 fixture 覆盖和 cleanup 设计是开 live gate 的硬前置。
