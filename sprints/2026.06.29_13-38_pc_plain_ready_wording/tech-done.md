# PC 普通就绪文案 micro sprint

sprint_type: micro

## 实际改动

- 将 PC 普通首屏、Robot Control summary、radar status、free-roam latest、目标总览和相关测试中的用户可见 `ready` 文案统一改为“就绪/未就绪”。
- 同步清理 `pc-tools/README.md` 与 `docs/product/pc_tools_workstation.md` 中面向普通用户例句里的 `ready` 混写；保留接口字段名、状态枚举和高级诊断 token 兼容。
- 未调用任何危险控制接口；本轮只读 live 验证只访问 `GET /api/robot-control/summary`。

## 验证结果

- `npm --prefix pc-tools/workstation test`：通过，2 个 test files，379 个 tests。
- `npm --prefix pc-tools/workstation run build`：通过；Vite 仍提示现有 bundle 超过 500 kB。
- `HOST=0.0.0.0 PORT=7001 npm --prefix pc-tools/workstation run api`：本机 Node API 已监听 `*:7001`。
- `GET http://127.0.0.1:7001/api/robot-control/summary`：通过；`current_fact_plain` 显示“建图启动：未就绪”和“建图验收：未就绪”，检查到的旧 `ready` 文案列表为空。

## 剩余风险

- 真实 live 仍显示摄像头首帧失败，根因更像 UVC 无视频帧，不是页面独占。
- 雷达当前仍是 stopped/not current，地图雷达点当前显示 0 个，旧来源点只作诊断。
- Nav2 上次路线结果成功但同窗口 wheel L/R 仍为 0/0；完整运动闭环仍需要现场安全确认后按 ROS 模式重跑并观察非零轮速。
