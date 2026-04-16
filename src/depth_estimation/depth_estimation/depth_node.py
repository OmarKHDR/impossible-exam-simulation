import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Float32
from cv_bridge import CvBridge
import cv2

class DepthEstimationNode(Node):
    def __init__(self):
        super().__init__('depth_node')
        
        self.declare_parameter('depth_threshold', 1.5)
        
        self.subscription = self.create_subscription(
            Image, 
            '/camera_frames', 
            self.listener_callback, 
            10)
        
        self.publisher_ = self.create_publisher(Float32, '/depth_data', 10)
        
        self.br = CvBridge()
        self.get_logger().info('Depth Estimation Node has started')

    def listener_callback(self, data):
        try:
            current_frame = self.br.imgmsg_to_cv2(data)
            
            if current_frame.size > 0:
                estimated_distance = float(current_frame.mean()) / 10.0
            else:
                estimated_distance = 1.2 
            
            msg = Float32()
            msg.data = float(estimated_distance)
            self.publisher_.publish(msg)
            
        except Exception as e:
            self.get_logger().error(f'Failed to process image: {str(e)}')

def main(args=None):
    rclpy.init(args=args)
    node = DepthEstimationNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
