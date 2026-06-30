# PC 首屏 Summary 底盘慢读降级

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`、`pc-tools/workstation/src/server/index.ts`
  - `status`、`camera_health`、`camera_devices`、`base_status` 和 `base_feedback_samples_latest` 在普通 summary 聚合里使用 2400ms 上限。
  - `base_status` 不再进入 summary 串行慢读队列，避免一个底盘串口只读窗口拖住地图、画面、雷达、Nav2 和自由移动状态。
  - summary 前置相机诊断也使用 2400ms 上限，避免首屏为了相机 health overlay 空等。
  - 独立 `/api/robot-control/base/status` 未改，仍可由用户明确点击后等待较长只读底盘反馈。
- `pc-tools/workstation/test/catalog.test.ts`
  - 将旧的“summary 等 4.5s 底盘慢读/5s 相机枚举/status 聚合”合同改为“summary 先返回分项事实，慢项以 2400ms 超时降级”。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步 PC 首屏 summary 不被底盘慢读拖住、轮速慢读改由独立只读刷新入口补证的口径。

## 验证结果

- 现场只读观测：`http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 在旧服务上约 18s 才返回；响应里 `base_status` 为 `fetch_timeout_8000ms`。随后直接读到 `/api/camera/devices` 约 11s、并发下 `/api/status` 可到约 11s；地图预览直接读 `/api/map/preview` 约 1.0s。
- 通过：`npm test -- --run test/catalog.test.ts -t "workstation summary route caps slow base readback so the plain first screen stays responsive"`。
- 通过：`npm test -- --run test/catalog.test.ts -t "Robot Control summary reads fast endpoints before serial slow aggregate endpoints"`。
- 通过：`npm test -- --run test/catalog.test.ts -t "Robot Control summary caps slow camera devices readback for a responsive plain first screen"`。
- 通过：`npm test -- --run test/catalog.test.ts -t "Robot Control summary keeps camera diagnosis while capping slow status readback"`。
- 通过：`npm test -- --run`，2 files passed，389 tests passed。
- 通过：`npm run lint`，0 errors，4 个既有 Vue multiline warning。
- 通过：`npm run build`，TypeScript 与 Vite build 通过；Vite 仍提示单 chunk 大于 500 kB 的既有 warning。
- 通过：`git diff --check`。
- 通过：新版 7001 summary 实测，`curl --max-time 12` 返回 `HTTP 200 time 5.428745`；`status`、`camera_health`、`camera_devices`、`base_status`、`base_feedback_samples_latest` 均按 `fetch_timeout_2400ms` 降级，`map_proof_latest`、`nav2_status`、`radar_status` 仍返回分项事实。

## 剩余风险

- 该变化只影响 PC 首屏 summary 的只读聚合时延；不启动 ROS2 runtime，不执行 Nav2，不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 轮速 raw L/R 非零验收仍需要真实底盘读数或独立只读刷新返回；summary 超时时不会伪造轮速。
