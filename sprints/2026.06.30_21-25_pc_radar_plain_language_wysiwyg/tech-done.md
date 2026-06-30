# PC Radar Plain Language WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 新增雷达缺失观测中文映射，把 `scan_once/scan_hz/raw_packet_once` 转成普通用户可读的“没有读到一帧雷达、雷达频率未确认、雷达原始包未确认”。
  - `radar_status_plain`、`radar_next_action_plain` 和地图雷达贴图 next action 不再在普通文案里暴露底层字段。
- `pc-tools/workstation/src/server/index.ts`
  - 同步修正 `/api/robot-control/radar/status` 代理的地图雷达贴图 next action 文案。
- `pc-tools/workstation/test/catalog.test.ts`
  - 增加普通文案不包含 `raw_packet_once`、机器字段仍保留原始原因的回归断言。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 记录雷达普通文案中文化和机器字段保留边界。

## 验证结果

- `npm test -- catalog.test.ts`：通过，174 tests。
- `npm test -- robotControlSummary.test.ts`：通过，3 tests。
- `npm test -- App.test.ts`：通过，225 tests。
- `npm test -- --run`：通过，402 tests。
- `npm run lint`：通过，保留既有 4 个 Vue multiline warning，无 error。
- `npm run build`：通过，Vite 仍提示既有 chunk size warning。
- `git diff --check`：通过。
- 7001 只读 smoke：`/api/robot-control/summary` 和 `/api/robot-control/radar/status` 均确认普通文案 `raw_in_plain=false`，机器字段仍为 `scan_once,scan_hz,raw_packet_once`，`robot_control_executed=false`。

## 剩余风险

- 本轮只修 PC 只读文案和接口合同，没有发送 live motion/control POST。
- 真实雷达仍缺新扫描材料，地图雷达点贴图还需要上车端提供当前雷达点和同轮 map preview。
