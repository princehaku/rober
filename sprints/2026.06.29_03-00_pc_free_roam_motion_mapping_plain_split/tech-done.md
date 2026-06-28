# PC Free Roam Motion And Mapping Plain Split

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：在 `readback_summary.free_roam` 增加 `motion_readiness_plain` 和 `mapping_readiness_plain`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：把“可先自由移动”和“可按建图验收”拆成两个只读白话结论；自由移动只看状态机/停止兜底，建图验收才看画面首帧、雷达新鲜、地图记录和地图画面。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏自由移动事实、建图事实和上车建议优先消费两个短字段，避免长句把相机/雷达缺口误写成不能动。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`：补齐 fixture 和 free-roam 回归断言。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步产品边界和 PC 工作站合同。

## 验证结果

- `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "free-roam|Free roam|自由移动|Robot Control summary"`：通过，1 个文件，48 个测试通过。
- `npm --prefix pc-tools/workstation test`：通过，2 个文件，373 个测试通过。
- `npm --prefix pc-tools/workstation run build`：通过；Vite 保留既有 chunk size warning。
- 7001 本地 live 只读复验：`GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `readback_summary.free_roam.status=start_ready`，`motion_readiness_plain=可先自由移动；当前有停止请求，开始自由移动会先清除停止请求。`，`mapping_readiness_plain=建图验收未 ready；还差：画面首帧、雷达新鲜、地图记录、地图画面；不影响先低速自由移动。`，同时 `safe_to_control=false`、`robot_control_executed=false`。

## 剩余风险

- 本轮只拆清 PC 只读口径和首屏文案，不启动 free-roam、不发键盘/手控/Nav2 命令，不证明真实自由移动或建图完成。
- 当前 live 若相机首帧、雷达新鲜、地图记录或地图画面缺失，仍只能说明“可先自由移动，建图验收未 ready”。
