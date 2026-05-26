import { promises as fs } from "node:fs";
import path from "node:path";
import { PROOF_FLAGS } from "../shared/contracts";
import type {
  DatasetAssetReadiness,
  DatasetWorkspaceScan,
  TrainingLabelingResponse,
} from "../shared/contracts";
import { displayRoot, LABELING_ROOT, TRAINING_ROOT } from "./paths";

const STRUCTURED_EXTENSIONS = new Set([".json", ".jsonl", ".yaml", ".yml"]);
// 结构化扩展只用于本地清单识别，不触发 schema 校验或训练配置加载。
const IMAGE_EXTENSIONS = new Set([".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"]);
// 图片扩展保持常见格式集合，避免把任意二进制文件计入数据集准备度。
const ANNOTATION_EXTENSIONS = new Set([".xml", ".txt", ".csv", ".ann", ".anno", ".label", ".labels"]);
// 标注扩展偏向轻量文本格式，复杂格式仍通过命名 hint 进入人工复核。
const MANIFEST_NAME_HINTS = ["manifest", "dataset", "data", "coco", "labels", "annotations", "labeling", "training"];
// manifest hint 只做候选发现，避免把任意 JSON 都展示成数据集入口。
const ANNOTATION_NAME_HINTS = ["label", "labels", "annotation", "annotations", "coco", "voc", "yolo"];
// 标注 hint 覆盖常见数据集命名，不声明这些格式已被解析通过。

interface AssetFile {
  // 绝对路径仅在服务端内部递归使用，不进入 API 响应。
  absPath: string;
  // displayPath 统一走仓库相对路径，避免 UI 泄露本机目录结构。
  displayPath: string;
  // extension 提前归一化，后续分类不重复处理大小写。
  extension: string;
  // basename 用于 hint 判断，不读取文件内容做深层推断。
  basename: string;
}

export interface TrainingLabelingRoots {
  // 测试可覆盖根目录，生产 API 默认使用 pc-tools/training。
  trainingRoot?: string;
  // labelingRoot 独立覆盖，便于验证两个工作区的缺口状态。
  labelingRoot?: string;
}

async function listWorkspaceFiles(root: string): Promise<AssetFile[]> {
  // 缺目录按空工作区处理，避免 API 500 被误读成流水线可用。
  try {
    const entries = await fs.readdir(root, { withFileTypes: true });
    const nested = await Promise.all(
      entries.map(async (entry) => {
        const absPath = path.join(root, entry.name);
        if (entry.isDirectory()) {
          // 递归只走目录树，不执行目录中的脚本或工具。
          return listWorkspaceFiles(absPath);
        }
        if (!entry.isFile()) {
          // 非普通文件忽略，避免符号链接或特殊文件扩大扫描边界。
          return [];
        }
        const extension = path.extname(entry.name).toLowerCase();
        return [
          {
            absPath,
            displayPath: displayRoot(absPath),
            extension,
            basename: path.basename(entry.name, extension).toLowerCase(),
          },
        ];
      }),
    );
    return nested.flat().sort((left, right) => left.displayPath.localeCompare(right.displayPath));
  } catch {
    return [];
  }
}

function isPython(file: AssetFile): boolean {
  // Python 文件只计入忽略数量，不进入可展示资产，确保旧 pc-tools Python 不被恢复成入口。
  return file.extension === ".py";
}

function isStructured(file: AssetFile): boolean {
  // 结构化文件是 manifest 候选来源，但存在本身不代表训练配置已可执行。
  return STRUCTURED_EXTENSIONS.has(file.extension);
}

function isImage(file: AssetFile): boolean {
  // 图片只作为本地数据资产计数，不读取像素、不上传、不生成预览缓存。
  return IMAGE_EXTENSIONS.has(file.extension);
}

function isAnnotation(file: AssetFile): boolean {
  // 标注文件既支持常见独立扩展，也支持带 labels/annotations 语义的 JSON/YAML 清单。
  if (ANNOTATION_EXTENSIONS.has(file.extension)) {
    return true;
  }
  return isStructured(file) && ANNOTATION_NAME_HINTS.some((hint) => file.basename.includes(hint));
}

function isManifestCandidate(file: AssetFile): boolean {
  // manifest candidate 是 operator 下一步检查入口，不等同于真实训练配置通过。
  return isStructured(file) && MANIFEST_NAME_HINTS.some((hint) => file.basename.includes(hint));
}

function isRecognizedAsset(file: AssetFile): boolean {
  // 只把明确支持的本地资产纳入计数，README 等说明文件不提升 readiness。
  return isStructured(file) || isImage(file) || isAnnotation(file);
}

function readinessStatus(files: AssetFile[], manifests: AssetFile[], images: AssetFile[], annotations: AssetFile[]): DatasetAssetReadiness {
  // readiness 只描述本地资产清单缺口，所有状态都保留 not_connected 后缀。
  if (files.length === 0) {
    return "empty_not_connected";
  }
  if (manifests.length === 0) {
    return "missing_manifest_not_connected";
  }
  if (images.length === 0) {
    return "missing_images_not_connected";
  }
  if (annotations.length === 0) {
    return "missing_annotations_not_connected";
  }
  return "assets_present_not_connected";
}

