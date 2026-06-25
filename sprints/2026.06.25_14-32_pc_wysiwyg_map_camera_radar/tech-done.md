# PC 首屏地图/画面/雷达现场视图

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `实时画面` 继续使用真实 `<video data-testid="robot-camera-preview-video">` 承载画面。
  - 普通首屏 `地图` 卡新增现场地图视口 `plain-map-wysiwyg-view`，只消费已有 summary、map refresh、map lifecycle 和 operator route/map readback。
  - 地图视口在缺定位时明确显示 `位置未读到`，不伪造机器人坐标；雷达 marker 直接显示 `雷达已运行 / 雷达待刷新 / 雷达未运行` 等当前状态。
- `pc-tools/workstation/src/styles.css`
  - 给首屏 video 和地图视口增加稳定尺寸、边界和 marker 样式，避免刷新、hover 或状态变化造成布局跳动。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖默认首屏必须存在真实 video 节点、地图视口、雷达 marker 和缺定位提示。
  - 覆盖 `lifecycle_running=true` 但 scan proof 不完整时，地图视口显示 `雷达待刷新` 且不提示重复 `启动雷达`。
- `docs/product/pc_tools_workstation.md`
  - 同步 PC 工作站默认公开入口 `0.0.0.0:7001`。
  - 记录首屏现场地图视口的可见状态、数据来源和控制边界。

## 验证结果

- 已通过 targeted Vitest：
  - `npm test -- -t "renders Robot Control V1|treats running lidar"`
  - 结果：1 个 test file 通过，2 个用例通过，150 个用例按过滤跳过。
- 已通过完整 Vitest：
  - `npm test`
  - 结果：2 个 test file 通过，152 个用例通过。
- 已通过静态检查：
  - `npm run lint`
  - 结果：0 error，0 warning。
- 已通过构建：
  - `npm run build`
  - 结果：`tsc -p tsconfig.app.json`、`vite build`、`tsc -p tsconfig.server.json` 全部通过。
- 已通过补丁检查：
  - `git diff --check`
  - 结果：无 whitespace/error 输出。
- 已通过本机浏览器只读验证：
  - URL：`http://127.0.0.1:7001/`
  - 首屏读到 `雷达待刷新`、地图视口 `地图可见 / 地图记录已读取`，video 容器尺寸约 `234x132`，地图视口尺寸约 `234x210`。
  - 该验证只读取 DOM 和布局盒，不点击发车、manual、keyboard pulse、stop、delivery complete 或 `/cmd_vel`。
- `npm test` 会刷新历史 smoke artifact 的 `checked_at`；本轮已恢复：
  - `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/camera_frame_quality_dom_smoke.json`
  - `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/pc_plain_user_home_dom_smoke.json`

## 剩余风险

- 本轮只做 PC 首屏可视化闭环，不新增后端 `readback_summary.map` 合同；真实地图图像、真实 AMCL 坐标和点击地图发目标仍未接入。
- 本轮没有触发任何会让小车运动的接口；真实 Nav2 路线执行、delivery success 和 PC 键盘连续手控仍需要在现场显式确认后继续验证。
