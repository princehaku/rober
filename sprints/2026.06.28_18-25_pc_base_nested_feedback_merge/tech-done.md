# 2026-06-28 18:25 PC base nested feedback readback 合并

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 新增当前底盘反馈只读状态合并逻辑，同时读取直接 `/api/base/status` 与嵌套 `/api/status.base`。
  - 当两个来源冲突时按 `read_error > t1001_not_observed > t1001_observed > not_loaded` 显示更保守结论。
  - 该改动只影响 PC summary 的只读事实展示，不发送 manual、keyboard、Nav2、delivery、free-roam、stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/catalog.test.ts`
  - 加强 PC Node summary 回归测试：模拟 `/api/status.base` 当前 T=130 串口读失败、`/api/base/status` 只显示未观察到 T=1001、旧 samples 带历史非零材料时，summary 仍必须显示当前 read error。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 PC Node summary 对直接 base status 与 nested status base 的合并口径。

## 验证结果

- 通过：`npm test -- --run test/catalog.test.ts -t "nested status T130 read errors"`
  - 结果：1 个测试文件通过，1 个目标测试通过，147 个测试按过滤跳过。
- 通过：`npm test`
  - 结果：2 个测试文件通过，345 个测试通过。
- 通过：`npm run lint`
  - 结果：ESLint 无报错。
- 通过：`npm run build`
  - 结果：TypeScript 与 Vite 生产构建通过；仅保留既有 Vite chunk size warning。
- 通过：`git diff --check`
  - 结果：无空白或 patch 格式问题。

## 剩余风险

- 本轮未做真实底盘 HIL 或真实发车验证；变更限定在 PC summary 只读展示和回归测试。
- 当前真实上位机可能仍存在 T=1001 未观察到或串口偶发读失败，需要现场按安全流程继续用只读刷新与低速手控验证。
