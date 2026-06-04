# Tech Done: O9 Narrow Runtime Material Epic

sprint_type: epic

## Robot Software P0

### 实际改动

- 本地产品代码未改动：`onboard/scripts/upper_robot_api.py` 已具备 `/api/radar/status` latest proof readback 字段与 fail-closed 边界，测试也已有覆盖。
- 远端只同步必要上位机 API 脚本：`scp -P 37878 onboard/scripts/upper_robot_api.py root@192.168.1.11:/root/rober/onboard/scripts/upper_robot_api.py`。
- 同步后远端 hash 与本地一致：`d58a841be84e2b41064d640e32469212d48dbef4391cb12a3aeb678434bfe49c /root/rober/onboard/scripts/upper_robot_api.py`。
- 本轮未调用 `/api/base/manual`、未发布 `/cmd_vel`、未发送 WAVE ROVER 运动命令，远端验证只覆盖 8787 service restart、radar status/latest curl 和只读 map status readback。

### 验证结果

```text
$ python3 -m unittest onboard.scripts.test_upper_robot_api onboard.scripts.test_o1_lidar_scan_proof_collector
Ran 41 tests in 3.094s
OK (skipped=2)
```

```text
$ python3 -m compileall -q onboard/scripts onboard/src
passed with no output
```

```text
$ ssh root@192.168.1.11 -p 37878 'systemctl restart trashbot-upper-robot-api.service && sleep 2 && curl -fsS http://127.0.0.1:8787/api/radar/status && printf "\n---latest---\n" && curl -fsS http://127.0.0.1:8787/api/radar/scan-proof/latest'
```

关键远端 8787 status 证据：

```json
{
  "scan_status": "fresh_scan_proof_observed",
  "continuous_scan_status": "not_proven",
  "fresh_scan_proof_observed": true,
  "latest_scan_proof_state": "scan_once_hz_raw_packet_tf_observed",
  "latest_scan_hz_average_rate_hz": 257.987,
  "runtime_summary_fallback_used": true,
  "latest_scan_proof": {
    "observed": true,
    "failure_reason": null,
    "scan_once_observed": true,
    "scan_hz_observed": true,
    "raw_packet_once_observed": true,
    "tf_observed": true,
    "all_required_observations_observed": true,
    "runtime_summary_path": "/tmp/o1_lidar_ros2_scan_smoke/summary.json",
    "safe_to_control": false,
    "sends_base_motion_commands": false,
    "calls_base_manual": false,
    "publishes_cmd_vel": false,
    "robot_control_executed": false
  },
  "latest_scan_proof_blocked_reasons": [],
  "continuous_blocked_reasons": ["scan_continuity_not_observed"],
  "blocked_reasons": ["scan_continuity_not_observed"]
}
```

关键远端 latest proof readback 证据：

```json
{
  "artifact": {
    "path": "runtime/lidar_scan_proof_latest.json",
    "status": "loaded",
    "bytes_read": 21578
  },
  "latest_result": {
    "proof": {
      "status": "scan_once_hz_raw_packet_tf_observed",
      "scan_once_observed": true,
      "scan_hz_observed": true,
      "scan_hz_average_rate_hz": 257.987,
      "raw_packet_once_observed": true,
      "tf_observed": true,
      "all_required_observations_observed": true,
      "runtime_summary_fallback_used": true
    },
    "safe_to_control": false,
    "sends_motion_commands": false,
    "robot_control_executed": false,
    "hil_pass": false
  }
}
```

额外只读 `/map` lifecycle 复核：

```text
/api/map/list http 200 -> artifact_dir_exists=false, map_count=0, failure_reason=map_artifact_dir_missing
/api/map/proof/latest http 404 -> runtime/map_lifecycle_latest.json missing
/api/status http 200 -> radar.scan_status=fresh_scan_proof_observed, radar.continuous_scan_status=not_proven, map.status=not_proven
```

### 失败定位与剩余 blocker

- `/api/radar/status` 的 latest proof 字段已在远端新版 8787 加载并通过 curl 复验；02-03 的“远端未 restart/curl”缺口已关闭。
- continuous radar 仍未成立：`continuous_scan_status="not_proven"`，blocker 为 `scan_continuity_not_observed`。本轮没有证明长稳 `/scan` 或连续雷达 ready。
- SLAM `/map` lifecycle 仍未成立：`/api/map/list` 没有地图 artifact 目录，`/api/map/proof/latest` 返回 404，缺 `runtime/map_lifecycle_latest.json`。本轮没有证明 `/map` once、地图 yaml/image/pbstream、slam_toolbox lifecycle、AMCL 或 Nav2 消费。
- 安全边界保持：`safe_to_control=false`、`robot_control_executed=false`、`hil_pass=false`，不证明底盘 HIL、WAVE ROVER ACK、`/odom`、`/imu/data`、`/battery` 或 delivery success。

