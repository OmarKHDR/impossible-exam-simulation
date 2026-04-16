import rclpy
from rclpy.node import Node
import json
from std_msgs.msg import Float32, String

class BehaviorAnalysisNode(Node):
    def __init__(self):
        super().__init__('behavior_node')
        self.declare_parameter('attention_threshold', 0.5)
        self.attention_threshold = self.get_parameter('attention_threshold').value

        self.last_depth = 10.0  
        self.last_face = True
        self.last_object = False

        self.create_subscription(Float32, '/depth_data', self.depth_cb, 10)
        self.create_subscription(String, '/face_data', self.face_cb, 10)
        self.create_subscription(String, '/object_data', self.obj_cb, 10)
        
        self.behavior_pub = self.create_publisher(String, '/behavior_state', 10)
        
        self.create_timer(1.0, self.analyze_behavior)
        self.get_logger().info("Behavior Analysis Node Started")

    def depth_cb(self, msg): self.last_depth = msg.data
    def face_cb(self, msg):
        try:
            data = json.loads(msg.data)
            self.last_face = data.get('face_detected', False)
        except json.JSONDecodeError:
            pass
    def obj_cb(self, msg):
        try:
            data = json.loads(msg.data)
            self.last_object = data.get('violation_detected', False)
        except json.JSONDecodeError:
            pass

    def analyze_behavior(self):
        violations = []
        
        # Using simple heuristic since looking away is hard to gauge directly 
        # from just face detection, but we can assume no face = looking away.
        if not self.last_face:
            violations.append("Looking Away")
            
        if self.last_object:
            violations.append("Prohibited Object")
            
        if self.last_depth < 0.5: 
            violations.append("Suspicious Distance")

        if violations:
            state = "VIOLATION: " + ", ".join(violations)
        else:
            state = "Normal"

        msg = String()
        msg.data = state
        self.behavior_pub.publish(msg)
        self.get_logger().info(f"Behavior State: {state}")

def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(BehaviorAnalysisNode())
    rclpy.shutdown()

if __name__ == '__main__':
    main()
