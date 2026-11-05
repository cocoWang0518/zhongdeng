from flask import Blueprint, send_from_directory, jsonify
import os

static_bp = Blueprint("static", __name__)


# 提供Vue.js构建文件，从'web'目录
@static_bp.route("/", defaults={"path": ""})
@static_bp.route("/<path:path>")
def serve_vue_app(path):
    """从web目录提供Vue.js应用"""
    # 获取正确的web目录路径
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    web_dir = os.path.join(current_dir, "../web")

    # 检查路径是否存在
    if not os.path.exists(web_dir):
        return jsonify({"status": "error", "message": "Web directory not found"}), 404

    static_path = os.path.join(web_dir, path)
    if path != "" and os.path.isfile(static_path):
        # 提供请求的文件
        return send_from_directory(web_dir, path)
    else:
        # 为所有其他路径提供index.html（适用于Vue路由器的历史模式）
        return send_from_directory(web_dir, "index.html")
