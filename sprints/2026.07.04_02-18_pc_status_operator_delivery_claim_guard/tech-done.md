# PC status operator delivery claim guard

## sprint_type

micro

## 实际改动

- 修正 PC `GET /api/robot-control/summary` 的 dangerous true 扫描：`/api/status` 内嵌的 `operator_report.structured_hil_claims.delivery_success=true` 只作为人工送达材料回显，不再把 PC 控制台误判为 `blocked`。
- 保持 fail-closed 边界：顶层 `delivery_success=true`、非 operator report 路径的 `structured_hil_claims.delivery_success=true`、`hil_pass=true` 等仍会 blocked。
- 补充单测覆盖现场 `/api/status.operator_report.structured_hil_claims.delivery_success` 形状，并保留伪造 structured HIL claim 的 blocked 断言。
- 同步更新 `docs/product/pc_free_roam_mapping_design.md` 和 `docs/product/pc_tools_workstation.md`，明确普通用户用 PC 大地图和 `/map`，RViz2/Foxglove 只作为工程观察；delivery success 材料不升级成全局整机成功。

## 验证结果

- 通过：`npm test -- test/catalog.test.ts -t "structured HIL"`，1 个测试文件，2 个相关测试通过。
- 现场 PC 服务已重启到 `0.0.0.0:7001`，`lsof` 显示 `node` 监听 `TCP *:7001`。
- 现场上位机连通：`ssh root@192.168.1.11 -p 7878` 成功，`8787` Robot API 和 `8088` camera service 均 active。
- 修复后 live summary：`connection=readable`、`blocked=0`、`dangerous=[]`、`blocked_reasons=[]`。
- 地图 live：`/api/robot-control/map/preview` 返回 `image=true`、原始地图 `261x113`、`path_count=18`、`robot_pose_status=map_pose_observed`、`route_target_visible=true`。PC CSS 合同为高度优先大画布放大，原始小 PNG 不按原尺寸显示。
- ROS2 配套 live summary：`map_display_primary_tool=pc_big_map`、`map_display_primary_url=/map`、`map_display_ros2_companion_tools=[rviz2,foxglove]`、RViz2 命令 `ros2 launch ros2_trashbot_bringup rviz.launch.py`、Foxglove bridge 命令 `ros2 launch ros2_trashbot_bringup foxglove_bridge.launch.py`、WebSocket `ws://192.168.1.11:8765`，且 `map_display_starts_ros2=false`、`map_display_sends_motion_when_clicked=false`。
- 手控 live：短 `forward` PWM 代理返回 `proxy_status=command_forwarded`，随后 stop 返回 `proxy_status=command_forwarded`；summary 返回 `keyboard_continuous_motion_verified=true`、`keyboard_command_raw_lr_nonzero=true`、`keyboard_wheel_lr_nonzero=false`。
- Nav2/自动路线 live：summary 保留 `nav2_status=goal_succeeded`、`nav2_result=succeeded`、`nav2_base_command_nonzero=true`、`nav2_imu_motion=true`、`nav2_wheel_lr=false`。
- 送达 live：`POST /api/robot-control/delivery/complete` 返回 `completion_forwarded`、`delivery_success=true`；`GET /api/robot-control/delivery/latest` 返回 `delivery_success=true`，route acceptance packet 显示 `delivery_success=true`。
- 相机 live：共享预览不是页面独占，`exclusive_camera_claim=false`；USB recovery 已触发服务重启，DV20 在 `/dev/video1`、UVC、480M，但首帧 probe 仍 `probe_total_timeout` / `uvc_no_frame_not_exclusive`，没有真实画面。

## 剩余风险

- 相机仍未看到实时画面。当前证据指向 DV20/UVC 输入、视频线、接口、供电或源信号问题，不是 PC 页面独占；它继续阻塞实时图传和建图视觉验收，但不阻塞地图、WASD、自由移动或图上路线执行。
- WAVE ROVER `T=1001` wheel raw L/R 仍为 `0/0`，本轮只证明 PC 命令 raw 非零和 IMU/运动信号，不宣称 wheel raw L/R 非零。
- Codex 内置浏览器两次卡在本地页 attach，未取得浏览器截图；本轮 UI 验证以 Vitest DOM 合同、live API 和 CSS 合同为准。
