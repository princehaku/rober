# PRD - O3 LiDAR Runtime Hardware Probe

## Summary

This sprint continues from `sprints/2026.07.12_19-56_o3_scan_qos_endpoint_readback_split/`. The latest accepted live artifact narrowed the O3/O1 strict no-motion `/scan` blocker to:

`/scan_lidar_runtime_exception_after_endpoint_visible_qos_compatible_timeout`

The endpoint is visible, QoS is compatible, both BEST_EFFORT and RELIABLE readbacks timed out with `sample_count=0`, and runtime logs observed `serial.serialutil.SerialException` with the message hint `device reports readiness to read but returned no data`. Product now routes P0 to `robot-hardware-engineer` after mandatory vendor-doc review.

## 用户价值和产品北极星

北极星：普通手机用户不懂 ROS2、不看 SSH、不调串口，也能让小车沿固定路线完成垃圾投递，并得到可验证的成功或失败结果。

本轮不做手机、云端、路线执行或底盘运动；本轮交付的是更接近现场修复的 LiDAR runtime 证据。LiDAR `/scan` 是 AMCL、dynamic `map->odom` 和 planner-only path proof 的前置输入，因此这轮必须把 runtime exception 候选变成可执行的配置/接线/串口修复建议，或至少产出比 19:56 更窄的 no-motion live artifact。

## Problem

19:56 artifact 已排除了两个旧层级：

1. 不是 `/scan` no-publisher：publisher endpoint visible/stable，publisher node 为 `lidar_driver`。
2. 不是简单 QoS 不兼容：BEST_EFFORT and RELIABLE attempts were compatible but timed out with zero samples。

剩余问题集中在 LiDAR runtime 层：

- `serial.serialutil.SerialException` 表明驱动看到串口 ready-to-read，却读不到数据。
- 既有材料中存在 `/dev/ttyACM0 @ 150000` 与 current helper defaults `230400` 的 baudrate drift。
- 需要确认 `/dev/ttyACM0` 是否为当前 LiDAR 设备、是否被占用、是否能产生 raw bytes、是否有 empty-read 计数、是否有 wiring/power/USB 枚举或 runtime startup 问题。
- 这些判断涉及硬件事实，必须以 `docs/vendor/VENDOR_INDEX.md` 及其指向资料为入口，不能凭记忆或旧代码默认值下结论。

## Scope

In scope for `robot-hardware-engineer`:

- 读取 `docs/vendor/VENDOR_INDEX.md`，并按任务需要打开其指向的本地 vendor 文件。
- 涉及 Orange Pi 串口、USB、电气或供电时，读取 `docs/vendor/orangepizero3/OrangePi_Zero3_H618_用户手册_v1.6.pdf` 与 `docs/vendor/orangepizero3/OrangePi-ZERO3_电路图.pdf`。
- 涉及 WAVE ROVER/base UART、ESP32、firmware 或 chassis UART 时，只读 `docs/vendor/waveshare_wave_rover/` 下 WAVE ROVER、`ugv_rpi` 与 firmware 文件；本轮不得打开或使用 WAVE ROVER UART。
- 检查 LiDAR-only runtime：`/dev/ttyACM0`、baudrate `150000` vs `230400` drift、`lidar_driver` diagnostics、raw bytes、empty-read counters、`serial.serialutil.SerialException`、`/scan` sample。
- 运行 no-motion LiDAR lifecycle/smoke 或 helper，只产出 artifact、logs、diagnostics 和下一步修复建议。
- 如果需要小范围 helper contract 支持，向 `robot-software-engineer` 请求 bounded support；Robot Software 不接管 Hardware 诊断。

Out of scope:

- O5 production/cloud support-only、readiness packet、handoff、review、status panel。
- UI/API、mobile、O6/O7 consumer surface。
- `/cmd_vel`、`/api/base/manual`、NavigateToPose、route execution、delivery command、HIL motion。
- WAVE ROVER UART open/write/read、`/dev/ttyS5` base UART、ESP32 command sending、firmware flashing。
- 在未读 vendor docs、未产出现场 readback 前，把 `150000` 或 `230400` 写成全局事实。
- 声明 mission progress、safe-to-control、delivery success、current live HIL pass 或 production external evidence。

