# 2026-07-02 01:55 Summary 现场短别名

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 为 `GET /api/robot-control/summary` 增加现场脚本短 alias 类型：
    `field_acceptance_primary_missing_id`、`field_acceptance_primary_missing_label`、
    `field_acceptance_primary_missing_action_id`、`field_acceptance_primary_readback_endpoint`、
    `field_acceptance_primary_readback_method`、`field_acceptance_primary_requires_motion_before_readback`、
    `field_acceptance_primary_requires_safety_confirm_before_motion`、`field_acceptance_primary_blocks_field_acceptance`、
    `live_wysiwyg_missing_reasons`、`mapping_start_missing_evidence`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 顶层短 alias 直接镜像既有权威字段，减少现场 `curl | jq` 查嵌套路径的成本。
  - 这些字段只读，不新增任何 motion/control endpoint。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 锁定短 alias 与原始字段同源，防止后续退回 `null`。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录 summary 短 alias 的边界：只服务读回和现场验收，不重算状态，不发车。

## 验证结果

- `git diff --check`：通过。
- `cd pc-tools/workstation && npm test -- --run robotControlSummary.test.ts`：通过，1 file / 10 tests。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍提示 bundle 超 500 kB 的既有体积 warning。
- 7001 重启验证：`node` PID `7242` 监听 `*:7001`。
- `curl http://127.0.0.1:7001/api/robot-control/summary | jq '{status, field_acceptance_primary_missing_id, live_wysiwyg_missing_reasons, mapping_start_missing_evidence}'`：
  - `status=needs_wheel_rerun`
  - `field_acceptance_primary_missing_id=same_window_wheel_lr_nonzero`
  - `live_wysiwyg_missing_reasons=[camera,radar_map_points]`
  - `mapping_start_missing_evidence=[camera_first_frame]`

## 剩余风险

- 本轮没有执行 Nav2、键盘、自由移动、建图或任何 `/cmd_vel`；运动闭环仍需要现场安全确认后验证。
- 相机首帧仍取决于真实上车硬件状态；本轮只改善 PC summary 读回口径。
