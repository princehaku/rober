# PC 建图相机复测入口

## sprint_type

micro

## 实际改动

- 在 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 的 `plain-mapping-camera-unblock-plan` 增加 `plain-mapping-camera-recovery-refresh` 按钮。
- 按钮固定执行相机首帧复测、共享 MJPEG 状态读取、summary 刷新，用于确认“相机不是页面独占但无首帧”的现场恢复路径。
- 按钮和父级 DOM 同步暴露 no-motion 合同：不启动独占相机、不启动地图 runtime、不启动自由移动、不执行 Nav2/manual/keyboard、不提交 delivery、不 stop、不发布 `/cmd_vel`。
- 在 `pc-tools/workstation/test/App.test.ts` 增加默认首页 DOM 合同断言和独立点击测试，确认复测按钮只调用固定相机/summary 只读链路。
- 更新 `docs/product/pc_tools_workstation.md`，记录普通首屏建图相机复测入口与安全边界。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default|rechecks mapping camera recovery"`。
- 本轮尚未执行真实小车运动 smoke；按当前安全边界，没有新发任何 live motion/control POST。

## 剩余风险

- 真实相机仍可能因为 USB、供电、UVC 设备或上车端采集链路无首帧而失败；本轮只补 PC 侧复测入口和 no-motion 合同，不替代硬件排查。
- ROS2 配套地图观察继续采用既有路径：普通用户优先 `/map` 大地图；工程调试用 RViz2，远程浏览器观察用 Foxglove bridge。
