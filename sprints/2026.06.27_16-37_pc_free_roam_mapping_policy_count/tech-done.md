# PC free-roam mapping policy count

## Sprint Type

sprint_type: micro

## Actual Changes

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - Changed the plain free-roam readiness summary so `建图验收 x/y` uses `free_roam_autonomy_policy.mapping_required_gates` as the denominator.
  - Missing mapping gate rows, such as camera first frame and fresh map preview, are now evaluated from PC WYSIWYG facts instead of being omitted from the count.
  - This keeps the top summary aligned with the lower missing-gaps text, for example `建图验收 2/4 已满足` plus `缺口：画面首帧未出、地图记录未启动`.
- `pc-tools/workstation/test/App.test.ts`
  - Added regression assertions that loaded free-roam mapping readiness counts use `/4`, not the old `/3` mapping rows count.
- `docs/product/pc_free_roam_mapping_design.md`
  - Documented the mapping policy count contract.
- `docs/product/pc_tools_workstation.md`
  - Documented the plain UI behavior and no-motion boundary.

## Verification

- `npm test -- --run test/App.test.ts -t "starts ready free-roam autonomy even when radar proof is stale|shows start-ready free-roam autonomy as startable while runtime is still artifact-only"`: passed, 2 tests.
- `npm test -- --run`: passed, 2 files / 298 tests.
- `npm run build`: passed. Vite still reports the pre-existing chunk-size warning.
- `npm run lint`: passed.
- `git diff --check`: passed.
- 7001 live DOM smoke against `http://127.0.0.1:7001/?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`: passed.
  - Served bundle: `/assets/index-Czy1_dsQ.js`.
  - `plain-free-roam-autonomy-readiness` contained `建图验收 2/4 已满足`.
  - It did not contain the old `建图验收 1/3 已满足`.
  - Page load did not issue base manual, Nav2 execute, free-roam start, or delivery complete requests.

## Remaining Risks

- This sprint only corrects the PC readiness count. It does not start real free-roam motion or complete mapping.
- Current live mapping still lacks camera first frame and active map recording; the UI now reflects that as 2/4 mapping gates satisfied.
- The historical dirty JSON artifacts under `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/` were not touched or staged.
