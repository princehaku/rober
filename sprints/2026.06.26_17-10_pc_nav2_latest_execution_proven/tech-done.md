# PC Nav2 latest 执行证明口径修复

sprint_type: micro

## 实际改动

- 修复 `pc-tools/workstation/src/server/index.ts` 的 Nav2 latest/execute 摘要口径：当上位机外层 fail-closed 摘要带 `nav2_goal_execution_proven=false`，但真实 action 证据已经满足 `goal_succeeded + goal_accepted + result_received + result_status=succeeded + robot_control_executed=true` 时，PC 端 `goal_execution_key_values.nav2_goal_execution_proven` 归一化为 `true`。
- 兼容两种真机响应形状：`latest_result` 嵌套 action artifact，以及顶层直接返回 action artifact。
- 补充 `pc-tools/workstation/test/catalog.test.ts` 覆盖：
  - 外层 `nav2_goal_execution_proven=false` 不再压掉内层真实执行成功证据。
  - 顶层 action 成功响应也能推导出 `nav2_goal_execution_proven=true`。

## 验证结果

- `npm test`：通过，2 个测试文件，221 个用例通过。
- `npm run build`：通过；Vite 仍提示 bundle chunk 大于 500 kB，这是既有构建提醒，不影响产物生成。
- `npm run lint`：通过。
- `git diff --check`：通过。
- PC API 已重启到 `0.0.0.0:7001`，监听 PID 为 `85681`。
- 真机 smoke：
  - 请求：`GET http://127.0.0.1:7001/api/robot-control/nav2/goal/execution/latest?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`
  - 返回关键字段：`proxy_status=latest_loaded`、`remote_http_status=200`、`kv_status=goal_succeeded`、`kv_nav2_goal_execution_proven=true`、`kv_goal_accepted=true`、`kv_result_received=true`、`kv_result_status=succeeded`、`kv_feedback_sample_count=8`、`kv_robot_control_executed=true`、`top_robot_control_executed=true`、`delivery_success=false`、`blocked_reasons=[]`。

## 剩余风险

- 本轮只修 PC 端 Nav2 latest 执行证明聚合；未证明新的物理位移、未做 HIL 现场导航复跑。
- `delivery_success=false` 保持不变，说明送达确认仍需后续材料/确认链路完成。
- 摄像头多人实时预览和自由移动/自动驾驶完整现场复验仍属于后续迭代范围。
