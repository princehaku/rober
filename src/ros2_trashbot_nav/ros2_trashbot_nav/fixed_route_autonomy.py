import os
import json
import time
import yaml
from typing import List, Dict

import cv2
from cv_bridge import CvBridge, CvBridgeError
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from geometry_msgs.msg import PoseStamped

from ros2_trashbot_nav.route_utils import (
    ROUTE_CONTRACT_VERSION,
    FAILURE_CODE_CHECKPOINT_MISSING,
    FAILURE_CODE_NAVIGATION_ABORT,
    FAILURE_CODE_NAVIGATION_INTERRUPTED,
    FAILURE_CODE_NAVIGATION_TIMEOUT,
    FAILURE_CODE_NO_ROUTE,
    build_checkpoint_id,
    build_route_checkpoint_payload,
    build_route_replay_artifact_path,
    build_route_replay_entry,
    build_route_id,
    build_elevator_assist_evidence,
    build_elevator_assist_status,
    load_waypoints_from_csv,
    validate_route_yaml_data,
)
from ros2_trashbot_nav.route_proof_summary import build_route_proof_summary


class FixedRouteAutonomy(Node):
    """Route runner for neighborhood fixed-path trash collection.

    Uses prerecorded route waypoints and optional camera keyframe matching.
    """

    def __init__(self):
        super().__init__('fixed_route_autonomy')
        self.declare_parameter('route_file', '~/.ros/trashbot_maps/fixed_route.yaml')
        self.declare_parameter('camera_topic', '/camera/image_raw')
        self.declare_parameter('enable_visual_gate', True)
        self.declare_parameter('visual_match_threshold', 25)
        self.declare_parameter('keyframe_dir', '~/.ros/trashbot_maps/keyframes')
        self.declare_parameter('dry_run', False)
        self.declare_parameter('debug_status_file', '/tmp/trashbot_fixed_route_status.json')
        self.declare_parameter('evidence_ref', '')
        self.declare_parameter('navigation_timeout_sec', 0.0)

        self.route_file = os.path.expanduser(self.get_parameter('route_file').value)
        self.camera_topic = self.get_parameter('camera_topic').value
        self.enable_visual_gate = bool(self.get_parameter('enable_visual_gate').value)
        self.visual_match_threshold = int(self.get_parameter('visual_match_threshold').value)
        self.keyframe_dir = os.path.expanduser(self.get_parameter('keyframe_dir').value)
        self.dry_run = bool(self.get_parameter('dry_run').value)
        self.debug_status_file = self.get_parameter('debug_status_file').value
        self.route_progress_evidence_ref = str(self.get_parameter('evidence_ref').value).strip() or self.debug_status_file
        self.navigation_timeout_sec = float(self.get_parameter('navigation_timeout_sec').value)
        self.route_id = build_route_id(self.route_file)
        self.source = 'fixed_route'
        self.route_replay_artifact_path = build_route_replay_artifact_path(self.debug_status_file)

        self.bridge = CvBridge()
        self.navigator = None if self.dry_run else BasicNavigator()
        self.orb = cv2.ORB_create(600)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        self.latest_frame = None
        self.current_index = 0
        self.last_error = ''
        self.failure_reason = ''
        self.failure_code = ''
        self.visual_gate_status = 'not_checked'
        self.visual_gate_detail = ''
        self.visual_gate_checkpoint = None
        self.navigation_started_at = None
        self.navigation_elapsed_sec = 0.0
        self.keyframe_preflight = {}
        self.state = 'initializing'
        self.last_transition = ''
        self.last_nav_result = ''
        self.route_poses = self._load_route(self.route_file)
        self.keyframes = self._load_keyframes(len(self.route_poses))

        self.create_subscription(Image, self.camera_topic, self._on_image, 10)
        self.runner_timer = self.create_timer(0.5, self._run_route)
        self.busy = False
        self.task_in_progress = False

        self.get_logger().info(
            f'FixedRouteAutonomy loaded {len(self.route_poses)} poses from {self.route_file}, dry_run={self.dry_run}')
        if not self.route_poses:
            if not self.failure_reason:
                self._set_failure('route contains no waypoints', FAILURE_CODE_NO_ROUTE)
            self._write_debug_status('error')
        else:
            self._write_debug_status('ready')

    def _navigation_error_code(self, result) -> str:
        result_name = str(result).strip().lower()
        if 'timeout' in result_name:
            return FAILURE_CODE_NAVIGATION_TIMEOUT
        if 'cancel' in result_name:
            return FAILURE_CODE_NAVIGATION_INTERRUPTED
        return FAILURE_CODE_NAVIGATION_ABORT

    def _set_navigation_error(self, checkpoint: int, result) -> None:
        code = self._navigation_error_code(result)
        if code == FAILURE_CODE_NAVIGATION_TIMEOUT:
            self._set_failure(f'checkpoint {checkpoint} navigation timeout', code)
            self.last_nav_result = 'timeout'
        elif code == FAILURE_CODE_NAVIGATION_INTERRUPTED:
            self._set_failure(f'checkpoint {checkpoint} navigation interrupted', code)
            self.last_nav_result = 'interrupted'
        else:
            self._set_failure(f'checkpoint {checkpoint} failed', code)
            self.last_nav_result = str(result)

    def _mark_checkpoint_progress(self, state: str, current_target: dict | None = None):
        target_payload = build_route_checkpoint_payload(
            self.route_file,
            self.debug_status_file,
            self.current_index,
            len(self.route_poses),
            route_id=self.route_id,
            failure_code=self.failure_code,
            evidence_ref=self.route_progress_evidence_ref,
        )
        target_payload['route_contract_version'] = ROUTE_CONTRACT_VERSION
        target_payload['source'] = self.source
        target_payload['evidence_ref'] = self.route_progress_evidence_ref
        target_payload['checkpoint_id'] = build_checkpoint_id(
            target_payload['route_id'],
            target_payload['checkpoint'],
        )
        target_payload['current_index'] = target_payload['checkpoint']
        target_payload['target'] = current_target
        if self.navigation_started_at is not None and state in ('running', 'waiting_visual_gate'):
            elapsed = time.monotonic() - self.navigation_started_at
            target_payload['navigation_elapsed_sec'] = max(0.0, round(elapsed, 4))
        else:
            target_payload['navigation_elapsed_sec'] = self.navigation_elapsed_sec
        return target_payload

    def _load_route(self, path: str) -> List[PoseStamped]:
        if not os.path.exists(path):
            self.get_logger().error(f'Route file not found: {path}')
            self._set_failure(f'route file not found: {path}', FAILURE_CODE_NO_ROUTE)
            return []
        try:
            if path.endswith('.csv'):
                return self._load_route_csv(path)
            return self._load_route_yaml(path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            self.get_logger().error(f'Failed loading route file {path}: {exc}')
            self._set_failure(str(exc), FAILURE_CODE_NO_ROUTE)
            return []

    def _load_route_yaml(self, path: str) -> List[PoseStamped]:
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        return [self._row_to_pose(item) for item in validate_route_yaml_data(data, path)]

    def _load_route_csv(self, path: str) -> List[PoseStamped]:
        return [self._row_to_pose(row) for row in load_waypoints_from_csv(path)]

    def _row_to_pose(self, row: Dict) -> PoseStamped:
        if not isinstance(row, dict):
            raise ValueError(f'route waypoint must be a mapping, got {type(row).__name__}')
        pose = PoseStamped()
        pose.header.frame_id = row.get('frame_id') or 'map'
        try:
            pose.pose.position.x = float(row.get('x') or 0.0)
            pose.pose.position.y = float(row.get('y') or 0.0)
            pose.pose.position.z = float(row.get('z') or 0.0)
            pose.pose.orientation.x = float(row.get('qx') or 0.0)
            pose.pose.orientation.y = float(row.get('qy') or 0.0)
            pose.pose.orientation.z = float(row.get('qz') or 0.0)
            pose.pose.orientation.w = float(row.get('qw') or 1.0)
        except ValueError as exc:
            raise ValueError(f'invalid numeric waypoint field: {row}') from exc
        return pose

    def _load_keyframes(self, count: int):
        keyframes = {}
        missing_keyframes = []
        invalid_keyframes = []
        for idx in range(count):
            keyframe_path = os.path.join(self.keyframe_dir, f'{idx:03d}.jpg')
            if not os.path.exists(keyframe_path):
                missing_keyframes.append(idx)
                continue
            img = cv2.imread(keyframe_path)
            if img is None:
                invalid_keyframes.append({'index': idx, 'reason': 'image_unreadable'})
                continue
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            kp, des = self.orb.detectAndCompute(gray, None)
            if des is not None and len(kp) > 0:
                keyframes[idx] = des
            else:
                invalid_keyframes.append({'index': idx, 'reason': 'no_descriptors'})
        self.keyframe_preflight = {
            'enabled': self.enable_visual_gate,
            'total_checkpoints': count,
            'loaded_keyframes': sorted(keyframes.keys()),
            'missing_keyframes': missing_keyframes,
            'invalid_keyframes': invalid_keyframes,
            'route_visual_ready': (
                not self.enable_visual_gate
                or (not missing_keyframes and not invalid_keyframes and len(keyframes) == count)
            ),
        }
        return keyframes

    def _set_failure(self, reason: str, code: str):
        self.failure_reason = str(reason)
        self.last_error = str(reason)
        self.failure_code = str(code)

    def _clear_failure(self):
        self.failure_reason = ''
        self.last_error = ''
        self.failure_code = ''

    def _on_image(self, msg: Image):
        try:
            self.latest_frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except CvBridgeError as exc:
            self.get_logger().warn(f'image convert failed: {exc}')

    def _visual_gate_pass(self, idx: int) -> bool:
        self.visual_gate_checkpoint = idx
        if not self.enable_visual_gate:
            self.visual_gate_status = 'disabled'
            self.visual_gate_detail = 'visual gate disabled by parameter'
            self._clear_failure()
            return True
        if not self.keyframe_preflight.get('route_visual_ready', False):
            self._set_failure(self._keyframe_preflight_error(), FAILURE_CODE_CHECKPOINT_MISSING)
            self.visual_gate_status = 'keyframe_preflight_failed'
            self.visual_gate_detail = self.last_error
            return False
        if idx not in self.keyframes:
            self._set_failure(
                f'visual gate missing keyframe for checkpoint {idx}',
                FAILURE_CODE_CHECKPOINT_MISSING,
            )
            self.visual_gate_status = 'missing_keyframe'
            self.visual_gate_detail = self.last_error
            return False
        if self.latest_frame is None:
            self._set_failure(f'visual gate waiting for camera frame at checkpoint {idx}', '')
            self.visual_gate_status = 'waiting_camera_frame'
            self.visual_gate_detail = self.last_error
            return False
        gray = cv2.cvtColor(self.latest_frame, cv2.COLOR_BGR2GRAY)
        _, live_des = self.orb.detectAndCompute(gray, None)
        if live_des is None:
            self._set_failure(f'visual gate found no live descriptors at checkpoint {idx}', '')
            self.visual_gate_status = 'no_live_descriptors'
            self.visual_gate_detail = self.last_error
            return False
        matches = self.matcher.match(self.keyframes[idx], live_des)
        if len(matches) < self.visual_match_threshold:
            self._set_failure(
                (
                    f'visual gate matched {len(matches)}/{self.visual_match_threshold} '
                    f'features at checkpoint {idx}'
                ),
                '',
            )
            self.visual_gate_status = 'insufficient_matches'
            self.visual_gate_detail = self.last_error
            return False
        self._clear_failure()
        self.visual_gate_status = 'passed'
        self.visual_gate_detail = f'visual gate passed checkpoint {idx}'
        return True

    def _keyframe_preflight_error(self) -> str:
        missing = self.keyframe_preflight.get('missing_keyframes', [])
        invalid = self.keyframe_preflight.get('invalid_keyframes', [])
        parts = []
        if missing:
            parts.append(f'missing keyframes: {missing}')
        if invalid:
            invalid_indexes = [item.get('index') for item in invalid]
            parts.append(f'invalid keyframes: {invalid_indexes}')
        if not parts:
            parts.append('keyframe preflight failed')
        return '; '.join(parts)

    def _run_route(self):
        if not self.route_poses:
            if not self.failure_reason:
                self._set_failure('route contains no waypoints', FAILURE_CODE_NO_ROUTE)
            self._write_debug_status('error')
            return
        if self.current_index >= len(self.route_poses):
            self._write_debug_status('completed')
            return
        if self.task_in_progress:
            self._poll_nav_result()
            return
        if self.busy:
            return
        if not self._visual_gate_pass(self.current_index):
            self._write_debug_status('waiting_visual_gate')
            return
        self.busy = True
        self._write_debug_status('running')
        if self.dry_run:
            self.current_index += 1
            self._clear_failure()
            self.last_nav_result = 'dry_run_checkpoint_passed'
            self.get_logger().info(f'[DRY_RUN] checkpoint passed -> next {self.current_index}')
        else:
            target = self.route_poses[self.current_index]
            target.header.stamp = self.get_clock().now().to_msg()
            self.get_logger().info(f'Navigate to checkpoint #{self.current_index}')
            self.navigation_started_at = time.monotonic()
            self.navigation_elapsed_sec = 0.0
            self.navigator.goToPose(target)
            self.task_in_progress = True
        state = 'completed' if self.current_index >= len(self.route_poses) else 'ready'
        self._write_debug_status(state)
        self.busy = False

    def _poll_nav_result(self):
        if not self.navigator.isTaskComplete():
            if (
                self.navigation_timeout_sec > 0
                and self.navigation_started_at is not None
                and (time.monotonic() - self.navigation_started_at) > self.navigation_timeout_sec
            ):
                self.navigation_elapsed_sec = time.monotonic() - self.navigation_started_at
                checkpoint_for_error = self.current_index
                self._set_failure(
                    f'checkpoint {checkpoint_for_error} navigation timeout',
                    FAILURE_CODE_NAVIGATION_TIMEOUT,
                )
                self.last_nav_result = 'timeout'
                self.navigation_started_at = None
                self.task_in_progress = False
                self._write_debug_status('error')
                return
            return
        result = self.navigator.getResult()
        self.navigation_elapsed_sec = (
            0.0 if self.navigation_started_at is None else time.monotonic() - self.navigation_started_at
        )
        if result == TaskResult.SUCCEEDED:
            self.current_index += 1
            self._clear_failure()
            self.last_nav_result = 'succeeded'
            self.get_logger().info(f'checkpoint reached -> next {self.current_index}')
        else:
            self._set_navigation_error(self.current_index, result)
            self.get_logger().warn(f'checkpoint {self.current_index} failed, retrying')
        self.task_in_progress = False
        self.navigation_started_at = None
        state = 'completed' if self.current_index >= len(self.route_poses) else 'ready'
        self._write_debug_status(state)

    def _write_debug_status(self, state: str):
        if state != self.state:
            self.last_transition = f'{self.state}->{state}'
            self.state = state
        checkpoint = self.current_index
        if checkpoint < 0:
            checkpoint = 0
        elif checkpoint > len(self.route_poses):
            checkpoint = len(self.route_poses)
        current_target = None
        if checkpoint < len(self.route_poses):
            pose = self.route_poses[checkpoint].pose
            current_target = {
                'index': checkpoint,
                'x': pose.position.x,
                'y': pose.position.y,
                'z': pose.position.z,
                'qx': pose.orientation.x,
                'qy': pose.orientation.y,
                'qz': pose.orientation.z,
                'qw': pose.orientation.w,
            }
        route_progress = self._mark_checkpoint_progress(state, current_target=current_target)
        route_proof_summary = build_route_proof_summary(
            total_checkpoints=len(self.route_poses),
            covered_checkpoints=self.current_index,
            gate_status=self.visual_gate_status,
            last_block_reason=self.failure_reason or self.last_error,
        )
        # Fixed-route does not infer elevator semantics by default. The status
        # carries a normalized placeholder so behavior/operator layers can write
        # or display future dry-run evidence without depending on camera OCR.
        elevator_evidence = build_elevator_assist_evidence(
            'door_closed_or_unknown',
            source='fixed_route_debug_status',
            confidence=0.0,
            detail='fixed-route autonomy has no elevator evidence source enabled',
            checkpoint=self.current_index if self.route_poses else None,
        )
        updated_at = time.time()
        route_replay_entry = build_route_replay_entry(
            route_progress=route_progress,
            state=state,
            source=self.source,
            route_contract_version=ROUTE_CONTRACT_VERSION,
            navigation_elapsed_sec=round(self.navigation_elapsed_sec, 4),
            updated_at=updated_at,
        )
        payload = {
            'state': state,
            'mode': 'dry_run' if self.dry_run else 'nav2',
            'route_contract_version': ROUTE_CONTRACT_VERSION,
            'route_file': self.route_file,
            'keyframe_dir': self.keyframe_dir,
            'checkpoint': checkpoint,
            'current_index': self.current_index,
            'target': current_target,
            'current_target': current_target,
            'route_id': route_progress['route_id'],
            'route_file_basename': route_progress['route_file_basename'],
            'checkpoint_id': route_progress['checkpoint_id'],
            'evidence_ref': route_progress['evidence_ref'],
            'source': self.source,
            'route_progress': route_progress,
            'software_proof': {
                'type': 'route_replay',
                'artifact_format': 'jsonl',
                'artifact_path': self.route_replay_artifact_path,
                'evidence_ref': route_progress['evidence_ref'],
                'fields': [
                    'checkpoint',
                    'current_index',
                    'target',
                    'failure_code',
                    'evidence_ref',
                    'checkpoint_id',
                ],
            },
            'total': len(self.route_poses),
            'dry_run': self.dry_run,
            'enable_visual_gate': self.enable_visual_gate,
            'navigation_timeout_sec': self.navigation_timeout_sec,
            'navigation_elapsed_sec': round(self.navigation_elapsed_sec, 4),
            'keyframe_preflight': self.keyframe_preflight,
            'visual_gate_status': self.visual_gate_status,
            'visual_gate_detail': self.visual_gate_detail,
            'visual_gate_checkpoint': self.visual_gate_checkpoint,
            'route_proof_summary': route_proof_summary,
            'elevator_assist': build_elevator_assist_status(
                elevator_evidence,
                enabled=False,
                mode='offline_schema',
            ),
            'last_error': self.last_error,
            'failure_reason': self.failure_reason,
            'failure_code': self.failure_code,
            'last_transition': self.last_transition,
            'last_nav_result': self.last_nav_result,
            'updated_at': updated_at,
        }
        try:
            status_dir = os.path.dirname(self.debug_status_file)
            if status_dir:
                os.makedirs(status_dir, exist_ok=True)
            replay_dir = os.path.dirname(self.route_replay_artifact_path)
            if replay_dir:
                os.makedirs(replay_dir, exist_ok=True)
            with open(self.route_replay_artifact_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(route_replay_entry, ensure_ascii=False) + '\n')
            temp_file = f'{self.debug_status_file}.tmp'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            os.replace(temp_file, self.debug_status_file)
        except Exception as exc:
            self.get_logger().warn(f'Failed writing debug status: {exc}')


def main(args=None):
    rclpy.init(args=args)
    node = FixedRouteAutonomy()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
