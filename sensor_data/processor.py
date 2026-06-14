# # sensor_data/processor.py
# import random
# from datetime import datetime, timedelta
# import time
# from threading import Thread
#
#
# class SensorDataProcessor:
#     def __init__(self):
#         # 初始化传感器数据
#         self.sensor_data = {
#             'temperature': 25.0,
#             'humidity': 60.0,
#             'soil_moisture': 50.0,
#             'light_intensity': 800.0,
#             'co2_level': 400.0,
#             'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#         }
#         # 初始化历史数据
#         self.historical_data = {
#             'temperature': [],
#             'humidity': [],
#             'soil_moisture': [],
#             'light_intensity': [],
#             'co2_level': [],
#             'growth_rate': []
#         }
#         self._generate_initial_historical_data()
#         self.running = True
#
#     def _generate_initial_historical_data(self):
#         """生成初始24小时历史数据"""
#         end_time = datetime.now()
#         start_time = end_time - timedelta(hours=24)
#         for i in range(24):
#             time_point = (start_time + timedelta(hours=i)).strftime('%H:%M')
#             self.historical_data['temperature'].append(
#                 {'time': time_point, 'value': round(20 + random.uniform(-3, 5) + (i / 24) * 2, 1)})
#             self.historical_data['humidity'].append(
#                 {'time': time_point, 'value': round(50 + random.uniform(-10, 15) - (i / 24) * 5, 1)})
#             self.historical_data['soil_moisture'].append(
#                 {'time': time_point, 'value': round(40 + random.uniform(-5, 10) - (i / 24) * 3, 1)})
#             self.historical_data['light_intensity'].append(
#                 {'time': time_point, 'value': round(500 + random.uniform(-100, 300) + (i % 12 - 6) * 50, 1)})
#             self.historical_data['co2_level'].append(
#                 {'time': time_point, 'value': round(380 + random.uniform(-20, 40) + (i / 24) * 10, 1)})
#             self.historical_data['growth_rate'].append(
#                 {'time': time_point, 'value': round(60 + random.uniform(-5, 5), 1)})
#
#     def update_sensor_data(self, growth_prediction=None):
#         """更新实时传感器数据"""
#         self.sensor_data['temperature'] = round(self.sensor_data['temperature'] + random.uniform(-0.3, 0.3), 1)
#         self.sensor_data['humidity'] = round(self.sensor_data['humidity'] + random.uniform(-0.5, 0.5), 1)
#         self.sensor_data['soil_moisture'] = round(self.sensor_data['soil_moisture'] + random.uniform(-0.8, 0.8),
#                                                   1)  # 降低波动幅度，更接近真实场景
#         self.sensor_data['light_intensity'] = round(self.sensor_data['light_intensity'] + random.uniform(-10, 10), 1)
#         self.sensor_data['co2_level'] = round(self.sensor_data['co2_level'] + random.uniform(-2, 2), 1)
#         self.sensor_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#
#         if growth_prediction:
#             self.sensor_data['growth_prediction'] = growth_prediction
#
#     def update_historical_data(self, growth_rate):
#         """每小时更新历史数据"""
#         current_hour = datetime.now().strftime('%H:00')
#         if not self.historical_data['temperature'] or self.historical_data['temperature'][-1]['time'] != current_hour:
#             for key in ['temperature', 'humidity', 'soil_moisture', 'light_intensity', 'co2_level']:
#                 self.historical_data[key].append({
#                     'time': current_hour,
#                     'value': self.sensor_data[key]
#                 })
#             self.historical_data['growth_rate'].append({
#                 'time': current_hour,
#                 'value': growth_rate
#             })
#             # 保持24小时数据窗口
#             for key in self.historical_data:
#                 if len(self.historical_data[key]) > 24:
#                     self.historical_data[key].pop(0)
#
#     def start_update_thread(self, decision_callback=None):
#         """启动传感器数据更新线程"""
#
#         def update_loop():
#             while self.running:
#                 # 允许外部传入决策回调（如自动控制逻辑）
#                 if decision_callback:
#                     decision_callback()
#                 time.sleep(5)  # 每5秒更新一次
#
#         Thread(target=update_loop, daemon=True).start()
#
#     def get_current_data(self):
#         """获取当前传感器数据"""
#         return self.sensor_data
#
#     def get_historical_data(self):
#         """获取历史数据"""
#         return self.historical_data


