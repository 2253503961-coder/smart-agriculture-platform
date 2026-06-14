# Smart Agriculture Monitoring Platform (智慧农业监控平台)

An IoT-enabled smart agriculture monitoring and control platform built with Flask. It integrates real-time sensor data via MQTT, SVM-based crop growth prediction, YOLOv3-tiny object detection for pest/field surveillance, and automatic environmental control (irrigation, ventilation, lighting, fertilization).

## Features

- **Real-time sensor dashboard** — displays temperature, humidity, soil moisture, light intensity, and CO₂ levels with live updates
- **MQTT data ingestion** — subscribes to sensor data from IoT edge devices via MQTT protocol
- **24-hour historical charts** — visual trend analysis for all environmental parameters
- **SVM growth prediction** — predicts crop growth rate (%) based on current environmental conditions (SVR with RBF kernel)
- **YOLOv3-tiny object detection** — real-time video stream with bounding-box detection for pest/field surveillance
- **Automatic device control** — rule-based intelligent decisions:
  - Irrigation: triggers when soil moisture < 40%, stops when > 60%
  - Ventilation: triggers when temperature > 30°C, stops when < 20°C
  - Lighting: triggers when light intensity < 500 lux, stops when > 1000 lux
- **Manual override** — toggle auto-control on/off and manually control each device via web UI
- **Decision audit log** — records all automatic actions with timestamps and reasons (last 50 entries)

## Tech Stack

| Layer | Technology |
|---|---|
| Backend Framework | Flask (Python 3.7+) |
| MQTT Client | paho-mqtt |
| Machine Learning | scikit-learn (SVR), joblib |
| Object Detection | OpenCV dnn + YOLOv3-tiny |
| Frontend | Jinja2 templates + Chart.js |
| Data Processing | NumPy, Pandas |
| Model Persistence | joblib (.pkl) |

## Directory Structure

```
智慧物联网-智慧农业监控平台-重构+mqtt/
├── app.py                      # Flask application entry point
├── sensor_data/                # Sensor data acquisition module
│   ├── __init__.py
│   ├── processor.py            # Sensor data processing + historical data
│   └── mqtt_client.py          # MQTT client wrapper
├── device_control/             # Device control module
│   ├── __init__.py
│   └── controller.py           # Intelligent decision engine + manual control
├── object_detection/           # Object detection module
│   ├── __init__.py
│   └── detector.py             # YOLOv3-tiny detection + video stream
├── analytics/                  # Analytics & prediction module
│   ├── __init__.py
│   └── predictor.py            # SVM growth rate predictor
├── templates/                  # Jinja2 HTML templates
│   ├── index.html              # Main dashboard
│   ├── dashboard.html          # Sensor data dashboard
│   ├── devices.html            # Device control panel
│   ├── analytics.html          # Growth prediction analytics
│   ├── detection.html          # Object detection video view
│   └── base.html               # Base template
├── yolov3-tiny.cfg             # YOLOv3-tiny network configuration
├── yolov3-tiny.weights         # YOLOv3-tiny pre-trained weights (35 MB)
├── coco.names                  # COCO class names (80 classes)
├── svm_model.pkl               # Trained SVM growth predictor model
├── scaler.pkl                  # Feature scaler for SVM
├── 智慧农业监控平台实验指导书.docx          # Experiment guide
├── 智慧农业监控平台项目分析与指导书.docx    # Project analysis guide
└── 传感器真实数据获取_mqtt_实验步骤.docx    # MQTT sensor data experiment guide
```

## Installation

### Prerequisites

- Python 3.7+
- OpenCV with DNN module support
- An MQTT broker (e.g., Mosquitto) running on your network

### Setup

```bash
# Clone and enter the project directory
cd 智慧物联网-智慧农业监控平台-重构+mqtt

# Install dependencies
pip install flask paho-mqtt opencv-python scikit-learn joblib numpy

# Download YOLOv3-tiny weights (if not already present)
# wget https://pjreddie.com/media/files/yolov3-tiny.weights
```

## Usage

### 1. Configure MQTT

Edit `app.py` to set your MQTT broker address:

```python
sensor_processor = SensorDataProcessor(
    mqtt_broker="192.168.109.181",  # Replace with your MQTT broker IP
    mqtt_port=1883,
    mqtt_topic="sensor/data"
)
```

### 2. Start the application

```bash
python app.py
```

The web dashboard is available at `http://127.0.0.1:5000/`.

### 3. Web Interface Routes

| Route | Description |
|---|---|
| `/` | Main index page with overview |
| `/dashboard` | Real-time sensor data dashboard |
| `/devices` | Device control panel (manual + auto) |
| `/analytics` | Growth prediction analysis |
| `/detection` | YOLOv3 object detection live stream |

### 4. API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/sensor-data` | GET | Current sensor readings (JSON) |
| `/api/historical-data` | GET | 24-hour historical data (JSON) |
| `/api/control-device` | POST | Toggle a device (`device`, `state`) |
| `/api/toggle-auto-control` | POST | Enable/disable automatic control |
| `/api/decision-logs` | GET | Recent automatic decision logs |
| `/api/growth-prediction` | GET | Current growth rate prediction |
| `/api/mqtt-status` | GET | MQTT connection status |
| `/detection/video_feed` | GET | MJPEG video stream from YOLO |
| `/detection/start` | GET | Start object detection |
| `/detection/stop` | GET | Stop object detection |

### MQTT Data Format

The MQTT client expects JSON messages on the configured topic with the following fields:

```json
{
  "temperature": 26.5,
  "humidity": 62.3,
  "soil_moisture": 45.0,
  "light_intensity": 850.0,
  "co2_level": 420.0
}
```

The client includes a non-standard JSON parser that handles key names without quotes (e.g., `temperature: 26.5`).

## SVM Growth Predictor

The growth prediction model uses a Support Vector Regressor (SVR) with an RBF kernel. It takes five environmental features as input:

- Temperature (°C)
- Humidity (%)
- Soil moisture (%)
- Light intensity (lux)
- CO₂ level (ppm)

If pre-trained models (`svm_model.pkl`, `scaler.pkl`) are not found, the system automatically trains on synthetic data and saves the models for subsequent runs.

## Notes

- **`debug=True`** is enabled in `app.py` — disable this before production deployment.
- The `yolov3-tiny.weights` file is ~35 MB and should be handled with Git LFS for GitHub hosting, or added to `.gitignore` and downloaded separately.
- The `.idea/` directory contains PyCharm IDE configuration and is excluded from version control via `.gitignore`.
- `__pycache__/` directories are excluded via `.gitignore`.
- The MQTT broker IP (`192.168.109.181`) is hardcoded — update to your actual broker address.
- The intelligent decision thresholds (soil moisture 40%/60%, temperature 20°C/30°C, light 500/1000 lux) can be adjusted in `device_control/controller.py`.

## License

This project is provided for educational and research purposes. Adapt MQTT configuration, decision thresholds, and model parameters to your specific agricultural environment before deployment.
