# Final - O3 Scan QoS Endpoint Readback Split

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_19-56_o3_scan_qos_endpoint_readback_split/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Closeout time: `2026-07-12 20:24 CST`
- Product status: accepted as O3/O1 strict no-motion `/scan` blocker split / bounded Hardware handoff only
- Proof boundary: `software_proof_o3_o1_strict_no_motion_scan_qos_endpoint_readback_split_only`

## 用户价值和产品北极星

用户价值是继续把真实上位机 fixed-route/nav 链路推进到可验证 same-run path generation、route execution、delivery/operator acceptance 和 HIL/production evidence。产品北极星仍是普通手机用户一键发车送垃圾，并得到可验证结果。

本 sprint 不交付用户可见发车能力；它交付的是一个关键诊断变化：上一轮 primary `/scan_reliable_and_best_effort_timeout` 已被拆成 endpoint visible、QoS compatible / no samples、LiDAR runtime exception candidate 三层。下一步可以 bounded handoff 给 Hardware，但必须先读 vendor docs。

## OKR 映射和方向判断

- O5：继续约 85%，方向仍是暂停 support-only；本轮没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence。
- O1/O3：继续 strict no-motion 现场链路。本轮接受为 `/scan` blocker split / Hardware handoff boundary，不接受为 path、route、HIL、安全控制或 delivery progress。
- O6/O7：继续约 93%，方向仍是等待 live route execution、delivery/operator 或 production readback。
- OKR 结论：O5 继续约 85%，O1/O6/O7 继续约 93%，`不调整` 百分比，`不归档` KR。
- 方向判断：继续 O3/O1，但下一步 owner 变为 Hardware bounded diagnosis；Hardware 必须先读 `docs/vendor/VENDOR_INDEX.md` 和 vendor docs。

## KR 拆解、更新或历史归档

本轮不归档任何 KR。新增证据只进入 O3/O1 supporting evidence chain：

- Primary live artifact: `sprints/2026.07.12_19-56_o3_scan_qos_endpoint_readback_split/artifacts/live_o10_scan_qos_endpoint_readback_split.raw.json`
- `status=blocked_with_root_cause`
- `proof.artifact_closeout.primary_root_cause.reason=/scan_lidar_runtime_exception_after_endpoint_visible_qos_compatible_timeout`
- `proof.artifact_closeout.primary_root_cause.canonical_blocker=/scan_reliable_and_best_effort_timeout`
- `proof.artifact_closeout.primary_root_cause.split_classification=lidar_runtime_exception_candidate_after_endpoint_qos_readback_split`
- `proof.artifact_closeout.primary_root_cause.next_owner=hardware_after_vendor_doc_review`
- `proof.scan_qos_endpoint_readback_split.schema=trashbot.o10.scan_qos_endpoint_readback_split.v1`

历史归档位置不变：已归档 O3 仍在 `OKR.md` 的归档 Objective 区等待真实现场验证重新激活；详细历史留在 `docs/process/okr_progress_log.md`。本轮没有把任何 KR 移入历史区。

## 本轮核心抓手

Robot Software 把 18:56 的 generic `/scan_reliable_and_best_effort_timeout` 往下推进了一层：

- Endpoint layer: `/scan` publisher endpoint visible/stable；publisher node `lidar_driver`；topic type `sensor_msgs/msg/LaserScan`；publisher reliability `RELIABLE`；observed across 2 child attempts。
- QoS/readback layer: BEST_EFFORT and RELIABLE attempts both compatible and timed out；both `sample_count=0`；CLI fallbacks also timed out；`ros_readback_false_timeout_still_possible=true`。
- Runtime layer: managed runtime log observed `serial.serialutil.SerialException` with message hint `device reports readiness to read but returned no data`。
- Handoff layer: `hardware_handoff_allowed=true`、`hardware_handoff_requires_vendor_docs=true`、`does_not_claim_vendor_hardware_root_cause=true`。

Product 判断：这是 additive blocker split evidence，不是 mission progress。

## 实际改动和验证结果

Robot Software 已完成 helper/tests/navigation docs/artifacts 侧实现，Product 本轮 closeout 更新 sprint/OKR/process 留档。

Engineering 验证事实来自 `tech-done.md`：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` exit `0`。
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` PASS with `Ran 133 tests ... OK`。
- `bash -n onboard/scripts/o11_nav2_lifecycle.sh` exit `0`。
- local strict no-motion run return `2` fail-closed。
- true-board SSH/scp deploy and pull exit `0`。
- true-board strict no-motion helper return `remote_rc=2` with blocked artifact pulled。
- scoped `git diff --check` exit `0`。

No-motion fields remain false:

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `path_generation_attempted=false`
- `path_generated=false`

## Product Acceptance

Accepted as O3/O1 strict no-motion `/scan` blocker split / bounded Hardware handoff only。

Accepted because:

- 18:56 baseline is preserved: `map_server_active=true`、`amcl_active=true`、`managed_runtime_log_lifecycle_readback.clean=true`、`map_once_observed=true`。
- `/scan` endpoint is visible and stable, so this is no longer a no-publisher or graph-only blocker。
- BEST_EFFORT and RELIABLE readbacks are both QoS-compatible yet timed out with zero samples, and CLI fallbacks also timed out。
- Runtime exception evidence is concrete enough to route the next sprint to Hardware, while still explicitly not claiming a vendor-backed hardware root cause。
- strict no-motion invariants stayed fail-closed。

Rejected as mission progress because this is not path generation, route execution, delivery/operator acceptance, current live HIL, safe-to-control, current live map navigation readiness or production cloud/external evidence。

## 优先级和验收口径

Next run P0 owner: `rober-hardware-engineer` / Hardware Infra。

验收口径：

- Hardware must read `docs/vendor/VENDOR_INDEX.md` and linked vendor docs before any LiDAR serial/runtime/wiring conclusion。
- Diagnose LiDAR serial/runtime/wiring based on `/scan` endpoint visibility, QoS-compatible no-sample readback, CLI timeout, and `serial.serialutil.SerialException`。
- Keep strict no-motion: do not publish `/cmd_vel`, do not call `/api/base/manual`, do not send NavigateToPose, do not open WAVE ROVER UART。
- Do not claim hardware root cause until vendor-doc-backed evidence supports it。
- `Algorithm` waits until `/scan`, `/amcl_pose`, and dynamic `map->odom` are clean enough for planner-only path proof。

## 风险、阻塞和证据链缺口

- `ros_readback_false_timeout_still_possible=true`，所以 readback false timeout 仍是残余风险。
- Hardware handoff is allowed, but vendor-backed hardware root cause is not proven。
- `/amcl_pose` remains unobserved。
- Dynamic `map->odom` source is still missing。
- `path_generation_attempted=false` and `path_generated=false`。
- Still no same-run path generation success, `route.csv`, keyframe, rosbag, replay JSONL, route execution, delivery/operator acceptance, current live HIL, safe-to-control or production external evidence。

## 需要创建或更新的 Sprint 文档

Created or updated in closeout:

- `sprints/2026.07.12_19-56_o3_scan_qos_endpoint_readback_split/side2side_check.md`
- `sprints/2026.07.12_19-56_o3_scan_qos_endpoint_readback_split/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
