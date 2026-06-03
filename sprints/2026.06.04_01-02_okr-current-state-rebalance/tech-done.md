# OKR Current State Rebalance Tech Done

sprint_type: micro

## 实际改动

- `OKR.md`
  - 在 `## 4.1 当前 OKR 进度快照` 下重写为更易迭代的当前表。
  - 保留 O1 约 97%、O5 约 96%、O6 约 96%、O7 约 98.9%，没有上调比例。
  - 增加“比例更新规则”，明确只有真实生产/现场/可回放材料才涨分。
  - 当前表只保留 O1/O5/O6/O7，并按“已验收/可计入、下一步可涨分 KR、不得越界”组织。
  - 最高优先级排序改为 O5/O6 -> O1 -> O7，并写明原因是 O5/O6 当前完成度最低。
- `docs/process/okr_progress_log.md`
  - 在 2026-06-04 系列下追加 `2026-06-04 01-02｜OKR current state rebalance｜当前 KR 和比例更新规则重排`。
  - 明确本轮只是结构和比例口径重平衡，不新增 runtime 证据，不涨分。
- `sprints/2026.06.04_01-02_okr-current-state-rebalance/tech-done.md`
  - 创建本 micro sprint 留档。

## 验证结果

已运行用户指定的三条只读验证命令：

1. `rg -n "比例更新规则|O5|O6|O1|O7|约 96%|约 97%|约 98.9%|not_proven|safe_to_control" OKR.md docs/process/okr_progress_log.md sprints/2026.06.04_01-02_okr-current-state-rebalance/tech-done.md`
   - exit 0。
   - 关键片段：
     - `OKR.md:157` 命中“比例更新规则”，明确 O5/O6、O1、O7 的涨分门槛。
     - `OKR.md:161-164` 命中 4.1 当前表，只保留 O5/O6/O1/O7，比例分别为约 96%、约 96%、约 97%、约 98.9%。
     - `OKR.md:180-185` 命中最高优先级排序：O5/O6 -> O1 -> O7。
     - `docs/process/okr_progress_log.md:18-30` 命中本轮不涨分、O5/O6 当前最低、O1/O7 只保留下一步可涨分证据规则。
2. `rg -n "safe_to_control=true|HIL pass|delivery success" OKR.md docs/process/okr_progress_log.md sprints/2026.06.04_01-02_okr-current-state-rebalance/tech-done.md || true`
   - exit 0。
   - 命中内容位于 `docs/process/okr_progress_log.md` 历史记录，均用于说明“不证明 / 仍未证明 / 不能写成”边界；本轮 `OKR.md` 当前 4.1/5 和 `tech-done.md` 没有把这些词写成正向完成证据。
3. `sed -n '1,220p' sprints/2026.06.04_01-02_okr-current-state-rebalance/tech-done.md`
   - exit 0。
   - 初次输出显示“验证结果”仍是待补齐状态；本段已根据前两条验证命令回填。

## 剩余风险

- 本轮是 OKR 结构/比例口径重平衡，不产生新的真实现场、HIL、production、delivery 或 `safe_to_control` 正向证据。
- O5/O6 仍是当前最低完成度 Objective，下一轮应优先补真实生产 TLS/公网 HTTPS/4G SIM/production DB/queue/OSS/CDN live traffic/真实 phone-browser 材料。
- O1 仍不能把 LiDAR `/scan` smoke 外推为底盘 HIL、ACK、SLAM/Nav2、长稳或安全准入。
- O7 仍不能把 realtime radar/map split 外推为真实 SLAM/map artifact、production operator workflow 或完整上车任务。
