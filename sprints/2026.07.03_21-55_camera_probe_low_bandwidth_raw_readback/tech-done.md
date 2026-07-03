# Camera probe low-bandwidth raw readback

## sprint_type

micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - 调整 `/api/camera/first-frame/probe` 的 `auto_format_fallback` 顺序：默认参数失败后优先尝试 `YUYV@320x240`、`MJPG@160x120`、`YUYV@160x120`，再回到常规 640/720p。
  - quick probe 总预算从 10s 调整为 11s，仍短于 PC 12s 代理超时，保证 PC 能拿到 fallback 摘要。
- `pc-tools/workstation/src/server/index.ts` 与 `src/shared/contracts.ts`
  - PC first-frame probe 返回体新增顶层 `probe_payload`、`fallback_attempts`、`auto_format_fallback`、`low_bandwidth_fallback_attempted`、`low_bandwidth_fallback_min_size`。
  - `probe_payload` 只保留压缩状态和后端尝试摘要，避免把完整 v4l2 dump 塞进普通 PC 响应。
- `onboard/tests/test_upper_robot_api.py` 与 `pc-tools/workstation/test/catalog.test.ts`
  - 锁定低负载 fallback 优先级、PC 顶层 fallback 字段和 no-motion/fail-closed 合同。
- `docs/vision/board_camera_publisher.md` 与 `docs/product/pc_tools_workstation.md`
  - 同步当前实板结论：DV20 位于 480M USB，高速下 320x240/480x320 仍 0 字节无帧；当前不是页面独占。

## 验证结果

- `python3 -m unittest onboard.tests.test_upper_robot_api`：102 tests passed，1 skipped。
- `npm test -- test/catalog.test.ts -t "workstation camera first-frame probe"`：3 passed。
- `npm test -- test/catalog.test.ts`：188 passed。
- `npm run build`：通过。
- 上位机部署：`/root/rober/onboard/scripts/upper_robot_api.py` hash 为 `18c2263ed76c15043e58aa48a2389b5582e4c8ebe43cc119b4d5c9c17116f5a9`，`trashbot-upper-robot-api.service` active，8787 health 返回 `ready`。
- PC Node：`0.0.0.0:7001` active，首页 `/` 与 `/map` 均 HTTP 200。
- Live first-frame probe：PC 返回 `auto_format_fallback=true`、`low_bandwidth_fallback_attempted=true`、`low_bandwidth_fallback_min_size=160x120`，`fallback_attempts` 包含 `YUYV@320x240`、`MJPG@160x120`、`YUYV@160x120`，最终仍为 `probe_total_timeout`。
- Live MJPEG status：`status=source_first_frame_failed`、`selected_device=/dev/video1`、`exclusive_camera_claim=false`、`source_usage_owner_count=0`、`camera_usb_speed=480M`、`source_diagnosis_status=uvc_no_frame_not_exclusive`。
- Live map preview：刷新 no-motion radar scan proof 后，地图 PNG 存在、路线 18 点、目标点可见、机器人位姿 `map_pose_observed`、雷达贴图 `loaded` 且当前点 43 个。

## 剩余风险

- 当前 DV20/UVC 源头仍不出真实视频帧；USB recovery 后 `YUYV@320x240@20` 与 `MJPG@480x320@30` 仍 0 字节超时。下一步需要检查摄像头输入、线缆、接口、供电，或换 known-good UVC 复测。
- 相机无首帧继续阻塞建图首帧/可见内容验收，但不阻塞地图显示、WASD、自由移动或 Nav2 运动入口。