## OKR Mapping And Direction Judgment

- O5 是当前最低 Objective，约 `85%`；本轮不做 O5，因为缺真实 external production evidence。继续 support-only 只会重复 `okr_credit_allowed=false`。
- O3/O1 strict no-motion 是本轮最高可执行抓手，因为 LiDAR `/scan` 直接阻塞 `/amcl_pose`、dynamic `map->odom`、same-run path generation、route execution、delivery/operator evidence 和 current live HIL。
- Direction: continue O3/O1, adjust owner to Hardware, pause O5 support-only, freeze independent O6/O7 surface.
- OKR percentage: default flat. Hardware diagnosis, wiring/config recommendation, or blocked artifact is supporting evidence only unless it produces clean same-run path generation, route execution, delivery/operator acceptance, current live HIL, or real production external evidence.

## Acceptance Criteria

P0 accepted outcome must satisfy all:

- `robot-hardware-engineer` explicitly records that `docs/vendor/VENDOR_INDEX.md` and required linked vendor docs were read before hardware conclusion.
- The resulting `tech-done.md` identifies one of:
  - clean `/scan` sample restored enough for Algorithm handoff;
  - vendor-doc-backed and no-motion-readback-backed config/baud/device/wiring correction candidate;
  - narrower fail-closed live artifact with exact next action and evidence gap.
- The diagnosis discusses `/dev/ttyACM0`, `150000` vs `230400`, `lidar_driver` diagnostics, raw bytes/empty-read evidence, and `serial.serialutil.SerialException`.
- strict no-motion is preserved: no `/cmd_vel`, no `/api/base/manual`, no NavigateToPose, no WAVE ROVER UART, no `/dev/ttyS5`.
- Artifact pull and scoped diff check are recorded.
- `Algorithm` handoff is allowed only if `/scan` is clean enough to retry `/amcl_pose` and dynamic `map->odom`.

Accepted blocked outcome:

- Hardware may close blocked only if the new artifact is narrower than `/scan_lidar_runtime_exception_after_endpoint_visible_qos_compatible_timeout` and states the exact next owner, command, or physical check.

Rejected outcomes:

- Repeating the 19:56 blocker phrase without new runtime, serial, baud, raw-byte, empty-read, or vendor-doc evidence.
- Claiming a vendor-backed hardware root cause without reading the required local vendor docs.
- Touching WAVE ROVER UART or any motion/control path.
- Returning to O5 support-only or a review/handoff/checklist-only sprint.
- Calling Algorithm before `/scan`, `/amcl_pose`, and dynamic `map->odom` are clean enough.

## KR 拆解、更新或历史归档

本 planning pass 不归档任何 KR。当前 KR 历史位置保持不变：

- 已完成或归档 Objective/KR 仍在 `OKR.md` 的历史/归档区和 `docs/process/okr_progress_log.md`。
- 本轮只允许新增 O3/O1 supporting evidence。
- O5 继续约 `85%`，O1/O6/O7 继续约 `93%`，除非 implementation 产生 stronger mission evidence。

## Risks And Evidence Gaps

- `ros_readback_false_timeout_still_possible=true` still means ROS readback false timeout remains a residual risk.
- `/dev/ttyACM0` may be the right device but wrong baud, wrong runtime start sequence, power/USB unstable, or occupied by another process.
- `150000` vs `230400` drift may come from historical smoke, current helper defaults, driver expectations, or hardware module variation; this sprint must not guess.
- `/amcl_pose` remains unobserved and dynamic `map->odom` remains missing until `/scan` samples are usable.
- No same-run path success, route execution, `route.csv`, keyframe, rosbag, replay JSONL, delivery/operator acceptance, current live HIL, safe-to-control, or production external evidence exists yet.
