# PC 键盘 realtime hold watchdog

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 键盘连续手控请求体改为 `feedback_mode=realtime_hold`，附带 `hold_session_id`、`hold_sequence` 和 `hold_watchdog_ms`。
  - 键盘 pulse 不再占用全局 `manualCommandPending`；按住期间不会把 UI 切回“等待上一条请求/等待条件”。
  - 连续发送从固定 `setInterval` 改成回包后自调度；上一拍慢于 260ms 时下一拍立即补发，避免错过 interval 后再空等一整拍。
  - 方向组合变化时，如果当前没有 in-flight pulse，会取消待发 timeout 并立即发送新方向。
- `pc-tools/workstation/src/server/index.ts`
  - PC 固定 manual 代理保留 `realtime_hold` 和 hold 元数据，仍只转发到固定 `/api/base/manual`。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 扩展手控请求合同，加入 `realtime_hold`、`hold_session_id`、`hold_sequence`、`hold_watchdog_ms`。
- `onboard/scripts/upper_robot_api.py`
  - 新增上车 `realtime_hold` 分支：按住刷新只写低速命令并刷新 watchdog，不在每拍末尾自动 stop。
  - watchdog 到期会发送停车兜底；release stop 取消 watchdog。
  - `/api/base/stop` 扩展为覆盖 ROS `/cmd_vel` 零速和 WAVE ROVER `T=13`、`T=1`、`T=11` 三种零命令。
  - 硬件协议资料来源：`docs/vendor/VENDOR_INDEX.md` 中 WAVE ROVER UART JSON 控制事实，尤其 `T=13` ROS 控制、`T=1` speed、`T=11` PWM。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录 realtime hold/watchdog 边界，明确普通点动和键盘按住的差异。
- `pc-tools/workstation/test/App.test.ts`、`onboard/tests/test_upper_robot_api.py`
  - 覆盖慢回包不空等下一整拍、`realtime_hold` 请求体、stop 点击期间立即停车、上车 hold 不每拍 auto stop。

## 验证结果

- 通过：`python3 -m py_compile onboard/scripts/upper_robot_api.py`。
- 通过：`python3 -m unittest onboard.tests.test_upper_robot_api`，106 tests，1 skipped。
- 通过：`cd pc-tools/workstation && npm run test -- App.test.ts -t "keeps keyboard hold smooth|keeps moving and sends a curved twist|pauses heavy live refresh"`，3 tests。
- 通过：`cd pc-tools/workstation && npm run test -- catalog.test.ts -t "realtime hold metadata|base manual proxy exposes IMU motion signal"`，2 tests。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run test -- App.test.ts robotControlSummary.test.ts`，264 tests。
- 通过：`cd pc-tools/workstation && npm run test`，3 files / 461 tests。
- 通过：`HOST=0.0.0.0 PORT=7001 npm run api` 已重启 PC Node，`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `*:7001`，首页加载新 bundle `assets/index-CEkuKU6S.js`，bundle 内可检索到 `realtime_hold`、`hold_session_id`、`hold_watchdog_ms`。
- 通过：已通过 `ssh root@192.168.1.11 -p 37878` 备份并部署 `/root/rober/onboard/scripts/upper_robot_api.py`，远端 `python3 -m py_compile` 通过；上车 API 重启后 PID `336182` 监听 `*:8787`，`/health` 返回 `ready`。
- 通过：未调用真实 `/api/base/manual` 做无提示发车；远端只读 grep 确认已包含 `realtime_hold` 和 `manual_hold_stop_all_surfaces`，PC `/api/robot-control/summary` 返回 `readable` / `bounded_repeating_manual_pulse`。

## 剩余风险

- 本轮仍未在真实车上长按复验轮速和体感；软件证据证明每拍不再主动 stop，但实际顺滑度还要现场确认。
- `realtime_hold` 依赖 PC 持续刷新 watchdog；PC 断拍时上车会自动停车，但断拍前的最后运动窗口最长受 `MAX_PULSE_MS=800` 限制。
- 完整 Nav2 路线执行、delivery success 和实时 costmap 图层不在本 micro 范围内。
