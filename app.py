#!/usr/bin/env python3
"""
火山引擎视频生成中转服务 - 完整调试版本 4.2-debug-logging
包含详细的认证和请求调试日志
"""
from flask import Flask, request, jsonify
import os
import time
import json
import sys
from datetime import datetime

app = Flask(__name__)

# === 硬编码配置 ===
VOLC_ACCESS_KEY_ID = "AKLTNjg4ZWUwOGNjZTVkNGRjNWFlZTY5MzU1MDI1ZWFhM2Q"
VOLC_SECRET_ACCESS_KEY = "WmpjNVl6SXhZVGM0TjJJNE5HVTJNbUUyT1dJM01UWTROamhqTWpjd01EZw=="
VOLC_REGION = "cn-north-1"
PROXY_AUTH_TOKEN = "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"

print("=" * 60)
print("火山引擎中转服务 - 完整调试版本 4.2-debug-logging")
print(f"Access Key: {VOLC_ACCESS_KEY_ID[:10]}...")
print(f"Region: {VOLC_REGION}")
print(f"Auth Token: {PROXY_AUTH_TOKEN[:10]}...")
print("=" * 60)

# 初始化火山引擎客户端
sdk_ready = False
visual_service = None

try:
    from volcengine.visual.VisualService import VisualService
    print(f"[SDK] 成功导入VisualService")
    
    visual_service = VisualService()
    print(f"[SDK] VisualService对象创建成功")
    
    # 设置认证信息
    visual_service.set_ak(VOLC_ACCESS_KEY_ID)
    visual_service.set_sk(VOLC_SECRET_ACCESS_KEY)
    
    # 调试：查看可用方法
    methods = [m for m in dir(visual_service) if not m.startswith('_')]
    print(f"[SDK] VisualService可用方法 ({len(methods)}个): {methods[:10]}...")
    
    # 尝试设置host（如果方法存在）
    if hasattr(visual_service, 'set_host'):
        visual_service.set_host("visual.volcengineapi.com")
        print(f"[SDK] 使用set_host设置端点")
    elif hasattr(visual_service, 'set_endpoint'):
        visual_service.set_endpoint("visual.volcengineapi.com")
        print(f"[SDK] 使用set_endpoint设置端点")
    else:
        print(f"[SDK] 警告: 未找到set_host或set_endpoint方法")
    
    # 尝试设置region（如果方法存在）
    if hasattr(visual_service, 'set_region'):
        visual_service.set_region(VOLC_REGION)
        print(f"[SDK] 使用set_region设置区域")
    elif hasattr(visual_service, 'region'):
        visual_service.region = VOLC_REGION
        print(f"[SDK] 直接设置region属性")
    else:
        print(f"[SDK] 警告: 未找到set_region方法或region属性")
        print(f"[SDK] 将使用默认区域配置")
    
    sdk_ready = True
    print(f"[SDK] 火山引擎VisualService初始化成功")
    
except Exception as e:
    print(f"[SDK] VisualService初始化错误: {str(e)}")
    import traceback
    traceback.print_exc()
    sdk_ready = False

def authenticate_request():
    """验证请求的Authorization token - 详细调试版本"""
    auth_header = request.headers.get("Authorization")
    
    print(f"[认证] 收到Authorization头: {auth_header}")
    
    if not auth_header:
        print("[认证] 失败: 缺少Authorization头")
        return False, "Missing Authorization header"
    
    if not auth_header.startswith("Bearer "):
        print(f"[认证] 失败: Authorization格式错误 (应该以'Bearer '开头)")
        print(f"[认证] 实际收到的头: '{auth_header}'")
        return False, "Invalid Authorization format"
    
    token = auth_header[7:]  # 移除"Bearer "前缀
    expected_token = PROXY_AUTH_TOKEN
    
    print(f"[认证] 收到的token (前10位): {token[:10]}...")
    print(f"[认证] 收到的token长度: {len(token)}")
    print(f"[认证] 期望的token (前10位): {expected_token[:10]}...")
    print(f"[认证] 期望的token长度: {len(expected_token)}")
    
    if token != expected_token:
        print(f"[认证] 失败: token不匹配")
        print(f"[认证] 收到的完整token: {token}")
        print(f"[认证] 期望的完整token: {expected_token}")
        return False, "Invalid token"
    
    print("[认证] 成功: token验证通过")
    return True, "Authenticated"

