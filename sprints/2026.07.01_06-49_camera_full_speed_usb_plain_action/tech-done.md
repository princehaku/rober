# 相机 full-speed USB 普通指引

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：把 `move_camera_to_high_speed_usb_port_or_powered_hub` 映射为普通用户中文文案，并在 summary 里优先使用 `uvc_video_on_full_speed_usb` 作为更具体的相机根因，说明摄像头挂在 USB 12M full-speed，需要换高速 USB 口/线或带供电 USB Hub 后复测。
- `pc-tools/workstation/src/server/index.ts`：同步修正 camera MJPEG status 本机 relay 的 action token 翻译，避免共享预览状态接口泄露英文枚举。
- `pc-tools/workstation/test/robotControlSummary.test.ts`：锁定 summary 不泄露英文相机 action token。
- `pc-tools/workstation/test/catalog.test.ts`：新增 full-speed USB MJPEG status 合同测试，确认 `source_diagnosis_next_action_plain`、`preview_next_action_plain`、`camera_wysiwyg_next_action_plain` 都输出中文且不执行机器人控制。
- `docs/product/pc_tools_workstation.md`：同步产品合同，说明该变化只修正只读诊断文案，不打开摄像头、不重置 USB、不启动建图或运动命令。

## 验证结果

- `npm test -- --run test/robotControlSummary.test.ts`：通过，6 passed；覆盖 summary 优先显示 USB 12M full-speed 根因。
- `npm test -- --run test/catalog.test.ts -t "workstation camera MJPEG status translates"`：通过，3 passed / 176 skipped。
- `npm run build`：通过，仍有既有 Vite chunk size warning。
- `npm run lint`：通过。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`，监听子进程 PID `53541`；`GET /api/health` 可读。
- live summary 确认相机诊断为 `uvc_full_speed_usb_not_exclusive`，`uvc_usb_topology_video_usb_speed=12M`，下一步中文为“摄像头现在挂在 USB 12M full-speed，换高速 USB 口/线或带供电 USB Hub，减少转接并确认供电后复测；共享预览不是页面独占。”；雷达地图点仍为 `true`。

## 剩余风险

- live no-motion 刷新已让地图雷达点恢复 WYSIWYG：`radar_overlay_status=loaded`，当前地图 68 个雷达点。
- 相机仍未出首帧，当前现场证据指向 USB 12M full-speed 与 UVC/USB 传输错误；本轮只把恢复动作翻译清楚，没有也不能通过软件修复物理 USB 链路。
- 本轮没有发送 Nav2、manual、keyboard、free-roam、建图 runtime、delivery、stop 或 `/cmd_vel`。
