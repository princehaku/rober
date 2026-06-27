# 2026.06.27 17:22 PC 自由移动键盘快捷入口

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 将自由移动 / 建图卡片的键盘快捷入口拆成两种 gate：相机或雷达未 ready 时，勾安全确认即可启用“键盘自由移动”；相机和雷达都 ready 时，仍按建图流程要求先开始地图记录。
  - 自由移动模式下，快捷键盘启用后主卡片显示“按住方向键/WASD 低速移动；松开即停”，按住时显示当前方向和 pulse 进度，停止中/停止失败也使用“自由移动状态”文案。
  - 保持真实运动边界不变：启用键盘本身不发 manual，只有按住方向键才走固定 manual pulse，松开/失焦仍走 stop。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展“相机和雷达未 ready 时自由移动与建图区分”用例，覆盖安全确认后启用键盘自由移动、启用不发车、按住才发 `/api/robot-control/base/manual`、松开走 `/api/robot-control/base/stop`。
  - 保留“相机和雷达 ready 时，键盘扫图必须等地图记录启动”的用例，防止建图验收流程被自由移动 gate 放松。
- `docs/product/pc_tools_workstation.md`
  - 记录普通首屏自由移动键盘快捷入口的行为边界。

## 验证结果

- 已通过：`npm test -- --run test/App.test.ts -t "splits free movement from mapping acceptance when camera and radar are not ready|keeps free-roam keyboard locked until map recording starts"`
  - 结果：目标 2 个用例 passed，其他 App 用例 skipped。
- 第一次全量 `npm test -- --run` 发现 2 个旧断言仍把自由移动模式的下一步固定为“开始记录（不发车）”；已更新为“启用键盘自由移动”，并保留记录按钮可用、不自动发 manual 的断言。
- 已通过：`npm test -- --run`
  - 结果：2 test files passed，300 tests passed。
- 已通过：`npm run build`
  - 结果：Vite 构建成功，当前产物为 `assets/index-DW0cu4I8.js` 和 `assets/index-DkzBjvNI.css`。
- 已通过：`npm run lint`
  - 结果：ESLint 无报错。
- 已通过：`git diff --check`
  - 结果：无空白或 patch 格式问题。
- 已确认：`http://127.0.0.1:7001/`
  - 结果：当前页面引用 `assets/index-DW0cu4I8.js`；Node 仍监听 `*:7001`，未改 Clash 或系统代理。

## 剩余风险

- 该轮只通过 PC 前端 mock 验证键盘入口和代理调用顺序，没有在真实小车上按住方向键验证 wheel raw L/R 非零。
- 摄像头 UVC 无帧、Nav2 ROS 模式完整路线复验、delivery success 仍是独立未完成项。
