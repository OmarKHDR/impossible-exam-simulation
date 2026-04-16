import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer
from std_msgs.msg import String
from proctoring_interfaces.action import AlertAction
import json

class AlertActionNode(Node):
    def __init__(self):
        super().__init__('alert_action_node')
        
        self.declare_parameter('alert_level', 1)
        self.alert_level = self.get_parameter('alert_level').value

        self.subscription = self.create_subscription(
            String,
            '/violation_event',
            self.violation_callback,
            10
        )
        self.publisher = self.create_publisher(String, '/alert_status', 10)
        self.action_server = ActionServer(
            self,
            AlertAction,
            '/alert_action',
            self.execute_callback
        )
        self.get_logger().info('Alert Action Node Started.')

    def violation_callback(self, msg):
        self.get_logger().warn(f'Received Violation Event: {msg.data}. Triggering action logic is handled via Action Server.')
        
        # Publish an automatic status update
        status_msg = String()
        status_msg.data = json.dumps({"status": "Alert pending for violation"})
        self.publisher.publish(status_msg)

    async def execute_callback(self, goal_handle):
        self.get_logger().info('Executing Alert Action Goal...')
        
        alert_msg = goal_handle.request.message
        requested_level = goal_handle.request.alert_level
        
        feedback_msg = AlertAction.Feedback()
        feedback_msg.current_status = f"Evaluating alert level {requested_level}..."
        goal_handle.publish_feedback(feedback_msg)
        
        # Simulate taking action
        import time
        time.sleep(1) # simulate work
        
        feedback_msg.current_status = f"Sending alert: {alert_msg}"
        goal_handle.publish_feedback(feedback_msg)
        time.sleep(1)
        
        goal_handle.succeed()
        
        result = AlertAction.Result()
        result.success = True
        result.final_status = "Alert successfully processed and delivered."
        
        # Publish to alert status topic
        final_msg = String()
        final_msg.data = json.dumps({"status": "Alert Executed", "details": alert_msg})
        self.publisher.publish(final_msg)
        
        return result

def main(args=None):
    rclpy.init(args=args)
    node = AlertActionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
