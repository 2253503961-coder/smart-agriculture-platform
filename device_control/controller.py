# device_control/controller.py
from datetime import datetime

class DeviceController:
    def __init__(self):
        # 设备初始状态
        self.devices = {
            'irrigation': False,
            'ventilation': False,
            'lighting': False,
            'fertilizer_pump': False
        }
        self.auto_control_enabled = True  # 自动控制开关
        self.decision_logs = []  # 决策日志

    def set_device_state(self, device, state):
        """设置设备状态（手动控制）"""
        if device in self.devices:
            self.devices[device] = state
            return True
        return False

    def toggle_auto_control(self):
        """切换自动控制开关"""
        self.auto_control_enabled = not self.auto_control_enabled
        return self.auto_control_enabled

    def intelligent_decision(self, sensor_data):
        """基于传感器数据的自动决策逻辑"""
        if not self.auto_control_enabled:
            return

        # 灌溉系统控制
        if sensor_data['soil_moisture'] < 40 and not self.devices['irrigation']:
            self._update_device('irrigation', True, f'土壤湿度 {sensor_data["soil_moisture"]}% 低于阈值40%')
        elif sensor_data['soil_moisture'] > 60 and self.devices['irrigation']:
            self._update_device('irrigation', False, f'土壤湿度 {sensor_data["soil_moisture"]}% 高于阈值60%')

        # 通风系统控制
        if sensor_data['temperature'] > 30 and not self.devices['ventilation']:
            self._update_device('ventilation', True, f'温度 {sensor_data["temperature"]}°C 高于阈值30°C')
        elif sensor_data['temperature'] < 20 and self.devices['ventilation']:
            self._update_device('ventilation', False, f'温度 {sensor_data["temperature"]}°C 低于阈值20°C')

        # 照明系统控制
        if sensor_data['light_intensity'] < 500 and not self.devices['lighting']:
            self._update_device('lighting', True, f'光照强度 {sensor_data["light_intensity"]} 低于阈值500')
        elif sensor_data['light_intensity'] > 1000 and self.devices['lighting']:
            self._update_device('lighting', False, f'光照强度 {sensor_data["light_intensity"]} 高于阈值1000')

        # 限制日志数量（只保留最近50条）
        if len(self.decision_logs) > 50:
            self.decision_logs = self.decision_logs[-50:]

    def _update_device(self, device, state, reason):
        """更新设备状态并记录日志"""
        self.devices[device] = state
        action = f'开启{self._get_device_name(device)}' if state else f'关闭{self._get_device_name(device)}'
        self.decision_logs.append({
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'action': action,
            'reason': reason
        })

    def _get_device_name(self, device_code):
        """设备编码转中文名称"""
        device_names = {
            'irrigation': '灌溉系统',
            'ventilation': '通风系统',
            'lighting': '照明系统',
            'fertilizer_pump': '施肥系统'
        }
        return device_names.get(device_code, device_code)

    def get_device_states(self):
        """获取所有设备状态"""
        return self.devices

    def get_decision_logs(self):
        """获取决策日志"""
        return self.decision_logs

    def is_auto_control_enabled(self):
        """获取自动控制状态"""
        return self.auto_control_enabled