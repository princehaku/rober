# sprint_type: micro

## 实际改动

- PC 普通“自由移动/建图”主提示接入上车端 `safe_command_boundary.free_roam_autonomy_next_action`。
- 当上车端说明“可先自由移动，建图验收还差...”时，普通卡片会在主 hint 中显示“上车建议”，并在本机已勾安全确认后把“勾选现场安全确认后可先自由移动”改写成“已勾安全确认，可先自由移动”。
- 这让“车可以先自由自助移动”和“相机/雷达 ready 后才算建图验收”在同一张普通卡片里同时可见。
- 本轮只消费只读 summary 字段并更新文案；没有触发自由移动 start、键盘脉冲、底盘 manual、Nav2、雷达启动、cmd_vel 或送达确认。

## 验证结果

- `npm --prefix pc-tools/workstation test -- -t "allows low-speed free-roam recording while marking mapping degraded"`：通过，1 passed。
- `npm --prefix pc-tools/workstation test`：通过，367 passed。
- `npm --prefix pc-tools/workstation run build`：通过，Vite 仍提示现有 chunk 大于 500 kB 的非阻塞 warning。
- 只读 live `GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`：通过，返回 `free_roam.status=start_ready`、`free_roam_autonomy_start_ready=true`、`free_roam_autonomy_next_action=勾选现场安全确认后可先自由移动；建图验收还差：画面首帧、雷达新鲜、地图记录、地图画面`、`mapping_missing=camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview`。相机仍为 `source_first_frame_failed` 且 `uvc_no_frame_not_exclusive`；雷达为 `lifecycle_running=false`、`runtime_scan_status=stale`、`latest_scan_proof_fresh=false`。

## 剩余风险

- 本轮没有现场安全确认，因此没有启动自由移动，也没有验证小车真实连续移动。
- live 当前可先自由移动，但不能按建图验收收口；建图还需要相机首帧、雷达新鲜、地图记录启动、地图画面刷新四项证据。
- PC 键盘连续控制和 Nav2 完整路线仍需现场安全确认后的真实执行窗口验证，尤其是同窗口 wheel raw L/R 非零。
