# 相机低带宽首帧兜底

sprint_type: micro

## 实际改动

- 在上车 `POST /api/robot-control/camera/first-frame/probe` 自动格式 fallback 中新增 `160x120` 低带宽候选：
  - `MJPG@160x120@30`
  - `YUYV@160x120@15`
  - `YUYV@160x120@10`
- 在首帧 probe 回包新增 `low_bandwidth_fallback_attempted` 和 `low_bandwidth_fallback_min_size`，便于现场确认 full-speed USB 场景是否真的跑到低带宽兜底。
- 更新上车单元测试和 PC 产品文档。硬件事实入口采用 `docs/vendor/VENDOR_INDEX.md`；本轮只读摄像头，不触碰 WAVE ROVER 底盘、UART 或运动控制。

## 验证结果

- 通过：`python3 -m unittest onboard.tests.test_upper_robot_api -k camera_probe`，5 tests OK。
- 通过：`python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/camera_first_frame_probe.py`。
- 通过：`npm test -- test/catalog.test.ts -t "workstation camera first-frame probe uses quick source check without backend smoke"`，1 passed / 182 skipped。
- 通过：`npm test -- test/catalog.test.ts`，183 passed。
- 通过：`npm run build`。Vite 仍提示已有 bundle size warning，但 TypeScript 和构建均通过。
- 通过：SSH 上车确认 8787 服务为 `python3 /root/rober/onboard/scripts/upper_robot_api.py --host 0.0.0.0 --port 8787 ...`。
- 通过：备份远端 `/root/rober/onboard/scripts/upper_robot_api.py` 到 `upper_robot_api.py.bak_20260702_1705`，同步新脚本，远端 `python3 -m py_compile` 通过，并重启 8787 到 PID `1360067`。
- 通过：直接调用上车 `POST http://192.168.1.11:8787/api/camera/first-frame/probe`，回包显示 `auto_format_fallback=true`、`low_bandwidth_fallback_attempted=true`、`low_bandwidth_fallback_min_size=160x120`、`fallback_attempts=11`，包含 `MJPG@160x120@30`、`YUYV@160x120@15`、`YUYV@160x120@10`，同时 `safe_to_control=false`、`robot_control_executed=false`、`sends_motion_commands=false`、`opens_serial=false`。
- 通过：重启 PC workstation 到 `0.0.0.0:7001`，PID `84391` 监听 `*:7001`。
- 通过：PC 代理 `POST http://127.0.0.1:7001/api/robot-control/camera/first-frame/probe` 透传 `probe_key_values.low_bandwidth_fallback_attempted=true`、`low_bandwidth_fallback_min_size=160x120`、`fallback_attempt_count=11`，摘要包含 `MJPG@160x120` 和 `YUYV@160x120`；边界保持 `safe_to_control=false`、`robot_control_executed=false`、`sends_motion_when_clicked=false`、`starts_nav2/manual/keyboard/free_roam/map_runtime=false`。
- 通过：`git diff --check`。

## 剩余风险

- `160x120` 低带宽兜底已经在线跑到，但现场仍是 `first_frame_timeout/deadline_expired`；当前证据继续指向 USB `12M` full-speed/线材/供电问题，需要换高速 USB 口/线或带供电 USB Hub 后复测。
- 本轮不执行 Nav2、manual、keyboard、free-roam、建图 runtime、delivery、stop 或 `/cmd_vel`；真实运动三项仍需要现场安全确认后 HIL 验收。
