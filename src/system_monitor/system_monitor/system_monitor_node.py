import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Float32
from sensor_msgs.msg import Image

class SystemMonitorNode(Node):
    def __init__(self):
        super().__init__('system_monitor_node')

        self.create_subscription(String, '/face_data', self.face_cb, 10)
        self.create_subscription(String, '/object_data', self.object_cb, 10)
        self.create_subscription(Float32, '/depth_data', self.depth_cb, 10)
        self.create_subscription(String, '/behavior_state', self.behavior_cb, 10)
        self.create_subscription(String, '/violation_event', self.violation_cb, 10)
        self.create_subscription(String, '/alert_status', self.alert_cb, 10)

        self.latest_face = "N/A"
        self.latest_object = "N/A"
        self.latest_depth = 0.0
        self.latest_behavior = "N/A"
        
        self.timer = self.create_timer(2.0, self.display_status)
        self.get_logger().info('System Monitor Node Started')

    def face_cb(self, msg): self.latest_face = msg.data
    def object_cb(self, msg): self.latest_object = msg.data
    def depth_cb(self, msg): self.latest_depth = msg.data
    def behavior_cb(self, msg): self.latest_behavior = msg.data
    def violation_cb(self, msg): self.get_logger().warn(f"[MONITOR] Violation Received: {msg.data}")
    def alert_cb(self, msg): self.get_logger().warn(f"[MONITOR] Alert Action Executed: {msg.data}")

    def display_status(self):
        self.get_logger().info(
            f"\n--- SYSTEM STATUS ---\n"
            f"Face Data: {self.latest_face[:50]}...\n"
            f"Object Data: {self.latest_object[:50]}...\n"
            f"Depth: {self.latest_depth:.2f}\n"
            f"Behavior: {self.latest_behavior}\n"
            f"---------------------"
        )

def main(args=None):
    rclpy.init(args=args)
    node = SystemMonitorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
