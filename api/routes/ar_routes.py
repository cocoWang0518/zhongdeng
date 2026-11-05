from io import BytesIO
from pathlib import Path

import pandas as pd
from flask import Blueprint, jsonify, request

from api.services.ar_evaluation import DEFAULT_DATA_END, evaluate_ar

ar_bp = Blueprint("ar", __name__)
MAX_UPLOAD_BYTES = 50 * 1024 * 1024


@ar_bp.route("/ar/calculate", methods=["POST"])
def calculate_ar():
    upload = request.files.get("file")
    if upload is None or not upload.filename:
        return jsonify(status="error", message="请上传评级结果文件"), 400
    suffix = Path(upload.filename).suffix.lower()
    if suffix not in {".xlsx", ".csv", ".parquet"}:
        return jsonify(status="error", message="仅支持 .xlsx、.csv、.parquet 评级结果文件"), 400
    content = upload.stream.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        return jsonify(status="error", message="评级结果文件不能超过50MB"), 413
    try:
        if suffix == ".xlsx":
            data = pd.read_excel(BytesIO(content), dtype=object)
        elif suffix == ".parquet":
            data = pd.read_parquet(BytesIO(content))
        else:
            try:
                data = pd.read_csv(BytesIO(content), dtype=object, encoding="utf-8-sig")
            except UnicodeDecodeError:
                data = pd.read_csv(BytesIO(content), dtype=object, encoding="gb18030")
        result = evaluate_ar(
            data,
            data_end=request.form.get("data_end", DEFAULT_DATA_END),
            id_col=request.form.get("id_col", "stkcd").strip(),
            date_col=request.form.get("date_col", "ym").strip(),
            rating_col=request.form.get("rating_col", "信用评级").strip(),
            default_date_col=request.form.get("default_date_col", "首次违约日期").strip(),
        )
        return jsonify(status="success", data=result)
    except (ValueError, KeyError, TypeError) as error:
        return jsonify(status="error", message=str(error)), 400
    except Exception:
        import traceback
        traceback.print_exc()
        return jsonify(status="error", message="AR计算失败，请检查文件是否完整及格式是否正确"), 500
