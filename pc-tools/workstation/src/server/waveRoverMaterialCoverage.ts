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

const BASE_CTRL_SOURCE = "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py";
const CONFIG_SOURCE = "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml";
const JSON_CMD_SOURCE = "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h";
const UART_CTRL_SOURCE = "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h";
const UGV_ADVANCE_SOURCE = "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h";

const VENDOR_SOURCES = [
  {
    path: "docs/vendor/VENDOR_INDEX.md",
    fact_ids: ["vendor_index_source_of_truth", "orange_pi_uart_not_proven", "hardware_boundary"],
  },
  {
    path: BASE_CTRL_SOURCE,
    fact_ids: ["rpi_default_serial_example", "json_line_send", "readline_receive"],
  },
  {
    path: CONFIG_SOURCE,
    fact_ids: ["cmd_config_movement_ids", "feedback_interval_config_reference"],
  },
  {
    path: JSON_CMD_SOURCE,
    fact_ids: ["cmd_id_definitions", "feedback_base_info_id"],
  },
  {
    path: UART_CTRL_SOURCE,
    fact_ids: ["newline_json_dispatch", "command_handler_dispatch"],
  },
  {
    path: UGV_ADVANCE_SOURCE,
    fact_ids: ["t1001_feedback_fields", "module_type_conditional_fields"],
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
  'base_ctrl.py writes json.dumps(data)+"\\n" and reads with readline()',
  "uart_ctrl.h serialCtrl() waits for newline before deserializeJson()",
  "config.yaml cmd_config maps cmd_movition_ctrl=1 and cmd_pwm_ctrl=11",
  "json_cmd.h defines FEEDBACK_BASE_INFO=1001",
  "json_cmd.h defines T=1/T=11/T=13/T=130/T=131/T=142/T=143 command IDs",
  "ugv_advance.h baseInfoFeedback() assembles T=1001 fields L/R/r/p/y/v",
  "ugv_advance.h moduleType=1 may change feedback fields and overwrite y with arm lastY",
];

const SERIAL_REFERENCE = {
  vendor_rpi_default_device: "/dev/ttyAMA0",
  vendor_rpi_alternate_device: "/dev/serial0",
  baudrate: 115200,
  orange_pi_device_status: "not_proven",
} as const;

const COMMAND_FACTS = [
  { t: 1, name: "CMD_SPEED_CTRL", source_path: JSON_CMD_SOURCE, hardware_verified: false },
  { t: 11, name: "CMD_PWM_INPUT", source_path: JSON_CMD_SOURCE, hardware_verified: false },
  { t: 13, name: "CMD_ROS_CTRL", source_path: JSON_CMD_SOURCE, hardware_verified: false },
  { t: 130, name: "CMD_BASE_FEEDBACK", source_path: JSON_CMD_SOURCE, hardware_verified: false },
  { t: 131, name: "CMD_BASE_FEEDBACK_FLOW", source_path: JSON_CMD_SOURCE, hardware_verified: false },
  { t: 142, name: "CMD_FEEDBACK_FLOW_INTERVAL", source_path: JSON_CMD_SOURCE, hardware_verified: false },
  { t: 143, name: "CMD_UART_ECHO_MODE", source_path: JSON_CMD_SOURCE, hardware_verified: false },
] as const;

const FEEDBACK_SCHEMA = {
  T1001: {
    base_fields: ["L", "R", "r", "p", "y", "v"],
    module_conditional_fields: ["moduleType=1 adds x/z/b/s/e/t and overwrites y with arm lastY"],
    source_path: UGV_ADVANCE_SOURCE,
  },
} as const;

function materialPresent(names: Set<string>, material: HardwareMaterialItem): boolean {
  // operator 报告允许无扩展名或 .json；其它材料必须精确匹配，避免把相似文件误算为覆盖。
  if (material.id === "operator_hil_report") {
    return names.has("operator_hil_report") || names.has("operator_hil_report.json");
  }
  return names.has(material.required_path);
}

function coverageStatus(present: number): HardwareMaterialStatus {
  // status 只描述本地材料覆盖情况，不使用 pass/success 语义，避免外推为 HIL 或上车成功。
  if (present === REQUIRED_MATERIALS.length) {
    return "material_coverage_complete_software_proof_only";
  }
  if (present > 0) {
    return "material_coverage_partial_software_proof_only";
  }
  return "material_coverage_missing_software_proof_only";
}

async function directFileNames(absDir: string): Promise<string[]> {
  // 缺目录或不可读时按空材料处理，API 继续返回 not_proven，而不是用 500 误导 UI。
  try {
    const entries = await fs.readdir(absDir, { withFileTypes: true });
    return entries.filter((entry) => entry.isFile()).map((entry) => entry.name).sort((left, right) => left.localeCompare(right));
  } catch {
    return [];
  }
}

async function collectMaterialDirs(absDir: string, rootAbsDir: string): Promise<string[]> {
  // 只有含直接文件的 wave_rover_* 子目录才成为材料组，避免把空目录或无关目录展示为证据。
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
  // 顶层只接受 wave_rover_* fixture；其它 evidence group 继续由 Evidence Tools 页面负责。
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

  // 每组只返回相对路径和文件名覆盖，不返回本机绝对路径，也不读取文件内容推断硬件状态。
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
  // 响应只做 Node 只读扫描；不打开串口、不执行 ROS2、不读取真实反馈，也不恢复旧 Python gate。
  const materialDirs = await waveRoverFixtureDirs();
  const groups = await Promise.all(materialDirs.map((dir) => buildGroup(dir)));
  const groupsComplete = groups.filter((group) => group.status === "material_coverage_complete_software_proof_only").length;
  const groupsMissing = groups.filter((group) => group.status === "material_coverage_missing_software_proof_only").length;

  return {
    schema: "trashbot.pc_tools_workstation.hardware_materials.v1",
    ...PROOF_FLAGS,
    fixture_root: displayRoot(EVIDENCE_FIXTURE_ROOT),
    vendor_sources: VENDOR_SOURCES,
    hardware_claim_level: "software_material_coverage",
    serial_reference: SERIAL_REFERENCE,
    command_facts: COMMAND_FACTS,
    feedback_schema: FEEDBACK_SCHEMA,
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
    boundary_copy:
      "coverage is not HIL pass; complete material coverage is still software_proof/not_proven and keeps hardware_connected=false.",
  };
}