### 协同需求

- 需要 Full-stack Software Engineer 继续复验 PC 同源 refresh 按钮消费这些字段，尤其是 `fresh_scan_proof_observed` 与 `continuous_scan_status=not_proven` 的区分。
- 需要 Robot Algorithm Engineer/Robot Software Engineer 后续用独立 sprint 推进 SLAM `/map` lifecycle runtime material。
- 不需要 Hardware Infra Engineer 参与本轮复验；若进入 stop-first HIL 或底盘反馈闭环，必须重新读 vendor 并满足现场安全授权。

## Full-stack P0: PC same-origin fresh proof readback

### 实际改动

- `pc-tools/workstation/test/App.test.ts`
  - 在既有 PC operator workflow 测试里补充 fresh proof 最小护栏：`Refresh scan proof` 通过 same-origin `/api/o7/direct-upper/radar/scan-proof/refresh` 后，UI 必须展示 `upper_result=fresh/full/fresh_scan_proof_observed`、latest artifact path、freshness，以及 `continuous_scan_status_not_proven` / `continuous_radar_not_proven` 边界。
  - 保留 same-origin 断言：浏览器请求包含 `/api/o7/direct-upper/radar/scan-proof/refresh`，不包含直接 upper URL、`/api/radar/scan-proof/refresh` 或 `/cmd_vel`。
- `sprints/2026.06.05_05-06_o9-narrow-runtime-material-epic/tech-done.md`
  - 追加 Full-stack P0 小节，记录最小护栏、验证结果、失败定位和剩余风险。
- 本轮没有改 `pc-tools/workstation/src/App.vue`、`pc-tools/workstation/src/shared/contracts.ts` 或 `docs/interfaces/o7_direct_upper_pc_api.md`。

### 验证结果

已运行：

```bash
cd pc-tools/workstation && npm test -- --run test/App.test.ts
```

结果：

```text
Test Files  1 passed (1)
Tests  28 passed (28)
```

新增护栏覆盖关键 UI 文案：

```text
upper_result=fresh/full/fresh_scan_proof_observed
upper_blockers=continuous_scan_status_not_proven
upper_not_proven=continuous_radar_not_proven
artifact=loaded:artifacts/radar/scan-proof-latest.json
freshness=fresh/1s
```

### 失败定位

- 上一轮 PC 侧失败已先落最小护栏：同源按钮 fresh proof 结果不会被 UI 包装成 continuous ready。
- 直接根因仍未完全消除：PC parser 和 UI 还没有完整消费 upper fresh proof 的 hz、TF、runtime fallback 扩展字段。
- 完整修复点在当前允许改动范围外：
  - `pc-tools/workstation/src/server/o7DirectUpperApi.ts`：`upperResultSummary()` 目前只输出 `status/proof_status/latest_proof_status/artifact/freshness/blockers/not_proven`，没有透出 hz、TF、runtime fallback、continuous boundary。
  - `pc-tools/workstation/src/components/O7LiveOperatorPanel.vue`：`upperResultCopy()` 只显示现有 `upper_result_summary` 字段，无法展示 `fresh=full`、`continuous=not_proven`、hz、TF 和 fallback。
- same-origin 边界已由 App 测试覆盖：浏览器请求包含 `/api/o7/direct-upper/radar/scan-proof/refresh`，不包含直接 upper URL；fixture/server helper 可以 mock `http://192.168.1.11:8787/api/radar/scan-proof/refresh`。

### 剩余风险

- 需要 Product/主节点补充授权文件范围：`pc-tools/workstation/src/server/o7DirectUpperApi.ts` 与 `pc-tools/workstation/src/components/O7LiveOperatorPanel.vue`。
- 未完成 hz、TF、runtime summary fallback 的 PC UI 全字段展示。
- 本轮 Robot Software 已完成真实 upper 8787 live curl；Full-stack 只完成 PC App 最小护栏，未完成 PC 本机 API live smoke 或 hz/TF/fallback 全字段展示，不证明 continuous radar ready、SLAM/Nav2、PC WASD、WAVE ROVER ACK、`safe_to_control=true` 或 delivery success。

