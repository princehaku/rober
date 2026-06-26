# 2026-06-26 19:35 Visible Route Requires Robot Pose

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `执行图上路线` 新增 WYSIWYG 门禁：当前路线已经画到地图上时，还必须看到 map-frame 小车位置，才允许普通首屏执行 Nav2 行程。
  - 缺 `robot_pose` 时，路线仍在地图上照实显示，但按钮显示 `先重新定位` 并禁用；行程状态、最小确认、路线说明和进度卡都提示先重新定位。
  - 进度卡在缺定位时聚焦 `重新定位` 按钮，不调用 Nav2 execute、manual、keyboard pulse、delivery、stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 `markRobotPoseVisible` helper，让成功执行路线的测试显式提供 map-frame 小车位置。
  - 更新路线 marker 用例：验证路线可见但小车位置缺失时不会调用 `/api/robot-control/nav2/goal/execute`，并且下一步聚焦 `重新定位`。
- `docs/product/pc_tools_workstation.md`
  - 记录“路线可见 + 小车位置可见”才允许普通首屏执行图上路线的产品边界。

## 验证结果

- `npm test -- App.test.ts`
  - 通过：132 tests passed。
- `npm test`
  - 通过：2 test files、233 tests passed。
- `npm run build`
  - 通过：`tsc -p tsconfig.app.json`、Vite build、`tsc -p tsconfig.server.json` 均完成；仅保留 Vite 现有 chunk size warning。
- Live PC summary：`http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787`
  - `path_generated=true`、`path_preview_point_count=36`、`path_preview_frame_id=map`。
  - `robot_pose=null`，同时 `amcl_pose_observed=true`、`localization_tf_observed=true`；当前 live 正好进入“路线可见但小车位置不可执行”的门禁场景。
  - camera 仍为 `source_first_frame_failed`，LiDAR lifecycle 仍为 `false`。

## 剩余风险

- 当前 live summary 仍显示 `robot_pose=null`，所以 PC 会正确阻止普通图上路线执行；真正完成 Nav2 行程仍需要现场定位恢复、路线执行和反馈样本证明。
- 本轮只改 PC 普通首屏门禁和文案，没有改变上位机 Nav2 后端、底盘控制、雷达 lifecycle 或相机硬件状态。
