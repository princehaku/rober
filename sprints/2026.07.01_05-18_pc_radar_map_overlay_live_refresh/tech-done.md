# PC 雷达地图贴图 no-motion 复测

## sprint_type

micro

## 实际改动

- 本轮没有改产品代码；执行 PC `7001` 固定 no-motion 雷达刷新链路，推进“雷达开始后地图标记 WYSIWYG”目标。
- 先调用 `POST /api/robot-control/radar/scan-proof/refresh`，再读取 `GET /api/robot-control/map/preview` 和 `GET /api/robot-control/summary`。
- 未执行 Nav2、manual、keyboard、free-roam、map start、delivery、stop 或 `/cmd_vel`。

## 验证结果

- `POST /api/robot-control/radar/scan-proof/refresh` 已转发到上车端；即时 readback 曾出现 `post_refresh_latest_readback_status=not_fresh_after_retry`，说明 PC 没有把旧 proof 冒充为当前贴图。
- 随后 `GET /api/robot-control/map/preview` 返回 `radar_overlay_status=loaded`、`radar_overlay_point_count=72`、`radar_overlay_source_point_count=99`、`radar_overlay_refresh_required=false`、`radar_overlay_primary_blocked_reason=none`。
- `GET /api/robot-control/summary` 返回 `live_wysiwyg_surface_summaries.radar_map_points.completed=true`、`proof_status=completed`、`missing_evidence=[]`；地图读回显示 `radar_overlay_current_visible=true`。
- 当前四项目标仍未完成：相机 WYSIWYG 还缺 `camera_first_frame`，运动闭环还缺同窗口 wheel L/R 非零、delivery success、键盘按住同窗口 wheel L/R 非零和松开后 stop，建图启动还缺相机首帧。

## 剩余风险

- 雷达贴图已在本轮 no-motion 复测中恢复，但真实现场仍需继续观察该状态是否保持新鲜；若后续 proof 再次过期，必须重新走雷达 scan proof refresh + map preview。
- 相机首帧失败仍是 UVC/USB 传输错误方向，非页面独占；需要检查 USB 线、接口、供电或更换 known-good UVC 后再复测。
