# PC Nav2 Material Alignment Proof Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏任务收口新增 `plain-nav2-material-alignment` 行程材料对齐验收条。
  - 该验收条明确区分：未读到本轮 Nav2、未读到当前 Nav2 route/map ref、送达材料未准备、材料已匹配当前行程、材料需更新、送达已确认。
  - DOM 暴露 `data-current-nav2-route-map-ref-loaded`、`data-route-map-comparable`、`data-route-map-matches-current-nav2`、`data-material-aligned-current-nav2` 和固定 latest endpoint，避免旧草稿 ref 被误读成当前行程同源证明。
- `pc-tools/workstation/src/styles.css`
  - 为行程材料对齐验收条补齐已对齐、已送达、待行程、待行程 ref、待材料和需更新状态样式。
- `pc-tools/workstation/test/App.test.ts`
  - 锁定默认无行程、恢复旧草稿、本轮材料已匹配、旧材料不匹配、重新准备后匹配等状态。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步说明该行只做 PC Web 只读收口判断，不执行 Nav2、不提交 delivery、不发送任何运动接口。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default"`：通过，1 个目标测试通过。
- `npm test -- test/App.test.ts -t "delivery"`：通过，22 个目标测试通过。
- `npm test -- --run`：通过，2 个测试文件、391 个测试全部通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-BiG9-p6e.js` 与 `dist/assets/index-BK2ry7Oj.css`。
- `git diff --check`：通过。
- 7001 重启：已停止旧监听进程，新监听进程为 `node` PID `4148`，地址 `TCP *:7001`。
- live bundle 检查：`http://127.0.0.1:7001/` 已引用 `index-BiG9-p6e.js` 和 `index-BK2ry7Oj.css`，资源内命中 `plain-nav2-material-alignment`、`行程材料对齐`、`data-material-aligned-current-nav2`、`data-route-map-comparable`、`当前行程编号未读到`、`送达材料已匹配当前行程` 等新合同。

## 剩余风险

- 本轮只改 PC Web 只读收口显示和 DOM 合同，不执行 Nav2、不提交 delivery、不发送 manual、keyboard、free-roam、stop 或 `/cmd_vel`。
- 未做真实上车 HIL 行程/送达验证；真实同源性仍取决于上车 latest 是否返回当前行程 ref 和材料 ref。
