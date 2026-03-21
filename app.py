#!/usr/bin/env python3
"""
火山引擎视频生成中转服务 - 完整版本
"""

from flask import Flask, request, jsonify
import os
import time
import json
from datetime import datetime

app = Flask(__name__)

# 环境变量配置
VOLC_ACCESS_KEY_ID = os.environ.get("VOLC_ACCESS_KEY_ID")
VOLC_SECRET_ACCESS_KEY = os.environ.get("VOLC_SECRET_ACCESS_KEY")
PROXY_AUTH_TOKEN = os.environ.get("PROXY_AUTH_TOKEN")

# 验证环境变量
if not VOLC_ACCESS_KEY_ID or not VOLC_SECRET_ACCESS_KEY:
    print("WARNING: Volcano Engine credentials not set in environment variables")
    print("Please set VOLC_ACCESS_KEY_ID and VOLC_SECRET_ACCESS_KEY")

if not PROXY_AUTH_TOKEN:
    print("WARNING: PROXY_AUTH_TOKEN not set in environment variables")

def authenticate_request():
    """验证请求的Authorization token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return False, "Missing Authorization header"
    
    if not auth_header.startswith("Bearer "):
        return False, "Invalid Authorization format"
    
    token = auth_header[7:]  # 移除"Bearer "前缀
    if token != PROXY_AUTH_TOKEN:
        return False, "Invalid token"
    
    return True, "Authenticated"

def call_volcano_engine(prompt, duration=5):
    """
    调用火山引擎视频生成API
    使用官方Python SDK
    """
    try:
        # 导入火山引擎SDK
        from volcengine.visual.VisualService import VisualService
        
        # 初始化服务
        visual_service = VisualService()
        visual_service.set_ak(VOLC_ACCESS_KEY_ID)
        visual_service.set_sk(VOLC_SECRET_ACCESS_KEY)
        visual_service.set_host('visual.volcengineapi.com')
        
        # 根据duration计算帧数
        # 默认24fps，5秒=120帧，火山引擎要求121帧
        frames = 121 if duration == 5 else 60  # 5秒121帧，其他按比例
        
        # 构建请求参数
        # 使用火山引擎即梦AI-视频生成3.0 API
        params = {
            "req_key": "jimeng_t2v_v30_1080p",
            "prompt": prompt,
            "seed": -1,  # 随机种子
            "frames": frames,
            "aspect_ratio": "9:16"  # 手机竖屏比例
        }
        
        print(f"Calling Volcano Engine API with params: {json.dumps(params, ensure_ascii=False)}")
        
        # 提交任务
        submit_result = visual_service.submit_task(params)
        
        if submit_result.get('code') == 10000:  # 火山引擎成功代码
            task_id = submit_result['data']['task_id']
            print(f"Task submitted successfully: {task_id}")
            
            # 轮询任务状态（最多等待5分钟）
            max_attempts = 30  # 30次 * 10秒 = 5分钟
            for attempt in range(max_attempts):
                time.sleep(10)  # 每10秒检查一次
                
                # 查询任务状态
                status_params = {
                    "req_key": "jimeng_t2v_v30_1080p",
                    "task_id": task_id
                }
                
                status_result = visual_service.get_task_result(status_params)
                
                if status_result.get('code') == 10000:
                    status_data = status_result.get('data', {})
                    status = status_data.get('status')
                    
                    if status == 'done':
                        video_url = status_data.get('video_url')
                        if video_url:
                            return {
                                "success": True,
                                "task_id": task_id,
                                "video_url": video_url,
                                "prompt": prompt,
                                "duration": duration,
                                "status": "completed",
                                "attempts": attempt + 1
                            }
                    elif status == 'failed':
                        return {
                            "success": False,
                            "error": "Video generation failed",
                            "task_id": task_id,
                            "status": "failed"
                        }
                    # 如果状态是running/processing，继续等待
                else:
                    print(f"Status check failed: {status_result.get('message')}")
            
            # 超时
            return {
                "success": False,
                "error": "Task timeout after 5 minutes",
                "task_id": task_id,
                "status": "timeout"
            }
        else:
            error_msg = submit_result.get('message', 'Unknown error')
            return {
                "success": False,
                "error": f"API submission failed: {error_msg}",
                "code": submit_result.get('code')
            }
            
    except ImportError:
        return {
            "success": False,
            "error": "Volcano Engine SDK not installed. Run: pip install volcengine"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Exception in Volcano Engine call: {str(e)}"
        }

# 健康检查接口
@app.route("/", methods=["GET"])
def health_check():
    return jsonify({
        "status": "running",
        "message": "Volcano Video Proxy Service is online",
        "timestamp": datetime.now().isoformat(),
        "volc_configured": bool(VOLC_ACCESS_KEY_ID and VOLC_SECRET_ACCESS_KEY),
        "auth_configured": bool(PROXY_AUTH_TOKEN)
    })

# 视频生成接口
@app.route("/generate_video", methods=["POST"])
def generate_video():
    # 验证token
    auth_ok, auth_message = authenticate_request()
    if not auth_ok:
        return jsonify({
            "success": False,
            "error": auth_message
        }), 401
    
    # 解析请求数据
    data = request.get_json()
    if not data:
        return jsonify({
            "success": False,
            "error": "Missing JSON data"
        }), 400
    
    prompt = data.get("prompt", "")
    duration = data.get("duration", 5)
    
    if not prompt:
        return jsonify({
            "success": False,
            "error": "Missing required parameter: prompt"
        }), 400
    
    # 验证duration
    if duration not in [5, 10]:  # 火山引擎支持5秒或10秒
        duration = 5
    
    print(f"Received video generation request: prompt='{prompt}', duration={duration}")
    
    # 检查火山引擎凭证
    if not VOLC_ACCESS_KEY_ID or not VOLC_SECRET_ACCESS_KEY:
        return jsonify({
            "success": False,
            "error": "Volcano Engine credentials not configured",
            "hint": "Set VOLC_ACCESS_KEY_ID and VOLC_SECRET_ACCESS_KEY environment variables"
        }), 500
    
    # 调用火山引擎
    result = call_volcano_engine(prompt, duration)
    
    if result.get("success"):
        return jsonify({
            "success": True,
            "task_id": result["task_id"],
            "video_url": result["video_url"],
            "prompt": result["prompt"],
            "duration": result["duration"],
            "status": result["status"],
            "generated_at": datetime.now().isoformat()
        })
    else:
        return jsonify({
            "success": False,
            "error": result.get("error", "Unknown error"),
            "code": result.get("code"),
            "task_id": result.get("task_id"),
            "status": result.get("status")
        }), 500

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Volcano Video Proxy Service on port {port}")
    print(f"Volcano Engine configured: {bool(VOLC_ACCESS_KEY_ID and VOLC_SECRET_ACCESS_KEY)}")
    print(f"Auth token configured: {bool(PROXY_AUTH_TOKEN)}")
    
    app.run(host="0.0.0.0", port=port, debug=False)
