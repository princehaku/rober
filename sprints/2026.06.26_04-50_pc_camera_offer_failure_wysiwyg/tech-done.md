# PC 实时画面 offer 失败 WYSIWYG

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增实时画面 offer 失败的普通提示映射，把 `remote_answer_missing` 等工程原因翻译成现场可执行文案。
  - 新增 `rawFailureReason`，默认首屏显示普通文案，高级诊断继续保留原始失败码。
  - start/stop/streaming/cleanup 路径同步清理或保留失败原因，避免旧失败跨会话污染。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 camera offer 失败测试，覆盖视频框 overlay、画面 WYSIWYG 状态、首屏不暴露原始工程码、高级诊断保留原始码。
- `docs/product/pc_tools_workstation.md`
  - 同步记录实时画面 offer 失败 WYSIWYG 行为边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npx vitest run test/App.test.ts -t "keeps failure status after Start Preview fails instead of collapsing to stopped_by_user"`
  - 1 个 test file passed，1 个测试通过，91 个跳过。
- 通过：`cd pc-tools/workstation && npm run lint`
  - `eslint .` 完成。
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- 通过：`cd pc-tools/workstation && npm test`
  - 2 个 test files passed，186 个测试通过。
- 通过：`git diff --check`
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - `node ... TCP *:7001 (LISTEN)`

## 剩余风险

- 该轮只覆盖 PC 前端 mock 行为，没有打开真实 WebRTC 相机，也没有触发真实机器人运动。
- `remote_answer_missing` 之外的新上位机失败码会回退为 `打开画面失败：<reason>`，后续可按现场高频错误继续补中文映射。
