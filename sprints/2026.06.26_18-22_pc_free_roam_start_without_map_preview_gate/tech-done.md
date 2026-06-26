# PC free roam start without map preview gate

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 自动扫图 start 不再硬性要求“本轮地图画面已刷新”或“地图已有 free cell”。
  - start 的 PC 侧条件收敛为：默认小车已连接、现场安全确认已勾、地图记录已启动、相机采集源 ready、停止兜底可用、且当前没有地图刷新正在进行。
  - 地图画面/free cell 从硬阻塞改为提示：首次建图允许低速启动，启动后仍会刷新地图画面作为所见即所得监看证据。
  - 雷达仍是监看/降级证据，不作为低速自移动硬门禁。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 start-ready + 地图记录已启动 + 未刷新本轮地图画面的自动扫图测试。
  - 测试确认按钮直接走固定 `/api/robot-control/free-roam/autonomy/start` 代理，不调用 PC 侧 manual、`/cmd_vel`、Nav2 goal 或 delivery complete。

## 验证结果

- `npm test -- --run test/App.test.ts -t "free-roam autonomy"` 通过：10 passed。
- `npm test` 通过：2 files, 228 tests passed。
- `npm run build` 通过；Vite 仍有单 chunk 大于 500 kB 的既有提示。
- 只读现场 API 核对：
  - PC Node 仍通过 `http://127.0.0.1:7001` 访问。
  - 小车连接 `readable`，相机 `ready`，视频源 `/dev/video1`。
  - `free_roam_autonomy_start_ready=true`，地图 runtime 已启动，自动扫图 runtime 仍为 `artifact_only=true`、`cmd_vel_publish_enabled=false`、`state=stopping`。
  - 当前雷达 latest fresh 为 `false`，近障碍 gate 显示 `0.04m`；本轮没有触发真实 start 或运动命令。

## 剩余风险

- 本轮只改 PC gate 和普通 UI，不在无人值守环境实际发车。
- 上车端当前仍停在 `现场请求停止`，真实自由移动还需要现场确认后点击 start，并观察 stop 兜底。
- 底盘 wheel raw 仍为 `L/R=0/0`，非零轮速证明没有完成。
- 雷达近障碍 `0.04m` 是现场真实风险信号；即使雷达不作硬门禁，现场也应保持接管并观察避障/换向行为。