def call_volcano_engine_safe(prompt, duration=5):
    """
    安全调用火山引擎API
    如果SDK有问题，返回模拟响应
    """
    try:
        if not sdk_ready or visual_service is None:
            raise ImportError("火山引擎SDK未初始化成功")
        
        print(f"[火山引擎] 使用VisualService调用API: {prompt}")
        
        # 构建请求参数
        req = {
            "req_key": "jimeng_t2v_v30_1080p",
            "prompt": prompt,
            "video_duration": duration,
            "aspect_ratio": "9:16",
            "resolution": "1080p",
            "seed": int(time.time() % 1000000)
        }
        
        print(f"[火山引擎] 请求参数: {json.dumps(req, ensure_ascii=False)}")
        
        # 查看可用的API方法
        api_methods = [m for m in dir(visual_service) if 'video' in m.lower() or 'generation' in m.lower()]
        print(f"[火山引擎] 可能的视频生成方法: {api_methods}")
        
        # 尝试调用API
        if hasattr(visual_service, 'video_generation'):
            print(f"[火山引擎] 使用video_generation方法")
            response = visual_service.video_generation(req)
        elif hasattr(visual_service, 'VideoGeneration'):
            print(f"[火山引擎] 使用VideoGeneration方法")
            response = visual_service.VideoGeneration(req)
        elif hasattr(visual_service, 'generate_video'):
            print(f"[火山引擎] 使用generate_video方法")
            response = visual_service.generate_video(req)
        else:
            raise AttributeError("未找到视频生成方法")
        
        print(f"[火山引擎] API响应类型: {type(response)}")
        print(f"[火山引擎] API响应: {response}")
        
        # 处理响应
        if isinstance(response, dict) and response.get("status_code") == 10000:
            task_id = response.get("data", {}).get("task_id")
            video_url = response.get("data", {}).get("video_url", "")
            
            if not video_url:
                video_url = f"https://volcano-video-storage.volcengineapi.com/videos/{task_id}.mp4"
            
            return {
                "success": True,
                "task_id": task_id,
                "video_url": video_url,
                "status": "submitted",
                "api_response": response
            }
        else:
            return {
                "success": True,
                "task_id": f"video_{int(time.time())}_{hash(prompt) % 10000:04d}",
                "video_url": f"https://volcano-video-storage.volcengineapi.com/videos/video_{int(time.time())}.mp4",
                "status": "simulated",
                "note": f"API响应格式未知，返回模拟响应。原始响应: {response}",
                "warning": "这是模拟响应，需要检查API方法"
            }
            
    except Exception as e:
        print(f"[异常] 视频生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 返回模拟响应
        task_id = f"video_{int(time.time())}_{hash(prompt) % 10000:04d}"
        video_url = f"https://volcano-video-storage.volcengineapi.com/videos/{task_id}.mp4"
        
        return {
            "success": True,
            "task_id": task_id,
            "video_url": video_url,
            "status": "simulated",
            "note": f"SDK调用失败: {str(e)}",
            "warning": "这是模拟响应"
        }

@app.route('/')
def health_check():
    """健康检查端点"""
    return jsonify({
        "status": "running",
        "message": "Volcano Video Proxy Service is online",
        "version": "4.2-debug-logging",
        "timestamp": datetime.now().isoformat(),
        "auth_configured": True,
        "volc_configured": True,
        "sdk_status": "ready" if sdk_ready else "failed",
        "sdk_module": "VisualService" if sdk_ready else "none",
        "note": "包含详细的调试日志，用于诊断400错误"
    })

@app.route('/generate_video', methods=['POST'])
def generate_video():
    """生成视频 - 详细调试版本"""
    
    print(f"\n{'='*60}")
    print(f"[API] 收到POST请求到 /generate_video")
    print(f"[API] 请求时间: {datetime.now().isoformat()}")
    print(f"[API] 客户端IP: {request.remote_addr}")
    print(f"[API] 请求方法: {request.method}")
    print(f"[API] 请求路径: {request.path}")
    
    # 打印所有请求头
    print(f"[API] 请求头:")
    for key, value in request.headers.items():
        print(f"  {key}: {value}")
    
    # 1. 验证Bearer Token
    print(f"\n[API] 开始认证验证...")
    auth_success, auth_message = authenticate_request()
    if not auth_success:
        print(f"[API] 认证失败: {auth_message}")
        return jsonify({
            "success": False,
            "error": auth_message,
            "code": "AUTH_REQUIRED",
            "timestamp": datetime.now().isoformat()
        }), 401
    
    print(f"[API] 认证成功")
    
    # 2. 验证请求数据
    print(f"\n[API] 检查请求是否为JSON...")
    print(f"[API] Content-Type头: {request.headers.get('Content-Type')}")
    print(f"[API] 请求数据长度: {len(request.data) if request.data else 0}字节")
    
    if request.data:
        print(f"[API] 原始请求数据 (前500字符):")
        raw_data = request.data.decode('utf-8', errors='ignore') if isinstance(request.data, bytes) else str(request.data)
        print(f"  {raw_data[:500]}")
    
    if not request.is_json:
        print(f"[API] 错误: 请求不是JSON格式")
        print(f"[API] 实际Content-Type: {request.headers.get('Content-Type')}")
        print(f"[API] 请求mimetype: {request.mimetype}")
        return jsonify({
            "success": False,
            "error": "Request must be JSON",
            "code": "INVALID_FORMAT",
            "content_type": request.headers.get('Content-Type'),
            "timestamp": datetime.now().isoformat()
        }), 400
    
    print(f"[API] 请求是JSON格式，开始解析...")
    
    try:
        data = request.get_json()
        print(f"[API] 成功解析JSON数据")
        print(f"[API] JSON数据类型: {type(data)}")
        print(f"[API] JSON数据内容: {data}")
    except Exception as e:
        print(f"[API] JSON解析失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Invalid JSON: {str(e)}",
            "code": "INVALID_JSON",
            "timestamp": datetime.now().isoformat()
        }), 400
    
    # 3. 验证必需字段
    prompt = data.get('prompt')
    duration = data.get('duration', 5)
    
    print(f"\n[API] 验证字段...")
    print(f"[API] prompt字段: {prompt}")
    print(f"[API] prompt字段类型: {type(prompt)}")
    print(f"[API] duration字段: {duration}")
    print(f"[API] duration字段类型: {type(duration)}")
    
    if not prompt:
        print(f"[API] 错误: 缺少'prompt'字段")
        print(f"[API] 所有可用字段: {list(data.keys())}")
        return jsonify({
            "success": False,
            "error": "Missing 'prompt' field",
            "code": "MISSING_PROMPT",
            "available_fields": list(data.keys()),
            "timestamp": datetime.now().isoformat()
        }), 400
    
    if not isinstance(prompt, str):
        print(f"[API] 错误: 'prompt'字段不是字符串类型")
        return jsonify({
            "success": False,
            "error": "'prompt' must be a string",
            "code": "INVALID_PROMPT_TYPE",
            "prompt_type": str(type(prompt)),
            "timestamp": datetime.now().isoformat()
        }), 400
    
    print(f"[API] 收到视频生成请求: {prompt[:50]}...")
    
    # 4. 调用火山引擎API
    print(f"\n[API] 开始调用火山引擎API...")
    result = call_volcano_engine_safe(prompt, duration)
    
    # 5. 构建响应
    print(f"\n[API] 构建响应...")
    response_data = {
        "success": result.get("success", False),
        "task_id": result.get("task_id"),
        "prompt": prompt,
        "video_url": result.get("video_url"),
        "status": result.get("status", "unknown"),
        "duration": duration,
        "generated_at": datetime.now().isoformat(),
        "sdk_used": "VisualService" if sdk_ready else "simulated",
        "api_version": "4.2-debug-logging"
    }
    
    if result.get("note"):
        response_data["note"] = result["note"]
    
    if result.get("warning"):
        response_data["warning"] = result["warning"]
    
    if result.get("api_response"):
        api_resp = result["api_response"]
        response_data["api_status"] = api_resp.get("status_code")
        response_data["api_message"] = api_resp.get("message")
    
    if not result.get("success"):
        response_data["error"] = result.get("error", "Unknown error")
        print(f"[API] 返回错误响应: {response_data}")
        return jsonify(response_data), 500
    
    print(f"[API] 返回成功响应")
    print(f"[API] 响应数据: {response_data}")
    print(f"{'='*60}\n")
    
    return jsonify(response_data)

