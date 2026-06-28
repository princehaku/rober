# PC free roam plain hint dedupe

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：收紧 `readback_summary.free_roam.plain_hint` 的合成逻辑，去掉 `next_action_plain` 中已经由 motion/mapping 两层说明过的停止请求和建图缺口。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：start-ready 时仍保留真正新增的“勾选现场安全确认后可先自由移动”；motion-ready/running 时不再提示“勾选后启动”。
- `pc-tools/workstation/test/catalog.test.ts`：更新 free-roam summary 断言，覆盖 start-ready、缺建图材料和 running 三类口径。
- `docs/product/pc_tools_workstation.md`：同步记录 `free_roam.plain_hint` 去重规则和只读边界。

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "free-roam|Robot Control summary"`，`1 passed`，`49 passed | 111 skipped`。
- 已通过：`npm --prefix pc-tools/workstation run build`，`tsc` 与 `vite build` 均成功；仅保留既有 chunk size warning。
- 已通过：`npm --prefix pc-tools/workstation test`，`2 passed`，`375 passed`。
- 已通过：重启 PC API 到 `0.0.0.0:7001`，`lsof` 显示 `node` PID `44982` 监听 `TCP *:7001`。
- 已通过：只读请求 `GET /api/robot-control/summary`，live `readback_summary.free_roam.plain_hint` 返回 `可先自由移动；当前有停止请求，开始自由移动会先清除停止请求。建图验收未 ready；还差：画面首帧、雷达新鲜、地图记录、地图画面；不影响先低速自由移动。下一步：勾选现场安全确认后可先自由移动。`；`next_action_plain` 仍保留完整诊断，`plain_hint` 已去重。

## 剩余风险

- 本轮只改善自由移动/建图的普通用户只读表达，不启动自由移动、不启动建图、不发送任何运动命令。
- live 车仍需要现场人员勾选安全确认后才能实际启动低速自由移动；本轮未调用该接口。
