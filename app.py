from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# 健康检查接口 - 用来确认服务是否正常运行
@app.route("/", methods=["GET"])
def health_check():
    return jsonify({
        "status": "running",
        "message": "Volcano Video Proxy Service is online"
    })

# 视频生成接口 - 占位版本，后续替换为真实逻辑
@app.route("/generate_video", methods=["POST"])
def generate_video():
    data = request.get_json()
    prompt = data.get("prompt", "")
    
    # 占位响应，后续替换
    return jsonify({
        "status": "received",
        "prompt": prompt,
        "message": "This is a placeholder. Replace with actual Volcano Engine SDK call."
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
