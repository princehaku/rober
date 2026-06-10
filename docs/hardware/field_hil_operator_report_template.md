# Field HIL Operator Report Template

本文是现场 HIL 人工材料提交模板。目标是把现场人员观察、外部视频、相机可见性、
wheel feedback、scan delta、route/map 和 delivery 布尔值提交到现有
`/api/operator/report`，并明确该 report 只是人工材料入口。

## 资料来源与边界

本模板采用以下本地资料，不新增硬件参数或运动指令假设：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/hardware/field_hil_execution_pack.md`
- `onboard/scripts/upper_robot_api.py`

WAVE ROVER 事实仍以 vendor 文件为准：上下位机链路是 UART，一行 UTF-8 JSON 以
`\n` 结束；vendor Raspberry Pi 示例是 `/dev/ttyAMA0 @ 115200`，当前 Orange Pi
实板证据是 `/dev/ttyS5 @ 115200`；`json_cmd.h` 定义 `CMD_SPEED_CTRL=1`、
`CMD_ROS_CTRL=13`、`CMD_BASE_FEEDBACK=130`、`CMD_BASE_FEEDBACK_FLOW=131`、
`CMD_FEEDBACK_FLOW_INTERVAL=142`、`CMD_UART_ECHO_MODE=143` 和
`FEEDBACK_BASE_INFO=1001`。

`/api/operator/report` 的边界：

- `operator_report_material_only=true`：只收人工材料，不触发 ROS2、串口或运动。
- `operator_report` 不能替代 `/trashbot/stop`、`/api/base/stop`、robot ACK、`T=1001`
  feedback、HIL pass、外部视频、scan delta、route/map 或 delivery proof。
- `operator_report` 可以辅助解释现场观察，但不能单独把
  `visible_content_proven`、`physical_motion_lidar_delta_proven`、
  `wheel_feedback_lr_nonzero_proven` 或 `delivery_success` 翻为 true。
- 当前 API normalizer 会把细分 HIL 材料持久化到 `structured_hil_claims`，并在
  POST/GET 回包中回显；这些字段仍然只是人工材料 claim，不会把 `hil_pass`、
  `delivery_success` 或 `safe_to_control` 翻为 true。

## 现场填写项

每轮现场 HIL 使用一个唯一 `evidence_ref`，建议格式：
`field-hil-YYYYMMDD-HHMM-operator-initials`。

必须填写的核心字段：

- `operator_present`：现场 operator 是否在场。
- `physical_clearance_confirmed`：安全空间、线缆、车体落地/架空和人员站位是否已确认。
- `emergency_stop_ready`：物理急停、断电或等价停止路径是否在手边。
- `observed_motion`：operator 是否观察到轮子或车体真实运动。
- `observed_stop`：operator 是否观察到 stop 后车体停止。
- `reported_at`：现场本地时间，使用 ISO-8601 或带时区的文本。
- `operator_notes`：必须包含外部视频、相机、wheel feedback、scan delta、
  route/map、delivery 和异常说明。

提交 payload 必须包含以下结构化材料字段。字段可放在顶层，也可放在
`structured_hil_claims` 对象中；顶层字段优先，API 会统一回写到
`structured_hil_claims`：

- `external_video_recorded`：是否有连续外部视频，且能看到轮子、地面参考物和 stop。
- `external_video_ref`：视频文件名、OSS key、本地 artifact 路径或现场手机编号。
- `visible_content_proven`：相机是否已从黑场变成可见内容。
- `camera_artifacts_ref`：OpenCV/ROS frame、metrics JSON、设备 facts 的引用。
- `wheel_feedback_lr_nonzero_proven`：同一 motion/post 时间窗内 `T=1001` 是否有非零
  left/right wheel feedback。
- `wheel_feedback_ref`：原始 `T=1001` JSONL 路径或片段引用。
- `physical_motion_lidar_delta_proven`：scan delta 是否满足 execution pack 阈值。
- `scan_delta_ref`：baseline/post scan metrics 和 delta JSON 的引用。
- `real_route_map_proven`：route/map/keyframes/manifest 是否来自同一轮真实移动。
- `route_map_ref`：`route.csv`、keyframes、manifest、`map.yaml/.pgm` 的引用。
- `delivery_success`：真实送达是否完成；没有出发、到达、投放/提醒、停止或返回闭环时必须为 false。
- `operator_report_material_only`：API 回包固定为 true，提醒下游不要把 report 当 proof。

## JSON payload 示例

把以下 JSON 保存为临时文件，例如 `/tmp/field_hil_operator_report_payload.json`，
按现场事实改值后提交。不要把临时文件留在仓库。

```json
{
  "operator_present": true,
  "evidence_ref": "field-hil-20260610-0445-ab",
  "physical_clearance_confirmed": true,
  "emergency_stop_ready": true,
  "observed_motion": false,
  "observed_stop": true,
  "reported_at": "2026-06-10T04:45:00+08:00",
  "operator_notes": "No HIL or motion proof is claimed by this report alone.",
  "external_video_recorded": false,
  "external_video_ref": null,
  "visible_content_proven": false,
  "camera_artifacts_ref": "runtime/camera_visibility/latest_metrics.json",
  "wheel_feedback_lr_nonzero_proven": false,
  "wheel_feedback_ref": "runtime/wave_rover_feedback_debug.jsonl",
  "physical_motion_lidar_delta_proven": false,
  "scan_delta_ref": "runtime/scan_delta/latest_metrics.json",
  "real_route_map_proven": false,
  "route_map_ref": null,
  "delivery_success": false,
  "site_state": "bench_or_floor_status_to_fill"
}
```

也可以把细分字段放到 nested claim 对象，便于 PC/上位机稳定消费：

```json
{
  "operator_present": true,
  "evidence_ref": "field-hil-20260610-0445-ab",
  "physical_clearance_confirmed": true,
  "emergency_stop_ready": true,
  "observed_motion": false,
  "observed_stop": true,
  "reported_at": "2026-06-10T04:45:00+08:00",
  "operator_notes": "Nested structured_hil_claims is material only.",
  "structured_hil_claims": {
    "external_video_recorded": false,
    "external_video_ref": null,
    "visible_content_proven": false,
    "camera_artifacts_ref": "runtime/camera_visibility/latest_metrics.json",
    "wheel_feedback_lr_nonzero_proven": false,
    "wheel_feedback_ref": "runtime/wave_rover_feedback_debug.jsonl",
    "physical_motion_lidar_delta_proven": false,
    "scan_delta_ref": "runtime/scan_delta/latest_metrics.json",
    "real_route_map_proven": false,
    "route_map_ref": null,
    "delivery_success": false,
    "site_state": "bench_or_floor_status_to_fill"
  }
}
```

## 提交命令

在上位机本机或 SSH shell 中，只提交人工材料，不发送任何运动命令：

```bash
python3 -m json.tool /tmp/field_hil_operator_report_payload.json
curl -sS -X POST http://127.0.0.1:8787/api/operator/report \
  -H 'Content-Type: application/json' \
  --data-binary @/tmp/field_hil_operator_report_payload.json | python3 -m json.tool
