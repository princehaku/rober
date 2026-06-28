# PC 自由移动 Readback 首屏可见 Micro Sprint

## Sprint 类型

sprint_type: micro

## 实际改动

- 普通首屏 `自由移动 / 建图` 卡片新增 `自由移动事实` 行，直接展示上车端 `free_roam` readback 与 PC `safe_command_boundary` 白话边界。
- 新增前端测试断言，确保默认普通首屏能看到“自由移动未就绪”和“相机、雷达、地图记录只影响建图验收”。
- 同步更新 `docs/product/pc_tools_workstation.md`，记录该变化只展示只读 summary/readback，不触发任何发车或停止接口。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "Robot Control V1"`，1 passed，214 skipped。
- 通过：`npm --prefix pc-tools/workstation run build`，Vite build 成功；仅保留既有 chunk size warning。
- 通过：`npm --prefix pc-tools/workstation test`，2 个测试文件、375 个测试全部 passed。
- 通过：PC API 已重启到 `0.0.0.0:7001`，`lsof` 显示 `node` 监听 `*:7001`。
- 通过：只读读取 `http://127.0.0.1:7001/api/robot-control/summary`，`readback_summary.free_roam` 返回 `status=start_ready`、`start_ready=true`、`motion_start_ready=true`、`motion_ready=false`、`mapping_ready=false`；白话事实为“可先自由移动；当前有停止请求，开始自由移动会先清除停止请求”和“建图验收未 ready；还差：画面首帧、雷达新鲜、地图记录、地图画面；不影响先低速自由移动”。

## 剩余风险

- 当前改动只让普通首屏更直接显示自由移动/建图分层事实，不改变上车端自由移动状态机、相机采集、雷达 lifecycle、Nav2 或 `/cmd_vel` 行为。
- 未经现场安全确认，本轮不调用 manual、keyboard、free-roam、Nav2、delivery、stop 或 `/cmd_vel` 控制接口。
