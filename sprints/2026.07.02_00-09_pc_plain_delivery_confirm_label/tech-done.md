# PC 普通送达确认标签

sprint_type: micro

## 实际改动

- 将 PC summary 现场验收缺失证据里的 `delivery_success` 可见标签改为“送达确认”，机器 id 仍保持 `delivery_success`。
- 将普通首屏目标收口清单、轮速复验闭环、完整行程验收文案中的“delivery success”改为“送达确认”，避免普通用户界面出现工程英文任务名。
- 同步 `pc-tools/README.md` 和 `docs/product/pc_tools_workstation.md`，明确普通可见标签和接口字段的边界。

## 验证结果

- 已通过：`git diff --check`
- 已通过：`cd pc-tools/workstation && npm test -- robotControlSummary.test.ts App.test.ts`，2 个测试文件、245 个用例通过。
- 已通过：`cd pc-tools/workstation && npm run lint`
- 已通过：`cd pc-tools/workstation && npm run build`；Vite 仍提示既有大 chunk warning。
- 已通过：重启 `0.0.0.0:7001` 后回读 `GET /api/robot-control/summary`，`field_acceptance_missing_evidence_ids` 仍包含 `delivery_success`，对应 `field_acceptance_missing_evidence_labels/items.label` 显示“送达确认”，`field_acceptance_packet.sends_motion_when_clicked=false`。

## 剩余风险

- 本轮只改 PC 可见文案和合同说明，不执行发车、不提交送达、不证明真实 wheel raw L/R 非零、完整 Nav2 路线现场通过或真实送达完成。
