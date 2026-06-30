# PC Camera Overlay Current Gate Micro Sprint

sprint_type: micro

## 实际改动

- 修正 `pc-tools/workstation/src/server/robotControlSummary.ts` 的相机首帧判定：当 `/api/camera/health` 在 summary 预算内超时或未加载时，MJPEG relay overlay 里残留的 `source_diagnosis_status=first_frame_observed` 不再被当作当前首帧证明。
- `camera_preview` action card 的 `camera_source_first_frame_ready` 只接受当前 `source_readiness=first_frame_observed`、当前可见帧或只读首帧 probe 成功，不再单独信任正向 `source_diagnosis_status`。
- 新增 catalog 回归测试，覆盖 camera health 超时但 overlay 残留“首帧已读到”的现场形态，要求 summary 不再显示“首帧已读到”，建图 gate 继续缺 `camera_first_frame`。
- 同步更新 `pc-tools/README.md` 和 `docs/product/pc_tools_workstation.md`，记录当前证据优先的相机首帧 gate 口径。

## 验证结果

- `npm test -- --run test/catalog.test.ts -t "stale positive camera overlay|camera no-frame diagnosis|relay first-frame total timeout"`：通过，1 个测试文件，3 个用例通过。
- `npm test -- --run`：通过，2 个测试文件，390 个用例通过。
- `npm run lint`：通过，0 error；保留既有 4 个 Vue 换行 warning。
- `npm run build`：通过，Vite 仍提示单 chunk 超过 500 kB 的既有体积 warning。
- `git diff --check`：通过。
- 已重启 PC Node 到 `0.0.0.0:7001`；端口监听 PID 为 `63156`。
- live 只读 summary 验证 `http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`：HTTP 200，耗时 5.380981s；`camera_status=fetch_failed`、`camera_wysiwyg_status_plain=画面未可见：页面会自动接入共享 MJPEG 预览；多个页面复用同一条上游流，未出帧前不当作画面可见。`、`source_readiness=not_loaded`、`source_diagnosis_status=not_loaded`、`camera_source_first_frame_ready=false`、`camera_blocks_mapping_start=true`、`mapping_start_missing=camera_first_frame,lidar_fresh`。

## 剩余风险

- 这轮只修 PC Node 只读 summary/action card/建图 gate 证据，不读取或独占真实摄像头，不发送 manual、keyboard、free-roam、Nav2、map start、delivery、stop 或 `/cmd_vel`。
- 真实摄像头是否有图仍需现场通过共享预览或只读首帧 probe 复验；当前修复的目标是防止旧 overlay 正向状态误导普通 PC 首屏。
