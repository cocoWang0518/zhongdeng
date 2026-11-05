from pathlib import Path
import json

from flask import Blueprint, jsonify, request

from new_main import PREDICTION_VERSION, validate_prediction_params
from api.utils.file_utils import ensure_directory_exists
from api.utils.hash_utils import calculate_hash

check_bp = Blueprint("check", __name__)

RESULT_ROOT = Path(__file__).resolve().parents[2] / "result"
SUPPORTED_EXTENSIONS = {".csv", ".parquet"}
EXPECTED_RESULT_FILES = {
    "biaoge.csv",
    "risk_metrics.json",
    "config.json",
}


def _result_exists(result_dir):
    if not result_dir.exists():
        return False

    if not all((result_dir / filename).exists() for filename in EXPECTED_RESULT_FILES):
        return False

    config_path = result_dir / "config.json"
    try:
        config_data = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        config_data = {}

    dataset_filename = config_data.get("dataset_filename")
    if dataset_filename:
        return (result_dir / dataset_filename).exists()

    return (result_dir / "dataset.csv").exists() or (result_dir / "dataset.parquet").exists()


def _calculate_prediction_hash(task_type, data_type, industry_type, file_content):
    return calculate_hash(task_type, PREDICTION_VERSION, data_type, industry_type, file_content)


@check_bp.route("/check-result", methods=["POST"])
def check_result():
    """检查 new_main 预测结果是否已存在。"""
    try:
        if "file" not in request.files:
            return jsonify({"status": "error", "message": "No file part in the request"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"status": "error", "message": "No file selected"}), 400

        if Path(file.filename).suffix.lower() not in SUPPORTED_EXTENSIONS:
            return jsonify({"status": "error", "message": "仅支持上传 .csv 或 .parquet 文件"}), 400

        task_type = request.form.get("task_type")
        data_type = request.form.get("data_type")
        industry_type = request.form.get("industry_type")
        task_type, data_type, industry_type = validate_prediction_params(
            task_type,
            data_type,
            industry_type,
        )

        file_content = file.read()
        hash_value = _calculate_prediction_hash(
            task_type,
            data_type,
            industry_type,
            file_content,
        )

        ensure_directory_exists(RESULT_ROOT)
        result_dir = RESULT_ROOT / hash_value
        result_exists = _result_exists(result_dir)

        return jsonify(
            {
                "status": "success",
                "exists": result_exists,
                "hash": hash_value,
                "result_directory": str(result_dir) if result_exists else None,
            }
        )

    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
