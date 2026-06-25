# PC 实时画面关闭 Pending 所见即所得

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏实时画面新增 `关闭中` 状态：点击 `关闭画面` 后，远端 camera peer close 请求未返回前，状态芯片、画面遮罩和 WYSIWYG 文案都显示正在关闭。
  - 本地 video 仍会立即清空，避免继续显示上一轮残留帧；远端释放结果仍以后端 peer close 返回为准。
- `pc-tools/workstation/src/styles.css`
  - 将 `关闭中` 加入 pending 状态芯片样式。
- `pc-tools/workstation/test/App.test.ts`
  - 新增延迟 camera peer close 的普通首屏测试，覆盖关闭 pending 期间 `关闭中` 状态、video 清空、远端 close 请求已发出，以及未调用 manual、Nav2、delivery 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 记录 2026-06-26 03:45 起的实时画面关闭 pending WYSIWYG 行为和不发车边界。

## 验证结果

- 已通过目标用例：

```bash
cd pc-tools/workstation
npx vitest run test/App.test.ts -t "shows camera closing state while peer cleanup is still pending"
```

结果：`1 passed | 94 skipped`。

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

结果：`2 passed (2)`，`189 passed (189)`。

- 已通过 diff 空白检查：

```bash
git diff --check
```

结果：通过，无输出。

## 剩余风险

- 本轮只做 PC/mock 验证，未连接真实 WebRTC 相机和真实上位机 camera peer。
- `关闭中` 只表示 PC 已发起远端 peer close 且尚未返回，不证明上位机已释放所有 camera 资源。