function missingRequirements(status: DatasetAssetReadiness): string[] {
  // 缺口文案服务人工准备资产，不触发任何训练或标注动作。
  if (status === "empty_not_connected") {
    return ["asset_files", "manifest_candidate", "image_files", "annotation_files", "real_pipeline_connection"];
  }
  const missing = ["real_pipeline_connection"];
  if (status === "missing_manifest_not_connected") {
    // 缺 manifest 时，即使有图片或标注，也不能称为可接流水线。
    missing.unshift("manifest_candidate");
  }
  if (status === "missing_images_not_connected") {
    // 缺图片时，标注文件只能说明资产零散存在，不能说明数据集闭环。
    missing.unshift("image_files");
  }
  if (status === "missing_annotations_not_connected") {
    // 缺标注时，图片存在也不能外推为标注工作区可用。
    missing.unshift("annotation_files");
  }
  return missing;
}

function nextActions(status: DatasetAssetReadiness): string[] {
  // next actions 是人工整理建议，刻意不包含 start/upload/execute 这类控制语义。
  const common = ["Keep real_pipeline_connected=false until a backend asset contract exists."];
  if (status === "empty_not_connected") {
    return [
      // 空目录的下一步只引导放置资产，不出现启动或上传语义。
      "Place dataset or annotation assets under this workspace for read-only inventory.",
      // manifest/images/annotations 三类缺口都满足后，仍然只进入人工复核。
      "Add a manifest candidate and paired images/annotations before readiness can improve.",
      ...common,
    ];
  }
  if (status === "assets_present_not_connected") {
    // 资产齐备时仍保持 not_connected，因为后端 pipeline 契约尚未存在。
    return ["Review the manifest, image and annotation counts against the future backend contract.", ...common];
  }
  // 部分缺口状态统一给出补资产建议，避免 UI 针对缺口生成动作按钮。
  return ["Add the missing asset class shown above, then refresh the local inventory.", ...common];
}

async function buildWorkspace(name: DatasetWorkspaceScan["name"], root: string): Promise<DatasetWorkspaceScan> {
  const allFiles = await listWorkspaceFiles(root);
  const files = allFiles.filter((file) => !isPython(file) && isRecognizedAsset(file));
  const pythonFiles = allFiles.filter(isPython).length;
  const manifests = files.filter(isManifestCandidate);
  const images = files.filter(isImage);
  const annotations = files.filter(isAnnotation);
  const structuredFiles = files.filter(isStructured);
  const status = readinessStatus(files, manifests, images, annotations);

  // 响应只返回仓库相对路径和计数，不返回文件内容，避免把资产读取升级为训练准备完成。
  return {
    name,
    root: displayRoot(root),
    // status 不使用 ready/success，防止 operator 误解为真实流水线可运行。
    status,
    real_pipeline_connected: false,
    asset_counts: {
      // total_assets 排除了 Python，确保旧工具脚本不会被当成本轮资产。
      total_assets: files.length,
      // structured_files 是候选配置数量，不等同于 manifest 已通过。
      structured_files: structuredFiles.length,
      // manifest_candidates 是人工入口计数，不做自动 schema 判断。
      manifest_candidates: manifests.length,
      // images 只按扩展名计数，不读取像素或生成缓存。
      images: images.length,
      // annotations 只按扩展名和命名 hint 计数，不解析标注质量。
      annotations: annotations.length,
      // ignored_python_files 让 reviewer 知道旧脚本被发现但未纳入资产。
      ignored_python_files: pythonFiles,
    },
    // 路径列表仅返回相对路径，避免 UI 泄露临时目录或用户目录。
    manifest_candidates: manifests.map((file) => file.displayPath),
    image_files: images.map((file) => file.displayPath),
    annotation_files: annotations.map((file) => file.displayPath),
    // 缺口和 next actions 均由服务端产生，前端不自行发明状态。
    missing_requirements: missingRequirements(status),
    next_actions: nextActions(status),
  };
}

export async function buildTrainingLabelingResponse(options: TrainingLabelingRoots = {}): Promise<TrainingLabelingResponse> {
  // Training/Labeling 是 Node-native 只读资产清单入口，不连接训练、标注、上传或机器人控制链路。
  const datasetRoot = options.trainingRoot ?? TRAINING_ROOT;
  const labelingRoot = options.labelingRoot ?? LABELING_ROOT;
  const workspaces = await Promise.all([
    buildWorkspace("dataset", datasetRoot),
    buildWorkspace("labeling", labelingRoot),
  ]);
  const missing = [...new Set(workspaces.flatMap((workspace) => workspace.missing_requirements))];
  const actions = [...new Set(workspaces.flatMap((workspace) => workspace.next_actions))];

  return {
    schema: "trashbot.pc_tools_workstation.training_labeling.v2",
    ...PROOF_FLAGS,
    roots: {
      // roots 让 UI 明确当前扫描的是哪两个本地目录。
      dataset: displayRoot(datasetRoot),
      labeling: displayRoot(labelingRoot),
    },
    // 顶层字段重复声明 false，方便 UI 和测试在不遍历 workspace 时也能 fail-closed。
    real_pipeline_connected: false,
    workspaces,
    // 聚合缺口帮助面板顶部展示总体 readiness，不替代每个 workspace 的细节。
    missing_requirements: missing,
    next_actions: actions,
    // boundary_copy 固化产品边界，避免文案把资产清单升级为真实能力。
    boundary_copy:
      "Dataset and labeling inventory is read-only software proof; it does not run pipelines, transfer data, write files, or prove a real pipeline.",
  };
}
