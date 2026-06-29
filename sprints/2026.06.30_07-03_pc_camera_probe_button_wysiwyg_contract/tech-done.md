# PC 相机只读检查按钮 WYSIWYG 合同

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 为普通首屏实时画面的 `plain-camera-probe` 按钮补齐 DOM 验收合同。
  - 按钮明确暴露固定 `/api/robot-control/camera/first-frame/probe`、`backendSmoke=1`、只读不发车、不打开 WebRTC、不保存 operator report、不启动建图 runtime、不执行 Nav2。
  - 同步暴露当前 MJPEG/视频帧可见性、共享预览 single-upstream 和 exclusive camera claim 状态，方便验收脚本区分“检查画面”和“共享实时预览”。
- `pc-tools/workstation/test/App.test.ts`
  - 在“只读检查画面”用例中补充按钮级 WYSIWYG 合同断言，并继续验证点击后不会调用 camera offer、operator report、manual、Nav2、delivery 或 `/cmd_vel`。
- `pc-tools/README.md`
  - 记录相机只读检查按钮的固定 endpoint、非发车边界和非保存材料边界。
- `docs/product/pc_tools_workstation.md`
  - 同步普通 PC 工作站产品文档，明确共享实时预览仍走 MJPEG relay，“检查画面”只做首帧诊断。

## 验证结果

- 已通过目标用例：
  - `npm test -- test/App.test.ts -t "checks the plain camera frame as a read-only WYSIWYG action"`
  - 结果：`Test Files 1 passed (1)`，`Tests 1 passed | 218 skipped (219)`。
- 已通过全量工作站测试：
  - `npm test -- --run`
  - 结果：`Test Files 2 passed (2)`，`Tests 389 passed (389)`。
- 已通过生产构建：
  - `npm run build`
  - 结果：`vite build` 成功，新 bundle 为 `dist/assets/index-CLXryn0N.js`。
- 已通过 diff 格式检查：
  - `git diff --check`
  - 结果：无输出，检查通过。
- 已重启 PC Node 工作站：
  - `0.0.0.0:7001` 当前由 `node` 监听，PID `12377`。
  - `curl http://127.0.0.1:7001/` 返回 `index-CLXryn0N.js` 和 `index-BmaNglvi.css`。

## 剩余风险

- 本轮只补 PC Web DOM 合同和单元测试，没有真实 UVC/MJPEG HIL 画面复验。
- 真实现场仍需在 7001 页面确认共享 MJPEG 多页面可见、首帧诊断与实际画面一致。
