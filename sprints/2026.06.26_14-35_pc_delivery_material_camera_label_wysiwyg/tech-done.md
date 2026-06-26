# PC 送达材料按钮按绘帧改文案

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏送达材料按钮在缺视频材料且浏览器还没绘制当前视频帧时显示 `检查画面并准备送达材料` 或 `检查画面并补送达画面`。
  - 浏览器已经绘制当前视频帧时继续显示 `准备送达材料` / `补送达画面`，保持普通用户简洁口径。
  - 动作保持不变：只读取最近行程、固定 camera first-frame probe 和 delivery latest，不提交送达。
- `pc-tools/workstation/test/App.test.ts`
  - 更新缺送达画面、画面关闭后、已绘帧后的按钮文案断言。
  - 将送达材料动作测试改为按 `data-testid` 触发，避免文案升级影响行为测试。
- `docs/product/pc_tools_workstation.md`
  - 记录送达材料按钮按绘帧显示的 WYSIWYG 边界。

## 验证结果

- `npm test -- -t "syncs latest readbacks and pre-fills delivery route material after visible-route trip execution|keeps final delivery confirmation disabled until every operator checklist item is checked|camera closing state|near-black preview"`：通过，1 个测试文件执行，4 个用例通过，198 个用例按过滤条件跳过。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 仍输出既有 chunk size warning，未新增构建错误。
- `npm test`：通过，2 个测试文件，202 个用例全部通过。
- `git diff --check`：通过。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：确认 Node 仍监听 `*:7001`。
- 完整 `npm test` 会刷新两个旧 smoke artifact 的 `checked_at`，本轮已恢复为原始时间戳，避免提交无关测试副作用。

## 剩余风险

- 当前为 PC 前端 mock 验证，未触发真实 WebRTC 摄像头、真实 camera probe、operator report、delivery complete、manual、Nav2、stop 或 `/cmd_vel`。
