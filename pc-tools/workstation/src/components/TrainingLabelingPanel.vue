<script setup lang="ts">
import type { DatasetWorkspaceScan, TrainingLabelingResponse } from "../shared/contracts";

defineProps<{
  trainingLabeling: TrainingLabelingResponse | null;
}>();

function workspaceTitle(workspace: DatasetWorkspaceScan): string {
  // 标题只区分资产工作区，不暗示存在真实训练或标注流水线。
  return workspace.name === "dataset" ? "Dataset assets" : "Labeling assets";
}

function limitedFiles(files: string[]): string[] {
  // UI 只展示少量路径用于 operator 定位，完整资产仍以计数为主。
  // 这样可以避免大数据集把只读工作站渲染成文件浏览器。
  return files.slice(0, 6);
}
</script>

<template>
  <section class="workspace">
    <div class="section-head">
      <!-- 顶部状态直接展示 not_proven，避免用户把资产清单误读成 pipeline readiness。 -->
      <h2>Dataset/Labeling Assets</h2>
      <span class="pill danger">proof_status=not_proven</span>
    </div>

    <dl class="kv">
      <!-- 这些顶层字段来自 API，不由前端根据文件计数推断。 -->
      <dt>real_pipeline_connected</dt>
      <dd>{{ trainingLabeling?.real_pipeline_connected ?? false }}</dd>
      <!-- primary action 固定关闭，面板不提供任何 pipeline 主动作。 -->
      <dt>primary_actions_enabled</dt>
      <dd>{{ trainingLabeling?.primary_actions_enabled ?? false }}</dd>
      <!-- roots 是本地扫描边界，显示出来便于 operator 放置资产。 -->
      <dt>dataset root</dt>
      <dd>{{ trainingLabeling?.roots.dataset ?? "pc-tools/training" }}</dd>
      <dt>labeling root</dt>
      <dd>{{ trainingLabeling?.roots.labeling ?? "pc-tools/labeling" }}</dd>
      <!-- boundary 文案由后端给出，前端不扩写真实能力声明。 -->
      <dt>boundary</dt>
      <dd>{{ trainingLabeling?.boundary_copy ?? "read-only local inventory; not proven" }}</dd>
    </dl>

    <div class="two-col">
      <!-- real_pipeline_connected=false 直接来自 API，避免 UI 文案升级能力。 -->
      <article v-for="workspace in trainingLabeling?.workspaces" :key="workspace.root">
        <div class="section-head compact-head">
          <!-- workspace 状态保留 not_connected 后缀，防止被误读成可用。 -->
          <h3>{{ workspaceTitle(workspace) }}</h3>
          <span class="pill danger">{{ workspace.status }}</span>
        </div>

        <dl class="kv compact-kv">
          <!-- 计数只解释本地资产形状，不解释数据质量或训练配置。 -->
          <dt>root</dt>
          <dd>{{ workspace.root }}</dd>
          <dt>total assets</dt>
          <dd>{{ workspace.asset_counts.total_assets }}</dd>
          <dt>manifest candidates</dt>
          <dd>{{ workspace.asset_counts.manifest_candidates }}</dd>
          <!-- images/annotations 分开显示，便于 operator 区分数据和标注缺口。 -->
          <dt>images</dt>
          <dd>{{ workspace.asset_counts.images }}</dd>
          <dt>annotations</dt>
          <dd>{{ workspace.asset_counts.annotations }}</dd>
          <!-- Python 只作为忽略计数，避免旧工具脚本再次成为入口。 -->
          <dt>ignored Python files</dt>
          <dd>{{ workspace.asset_counts.ignored_python_files }}</dd>
        </dl>

        <h3>Missing requirements</h3>
        <ul class="dense">
          <!-- 缺口由 API 计算，前端只按只读列表展示。 -->
          <li v-for="item in workspace.missing_requirements" :key="item">{{ item }}</li>
        </ul>

        <h3>Manifest candidates</h3>
        <ul class="dense">
          <!-- 候选 manifest 只是人工检查入口，不是自动执行入口。 -->
          <li v-for="file in limitedFiles(workspace.manifest_candidates)" :key="file">{{ file }}</li>
          <!-- none 明确表达空候选，避免用户误以为列表还在加载。 -->
          <li v-if="workspace.manifest_candidates.length === 0">none</li>
        </ul>

        <h3>Image/annotation samples</h3>
        <ul class="dense">
          <!-- 样例路径帮助定位资产，不生成预览、不读取文件内容。 -->
          <li v-for="file in limitedFiles([...workspace.image_files, ...workspace.annotation_files])" :key="file">
            {{ file }}
          </li>
          <!-- 空样例仍是可解释状态，不升级为前端错误。 -->
          <li v-if="workspace.image_files.length + workspace.annotation_files.length === 0">none</li>
        </ul>

        <h3>Next actions</h3>
        <ul class="dense">
          <!-- next actions 是人工准备建议，不渲染成按钮。 -->
          <li v-for="action in workspace.next_actions" :key="action">{{ action }}</li>
        </ul>
      </article>
    </div>
  </section>
</template>
