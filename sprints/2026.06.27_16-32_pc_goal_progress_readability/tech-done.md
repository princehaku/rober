# PC goal progress readability

## Sprint Type

sprint_type: micro

## Actual Changes

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - Cleaned each fragment in the plain `本轮进度 -> 当前读数` summary before joining wheel, trip, delivery, and keyboard text.
  - This removes punctuation artifacts such as `。；送达未完成` while preserving the same facts and gates.
- `pc-tools/workstation/test/App.test.ts`
  - Added a regression assertion that stale Nav2 trip evidence summaries do not contain `。；`.
- `docs/product/pc_tools_workstation.md`
  - Documented the plain goal-progress readability contract and no-motion boundary.

## Verification

- `npm test -- --run test/App.test.ts -t "stale summary Nav2|delivery latest missing material|current wheel L/R"`: passed, 3 tests.
- `npm test -- --run`: passed, 2 files / 298 tests.
- `npm run build`: passed. Vite still reports the pre-existing chunk-size warning.
- `npm run lint`: passed.
- `git diff --check`: passed.
- 7001 live DOM smoke against `http://127.0.0.1:7001/?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`: passed.
  - Served bundle: `/assets/index-ZzLrkfJ4.js`.
  - `plain-goal-progress-evidence-summary` no longer contained `。；` or `；；`.
  - Checking only `plainTripSafetyConfirmed` did not issue base manual, Nav2 execute, free-roam start, or delivery complete requests.

## Remaining Risks

- This sprint only fixes PC plain-summary readability. It does not complete Nav2, keyboard validation, delivery success, camera first frame, or real free-roam mapping.
- Current live state still shows wheel raw L/R currently `0/0`, old Nav2 PWM route requiring ROS rerun, and camera first frame missing.
- The historical dirty JSON artifacts under `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/` were not touched or staged.
