# Camera Shared Preview UVC Siblings Micro Sprint

## sprint_type

micro

## 实际改动

- 上车端 `local_webrtc_camera_smoke.py` 在 `/health` 与 `source_summary` 中新增共享预览合同 `single_shared_capture_for_multiple_clients`。
- 上车端新增 `selected_role`、`selected_sibling_video_nodes_summary`、`selected_sibling_video_node_count`，用于说明 DV20 这类 UVC 复合设备中 `/dev/video1` 是 `video_capture`、`/dev/video2=metadata` 只是同设备兄弟节点，不是备用画面源。
- PC `robotControlSummary.ts`、共享契约类型、普通控制台高级诊断同步消费这些短字段；首屏仍保持简易文案，不增加工程字段负担。
- 更新 `docs/product/pc_tools_workstation.md`，记录共享预览多人观看和 UVC sibling 诊断边界。

## 验证结果

- `ssh root@192.168.1.11 -p 37878` 只读探测：上位机可连接；`/dev/video1` 是 DV20 UVC `Video Capture`，`/dev/video2` 是 `Metadata Capture`；`fuser` 未发现其它 owner，当前无帧不是浏览器独占证据。
- `python -m unittest onboard.tests.test_local_webrtc_camera_smoke`：26 tests passed。
- `npm test -- --run test/catalog.test.ts`：130 tests passed。
- `npm test -- --run test/App.test.ts`：177 tests passed。
- `npm test -- --run`：307 tests passed。
- `npm run build`：通过；仅保留既有 Vite chunk >500 kB warning。
- `npm run lint`：通过。
- `git diff --check`：通过。

## 剩余风险

- 代码已能把“不是独占 / video2 是 metadata / 共享预览多人观看”说清楚，但真实 DV20 `/dev/video1` 仍未读到首帧；这更像 USB/摄像头输入/供电/设备本身或 OpenCV/V4L2 读帧问题，需要现场换 known-good UVC 或物理检查后再验证实时画面。
- 本轮未触发 manual、keyboard、free-roam、Nav2、delivery、stop 或 `/cmd_vel`，因此不改变小车运动状态。
