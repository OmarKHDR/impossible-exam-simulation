import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from proctoring_interfaces.srv import CheckViolation
import json

class RuleEvaluationNode(Node):
    def __init__(self):
        super().__init__('rule_evaluation_node')
        
        self.declare_parameter('violation_rules', '["Prohibited Object", "Looking Away", "Suspicious Distance"]')
        self.violation_rules = json.loads(self.get_parameter('violation_rules').value)

        self.subscription = self.create_subscription(
            String,
            '/behavior_state',
            self.behavior_callback,
            10
        )
        self.publisher = self.create_publisher(String, '/violation_event', 10)
        self.srv = self.create_service(CheckViolation, '/check_violation', self.check_violation_callback)

        self.current_behavior = "Normal"
        self.get_logger().info('Rule Evaluation Node Started.')

    def behavior_callback(self, msg):
        self.current_behavior = msg.data
        if "VIOLATION" in msg.data:
            # Check against predefined rules
            for rule in self.violation_rules:
                if rule in msg.data:
                    # Confirmed violation
                    violation_msg = String()
                    violation_msg.data = json.dumps({
                        "event": "Confirmed Violation",
                        "details": f"Rule triggered: {rule}",
                        "raw_state": msg.data
                    })
                    self.publisher.publish(violation_msg)
                    self.get_logger().warn(f'Violation Published: {rule}')
                    break

    def check_violation_callback(self, request, response):
        """Service to validate a specific behavior state string against rules."""
        response.is_violation = False
        response.violation_details = "None"
        
        state_to_check = request.behavior_state
        if "VIOLATION" in state_to_check:
            for rule in self.violation_rules:
                if rule in state_to_check:
                    response.is_violation = True
                    response.violation_details = f"Violated rule: {rule}"
                    break
        return response

def main(args=None):
    rclpy.init(args=args)
    node = RuleEvaluationNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
