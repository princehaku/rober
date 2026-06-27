# 2026.06.27 17:15 PC 自由移动近障碍主卡片提示

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 将自由移动近障碍提示拆成无前缀的人话函数，避免卡片主文案拼接出重复标点。
  - 在自由移动 / 建图主卡片 `hint` 中加入 `obstacle_clear` 非 ready 证据：未勾安全确认、可移动、可建图三个状态都会显示“当前雷达近障碍：...，原地换向避让，不继续直行”。
  - 在 `plain-free-roam-drive-status` 中加入同样提示，让普通用户不必去“当前事实”里找近障碍风险。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 runtime `/scan` 优先显示用例，断言自由移动主卡片 hint 和 drive-status 都显示近障碍提示。
- `docs/product/pc_tools_workstation.md`
  - 记录普通首屏自由移动主卡片近障碍提示的展示边界。

## 验证结果

- 已通过：`npm test -- --run test/App.test.ts -t "derives radar running state from runtime scan gates when lidar readback is missing"`
  - 结果：目标用例 1 passed，其他 App 用例 skipped。
- 第一次全量 `npm test -- --run` 发现 2 个旧断言仍要求未勾安全确认时不显示近障碍；已修正断言，保留安全锁定和近障碍可见两个口径。
- 已通过：`npm test -- --run`
  - 结果：2 test files passed，300 tests passed。
- 已通过：`npm run build`
  - 结果：Vite 构建成功，当前产物为 `assets/index-C0XOdfZi.js` 和 `assets/index-DkzBjvNI.css`。
- 已通过：`npm run lint`
  - 结果：ESLint 无报错。
- 已通过：`git diff --check`
  - 结果：无空白或 patch 格式问题。
- 已确认：`http://127.0.0.1:7001/`
  - 结果：当前页面引用 `assets/index-C0XOdfZi.js`；Node 仍监听 `*:7001`，未改 Clash 或系统代理。

## 剩余风险

- 该轮只改 PC 前端文案和 DOM 断言，不触发真实小车运动；自由移动真实避障效果仍以现场上车状态机和 operator 安全确认后的硬件验证为准。
- 摄像头 UVC 无帧、Nav2 ROS 模式复验、wheel raw L/R 非零证明仍属于独立未完成项，本轮不宣称解决。
