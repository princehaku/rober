# 2026-06-26 18:50 PC 共享画面、自助移动与定位真相

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - 将 `GET /api/robot-control/camera/mjpeg` 从“每个浏览器各自打开上游 MJPEG”改为“同一 Robot API baseUrl 单上游流 + 多浏览器 fanout”。
  - 最后一个浏览器关闭时释放上游 reader，避免多人进入 PC 页面时互相抢 `/dev/video1`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `free_roam_autonomy_start_ready` 不再把 `lidar_fresh` 当作基础启动硬门禁，只要求上车 runtime 已加载且 stop 兜底 ready。
  - 雷达新鲜度、障碍距离和 HIL 解锁仍保留在门禁列表，不把 artifact-only runtime 伪装成完整自动驾驶 ready。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 地图缺位 marker 新增 `定位缺坐标`：AMCL/TF 有证据但没有 map-frame `robot_pose` 时，不再泛化成“位置未读到”。
- `pc-tools/workstation/src/styles.css`
  - 为 `定位缺坐标` 增加独立警示样式，和真正 `定位失败` 区分。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖 AMCL/TF 已观察但 robot_pose 为空时的普通地图文案。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 MJPEG 多浏览器共享上游 reader。
  - 覆盖雷达 freshness blocked 时 `free_roam_autonomy_start_ready=true`，但完整 free roam 仍 locked。
- `docs/product/pc_tools_workstation.md`
  - 同步 PC MJPEG shared relay、定位缺坐标状态、free-roam 启动门禁和 live 摄像头风险。
- `docs/navigation/free_roam_autonomy.md`
  - 同步 PC 启动门禁口径：基础自助移动不把雷达 fresh 当硬挡板，完整自动扫图仍要求运动 HIL 和避障证据。

## 验证结果

- `npm test -- --run test/catalog.test.ts -t "free-roam start ready|localization reset|mjpeg"`
  - 通过：`3 passed | 98 skipped`
- `npm test -- --run test/App.test.ts -t "AMCL/TF observed|localization reset failure"`
  - 通过：`2 passed | 128 skipped`
- `npm test`
  - 通过：`2 passed (2)，231 passed (231)`
- `npm run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
- PC Node live
  - 已重启到 `0.0.0.0:7001`，监听 PID `93399`，screen `rober-pc-7001` detached。
  - `GET /api/health` 返回 `trashbot.pc_tools_workstation.health.v1`，`safe_to_control=false`、`delivery_success=false`。
- 真实上位机 live summary
  - camera readback：`status=ready`，`selected_path=/dev/video1`，`active_peer_count=0`。
  - localization：`robot_pose=null`，summary 仍可读到 `amcl=true`、`tf=true`，因此 PC 首屏会显示定位缺坐标而不是画假点。
  - free roam：`free_roam_start_ready=true`，`free_roam=locked`，runtime 为 `artifact_only=true`、`cmd_vel_publish_enabled=false`。
  - gates 中 `lidar_fresh=blocked`、`obstacle_clear=not_proven 最近障碍 0.04m`、`motion_hil_unlock=blocked`，说明雷达/HIL 仍是完整自动扫图风险，不再挡基础自助移动入口。
- 摄像头 live 排查
  - 直连上位机 `GET /api/camera/mjpeg` 8 秒内无首帧。
  - PC shared MJPEG proxy 在上游无首帧时返回 fail-closed，不影响其它 API。
  - `POST /api/robot-control/camera/first-frame/probe` 返回 `probe_failed/open_failed`，`/dev/video1` 未读到帧。
  - SSH 到 `root@192.168.1.11 -p 37878` 确认 `/dev/video1` 是 USB DV20，`active_peer_count=0`，未发现其它用户态进程占用；OpenCV 直读 `/dev/video1` 出现 V4L2 `select() timeout`。

## 剩余风险

- 当前真机摄像头问题不在 PC 多人预览 relay：上位机设备/驱动层无法稳定出帧。下一轮应处理 `/dev/video1` UVC 出帧 timeout，例如重启 camera service、重新插拔/复位 USB 摄像头、或调整 camera server 对 DV20 的 V4L2 打开参数。
- 当前自动驾驶不能真车移动仍有两个真实 gate：
  - `robot_pose=null`，AMCL/TF 有证据但没有 map-frame 坐标，Nav2 地图贴图和路线执行仍不能闭环证明。
  - `cmd_vel_publish_enabled=false`、`motion_hil_unlock=blocked`，free-roam 仍是 artifact-only，不发布 `/cmd_vel`。
- 本轮未执行真实 Nav2 发车和真实底盘运动；验证范围是 PC Node/UI 合同、summary 门禁、live 只读状态和摄像头只读/设备探针。
