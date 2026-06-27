# PC free-roam gate loaded WYSIWYG

## Sprint Type

sprint_type: micro

## Actual Changes

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - Changed the plain free-roam readiness policy text from a generic loading phrase to a structured gate summary when `free_roam_autonomy_gates[]` is already present.
  - The plain UI now shows `已读到上车端自由移动门禁` plus start/mapping gate counts such as `启动条件 1/2 已满足；建图验收 1/3 已满足`.
  - This only changes displayed readiness text; it does not alter the start gate, stop gate, mapping acceptance logic, or any motion proxy.
- `pc-tools/workstation/test/App.test.ts`
  - Added regression assertions so live-shaped free-roam gates no longer render `正在读取上车端自由移动门禁`.
- `docs/product/pc_free_roam_mapping_design.md`
  - Documented the gate-loaded policy text contract.
- `docs/product/pc_tools_workstation.md`
  - Documented the PC plain UI behavior and no-motion boundary.

## Verification

- `npm test -- --run test/App.test.ts -t "starts ready free-roam autonomy even when radar proof is stale|keeps trip controls safety-gated while running lidar proof only asks for refresh|shows start-ready free-roam autonomy"`: passed, 3 tests.
- `npm test -- --run`: passed, 2 files / 298 tests.
- `npm run build`: passed. Vite still reports the pre-existing chunk-size warning.
- `npm run lint`: passed.
- `git diff --check`: passed.
- 7001 live DOM smoke against `http://127.0.0.1:7001/?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`: passed.
  - Served bundle: `/assets/index-BHe-BMKD.js`.
  - `plain-free-roam-autonomy-readiness` contained `已读到上车端自由移动门禁`.
  - The same block did not contain `正在读取上车端自由移动门禁`.
  - The page load did not issue free-roam start, base manual, Nav2 execute, or delivery complete requests.

## Remaining Risks

- This sprint only fixes the PC WYSIWYG readiness text. It did not start real free-roam motion or create a new map.
- Current live camera still lacks a first frame, so mapping remains not acceptable even though free movement can be requested after safety confirmation.
- The historical dirty JSON artifacts under `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/` were not touched or staged.
