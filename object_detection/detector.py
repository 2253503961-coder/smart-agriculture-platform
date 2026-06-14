# object_detection/detector.py
import cv2
import numpy as np
from threading import Thread, Lock
import time

class ObjectDetector:
    def __init__(self):
        self.net, self.classes, self.output_layers = self._load_yolo_model()
        self.running = False
        self.frame = None
        self.lock = Lock()  # 线程安全锁

    def _load_yolo_model(self):
        """加载YOLO模型及类别"""
        try:
            net = cv2.dnn.readNet("yolov3-tiny.weights", "yolov3-tiny.cfg")
            with open("coco.names", "r") as f:
                classes = [line.strip() for line in f.readlines()]
            layer_names = net.getLayerNames()
            output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
            return net, classes, output_layers
        except Exception as e:
            raise RuntimeError(f"YOLO模型加载失败: {str(e)}")

    def detect_objects(self, img):
        """对单帧图像进行目标检测"""
        height, width, channels = img.shape
        blob = cv2.dnn.blobFromImage(img, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
        self.net.setInput(blob)
        outs = self.net.forward(self.output_layers)

        class_ids = []
        confidences = []
        boxes = []

        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.5:
                    center_x, center_y = int(detection[0]*width), int(detection[1]*height)
                    w, h = int(detection[2]*width), int(detection[3]*height)
                    x, y = int(center_x - w/2), int(center_y - h/2)
                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)

        # 非极大值抑制
        indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
        colors = np.random.uniform(0, 255, size=(len(self.classes), 3))
        for i in range(len(boxes)):
            if i in indexes:
                x, y, w, h = boxes[i]
                label = f"{self.classes[class_ids[i]]}: {confidences[i]:.2f}"
                cv2.rectangle(img, (x, y), (x+w, y+h), colors[class_ids[i]], 2)
                cv2.putText(img, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[class_ids[i]], 2)
        return img

    def _capture_and_process(self):
        """视频捕获与处理线程"""
        cap = cv2.VideoCapture(0)  # 0表示默认摄像头
        if not cap.isOpened():
            raise RuntimeError("无法打开摄像头")

        while self.running:
            ret, img = cap.read()
            if not ret:
                break
            processed_img = self.detect_objects(img)
            with self.lock:
                self.frame = processed_img
        cap.release()

    def start_detection(self):
        """启动目标检测"""
        if not self.running:
            self.running = True
            Thread(target=self._capture_and_process, daemon=True).start()

    def stop_detection(self):
        """停止目标检测"""
        self.running = False

    def generate_frames(self):
        """生成视频流帧（用于Flask响应）"""
        while self.running:
            with self.lock:
                if self.frame is None:
                    continue
                ret, buffer = cv2.imencode('.jpg', self.frame)
                frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.03)  # 控制帧率