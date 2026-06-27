# PC 屏幕方向键取消即停回归

sprint_type: micro

## 实际改动

- `pc-tools/workstation/test/App.test.ts`
  - 新增屏幕方向键 `pointercancel` 回归测试。
  - 覆盖流程：勾选安全确认 -> 启用键盘 -> 屏幕 `前进` 方向键 `pointerdown` -> 触发 `pointercancel` -> 必须调用固定 `/api/robot-control/base/stop` 代理，并显示停止原因 `方向键触控取消`。
  - 该测试锁住连续手控的安全收口，防止后续只依赖 `pointerup` 导致触屏取消或浏览器取消事件后残留连续点动。
- `docs/product/pc_tools_workstation.md`
  - 同步记录屏幕方向键取消/移出即停的 PC 交互边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "stops screen keyboard control when the pointer is cancelled"`，目标测试 1 个通过。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。Vite 仍输出既有 chunk size warning，不影响构建通过。
- 通过：`cd pc-tools/workstation && npm test`，2 个 test files / 276 个测试通过。
- 通过：`git diff --check`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 Node 监听 `TCP *:7001 (LISTEN)`；`GET /api/health` 返回 `mode=pc_only_readonly_workstation`、`pc_only=true`、`safe_to_control=false`。

## 剩余风险

- 本轮只补 PC 屏幕连续手控事件收口回归，不执行真实底盘点动、不证明 wheel raw L/R 非零、不证明完整 Nav2 路线执行或 delivery success。
- 摄像头当前仍是上车 `/dev/video1` 内核/UVC 无帧问题；雷达当前仍未刷新，不属于本轮修复范围。
