# Tech Done: O10 AMCL/Nav2 Readiness Epic

## sprint_type

sprint_type: epic

## 实际改动

本轮按 O10 受控送达 readiness chain 推进四段材料：

| Owner | 状态 | 实际改动 |
| --- | --- | --- |
| Robot Software Engineer | Partial pass | `GET /api/nav2/status` 新增 `amcl_nav2_readiness` 输入护栏，从 canonical `/root/rober/onboard/runtime/map_lifecycle_latest.json` 和 `/root/rober/onboard/runtime/maps` 只读折算 Nav2 输入状态；更新 `docs/navigation/nav2_map_quality_metrics.md` 和 API 回归测试。 |
| Full-stack Software Engineer | Pass | PC 端新增 `Read scan latest`、`Read map proof latest` 按钮和 browser workflow collector；生成 `pc-tools/workstation/.workstation-runtime/o7-direct-upper-browser-workflow.json` 与 `.png`，覆盖 refresh scan proof、read scan latest、read map proof latest、localize reset。 |
| Robot Algorithm Engineer | Blocked with root cause | 新增 `pc-tools/evidence/fixtures/elevator_o10_image_eval_decision_gate/blocked_missing_real_or_controlled_manifest.json`，更新 `docs/vision/elevator_opencv_baseline.md`，明确缺真实/受控电梯图片 manifest，不能跑 field eval。 |
| Hardware Infra Engineer | Blocked with root cause | 更新 `docs/hardware/o1_pc_manual_lidar_hil_boundary.md`，补 stop-first HIL CEO blocker 模板；已读 vendor source，确认无现场看护/净空/急停/授权时禁止运动。 |

## 验证结果

Robot Software：

- `python3 -m compileall -q onboard/scripts onboard/src`：通过。
- `python3 -m unittest discover -s onboard/scripts -p 'test_*.py'`：Ran 86 tests，OK，skipped=3。
- `python3 -m unittest discover -s onboard/src -p 'test_*.py'`：Ran 0 tests，exit 5；根因是 repo 顶层 discovery 不进入包级 `test/` 目录。
- 替代包级验证通过：nav 54、bringup 12、hardware 68、interfaces 6、vision 20、behavior 843 tests OK。

Full-stack：

- `cd pc-tools/workstation && TMPDIR=/tmp npm test`：3 files / 103 tests passed。
- `cd pc-tools/workstation && TMPDIR=/tmp npm run build`：通过。
- 8788 API 启动成功并完成 status / scan latest / map latest curl。
- `npm run o7:direct-upper-workflow`：`status=ok`，页面非空，无 console error，截图和 JSON 已落盘。

Algorithm：

- `python3 -m compileall -q onboard/scripts onboard/src`：通过。
- `python3 -m unittest onboard/src/ros2_trashbot_vision/test/test_elevator_opencv_baseline.py`：7 tests OK。
- `python3 -m unittest discover -s onboard/src/ros2_trashbot_vision/test -p 'test_*.py'`：20 tests OK。
- manifest template checker 输出 `blocked_missing_real_or_controlled_images`，`field_eval_ready=false`。

Hardware：

- `sed -n '1,220p' docs/vendor/VENDOR_INDEX.md`：已确认 vendor 入口。
- `python3 -m compileall -q onboard/scripts onboard/src`：通过。
- `python3 -m unittest onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py`：18 tests OK。
- 未执行 SSH、`/api/base/manual`、`T=1/T=11/T=13` 或 ROS `/cmd_vel`。

## 证据边界

- `browser_workflow_button_level`：PC 浏览器按钮级 proof 成立，但不证明 PC WASD、HIL、AMCL/Nav2 consumption 或 delivery success。
- `software_guard`：Nav2 readiness 只证明输入护栏，不证明 map quality pass、AMCL 定位、planner/controller lifecycle 或路径生成。
- `blocked_with_root_cause`：电梯图片 eval blocked 于缺真实/受控 manifest；HIL blocked 于 `missing_same-session_site_safety_authorization`。

## 剩余风险

- AMCL/Nav2 runtime collector 仍未跑；O3 不涨。
- 电梯真实/受控图片 manifest 缺失；O2 不涨。
- stop-first HIL 缺现场安全授权；O1 不涨，`safe_to_control=false` 保持。
- 本轮没有真实送达、真实跨楼层、PC WASD、HIL、robot ACK、`T=1001` 同场材料或 production cloud。
