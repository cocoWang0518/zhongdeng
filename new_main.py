import pandas as pd
import numpy as np
import os
import joblib
import gc
import time
import json
from sklearn.metrics import accuracy_score, classification_report, f1_score, recall_score, precision_score

# 仅开放已经通过评估的行业与数据组合；保留原有三个接口参数。
PREDICTION_VERSION = "industry_20260907_v1"
INDUSTRY_MODEL_MAP = {
    "券商": "quanshang",
    "银行": "yinhang",
    "非银行金融": "feiyinhangjinrong",
    "房地产": "fangdichan",
    "电力及公用事业": "dianlijigongyongshiye",
    "基础化工": "jichuhuagong",
    "石油石化": "shiyoushihua",
    "基础设施与地产产业": "jichusheshiyudichanchanye",
    "周期产业": "zhouqichanye",
    "工业设备制造": "gongyeshebeizhizao",
    "科技产业": "kejichanye",
}
ALL_INDUSTRIES = list(INDUSTRY_MODEL_MAP)
SUPPORTED_PREDICTION_COMBOS = {
    ("信用债项评级", data_type, industry)
    for industry in ALL_INDUSTRIES
    for data_type in ("财务+非财务", "仅财务")
    if not (industry in ("工业设备制造", "科技产业") and data_type == "仅财务")
}

def validate_prediction_params(task_type, data_type, industry_type):
    """校验并规范化 new_main 当前支持的预测参数组合。"""
    task_type = (task_type or "").strip()
    data_type = (data_type or "").strip()
    industry_type = (industry_type or "").strip()

    missing = [
        name for name, value in {
            "task_type": task_type,
            "data_type": data_type,
            "industry_type": industry_type,
        }.items()
        if not value
    ]
    if missing:
        raise ValueError(f"缺少必需参数: {', '.join(missing)}")

    combo = (task_type, data_type, industry_type)
    if combo not in SUPPORTED_PREDICTION_COMBOS:
        raise ValueError(
            f"不支持的预测组合: {task_type} / {data_type} / {industry_type}。\n"
            f"请检查传入的参数是否正确。"
        )

    return task_type, data_type, industry_type


def get_model_path(task_type, data_type, industry_type):
    """沿用原来的行业映射和 all/only 文件名路由。"""
    validate_prediction_params(task_type, data_type, industry_type)
    data_suffix = "all" if data_type == "财务+非财务" else "only"
    name = f"{task_type}_saved_model_{INDUSTRY_MODEL_MAP[industry_type]}_{data_suffix}_compressed.pkl"
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "model", "industry_20260907", name)


def calculate_rating_metrics(y_true, y_pred, labels):
    """按实际测试结果计算；加权口径与训练代码一致，不吞掉评估异常。"""
    labels = sorted(set(labels) | set(y_true) | set(y_pred))
    report = classification_report(y_true, y_pred, labels=labels, output_dict=True, zero_division=0)
    rows = []
    for label, values in report.items():
        if label == "accuracy":
            rows.append({"类别": label, "精确率": "", "召回率": "",
                         "F1 得分": round(values, 5), "样本数": len(y_true)})
        else:
            rows.append({"类别": label, "精确率": round(values["precision"], 5),
                         "召回率": round(values["recall"], 5), "F1 得分": round(values["f1-score"], 5),
                         "样本数": int(values["support"])})
    return {
        "准确率": round(accuracy_score(y_true, y_pred), 5),
        "精确率": round(precision_score(y_true, y_pred, average="weighted", zero_division=0), 5),
        "召回率": round(recall_score(y_true, y_pred, average="weighted", zero_division=0), 5),
        "F1 得分": round(f1_score(y_true, y_pred, average="weighted", zero_division=0), 5),
        "分类报告": rows,
    }


def execute_two_stage_ensemble(model_package, X_test):
    """解包字典模型，并复现两阶段预测过程。"""
    print(f"▶️ 开始执行两阶段预测流...")
    base_rf_model = model_package.get('base_rf_model') or model_package.get('stage1_model')
    sub_model_A = model_package.get('sub_model_A') or model_package.get('stage2_model_A')
    le_A = model_package.get('le_A') or model_package.get('stage2_le_A')
    sub_model_AA = model_package.get('sub_model_AA') or model_package.get('stage2_model_AA')
    le_AA = model_package.get('le_AA') or model_package.get('stage2_le_AA')

    if base_rf_model is None:
        raise ValueError("模型包中缺失第一阶段的大类预测模型。")

    X_test_array = X_test.values
    y_pred_large = base_rf_model.predict(X_test_array)
    final_pred = np.asarray(y_pred_large, dtype=object).copy()

    if sub_model_A is not None:
        mask_A = (final_pred == "A段")
        if mask_A.any():
            pred_enc = sub_model_A.predict(X_test_array[mask_A])
            final_pred[mask_A] = le_A.inverse_transform(pred_enc)

    if sub_model_AA is not None:
        mask_AA = (final_pred == "AA段")
        if mask_AA.any():
            pred_enc = sub_model_AA.predict(X_test_array[mask_AA])
            final_pred[mask_AA] = le_AA.inverse_transform(pred_enc)

    return final_pred


