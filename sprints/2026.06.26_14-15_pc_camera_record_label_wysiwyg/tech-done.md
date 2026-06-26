# PC 画面记录按钮按绘帧改文案

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏画面记录按钮只有在浏览器 `<video>` 已绘制当前帧时显示 `用当前画面记录`。
  - 未打开、已关闭、等待绘帧或没有可见帧时显示 `检查并记录画面`，避免误导 operator 以为屏幕上已有当前画面。
  - 动作保持不变：点击后仍只运行固定 camera first-frame probe，再把样张 ref 写入 operator report。
- `pc-tools/workstation/test/App.test.ts`
  - 更新关闭画面后的按钮文案断言。
  - 增加绘制真实视频帧后的 `用当前画面记录` 断言。
- `docs/product/pc_tools_workstation.md`
  - 记录画面记录按钮文案和 WYSIWYG 边界。

## 验证结果

- `npm test -- -t "camera closing state|near-black preview"`：通过，1 个测试文件执行，2 个用例通过，200 个用例按过滤条件跳过。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 仍输出既有 chunk size warning，未新增构建错误。
- `npm test`：通过，2 个测试文件，202 个用例全部通过。
- `git diff --check`：通过。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：确认 Node 仍监听 `*:7001`。
- 完整 `npm test` 会刷新两个旧 smoke artifact 的 `checked_at`，本轮已恢复为原始时间戳，避免提交无关测试副作用。

## 剩余风险

- 当前为 PC 前端 mock 验证，未触发真实 WebRTC 摄像头、真实 camera probe、operator report、manual、Nav2、delivery、stop 或 `/cmd_vel`。