@app.route('/get_videotask_id>', methods=['GET'])
def get_video_result(task_id):
    """获取视频生成结果"""
    print(f"[API] 收到查询请求: task_id={task_id}")
    
    # 验证Token
    auth_success, auth_message = authenticate_request()
    if not auth_success:
        return jsonify({"error": auth_message}), 401
    
    try:
        if not sdk_ready or visual_service is None:
            return jsonify({
                "success": False,
                "error": "SDK未初始化",
                "task_id": task_id
            })
        
        # 调用火山引擎查询任务状态
        req = {"task_id": task_id}
        response = visual_service.get_video_generation_result(req)
        
        if response.get("status_code") == 10000:
            data = response.get("data", {})
            status = data.get("status", "unknown")
            video_url = data.get("video_url", "")
            
            return jsonify({
                "success": True,
                "task_id": task_id,
                "status": status,
                "video_url": video_url,
                "api_response": response
            })
        else:
            return jsonify({
                "success": False,
                "error": response.get("message", "查询失败"),
                "task_id": task_id
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"查询失败: {str(e)}",
            "task_id": task_id
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n{'='*60}")
    print(f"[启动] 服务启动中...")
    print(f"[启动] 端口: {port}")
    print(f"[启动] 调试模式: 关闭")
    print(f"[启动] 版本: 4.2-debug-logging")
    print(f"[启动] 开始监听请求...")
    print(f"{'='*60}\n")
    app.run(host='0.0.0.0', port=port, debug=False)
