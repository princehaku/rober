# Tech Done

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 放宽普通首屏自由移动 start 条件：不再依赖 `free_roam_autonomy_start_ready` 或 `free_roam_autonomy=ready`。
- `开始自由移动（低速）` 现在只要求默认小车地址可用、已勾现场安全确认、停止兜底可用、没有正在刷新地图，并继续只调用固定 PC 代理 `/api/robot-control/free-roam/autonomy/start`。
- 相机首帧和雷达 running 不再阻塞低速自由移动，只决定 `confirm_mapping_active`：地图记录已启动且画面、雷达都 ready 时才按建图记录，否则只按自由移动记录。
- 更新普通首屏 readiness 文案，明确“可自由移动”和“可验收建图”是两层能力。
- 在 `pc-tools/workstation/test/App.test.ts` 增加/更新回归：summary 标记自动扫图 locked 时，勾安全确认后仍转发固定 free-roam start，且不调用 `map/start`、`base/manual`、Nav2、delivery 或 `/cmd_vel`。
- 同步更新 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `npm test -- --run test/App.test.ts`：150 tests passed。
- `npm run lint`：通过。
- `npm run build`：通过，包含 `tsc -p tsconfig.app.json`、`vite build`、`tsc -p tsconfig.server.json`。
- `git diff --check`：通过。

## 剩余风险

- 该轮只放开 PC 首屏到固定上车 free-roam start 代理的入口；真实小车是否运动仍取决于上车端 `/api/free-roam/autonomy/start`、底盘驱动和现场运动反馈。
- 摄像头无首帧、LiDAR 无 scan/raw 消息、Nav2 当前轮速 L/R 复验仍未在本轮解决。
- 如果上车端 free-roam runtime 仍处于 artifact-only 或拒绝运动，PC 会如实显示 start 失败或只按自由移动记录，不能把它作为建图完成证据。
