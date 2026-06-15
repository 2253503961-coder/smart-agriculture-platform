# app.py
import os
from flask import Flask, render_template, jsonify, request, Response
from sensor_data.processor import SensorDataProcessor
from object_detection.detector import ObjectDetector
from device_control.controller import DeviceController
from analytics.predictor import GrowthPredictor

app = Flask(__name__)

# 初始化各模块
detector = ObjectDetector()
device_controller = DeviceController()
growth_predictor = GrowthPredictor()

sensor_processor = SensorDataProcessor(
    mqtt_broker=os.environ.get("MQTT_BROKER", "localhost"),
    mqtt_port=int(os.environ.get("MQTT_PORT", "1883")),
    mqtt_topic=os.environ.get("MQTT_TOPIC", "sensor/data")
)

# 启动传感器更新线程（包含自动决策逻辑）
def sensor_update_callback():
    """传感器数据更新后的回调（MQTT数据更新 → 生长预测 → 自动决策 → 历史归档）"""
    # 预测生长率
    growth_pred = growth_predictor.predict_growth(sensor_processor.get_current_data())
    # 更新传感器数据（包含预测结果）
    sensor_processor.update_sensor_data_from_mqtt(growth_pred)
    # 执行自动决策
    device_controller.intelligent_decision(sensor_processor.get_current_data())
    # 更新历史数据
    if growth_pred:
        sensor_processor.update_historical_data(growth_pred)

sensor_processor.start_update_thread(decision_callback=sensor_update_callback)


# 路由定义
@app.route('/')
def index():
    return render_template('index.html',
                           sensor_data=sensor_processor.get_current_data(),
                           devices=device_controller.get_device_states(),
                           auto_control=device_controller.is_auto_control_enabled())

@app.route('/api/sensor-data')
def get_sensor_data():
    return jsonify(sensor_processor.get_current_data())

@app.route('/api/historical-data')
def get_historical_data():
    return jsonify(sensor_processor.get_historical_data())

@app.route('/api/control-device', methods=['POST'])
def control_device():
    data = request.json
    success = device_controller.set_device_state(data.get('device'), data.get('state'))
    return jsonify({
        'status': 'success' if success else 'error',
        'device': data.get('device'),
        'state': data.get('state')
    })

@app.route('/api/toggle-auto-control', methods=['POST'])
def toggle_auto_control():
    state = device_controller.toggle_auto_control()
    return jsonify({'status': 'success', 'auto_control': state})

@app.route('/api/decision-logs')
def get_decision_logs():
    return jsonify(device_controller.get_decision_logs())

@app.route('/api/growth-prediction')
def get_growth_prediction():
    pred = growth_predictor.predict_growth(sensor_processor.get_current_data())
    return jsonify({'prediction': pred, 'timestamp': sensor_processor.get_current_data()['timestamp']})

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/devices')
def devices_page():
    return render_template('devices.html',
                           devices=device_controller.get_device_states(),
                           auto_control=device_controller.is_auto_control_enabled(),
                           decision_logs=device_controller.get_decision_logs())

@app.route('/analytics')
def analytics():
    prediction = growth_predictor.predict_growth(sensor_processor.get_current_data())
    return render_template('analytics.html', growth_prediction=prediction)

@app.route('/detection')
def detection():
    return render_template('detection.html')

@app.route('/detection/video_feed')
def video_feed():
    return Response(detector.generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/detection/start')
def start_detection():
    detector.start_detection()
    return "Detection started"

@app.route('/detection/stop')
def stop_detection():
    detector.stop_detection()
    return "Detection stopped"

@app.route('/api/mqtt-status')
def mqtt_status():
    return jsonify({
        'connected': sensor_processor.mqtt_connected
    })

if __name__ == '__main__':
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode, host="0.0.0.0", port=int(os.environ.get("FLASK_PORT", "5000")))
