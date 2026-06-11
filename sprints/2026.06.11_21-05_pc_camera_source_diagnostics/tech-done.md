# PC Camera Source Diagnostics

## sprint_type

micro

## 背景

真实上位机 camera service 已能正确 auto 选择 `/dev/video1`，但 WebRTC offer 仍返回
`first_frame_timeout`。本轮把这些关键信息接入 PC workstation 的 Robot Control
summary 和默认关闭的高级诊断，避免 operator 必须 SSH 才能看见 camera 选源和首帧失败。

普通用户首屏不变，仍只显示“打开画面/关闭画面”和短状态。

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 新增 camera summary 压缩字段：
    - `video_source`
    - `video_source_mode`
    - `selected_path`
    - `active_peer_count`
    - `last_offer_error`
    - `last_offer_failure_reason`
  - 字段只来自固定只读 endpoint `/api/camera/health` 和 `/api/camera/devices`。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 扩展 `RobotControlSummaryResponse.readback_summary.camera` 合同。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 在默认关闭的 `高级诊断 -> 实时画面详情` 展示 camera source 和 last offer 错误。
  - 没有修改 `.simple-user-console` 普通首屏。
- `pc-tools/workstation/test/App.test.ts`
  - 补齐默认 fixture 的 camera summary 字段。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 `/dev/video1`、`auto`、`active_peer_count=0`、`first_frame_unreadable`、
    `first_frame_timeout` 的 summary 聚合。

## 验证结果

本地验证：

```bash
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run build
git diff --check
```

结果：

- `npm run test`：2 files / 92 tests passed。
- `npm run build`：通过。
- `git diff --check`：通过。

真实 PC proxy 只读 smoke：

```bash
PORT=18806 npm run api
curl 'http://127.0.0.1:18806/api/robot-control/summary?baseUrl=http://192.168.1.11:8787'
```

核心 readback：

```json
{
  "status": "ready",
  "devices_status": "loaded",
  "preview_status": "idle_not_started",
  "video_source": "/dev/video1",
  "video_source_mode": "auto",
  "selected_path": "/dev/video1",
  "active_peer_count": "0",
  "last_offer_error": "first_frame_unreadable",
  "last_offer_failure_reason": "first_frame_timeout"
}
```

证据：

- `artifacts/01_workstation_api.log`
- `artifacts/02_real_board_summary.json`

## 剩余风险

- PC 现在能显示相机选源和首帧失败，但没有恢复真实可见图传。
- `/dev/video1` 仍需现场检查 DV20 输入源、线缆、供电、采集卡状态，或换 known-good UVC。
- 非 stop 运动 gate 仍缺 `visible_content_proven=true`、外部视频、轮速非零和 LiDAR motion delta。
