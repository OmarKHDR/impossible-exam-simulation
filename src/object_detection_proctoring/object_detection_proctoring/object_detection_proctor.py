import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
from ultralytics import YOLO
import json
import cv2

# Prohibited objects as defined by the exam proctoring spec
PROHIBITED_OBJECTS = [
    'cell phone', 'book', 'laptop',
    'remote', 'keyboard', 'mouse',
    'tablet', 'earphone', 'headphones'
]

class ObjectDetectionProctoringNode(Node):
    def __init__(self):
        super().__init__('object_detection_node')

        self.declare_parameter('confidence_threshold', 0.5)
        self.declare_parameter('model_path', 'yolov8n.pt')

        conf       = self.get_parameter('confidence_threshold').value
        model_path = self.get_parameter('model_path').value

        self.conf   = conf
        self.model  = YOLO(model_path)
        self.bridge = CvBridge()

        # Store latest detections for display
        self.latest_frame      = None
        self.latest_detections = []

        self.subscription = self.create_subscription(
            Image, '/camera_frames', self.detect_callback, 10)

        # Task 3 topic name: /object_data
        self.publisher_ = self.create_publisher(String, '/object_data', 10)

        # Display timer
        self.display_timer = self.create_timer(0.03, self.update_display)

        self.get_logger().info(
            f'Object Detection (Proctoring) Node started | '
            f'Confidence threshold: {conf} | '
            f'Monitoring for: {PROHIBITED_OBJECTS}'
        )

    def detect_callback(self, msg):
        frame   = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        results = self.model(frame, conf=self.conf, verbose=False)

        all_detections        = []
        prohibited_detections = []

        for result in results:
            for box in result.boxes:
                class_name = result.names[int(box.cls)]
                detection  = {
                    'class':      class_name,
                    'confidence': round(float(box.conf), 3),
                    'bbox':       box.xyxy[0].tolist(),
                    'prohibited': class_name.lower() in PROHIBITED_OBJECTS
                }
                all_detections.append(detection)
                if detection['prohibited']:
                    prohibited_detections.append(detection)

        self.latest_frame      = frame.copy()
        self.latest_detections = all_detections

        # Publish only prohibited objects to /object_data
        out_msg      = String()
        out_msg.data = json.dumps({
            'prohibited_count':    len(prohibited_detections),
            'prohibited_objects':  prohibited_detections,
            'violation_detected':  len(prohibited_detections) > 0
        })
        self.publisher_.publish(out_msg)

        if prohibited_detections:
            self.get_logger().warn(
                f'PROHIBITED OBJECTS DETECTED: '
                f'{[d["class"] for d in prohibited_detections]}'
            )
        else:
            self.get_logger().info('No prohibited objects detected.')

    def update_display(self):
        if self.latest_frame is None:
            return

        display = self.latest_frame.copy()

        for det in self.latest_detections:
            x1, y1, x2, y2 = [int(v) for v in det['bbox']]
            label      = f"{det['class']} {det['confidence']:.2f}"

            # Red for prohibited, green for allowed
            color = (0, 0, 255) if det['prohibited'] else (0, 255, 0)

            cv2.rectangle(display, (x1, y1), (x2, y2), color, 2)

            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
            cv2.rectangle(display, (x1, y1 - th - 8), (x1 + tw, y1), color, -1)
            cv2.putText(display, label, (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            # Extra warning label for prohibited objects
            if det['prohibited']:
                cv2.putText(display, 'PROHIBITED!',
                            (x1, y2 + 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        prohibited = [d for d in self.latest_detections if d['prohibited']]

        # Status bar at top
        status = f"Prohibited objects: {len(prohibited)}"
        color  = (0, 0, 255) if prohibited else (0, 255, 0)
        cv2.putText(display, status, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

        if prohibited:
            cv2.putText(display, '!! VIOLATION DETECTED !!', (10, 65),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow('Object Detection - Proctoring', display)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            rclpy.shutdown()

    def destroy_node(self):
        cv2.destroyAllWindows()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = ObjectDetectionProctoringNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
