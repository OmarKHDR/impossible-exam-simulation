import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
import json
import numpy as np

class FaceDetectionNode(Node):
    def __init__(self):
        super().__init__('face_detection_node')

        # Parameters from the spec
        self.declare_parameter('scale_factor',  1.1)
        self.declare_parameter('min_neighbors', 5)

        self.scale_factor  = self.get_parameter('scale_factor').value
        self.min_neighbors = self.get_parameter('min_neighbors').value
        self.bridge        = CvBridge()

        # Load Haar Cascade — comes built into OpenCV, no download needed
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

        if self.face_cascade.empty():
            self.get_logger().error('Failed to load Haar Cascade classifier!')
            return

        # Latest frame for display
        self.latest_frame = None
        self.latest_faces = []

        self.subscription = self.create_subscription(
            Image, '/camera_frames', self.face_callback, 10)

        self.publisher_ = self.create_publisher(String, '/face_data', 10)

        # Timer for display window (separate from detection callback)
        self.display_timer = self.create_timer(0.03, self.update_display)

        self.get_logger().info(
            f'Face Detection Node started | '
            f'scale_factor={self.scale_factor} | '
            f'min_neighbors={self.min_neighbors}'
        )

    def face_callback(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor  = self.scale_factor,
            minNeighbors = self.min_neighbors,
            minSize      = (30, 30)
        )

        face_list = []
        if len(faces) > 0:
            for (x, y, w, h) in faces:
                face_list.append({
                    'x': int(x),
                    'y': int(y),
                    'w': int(w),
                    'h': int(h),
                    'center_x': int(x + w // 2),
                    'center_y': int(y + h // 2)
                })

        # Store for display
        self.latest_frame = frame.copy()
        self.latest_faces = face_list

        # Publish face data
        face_msg      = String()
        face_msg.data = json.dumps({
            'face_count': len(face_list),
            'faces':      face_list,
            'face_detected': len(face_list) > 0
        })
        self.publisher_.publish(face_msg)

        self.get_logger().info(
            f'Faces detected: {len(face_list)}'
        )

    def update_display(self):
        if self.latest_frame is None:
            return

        display = self.latest_frame.copy()

        for face in self.latest_faces:
            x, y, w, h = face['x'], face['y'], face['w'], face['h']

            # Draw face rectangle
            cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Draw label background
            label = f"Face ({w}x{h})"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
            cv2.rectangle(display, (x, y - th - 8), (x + tw, y), (0, 255, 0), -1)
            cv2.putText(display, label, (x, y - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)

            # Draw center point
            cx, cy = face['center_x'], face['center_y']
            cv2.circle(display, (cx, cy), 4, (0, 0, 255), -1)

        # Status text
        status = f"Faces: {len(self.latest_faces)}"
        color  = (0, 255, 0) if len(self.latest_faces) > 0 else (0, 0, 255)
        cv2.putText(display, status, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

        # Face detected indicator
        if len(self.latest_faces) > 0:
            cv2.putText(display, 'STUDENT PRESENT', (10, 65),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            cv2.putText(display, 'NO FACE DETECTED', (10, 65),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow('Face Detection', display)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            rclpy.shutdown()

    def destroy_node(self):
        cv2.destroyAllWindows()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = FaceDetectionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
