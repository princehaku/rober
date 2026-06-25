# PC Local Radar Scan WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏地图在已有 `scan_preview_points`、但没有 `robot_pose.frame_id=map` 时，新增右上角雷达局部点云小窗，显示 `雷达局部点 N 个，等待地图位置`；有 map-frame 位姿时继续使用原来的真实地图 scan overlay。
- `pc-tools/workstation/src/styles.css`：新增局部雷达点云小窗样式，固定在地图框内，不参与点击、不遮挡地图操作。
- `pc-tools/workstation/test/App.test.ts`：新增无定位但有 scan 点的回归测试，锁定只显示局部点云、不显示全局地图点、不触发 manual/Nav2/delivery。
- `docs/product/pc_tools_workstation.md`：同步记录缺定位时的雷达局部点云展示边界。

## 验证结果

- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm test`：通过，156 tests。
- `cd pc-tools/workstation && npm run build`：通过。
- PC 7001 只读 summary smoke：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `scan_preview_point_count=72`、`scan_preview_frame_id=laser_frame`、`robot_pose=null`、`amcl_pose_observed=false`、`safe_to_control=false`、`delivery_success=false`。这正好覆盖本轮“缺地图位置但 scan 点已读到”的现场状态。

## 剩余风险

- 本轮没有执行运动命令、Nav2 goal、delivery complete、map start/save/reset 或 radar refresh；只是让已有 scan 点在缺定位时可见。
- 局部点云不是地图坐标，不能替代 AMCL/map-frame 定位。要实现完整“雷达点在真实地图上所见即所得”，仍需要上位机产出 `robot_pose.frame_id=map`。