def filter_industry_data(data, industry_type):
    """按新行业名单筛选；无行业字段时沿用上传行业专属文件的用法。"""
    first_level = {
        "券商": ["证券", "券商"], "银行": ["银行"],
        "非银行金融": ["非银行金融", "非银金融"],
        "房地产": ["房地产"],
        "电力及公用事业": ["电力及公用事业", "电力以及公共事业"],
        "基础化工": ["基础化工"], "石油石化": ["石油石化"],
        "工业设备制造": ["工业设备制造", "机械"],
    }
    if industry_type in first_level and "中信一级行业" in data:
        values = data["中信一级行业"].fillna("").astype(str).str.strip()
        mask = values.isin(first_level[industry_type])
        # 券商可能在一级行业中归于“非银行金融”，专属文件按板块字段识别。
        if industry_type == "券商" and "所属产业板块" in data:
            mask |= data["所属产业板块"].fillna("").astype(str).str.strip().eq("券商")
        return data.loc[mask].copy()
    if "所属产业板块" in data:
        return data.loc[data["所属产业板块"].fillna("").astype(str).str.strip().eq(industry_type)].copy()
    return data.copy()


def normalize_rating(rating):
    """周期产业训练代码的11级评级口径。"""
    mapping = {"AAA": "AAA", "AA+": "AA+", "AA": "AA", "AA-": "AA", "A+": "A+",
               "A": "A", "A-": "A", "CC": "CC", "C": "C"}
    for base in ("BBB", "BB", "B", "CCC"):
        for suffix in ("", "+", "-"):
            mapping[base + suffix] = base
    return mapping.get(rating)


def prepare_model_features(test_data, model_package):
    """遵循模型保存的起始列、原始特征顺序和特征筛选器。"""
    selector = model_package.get("feature_selector")
    model = model_package.get("base_rf_model", model_package.get("stacking_model", model_package.get("stack_reg_model")))
    input_model = selector if selector is not None else model
    names = getattr(input_model, "feature_names_in_", None)
    start = model_package["feature_start_col_index"]
    raw = test_data.iloc[:, start:].drop(columns=["month", "target_num"], errors="ignore")
    if "stack_reg_model" in model_package:
        raw = raw.drop(columns=["信用评级", "ym"], errors="ignore")
    # f0/f1模型没有保存业务列名，随模型附上由配套数据核对的列顺序。
    input_features = model_package.get("input_features")
    if input_features is not None:
        missing = [name for name in input_features if name not in raw]
        if missing:
            raise ValueError(f"上传数据缺少模型特征或特征位置不符: {', '.join(missing[:10])}")
        raw = raw.loc[:, input_features]
    # 部分训练文件将原始列依次重命名为 f0、f1…，此时按起始列切片后再同样命名。
    synthetic_names = names is not None and list(names) == [f"f{i}" for i in range(len(names))]
    if synthetic_names and raw.shape[1] == len(names):
        raw.columns = names
    if names is not None:
        missing = [str(name) for name in names if name not in raw]
        if missing:
            raise ValueError(f"上传数据缺少模型特征或特征位置不符: {', '.join(missing[:10])}")
        raw = raw.loc[:, list(names)]
    expected = input_model.n_features_in_
    if raw.shape[1] != expected:
        raise ValueError(f"模型需要 {expected} 个原始特征，上传数据提供 {raw.shape[1]} 个；请使用对应行业的数据文件。")
    raw = raw.apply(pd.to_numeric, errors="coerce").fillna(0)
    if not np.isfinite(raw.to_numpy()).all():
        raise ValueError("上传数据的模型特征含无穷值，请清理后重试。")
    if selector is not None:
        selected = selector.transform(raw)
        names = model_package.get("selected_features")
        features = pd.DataFrame(selected, columns=names, index=raw.index)
    else:
        features = raw
    if features.shape[1] != model.n_features_in_:
        raise ValueError("特征筛选结果与模型输入维度不一致，请检查模型包。")
    return raw, features


