from flask import Blueprint, request, jsonify, send_from_directory
import os
import traceback
from api.utils.visualization_utils import generate_row_visualization
from api.utils.file_utils import ensure_directory_exists

visualization_bp = Blueprint("visualization", __name__)


@visualization_bp.route("/img/<hash_value>/<index>", methods=["GET"])
def get_row_img(hash_value, index):
    """获取特定行的图像"""
    try:
        # 确保结果目录存在
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        result_dir = os.path.join(current_dir, "../result")
        ensure_directory_exists(result_dir)

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

        # 确保行目录存在
        row_dir = os.path.join(result_dir, "row")
        ensure_directory_exists(row_dir)

        if not os.path.exists(f"{row_dir}/{index}"):
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"File {index} not found in row directory",
                    }
                ),
                404,
            )

        print(f"提供文件: {os.path.join(result_dir, 'row')}/{index}")
        return send_from_directory(os.path.join(result_dir, "row"), index)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@visualization_bp.route("/row", methods=["GET"])
def get_row_plot():
    """为特定行索引生成图像并返回相关数据"""
    try:
        # 从查询参数中获取哈希和索引
        hash_value = request.args.get("hash")
        index_str = request.args.get("index")

        # 验证参数
        if not hash_value:
            return (
                jsonify(
                    {"status": "error", "message": "Missing required parameter: hash"}
                ),
                400,
            )

        if not index_str or not index_str.isdigit():
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Missing or invalid index parameter (must be an integer)",
                    }
                ),
                400,
            )

        index = int(index_str)

        # 确保结果目录存在
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        result_dir = os.path.join(current_dir, "../result")
        ensure_directory_exists(result_dir)

        # 检查结果目录是否存在
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

        # 创建行子目录（如果不存在）
        row_dir = os.path.join(result_dir, "row")
        ensure_directory_exists(row_dir)

        # 检查文件是否已存在
        if os.path.exists(f"{row_dir}/{index}.txt") and os.path.exists(
            f"{row_dir}/{index}.png"
        ):
            response = {
                "status": "success",
                "hash": hash_value,
                "index": index,
                "plot_url": f"/img/{hash_value}/{index}.png",
                "text_url": f"/img/{hash_value}/{index}.txt",
            }

            return jsonify(response)

        # 生成可视化
        success = generate_row_visualization(hash_value, index, result_dir)

        if not success:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Required files not found in result directory",
                    }
                ),
                404,
            )

        # 返回响应
        response = {
            "status": "success",
            "hash": hash_value,
            "index": index,
            "plot_url": f"/img/{hash_value}/{index}.png",
            "text_url": f"/img/{hash_value}/{index}.txt",
        }

        return jsonify(response)

    except Exception as e:
        error_message = traceback.format_exc()
        return (
            jsonify({"status": "error", "message": str(e), "traceback": error_message}),
            500,
        )
