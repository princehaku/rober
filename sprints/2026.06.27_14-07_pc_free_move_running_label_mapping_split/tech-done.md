# 2026-06-27 14:07 PC 自由移动运行态与建图验收标签拆分

## sprint_type: micro

本轮目标是修正普通 PC summary/API 的状态表达：小车已经能低速自由移动时，不再因为运动发布已解锁就直接叫“自动扫图”。只有摄像头首帧、雷达新鲜、地图记录和新地图画面都满足时，才升级为可验收自动扫图。

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 新增自由移动建图验收 gate 判定。
  - `free_roam_autonomy_label` 改为三层表达：未运行、自由移动运行中、自动扫图。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 合同类型加入 `自由移动（运行中）`。
- `pc-tools/workstation/test/catalog.test.ts`
  - 补齐“自动扫图 ready”fixture 的摄像头首帧和新地图画面 gate。
  - 新增“运动已解锁但建图材料不齐时仍标为自由移动运行中”的回归。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 API 标签边界，明确该改动不触发任何运动命令。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run catalog.test.ts -t "free-roam"`：通过，`1 passed`，`9 passed | 117 skipped`。
- `cd pc-tools/workstation && npm test`：通过，`2 passed`，`291 passed`。
- `cd pc-tools/workstation && npm run build`：通过，Vite 仅提示 chunk size warning。
- 重启本机 PC Node：`node` PID `1658` 监听 `*:7001`。
- `GET http://127.0.0.1:7001/api/robot-control/summary`：
  - camera：`source_first_frame_failed`，`source_readiness=first_frame_failed`，`source_failure_reason=capture_read_returned_false`，`shared_preview_shared_capture=true`。
  - lidar：`latest_proof_stale_while_lifecycle_running`，`latest_scan_proof_fresh=false`。
  - free-roam：`start_ready`，label `自由移动（勾确认后可启动）`，建图缺口 `camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview`。
  - Nav2：`goal_succeeded_wheel_feedback_not_proven`，下一步提示用 `ROS` 重跑图上路线并复验 wheel raw L/R。
- 上车 SSH 只读诊断：
  - `ss -ltnp` 显示 upper robot API 监听 `0.0.0.0:8787`。
  - `/dev/video1` 是 `USB Composite Device: DV20 USB` 的 UVC Video Capture；`/dev/video2` 是 metadata，`/dev/video0` 是 cedrus decoder。
  - `camera_first_frame_probe.py --include-backend-smoke` 结果：OpenCV `open_ok=true` 但 `read_ok=false`，v4l2 MJPG/YUYV 和 ffmpeg MJPG/YUYV 全部 `no_frame_timeout`、0 bytes；证明当前不是浏览器独占，而是 USB 摄像头链路无内核帧。
  - `/api/base/status`：`/dev/ttyS5`、`115200`，按 `docs/vendor/VENDOR_INDEX.md` 指向的 WAVE ROVER UART JSON 资料，`T=130` 可读到 `T=1001`，电压约 `12.39V`，wheel L/R 仍为 `0/0`。
  - Nav2 summary：上次 `base_command_mode=pwm`，非零底盘命令 `49` 条，底盘反馈样本 `239` 个，wheel 非零样本 `0`；当前配置显示 `nav2_base_command_mode=ros`，下一次不再用旧 PWM 默认。

## 剩余风险

- 本轮没有触发任何运动命令；真实自由移动、Nav2 ROS 模式复验和 delivery success 仍需要现场勾选安全确认后执行。
- 摄像头当前不是独占问题，底层 UVC 无帧；需要现场检查 DV20 USB 输入/供电/线缆，或换 known-good UVC 复测。
- 雷达 lifecycle 在跑但 latest proof stale；自由移动不被雷达阻塞，建图/自动扫图验收仍需要 fresh 雷达 proof 和新地图画面。
