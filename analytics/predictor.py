# analytics/predictor.py
import os
import random
import joblib
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler

# 模型文件存放在项目根目录，基于当前模块位置向上两级定位
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_MODULE_DIR)
MODEL_PATH = os.path.join(_PROJECT_ROOT, 'svm_model.pkl')
SCALER_PATH = os.path.join(_PROJECT_ROOT, 'scaler.pkl')


class GrowthPredictor:
    def __init__(self):
        self.model = None
        self.scaler = None
        self._load_or_train_model()

    def _load_or_train_model(self):
        """加载已保存的模型或训练新模型"""
        try:
            if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
                self.model = joblib.load(MODEL_PATH)
                self.scaler = joblib.load(SCALER_PATH)
            else:
                self._train_model()
        except Exception as e:
            print(f"模型加载失败，重新训练: {str(e)}")
            self._train_model()

    def _train_model(self):
        """训练SVM生长预测模型"""
        # 生成训练数据（300条环境数据+生长率）
        X, y = [], []
        for _ in range(300):
            temp = 15 + random.uniform(0, 20)  # 15-35°C
            hum = 30 + random.uniform(0, 60)  # 30-90%
            soil = 20 + random.uniform(0, 80)  # 20-100%
            light = 300 + random.uniform(0, 1200)  # 300-1500lux
            co2 = 300 + random.uniform(0, 700)  # 300-1000ppm

            # 模拟生长率计算（基于环境因素）
            growth = 50 + (temp - 25) * 1.5 + (hum - 60) * 0.8 + (soil - 50) * 1.2 + (light - 800) * 0.02 + (
                        co2 - 400) * 0.05
            growth = max(30, min(95, growth))  # 限制在30-95%之间

            X.append([temp, hum, soil, light, co2])
            y.append(growth)

        # 数据标准化
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # 训练SVM模型
        self.model = SVR(kernel='rbf', C=100, gamma=0.1, epsilon=0.1)
        self.model.fit(X_scaled, y)

        # 保存模型（使用绝对路径，避免工作目录切换导致文件丢失）
        joblib.dump(self.model, MODEL_PATH)
        joblib.dump(self.scaler, SCALER_PATH)

    def predict_growth(self, sensor_data):
        """基于当前传感器数据预测生长率"""
        if not self.model or not self.scaler:
            return None
        # 提取特征
        features = [
            sensor_data['temperature'],
            sensor_data['humidity'],
            sensor_data['soil_moisture'],
            sensor_data['light_intensity'],
            sensor_data['co2_level']
        ]
        # 标准化并预测
        X_scaled = self.scaler.transform([features])
        prediction = self.model.predict(X_scaled)
        return round(prediction[0], 1)