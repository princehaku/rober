# Delivery Latest Material Refs

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- date: 2026-06-22

## 实际改动

- PC 代理 `GET /api/robot-control/delivery/latest` 新增只读 `delivery_material_refs` 摘要，从上位机 latest delivery result 的 operator report 草稿中抽取视频、相机、route/map 和 operator evidence ref。
- 前端 `loadDeliveryLatest()` 读取到这些 ref 后，只在本页输入为空时自动预填送达材料，让页面刷新后能恢复已有草稿材料。
- 补测试覆盖真实现场状态：latest 已有送达草稿 ref 时，普通首屏显示材料已预填，但不提交 operator report、不调用 delivery complete、不触发 manual 或 `/cmd_vel`。
- 更新 `docs/product/pc_tools_workstation.md` 记录该只读恢复行为。

## 验证结果

- 通过：`npm test`，2 个 test files、118 个 tests 全部通过。
- 通过：`npm run lint`。
- 通过：`npm run build`，完成 `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
- 通过：`git diff --check`。

## 剩余风险

- 本轮不自动采集新画面、不提交最终确认、不确认 delivery success。
- 真实上位机当前仍缺 wheel raw L/R 非零、LiDAR motion delta、operator observed motion/stop 和 delivery success 最终确认；本轮只减少 PC 页面刷新后的材料恢复摩擦。
