# 自由移动建图降级原因 WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `freeRoamMappingMissingPlainLabels`，把上车端 `sensor_readiness.mapping_readiness.missing` 的稳定 token 翻译为普通首屏可读原因。
  - 当 PC 请求建图记录但上车端二次确认返回 `mapping_active_applied=false` 时，`状态机写入` 行不再只说 `本轮只按自由移动记录`，而是同步显示 `建图缺口：画面首帧未出、雷达未刷新` 等具体原因。
- `pc-tools/workstation/test/App.test.ts`
  - 新增回归测试，覆盖 PC 发送 `confirm_mapping_active=true`、上车端降级 `mapping_active_applied=false`、普通首屏显示建图缺口，并确认没有调用 base/manual、Nav2 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录自由移动可启动但建图验收降级的 WYSIWYG 规则。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "shows onboard mapping-readiness gaps"`，目标测试 1 个通过。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。Vite 仍输出既有 chunk size warning，不影响构建通过。
- 通过：`cd pc-tools/workstation && npm test`，2 个 test files / 277 个测试通过。
- 通过：`git diff --check`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 Node 监听 `TCP *:7001 (LISTEN)`；`GET /api/health` 返回 `mode=pc_only_readonly_workstation`、`pc_only=true`、`safe_to_control=false`。

## 剩余风险

- 本轮只改善 PC 对上车端二次确认结果的 WYSIWYG 展示，不执行真实自由移动、manual、Nav2 或 delivery。
- 当前现场 camera 仍是 `/dev/video1` 内核/UVC 无帧，雷达仍未刷新；真实可验收建图仍要等相机首帧和雷达新鲜度恢复。
