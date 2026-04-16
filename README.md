# Distributed Smart Exam Proctoring

Welcome to the Distributed Smart Exam Proctoring repository! This ROS 2-based system is designed to use computer vision and behavioral analysis to enforce exam rules dynamically across a network. 

By splitting the workload across various specialized nodes, the system is lightweight, reactive, and fully distributed.

## ⚙️ Prerequisites & Setup
Before running the system, ensure you have ROS 2 installed. 

### Important NumPy Warning
Due to OpenCV and Ultralytics YOLO backwards-compatibility issues with the latest NumPy 2.x releases, you **must** use NumPy `< 2.0`. Run this command to ensure your environment is set up correctly:

```bash
pip install "numpy<2.0"
```
*(If you are on Ubuntu 24.04 and encountering externally-managed-environment errors, add `--break-system-packages` or use a Python virtual environment).*

## 🛠️ Building the Workspace
To build the nodes, navigate to the root of your workspace (`smart_exam`) and run:
```bash
colcon build --symlink-install
```
*(Using `--symlink-install` allows you to edit the Python files without needing to rebuild the workspace every time!)*

## 🚀 Quick Start: Running the Nodes
Because this is a distributed pub/sub architecture, it's best to start the nodes **Bottom-Up**. This means initializing the final consumers first, then slowly working your way back to the data source (the camera).

Open a new terminal for each of the following components.
**Remember to source the workspace in EVERY terminal before you run a node:**
```bash
source install/setup.bash
```

### 1. System Monitor (The Dashboard)
Passive oversight of the whole system. Let this terminal sit on the side so you can watch everything boot up.
```bash
ros2 run system_monitor system_monitor_node
```

### 2. Alert Action Server (The Enactor)
Idles in the background, waiting to enact physical/external alerts (like emails/texts) if a violation occurs.
```bash
ros2 run alert_action alert_action_node
```

### 3. Rule Evaluation (The Judge)
Processes suspected behaviors and filters them through strict administrative rules.
```bash
ros2 run rule_evaluation rule_evaluation_node
```

### 4. Behavior Analysis (The Integrator)
Collects Face, Object, and Depth data and groups it into behavioral guesses ("e.g., student is looking away").
```bash
ros2 run behavior_analysis behavior_node
```

### 5. Depth Estimation (Feature Extractor)
Extrapolates distance purely from standard camera frames.
```bash
ros2 run depth_estimation depth_node
```

### 6. Object Detection (Feature Extractor)
Scans for prohibited items like cell phones and books around the student.
```bash
ros2 run object_detection_proctoring object_detection_node
```

### 7. Face Detection (Feature Extractor)
Validates that the student is actually in front of the camera using Haar Cascades.
```bash
ros2 run face_detection face_detection_node
```

### 8. Camera Stream (The Source Engine)
Finally, start broadcasting the frames. Once this node runs, the entire network will burst into life!
```bash
ros2 run camera_stream camera_stream_node
```
*(Tip: To test using the included local video instead of a webcam, run:)*
`ros2 run camera_stream camera_stream_node --ros-args -p video_path:="/full/path/to/WIN_20260416_20_22_53_Pro.mp4"`
