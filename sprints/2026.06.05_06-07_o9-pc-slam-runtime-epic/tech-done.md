# Tech Done: O9 PC + SLAM Runtime Epic

## sprint_type

sprint_type: epic

## 实际改动

### Full-stack Software Engineer

- 扩展 PC direct-upper scan-proof refresh 契约：
  - `pc-tools/workstation/src/shared/contracts.ts`
  - `pc-tools/workstation/src/server/o7DirectUpperApi.ts`
  - `pc-tools/workstation/src/components/O7LiveOperatorPanel.vue`
  - `pc-tools/workstation/test/App.test.ts`
- PC API/UI 现在显式展示并测试：
  - `fresh_scan_proof_observed`
  - `scan_hz_average_rate_hz`
  - `tf_observed`
  - `runtime_summary_fallback_used`
  - `continuous_scan_status`
  - `continuous_blocked_reasons`
- 更新接口文档：`docs/interfaces/o7_direct_upper_pc_api.md`。
- 证据文件：`evidence/full_stack_pc_same_origin_refresh.json`。

### Robot Software Engineer

- 未改 Python/ROS2 产品代码。
- 新增远端 runtime 证据与 root cause：
  - `evidence/robot_software_radar_or_slam_lifecycle.log`
  - `evidence/robot_software_bash_ros2_map_root_cause.log`
  - `evidence/robot_software_root_cause_summary.md`
- 更新运行时边界文档：
  - `docs/interfaces/lidar_ros2_closed_loop.md`
  - `docs/navigation/nav2_map_quality_metrics.md`

## 验证结果

### PC 软件护栏

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
$ git diff --check -- pc-tools/workstation/src/server/o7DirectUpperApi.ts pc-tools/workstation/src/components/O7LiveOperatorPanel.vue pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/test/App.test.ts docs/interfaces/o7_direct_upper_pc_api.md sprints/2026.06.05_06-07_o9-pc-slam-runtime-epic/evidence
exit 0
```

### PC live smoke

```text
$ PORT=8788 ROBER_UPPER_API_BASE_URL=http://192.168.1.11:8787 npm run api
Error: listen ENOTSUP: operation not supported on socket /mnt/c/Users/haku/AppData/Local/Temp/tsx-0/227226.pipe
```

结果：blocked。`tsx` 在 WSL 下尝试监听 Windows temp pipe，导致 8788 API 未启动；随后 `curl http://127.0.0.1:8788/...` 无法连接。该 blocker 已写入 `evidence/full_stack_pc_same_origin_refresh.json`。

### Robot Software runtime

```text
POST /api/radar/scan-proof/refresh -> proof_state=scan_once_hz_raw_packet_tf_observed
GET /api/radar/status -> scan_status=fresh_scan_proof_observed
GET /api/radar/status -> continuous_scan_status=not_proven
GET /api/radar/status -> continuous_blocked_reasons=["scan_continuity_not_observed"]
```

`bash -lc` 复核后：

```text
ros2 topic list
/parameter_events
/rosout
```

`GET /api/map/proof/latest` 返回结构化 HTTP 404：`runtime/map_lifecycle_latest.json` missing。`/root/rober/onboard/runtime` 和 `/root/rober/onboard/runtime/maps` 不存在。

## 失败定位

- Full-stack 两个 agent 均 timeout；协调节点验收了其留下的 PC 改动。软件护栏通过，但 live smoke blocked 在 `tsx_ipc_pipe_enotsup`。
- Robot Software 已把 O3/O9 root cause 收敛为：只有 API-managed 短窗口 LiDAR proof，没有 continuous radar runtime，也没有 SLAM/map lifecycle runtime 或 map artifact。
- 远端 SSH 默认 shell 是 `zsh`，ROS2 验证命令必须使用 `bash -lc`；否则 `setup.bash` source 会失败并让 `ros2` 不进 PATH。

## 剩余风险

- 不证明 PC live same-origin refresh 已现场通过。
- 不证明 continuous radar ready。
- 不证明 SLAM map usable、AMCL/Nav2 ready。
- 不证明 PC WASD、WAVE ROVER ACK、HIL、`safe_to_control=true` 或 delivery success。

## 下一步

1. Full-stack：修 PC 本机 `npm run api` 的 `tsx` temp pipe 问题，优先通过设置 Linux-side `TMPDIR` 或替换 API smoke 启动方式，让 8788 live smoke 可复跑。
2. Robot Software + Algorithm：启动 no-motion LiDAR+SLAM runtime proof，采 `/map` once、map artifact、metadata，并让 `/api/map/proof/latest` 回放同一 artifact。
