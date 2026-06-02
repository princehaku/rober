# O7 camera service recovery readiness

## sprint_type

micro

## 实际改动

- 扩展 `pc-tools/workstation/scripts/o7-camera-service-readiness-collector.mjs` 的只读 SSH 诊断：除监听端口和进程摘要外，新增 camera/WebRTC 相关 systemd/unit 摘要、远端脚本摘要、`service_unit_hint_present`、`remote_script_present`、`readiness.action_category` 和脱敏 `safe_start_command_hint`。
- 更新 `pc-tools/workstation/src/server/realMaterialAcceptance.ts`，让 `GET /api/real-material/acceptance` 只读消费 `.workstation-runtime/o7-camera-service-readiness.json` 或 `ROBER_O7_CAMERA_SERVICE_READINESS_ARTIFACT` 指向的 readiness artifact，并在 O7 item 内暴露脱敏 `o7_camera_service_readiness` 摘要。
- 更新 `pc-tools/workstation/src/shared/contracts.ts` 和 `pc-tools/workstation/test/catalog.test.ts`，覆盖 readiness artifact 摘要、action category、blocked reason 拼接、安全 false 字段，以及不暴露 IP、SSH target、绝对路径或 traceback。
- 更新 `docs/product/pc_tools_workstation.md` 与 `docs/interfaces/real_material_acceptance_queue.md`，同步 O7 readiness artifact 进入 acceptance queue 的产品边界和只读恢复动作。

## 验证结果

1. `cd pc-tools/workstation && npm run o7:camera-service-readiness -- --dry-run`
   - 退出状态：0。
   - 关键输出：`status=dry_run`，`artifact_written=false`，`network_probe_executed=false`，`ssh_probe_executed=false`，`post_executed=false`，`webrtc_session_created=false`，`offer_executed=false`，`safe_to_control=false`，`sends_commands=false`，`robot_control_executed=false`，`readiness.action_category=not_observed`。
2. `cd pc-tools/workstation && npm run o7:camera-service-readiness`
   - 退出状态：1，按 collector contract 表示真实 readiness blocked，不是测试失败。
   - artifact 写入：`.workstation-runtime/o7-camera-service-readiness.json`。
   - 关键分类：`status=blocked`，`http_probe.health.status=unreachable`，`http_probe.devices.status=unreachable`，`ssh_probe.status=reachable`，`camera_port_listening=false`，`process_hint_present=false`，`service_unit_hint_present=false`，`remote_script_present=true`，`readiness.action_category=remote_script_present_but_service_inactive`。
   - 安全边界：`post_executed=false`，`webrtc_session_created=false`，`offer_executed=false`，`safe_to_control=false`，`sends_commands=false`，`robot_control_executed=false`。
3. `cd pc-tools/workstation && npm run test`
   - 退出状态：0。
   - 关键输出：`2` 个 test files / `62` 个 tests passed。
4. `cd pc-tools/workstation && npm run build`
   - 退出状态：0。
   - 关键输出：Vite `35 modules transformed`，build completed。
5. `cd pc-tools/workstation && npm run lint`
   - 退出状态：0。
   - 关键输出：`eslint .` 完成，无 lint error。

## 剩余风险

- 本轮没有启动板端 camera/WebRTC 服务，没有 POST `/offer`，没有创建 WebRTC session，也没有采集 180s/3-5min browser long-stability artifact。
- 真实 blocker 已从 generic connection refused 收敛为：SSH 可达、远端存在 `local_webrtc_camera_smoke.sh/.py`，但 8088 未监听且没有可见 camera/WebRTC service/unit 或活跃进程。
- 下一步应由 operator 在板端人工启动或安装 `local_webrtc_camera_smoke` 服务，再重跑 `npm run o7:camera-service-readiness`；只有 `ready_for_long_stability=true` 后才运行 `npm run o7:browser-long-stability`。
- O1 仍保持 `target_port_identity_possible_lidar_or_other_stc_before_more_T130`，本轮没有触碰 WAVE ROVER 串口、`T=130/T=1/T=13/T=131` 或 `/cmd_vel`。

## 本轮时间

- 记录时间：2026-06-02 16:59:20 CST
