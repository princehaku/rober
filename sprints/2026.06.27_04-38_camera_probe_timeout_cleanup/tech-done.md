# 相机深度探针超时清理 micro sprint

- sprint_type: micro
- owner: mainline-no-subagent
- scope: 上车端 camera first-frame probe 诊断稳定性

## 实际改动

- `onboard/scripts/camera_first_frame_probe.py`
  - 新增 `run_subprocess_group()`，外部 v4l2/ffmpeg 取帧命令使用独立进程组执行。
  - 超时时对整个进程组发送 `SIGKILL`，避免 `ffmpeg` 子进程残留占用 `/dev/video1`。
  - 后端矩阵 timeout 调整为 v4l2 4s、ffmpeg 5s，使 deep probe 最坏耗时落在 PC 代理超时内。
- `onboard/tests/test_camera_first_frame_probe.py`
  - 更新 backend command timeout/frame-observed 测试以覆盖新 helper。
  - 新增进程组超时清理断言，锁住 `killpg` 行为。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录现场 deep probe 复测结果和仍未出帧的边界。

## 现场验证结果

- 修复前：
  - `backendSmoke=1` 被 PC 代理超时中断。
  - 上车端残留 `/usr/bin/python3 camera_first_frame_probe.py ... --include-backend-smoke` 与 `ffmpeg ... /dev/video1`，`ffmpeg` 约 97% CPU。
  - 后续直接 probe 因残留占用变成 `open_failed`。
- 修复后已同步脚本到上车端：
  - `scp -P 37878 onboard/scripts/camera_first_frame_probe.py root@192.168.1.11:/root/rober/onboard/scripts/camera_first_frame_probe.py`
  - `python3 -m py_compile /root/rober/onboard/scripts/camera_first_frame_probe.py`
- PC deep probe 复测：
  - `POST /api/robot-control/camera/first-frame/probe?baseUrl=http://192.168.1.11:8787&backendSmoke=1`
  - `remote_http_status=503`
  - `status=first_frame_timeout`
  - `failure_reason=capture_read_call_timeout`
  - `backend_smoke_status=backend_no_frame_observed`
  - `backend_frame_observed=false`
  - `backend_attempts=4`
  - `elapsed_ms=22901`
- 残留进程复核：
  - `ps -ef | grep -E "camera_first_frame_probe|v4l2-ctl|ffmpeg" | grep -v grep`
  - 无输出，确认 deep probe 结束后没有残留占用。

## 本地验证结果

- 通过：`python3 -m unittest onboard.tests.test_camera_first_frame_probe`
  - `Ran 11 tests`
  - `OK`
- 通过：`python3 -m unittest onboard.tests.test_camera_first_frame_probe onboard.tests.test_upper_robot_api`
  - `Ran 71 tests`
  - `OK`
- 通过：`cd pc-tools/workstation && npm test -- --testNamePattern "camera first-frame|camera MJPEG|camera source first-frame|camera source owner|shared preview"`
  - `Test Files 2 passed (2)`
  - `Tests 11 passed | 249 skipped (260)`
- 通过：`cd pc-tools/workstation && npm test`
  - `Test Files 2 passed (2)`
  - `Tests 260 passed (260)`
- 通过：`python3 -m unittest discover onboard/tests`
  - `Ran 174 tests`
  - `OK`
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`
  - Vite 仍提示单个 chunk 超过 500 kB；这是既有打包体积警告，本轮未扩大处理范围。
- 通过：`git diff --check`

## 剩余风险

- 当前摄像头仍未出首帧：`/dev/video1` deep probe 和 backend smoke 都未观察到真实 frame。
- 本轮修复的是诊断工具残留占用与超时结构化返回；不等于 camera ready。
- Nav2 完整路线 HIL 仍未完成，同窗口 `T1001 L/R` 非零未证明。
