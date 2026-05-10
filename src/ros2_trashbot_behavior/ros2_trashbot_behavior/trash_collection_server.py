import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer
from ros2_trashbot_interfaces.action import TrashCollection


LEGACY_ERROR_CODE = 'legacy_server_quarantined'
LEGACY_ERROR_MESSAGE = (
    'legacy_trash_collection_server is quarantined because it was a sleep-demo '
    'pipeline. Use task_orchestrator for /trashbot/collect_trash.'
)


class TrashCollectionServer(Node):
    """Compatibility action server that refuses the legacy sleep-demo path."""

    def __init__(self):
        super().__init__('trash_collection_server')

        self.action_server = ActionServer(
            self, TrashCollection, '/trashbot/collect_trash',
            self._execute_callback)

        self.get_logger().warn(
            'legacy_trash_collection_server is quarantined; '
            'use task_orchestrator for /trashbot/collect_trash'
        )

    async def _execute_callback(self, goal_handle):
        """Abort legacy goals instead of reporting fake collection success."""
        feedback = TrashCollection.Feedback()
        result = TrashCollection.Result()

        target = goal_handle.request.trash_goal_frame
        self.get_logger().error(
            f'Rejecting legacy trash collection goal for {target!r}: '
            f'{LEGACY_ERROR_MESSAGE}'
        )

        feedback.status = 0
        feedback.percent_complete = 0.0
        feedback.current_step = 'legacy_server_quarantined'
        feedback.state = 'error'
        feedback.event = LEGACY_ERROR_CODE
        feedback.message = LEGACY_ERROR_MESSAGE
        goal_handle.publish_feedback(feedback)

        result.success = False
        result.items_collected = 0
        result.items_disposed = 0
        result.total_duration_sec = 0.0
        result.error_code = LEGACY_ERROR_CODE
        result.error_message = LEGACY_ERROR_MESSAGE
        result.final_state = 'error'
        result.task_record_path = ''

        goal_handle.abort()
        return result


def main(args=None):
    rclpy.init(args=args)
    node = TrashCollectionServer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
