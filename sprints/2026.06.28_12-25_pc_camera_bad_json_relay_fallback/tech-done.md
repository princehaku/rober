# 2026-06-28 12:25 PC camera bad JSON relay fallback

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 当 camera health 读取失败为 `fetch_failed/bad_json/not_object`，但共享 MJPEG relay 已明确
    `camera_source_first_frame_failed` 时，PC summary 将 camera `status` 归并为 `source_first_frame_failed`。
  - 归并后 `source_readiness` 继续同步为 `first_frame_failed`，避免 live 首屏同时出现 `bad_json` 和
    `uvc_no_frame_not_exclusive` 两套互相打架的事实。
  - 单纯坏 JSON 且没有 relay 无首帧证据时仍保持读取异常，不把未知状态包装成摄像头故障。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增 bad JSON health + relay no-frame diagnosis 用例，确认 endpoint 仍保留 `camera_health.request_status=bad_json`，
    但聚合 camera summary 面向 operator 显示 `source_first_frame_failed/first_frame_failed`。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录该 fallback 只消费已有共享 relay 事实，不新开相机上游、不发送控制命令、不改变建图 camera ready gate。

## 验证结果

- `npm test -- test/catalog.test.ts -t "Robot Control summary uses relay no-frame diagnosis when camera health returns bad JSON"`：通过，1 个用例通过、145 个跳过。
- `npm test`：通过，2 个 test file、333 个测试全部通过。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 仍提示单个 chunk 超过 500 kB，这是既有前端体积 warning，不影响本轮 camera summary fallback。
- `git diff --check`：通过。
- 重启本机 PC Node 到 `0.0.0.0:7001`：通过，`lsof` 显示 `node` 监听 `TCP *:7001`。
- 只读检查 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：通过，
  `robot_api_connection.status=readable`，camera `status=source_first_frame_failed`、
  `source_readiness=first_frame_failed`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、
  `source_diagnosis_not_exclusive=true`、`shared_preview_last_failure_reason=camera_source_first_frame_failed`。

## 剩余风险

- 当前 live 摄像头仍是 UVC 无首帧，需要现场检查 USB、摄像头输入或供电，必要时换 known-good UVC；本轮只修正 PC 所见即所得口径。
- 本轮不发送 manual、keyboard、free-roam、Nav2、delivery、stop 或 `/cmd_vel`，不证明建图 camera ready 或真实运动完成。
