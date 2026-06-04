# Tech Done: O9 Radar Status Fresh Proof PC Readback

## sprint_type

sprint_type: micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - `/api/radar/status` 现在会读取 `lidar_scan_proof_latest.json` 的 latest scan proof summary。
  - 新增顶层字段：`fresh_scan_proof_observed`、`latest_scan_proof_state`、`latest_scan_hz_average_rate_hz`、`runtime_summary_fallback_used`、`latest_scan_proof`、`latest_scan_proof_blocked_reasons`、`continuous_scan_status`、`continuous_blocked_reasons`。
  - 设计边界：fresh proof 成立只表示 latest artifact 证明 `/scan` once/hz、`/lidar/raw_packet`、TF；`continuous_scan_status` 仍为 `not_proven`，不会把单次材料外推为 continuous radar ready。
  - 安全字段继续 fail-closed：`safe_to_control=false`、`sends_base_motion_commands=false`、`calls_base_manual=false`、`publishes_cmd_vel=false`、`robot_control_executed=false`、`hil_pass=false`。
- `onboard/scripts/test_upper_robot_api.py`
  - 增加 missing latest、bad JSON、full fresh proof、runtime summary fallback 后 radar status 字段的回归覆盖。
- `docs/interfaces/lidar_ros2_closed_loop.md`
  - 同步说明 `/api/radar/status` 会消费 latest fresh proof，但 continuous radar/SLAM/Nav2/HIL 仍需单独验收。
- `docs/interfaces/o7_upper_robot_api.md`
  - 同步 8787 radar status / latest proof 的 PC 判读边界，要求 PC 不把 fresh proof 误读成控车、地图、导航或 HIL 成功。

## Full-stack 尝试与收口

- Full-stack Engineer 尝试补 PC 侧 App/contract 测试来消费 fresh proof 字段，但 `npm test -- --run test/App.test.ts` 失败：`30 tests | 3 failed | 27 passed`。
- 失败定位：
  - PC UI 尚未展示 `fresh=full`、`continuous=not_proven`、hz、TF、fallback。
  - `buildO7LiveOperatorPanel()` 尚未完整透出 latest fresh proof 字段。
  - `upperResultSummary()` 尚未解析 refresh 回包中的 `proof_summary`。
- 未完成的 `pc-tools/workstation` 半成品 diff 已清理；本 sprint 不声明 O7 PC 侧消费完成，也不基于 PC 侧上调 OKR。

## 验证结果

Robot Software 已运行：

```bash
python3 -m unittest onboard.scripts.test_upper_robot_api onboard.scripts.test_o1_lidar_scan_proof_collector
```

结果：

```text
Ran 40 tests in 2.682s
OK (skipped=2)
```

Robot Software 已运行：

```bash
python3 -m compileall -q onboard/scripts onboard/src
```

结果：退出码 0。

Robot Software 已运行：

```bash
git diff --check -- onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py docs/interfaces/lidar_ros2_closed_loop.md docs/interfaces/o7_upper_robot_api.md sprints/2026.06.05_02-03_o9_radar_status_fresh_proof/tech-done.md
```

结果：退出码 0。

本地最终协调验证还需在提交前重跑，确认代码、文档和 sprint 留档合并后仍通过。

## 远端状态

- 已执行：`scp -P 37878 onboard/scripts/upper_robot_api.py root@192.168.1.11:/root/rober/onboard/scripts/`，退出码 0。
- 未执行：远端 `systemctl restart trashbot-upper-robot-api.service`。
- 未执行：远端 `curl http://127.0.0.1:8787/api/radar/status` 和 `curl http://127.0.0.1:8787/api/radar/scan-proof/latest`。
- 证据边界：远端文件已同步，但 8787 服务是否已加载新版 `radar/status` 字段尚未验证。

## OKR 判断

- O9：本轮是 01-02 fresh scan proof 的 API/status 消费改进，不新增 fresh runtime material；不建议在 01-02 已有涨分基础上继续叠加。
- O3：本轮让 radar status 能表达 latest fresh proof 与 continuous not_proven 的差异，属于 readback/status contract 进展；不证明 SLAM `/map`、AMCL、Nav2 或 continuous radar ready。
- O7：PC 侧消费尝试失败且半成品已清理；不建议基于 O7 上调。
- O1/O2/O5/O6/O8：本轮不触达可涨分材料。

## 剩余风险

- 远端 8787 尚未重启/curl 验证新版 status 字段。
- PC 侧 parser/UI 仍未完成 fresh proof 消费，后续需要单独重开 O7 micro 或纳入下一轮 Epic。
- 不证明 continuous radar ready、SLAM `/map`、AMCL、Nav2 lifecycle、固定路线、PC WASD、WAVE ROVER ACK、HIL、`safe_to_control=true` 或真实送达。
- 下一步应优先做 PC 同源复验、continuous radar/SLAM map lifecycle、真实/受控电梯图片 manifest 或 stop-first HIL，而不是重复写 refresh/latest 接口。
