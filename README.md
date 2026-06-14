# 智慧农业监控平台 — 基于物联网与机器学习的精准农业控制系统

## 摘要

本项目构建了一个融合物联网（IoT）、机器学习与计算机视觉的智慧农业监控平台。系统基于 Flask Web 框架，通过 MQTT 协议实时接入边缘传感器数据，利用支持向量回归（SVR）模型预测作物生长率，结合 YOLOv3-tiny 目标检测实现农田虫害与作物状态监控，并基于阈值规则引擎自动控制灌溉、通风、照明、施肥设备。平台通过 Web 仪表盘提供实时数据可视化与手动/自动双模控制能力。

## 研究动机与创新点

精准农业（Precision Agriculture）是农业现代化的核心方向，旨在通过传感器网络和智能算法实现对农业生产环境的精细化管控。现有农业物联网方案普遍面临以下瓶颈：① 数据采集与决策控制分离，缺乏统一的软件架构；② 环境参数与作物生长的关系建模过于简化，多为线性回归；③ 缺乏可交互的实时可视化界面。

本工作的主要创新包括：

1. **多模态感知融合架构**：统一集成 MQTT 传感器数据接入、SVR 生长率预测、YOLOv3-tiny 视觉检测和规则引擎设备控制四大模块，形成感知-预测-决策-执行的闭环
2. **基于 RBF 核 SVR 的非线性生长建模**：使用支持向量回归捕捉温度、湿度、土壤湿度、光照强度、CO₂ 浓度五维环境特征与作物生长率之间的非线性映射关系
3. **滞回控制策略**：为灌溉、通风、照明系统分别设置上下双阈值，避免设备在阈值边界频繁切换，延长执行器寿命
4. **非标准 JSON 解析器**：针对物联网边缘设备常见的非严格 JSON 格式（键名无引号），实现正则表达式容错解析

## 系统架构

```
┌──────────────────────────────────────────────────────┐
│                    Flask Web 前端                      │
│  仪表盘 │ 设备控制 │ 生长分析 │ 目标检测 │ 决策日志     │
└────────────────────────┬─────────────────────────────┘
                         │
┌────────────────────────┴─────────────────────────────┐
│                    核心服务层                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│
│  │ MQTT     │ │ SVR      │ │ YOLOv3   │ │ 规则引擎  ││
│  │ 数据接入  │ │ 生长预测  │ │ 目标检测  │ │ 设备控制  ││
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘│
└────────────────────────┬─────────────────────────────┘
                         │
┌────────────────────────┴─────────────────────────────┐
│                    物理层                              │
│  温度/湿度/土壤/光照/CO₂ 传感器 ←→ 灌溉/通风/照明/施肥  │
└──────────────────────────────────────────────────────┘
```

## 算法原理

### SVR 生长率预测模型

采用支持向量回归（Support Vector Regression, SVR）建模环境参数与作物生长率之间的关系。SVR 的核心思想是在特征空间中寻找一个 $\epsilon$-不敏感管道，使得尽可能多的训练样本落入管道内，同时最小化模型复杂度。

**模型配置**：RBF（高斯）核函数，$C=100$，$\gamma=0.1$，$\epsilon=0.1$。

RBF 核函数定义为：

$$
K(x_i, x_j) = \exp(-\gamma \|x_i - x_j\|^2)
$$

选用 RBF 核的理由：环境参数与生长率之间存在高度非线性关系，RBF 核能将原始五维特征空间映射到无限维希尔伯特空间，理论上可逼近任意连续函数。

**输入特征向量**（5 维）：

$$
x = [T, H, S, L, C]^T
$$

其中 $T$ 为温度（°C）、$H$ 为湿度（%）、$S$ 为土壤湿度（%）、$L$ 为光照强度（lux）、$C$ 为 CO₂ 浓度（ppm）。

**特征标准化**：使用 `StandardScaler` 对训练数据进行 Z-score 标准化：