def main(task_type, data, data_type, industry_type):
    """保留原主流程：校验、筛选、90/10划分、加载、预测、评估、返回。"""
    task_type, data_type, industry_type = validate_prediction_params(task_type, data_type, industry_type)
    if "信用评级" not in data:
        raise ValueError("上传数据缺少“信用评级”列，无法计算准确率和召回率。")
    data = filter_industry_data(data, industry_type)
    if data.empty:
        raise ValueError(f"筛选后数据为空，未匹配到行业: {industry_type}。请检查数据文件。")
    if data["信用评级"].isna().any():
        raise ValueError("信用评级存在空值，请补齐后再进行预测评估。")
    model_path = get_model_path(task_type, data_type, industry_type)
    if not os.path.isfile(model_path):
        raise FileNotFoundError(f"找不到模型文件: {model_path}")
    loaded_obj = joblib.load(model_path)
    if not isinstance(loaded_obj, dict):
        raise ValueError("行业模型包必须包含模型及特征处理参数。")
    schema_path = os.path.join(os.path.dirname(model_path), "feature_columns.json")
    with open(schema_path, encoding="utf-8") as stream:
        schemas = json.load(stream)
    loaded_obj["input_features"] = schemas[os.path.basename(model_path)]

    # 周期产业保存的模型采用合并后的评级；与配套代码保持同一口径。
    if industry_type == "周期产业":
        if "ym" in data:
            data["month"] = pd.to_datetime(data["ym"], errors="coerce")
        data = data.sample(frac=1, random_state=loaded_obj.get("random_seed", 42)).reset_index(drop=True)
        data["细分评级"] = data["信用评级"].map(normalize_rating)
        data = data.loc[data["细分评级"].notna()].copy()
        counts = data["细分评级"].value_counts()
        fixes = {k: {"A+": "A", "AA": "AA+", "AAA": "AA+"}.get(k, k)
                 for k in counts[counts < 3].index}
        data["细分评级"] = data["细分评级"].replace(fixes)
        rating_basis = "11级合并评级（含训练代码的稀有类别合并）"
    else:
        # 回归模型训练时未在原始特征前添加日期辅助列。
        if "ym" in data and "stack_reg_model" not in loaded_obj:
            data["month"] = pd.to_datetime(data["ym"], errors="coerce")
        if "stack_reg_model" in loaded_obj:
            target = data["信用评级"].map(loaded_obj["rating_to_num"])
            data = data.loc[target.notna()].copy()
        data = data.sample(frac=1, random_state=loaded_obj.get("random_seed", 42)).reset_index(drop=True)
        rating_basis = "11级合并评级" if "stack_reg_model" in loaded_obj else "原始信用评级"

    test_data = data.iloc[int(0.9 * len(data)):].copy()
    if test_data.empty:
        raise ValueError("测试集为空，请检查评级是否属于模型支持的范围。")
    X_raw, X_test = prepare_model_features(test_data, loaded_obj)
    if "stack_reg_model" in loaded_obj:
        model_type = "Stacking回归得分与阈值评级"
        scores = loaded_obj["stack_reg_model"].predict(X_test)
        codes = np.digitize(scores, loaded_obj["best_thresholds"]) + 1
        test_predictions_labels = np.array([loaded_obj["num_to_rating"][int(code)] for code in codes])
        y_test_original = test_data["信用评级"].map(loaded_obj["rating_to_num"]).map(loaded_obj["num_to_rating"])
    elif "stacking_model" in loaded_obj:
        model_type = "Stacking特征筛选集成架构"
        codes = loaded_obj["stacking_model"].predict(X_test)
        test_predictions_labels = loaded_obj["label_encoder"].inverse_transform(codes)
        y_test_original = test_data["细分评级"] if industry_type == "周期产业" else test_data["信用评级"]
    elif "base_rf_model" in loaded_obj or "stage1_model" in loaded_obj:
        model_type = "大类预测+细分修正 两阶段架构"
        test_predictions_labels = execute_two_stage_ensemble(loaded_obj, X_test)
        y_test_original = test_data["信用评级"]
    else:
        raise ValueError("模型包结构不受支持，请检查模型文件内的键名。")

    result_df = X_test.copy()
    result_df["预测结果"] = test_predictions_labels
    identifier_cols = [col for col in ['债券代码', '债券名称', 'ym', '所属产业板块', '中信一级行业',
                                      '债券一级分类', '信用评级', 'stkcd', '所在地区'] if col in test_data]
    biaoge = test_data[identifier_cols].copy()
    biaoge["评估评级"] = y_test_original
    biaoge["预测结果"] = test_predictions_labels
    if "ym" in biaoge:
        biaoge = biaoge.sort_values("ym")
    biaoge = biaoge.reset_index(drop=True)
    risk = calculate_rating_metrics(y_test_original, test_predictions_labels, sorted(y_test_original.unique()))
    test_info = {
        "测试任务": task_type, "评估行业": industry_type, "数据维度": data_type,
        "模型架构": model_type, "原始特征数量": X_raw.shape[1], "特征数量": X_test.shape[1],
        "测试集样本量": len(X_test), "测试集划分": "固定随机种子打乱后取后10%（沿用系统规则）",
        "评级口径": rating_basis, "指标口径": "准确率；精确率、召回率和F1按样本数加权",
        "生成时间": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
    }
    if industry_type == "工业设备制造":
        test_info["评估说明"] = "沿用系统90/10切分，与训练脚本的分层抽样不同，指标不等同于训练报告的独立测试成绩。"
    del loaded_obj
    gc.collect()
    return result_df, biaoge, risk, test_info
