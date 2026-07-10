# O7 Worker Report

## 实际改动文件

- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `docs/product/pc_tools_workstation.md`
- `pc-tools/README.md`

## 用户旅程变化和触点收益

- O7 consumer detail / artifact bundle readiness 的 fixture 与断言现在明确证明 `nav_msgs/msg/Odometry` matrix item 可被 UI 读取为 `decode_status=decoded`。
- PC 端页面文案和文档同步说明 semantic replay / full semantic decode matrix 已覆盖 Odometry，但仍保持只读、离线、非成功证明口径。
- 运营/研发在查看同一 `task_id` 的 route bag decoder 覆盖时，不再只看到 Odometry failed 样例，能直接看到 decoded label、counts 和 coverage 提升。

## 改动文件和接口影响

- `pc-tools/workstation/test/catalog.test.ts`
  - 把 route bag semantic replay fixture 补到 `semantic_topic_types` 包含 `nav_msgs/msg/Odometry`。
  - 把 full semantic decode matrix fixture 的 `/odom` item 从 failed 改成 `decode_status=decoded`、`decoder_name=decode_odometry_payload`。
  - 同步更新 decoded/failed counts、coverage ratio、blocked reasons 和 next required evidence 断言。
- `pc-tools/workstation/test/App.test.ts`
  - 同步 DOM fixture 与页面断言，证明 UI 会显示 Odometry decoded matrix item、decoder label 和新的 counts/coverage。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 更新 semantic replay 中文注释，明确白名单摘要已包含 Odometry。
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
  - 更新 semantic replay 中文注释和页面提示文案，避免文案仍停留在 LaserScan/Image/TF。
- `docs/product/pc_tools_workstation.md`
  - 更新 O7 consumer read / semantic replay / full semantic decode matrix 产品边界，写明 Odometry decoded 仍只是 local/offline software proof。
- `pc-tools/README.md`
  - 同步更新 O7 preview 主路径说明，补充 Odometry 已纳入只读 semantic coverage。

## 前后端/ROS2 联调结果

- 本轮未新增前后端接口，也未改变 O7 adapter 的 fail-closed 逻辑。
- 通过 fixture/test 证明当前 O7 consumer 与 UI 已能消费并展示 O6/Algorithm 提供的 Odometry decoded matrix item。
- `ready_not_route_execution_proof` 继续只表示本地/离线 semantic coverage 可读，不表示真实 route execution 或 delivery success。

## 验证命令输出结果

```text
cd pc-tools/workstation && npm run test && npm run build && npm run lint

Test Files  3 passed (3)
Tests       482 passed (482)
Duration    45.16s

vite build completed
dist/assets/index-DvFRaNnV.css     82.17 kB
dist/assets/index-Cd8zoKjg.js   1,481.79 kB

eslint .
```

## 失败定位

- 无。验收命令一次通过。

## 剩余风险

- 这轮只证明 O7 在 local/mock consumer detail 上能展示 Odometry decoded coverage，不证明真实 production cloud、真实 route bag 全量语义回放、真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation 或真实 delivery success。
- 当前 fixture 仍保留 `diagnostic_msgs/msg/DiagnosticArray` unsupported，因此 full semantic decode matrix 仍带 `route_bag_full_semantic_decode_matrix_unsupported_types_present`。
