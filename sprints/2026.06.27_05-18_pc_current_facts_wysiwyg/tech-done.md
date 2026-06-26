# Tech Done

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 普通首屏新增 `plain-current-facts` 当前事实条。
- 当前事实条只读取现有 `robotSummary`/computed 状态，翻译四类现场事实：画面是否无首帧且非独占、雷达是否已启动但地图无新点、行程是否已执行但当前 L/R 待复验、键盘是否可启用。
- 在 `pc-tools/workstation/src/styles.css` 为事实条加紧凑网格样式，保持普通用户简易风格。
- 在 `pc-tools/workstation/test/App.test.ts` 增加默认首屏、雷达无新点、行程已执行但 L/R=0/0 三类断言。
- 同步更新 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `npm test -- --run test/App.test.ts`：150 tests passed。
- `npm run lint`：通过。
- `npm run build`：通过，包含 `tsc -p tsconfig.app.json`、`vite build`、`tsc -p tsconfig.server.json`。
- `npm run typecheck`：未运行成功，原因是 `package.json` 没有 `typecheck` 脚本；已由 `npm run build` 覆盖 TypeScript 编译检查。

## 剩余风险

- 该轮只改善 PC 首屏 WYSIWYG 和易读性，不修复真实摄像头无首帧、LiDAR 无 scan/raw 消息、Nav2 HIL 未完成的问题。
- 事实条只读展示，不会自动发车、自动确认送达或自动建图；完整目标仍需继续推进真实相机/雷达/运动闭环。