$$
x' = \frac{x - \mu}{\sigma}
$$

其中 $\mu$ 和 $\sigma$ 分别为各特征的均值和标准差。标准化消除量纲差异，使 RBF 核的距离度量不受特征尺度影响。

**训练数据生成**：当预训练模型（`svm_model.pkl` / `scaler.pkl`）不存在时，系统自动生成 300 条合成数据。生长率模拟公式：

$$
\text{growth} = 50 + 1.5(T - 25) + 0.8(H - 60) + 1.2(S - 50) + 0.02(L - 800) + 0.05(C - 400)
$$

最终限制在 $[30\%, 95\%]$ 区间内。

### YOLOv3-tiny 目标检测

使用 YOLOv3-tiny 轻量级目标检测网络进行实时视频流分析。处理流程：

1. **Blob 预处理**：`cv2.dnn.blobFromImage` 将输入帧缩放至 416×416，均值减法归零，缩放因子 0.00392（1/255）
2. **前向推理**：通过 OpenCV DNN 模块加载 `yolov3-tiny.weights` 和 `yolov3-tiny.cfg`
3. **后处理**：置信度阈值 > 0.5，NMS 阈值 0.5（IoU），NMS 阈值 0.4（score）
4. **可视化**：在检测框上绘制类别标签与置信度分数

### 滞回控制策略

为避免执行器在阈值边界频繁切换（抖动），采用滞回（Hysteresis）控制策略：

| 设备 | 开启条件 | 关闭条件 | 滞回区间 |
|------|---------|---------|---------|
| 灌溉系统 | 土壤湿度 < 40% | 土壤湿度 > 60% | 20% |
| 通风系统 | 温度 > 30°C | 温度 < 20°C | 10°C |
| 照明系统 | 光照 < 500 lux | 光照 > 1000 lux | 500 lux |

所有自动决策记录时间、动作和原因至决策日志（最近 50 条），支持事后审计。

## 数据处理方法

### MQTT 数据接入

`MQTTSensorClient` 封装 paho-mqtt 客户端，支持：

- 非标准 JSON 容错解析：通过正则表达式 `(\w+):` → `"\1":` 为键名添加引号
- 自动重连：连接断开时自动尝试恢复
- 线程安全的网络循环：`loop_start()` 在后台线程运行

预期 MQTT 消息格式：

```json
{
  "temperature": 26.5,
  "humidity": 62.3,
  "soil_moisture": 45.0,
  "light_intensity": 850.0,
  "co2_level": 420.0
}
```

### 历史数据管理

首次启动时生成 24 小时模拟历史数据（含日夜周期性波动），后续每小时从实时数据追加新记录，以滑动窗口维护最近 24 小时。Chart.js 在前端渲染时序曲线。

## 与现有方法的对比

| 特征 | 传统 SCADA | 简单 IoT 平台 | 本平台 |
|------|-----------|-------------|--------|
| 通信协议 | Modbus/OPC | HTTP | MQTT (发布-订阅) |
| 生长预测 | 无 / 线性回归 | 无 | SVR (RBF 核) |
| 目标检测 | 无 | 无 | YOLOv3-tiny |
| 控制策略 | 单阈值 | 单阈值 | 滞回双阈值 |
| 可视化 | 桌面端 | 移动端 | Web 响应式 |
| 决策审计 | 有 | 无 | 有（最近 50 条） |
| 架构解耦 | 低 | 中 | 高（模块化） |

## 技术栈

| 层次 | 技术选型 |
|------|---------|
| 后端框架 | Flask (Python 3.7+) |
| MQTT 客户端 | paho-mqtt |
| 机器学习 | scikit-learn (SVR), joblib |
| 目标检测 | OpenCV dnn + YOLOv3-tiny |
| 前端 | Jinja2 模板 + Chart.js |
| 数据处理 | NumPy |
| 模型持久化 | joblib (.pkl) |

## 目录结构

