import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, ActionClient
from std_msgs.msg import String
from proctoring_interfaces.action import AlertAction
import json
import time

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
        
        self.action_client = ActionClient(self, AlertAction, '/alert_action')
        
        self.get_logger().info('Alert Action Node Started.')

    def violation_callback(self, msg):
        self.get_logger().warn(f'Received Violation Event. Triggering action logic via Action Server.')
        
        # Publish an automatic status update
        status_msg = String()
        status_msg.data = json.dumps({"status": "Alert pending for violation"})
        self.publisher.publish(status_msg)
        
        # Parse violation details to send as message
        try:
            violation_data = json.loads(msg.data)
            alert_text = violation_data.get("details", "Unknown violation")
        except json.JSONDecodeError:
            alert_text = msg.data

        self.send_alert_goal(alert_text)

    def send_alert_goal(self, message):
        goal_msg = AlertAction.Goal()
        goal_msg.message = message
        goal_msg.alert_level = self.alert_level

        if not self.action_client.wait_for_server(timeout_sec=1.0):
            self.get_logger().error('AlertAction server not available!')
            return

        self.get_logger().info(f'Sending goal to /alert_action: {message}')
        self._send_goal_future = self.action_client.send_goal_async(
            goal_msg, feedback_callback=self.feedback_callback)
        self._send_goal_future.add_done_callback(self.goal_response_callback)

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        self.get_logger().info(f'Alert Action Feedback: {feedback.current_status}')

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Goal rejected by Action Server')
            return
        
        self.get_logger().info('Goal accepted by Action Server')
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info(f'Alert Action Result: success={result.success}, final_status="{result.final_status}"')

    async def execute_callback(self, goal_handle):
        self.get_logger().info('Executing Alert Action Goal...')
        
        alert_msg = goal_handle.request.message
        requested_level = goal_handle.request.alert_level
        
        feedback_msg = AlertAction.Feedback()
        feedback_msg.current_status = f"Evaluating alert level {requested_level}..."
        goal_handle.publish_feedback(feedback_msg)
        
        # Simulate taking action
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
