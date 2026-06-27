# Free Roam Motion Gate Wording

sprint_type: micro

## 实际改动

- 将 PC summary 中 `motion_hil_unlock` 运行态诊断从“自动扫图节点”改为“自由移动状态机”，避免自由移动已可启动时仍被误读为自动扫图未启动。
- 将普通首屏 runtime fallback 文案同步改为“当前尚未启动自由移动”和“自由移动运动发布已打开”，保持用户可见文字与 summary gate 一致。
- 同步更新 workstation catalog/UI 测试 fixture 和断言，覆盖“尚未启动自由移动”文案，并显式防止运行态再次显示“当前尚未启动自动扫图”。
- 同步更新 `docs/product/pc_free_roam_mapping_design.md` 与 `docs/product/pc_tools_workstation.md`，记录自由移动与建图验收的文案边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- catalog.test.ts --testNamePattern "free-roam|free movement|free-roam autonomy"`，1 个文件通过，10 个命中测试通过。
- 通过：`cd pc-tools/workstation && npm test -- App.test.ts --testNamePattern "free-roam|free movement|自由移动|自动扫图"`，修正旧精确断言后 1 个文件通过，23 个命中测试通过。
- 通过：`cd pc-tools/workstation && npm test`，2 个文件通过，313 个测试通过。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`；Vite 仍提示单 chunk 超过 500 kB，这是既有打包体积提醒，不阻塞本轮。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只修正 PC 运行态文案和测试契约，不进行真实小车运动、摄像头独占释放、Nav2 发车或硬件 HIL 验证。
