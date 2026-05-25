import { promises as fs } from "node:fs";
import path from "node:path";
import { PROOF_FLAGS } from "../shared/contracts";
import type {
  HardwareMaterialGroup,
  HardwareMaterialItem,
  HardwareMaterialStatus,
  HardwareMaterialsResponse,
} from "../shared/contracts";
import { displayRoot, EVIDENCE_FIXTURE_ROOT } from "./paths";

const REQUIRED_MATERIALS: HardwareMaterialItem[] = [
  {
    id: "feedback_T1001.log",
    required_path: "feedback_T1001.log",
    description: "WAVE ROVER T=1001 base feedback log material.",
  },
  {
    id: "odom_once.jsonl",
    required_path: "odom_once.jsonl",
    description: "One odom sample material exported as JSONL.",
  },
  {
    id: "imu_once.jsonl",
    required_path: "imu_once.jsonl",
    description: "One IMU sample material exported as JSONL.",
  },
  {
    id: "battery_once.jsonl",
    required_path: "battery_once.jsonl",
    description: "One battery sample material exported as JSONL.",
  },
  {
    id: "operator_hil_report",
    required_path: "operator_hil_report or operator_hil_report.json",
    description: "Operator HIL report material; file presence is not HIL pass.",
  },
];

const FAIL_CLOSED_TOKENS = [
  "hil_pass=false",
  "hardware_connected=false",
  "serial_path_not_proven",
  "baudrate_link_not_proven",
  "wheel_direction_not_proven",
  "cmd_ros_ctrl_not_proven_on_chassis",
  "feedback_frequency_not_proven",
  "imu_calibration_not_proven",
  "battery_calibration_not_proven",
  "delivery_success_not_proven",
];

const VENDOR_FACTS_BOUNDED = [
  "UART newline-delimited JSON",
  "base_ctrl.py writes json.dumps(data)+'\\n' and reads readline()",
  "ESP32 serialCtrl() deserializes one JSON command after newline",
  "FEEDBACK_BASE_INFO=1001",
  "T=1/T=13/T=130/T=131/T=142/T=143 command IDs",
  "T=1001 feedback fields include L/R/r/p/y/v",
];

function materialPresent(names: Set<string>, material: HardwareMaterialItem): boolean {
  // operator report 允许无扩展名或 .json；其他材料必须精确匹配，避免误把相似文件算覆盖。
  if (material.id === "operator_hil_report") {
    return names.has("operator_hil_report") || names.has("operator_hil_report.json");
  }
  return names.has(material.required_path);
}

function coverageStatus(present: number): HardwareMaterialStatus {
  // status 只描述 material coverage，不使用 HIL/pass/success 状态词。
  if (present === REQUIRED_MATERIALS.length) {
    return "material_coverage_complete_software_proof_only";
  }
  if (present > 0) {
    return "material_coverage_partial_software_proof_only";
  }
  return "material_coverage_missing_software_proof_only";
}

async function directFileNames(absDir: string): Promise<string[]> {
  // 缺目录或无法读取时按空材料处理，API 仍返回 not_proven 而不是 500。
  try {
    const entries = await fs.readdir(absDir, { withFileTypes: true });
    return entries.filter((entry) => entry.isFile()).map((entry) => entry.name).sort((left, right) => left.localeCompare(right));
  } catch {
    return [];
  }
}

async function collectMaterialDirs(absDir: string, rootAbsDir: string): Promise<string[]> {
  // 只把 wave_rover_* 目录及其含直接文件的子目录作为材料组，避免 node_modules 或无关目录进来。
  const fileNames = await directFileNames(absDir);
  const dirs = fileNames.length > 0 ? [absDir] : [];
  try {
    const entries = await fs.readdir(absDir, { withFileTypes: true });
    const nested = await Promise.all(
      entries
        .filter((entry) => entry.isDirectory())
        .map((entry) => collectMaterialDirs(path.join(absDir, entry.name), rootAbsDir)),
    );
    return [...dirs, ...nested.flat()].sort((left, right) =>
      path.relative(rootAbsDir, left).localeCompare(path.relative(rootAbsDir, right)),
    );
  } catch {
    return dirs;
  }
}

async function waveRoverFixtureDirs(): Promise<string[]> {
  // 顶层只接受 wave_rover_* fixture；其他 evidence group 继续留给 Evidence Tools。
  try {
    const entries = await fs.readdir(EVIDENCE_FIXTURE_ROOT, { withFileTypes: true });
    const roots = entries
      .filter((entry) => entry.isDirectory() && entry.name.startsWith("wave_rover_"))
      .map((entry) => path.join(EVIDENCE_FIXTURE_ROOT, entry.name));
    const groups = await Promise.all(roots.map((root) => collectMaterialDirs(root, EVIDENCE_FIXTURE_ROOT)));
    return groups.flat().sort((left, right) => displayRoot(left).localeCompare(displayRoot(right)));
  } catch {
    return [];
  }
}

async function buildGroup(absDir: string): Promise<HardwareMaterialGroup> {
  const names = new Set(await directFileNames(absDir));
  const presentMaterials = REQUIRED_MATERIALS.filter((material) => materialPresent(names, material)).map((material) => material.id);
  const missingMaterials = REQUIRED_MATERIALS.filter((material) => !materialPresent(names, material)).map((material) => material.id);
  const relativePath = displayRoot(absDir);

  return {
    group: path.relative(EVIDENCE_FIXTURE_ROOT, absDir).split(path.sep).join("/"),
    fixture_relative_path: relativePath,
    present_materials: presentMaterials,
    missing_materials: missingMaterials,
    coverage_counts: {
      present: presentMaterials.length,
      missing: missingMaterials.length,
      required: REQUIRED_MATERIALS.length,
    },
    status: coverageStatus(presentMaterials.length),
  };
}

export async function buildHardwareMaterialsResponse(): Promise<HardwareMaterialsResponse> {
  // 该响应是 Node-native coverage summary，不读取串口、不执行 HIL、不恢复旧 Python gate。
  const materialDirs = await waveRoverFixtureDirs();
  const groups = await Promise.all(materialDirs.map((dir) => buildGroup(dir)));
  const groupsComplete = groups.filter((group) => group.status === "material_coverage_complete_software_proof_only").length;
  const groupsMissing = groups.filter((group) => group.status === "material_coverage_missing_software_proof_only").length;

  return {
    schema: "trashbot.pc_tools_workstation.hardware_materials.v1",
    ...PROOF_FLAGS,
    fixture_root: displayRoot(EVIDENCE_FIXTURE_ROOT),
    required_materials: REQUIRED_MATERIALS,
    groups,
    coverage_summary: {
      groups_total: groups.length,
      groups_complete: groupsComplete,
      groups_partial: groups.length - groupsComplete - groupsMissing,
      groups_missing: groupsMissing,
      required_per_group: REQUIRED_MATERIALS.length,
    },
    vendor_facts_bounded: VENDOR_FACTS_BOUNDED,
    fail_closed_tokens: FAIL_CLOSED_TOKENS,
    not_proven_tokens: FAIL_CLOSED_TOKENS,
    boundary_copy: "coverage is not HIL pass; material coverage is software_proof/not_proven and keeps safe_to_control=false.",
  };
}