# sensor_data/processor.py
import random
from datetime import datetime, timedelta
import time
from threading import Thread
from .mqtt_client import MQTTSensorClient  # 导入MQTT客户端


class SensorDataProcessor:
    def __init__(self, mqtt_broker="localhost", mqtt_port=1883, mqtt_topic="sensor/data"):
        # 初始化MQTT客户端
        self.mqtt_client = MQTTSensorClient(mqtt_broker, mqtt_port, mqtt_topic)
        self.mqtt_connected = self.mqtt_client.connect()

        # 初始化传感器数据
        self.sensor_data = {
            'temperature': 25.0,
            'humidity': 60.0,
            'soil_moisture': 50.0,
            'light_intensity': 800.0,
            'co2_level': 400.0,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        # 初始化历史数据
        self.historical_data = {
            'temperature': [],
            'humidity': [],
            'soil_moisture': [],
            'light_intensity': [],
            'co2_level': [],
            'growth_rate': []
        }
        self._generate_initial_historical_data()
        self.running = True

    def _generate_initial_historical_data(self):
        """生成初始24小时历史数据（首次启动时使用）"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        for i in range(24):
            time_point = (start_time + timedelta(hours=i)).strftime('%H:%M')
            self.historical_data['temperature'].append(
                {'time': time_point, 'value': round(20 + random.uniform(-3, 5) + (i / 24) * 2, 1)})
            self.historical_data['humidity'].append(
                {'time': time_point, 'value': round(50 + random.uniform(-10, 15) - (i / 24) * 5, 1)})
            self.historical_data['soil_moisture'].append(
                {'time': time_point, 'value': round(40 + random.uniform(-5, 10) - (i / 24) * 3, 1)})
            self.historical_data['light_intensity'].append(
                {'time': time_point, 'value': round(500 + random.uniform(-100, 300) + (i % 12 - 6) * 50, 1)})
            self.historical_data['co2_level'].append(
                {'time': time_point, 'value': round(380 + random.uniform(-20, 40) + (i / 24) * 10, 1)})
            self.historical_data['growth_rate'].append(
                {'time': time_point, 'value': round(60 + random.uniform(-5, 5), 1)})

    def update_sensor_data_from_mqtt(self, growth_prediction=None):
        """从MQTT更新传感器数据"""
        if not self.mqtt_connected:
            # 如果MQTT连接断开，尝试重连
            self.mqtt_connected = self.mqtt_client.connect()
            return False

        # 获取MQTT最新数据
        mqtt_data = self.mqtt_client.get_latest_data()
        if mqtt_data:
            # 更新传感器数据（确保字段匹配）
            required_fields = ['temperature', 'humidity', 'soil_moisture', 'light_intensity', 'co2_level']
            if all(field in mqtt_data for field in required_fields):
                self.sensor_data.update({
                    'temperature': float(mqtt_data['temperature']),
                    'humidity': float(mqtt_data['humidity']),
                    'soil_moisture': float(mqtt_data['soil_moisture']),
                    'light_intensity': float(mqtt_data['light_intensity']),
                    'co2_level': float(mqtt_data['co2_level']),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })

                if growth_prediction:
                    self.sensor_data['growth_prediction'] = growth_prediction
                return True
        return False

    def update_historical_data(self, growth_rate):
        """每小时更新历史数据"""
        current_hour = datetime.now().strftime('%H:00')
        if not self.historical_data['temperature'] or self.historical_data['temperature'][-1]['time'] != current_hour:
            for key in ['temperature', 'humidity', 'soil_moisture', 'light_intensity', 'co2_level']:
                self.historical_data[key].append({
                    'time': current_hour,
                    'value': self.sensor_data[key]
                })
            self.historical_data['growth_rate'].append({
                'time': current_hour,
                'value': growth_rate
            })
            # 保持24小时数据窗口
            for key in self.historical_data:
                if len(self.historical_data[key]) > 24:
                    self.historical_data[key].pop(0)

    def start_update_thread(self, decision_callback=None):
        """启动传感器数据更新线程"""

        def update_loop():
            while self.running:
                # 从MQTT更新数据
                self.update_sensor_data_from_mqtt()
                # 执行回调（如自动控制逻辑）
                if decision_callback:
                    decision_callback()
                time.sleep(5)  # 每5秒检查一次新数据

        Thread(target=update_loop, daemon=True).start()

    def get_current_data(self):
        """获取当前传感器数据"""
        return self.sensor_data

    def get_historical_data(self):
        """获取历史数据"""
        return self.historical_data