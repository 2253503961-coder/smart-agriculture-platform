import paho.mqtt.client as mqtt
import json
import time
from threading import Thread

import json
import re

def parse_non_standard_json(data_str):
    # 使用正则表达式给键名添加双引号
    # 匹配类似 "key:" 的模式，其中key是由字母、数字和下划线组成
    standardized = re.sub(r'(\w+):', r'"\1":', data_str)
    try:
        # 解析标准化后的JSON
        return json.loads(standardized)
    except json.JSONDecodeError as e:
        print(f"解析错误: {e}")
        return None

class MQTTSensorClient:
    def __init__(self, broker_host, broker_port, topic, client_id=None):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topic = topic
        self.client_id = client_id or f"sensor-client-{int(time.time())}"
        self.client = mqtt.Client(
            client_id=self.client_id,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )
        self.sensor_data = None
        self.connected = False

        # 设置回调函数
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

    # 关键修复：添加 properties 参数以匹配新版本API
    def _on_connect(self, client, userdata, flags, rc, properties):
        if rc == 0:
            print(f"Connected to MQTT broker {self.broker_host}:{self.broker_port}")
            self.connected = True
            client.subscribe(self.topic)
        else:
            print(f"Failed to connect, return code {rc}")
            self.connected = False

    # 检查并更新 on_message 回调以匹配新版本API
    def _on_message(self, client, userdata, msg, properties=None):
        try:
            payload_str = msg.payload.decode()
            # 先尝试标准 JSON 解析
            try:
                payload = json.loads(payload_str)
            except json.JSONDecodeError:
                # 容错：修复非标准 JSON（键名无引号）
                payload = parse_non_standard_json(payload_str)
                if payload is None:
                    print("Failed to decode MQTT message as JSON")
                    return
            self.sensor_data = payload
            print(f"Received sensor data: {payload}")
        except UnicodeDecodeError:
            print("Failed to decode MQTT message payload")

    # 检查并更新 on_disconnect 回调以匹配新版本API
    def _on_disconnect(self, client, userdata, rc, properties=None):
        print(f"Disconnected from MQTT broker with code {rc}")
        self.connected = False

    def connect(self):
        """连接到MQTT broker"""
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            # 启动网络循环线程
            self.client.loop_start()
            return True
        except Exception as e:
            print(f"MQTT connection error: {str(e)}")
            return False

    def disconnect(self):
        """断开MQTT连接"""
        self.client.loop_stop()
        self.client.disconnect()

    def get_latest_data(self):
        """获取最新的传感器数据"""
        return self.sensor_data.copy() if self.sensor_data else None
