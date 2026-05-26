# PC Tools Training Labeling Assets Tech Done

## 1. Sprint 声明

- sprint_type: micro
- sprint_id: `2026.05.26_00-35_pc-tools-training-labeling-assets`
- owner: `full-stack-software-engineer`
- closeout time: 2026-05-26 Asia/Shanghai

## 2. 实际改动

- 新增 `pc-tools/workstation/src/server/datasetAssets.ts`，只读扫描 `pc-tools/training/` 与 `pc-tools/labeling/` 的非 Python 数据集/标注资产。
- 扩展 `TrainingLabelingResponse` 为 v2，返回 roots、workspace readiness、asset counts、manifest candidates、image/annotation counts、missing requirements、next actions 和 fail-closed boundary copy。
- 更新 `TrainingLabelingPanel.vue`，显示两个工作区的本地资产清单、缺口与 next actions，并继续显示 `real_pipeline_connected=false`、`proof_status=not_proven`、`primary_actions_enabled=false`。
- 更新 Vitest 覆盖：空目录 `empty_not_connected`、临时 fixture 的 manifest/images/annotations 计数、面板无 pipeline 控制按钮或上传/执行语义、旧 Python gate 语义继续禁止。
- 更新 `docs/product/pc_tools_workstation.md`，同步 Node-native Training/Labeling asset inventory 边界。

## 3. 验证结果

```bash
cd pc-tools/workstation && npm run build
# pass
# vite v7.3.3 built client production bundle; tsc server/app completed
```

```bash
cd pc-tools/workstation && npm run test
# pass
# Test Files 2 passed (2)
# Tests 14 passed (14)
```

```bash
cd pc-tools/workstation && npm run lint
# pass
# eslint . exited 0
```

```powershell
Get-ChildItem -Path pc-tools -Recurse -File -Include *.py | Where-Object { $_.FullName -notmatch '\\workstation\\node_modules\\' }
# pass
# no output
```

## 4. 剩余风险

- 当前能力仍是 `software_proof` 本地只读清单，不证明真实训练流水线、真实标注服务或数据上传链路。
- 不证明数据集 schema、类别体系、图片可读性、标注质量或模型训练可用。
- 不证明真实 ROS2、WAVE ROVER、手机、云端或投放交付成功。
