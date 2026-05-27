# O7 RTC Signaling Contract Probe Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/o7RtcSignalingContractProbe.ts` 新增 PC 端只读 HTTP contract probe：只允许本机 HTTP 回环 base URL，固定拉取 `/api/o7/rtc-signaling/contract`，校验 `trashbot.o7.rtc_signaling_contract.v1`，扫描 RTC/WebRTC/media/ROS2/control 相关危险 true 字段并 fail closed。
- `pc-tools/workstation/src/server/catalog.ts`、`pc-tools/workstation/src/server/index.ts`、`pc-tools/workstation/src/client/workstationApi.ts`、`pc-tools/workstation/src/shared/contracts.ts` 接入新 API、共享响应契约和 health route catalog。
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue` 新增 “RTC signaling contract probe” 手动面板；页面不自动 probe，不提供 bearer/token、connect/start/video/send 控件，只展示 remote schema、contract status、核心 false fields、protocol surface keys、required evidence refs、blocked/not_proven 和 dangerous true fields。
- `pc-tools/workstation/src/server/o7PreviewsAcceptance.ts` 补齐 `rtc_signaling_contract_probe` acceptance surface，纳入 `GET /api/o7/previews/acceptance` 的 `covered_surface_ids` / `surfaces`，并在 `remaining_real_capability_gaps` 明确 contract probe 不证明真实 RTC/video/media transport。
- `pc-tools/workstation/test/catalog.test.ts` 新增 loopback/schema/dangerous true 字段测试；`pc-tools/workstation/test/App.test.ts` 新增 UI 入口、手动触发、client URL 和脱敏摘要断言。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`、`docs/interfaces/o7_rtc_signaling_contract_probe_api.md` 同步 PC probe 的接口、UI 边界和未证明事项。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`、`pc-tools/README.md`、`docs/product/pc_tools_workstation.md` 继续同步 acceptance guard 覆盖新 surface 的验收口径。

## 验证结果

- `cd pc-tools/workstation && npm run build`
  - 结果：通过。`vite v7.3.3 building client environment for production...`，`✓ 31 modules transformed.`，`✓ built in 2.25s`，退出码 0。
  - acceptance guard 补丁后复跑：通过。`✓ 31 modules transformed.`，`✓ built in 2.34s`，退出码 0。
- `cd pc-tools/workstation && npm run test`
  - 首轮失败：`test/App.test.ts > loads O7 fixture previews through PC-only read-only API clients` 中新增 baseUrl 输入导致 archive path 下标偏移，测试把 `operator-soft` 留在本地 TTS draft。
  - 修复：将测试里后续 archive path 输入下标从 `inputs[3]` 调整为 `inputs[4]`。
  - 复跑结果：通过。`Test Files  2 passed (2)`，`Tests  40 passed (40)`，退出码 0。
  - acceptance guard 补丁首轮失败：App 测试错误断言 UI 会展示每个 surface 的 `source_endpoint`，但当前 Covered surfaces 只展示 id/boundary/status；`source_endpoint` 和详细 blocked/not_proven 已由 catalog 测试覆盖。
  - 修复：App 测试改为断言 UI 实际展示的 `rtc_signaling_contract_probe` surface id 和 remaining gap；catalog 测试继续断言 endpoint、blocked/not_proven 明细。
  - acceptance guard 补丁复跑：通过。`Test Files  2 passed (2)`，`Tests  40 passed (40)`，退出码 0。
- `cd pc-tools/workstation && npm run lint`
  - 结果：通过，退出码 0。
  - acceptance guard 补丁后复跑：通过，退出码 0。
- `git diff --check -- pc-tools/workstation/src/server/o7RtcSignalingContractProbe.ts pc-tools/workstation/src/server/catalog.ts pc-tools/workstation/src/server/index.ts pc-tools/workstation/src/client/workstationApi.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/App.test.ts pc-tools/workstation/test/catalog.test.ts pc-tools/README.md docs/product/pc_tools_workstation.md docs/interfaces/o7_rtc_signaling_contract_probe_api.md sprints/2026.05.27_42-43_o7-rtc-signaling-contract-probe/tech-done.md`
  - 结果：通过，退出码 0。
- `git diff --check -- pc-tools/workstation/src/server/o7RtcSignalingContractProbe.ts pc-tools/workstation/src/server/catalog.ts pc-tools/workstation/src/server/index.ts pc-tools/workstation/src/client/workstationApi.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/src/server/o7PreviewsAcceptance.ts pc-tools/workstation/test/App.test.ts pc-tools/workstation/test/catalog.test.ts pc-tools/README.md docs/product/pc_tools_workstation.md docs/interfaces/o7_rtc_signaling_contract_probe_api.md sprints/2026.05.27_42-43_o7-rtc-signaling-contract-probe/tech-done.md`
  - acceptance guard 补丁后复跑：通过，退出码 0。

## 剩余风险

- 当前只证明 PC 能从本机回环 relay 读取 fail-closed RTC signaling/media 合同；没有证明真实 WebRTC signaling session、offer/answer、ICE、video track、media transport、实时 pose stream、ROS2 `/tf` bridge、机器人 ACK、HIL 或硬件安全。
- 本轮未改 robot/relay 侧实现；依赖上一轮 `GET /api/o7/rtc-signaling/contract` 静态合同。
