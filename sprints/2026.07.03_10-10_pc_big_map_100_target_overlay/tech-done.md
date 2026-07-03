# PC 大地图 100% 默认与目标点贴图

## Sprint 类型

sprint_type: micro

本轮按 CEO 现场反馈处理 PC 地图太小问题，不启用 subagent。目标是让普通 PC 首页保持简易驾驶台，但地图默认足够大，并完整显示底图、Nav2 路线、机器人位置、雷达点和目标点；ROS2 配套只作为工程观察入口。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首页地图默认缩放从 `45%` 完整态势改为 `100%` 细节视角，`适配` 保留为 `45%` 看全图。
  - 放大地图后自动把机器人、路线目标点和雷达 marker 带进可视区域，只改变滚动视角，不改变地图坐标或任何运动门禁。
  - 地图 overlay 合同补齐 `target`，`data-map-zoom-affects`、`data-refresh-affects` 和 `data-wysiwyg-overlays` 均覆盖 `image-route-robot-radar-target`。
- `pc-tools/workstation/src/styles.css`
  - 普通首页地图卡改为纵向 flex，默认收起长说明、地图生命周期按钮和工程说明正文，把首屏高度让给真实地图画布。
  - 首页地图画布高度在 1280x720 下实测为 `858x470`，避免再次被说明文字压成细条；点击 `ROS2观察` 仍可展开 RViz2/Foxglove 只读观察入口。
- `pc-tools/workstation/src/server/robotControlSummary.ts`、`pc-tools/workstation/src/shared/contracts.ts`
  - summary/live closure 合同同步 `map_display_default_zoom_percent=100%`、`map_display_fit_zoom_percent=45%`、`map_display_wysiwyg_overlays=[image,route,robot,radar,target]`。
- `docs/product/pc_tools_workstation.md`
  - 同步 PC 地图当前有效口径：普通首页和 `/map` 默认 `100%`，`适配` 回 `45%`，ROS2 配套为 RViz2/Foxglove 只读观察，不替代普通用户 PC 简易界面。
- `pc-tools/workstation/test/App.test.ts`、`test/robotControlSummary.test.ts`、`test/catalog.test.ts`
  - 更新默认缩放、target overlay 和实时只读刷新相关断言。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- App.test.ts robotControlSummary.test.ts catalog.test.ts`
  - 结果：`Test Files 3 passed (3)`，`Tests 435 passed (435)`。
  - 中间曾出现一次 catalog 短预算并发波动，单独复跑目标用例通过，随后全组复跑通过。
- 通过：`cd pc-tools/workstation && npm run build`
  - 结果：TypeScript 与 Vite build 通过；仍有既有 chunk size warning。
- 通过：重启 PC Node 到 `0.0.0.0:7001`
  - `lsof` 显示 `node` 监听 `TCP *:7001`。
  - `/api/health` 返回 `workstation_host=0.0.0.0`、`workstation_port=7001`、`default_robot_api_base_url=http://192.168.1.11:8787`。
- 通过：系统 Chrome 1280x720 浏览器验证 `http://127.0.0.1:7001/`
  - `plain-map-panel` 为 `888x624`，地图 layer 为 `858x470`。
  - `data-map-zoom-percent=100%`、`data-default-map-zoom-percent=100%`、`data-fit-map-zoom-percent=45%`。
  - `data-wysiwyg-overlays=image-route-robot-radar-target`，summary overlay 为 `image,route,robot,radar,target`。
  - 机器人、目标点、雷达 marker 均在地图 layer 和页面可视区域内；首页 caption、长验收说明和 ROS2 说明正文默认隐藏。
- 通过：只读接口验收
  - summary 返回 `map_display_default_zoom_percent=100%`、`map_display_fit_zoom_percent=45%`、`map_display_wysiwyg_overlays=[image,route,robot,radar,target]`、`map_current_visible=true`、`path_current_visible=true`、`radar_map_points_visible=true`、`nav2_goal_succeeded=true`。
  - map preview 返回 `path_preview_point_count=18`、`route_target_visible=true`、`target={x:0.8,y:0.05,frame_id=map,source=path_preview_points,source_index=17}`、`robot_pose_status=map_pose_observed`、`radar_overlay_status=loaded`。

## 剩余风险

- 摄像头仍未出可显示画面：PC 读回 `source_diagnosis_status=uvc_full_speed_usb_not_exclusive`、`camera_usb_speed=12M`、`camera_hardware_action_required=true`。当前判断仍是 USB full-speed/物理链路问题，不是页面独占。
- 运动闭环仍缺硬件轮速证据：summary 读回 `wheel_lr_nonzero_proven=false`，不能把 Nav2 action success 直接升级为真实底盘移动成功。
- delivery success 仍未证明：summary 读回 `delivery_success=false`。本轮只解决 PC 地图显示与 ROS2 观察入口，不声明送达闭环完成。
