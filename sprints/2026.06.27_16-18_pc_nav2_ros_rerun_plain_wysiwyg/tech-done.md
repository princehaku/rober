# PC Nav2 ROS rerun plain WYSIWYG

## Sprint Type

sprint_type: micro

## Actual Changes

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - Added a shared plain-trip execution action label that consumes live summary / safe boundary Nav2 facts.
  - When the previous route used `pwm`, the next run is `ros`, and wheel raw L/R is still `0/0`, the plain trip status, minimal precheck, and primary trip button now show `用 ROS 重跑图上路线`.
  - Kept the existing safety gate unchanged: checking the local safety box only unlocks the fixed backend action button and does not automatically send motion.
- `pc-tools/workstation/test/App.test.ts`
  - Added regression coverage for the live-shaped case where summary has `pending_ros_rerun_after_pwm` / `goal_succeeded_but_wheel_lr_zero`, but latest execution readback is empty.
  - Verified that checking the safety box alone does not call Nav2 execute, base manual, or `/cmd_vel`.
- `docs/product/pc_tools_workstation.md`
  - Documented the plain user Nav2 ROS-rerun display contract.
- `docs/product/pc_free_roam_mapping_design.md`
  - Documented that stale `goal_succeeded` records must still surface the summary-requested ROS rerun when wheel L/R is zero.

## Verification

- `npm test -- --run test/App.test.ts -t "summary-requested ROS rerun|refreshes Robot Control summary after plain Nav2 execution latest is loaded|draws no-motion route markers"`: passed, 3 tests.
- `npm test -- --run`: passed, 2 files / 298 tests.
- `npm run build`: passed. Vite still reports the pre-existing chunk-size warning.
- `git diff --check`: passed.
- 7001 live DOM smoke against `http://127.0.0.1:7001/?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`: passed.
  - Served bundle: `/assets/index-DLvIE-Xd.js`.
  - After checking only `plainTripSafetyConfirmed`, `plain-trip-execute` showed `用 ROS 重跑图上路线`.
  - `plain-trip-minimal-precheck` showed `行程前确认：安全确认已完成；可以用 ROS 重跑图上路线，执行接口只复核安全确认和固定白名单。`
  - `plain-trip-run-status` showed `行程状态：读到旧行程成功记录；下一步用 ROS 重跑图上路线。`
  - Observed motion request list was empty: no Nav2 execute, no base manual, no stop, no free-roam start.

## Remaining Risks

- This sprint only fixes PC plain-user WYSIWYG for the already reported Nav2 rerun state. It did not physically execute the ROS rerun.
- Complete route success still requires a real execution window with wheel raw L/R nonzero proof; IMU-only motion remains insufficient.
- The two historical dirty JSON artifacts under `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/` were not touched or staged.
