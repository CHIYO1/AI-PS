from flask import Flask, jsonify, request
from collector import collect_processes
from detector import AnomalyDetector
from process_classifier import ProcessClassifier
from label_manager import LabelManager
from prophet import Prophet
from monitor import ResourceMonitor

import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)

# 1. 初始化各组件
detector = AnomalyDetector()
config_file = os.path.join(os.path.dirname(__file__), "classifier_config.json")
classifier = ProcessClassifier(config_file if os.path.exists(config_file) else None)
label_manager = LabelManager()
monitor = ResourceMonitor()
monitor.start_monitoring()

# 2. 主页
@app.route("/")
def index():
    return "AI-enhanced ps backend running"

# 3. 智能进程采集与异常检测
@app.route("/api/processes")
def get_processes():
    processes = collect_processes()
    analyzed = detector.detect(processes)
    return jsonify(analyzed)

# 4. 预测性资源分析
@app.route("/predict/<int:pid>")
def predict(pid):
    metric_type = request.args.get('metric', 'cpu')
    with monitor.lock:
        df = monitor.history[monitor.history['pid'] == pid].copy()
    if len(df) < 10:
        return jsonify({
            "status": "waiting",
            "message": f"正在积累数据...当前已有点数: {len(df)}/10"
        }), 202
    model_df = df[['ds', metric_type]].rename(columns={metric_type: 'y'})
    try:
        model = Prophet(
            interval_width=0.8,
            daily_seasonality=False,
            weekly_seasonality=False,
            yearly_seasonality=False
        )
        model.fit(model_df)
        future = model.make_future_dataframe(periods=12, freq='5S')
        forecast = model.predict(future)
        results = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(12)
        return jsonify({
            "pid": pid,
            "metric": metric_type,
            "current_val": float(df[metric_type].iloc[-1]),
            "predictions": results.to_dict(orient='records')
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 5. 智能进程分类与标签增强API
@app.route("/api/classify_processes")
def classify_processes_api():
    limit = int(request.args.get('limit', 30))
    # 采集基本进程列表
    processes = []
    for proc in collect_processes(limit=limit):
        processes.append(proc)
    # 分类
    classified = classifier.batch_classify(processes)
    # 合并异常检测和原始属性
    detected = detector.detect(processes)
    detected_dict = {p["pid"]: p for p in detected}
    for proc in classified:
        pid = proc["pid"]
        if pid in detected_dict:
            proc["anomaly"] = detected_dict[pid]["anomaly"]
            proc["score"] = detected_dict[pid]["score"]
            proc["reasons"] = detected_dict[pid]["reasons"]
        # 合入标签
        proc["manual_labels"] = list(label_manager.get_process_labels(pid))
        proc["has_manual_labels"] = bool(proc["manual_labels"])
    return jsonify({
        "success": True,
        "timestamp": datetime.now().isoformat(),
        "processes": classified,
        "total": len(classified)
    })


if __name__ == "__main__":
    app.run(debug=True)