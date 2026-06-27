# PC camera backend smoke WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 在 `readback_summary.camera` 增加 backend smoke 短字段：
    `first_frame_probe_backend_smoke_status`、`first_frame_probe_backend_frame_observed`、
    `first_frame_probe_backend_attempts`、`first_frame_probe_fallback_attempts_summary`。
- `pc-tools/workstation/src/server/index.ts`
  - camera first-frame probe overlay 保留 backend smoke 结果，供后续 summary 读取。
  - 修复 CLI 启动时 `server` 只保存在 Promise 回调局部变量的问题，改为模块级保留 `cliServer`，避免 7001 后台启动后被回收退出。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - PC summary 将最近一次 camera first-frame probe 的 backend smoke 结论透传到 `readback_summary.camera`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏画面失败文案优先显示 `backend_no_frame_observed`：明确“不是页面独占，摄像头能打开，后端多种方式也没有取到视频帧”。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖 live not-in-use + backend no-frame 的普通用户文案。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 backend smoke probe 后 summary 保留 backend smoke 字段。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录 camera shared preview / backend smoke 的所见即所得口径。

## 现场只读证据

- SSH：`ssh root@192.168.1.11 -p 37878` 可连，目标机为 `op-z3-b6.home`。
- 目标机监听：
  - `0.0.0.0:8088` camera smoke service
  - `0.0.0.0:8787` upper robot API
- `GET /api/camera/health`：
  - `status=source_first_frame_failed`
  - `selected_path=/dev/video1`
  - `source_usage.status=not_in_use`
  - `source_failure_reason=capture_read_returned_false`
- `v4l2-ctl -d /dev/video1 --stream-mmap=3 --stream-count=3 --stream-to=/tmp/...`：
  - 8 秒超时，输出文件 0 字节。
- PC fixed probe：
  - `POST /api/robot-control/camera/first-frame/probe?backendSmoke=1`
  - 返回 `proxy_status=probe_failed`、`status=first_frame_timeout`、`failure_reason=capture_read_call_timeout`
  - `backend_smoke_status=backend_no_frame_observed`、`backend_frame_observed=false`、`backend_attempts=4`
- PC 7001 runtime：
  - 用 detached Node/tsx 方式重启后，`TCP *:7001 (LISTEN)` 保持运行。
  - `GET /api/health` 返回 `mode=pc_only_readonly_workstation`、`pc_only=true`、`safe_to_control=false`。
  - 重启后再次触发 `backendSmoke=1`，`GET /api/robot-control/summary` 读回
    `first_frame_probe_backend_smoke_status=backend_no_frame_observed`、
    `first_frame_probe_backend_frame_observed=false`、`first_frame_probe_backend_attempts=4`。

## 验证结果

- 已通过：
  - `cd pc-tools/workstation && npm test -- -t "explains a live not-in-use camera first-frame failure as not exclusive access"`
  - `cd pc-tools/workstation && npm test -- -t "workstation camera first-frame probe can request backend smoke for explicit diagnostics"`
  - `cd pc-tools/workstation && npm run lint`
  - `cd pc-tools/workstation && npm run build`
  - `cd pc-tools/workstation && npm test`
  - `git diff --check`

## 剩余风险

- 摄像头真实画面仍未恢复；本轮证明并展示的是“不是 PC 页面独占，而是上车 UVC 源头无帧”。
- 本轮未执行 USB unbind/bind、重启 camera service 或更换摄像头输入；这些属于现场恢复动作，需要 operator 明确允许。
- 雷达当前 live summary 仍为 `missing/lifecycle_not_running`，Nav2 完整路线仍缺 wheel raw L/R 非零同窗口证明。
