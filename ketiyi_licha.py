import os
import warnings
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

warnings.filterwarnings('ignore')

# ==========================================
# 1. 基础配置与数据集映射
# ==========================================
EXCLUDE_BLACK_LIST = {
    'ym', 'CS', 'CS_benchmark', 'stkcd', '报表时间', 'year',
    '财务数据统计截止日期', 'ym_period', 'date'
}

ID_CANDIDATES = ['债券代码', '城投平台', 'stkcd', '债券名称']

DATASET_MAPPING = {
    "券商债项": "1.1券商债项",
    "银行债项": "1.2银行债项",
    "信用债项": "1.信用债项",
    "券商主体": "2.1券商主体",
    "银行主体": "2.2银行主体",
    "信用债主体": "2.信用债主体",
    "城投债项": "3.城投债项",
    "城投主体": "4.城投主体",
    "ABS专项": "5.ABS"
}

# 当正式数据目录（converted_data）中缺少对应文件时，回退到项目 file/ 目录中的结项数据
FALLBACK_FILE_MAPPING = {
    "ABS专项": "ABS数据_结项.parquet",
    "城投债项": "城投数据_结项.parquet",
}


# ==========================================
# 2. 核心数据加载函数
# ==========================================
def _load_file(file_path: Path, display_name: str, columns=None, month_window=None) -> pd.DataFrame:
    """读取文件并统一处理 ym 日期列"""
    if file_path.suffix == '.parquet':
        filters = None
        if month_window is not None:
            from pyarrow import parquet, types

            date_type = parquet.ParquetFile(file_path).schema_arrow.field('ym').type
            if types.is_timestamp(date_type) and date_type.tz is None:
                start, end = month_window
                filters = [('ym', '>=', start.start_time), ('ym', '<', (end + 1).start_time)]
        df = pd.read_parquet(file_path, columns=columns, filters=filters)
    elif file_path.suffix == '.csv':
        df = pd.read_csv(file_path, usecols=columns)
    else:
        df = pd.read_excel(file_path, usecols=columns)

    if 'ym' in df.columns:
        df['ym'] = pd.to_datetime(df['ym'], errors='coerce')
        df = df.dropna(subset=['ym']).sort_values('ym')
        df['ym_period'] = df['ym'].dt.to_period('M')
    else:
        print(f"❌ 错误: 数据集【{display_name}】中不存在 'ym' 日期列。")
        return None

    return df


def load_dataset_by_name(data_dir: Path, display_name: str, columns=None, month_window=None) -> pd.DataFrame:
    """按业务名称加载数据集并处理日期列"""
    internal_name = DATASET_MAPPING.get(display_name, display_name)
    file_path = None

    # 候选目录：优先用户指定的数据根目录，其次回退到项目自带 file/ 目录
    dir_candidates = [Path(data_dir)]
    fallback_dir = Path(__file__).resolve().parent / "file"
    if fallback_dir not in dir_candidates:
        dir_candidates.append(fallback_dir)

    for d in dir_candidates:
        # 1. 精确匹配（正式数据目录中的规范文件名）
        for ext in ['.parquet', '.csv', '.xlsx']:
            p = d / f"{internal_name}{ext}"
            if p.exists():
                file_path = p
                break
        if file_path is not None:
            break

        # 2. 回退匹配（file/ 目录中的结项数据）
        fallback_name = FALLBACK_FILE_MAPPING.get(display_name)
        if fallback_name:
            p = d / fallback_name
            if p.exists():
                file_path = p
                break

    if file_path is None:
        print(f"❌ 错误: 未能在路径【{dir_candidates}】找到【{display_name}】对应文件 ({internal_name})。")
        return None

    return _load_file(file_path, display_name, columns, month_window)


# ==========================================
# 3. 核心预测与评级推演逻辑
# ==========================================
RATING_BINS = [0, 0.01, 0.09, 0.18, 0.33, 0.52, 0.71, 0.85, 0.94, 0.98, 0.99, 1.0]
RATING_LABELS = ['AAA级', 'AA+级', 'AA级', 'A+级', 'A级', 'BBB级', 'BB级', 'B级', 'CCC级', 'CC级', 'C级']


def ratings_from_percentiles(percentiles):
    return pd.cut(percentiles, bins=RATING_BINS, labels=RATING_LABELS, include_lowest=True, right=True)


