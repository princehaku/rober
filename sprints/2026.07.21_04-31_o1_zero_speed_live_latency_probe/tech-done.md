# O1 Zero-Speed Live Latency Probe - Tech Done

## Sprint metadata

- `sprint_type: micro`
- Owner：`full-stack-software-engineer`
- 状态：`blocked_before_deployment_version_gate`
- 证据边界：`read_only_live_preflight_only_not_zero_speed_sample_not_physical_latency`
- `deployment_attempted=false`
- `service_restart_attempted=false`
- `zero_speed_sample_attempted=false`
- `zero_speed_request_count=0`
- `live_nonzero_request_count=0`
- `physical_latency_not_measured=true`

## 实际改动

本轮没有修改或部署产品代码。只新增本 micro sprint 留档与两个只读证据 artifact：

- `artifacts/preflight_summary.json`
- `artifacts/hash_manifest.json`

没有修改 `OKR.md`、进度日志、vendor 文档、其他 sprint、测试或产品文件；没有 commit、push、reset 或 stash。

## 验证结果

### 本地静态与软件验证

- `npm test -- robotControlLatency.test.ts`：`3 passed`。
- `npm run build`：通过，仅保留既有 Vite `>500kB` chunk warning。
- `python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge_node.py`：通过。

### 上车只读 preflight

- SSH `root@192.168.1.11:37878` 可达；Upper `/health` HTTP 200 且 `status=ready`。
- `/api/nav2/status` 为 `running=false/state=stopped`，未调用 Nav2 start/goal/stop。
- 最新 `T=1001` 为 `L=0/R=0`；最新 bridge command 为 `T=11,L=0,R=0` 且 `sends_motion=false`。
- `/cmd_vel` ROS 图只有 1 个 publisher 与 1 个 subscriber。
- PID `1218` 是 `trashbot-esp32-bridge.service` 的 `ros2 run` wrapper，PID `3765` 是其唯一 node child；仅 PID `3765`
  占用 `/dev/ttyS5`。remote source 与 build 中 bridge 文件 inode 相同，证明当前运行模块映射明确。
- systemd bridge unit 为 `KillMode=control-group`，wrapper/child 精确重启边界可识别；本轮没有执行重启。

### 三方版本核对与硬停止

- Remote Upper SHA `8c0f...` 精确匹配历史 commit `85ba730...`，并与既有 Phase 0 deployment artifact 一致，属于已知
  7 月 20 日部署基线。
- Remote bridge SHA `6e82...` 与本地 HEAD bridge 完全相同；本地 latency bridge 为 `ff787...`，其工作树 diff 是
  keep-alive/no-replay 和 bridge local timing spans。
- 本地已验证 Upper SHA `417c...` 同时包含 latency 实现与 commit `c8f93486...` 的 sensor-owned Nav2、canonical
  initialpose、lifecycle ownership 等跨文件合同。c8 对应 Phase 0 artifact 明确记录 Upper、O10、O11、Nav2 params
  `deployed=false`。
- 因此 Remote Upper→本地已验证 Upper 的差异并非 latency-only。若整文件替换，会只部署 c8 Upper 而遗漏其配套
  O10/O11/Nav2 params；若现场手工拆出 latency-only patch，则没有与该组合精确匹配的已验证 artifact。两者都不满足
  本轮“已知基线 + 仅 latency hunks”的部署硬门。

硬停止后未 scp、未写远端临时文件、未备份、未 py_compile 远端候选、未重启 PC/Upper/bridge，也没有发出候选的
一次零速同路径请求。控制调用计数保持：manual/stop/direct `/cmd_vel`/UART/Nav2 全部 `0`。

## 失败定位

唯一 blocker：`local_verified_upper_combines_latency_with_undeployed_c8_cross_file_nav2_contract`。

这不是网络、服务 ownership 或静止状态失败；这些门均已通过。失败发生在部署版本完整性门：无法证明本 micro 的远端
Upper 候选只包含已经软件验收过的 latency 差异，同时又不引入尚未整套部署的 c8 跨文件合同。

## 剩余风险

- PC `*:7001` 当前进程从 7 月 9 日持续运行，不能证明已加载最新 latency 代码；本轮没有重启。
- Upper 与 bridge 未部署 latency 版本，因此没有可关联的 PC receive、Upper receive/publish、bridge callback/write 现场 spans。
- 零速请求没有发送，所以本轮没有 same-path live trace；更没有 wheel onset、物理 keydown-to-wheel latency 或 HIL 证据。
- `safe_to_control=false`、`hil_pass=false`、`delivery_success=false`、`robot_control_executed=false` 保持不变。

安全下一步是先产出一个可复现、可测试的 latency-only Upper deployment candidate（以 remote `85ba730` 为基线），或先由
c8 owner 在独立维护窗口完整部署并验证其四文件合同，再重新从 hash、静止、唯一 owner preflight 开始。届时仍只能发送一次
显式零速同路径样本；任何失败不得自动重试。