curl -sS http://127.0.0.1:8787/api/operator/report | python3 -m json.tool
```

预期回包必须包含：

- `endpoint="/api/operator/report"`
- `operator_report_material_only=true`
- `operator_report_status` 为 `ready_for_execution`、`ready_for_review` 或
  `unsafe_or_incomplete`
- `does_not_replace` 包含 `/api/base/stop`、`T=1001`、robot ACK、HIL 和现场视频/记录
- `sends_motion_commands=false`
- `opens_serial=false`
- `hil_pass=false`
- `delivery_success=false`
- `structured_hil_claims` 回显提交的细分材料字段；即使
  `structured_hil_claims.delivery_success=true`，顶层 `delivery_success` 也必须保持
  false。

若回包缺少以上 fail-closed 字段，不得把本 report 纳入 HIL 证据。

## 证据升级规则

`structured_hil_claims` 中的布尔值只代表人工材料声明。证据升级必须按
`docs/hardware/field_hil_execution_pack.md` 的成功判据执行：

- `visible_content_proven=true` 需要原始图片、metrics 和设备 facts。
- `physical_motion_lidar_delta_proven=true` 需要健康 baseline/post `/scan` 与 delta 阈值通过。
- `wheel_feedback_lr_nonzero_proven=true` 需要同一时间窗的 `T=1001` wheel feedback 非零。
- `real_route_map_proven=true` 需要同一轮真实移动的 route、keyframes、manifest 和 map。
- `delivery_success=true` 需要真实路线导航或人工辅助送达闭环，且 stop、任务日志和外部视频可对齐。

缺少任一原始 artifact 时，最终 review 必须保持对应布尔值 false 或 boundary。
