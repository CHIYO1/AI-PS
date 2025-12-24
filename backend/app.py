from flask import Flask, jsonify, request
from collector import collect_processes
from detector import AnomalyDetector
from prophet import Prophet
from monitor import ResourceMonitor
import pandas as pd

app = Flask(__name__)
detector = AnomalyDetector()
# 初始化监控器并启动
monitor = ResourceMonitor()
monitor.start_monitoring()

@app.route("/")
def index():
    return "AI-enhanced ps backend running"


@app.route("/api/processes")
def get_processes():
    processes = collect_processes()
    analyzed = detector.detect(processes)
    return jsonify(analyzed)

@app.route("/predict/<int:pid>")
def predict(pid):
    """
    预测性资源分析接口
    用法: /predict/1234?metric=cpu (或 mem)
    """
    metric_type = request.args.get('metric', 'cpu')
    
    with monitor.lock:
        # 获取特定 PID 的历史数据 
        df = monitor.history[monitor.history['pid'] == pid].copy()
    
    # Prophet 至少需要一定数量的数据点才能预测
    if len(df) < 10:
        return jsonify({
            "status": "waiting", 
            "message": f"正在积累数据...当前已有点数: {len(df)}/10"
        }), 202

    # 准备 Prophet 格式的数据
    model_df = df[['ds', metric_type]].rename(columns={metric_type: 'y'})
    
    try:
        # 实例化并拟合模型
        # 关闭所有周期性以加快简单时间序列的预测速度
        model = Prophet(
            interval_width=0.8, 
            daily_seasonality=False, 
            weekly_seasonality=False, 
            yearly_seasonality=False
        )
        model.fit(model_df)
        
        # 预测未来 60 秒（12 个周期，每个周期 5 秒）
        future = model.make_future_dataframe(periods=12, freq='5S')
        forecast = model.predict(future)
        
        # 提取最后 12 条预测结果
        results = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(12)
        
        return jsonify({
            "pid": pid,
            "metric": metric_type,
            "current_val": float(df[metric_type].iloc[-1]),
            "predictions": results.to_dict(orient='records')
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    

if __name__ == "__main__":
    app.run()
