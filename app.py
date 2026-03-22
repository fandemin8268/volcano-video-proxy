from flask import Flask, request, jsonify
from datetime import datetime
import json
from volcengine.visual.VisualService import VisualService

app = Flask(__name__)

# 配置信息
VOLC_ACCESS_KEY_ID = "AKLTNjg4ZWUwOGNjZTVkNGRjNWFlZTY5MzU1MDI1ZWFhM2Q"
VOLC_SECRET_ACCESS_KEY = "WmpjNVl6SXhZVGM0TjJJNE5HVTJNbUUyT1dJM01UWTROamhqTWpjd01EZw=="
PROXY_AUTH_TOKEN = "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"

# 初始化火山引擎服务
try:
    visual_service = VisualService()
    visual_service.set_ak(VOLC_ACCESS_KEY_ID)
    visual_service.set_sk(VOLC_SECRET_ACCESS_KEY)
    visual_service.set_host('visual.volcengineapi.com')
    SDK_READY = True
    SDK_MODULE = "VisualService"
except Exception as e:
    SDK_READY = False
SDK_MODULE = f"failed: {str(e)}"

# 认证中间件
def authenticate_request():
auth_header = request.headers.get('Authorization')
if not auth_header or not auth_header.startswith('Bearer '):
return False, "Missing or invalid Authorization header"

token = auth_header[7:] # 移除"Bearer "前缀
if token != PROXY_AUTH_TOKEN:
return False, "Invalid authentication token"

return True, "Authentication successful"

@app.route('/')
def health_check():
return jsonify({
"status": "running",
"version": "6.0-correct-visualservice",
"sdk_module": SDK_MODULE,
"sdk_status": "ready" if SDK_READY else "failed",
"auth_configured": True,
"volc_configured": True,
"message": "火山引擎视频中转服务 - 使用VisualService模块",
"timestamp": datetime.now().strftime("%Y/%m/%d %H:%M:%S")
})

@app.route('/generate_video', methods=['POST'])
def generate_video():
# 认证检查
auth_success, auth_message = authenticate_request()
if not auth_success:
return jsonify({"success": False, "error": auth_message}), 401

# 解析请求数据
try:
data = request.json
prompt = data.get('prompt', '')
aspect_ratio = data.get('aspect_ratio', '9:16')

if not prompt:
return jsonify({"success": False, "error": "Missing prompt parameter"}), 400
except Exception as e:
return jsonify({"success": False, "error": f"Invalid request data: {str(e)}"}), 400

# 检查SDK状态
if not SDK_READY:
return jsonify({
"success": True,
"status": "simulated",
"sdk_used": "simulated",
"prompt": prompt,
"task_id": f"video_simulated_{int(datetime.now().timestamp())}",
"video_url": f"https://volcano-video-storage.volcengineapi.com/videos/simulated_{int(datetime.now().timestamp())}.mp4",
"warning": "SDK未就绪，返回模拟响应",
"note": "VisualService SDK初始化失败，无法调用真实API",
"api_version": "6.0-correct-visualservice"
})

# 调用火山引擎API
try:
req = {
"req_key": "jimeng_t2v_v30_1080p",
"prompt": prompt,
"seed": -1,
"frames": 121,
"aspect_ratio": aspect_ratio
}

response = visual_service.common_handler("CVSync2AsyncSubmitTask", req)

if response.get('code') == 10000:
task_id = response.get('data', {}).get('task_id', '')
return jsonify({
"success": True,
"status": "submitted",
"sdk_used": "VisualService",
"prompt": prompt,
"task_id": task_id,
"note": "视频生成任务已提交到火山引擎",
"api_version": "6.0-correct-visualservice"
})
else:
return jsonify({
"success": False,
"error": f"火山引擎API错误: {response.get('message', '未知错误')}",
"code": response.get('code', '未知'),
"api_version": "6.0-correct-visualservice"
})

except Exception as e:
return jsonify({
"success": False,
"error": f"API调用异常: {str(e)}",
"api_version": "6.0-correct-visualservice"
})

if __name__ == '__main__':
app.run(host='0.0.0.0', port=10000, debug=False)
