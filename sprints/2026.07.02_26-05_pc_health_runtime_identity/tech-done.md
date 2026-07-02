# PC Health Runtime Identity

## sprint_type

micro

## 实际改动

- 重启本机 `0.0.0.0:7001` PC 工作站服务到当前代码，并只读验证 summary 顶层 `nav2_goal_execution_proven=false`，与完整行程缺口 `same_window_wheel_lr_nonzero,delivery_success` 一致。
- 在 PC `GET /api/health` 增加运行态标识：监听 host/port、listen address、默认小车 API 地址、服务启动时间戳和 ISO 时间。
- `health` 同步暴露只读边界字段，明确它不探测 Robot API、不发车、不启动 Nav2/manual/keyboard/free-roam/建图、不提交送达、不停止车辆。
- 更新 catalog 测试和产品文档，避免现场看到旧 7001 进程时无法确认服务是否已经从当前代码重启。

## 验证结果

- 通过：重启前后只读读取 `http://127.0.0.1:7001/api/robot-control/summary`，确认当前服务返回 `nav2_goal_succeeded=true`、`nav2_goal_execution_proven=false`、`trip_execution_missing_evidence=["same_window_wheel_lr_nonzero","delivery_success"]`。
- 通过：`cd pc-tools/workstation && npm test -- --run catalog.test.ts`，结果 `Test Files 1 passed (1)`、`Tests 182 passed (182)`。
- 通过：`git diff --check`，无空白错误输出。
- 通过：`cd pc-tools/workstation && npm run build`，`tsc` 与 `vite build` 完成；Vite 保留既有 chunk size warning。
- 通过：`cd pc-tools/workstation && npm run lint`，ESLint 无错误输出。

## 剩余风险

- 本轮 health 运行态标识只证明 PC 7001 服务进程与只读合同，不证明真实 Nav2 HIL、键盘轮速、自由移动、相机画面、雷达贴图或建图完成。
