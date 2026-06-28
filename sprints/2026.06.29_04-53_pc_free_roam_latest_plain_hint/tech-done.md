# PC Free-Roam Latest Plain Hint

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- started_at: 2026-06-29 04:53 CST
- status: done

## 实际改动

- 扩展 PC Node 只读 `GET /api/robot-control/free-roam/autonomy/latest` 响应合同，新增顶层 `plain_hint` 与 `next_action_plain`。
- `plain_hint` 汇总自由移动 start/运行态与建图验收态；`next_action_plain` 汇总“可先自由移动/继续监看”和“建图还缺哪些材料”。
- 保留既有细分字段 `free_move_start_status_plain`、`motion_runtime_status_plain`、`mapping_acceptance_status_plain`、`motion_next_action_plain`、`mapping_next_action_plain`，供普通首屏分区展示。
- 补充 free-roam latest 回归测试，锁定运行中与停止请求但可启动两类状态下，顶层白话字段可直接说明自由移动与建图下一步。
- 同步 `docs/product/pc_tools_workstation.md`，说明该 latest 入口仍然只读 runtime artifact，不启动 free-roam、不启动建图、不发送 manual、keyboard、Nav2、delivery、stop 或 `/cmd_vel`。

## 验证结果

- `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "free-roam autonomy latest"`：通过，2 个测试通过。
- `npm --prefix pc-tools/workstation run build`：通过。
- `npm --prefix pc-tools/workstation test`：通过，2 个测试文件、375 个测试通过。
- 重启 PC API 到 `0.0.0.0:7001` 后执行只读 `GET /api/robot-control/free-roam/autonomy/latest`：通过，返回 `plain_hint=自由移动可启动...建图验收未 ready...`、`next_action_plain=勾选现场安全确认后可先自由移动...建图验收还差...`、`free_move_start_ready=true`、`motion_ready=false`、`mapping_readiness_ready=false`、`robot_control_executed=false`。
- `git diff --check`：通过。

## 剩余风险

- 当前改动只增强自由移动 latest 的只读可读性；真实低速自由移动仍需要现场勾选安全确认后由 operator 主动点击开始。建图验收仍受画面首帧、雷达新鲜、地图记录和地图画面限制。
