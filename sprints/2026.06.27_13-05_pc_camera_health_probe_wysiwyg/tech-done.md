# sprint_type: micro

## 实际改动

- 修正 PC 普通首屏 `只读检查` 文案：当 summary/camera health 已经确认 `source_first_frame_failed` 时，不再显示“还没做首帧检查”。
- 对 `source_diagnosis_status=uvc_no_frame_not_exclusive` 的 live 形状，直接把“不是页面独占、UVC 没有输出视频帧”的 health 诊断显示到首屏检查摘要。
- 更新相机 WYSIWYG 测试，锁定 not-in-use + first-frame failed 时首屏不会回退成未知检查状态。
- 同步更新 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `npm test -- --run App.test.ts -t "explains a live not-in-use camera first-frame failure"`：通过，1 个测试通过。
- `npm test`：通过，2 个测试文件、287 个测试通过。
- `npm run build`：通过，Vite 保留既有 chunk size warning。

## 剩余风险

- 本轮只修正 PC 端状态展示，不修复 UVC 设备无帧的硬件/驱动根因。
- live 相机仍需要检查 USB、摄像头输入或供电，或更换 known-good UVC 复测。
