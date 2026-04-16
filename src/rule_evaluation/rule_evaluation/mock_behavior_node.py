import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class MockBehaviorNode(Node):
    def __init__(self):
        super().__init__('mock_behavior_node')
        
        # Publish to the topic that rule_evaluation_node expects
        self.publisher = self.create_publisher(String, '/behavior_state', 10)
        
        # We will cycle through different simulated behaviors
        self.behaviors = [
            "Normal",
            "Normal",
            "VIOLATION: Looking Away",
            "Normal",
            "VIOLATION: Prohibited Object",
            "Normal",
            "Normal",
            "VIOLATION: Suspicious Distance",
        ]
        self.current_idx = 0
        
        # Timer to publish mock states every 2 seconds
        self.timer = self.create_timer(2.0, self.publish_mock_data)
        self.get_logger().info('Mock Behavior Node Started. Pumping fake behavior data...')

    def publish_mock_data(self):
        behavior = self.behaviors[self.current_idx]
        msg = String()
        msg.data = behavior
        self.publisher.publish(msg)
        self.get_logger().info(f'Published mock behavior: {behavior}')
        
        self.current_idx = (self.current_idx + 1) % len(self.behaviors)

def main(args=None):
    rclpy.init(args=args)
    node = MockBehaviorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
