# Side2Side Check - O3 Scan QoS Endpoint Readback Split

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_19-56_o3_scan_qos_endpoint_readback_split/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Product status: accepted as O3/O1 strict no-motion `/scan` blocker split / bounded Hardware handoff only
- Proof boundary: `software_proof_o3_o1_strict_no_motion_scan_qos_endpoint_readback_split_only`

## 用户价值和产品北极星

产品北极星仍是普通手机用户一键发车送垃圾，并得到可验证的成功或失败结果。本 sprint 不交付用户可见发车能力，也不交付路线执行；它交付的是 fixed-route delivery 前置定位链路的下一层事实：`/scan` 已从泛化 sample timeout 被拆成 endpoint、QoS/readback 与 LiDAR runtime 三层。

本轮用户价值是把下一步从继续反复包装 `/scan_reliable_and_best_effort_timeout`，推进为有边界的 Hardware 诊断入口。只有 LiDAR runtime/serial/wiring 被 vendor-doc-backed 地诊断清楚，后续才可能恢复 `/amcl_pose`、dynamic `map->odom`、planner-only path proof、route execution 和 delivery/operator evidence。

## Acceptance Side-by-side

| Gate | PRD / tech-plan expectation | Product check |
| --- | --- | --- |
| 18:56 baseline preserved | 保持 `map_server_active=true`、`amcl_active=true`、`managed_runtime_log_lifecycle_readback.clean=true` | Accepted: live artifact 继续显示 `map_server_active=true`、`amcl_active=true`、`managed_runtime_log_lifecycle_readback.clean=true`，且 `map_once_observed=true`。 |
| `/scan` blocker split | 把 `/scan_reliable_and_best_effort_timeout` 拆成 endpoint、QoS/window/ROS readback、LiDAR runtime | Accepted: `proof.scan_qos_endpoint_readback_split.schema=trashbot.o10.scan_qos_endpoint_readback_split.v1`，primary reason 为 `/scan_lidar_runtime_exception_after_endpoint_visible_qos_compatible_timeout`。 |
| Endpoint layer | 证明 publisher endpoint 是否存在且稳定 | Accepted: `/scan` publisher endpoint visible/stable，publisher node `lidar_driver`，topic type `sensor_msgs/msg/LaserScan`，publisher reliability `RELIABLE`，observed across 2 child attempts。 |
| QoS/readback layer | BEST_EFFORT / RELIABLE readback 分层，避免误把 QoS 当硬件根因 | Accepted: BEST_EFFORT 与 RELIABLE 均 compatible 且均 timed out，两个 child attempts `sample_count=0`，CLI fallbacks 也 timed out；`ros_readback_false_timeout_still_possible=true` 保留边界。 |
| Runtime layer | 只有 endpoint/readback 分清后才允许 Hardware handoff | Accepted: runtime split 观察到 `serial.serialutil.SerialException`，message hint 为 `device reports readiness to read but returned no data`；`hardware_handoff_allowed=true`、`hardware_handoff_requires_vendor_docs=true`、`does_not_claim_vendor_hardware_root_cause=true`。 |
| Strict no-motion | 不发运动、不安全控制、不路线执行 | Accepted: `safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`。 |
| Mission evidence | 只有 same-run path/route/delivery/HIL/production 才计主进度 | Rejected as mission progress: `path_generation_attempted=false`、`path_generated=false`、`amcl_pose_observed=false`，TF 仍是 `map_to_odom_dynamic_source_missing`。 |

## OKR 映射和方向判断

- O5 继续约 85%，本轮没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence。
- O1/O6/O7 继续约 93%，本轮没有 current live HIL、safe-to-control、same-run path generation success、Nav2 route execution success、delivery record、operator acceptance 或 production readback。
- 方向判断：继续 O3/O1 strict no-motion lane，但下一 owner 从 Robot Software split 转为 Hardware bounded diagnosis。
- Product 决策：`不调整` 百分比，`不归档` KR。

## Product Acceptance

Accepted as O3/O1 strict no-motion `/scan` blocker split / bounded Hardware handoff only.

Product 接受原因：

- Primary blocker 比 18:56 的 `/scan_reliable_and_best_effort_timeout` 更窄。
- Endpoint 已可见且稳定，QoS 兼容性已读回，BEST_EFFORT / RELIABLE / CLI readback 都没有样本。
- LiDAR runtime exception 给出了下一步可执行诊断入口，但 artifact 明确不声称 vendor-backed hardware root cause。
- no-motion safety booleans 全部 fail-closed。

Product 不接受为：

- mission progress。
- path generation。
- route execution。
- delivery/operator acceptance。
- current live HIL。
- safe-to-control。
- production external evidence。
- vendor-backed hardware root cause。

## Next Owner And Acceptance

Next owner: `rober-hardware-engineer` / Hardware Infra, only after reading `docs/vendor/VENDOR_INDEX.md` and the linked vendor docs.

Next task acceptance:

- Diagnose LiDAR serial/runtime/wiring based on the endpoint/QoS facts and `serial.serialutil.SerialException`。
- Keep strict no-motion: no `/cmd_vel`、no `/api/base/manual`、no NavigateToPose、no WAVE ROVER UART。
- Do not change serial/UART/baudrate/wiring assumptions or claim hardware root cause without vendor-doc-backed evidence。
- Algorithm waits until `/scan` samples, `/amcl_pose`, and dynamic `map->odom` are clean enough for planner-only path proof。

## Validation Readback

Engineering validation accepted from `tech-done.md`:

- `py_compile` exit `0`。
- unittest `Ran 133 tests ... OK`。
- `bash -n` exit `0`。
- local strict no-motion exit `2` fail-closed。
- true-board SSH/scp exit `0`。
- true-board helper `remote_rc=2` with blocked artifact pulled。
- scoped `git diff --check` exit `0`。

Product closeout still requires the final rg/diff check over `side2side_check.md`、`final.md`、`OKR.md` and `docs/process/okr_progress_log.md`。
