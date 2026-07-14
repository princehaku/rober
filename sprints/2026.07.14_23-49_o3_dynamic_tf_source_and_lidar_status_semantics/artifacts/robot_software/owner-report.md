# Robot Software Owner Report

## Owner 与范围

- Owner: `robot-software-engineer`
- Lane: Owner B / integration owner 初始 lane
- Capture window: `2026-07-14T16:09:22Z` - `2026-07-14T16:09:26Z`
- Target: `root@192.168.1.11:37878`
- Boundary: strict no-motion；仅部署 status 脚本、执行 `status`、读取
  `GET http://127.0.0.1:8787/api/radar/status`
- 未执行：LiDAR `start`/`stop`、upper API 重启、systemd/launch/baudrate 修改、
  `/cmd_vel`、`/api/base/manual`、WAVE ROVER UART、planner/route action

## 实际改动

1. `onboard/scripts/o1_lidar_lifecycle.sh`
   - bare `status` 不再把命令默认/reference `230400` 写成 current。
   - current 优先级为 running holder argv、PID-matched persisted status、running driver
     diagnostics、`start/__run` 显式 current command。
   - holder 冲突时以 holder 为 current 并返回冲突；无 holder 且可信候选冲突时 fail closed。
   - 无 current 证据返回 `baudrate=null`、`unknown_no_current_readback`。
   - 独立输出 `vendor_reference_baudrate=230400`、
     `vendor_reference_status=reference_only_not_current`，不把现场 `150000` 写成 vendor confirmed。
2. `onboard/tests/test_lidar_lifecycle_script.py`
   - 覆盖 bare status fail closed、running holder `150000`、holder 优先、PID-matched
     status、PID mismatch stale、diagnostics fallback、安全字段 false。
3. `docs/hardware/board_sensor_stack_smoke.md`
   - 记录 current/reference 优先级、冲突语义、vendor/current proof boundary 与 no-motion 边界。
4. 本目录 live artifacts
   - 双端 SHA、部署 stderr、两条只读命令 exit/stderr、lifecycle/API 原始 JSON、采集时间。

## 本地验证

### Shell 与 lifecycle targeted tests

```text
$ bash -n onboard/scripts/o1_lidar_lifecycle.sh
exit 0

$ python3 -m unittest onboard.tests.test_lidar_lifecycle_script
........
Ran 8 tests in 0.257s
OK
```

### Upper API regressions

```text
$ python3 -m unittest \
    onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_radar_status_prefers_driver_diagnostics_baudrate_over_stale_lifecycle_reference \
    onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_radar_status_does_not_promote_reference_baudrate_without_current_readback
..
Ran 2 tests in 0.002s
OK
```

`rg -n 'baudrate_readback|holder|diagnostics|current|reference|230400|150000' ...` 命中实现、
测试与文档预期字段；scoped `git diff --check` exit `0`。

## 真机部署与只读验证

- Local SHA256: `5e65abc31ebc7a08019bf4631c1fd0316956fc216f1456893e285239fbd77cb1`
- Remote SHA256: `5e65abc31ebc7a08019bf4631c1fd0316956fc216f1456893e285239fbd77cb1`
- deploy stderr bytes: `0`
- lifecycle status SSH exit: `0`; stderr bytes: `0`
- radar API SSH/curl exit: `0`; stderr bytes: `0`
- 两个 JSON 均通过 `python3 -m json.tool`。

Lifecycle current fields：

```json
{
  "running": true,
  "pid": 550851,
  "serial_port": "/dev/ttyACM0",
  "baudrate": 150000,
  "baudrate_readback_source": "running_holder.argv.--serial-baudrate",
  "baudrate_readback_status": "current_with_reference_conflict",
  "vendor_reference_baudrate": 230400,
  "vendor_reference_status": "reference_only_not_current"
}
```

holder argv 明确包含：

```text
o1_lidar_lifecycle.sh __run --serial-port /dev/ttyACM0 --serial-baudrate 150000
```

三个 current 候选一致：

```text
running_holder.argv.--serial-baudrate = 150000
persisted_status.pid_matched.baudrate = 150000
driver_diagnostics.serial.serial_baudrate = 150000
```

API current fields：

```json
{
  "lifecycle_running": true,
  "lifecycle_pid": 550851,
  "baudrate": 150000,
  "baudrate_readback_source": "lifecycle_status_readback.latest_result.baudrate",
  "baudrate_readback_status": "current",
  "vendor_reference_baudrate": 230400
}
```

结构断言通过：lifecycle current 为 `150000` 且来源属于 holder/PID-matched
status/diagnostics；API 同为 `150000`；两端 vendor reference 为 `230400`；
`safe_to_control`、`calls_base_manual`、`uses_base_uart`、`publishes_cmd_vel`、
`robot_control_executed`、`route_execution_success`、`delivery_success`、`hil_pass` 全为 false。

## 失败定位

无最终失败。首轮本地 targeted tests、部署、SSH status、curl、JSON parse、结构断言均通过，
未触发 SSH 255 重试或修复后复验分支。

## Vendor / Current Proof Boundary

- Vendor source：`docs/vendor/VENDOR_INDEX.md` 指向的
  `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py` 第 31、128 行，只证明 vendor
  Raspberry Pi reference `/dev/ttyACM* @ 230400`。
- Current source：本窗口真实 manager holder PID `550851` argv、PID-matched persisted status、
  driver diagnostics 三者共同证明 `/dev/ttyACM0 @ 150000`。
- `150000` 不是 vendor confirmed；`230400` 不是当前 holder readback。

## 剩余风险与协同

- 本 lane 只修复 LiDAR lifecycle/API current/reference 语义，不证明 LiDAR HIL、动态 TF
  publisher attribution、Nav2 route execution、delivery/operator acceptance 或 O5 production cloud。
- upper API 当前把 lifecycle `150000` 选为 current，top-level
  `baudrate_readback_status=current`；vendor reference 仍通过独立字段表达。若未来要求 API 同时
  把 reference 差异编码为 conflict，需要单独修改 `upper_robot_api.py`，不在本轮允许范围。
- 等待 Algorithm owner report；只有主节点 follow-up 后，integration owner 才创建
  `tech-done.md` 汇总两条 lane。
