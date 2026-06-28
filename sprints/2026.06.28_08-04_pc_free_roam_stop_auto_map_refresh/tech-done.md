# PC 自动扫图 stop 后地图自动刷新

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `stopFreeRoamAutonomy()` 在上车端 stop 成功后自动调用只读 `refreshMapPreview({ countForFreeRoamSession: true, radarStatusRefresh: true })`。
  - stop 后先清空旧的扫图地图 fresh 标记，再用停止后的真实地图画面重新置位，避免沿用启动前或运动中的旧画面。
  - 自动刷新只读 map preview 和 radar status，不重新启动 free-roam，不发送 manual、Nav2、delivery、stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 更新自动扫图 start/stop 主链路测试，断言 stop 后自动多一次 map preview，地图 marker 直接进入 `自动扫图已停止，可保存`，下一步聚焦保存地图。
  - 更新 start pending 时排队 stop 的测试，断言启动返回后自动 stop 也会自动刷新地图并进入可保存。
  - 继续断言不会调用 base manual、Nav2 goal 或 `/cmd_vel`。
- `pc-tools/README.md`
  - 同步 stop 后自动刷新停止后地图画面的 PC 合同。
- `docs/product/pc_tools_workstation.md`
  - 同步产品文档，说明刷新成功直接进入保存，失败仍保留重试刷新入口。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "starts free-roam autonomy through the fixed proxy only after ready readback and safety confirmation"`
  - 通过：`1 passed | 202 skipped (203)`。
- `cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "free-roam autonomy"`
  - 通过：`10 passed | 193 skipped (203)`。
- `cd pc-tools/workstation && npm test`
  - 通过：`2 passed (2)`，`351 passed (351)`。
- `cd pc-tools/workstation && npm run lint`
  - 通过：`eslint .` 无报错。
- `cd pc-tools/workstation && npm run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 成功；保留既有 Vite chunk size warning。
- `git diff --check`
  - 通过：无 trailing whitespace 或 patch 格式问题。

## 剩余风险

- 本轮是 PC 软件侧流程改动，未在真实上位机执行自动扫图 stop。
- 如果真实 map preview 在 stop 后失败，普通首屏会保留重试刷新入口；真实地图内容是否可用仍需现场建图验证。
- 旧的 `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/*.json` 脏文件不是本轮改动，提交时保持不纳入。
