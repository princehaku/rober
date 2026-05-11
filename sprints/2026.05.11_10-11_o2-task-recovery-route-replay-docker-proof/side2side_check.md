# Side-by-side Check: O2 Task Recovery Route Replay Docker Proof

## 对照项

| 验收项 | 结果 |
| --- | --- |
| fixed-route status route_progress 透传 | 通过 py_compile 与 targeted unittest 覆盖 |
| route_progress-only status 可提升 evidence_ref | 通过 targeted unittest 覆盖 |
| task record 顶层 route_progress | 通过 targeted unittest 覆盖 |
| diagnostics 空 top-level route_progress 不阻断 nav fallback | 通过 targeted unittest 覆盖 |
| crosscheck --task-record-dir 找不到匹配返回非 0 | 通过测试与手工 failure sample 覆盖 |
| O1 不声明 hil_pass | OKR 和本 sprint docs 明确保留 blocked |

## 用户验收口径

本轮只接受 software proof：命令输出必须显示 targeted tests 通过、crosscheck 成功样例 `mismatches=0`，失败样例非 0。没有真实串口与上车 route run，所以不能作为硬件/HIL 验收。

## 当前状态

通过。`py_compile` exit 0，targeted unittest `Ran 46 tests ... OK`，crosscheck success sample `mismatches=0`，missing-match sample 返回非 0，scoped `git diff --check` exit 0。