```
智慧农业监控平台/
├── app.py                        # Flask 应用入口（路由注册 + 模块初始化）
├── sensor_data/                  # 传感器数据采集模块
│   ├── __init__.py
│   ├── processor.py              # 传感器数据处理 + 历史数据 + MQTT 集成
│   └── mqtt_client.py            # MQTT 客户端封装（含非标准 JSON 解析器）
├── device_control/               # 设备控制模块
│   ├── __init__.py
│   └── controller.py             # 滞回规则引擎 + 手动控制 + 决策日志
├── object_detection/             # 目标检测模块
│   ├── __init__.py
│   └── detector.py               # YOLOv3-tiny 检测 + MJPEG 视频流
├── analytics/                    # 预测分析模块
│   ├── __init__.py
│   └── predictor.py              # SVR (RBF) 生长率预测器
├── templates/                    # Jinja2 HTML 模板
│   ├── base.html                 # 基础模板
│   ├── index.html                # 主页概览
│   ├── dashboard.html            # 传感器实时仪表盘
│   ├── devices.html              # 设备控制面板
│   ├── analytics.html            # 生长预测分析
│   └── detection.html            # 目标检测视频视图
├── yolov3-tiny.cfg               # YOLOv3-tiny 网络配置
├── yolov3-tiny.weights           # YOLOv3-tiny 预训练权重 (35 MB)
├── coco.names                    # COCO 80 类类别名称
├── svm_model.pkl                 # 训练好的 SVR 模型
├── scaler.pkl                    # 特征标准化器
├── requirements.txt              # Python 依赖
└── .gitignore
```

## 依赖安装

```bash
pip install flask paho-mqtt opencv-python scikit-learn joblib numpy
```

YOLOv3-tiny 权重文件（`yolov3-tiny.weights`, 35MB）需单独下载：

```
wget https://pjreddie.com/media/files/yolov3-tiny.weights
```

## 使用流程

### 1. 配置 MQTT

在 `app.py` 中设置 MQTT Broker 地址：

```python
sensor_processor = SensorDataProcessor(
    mqtt_broker="192.168.109.181",  # 替换为实际 IP
    mqtt_port=1883,
    mqtt_topic="sensor/data"
)
```

### 2. 启动应用

```bash
python app.py
```

Web 仪表盘访问地址：`http://127.0.0.1:5000/`。

### 3. Web 界面路由

| 路由 | 功能 |
|------|------|
| `/` | 主页概览 |
| `/dashboard` | 实时传感器数据仪表盘 |
| `/devices` | 设备控制面板（手动/自动切换） |
| `/analytics` | 生长率预测分析 |
| `/detection` | YOLOv3-tiny 实时目标检测 |

### 4. API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/sensor-data` | GET | 当前传感器读数（JSON） |
| `/api/historical-data` | GET | 24 小时历史数据（JSON） |
| `/api/control-device` | POST | 手动控制设备（`device`, `state`） |
| `/api/toggle-auto-control` | POST | 切换自动/手动控制模式 |
| `/api/decision-logs` | GET | 最近自动决策日志 |
| `/api/growth-prediction` | GET | 当前生长率预测值 |
| `/api/mqtt-status` | GET | MQTT 连接状态 |
| `/detection/video_feed` | GET | MJPEG 视频流 |
| `/detection/start` | GET | 启动目标检测 |
| `/detection/stop` | GET | 停止目标检测 |

## 注意事项

- `debug=True` 在生产环境应关闭，避免性能下降和安全风险
- `yolov3-tiny.weights` 约 35MB，已加入 `.gitignore`，需单独下载
- MQTT Broker IP（`192.168.109.181`）为硬编码默认值，部署时务必修改
- SVR 预测模型在首次启动时使用合成数据自动训练，建议接入真实传感器数据后重新训练
- 滞回阈值可在 `device_control/controller.py` 中按实际需求调整

## 许可证

本项目仅供学术研究与教育用途。部署前请根据实际农业环境调整 MQTT 配置、决策阈值和模型参数。
