# tech-done

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：把 `wheel_feedback_latest_nonzero_left_speed/right_speed` 加入 PC summary 只读 key 白名单，让 `/api/base/feedback-samples/latest.latest_result.wheel_feedback_summary.latest_nonzero_pair` 不再被压缩摘要丢弃。
- `pc-tools/workstation/test/catalog.test.ts`：补充 live 形态回归测试，覆盖 latest wheel L/R 为 `0/0`、历史最新非零 L/R 为 `164/164` 的展示边界。
- `docs/product/pc_tools_workstation.md`、`docs/hardware/wave_rover_json_bridge.md`：同步记录 PC 只读非零 L/R 与 Nav2 同窗口验收的边界。

## 验证结果

- 通过：`npm test -- --run test/catalog.test.ts`，`113 passed (113)`。
- 通过：`npm test -- --run test/App.test.ts`，`150 passed (150)`。
- 通过：`npm run lint`。
- 通过：`npm run build`；仍有既有 Vite chunk size warning，未影响构建产物生成。
- 通过：重启 PC Node 到 `0.0.0.0:7001`，screen 为 `85910.rober_pc_7001`。
- 通过：live summary `readback_summary.base.wheel_feedback_latest_nonzero_left_speed/right_speed=164/164`，同时 Nav2 同窗口仍为 `goal_execution_base_feedback_latest_left_speed/right_speed=0/0`、`goal_execution_proven=false`。
- 通过：live camera summary 显示 `source_first_frame_failed`、`source_usage_status=not_in_use`、`shared_preview_exclusive_camera_claim=false`、MJPEG latest failure `502`；当前问题不是浏览器独占，而是板端 `/dev/video1` 打不开/读不到首帧。

## 剩余风险

- 该改动只修复 PC WYSIWYG 摘要信息丢失，不证明 Nav2 路线真实移动完成。
- live 上位机最近一次 Nav2 artifact 仍显示 Nav2 执行窗口内 `base_feedback_summary.nonzero_sample_count=0`、`latest_pair=0/0`，因此完整路线执行仍需重新跑带同窗口 wheel raw L/R 非零的上车验证。
- 摄像头共享预览链路已给出非独占诊断，但真实画面仍依赖板端摄像头恢复首帧输出；本轮没有更换 USB 摄像头、线缆或供电。
