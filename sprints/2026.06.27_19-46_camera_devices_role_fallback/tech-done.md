# Camera Devices Role Fallback

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - PC summary 在 `/api/camera/health` 缺少 `selected_role`、`selected_sibling_video_nodes_summary` 时，会从只读 `/api/camera/devices` 的 `source_candidates` 推断。
  - 对 live 形态 `/dev/video1` + `/dev/video2` 的 UVC 复合设备，summary 可显示 `/dev/video1=video_capture` 语义和 `/dev/video2=metadata` 兄弟节点。
  - 该改动只读解析相机设备枚举，不打开摄像头、不改变上车端摄像头占用策略、不发送运动命令。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增回归：health 只给 `/dev/video1`，devices 给 UVC capture/metadata 候选时，summary 必须补出 `selected_role=video_capture` 和 `selected_sibling_video_nodes_summary=/dev/video2=metadata`。

## 验证结果

- `npm test -- --runInBand test/catalog.test.ts`
  - 失败：Vitest 不支持 Jest 的 `--runInBand` 参数，未执行测试主体。
- `npm test -- test/catalog.test.ts`
  - 通过：`132 passed`。
- `npm test`
  - 通过：`309 passed`。
- `npm run build`
  - 通过：TypeScript + Vite build + server TypeScript build 通过；保留既有 chunk size warning。
- `npm run lint`
  - 通过。

## live 复核

- 已重启本机 PC Node 到 `0.0.0.0:7001`，未修改 Clash 或系统代理。
- 重启前 live summary 已确认：
  - 相机 shared preview 合同为 `single_shared_capture_for_multiple_clients`，不是页面独占；当前真实失败是 `/dev/video1` 首帧超时。
  - 自由移动 `start_ready=true`，只需要现场安全确认和停止兜底；雷达材料只影响建图验收。
  - Nav2 上次 `pwm` action succeeded，但 wheel raw L/R 为 `0/0`，下一步提示用 `ros` 重跑。
- 本次代码落地后已重启 7001 并再次 live 读回：
  - `selected_role=video_capture`
  - `selected_sibling_video_nodes_summary=/dev/video2=metadata`
  - `source_diagnosis_status=uvc_no_frame_not_exclusive`
  - `free_roam.start_ready=true`
  - `nav2.next_execution_base_command_mode=ros`

## 剩余风险

- 摄像头仍未出首帧：本轮只把“不是独占、是 UVC 无帧”诊断展示得更完整，未解决真实 USB 摄像头无画面。
- 未发送真实自由移动或 Nav2 重跑命令；需要现场明确安全确认后才能执行运动验证。
- `/dev/video1`/`/dev/video2` sibling 推断依赖 v4l2/sysfs 名称一致；若未来摄像头驱动命名变化，需要再补匹配规则。
