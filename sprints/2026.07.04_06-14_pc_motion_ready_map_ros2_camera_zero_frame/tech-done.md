# PC 运动可用态与大地图 ROS2 配套复核

sprint_type: micro

## 实际改动

- 修正 PC `live-summary` 的普通用户状态：当同轮已证明 command raw L/R 非零且 IMU/车体运动信号存在时，页面状态返回 `ready_for_motion`，wheel raw `T=1001 L/R=0/0` 继续作为反馈诊断风险，不再把 WASD、自由移动和图上路线入口压回“必须先重跑轮速”。
- 新增 summary 回归测试，覆盖“wheel raw 为 0，但 command raw + IMU motion 已证明”的现场状态。
- 复核并记录地图太小的当前方案：普通用户继续用 PC 首页大地图和 `/map` 直达大屏；ROS2 配套为本地 RViz2/Nav2 RViz 配置，远程浏览器观察为 Foxglove bridge + Foxglove Web。二者只看 `/map`、`/scan`、TF、路径、定位和 costmap，不替代简易 PC 控制台，也不发车。
- 复核相机零帧边界：DV20 `/dev/video1` 为 480M UVC、无人独占，但 `v4l2-ctl` 与 `ffmpeg` 对 MJPG/YUYV 多格式直接采帧仍 0 字节；PC USB recovery 返回 `high_speed_zero_byte_no_frame`。当前实时图传缺口继续指向输入源、线材、接口、供电、采集卡或 known-good UVC。

## 验证结果

- `cd pc-tools/workstation && npm test -- test/robotControlSummary.test.ts --run` 通过，17 tests OK。
- `cd pc-tools/workstation && npm test -- test/App.test.ts -t "map display|direct map|ROS2|Foxglove|RViz2|plain map" --run` 通过，7 tests OK / 234 skipped。
- `cd pc-tools/workstation && npm run build` 通过，仅保留 Vite 大 chunk warning。
- 7001 已重启到 `0.0.0.0:7001`，`/` 与 `/map` 均返回 HTTP 200。只读雷达刷新后，PC map preview 已有地图 PNG、路线 18 点、目标点、小车 map pose 和当前雷达贴图，`radar_overlay_status=loaded`、当前雷达点 141 个。
- live-summary 返回 `status=ready_for_motion`，并显示 `map_current_visible=true`、`path_current_visible=true`、`route_target_current_visible=true`、`radar_map_points_current_visible=true`、`keyboard_continuous_motion_verified=true`、`needs_same_window_wheel_rerun=true`、`wheel_lr_nonzero_proven=false`。
- 相机现场复核显示 `exclusive_camera_claim=false`、`source_usage_owner_count=0`、USB `480M`，但首帧仍超时；该问题不阻塞 PC 大地图、WASD、自由移动或图上路线入口。
- 浏览器内置自动化两次连接本机页面超时，未取得截图；已用 App DOM 回归、HTTP 200 和 live API 读回来覆盖本轮验收。

## 剩余风险

- wheel raw 非零仍未闭环，不能把 command raw 或 IMU 动作信号冒充为 WAVE ROVER `T=1001 L/R` 非零。
- 实时图传仍无真实首帧，剩余需要现场检查 DV20 上游视频输入、线材、接口、供电、采集卡或更换 known-good UVC 后复测。
- 本轮只做 PC summary/UI 口径、文档和只读/软件验证；没有再次执行新的 Nav2 真实路线或 delivery success 发车验收。