## Robot Algorithm P1: elevator image manifest fact check

### 实际结果

- 本地未发现真实/受控电梯图片 manifest。
- 仅发现模板 `pc-tools/evidence/templates/elevator_image_manifest_collection_template.json`、fixture `pc-tools/evidence/fixtures/elevator_opencv_baseline_offline_eval/manifest.json` 和 blocker fixture `pc-tools/evidence/fixtures/elevator_real_image_manifest_blocker/blocked_missing_manifest.json`。
- 远端 `root@192.168.1.11:37878` 未发现真实/受控电梯图片 manifest；`/root/rober/pc-tools/evidence` 不存在，图片枚举只返回 vendor/WAVE ROVER 文档图片，不是电梯采集材料。

### 验证命令

```bash
ssh root@192.168.1.11 -p 37878 'find /root/rober \( -iname "*elevator*" -o -iname "*manifest*" \) -print 2>/dev/null | head -120'
```

### blocker

- `blocked_with_root_cause=missing_real_or_controlled_elevator_images`
- checker、template、fixture eval 不能作为 O2/O9 涨分材料。
- 最小下一步：采集真实/受控电梯 JPEG/PNG/WebP，回填 `trashbot.elevator_image_manifest.v1`，覆盖 door open/closed、inside/outside、target floor、safe/unsafe exit、uncertain/bad-light，并跑 checker 和 OpenCV eval。

## Hardware Infra P1: stop-first HIL decision gate

### 已读来源

- `docs/vendor/VENDOR_INDEX.md`
- 远端只读 `/api/status`

### 实际结果

- 当前不具备 stop-first HIL 前提。
- 远端只读 `/api/status` 显示 `/dev/ttyS5 @115200` 存在且 `write_control_available=true`，但 `safe_to_control=false`、`robot_control_executed=false`、`sends_commands=false`、`feedback_ack.t1001_observed=false`。
- 历史 `T=1001` samples 已 stale，且仍明确 `hil_pass=false`。
- 本轮没有现场看护、物理净空、急停/断电路径和 CEO/现场授权材料。

### 未执行命令

- 未执行 `/api/base/manual`。
- 未执行 `/api/base/stop`。
- 未执行 `/api/base/feedback-request`。
- 未发布 `/cmd_vel`。
- 未发送 WAVE ROVER `T=1/T=13/T=130/T=131`。

### blocker

- `blocked_with_root_cause=hil_safety_preconditions_not_met`
- 禁止低速 pulse。下一步必须先补齐现场看护、净空、急停/断电、授权、同一 `evidence_ref`、stop-first 记录、post-status、`T=1001` 与 operator report，才能进入真实 HIL。

## Coordinator verification

### 本地验证

```text
$ python3 -m unittest onboard.scripts.test_upper_robot_api onboard.scripts.test_o1_lidar_scan_proof_collector
Ran 41 tests in 2.657s
OK (skipped=2)
```

```text
$ python3 -m compileall -q onboard/scripts onboard/src
passed with no output
```

```text
$ cd pc-tools/workstation && npm test -- --run test/App.test.ts
Test Files  1 passed (1)
Tests  28 passed (28)
```

```text
$ cd pc-tools/workstation && npm run build
vite build passed; tsc app/server passed
```

```text
$ cd pc-tools/workstation && npm run lint
exit 0
```

```text
$ git diff --check -- pc-tools/workstation/test/App.test.ts sprints/2026.06.05_05-06_o9-narrow-runtime-material-epic
exit 0
```

### 远端验证

```bash
ssh root@192.168.1.11 -p 37878 'systemctl restart trashbot-upper-robot-api.service && sleep 2 && curl -fsS http://127.0.0.1:8787/api/radar/status && printf "\n---latest---\n" && curl -fsS http://127.0.0.1:8787/api/radar/scan-proof/latest'
```

关键结果：

- `fresh_scan_proof_observed=true`
- `latest_scan_proof_state=scan_once_hz_raw_packet_tf_observed`
- `latest_scan_hz_average_rate_hz=257.987`
- `runtime_summary_fallback_used=true`
- `continuous_scan_status=not_proven`
- `continuous_blocked_reasons=["scan_continuity_not_observed"]`
- `safe_to_control=false`
- `robot_control_executed=false`
- `hil_pass=false`