def predict_single_month(
    data_dir: str,
    display_name: str,
    target_month_str: str,
    *,
    rating_rule=ratings_from_percentiles,
    skip_missing_targets=False,
):
    """
    单月预测核心逻辑
    返回 3 项内容:
      1. meta_info (dict): 训练/预测窗口与样本数元信息
      2. bond_df (DataFrame): 精简后的债券预测与中文评级明细
      3. metrics (dict): 评估指标 (MAE, RMSE, R²) 及 各评级数量统计
    """
    target_month = pd.Period(target_month_str, freq='M')
    train_start_month = target_month - 6
    train_end_month = target_month - 1

    # 信用债主体明细较大，综合评级仅读取本次所需的月份。
    month_window = None
    if skip_missing_targets and display_name == "信用债主体":
        month_window = (train_start_month, target_month)
    df = load_dataset_by_name(Path(data_dir), display_name, month_window=month_window)
    if df is None:
        return None, None, None

    train_data = df[(df['ym_period'] >= train_start_month) & (df['ym_period'] <= train_end_month)]
    test_data = df[df['ym_period'] == target_month]
    if skip_missing_targets:
        train_data = train_data[np.isfinite(train_data['CS'])]

    if train_data.empty or test_data.empty:
        print(f"❌ 错误: 缺乏 {train_start_month}~{train_end_month} 或 {target_month_str} 数据。")
        return None, None, None

    # 确定标识 ID 列与特征列
    all_cols = df.columns.tolist()
    id_col = next((col for col in ID_CANDIDATES if col in all_cols), 'index')

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    feature_columns = [col for col in numeric_cols if col not in EXCLUDE_BLACK_LIST and col not in ID_CANDIDATES]

    # 特征准备与中位数填充
    X_train = train_data[feature_columns].copy()
    y_train = train_data['CS'].copy()
    X_test = test_data[feature_columns].copy()
    y_test = test_data['CS'].copy() if 'CS' in test_data.columns else None

    train_medians = X_train.median()
    X_train = X_train.fillna(train_medians).fillna(0)
    X_test = X_test.fillna(train_medians).fillna(0)

    # 1. 训练 GBDT 模型并预测
    model = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    # 2. 计算月内百分位并划分中文评级
    percentiles = pd.Series(predictions).rank(pct=True, ascending=True)

    ratings = rating_rule(percentiles)

    # 3. 构建精简版债券明细 DataFrame
    res_df = pd.DataFrame({
        '数据类型': display_name,
        '预测月份': target_month_str,
        '代码': test_data[id_col].values if id_col != 'index' else test_data.index,
        '预测利差': np.round(predictions, 4),
        '评级结果': ratings
    })

    # -------------------------------------------------------------
    # 内容 1：预测元信息 (Meta Info)
    # -------------------------------------------------------------
    meta_info = {
        "数据集名称": display_name,
        "预测目标月份": target_month_str,
        "训练窗口": f"{train_start_month} ~ {train_end_month}",
        "训练集样本数": int(len(train_data)),
        "预测集样本数": int(len(test_data)),
        "评估特征数量": int(len(feature_columns))
    }

    # -------------------------------------------------------------
    # 内容 3：评估指标与各评级数量统计 (Metrics)
    # -------------------------------------------------------------
    metrics = {}
    if skip_missing_targets and y_test is not None:
        valid_targets = np.isfinite(y_test)
        y_test = y_test[valid_targets]
        predictions = predictions[valid_targets.to_numpy()]
    if y_test is not None and not y_test.isnull().all():
        mae = mean_absolute_error(y_test, predictions)
        rmse = np.sqrt(mean_squared_error(y_test, predictions))

        metrics["MAE"] = round(float(mae), 4)
        metrics["RMSE"] = round(float(rmse), 4)
        if not skip_missing_targets or len(y_test) >= 2:
            metrics["R²"] = round(float(r2_score(y_test, predictions)), 4)

    # 统计各个中文评级的债券数量分布
    rating_counts = res_df['评级结果'].value_counts().to_dict()
    # 按照 rating 顺序整理
    ordered_rating_counts = {label: int(rating_counts.get(label, 0)) for label in RATING_LABELS if label in rating_counts}
    metrics["各评级数量统计"] = ordered_rating_counts

    return meta_info, res_df, metrics


# ==========================================
# 3.5 JSON 序列化辅助
# ==========================================
def _to_native(obj):
    """递归将 numpy 类型转换为 JSON 可序列化的 Python 原生类型"""
    if isinstance(obj, dict):
        return {k: _to_native(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_native(v) for v in obj]
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, float) and pd.isna(obj):
        return None
    return obj


def predict_single_month_json(data_dir: str, display_name: str, target_month_str: str):
    """
    单月预测统一 JSON 入口
    返回结构（直接可 JSON 序列化）:
    {
        "meta_info": {...},   # 本次预测信息
        "metrics": {...},     # 预测效果（评估指标 + 各评级数量统计）
        "bond_list": [...]    # 预测结果（债券明细列表）
    }
    失败时返回 None
    """
    meta_info, bond_df, metrics = predict_single_month(
        data_dir=data_dir,
        display_name=display_name,
        target_month_str=target_month_str,
    )
    if bond_df is None:
        return None

    bond_list = _to_native(bond_df.to_dict(orient='records'))

    return {
        "meta_info": _to_native(meta_info),
        "metrics": _to_native(metrics),
        "bond_list": bond_list,
    }


# ==========================================
# 4. 主程序入口
# ==========================================
if __name__ == "__main__":
    # -------------------------------------------------------------
    # 用户处理输入参数区域
    # -------------------------------------------------------------
    DATA_DIR = "converted_data"  # 数据根目录路径
    SELECTED_DATASET = "城投债项"  # 选择的数据集分类
    TARGET_MONTH = "2023-10"      # 预测目标月份
    # -------------------------------------------------------------

    print("=" * 65)
    print("🚀 开始执行信用利差单月预测与智能评级推演")
    print("=" * 65)

    # 1. 运行预测，获取统一 JSON 输出（含 meta_info / metrics / bond_list 三部分）
    result = predict_single_month_json(
        data_dir=DATA_DIR,
        display_name=SELECTED_DATASET,
        target_month_str=TARGET_MONTH
    )

    # 2. 结果处理与展示
    if result is not None:
        meta_info = result["meta_info"]
        metrics = result["metrics"]
        bond_list = result["bond_list"]

        print("\n📌 【1. 本次预测配置与数据信息】")
        for k, v in meta_info.items():
            print(f"   - {k}: {v}")

        print("\n📊 【2. 模型指标与各评级分布统计】")
        for k, v in metrics.items():
            if k == "各评级数量统计":
                print(f"   - {k}:")
                for rating, count in v.items():
                    print(f"       • {rating}: {count} 只")
            else:
                print(f"   - {k}: {v}")

        print("\n📋 【3. 债券预测与评级明细表 (前 10 条展示)】")
        print(pd.DataFrame(bond_list).head(10).to_string(index=False))
