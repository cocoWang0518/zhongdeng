from pathlib import Path
import datetime
import shutil
import time
import traceback

from flask import Blueprint, jsonify, request
import pandas as pd

from new_main import main as run_prediction
from api.utils.hash_utils import calculate_hash
from api.utils.file_utils import (
    ensure_directory_exists,
    prepare_risk_data_for_serialization,
    save_dataframe_to_csv,
    save_json_to_file,
)

predict_bp = Blueprint("predict", __name__)

RESULT_ROOT = Path(__file__).resolve().parents[2] / "result"
SUPPORTED_EXTENSIONS = {".csv", ".parquet"}


def _read_upload_dataframe(file):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError("仅支持上传 .csv 或 .parquet 文件")

    file.stream.seek(0)
    if suffix == ".csv":
        return pd.read_csv(file.stream)

    return pd.read_parquet(file.stream)


def _calculate_prediction_hash(task_type, data_type, industry_type, file_content):
    return calculate_hash(task_type, "", data_type, industry_type, file_content)


def _result_exists(result_dir):
    if not result_dir.exists():
        return False

    required_files = {
        "biaoge.csv",
        "risk_metrics.json",
        "config.json",
    }
    if not all((result_dir / filename).exists() for filename in required_files):
        return False

    return (result_dir / "dataset.csv").exists() or (result_dir / "dataset.parquet").exists()


@predict_bp.route("/predict", methods=["POST"])
def predict():
    try:
        total_start = time.perf_counter()
        timings = {}

        if "file" not in request.files:
            return jsonify({"status": "error", "message": "No file part in the request"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"status": "error", "message": "No file selected"}), 400
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            return jsonify({"status": "error", "message": "仅支持上传 .csv 或 .parquet 文件"}), 400

        task_type = request.form.get("task_type")
        data_type = request.form.get("data_type")
        industry_type = request.form.get("industry_type")
        force = str(request.form.get("force", "")).lower() in {"1", "true", "yes"}

        from new_main import validate_prediction_params
        task_type, data_type, industry_type = validate_prediction_params(
            task_type,
            data_type,
            industry_type,
        )

        read_start = time.perf_counter()
        file_content = file.read()
        timings["file_read_seconds"] = round(time.perf_counter() - read_start, 3)

        hash_start = time.perf_counter()
        hash_value = _calculate_prediction_hash(
            task_type,
            data_type,
            industry_type,
            file_content,
        )
        timings["hash_seconds"] = round(time.perf_counter() - hash_start, 3)

        ensure_directory_exists(RESULT_ROOT)
        result_dir = RESULT_ROOT / hash_value
        if _result_exists(result_dir) and not force:
            timings["total_seconds"] = round(time.perf_counter() - total_start, 3)
            print(f"预测结果已存在，跳过模型运行: hash={hash_value}, timings={timings}")
            return jsonify(
                {
                    "status": "exists",
                    "hash": hash_value,
                    "timings": timings,
                }
            )

        parse_start = time.perf_counter()
        input_data = _read_upload_dataframe(file)
        timings["dataframe_parse_seconds"] = round(time.perf_counter() - parse_start, 3)
        if input_data.empty:
            return jsonify({"status": "error", "message": "Uploaded file is empty"}), 400

        predict_start = time.perf_counter()
        _result_df, biaoge, risk, test_info = run_prediction(
            task_type=task_type,
            data=input_data,
            data_type=data_type,
            industry_type=industry_type,
        )
        timings["prediction_seconds"] = round(time.perf_counter() - predict_start, 3)

        save_start = time.perf_counter()
        if result_dir.exists():
            shutil.rmtree(result_dir)
        ensure_directory_exists(result_dir)

        save_dataframe_to_csv(biaoge, result_dir / "biaoge.csv")
        dataset_filename = f"dataset{suffix}"
        (result_dir / dataset_filename).write_bytes(file_content)

        serializable_risk = prepare_risk_data_for_serialization(risk)
        save_json_to_file(serializable_risk, result_dir / "risk_metrics.json")

        timings["save_seconds"] = round(time.perf_counter() - save_start, 3)
        timings["total_seconds"] = round(time.perf_counter() - total_start, 3)

        config_data = {
            "task_type": task_type,
            "data_type": data_type,
            "industry_type": industry_type,
            "engine": "new_main",
            "original_filename": file.filename,
            "dataset_filename": dataset_filename,
            "processing_time": datetime.datetime.now().isoformat(),
            "test_info": test_info,
            "performance_timings": timings,
        }
        save_json_to_file(config_data, result_dir / "config.json")

        print(f"预测完成: hash={hash_value}, timings={timings}")
        return jsonify({"status": "success", "hash": hash_value, "timings": timings})

    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        error_msg = traceback.format_exc()
        print(error_msg)
        return jsonify({"status": "error", "message": str(e), "traceback": error_msg}), 500
