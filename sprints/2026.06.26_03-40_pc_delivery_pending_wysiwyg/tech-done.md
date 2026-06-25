# PC 送达确认 Pending 所见即所得

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏点击 `确认送达（不发车）` 后，只要本轮 Nav2 行程已到达且送达确认请求仍在 pending，地图终点 marker 显示 `送达确认中`。
  - 地图 caption 在 pending 期间显示 `行程执行：已到达，反馈 N 次，送达确认中`，避免 operator 误以为送达已经成功或页面没有响应。
  - `任务收口` pending 文案区分最终确认提交中和 latest/check 读取中；红色确认按钮 pending 时显示 `确认中`。
- `pc-tools/workstation/src/styles.css`
  - 为 `送达确认中` 的路线目标 marker 增加 pending 样式，视觉上不等同于 `已送达`。
- `pc-tools/workstation/test/App.test.ts`
  - 新增延迟 `delivery/complete` 的普通首屏流程测试，覆盖：图上路线已到达、材料和最终确认已齐、点击确认送达后 pending 期间地图 marker / caption / 任务收口状态同步更新，且不调用 manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 记录 2026-06-26 03:40 起的送达确认 pending WYSIWYG 行为和不发车边界。

## 验证结果

- 已通过目标用例：

```bash
cd pc-tools/workstation
npx vitest run test/App.test.ts -t "shows delivery confirmation pending on the map while final completion is in flight"
```

结果：`1 passed | 93 skipped`。

- 已通过静态检查：

```bash
cd pc-tools/workstation
npm run lint
```

结果：`eslint .` 通过。

- 已通过生产构建：

```bash
cd pc-tools/workstation
npm run build
```

结果：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 通过。

- 已通过完整 PC 测试：

```bash
cd pc-tools/workstation
npm test
```

结果：`2 passed (2)`，`188 passed (188)`。

- 已通过 diff 空白检查：

```bash
git diff --check
```

结果：通过，无输出。

## 剩余风险

- 本轮只做 PC/mock 验证，未触发真实小车运动、真实 Nav2 行程或真实 delivery gate。
- `送达确认中` 只表示本页已经发起最终确认请求且尚未返回，不证明 delivery success；最终仍以后端 `delivery/complete` 返回为准。
