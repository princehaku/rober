# Free Roam Primary Button Summary

## sprint_type

micro

## 实际改动

- 在 PC 普通用户自由移动/建图卡的安全确认后、主按钮前新增 `plain-free-roam-primary-button-summary` 只读说明，明确当前主按钮点击会 `只自由移动` 还是 `先建图再移动`。
- 该说明同步暴露 `data-primary-action-kind`、是否会启动 free-roam、是否会先启动 mapping runtime、相机/雷达是否阻塞移动、固定 start endpoint 和 post-start readback endpoint。
- 补充 App DOM 测试，覆盖“相机未首帧证明、雷达已就绪”时可以先低速自由移动但不启动建图记录。
- 同步更新 `docs/product/pc_tools_workstation.md`，登记普通用户主按钮判定的只读合同。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run App.test.ts`，结果 `Test Files 1 passed (1)`、`Tests 237 passed (237)`。
- 通过：`git diff --check`，无空白错误输出。
- 通过：`cd pc-tools/workstation && npm run build`，`tsc` 与 `vite build` 完成；Vite 保留既有 chunk size warning。
- 通过：`cd pc-tools/workstation && npm run lint`，ESLint 无错误输出。

## 剩余风险

- 本轮未做真实硬件 HIL 发车；改动仅影响 PC DOM 可见说明和只读验收字段，不改变实际 free-roam、mapping、Nav2 或 stop 控制路径。
