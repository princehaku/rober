# PC 行程执行进度 WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏地图 caption 新增 `行程执行` 短状态，显示执行中、已到达且有反馈、已到达但缺反馈、旧到达记录或未通过。
  - `行程操作` 卡片新增 `行程进度` 行，把直接执行/最近执行结果翻译成普通用户可理解的下一步。
  - 新增状态只消费已加载的直接执行或最近执行结果，不自动读取 latest、不自动执行 Nav2、不提交送达确认、不发送手控或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖已到达且有执行反馈、已到达但缺反馈、最近行程未通过三种 WYSIWYG 文案。

## 验证结果

- `npm test -- --testNamePattern "Nav2|plain trip|goal execution|行程|route"`：通过，2 个测试文件，32 个相关测试通过。
- `npm run lint`：通过。
- `npm test`：通过，2 个测试文件，167 个测试通过。
- `npm run build`：通过，完成 TypeScript 和 Vite production build。

## 剩余风险

- 本轮是 PC 端执行结果展示增强，不代表真实 Nav2 HIL 行程已重新跑通。
- 真车完整行程仍需要现场 operator 在 7001 页面勾选安全确认后显式执行，并由上位机返回真实执行反馈样本。
