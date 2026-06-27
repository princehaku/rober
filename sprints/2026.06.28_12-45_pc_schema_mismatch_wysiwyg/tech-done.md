# 2026-06-28 12:45 PC schema mismatch WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 新增 `isRobotReadbackSchemaMismatch()`，让 `schema_mismatch_count` 只统计已成功读取、且 schema 明确不属于允许前缀的真实合同错配。
  - `fetch_failed`、optional missing、`schema_missing/not_loaded/not_object` 不再计入 schema mismatch。
  - 合法本地相机 schema `trashbot.local_webrtc_camera_*` 不再被误算成上位机 schema mismatch。
- `pc-tools/workstation/test/catalog.test.ts`
  - 在 optional radar latest 缺失、本地相机 schema 和短 readback timeout 场景中断言 `schema_mismatch_count=0`。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录 PC summary 的 schema mismatch 只表示真实合同错配，不再把超时、optional missing 或本地相机 schema 当成 mismatch。

## 验证结果

- `npm test -- test/catalog.test.ts -t "keeps robot connection readable when optional radar latest endpoints are not installed|Robot Control summary returns partial readbacks when the HTTP first-screen budget is shorter than slow camera health"`：通过，2 个用例通过、144 个跳过。
- `npm test`：通过，2 个 test file、333 个测试全部通过。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 仍提示单个 chunk 超过 500 kB，这是既有前端体积 warning，不影响本轮 schema mismatch 计数。
- `git diff --check`：通过。
- 重启本机 PC Node 到 `0.0.0.0:7001`：通过，`lsof` 显示 `node` 监听 `TCP *:7001`。
- 只读检查 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：通过，
  `robot_api_connection.status=degraded`、`failed_count=3`、`blocked_count=0`、
  `schema_mismatch_count=0`。当前 degraded 原因如实保留为
  `status:fetch_timeout_2400ms`、`camera_health:fetch_timeout_2400ms`、`camera_devices:fetch_timeout_2400ms`；
  optional `radar_raw_packet_proof_latest` 仍是 `status=missing/schema=not_loaded`，不再误算 mismatch。

## 剩余风险

- 本轮只修正 PC 诊断计数，不改变任何控制门禁、Nav2 执行条件、free-roam 双锁或建图 camera/radar readiness。
- 如果上位机未来返回非允许前缀但实际兼容的新 schema，仍需要显式加入允许列表或升级 schema 合同。
