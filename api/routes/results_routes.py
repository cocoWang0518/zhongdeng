from flask import Blueprint, jsonify, send_from_directory
import os
from api.utils.file_utils import ensure_directory_exists

results_bp = Blueprint("results", __name__)


@results_bp.route("/results", methods=["GET"])
def list_results():
    """获取所有结果目录（哈希）列表及其创建时间"""
    try:
        # 确保结果目录存在
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        result_dir = os.path.join(current_dir, "../result")
        ensure_directory_exists(result_dir)

        # 获取结果文件夹中的所有目录及其创建时间
        result_dirs = []
        for d in os.listdir(result_dir):
            dir_path = os.path.join(result_dir, d)
            if os.path.isdir(dir_path):
                creation_time = os.path.getctime(dir_path)
                result_dirs.append({"hash": d, "creation_time": creation_time})

        # 按创建时间排序结果，最新的在前面
        result_dirs.sort(key=lambda x: x["creation_time"], reverse=True)

        # 返回目录列表及其创建时间
        return jsonify(
            {"status": "success", "results": result_dirs, "count": len(result_dirs)}
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@results_bp.route("/results/<hash_value>/<filename>", methods=["GET"])
def get_result_file(hash_value, filename):
    """从结果目录中获取特定文件"""
    try:
        # 确保结果目录存在
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        result_dir = os.path.join(current_dir, "../result")
        ensure_directory_exists(result_dir)

        # 检查目录是否存在
        result_dir = os.path.join(result_dir, hash_value)
        if not os.path.exists(result_dir):
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Result directory with hash {hash_value} not found",
                    }
                ),
                404,
            )

        # 检查文件是否存在于目录中
        file_path = os.path.join(result_dir, filename)
        if not os.path.exists(file_path):
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"File {filename} not found in result directory {hash_value}",
                    }
                ),
                404,
            )

        # 提供文件
        print(f"提供文件: ./result/{hash_value}/{filename}")
        return send_from_directory(result_dir, filename)

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# 添加对/result路径的支持，与/results保持兼容
@results_bp.route("/result/<hash_value>/<filename>", methods=["GET"])
def get_result_file_alt(hash_value, filename):
    """从结果目录中获取特定文件(替代路径)"""
    return get_result_file(hash_value, filename)
