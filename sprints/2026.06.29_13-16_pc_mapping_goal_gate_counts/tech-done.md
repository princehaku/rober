# tech-done

sprint_type: micro

## 实际改动

- 收紧 PC Robot Control summary 的建图目标口径：`mapping_start` 未达到建图启动条件时，动作卡和目标检查不再标记为需要现场安全确认，也不再计入真实运动验证项。
- 更新 PC workstation 服务端测试与前端 fixture，防止未就绪建图再次被算成第 4 个可发车动作。
- 同步更新 `pc-tools/README.md` 与 `docs/product/pc_tools_workstation.md`，记录该变化只影响只读 summary 结构，不触发任何运动命令。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "proxies Robot API readback"`，1 passed / 163 skipped。
- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "marks free-roam autonomy ready"`，1 passed / 163 skipped。
- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "renders Robot Control V1"`，1 passed / 214 skipped。
- 通过：`npm --prefix pc-tools/workstation test`，2 files passed，379 tests passed。
- 通过：`npm --prefix pc-tools/workstation run build`，Vite build 成功；仅保留既有 chunk size warning。
- 通过：重启 PC API 到 `0.0.0.0:7001`，PID `88674`；只读 live summary 回读 `loaded_count=15`、`failed_count=0`、`safety_confirm_needed_count=3`、`motion_needed_count=3`。
- 通过：只读 7071 误填回读仍 fail-closed，`first_blocker=robot_api_port_7071_mismatch_use_8787`。

## 剩余风险

- 本轮不调用任何 unsafe endpoint，不会启动 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`；真实车运动、摄像头首帧和雷达新鲜度仍需现场确认。
