import pandas as pd
import numpy as np
import os
from pathlib import Path
from sklearn.linear_model import LinearRegression
import matplotlib.font_manager as fm
from transformers import BertTokenizer, BertForSequenceClassification
from tqdm import tqdm
import re
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, recall_score
import shap
import time
import openai
import matplotlib.pyplot as plt
from openai import OpenAI
import xgboost as xgb
from sklearn.ensemble import AdaBoostRegressor
from sklearn.ensemble import GradientBoostingRegressor
import tensorflow as tf
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import seaborn as sns
import numpy as np
from tensorflow.keras import layers, models
from tensorflow.keras.callbacks import EarlyStopping
import requests
import joblib
from tensorflow.keras.models import load_model
import torch
import torch_geometric
from torch_geometric.data import Data
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import torch.nn as nn
from torch_geometric.nn import GCNConv, global_mean_pool, GATConv
from torch_geometric.data import DataLoader
from sklearn.metrics import accuracy_score, f1_score, recall_score
from torch_geometric.data import DataLoader as GeometricDataLoader
from sklearn.preprocessing import StandardScaler
import torch.nn.functional as F
import h5py  # 导入h5py模块
from torch_geometric.nn import GCNConv, global_mean_pool, GATConv, global_max_pool
import torch.optim as optim
from torch_geometric.data import DataLoader as GeometricDataLoader
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT / ".env.local", override=True)

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
)


def main(task_type, model_name, data, data_type, industry_type):
    """
    主函数框架，用于处理用户选择的任务类型和模型，并生成预测结果和图。

    参数:
    task_type (str): 任务类型，可选 '债券回归' 或 '信用评级'。
    model_name (str): 用户选择的模型名称。
    input_df (pd.DataFrame): 用户传入的数据，格式为 DataFrame。

    返回:
    None（结果保存为 CSV 文件，图保存为 PNG 文件）。
    """

    # 检查任务类型
    if task_type == "信用利差预测":
        # 调用债券回归任务的模型处理逻辑
        result_df,  biaoge, feature_imports,  feature_columns,risk ,all_plot,etext ,tezhen= handle_bond_regression(model_name, data,
                                                                                                       data_type)
    elif task_type == "债项信用评级":
        # 调用信用评级任务的模型处理逻辑
        result_df,  biaoge, feature_imports,  feature_columns ,risk,all_plot,etext,tezhen= handle_credit_rating(model_name, data,
                                                                                                     data_type,
                                                                                                     industry_type)
    elif task_type == "主体信用评级":
        result_df,  biaoge, feature_imports,  feature_columns ,risk,all_plot,etext,tezhen= handle_credit_zhuti(model_name, data,
                                                                                                     data_type,
                                                                                                     industry_type)
    else:
        raise ValueError("无效的任务类型，请选择 '信用利差预测' 或 '债项信用评级'")

    return result_df,  biaoge, feature_imports,  feature_columns,risk,all_plot,etext,tezhen


def get_llm_explanation(feature_importance_df):
    """
    调用深度求索大模型生成解释总结
    """
    feature_info = feature_importance_df.to_csv(index=False)

    prompt = (
        "请根据以下特征重要性数据，分析该债券样本的预测结果：\n"
        "结合债券市场知识综合分析这些特征的影响\n"
        "数据如下：\n\n"
        f"{feature_importance_df.to_csv(index=False)}\n\n"
        "请用专业但易懂的中文成段说明，尽可能少的分条，但要有结构化一点。"
    )
    try:
        response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "deepseek-chat"),
            messages=[
                {"role": "system", "content": "您是债券市场分析师，擅长用SHAP值解释模型预测，使用markdown格式输出内容，使用加粗来强调，加粗的**与文字之间要有空格"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            stream=False
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"DeepSeek API 调用失败: {e}")
        return "网络错误，请修复网络后重试"

def calculate_r_os2(y_true, y_pred, benchmark):
    """
    计算 out-of-sample R² 相对于基准序列的 R2_os
    """
    numerator = np.sum((y_true - y_pred) ** 2)
    denominator = np.sum((y_true - benchmark) ** 2)
    return 1 - (numerator / denominator)

def handle_bond_regression(model_name, data, data_type):
    """
    处理信用利差回归任务的逻辑。
    """
    all_labels = ['AAA', 'AA+', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC', 'CC', 'C']
    def calculate_risk_metrics(y_true, y_pred, identifiers):
        # 确保y_pred转换为带索引的Series
        y_pred_series = pd.Series(y_pred, index=y_true.index, name='predicted_CS')

        # 基础回归指标
        from sklearn.metrics import mean_absolute_error, mean_squared_error
        # 'MAE': mean_absolute_error(y_true, y_pred_series),
        # 'RMSE': np.sqrt(mean_squared_error(y_true, y_pred_series))
        # 基础回归指标
        metrics = {
            'R²': round(r2_score(y_true, y_pred_series), 5),
            # 新增 R2_os，使用 identifiers 中的 CS_benchmark 列
            'R²_os': round(
                calculate_r_os2(
                    y_true.values,
                    y_pred_series.values,
                    identifiers['CS_benchmark'].loc[y_true.index].values
                ),
                5),
            'MAE': round(mean_absolute_error(y_true, y_pred_series), 5),
            'RMSE': round(np.sqrt(mean_squared_error(y_true, y_pred_series)), 5)
        }

        # 利差变动方向分析（需确保数据按时间排序）
        true_chg = y_true.diff().dropna()
        pred_chg = y_pred_series.diff().dropna()

        # 对齐索引（重要！）
        common_index = true_chg.index.intersection(pred_chg.index)
        metrics['方向准确率'] = round(np.mean((true_chg.loc[common_index] * pred_chg.loc[common_index]) > 0),5)

        # 波动率计算（年化）
        def annual_vol(s):
            return s.std() * np.sqrt(252) if isinstance(s, pd.Series) else np.std(s) * np.sqrt(252)

        metrics.update({
            '实际利差波动率': round(annual_vol(y_true),5),
            '预测利差波动率': round(annual_vol(y_pred_series),5),
            '残差波动率': round(annual_vol(y_true - y_pred_series),5)
        })

        # 信用VaR（考虑利差扩大风险）
        def credit_var(series, alpha=0.95):
            """计算利差扩大的VaR"""
            if isinstance(series, pd.Series):
                spread_changes = series.diff().dropna()
            else:
                spread_changes = np.diff(series)
            return np.percentile(spread_changes, 100 * alpha)

        metrics.update({
            '实际CS_VaR(95%)': round(credit_var(y_true),5),
            '预测CS_VaR(95%)': round(credit_var(y_pred_series),5),
            '残差VaR(95%)': round(credit_var(y_true - y_pred_series),5)
        })

        # 行业风险分析（添加空值保护）

        if '中信一级行业' in identifiers.columns:
            industry_metrics = []
            for industry in identifiers['中信一级行业'].unique():
                mask = identifiers['中信一级行业'] == industry
                try:
                    r2_val = r2_score(y_true[mask], y_pred_series[mask])
                    if np.isnan(r2_val):
                        r2_val = ""
                    industry_metrics.append({
                        '行业': industry,
                        '样本数': sum(mask),
                        '行业R²': round(r2_val,5),
                        '行业最大误差': round(np.max(np.abs(y_true[mask] - y_pred_series[mask])),5),
                        '行业风险溢价': round(y_true[mask].mean() - y_pred_series[mask].mean(),5)
                    })
                except Exception as e:
                    print(f"行业{industry}计算异常: {str(e)}")
            metrics['行业风险分析'] = pd.DataFrame(industry_metrics)

        # 压力测试指标（添加空值保护）
        # try:
        #     stress_threshold = y_true.quantile(0.9)
        #     stress_period = y_true >= stress_threshold
        #     metrics.update({
        #         '压力期R²': r2_score(y_true[stress_period], y_pred_series[stress_period]),
        #         '压力期平均偏差': np.mean(y_pred_series[stress_period] - y_true[stress_period])
        #     })
        # except Exception as e:
        #     print(f"压力测试计算异常: {str(e)}")

        return metrics



    # 选择数据列
    if data_type == "6W-财务+非财务":
        feature_columns = ([f'F{i}' for i in range(1, 48)] +
                           [f'M{i}' for i in range(1, 86)] +
                           [f'NF{i}' for i in range(1, 35)] +
                           [f'B{i}' for i in range(1, 6)])
        if model_name == "lasso":
            feature_columns = [f'F{i}' for i in range(1, 48)] + [f'M{i}' for i in range(1, 86)] + [f'B{i}' for i in
                                                                                                   range(1, 6)] + [
                                  f'NF{i}'
                                  for i in
                                  range(1,
                                        37)]
        # 导出表格内容
    elif data_type == "6W-仅财务":
        feature_columns = ([f'F{i}' for i in range(1, 48)] +
                           [f'M{i}' for i in range(1, 86)] +
                           [f'B{i}' for i in range(1, 6)])


    identifier_cols = ['债券代码', '债券名称', 'ym','所属产业板块', '中信一级行业', '债券一级分类','CS_benchmark', 'CS']
    feature_columns = [col for col in feature_columns if col in data.columns]
    identifier_cols = [col for col in identifier_cols if col in data.columns]
    X = data[feature_columns]
    y = data['CS']
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.2, random_state=42)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)
    test_identifiers = data.loc[X_test.index, identifier_cols].copy()

    if model_name == "XGboost":

        if data_type == "6W-财务+非财务":
            model_path = "model/xgboost_model_all_data_811.pkl"
        elif data_type == "6W-仅财务":
            model_path = "model/xgboost_model_only_caiwu_811.pkl"

        loaded_model = joblib.load(model_path)
        test_predictions = loaded_model.predict(X_test)
        shap_values = get_shap_values_xgb(loaded_model, X_test)
        X_test['预测结果'] = test_predictions

        # 执行风险计算
        risk_metrics = calculate_risk_metrics(
            y_test,
            test_predictions,
            test_identifiers
        )

        #模型的特征重要性排序
        feature_importance = np.abs(shap_values).mean(axis=0)
        feature_importance_df = pd.DataFrame({
            'Feature': feature_columns,
            'Importance': feature_importance
        }).sort_values(by='Importance', ascending=False).head(20)


        tezheng_df = pd.DataFrame({
            'Feature': feature_columns,
            'Importance': feature_importance
        }).sort_values(by='Importance', ascending=False).head(100)

        #调用大模型进行可解释性分析
        mapping_df = pd.read_csv("file/content_tezheng.csv")  # 请确保文件路径正确
        # 假设 CSV 第一列名称为 "特征名"，第二列名称为 "实际含义"
        mapping_dict = dict(zip(mapping_df["特征名"], mapping_df["实际含义"]))
        feature_importance_df["特征含义"] = feature_importance_df["Feature"].map(mapping_dict)
        tezheng_df["特征含义"] = tezheng_df["Feature"].map(mapping_dict)
        # 调用大模型生成解释总结文本
        explanation_text = get_llm_explanation(feature_importance_df)
        # explanation_text = '好'
        print("模型解释总结：\n", explanation_text)

        # 输出每一行的特征重要性
        shap_values_df = pd.DataFrame(shap_values, columns=feature_columns, index=X_test.index)
        # 将测试数据的标识信息（如债券代码、债券名称）提取出来，确保索引与 X_test 一致
        per_instance_info = test_identifiers.copy()
        # 合并标识信息、预测结果以及每条数据的特征重要性
        per_instance_importance = pd.concat([per_instance_info.reset_index(drop=True),
                                             X_test['预测结果'].reset_index(drop=True),
                                             shap_values_df.reset_index(drop=True)], axis=1)

        print("feature_import type:", type(per_instance_importance))


    elif model_name == "Adaboost":

        if data_type == "6W-财务+非财务":
            model_path = "model/adaboost_model_all_data_811.pkl"
        elif data_type == "6W-仅财务":
            model_path = "model/adaboost_model_only_caiwu_811.pkl"

        loaded_model = joblib.load(model_path)
        test_predictions = loaded_model.predict(X_test)
        shap_values = get_shap_values_ada(loaded_model, X_test)
        X_test['预测结果'] = test_predictions

        risk_metrics = calculate_risk_metrics(
            y_test,
            test_predictions,
            test_identifiers
        )


        feature_importance = np.abs(shap_values).mean(axis=0)
        feature_importance_df = pd.DataFrame({
            'Feature': feature_columns,
            'Importance': feature_importance
        }).sort_values(by='Importance', ascending=False).head(20)

        tezheng_df = pd.DataFrame({
            'Feature': feature_columns,
            'Importance': feature_importance
        }).sort_values(by='Importance', ascending=False).head(100)


        mapping_df = pd.read_csv("file/content_tezheng.csv")  # 请确保文件路径正确
        # 假设 CSV 第一列名称为 "特征名"，第二列名称为 "实际含义"
        mapping_dict = dict(zip(mapping_df["特征名"], mapping_df["实际含义"]))
        feature_importance_df["特征含义"] = feature_importance_df["Feature"].map(mapping_dict)
        tezheng_df["特征含义"] = tezheng_df["Feature"].map(mapping_dict)
        # 调用大模型生成解释总结文本
        explanation_text = get_llm_explanation(feature_importance_df)
        # explanation_text = '好'
        print("模型解释总结：\n", explanation_text)

        # 输出每一行的特征重要性
        shap_values_df = pd.DataFrame(shap_values, columns=feature_columns, index=X_test.index)
        # 将测试数据的标识信息（如债券代码、债券名称）提取出来，确保索引与 X_test 一致
        per_instance_info = test_identifiers.copy()
        # 合并标识信息、预测结果以及每条数据的特征重要性
        per_instance_importance = pd.concat([per_instance_info.reset_index(drop=True),
                                             X_test['预测结果'].reset_index(drop=True),
                                             shap_values_df.reset_index(drop=True)], axis=1)



    elif model_name == "GBDT":

        if data_type == "6W-财务+非财务":
            model_path = "model/gbdt_model_all_data_811.pkl"
        elif data_type == "6W-仅财务":
            model_path = "model/gbdt_model_only_caiwu_811.pkl"

        loaded_model = joblib.load(model_path)
        test_predictions = loaded_model.predict(X_test)
        shap_values = get_shap_values_xgb(loaded_model, X_test)
        X_test['预测结果'] = test_predictions

        risk_metrics = calculate_risk_metrics(
            y_test,
            test_predictions,
            test_identifiers
        )


        # 保存特征重要性
        feature_importance = np.abs(shap_values).mean(axis=0)
        feature_importance_df = pd.DataFrame({
            'Feature': feature_columns,
            'Importance': feature_importance
        }).sort_values(by='Importance', ascending=False).head(20)

        tezheng_df = pd.DataFrame({
            'Feature': feature_columns,
            'Importance': feature_importance
        }).sort_values(by='Importance', ascending=False).head(100)

        mapping_df = pd.read_csv("file/content_tezheng.csv")  # 请确保文件路径正确
        # 假设 CSV 第一列名称为 "特征名"，第二列名称为 "实际含义"
        mapping_dict = dict(zip(mapping_df["特征名"], mapping_df["实际含义"]))
        feature_importance_df["特征含义"] = feature_importance_df["Feature"].map(mapping_dict)
        tezheng_df["特征含义"] = tezheng_df["Feature"].map(mapping_dict)
        # 调用大模型生成解释总结文本
        explanation_text = get_llm_explanation(feature_importance_df)
        # explanation_text = '好'
        print("模型解释总结：\n", explanation_text)

        # 输出每一行的特征重要性
        shap_values_df = pd.DataFrame(shap_values, columns=feature_columns, index=X_test.index)
        # 将测试数据的标识信息（如债券代码、债券名称）提取出来，确保索引与 X_test 一致
        per_instance_info = test_identifiers.copy()
        # 合并标识信息、预测结果以及每条数据的特征重要性
        per_instance_importance = pd.concat([per_instance_info.reset_index(drop=True),
                                             X_test['预测结果'].reset_index(drop=True),
                                             shap_values_df.reset_index(drop=True)], axis=1)
        #print("feature_import type:", type(feature_import))

    elif model_name == "RF":

        if data_type == "6W-财务+非财务":
            model_path = "model/rf_model_all_data_811.pkl"
        elif data_type == "20W-仅财务":
            model_path = "model/rf_model_only_caiwua_811.pkl"

        X_test = X_test[:10]

        loaded_model = joblib.load(model_path)
        test_predictions = loaded_model.predict(X_test)
        shap_values = get_shap_values_xgb(loaded_model, X_test)
        X_test['预测结果'] = test_predictions

        risk_metrics = calculate_risk_metrics(
            y_test,
            test_predictions,
            test_identifiers
        )


        # 保存特征重要性
        feature_importance = np.abs(shap_values).mean(axis=0)
        feature_importance_df = pd.DataFrame({
            'Feature': feature_columns,
            'Importance': feature_importance
        }).sort_values(by='Importance', ascending=False).head(20)

        tezheng_df = pd.DataFrame({
            'Feature': feature_columns,
            'Importance': feature_importance
        }).sort_values(by='Importance', ascending=False).head(100)

        mapping_df = pd.read_csv("file/content_tezheng.csv")  # 请确保文件路径正确
        # 假设 CSV 第一列名称为 "特征名"，第二列名称为 "实际含义"
        mapping_dict = dict(zip(mapping_df["特征名"], mapping_df["实际含义"]))
        feature_importance_df["特征含义"] = feature_importance_df["Feature"].map(mapping_dict)
        tezheng_df["特征含义"] = tezheng_df["Feature"].map(mapping_dict)
        # 调用大模型生成解释总结文本
        explanation_text = get_llm_explanation(feature_importance_df)
        # explanation_text = '好'
        print("模型解释总结：\n", explanation_text)

        # 输出每一行的特征重要性
        shap_values_df = pd.DataFrame(shap_values, columns=feature_columns, index=X_test.index)
        # 将测试数据的标识信息（如债券代码、债券名称）提取出来，确保索引与 X_test 一致
        per_instance_info = test_identifiers.copy()
        # 合并标识信息、预测结果以及每条数据的特征重要性
        per_instance_importance = pd.concat([per_instance_info.reset_index(drop=True),
                                             X_test['预测结果'].reset_index(drop=True),
                                             shap_values_df.reset_index(drop=True)], axis=1)

    if model_name == "lasso":

        if data_type == "6W-财务+非财务":
            model_path = "model/lasso_model_all_data_811.pkl"
        elif data_type == "6W-仅财务":
            model_path = "model/lasso_model_only_caiwu_811.pkl"

        loaded_model = joblib.load(model_path)
        test_predictions = loaded_model.predict(X_test)
        shap_values = get_shap_values_lasso(loaded_model, X_test)
        X_test['预测结果'] = test_predictions

        # 执行风险计算
        risk_metrics = calculate_risk_metrics(
            y_test,
            test_predictions,
            test_identifiers
        )

        #模型的特征重要性排序
        feature_importance = np.abs(shap_values).mean(axis=0)
        feature_importance_df = pd.DataFrame({
            'Feature': feature_columns,
            'Importance': feature_importance
        }).sort_values(by='Importance', ascending=False).head(20)


        tezheng_df = pd.DataFrame({
            'Feature': feature_columns,
            'Importance': feature_importance
        }).sort_values(by='Importance', ascending=False).head(100)

        #调用大模型进行可解释性分析
        mapping_df = pd.read_csv("file/content_tezheng.csv")  # 请确保文件路径正确
        # 假设 CSV 第一列名称为 "特征名"，第二列名称为 "实际含义"
        mapping_dict = dict(zip(mapping_df["特征名"], mapping_df["实际含义"]))
        feature_importance_df["特征含义"] = feature_importance_df["Feature"].map(mapping_dict)
        tezheng_df["特征含义"] = tezheng_df["Feature"].map(mapping_dict)
        # 调用大模型生成解释总结文本
        explanation_text = get_llm_explanation(feature_importance_df)
        # explanation_text = '好'
        print("模型解释总结：\n", explanation_text)

        # 输出每一行的特征重要性
        shap_values_df = pd.DataFrame(shap_values, columns=feature_columns, index=X_test.index)
        # 将测试数据的标识信息（如债券代码、债券名称）提取出来，确保索引与 X_test 一致
        per_instance_info = test_identifiers.copy()
        # 合并标识信息、预测结果以及每条数据的特征重要性
        per_instance_importance = pd.concat([per_instance_info.reset_index(drop=True),
                                             X_test['预测结果'].reset_index(drop=True),
                                             shap_values_df.reset_index(drop=True)], axis=1)

        print("feature_import type:", type(per_instance_importance))


    biaoge_df = test_identifiers
    biaoge_df = biaoge_df
    biaoge_df['预测结果'] = test_predictions
    # 保留5位小数
    biaoge_df['CS_benchmark'] = biaoge_df['CS_benchmark'].round(5)
    biaoge_df['预测结果'] = biaoge_df['预测结果'].round(5)
    # 重置索引
    biaoge_df = biaoge_df.reset_index(drop=True)

    return X_test,  biaoge_df, per_instance_importance, feature_columns,risk_metrics,feature_importance_df,explanation_text,tezheng_df


def handle_credit_rating(model_name, data, data_type, industry_type):
    """
    处理信用评级任务的逻辑。
    """
    all_labels = ['AAA', 'AA+', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC', 'CC', 'C']
    global model_path
    identifier_cols = ['债券代码', '债券名称','ym', '所属产业板块', '中信一级行业', '债券一级分类', '信用评级']
    identifier_cols = [col for col in identifier_cols if col in data.columns]

    if data_type == "6W-财务+非财务" or data_type == "20W-财务+非财务":
        # 注意此处整体缩进
        columns_to_select = [f'F{i}' for i in range(1, 48)] + [f'M{i}' for i in range(1, 86)] + [f'B{i}' for i in
                                                                                                 range(1, 6)] + [
                                f'NF{i}' for i in range(1, 38)]
    elif data_type == "6W-仅财务":
        # 此处与外层 if 对齐
        columns_to_select = [f'F{i}' for i in range(1, 48)] + [f'M{i}' for i in range(1, 86)] + [f'B{i}' for i in
                                                                                                 range(1, 6)]

    if model_name == "MLP":
        if data_type == "6W-财务+非财务" :
            columns_to_select = [f'F{i}' for i in range(1, 48)] + [f'M{i}' for i in range(1, 86)] + [f'NF{i}' for i in
                                                                                                     range(1, 31)] + [
                                    f'B{i}' for i in range(1, 6)]
        elif data_type == "6W-仅财务" or data_type == "20W-财务+非财务":
            columns_to_select = [f'F{i}' for i in range(1, 48)] + [f'M{i}' for i in range(1, 86)] + [f'B{i}' for i in range(1, 6)]
    if model_name == 'Bert':
        columns_to_select = (
                [f'NF{i}' for i in range(1, 36)] +
                [f'F{i}' for i in range(1, 48)] +
                [f'M{i}' for i in range(1, 86)])



    columns_to_select = [col for col in columns_to_select if col in data.columns]
    a = 0
    print(industry_type)
    if industry_type != "全产业":

        if industry_type == "房地产" or industry_type == "电力及公用事业" or industry_type == "建筑":
            data = data[data['所属产业板块'] == '基础设施与地产产业']
            new_industry_type = industry_type.replace("产业", "")
            data = data[data['中信一级行业'] == new_industry_type]
            a = 2
        else:
            data = data[data['所属产业板块'] == industry_type]
            a = 1


    if model_name != 'RF':

        X_df = data[columns_to_select]  # 保持DataFrame结构
        y = data['信用评级']
        label_encoder = LabelEncoder()
        y_encoded = label_encoder.fit_transform(y)

        # 划分数据集 (8:1:1)
        X = X_df
        X_train, X_temp, y_train, y_temp = train_test_split(X, y_encoded, test_size=0.2, random_state=42)
        X_val, X_test2, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)
        print(X_test2.shape)
        test_identifiers = data.loc[X_test2.index, identifier_cols].copy()
        # print("数据列名:", data.columns.tolist())
        # print("筛选后的 columns_to_select:", columns_to_select)
    else:
        data['month'] = pd.to_datetime(data['ym'], format='%Y-%m-%d')

        # 设置随机种子，确保结果可重复
        random_seed = 42

        # 打乱数据顺序
        #df = data.sample(frac=1, random_state=random_seed).reset_index(drop=True)
        df = data.sample(frac=1, random_state=random_seed)  # 保留原始索引
        # 数据划分比例
        train_ratio = 0.8  # 训练集比例
        val_ratio = 0.1  # 验证集比例
        test_ratio = 0.1  # 测试集比例

        # 计算样本数
        n = len(df)
        train_end = int(train_ratio * n)
        val_end = train_end + int(val_ratio * n)

        # 按比例划分数据集
        train_data = df.iloc[:train_end]
        val_data = df.iloc[train_end:val_end]
        test_data = df.iloc[val_end:]

        # 检查划分结果
        print(f"训练集样本数: {len(train_data)}")
        print(f"验证集样本数: {len(val_data)}")
        print(f"测试集样本数: {len(test_data)}")

        # 特征与目标变量
        X_train = train_data.iloc[:, 10:].drop(columns=['month'], errors='ignore').apply(pd.to_numeric,
                                                                                         errors='coerce').fillna(0)
        y_train = train_data['信用评级']

        X_val = val_data.iloc[:, 10:].drop(columns=['month'], errors='ignore').apply(pd.to_numeric,
                                                                                     errors='coerce').fillna(0)
        y_val = val_data['信用评级']

        X_test2 = test_data.iloc[:, 10:].drop(columns=['month'], errors='ignore').apply(pd.to_numeric,
                                                                                       errors='coerce').fillna(0)
        y_test = test_data['信用评级']
        #test_identifiers = data.loc[X_test2.index, identifier_cols].copy()
        test_identifiers = test_data[identifier_cols].copy()

    if model_name == "CNN":

        X_train = X_train.values.reshape(X_train.shape[0], X_train.shape[1], 1)
        X_val = X_val.values.reshape(X_val.shape[0], X_val.shape[1], 1)
        X_test = X_test2.values.reshape(X_test2.shape[0], X_test2.shape[1], 1)

        if data_type == "6W-财务+非财务":
            if a == 0:
                model_path ="model/CNN/6W-财务+非财务/model_all-6w-all.h5"
            elif a == 1:
                model_path = f"model/CNN/6W-财务+非财务/model_{industry_type}-6w-all.h5"
            elif a == 2:
                new_industry_type = industry_type.replace("产业", "")
                model_path = f"model/CNN/6W-财务+非财务/model_{industry_type}-6w-all.h5"
        elif data_type == "6W-仅财务":

            if a == 0:
                model_path ="model/CNN/6W-仅财务/model_all-6w-only.h5"
            elif a == 1:
                model_path = f"model/CNN/6W-仅财务/model_{industry_type}-6w_only.h5"
            elif a == 2:
                new_industry_type = industry_type.replace("产业", "")
                model_path = f"model/CNN/6W-仅财务/model_{industry_type}-6w_only.h5"


        elif data_type == "20W-财务+非财务":
            if a == 0:
                model_path ="model/CNN/20W/model_all_20W.h5"
            elif a == 1:
                model_path = f"model/CNN/20W/model_{industry_type}-_20W.h5"
            elif a == 2:
                new_industry_type = industry_type.replace("产业", "")
                model_path = f"model/CNN/20W/model_{industry_type}-_20W.h5"

        if data_type == "6W-财务+非财务"or data_type == "20W-财务+非财务":

            columns_to_select = (
                    [f'F{i}' for i in range(1, 48)] + [f'M{i}' for i in range(1, 86)] + [f'B{i}' for i in range(1, 6)]+[f'NF{i}' for i in range(1, 36)])

        elif data_type == "6W-仅财务" :

            columns_to_select = (
                    [f'F{i}' for i in range(1, 48)] + [f'M{i}' for i in range(1, 86)] + [f'B{i}' for i in range(1, 6)])



        columns_to_select = [col for col in columns_to_select if col in data.columns]
        loaded_model = models.load_model(model_path)
        test_predictions= np.argmax(loaded_model.predict(X_test), axis=1)
        shap_values_normalized = get_shap_values_cnn(loaded_model, X_train, X_test)
        shap_aggregated = np.abs(shap_values_normalized).mean(axis=0).mean(axis=-1).squeeze()

        X_test_df = pd.DataFrame(X_test2, columns=columns_to_select)
        X_test_df['预测结果'] = test_predictions
        test_predictions_2 = test_predictions
        test_predictions = label_encoder.inverse_transform(test_predictions)
        feature_names = data[columns_to_select].columns.tolist()
        # 创建DataFrame存储特征重要性
        feature_importance_df = pd.DataFrame({
            'Feature': feature_names,
            'Importance': shap_aggregated
        }).sort_values(by='Importance', ascending=False).head(20)

        tezheng_df = pd.DataFrame({
            'Feature': feature_names,
            'Importance': shap_aggregated
        }).sort_values(by='Importance', ascending=False).head(100)

        mapping_df = pd.read_csv("file/content_tezheng.csv")  # 请确保文件路径正确
        # 假设 CSV 第一列名称为 "特征名"，第二列名称为 "实际含义"
        mapping_dict = dict(zip(mapping_df["特征名"], mapping_df["实际含义"]))
        feature_importance_df["特征含义"] = feature_importance_df["Feature"].map(mapping_dict)
        tezheng_df["特征含义"] = tezheng_df["Feature"].map(mapping_dict)
        # 调用大模型生成解释总结文本
        explanation_text = get_llm_explanation(feature_importance_df)
        # explanation_text = '好'
        print("模型解释总结：\n", explanation_text)

        accuracy = accuracy_score(y_test, test_predictions_2)
        f1 = f1_score(y_test, test_predictions_2, average='macro')
        recall = recall_score(y_test, test_predictions_2, average='macro')
        # 计算多分类任务评价指标（target_names 也可以直接使用 label_encoder.classes_）
        class_report = classification_report(y_test,test_predictions_2, target_names=label_encoder.classes_)
        confusion_mat = confusion_matrix(y_test, test_predictions_2)
        print(len(class_report))

        accuracy = round(accuracy, 5)
        f1 = round(f1, 5)
        recall = round(recall, 5)

        print("准确率:", accuracy)
        print("F1 得分:", f1)
        print("召回率:", recall)
        print("分类报告:\n", class_report)
        # print("混淆矩阵:\n", confusion_mat)

        metrics = {
            "准确率": accuracy,
            "召回率": recall,
            "F1 得分": f1,
            "分类报告": class_report
        }

        # per_instance_importance = ''
        per_instance_importance = pd.DataFrame()
    elif model_name == "MLP":

        if data_type == "6W-财务+非财务":
            if a == 0:
                model_path ="model/MLP/6W/all_mlp_model.h5"
            elif a == 1:
                model_path = f"model/MLP/6W/{industry_type}_mlp_model.h5"
            elif a == 2:
                model_path = f"model/MLP/6W/{industry_type}_mlp_model.h5"

        elif data_type == "6W-仅财务":
            if a == 0:
                model_path = "model/MLP/6W-jincaiwu/all_mlp_model.h5"
            elif a == 1:
                model_path = f"model/MLP/6W-jincaiwu/{industry_type}_mlp_model.h5"
            elif a == 2:
                model_path = f"model/MLP/6W-jincaiwu/{industry_type}_mlp_model.h5"
        elif data_type == "20W-财务+非财务":
            if a == 0:
                model_path = "model/MLP/20W/all_mlp_model.h5"
            elif a == 1:
                model_path = f"model/MLP/20W/{industry_type}_mlp_model.h5"
            elif a == 2:
                model_path = f"model/MLP/20W/{industry_type}_mlp_model.h5"


        #导入模型
        loaded_model = models.load_model(model_path)
        #loaded_model = joblib.load(model_path)

        #预测 标签
        X_train = X_train.values
        X_test3 = X_test2
        X_test2 = X_test2.values
        #y_pred = loaded_model.predict(X_test2)
        test_predictions = np.argmax(loaded_model.predict(X_test2), axis=1)
        test_predictions = label_encoder.inverse_transform(test_predictions)

        #特征重要性  N（数据数量）×167
        shap_values_normalized = get_shap_values_MLP(loaded_model, X_train, X_test2)
        shap_values_reduced = shap_values_normalized.mean(axis=-1)

        print(shap_values_normalized.shape)
        shap_aggregated = np.abs(shap_values_normalized).mean(axis=0).mean(axis=-1).squeeze()
        print(shap_aggregated.shape)



        X_test_df = pd.DataFrame(X_test2, columns=columns_to_select)
        X_test_df['预测结果'] = test_predictions
        feature_names = data[columns_to_select].columns.tolist()
        feature_importance_df = pd.DataFrame({
            'Feature': feature_names,
            'Importance': shap_aggregated
        }).sort_values(by='Importance', ascending=False).head(20)

        tezheng_df = pd.DataFrame({
            'Feature': feature_names,
            'Importance': shap_aggregated
        }).sort_values(by='Importance', ascending=False).head(100)

        mapping_df = pd.read_csv("file/content_tezheng.csv")  # 请确保文件路径正确
        # 假设 CSV 第一列名称为 "特征名"，第二列名称为 "实际含义"
        mapping_dict = dict(zip(mapping_df["特征名"], mapping_df["实际含义"]))
        feature_importance_df["特征含义"] = feature_importance_df["Feature"].map(mapping_dict)
        tezheng_df["特征含义"] = tezheng_df["Feature"].map(mapping_dict)
        # 调用大模型生成解释总结文本
        explanation_text = get_llm_explanation(feature_importance_df)
        # explanation_text = '好'
        print("模型解释总结：\n", explanation_text)

        # 输出每一行的特征重要性
        shap_values_df = pd.DataFrame(shap_values_reduced, columns=columns_to_select , index=X_test_df[:100].index,)
        # 将测试数据的标识信息（如债券代码、债券名称）提取出来，确保索引与 X_test 一致
        per_instance_info = test_identifiers.copy()
        # 合并标识信息、预测结果以及每条数据的特征重要性
        per_instance_importance = pd.concat([per_instance_info.reset_index(drop=True),
                                             X_test_df['预测结果'].reset_index(drop=True),
                                             shap_values_df.reset_index(drop=True)], axis=1)

        accuracy = accuracy_score(y_test, test_predictions)
        y_test_labels = label_encoder.inverse_transform(y_test)
        #y_pred_labels = label_encoder.inverse_transform(y_pred)
        y_pred_labels = test_predictions
        accuracy = accuracy_score(y_test_labels, y_pred_labels)
        f1 = f1_score(y_test_labels, y_pred_labels, average='macro')
        recall = recall_score(y_test_labels, y_pred_labels, average='macro')
        # 计算多分类任务评价指标（target_names 也可以直接使用 label_encoder.classes_）
        class_report = classification_report(y_test_labels, y_pred_labels, target_names=label_encoder.classes_)
        confusion_mat = confusion_matrix(y_test_labels, y_pred_labels)
        print(len(class_report))

        accuracy = round(accuracy, 5)
        f1 = round(f1, 5)
        recall = round(recall, 5)

        print("准确率:", accuracy)
        print("F1 得分:", f1)
        print("召回率:", recall)
        print("分类报告:\n", class_report)
       # print("混淆矩阵:\n", confusion_mat)

        metrics = {
            "准确率": accuracy,
            "召回率": recall,
            "F1 得分": f1,
            "分类报告": class_report
        }

    elif model_name == "GNN":

        if data_type == "6W-财务+非财务":
            if a == 0:
                model_path ="model/GNN/6W/all_GAT_model.pth"
            elif a == 1:
                model_path = f"model/GNN/6W/{industry_type}_GAT_model.pth"
            elif a == 2:
                model_path = f"model/GNN/6W/{industry_type}_GAT_model.pth"

        elif data_type == "6W-仅财务":

            if a == 0:
                model_path = "model/GNN/6W-jincaiwu/all_GAT_model.pth"
            elif a == 1:
                model_path = f"model/GNN/6W-jincaiwu/{industry_type}_GAT_model.pth"
            elif a == 2:
                model_path = f"model/GNN/6W-jincaiwu/{industry_type}_GAT_model.pth"
        elif data_type == "20W-财务+非财务":
            if a == 0:
                model_path = "model/GNN/20W/all_GAT_model.pth"
            elif a == 1:
                model_path = f"model/GNN/20W/{industry_type}_GAT_model.pth"
            elif a == 2:
                model_path = f"model/GNN/20W/{industry_type}_GAT_model.pth"

        # GAT model definition
        class GAT(nn.Module):
            def __init__(self, input_channel, out_channel):
                super(GAT, self).__init__()
                self.gcn1 = GATConv(input_channel, 8)
                self.gcn2 = GATConv(8, 64)
                self.gcn3 = GATConv(64, 32)
                self.gcn4 = GATConv(32, out_channel)

                self.lin1 = nn.Linear(8 + 64 + 32 + out_channel, 5000)
                self.lin2 = nn.Linear(5000, 1024)
                self.lin3 = nn.Linear(1024, 10)

            def forward(self, batch):
                batch_size = batch.batch.max() + 1
                x = batch.x
                edge_index = batch.edge_index
                batch_idx = batch.batch

                x1 = F.relu(self.gcn1(x, edge_index))
                out1 = global_max_pool(x1, batch_idx)

                x2 = F.relu(self.gcn2(x1, edge_index))
                out2 = global_max_pool(x2, batch_idx)

                x3 = F.relu(self.gcn3(x2, edge_index))
                out3 = global_max_pool(x3, batch_idx)

                x4 = F.relu(self.gcn4(x3, edge_index))
                out4 = global_max_pool(x4, batch_idx)

                final_out = torch.cat([out1, out2, out3, out4], dim=1)

                final_out = F.relu(self.lin1(final_out))
                final_out = F.relu(self.lin2(final_out))
                final_out = self.lin3(final_out)

                return final_out


        loaded_model = GAT(input_channel=1, out_channel=10)
        # 加载保存的模型权重
        # model.load_state_dict(torch.load(model_path))  # 使用保存时的文件路径
        loaded_model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))


        graphs = []
        labels = []
        df = X_test2

        if data_type == "6W-财务+非财务":
            for i, row in df.iterrows():
                feature_values = row.values
                feature_columns = [f"B{i}" for i in range(1, 6)] + [f"F{i}" for i in range(1, 48)] + [f"M{i}" for i in
                                                                                                      range(1, 86)]+[f"NF{i}" for i in
                                                                                                      range(1, 31)]
                feature_values = row[feature_columns].fillna(0).values.astype(float)
                dot_product_matrix = np.outer(feature_values, feature_values)

                edge_index = []
                edge_attr = []

                for j in range(167):
                    for k in range(j + 1, 167):
                        if dot_product_matrix[j, k] >= 0.9:
                            edge_index.append([j, k])
                            edge_attr.append(dot_product_matrix[j, k])

                edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
                edge_attr = torch.tensor(edge_attr, dtype=torch.float)

                x = torch.tensor(feature_values, dtype=torch.float).view(-1, 1)

                y_test_labels = label_encoder.inverse_transform(y_test)
                labels = y_test_labels
                encoder = LabelEncoder()
                labels = encoder.fit_transform(labels)  # 将字符串标签转换为整数标签
                graph = Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=torch.tensor(labels, dtype=torch.long))
                graphs.append(graph)

        elif data_type == "6W-仅财务" or data_type == "20W-财务+非财务":
            for i, row in df.iterrows():
                feature_values = row.values
                feature_columns = [f"B{i}" for i in range(1, 6)] + [f"F{i}" for i in range(1, 48)] + [f"M{i}" for i in
                                                                                                      range(1, 86)]
                feature_values = row[feature_columns].fillna(0).values.astype(float)
                dot_product_matrix = np.outer(feature_values, feature_values)

                edge_index = []
                edge_attr = []

                for j in range(137):
                    for k in range(j + 1, 137):
                        if dot_product_matrix[j, k] >= 0.9:
                            edge_index.append([j, k])
                            edge_attr.append(dot_product_matrix[j, k])

                edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
                edge_attr = torch.tensor(edge_attr, dtype=torch.float)

                x = torch.tensor(feature_values, dtype=torch.float).view(-1, 1)

                y_test_labels = label_encoder.inverse_transform(y_test)
                labels = y_test_labels
                encoder = LabelEncoder()
                labels = encoder.fit_transform(labels)  # 将字符串标签转换为整数标签
                graph = Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=torch.tensor(labels, dtype=torch.long))
                graphs.append(graph)

        loader = GeometricDataLoader(graphs, batch_size=32)


        #预测 标签
        loaded_model.eval()
        all_preds = []
        all_labels = []
        with torch.no_grad():
            for data_ in loader:
                out = loaded_model(data_)
                preds = out.argmax(dim=1) # 每一个batch的预测结果 32个
                all_preds.append(preds)
                all_labels.append(data_.y)
        print(all_preds)
        print(all_labels)
        print(type(all_preds))
        print(type(all_labels))

        X_train = X_train.values
        X_test3 = X_test2
        X_test2 = X_test2.values
        y_pred = all_preds
        # 合并 y_pred 中的所有张量
        y_pred = torch.cat(y_pred)
        # 将合并后的张量转换为 NumPy 数组
        y_pred = y_pred.numpy()
        print(y_pred)

        y_pred = label_encoder.inverse_transform(y_pred)
        print(y_pred)

        if data_type == "6W-财务+非财务":
            if a == 0:
                model_path ="model/MLP/6W/all_mlp_model.h5"
            elif a == 1:
                model_path = f"model/MLP/6W/{industry_type}_mlp_model.h5"
            elif a == 2:
                model_path = f"model/MLP/6W/{industry_type}_mlp_model.h5"

        elif data_type == "6W-仅财务":
            if a == 0:
                model_path = "model/MLP/6W-jincaiwu/all_mlp_model.h5"
            elif a == 1:
                model_path = f"model/MLP/6W-jincaiwu/{industry_type}_mlp_model.h5"
            elif a == 2:
                model_path = f"model/MLP/6W-jincaiwu/{industry_type}_mlp_model.h5"
        elif data_type == "20W-财务+非财务":
            if a == 0:
                model_path = "model/MLP/20W/all_mlp_model.h5"
            elif a == 1:
                model_path = f"model/MLP/20W/{industry_type}_mlp_model.h5"
            elif a == 2:
                model_path = f"model/MLP/20W/{industry_type}_mlp_model.h5"


        loaded_model_ = models.load_model(model_path)
        #特征重要性  N（数据数量）×167

        shap_values_normalized = get_shap_values_MLP(loaded_model_, X_train, X_test2)
        shap_values_reduced = shap_values_normalized.mean(axis=-1)

        print(shap_values_normalized.shape)
        shap_aggregated = np.abs(shap_values_normalized).mean(axis=0).mean(axis=-1).squeeze()
        print(shap_aggregated.shape)



        X_test_df = pd.DataFrame(X_test2, columns=columns_to_select)
        X_test_df['预测结果'] = y_pred

        feature_names = data[columns_to_select].columns.tolist()
        feature_importance_df = pd.DataFrame({
            'Feature': feature_names,
            'Importance': shap_aggregated
        }).sort_values(by='Importance', ascending=False).head(20)

        tezheng_df = pd.DataFrame({
            'Feature': feature_names,
            'Importance': shap_aggregated
        }).sort_values(by='Importance', ascending=False).head(100)

        mapping_df = pd.read_csv("file/content_tezheng.csv")  # 请确保文件路径正确
        # 假设 CSV 第一列名称为 "特征名"，第二列名称为 "实际含义"
        mapping_dict = dict(zip(mapping_df["特征名"], mapping_df["实际含义"]))
        feature_importance_df["特征含义"] = feature_importance_df["Feature"].map(mapping_dict)
        tezheng_df["特征含义"] = tezheng_df["Feature"].map(mapping_dict)
        # 调用大模型生成解释总结文本
        explanation_text = get_llm_explanation(feature_importance_df)
        # explanation_text = '好'
        print("模型解释总结：\n", explanation_text)

        # 输出每一行的特征重要性
        # shap_values_df = pd.DataFrame(shap_values_reduced, columns=columns_to_select , index=X_test_df.index,)
        # # 将测试数据的标识信息（如债券代码、债券名称）提取出来，确保索引与 X_test 一致
        # per_instance_info = test_identifiers.copy()
        # # 合并标识信息、预测结果以及每条数据的特征重要性
        # per_instance_importance = pd.concat([per_instance_info.reset_index(drop=True),
        #                                      X_test_df['预测结果'].reset_index(drop=True),
        #                                      shap_values_df.reset_index(drop=True)], axis=1)

        accuracy = accuracy_score(y_test, y_pred)
        y_test_labels = label_encoder.inverse_transform(y_test)
        #y_pred_labels = label_encoder.inverse_transform(y_pred)
        y_pred_labels = y_pred
        accuracy = accuracy_score(y_test_labels, y_pred_labels)
        f1 = f1_score(y_test_labels, y_pred_labels, average='macro')
        recall = recall_score(y_test_labels, y_pred_labels, average='macro')
        # 计算多分类任务评价指标（target_names 也可以直接使用 label_encoder.classes_）
        class_report = classification_report(y_test_labels, y_pred_labels, target_names=label_encoder.classes_)
        confusion_mat = confusion_matrix(y_test_labels, y_pred_labels)
        print(len(class_report))

        accuracy = round(accuracy, 5)
        f1 = round(f1, 5)
        recall = round(recall, 5)

        print("准确率:", accuracy)
        print("F1 得分:", f1)
        print("召回率:", recall)
        print("分类报告:\n", class_report)
       # print("混淆矩阵:\n", confusion_mat)

        metrics = {
            "准确率": accuracy,
            "召回率": recall,
            "F1 得分": f1,
            "分类报告": class_report
        }

        # per_instance_importance = ''
        per_instance_importance = pd.DataFrame()



    elif model_name == "RF":

        if data_type == "6W-财务+非财务":
            if a == 0:
                model_path = "model/RF/10000只债券（6w财务+非财务）/RF分类_10000_全产业_财务+非财务_model.pkl"
            elif a == 1:
                model_path = f"model/RF/10000只债券（6w财务+非财务）/RF分类_10000_{industry_type}_财务+非财务_model.pkl"
            elif a == 2:
                model_path = f"model/RF/10000只债券（6w财务+非财务）/RF分类_10000_一级行业_{industry_type}_财务+非财务_model.pkl"

        elif data_type == "6W-仅财务":
            if a == 0:
                model_path = "model/RF/10000只债券（6w财务+非财务）/RF分类_10000_全产业_仅财务_model.pkl"
            elif a == 1:
                model_path = f"model/RF/10000只债券（6w财务+非财务）/RF分类_10000_{industry_type}_仅财务_model.pkl"
            elif a == 2:
                model_path = f"model/RF/10000只债券（6w财务+非财务）/RF分类_10000_一级行业_{industry_type}_仅财务_model.pkl"

        elif data_type == "20W-财务+非财务":
            if a == 0:
                model_path ="model/RF/10000只债券（20w财务）/RF分类_10000_全产业_20w财务_model.pkl"
            elif a == 1:
                model_path = f"model/RF/10000只债券（20w财务）/RF分类_10000_{industry_type}_20w财务_model.pkl"
            elif a == 2:
                model_path = f"model/RF/10000只债券（20w财务）/RF分类_10000_一级行业_{industry_type}_20w财务_model.pkl"

        if data_type == "6W-财务+非财务":
            columns_to_select = (

                    [f'NF{i}' for i in range(1, 36)] +
                    [f'B{i}' for i in range(1, 6)] +
                    [f'F{i}' for i in range(1, 48)] +
                    [f'M{i}' for i in range(1, 86)])

        elif data_type == "6W-仅财务" or data_type == "20W-财务+非财务":
            columns_to_select = (
                    [f'B{i}' for i in range(1, 6)]+
                    [f'F{i}' for i in range(1, 48)] +
                    [f'M{i}' for i in range(1, 86)])
        columns_to_select = [col for col in columns_to_select if col in data.columns]
        loaded_model = joblib.load(model_path)
        X_test2 = X_test2[columns_to_select]
        #X_test2 = X_test2[:50]
        test_predictions = loaded_model.predict(X_test2)
        print("预测完成")
        shap_values = get_shap_values_xgb_pingjirf(loaded_model, X_test2)
        print("特征重要性提取完成")
        shap_values_mean = np.mean(shap_values, axis=2)
        feature_importance = np.abs(shap_values).mean(axis=0)
        feature_importance = np.abs(feature_importance).mean(axis=1)

        X_test_df = pd.DataFrame(X_test2, columns=columns_to_select)
        X_test_df['预测结果'] = test_predictions
        feature_names = data[columns_to_select].columns.tolist()
        print(len(feature_importance))
        print(len(feature_names))
        feature_importance_df = pd.DataFrame({
            'Feature': feature_names,
            'Importance': feature_importance
        }).sort_values(by='Importance', ascending=False).head(20)

        tezheng_df = pd.DataFrame({
            'Feature': feature_names,
            'Importance': feature_importance
        }).sort_values(by='Importance', ascending=False).head(100)

        mapping_df = pd.read_csv("file/content_tezheng.csv")  # 请确保文件路径正确
        # 假设 CSV 第一列名称为 "特征名"，第二列名称为 "实际含义"
        mapping_dict = dict(zip(mapping_df["特征名"], mapping_df["实际含义"]))
        feature_importance_df["特征含义"] = feature_importance_df["Feature"].map(mapping_dict)
        tezheng_df["特征含义"] = tezheng_df["Feature"].map(mapping_dict)
        # 调用大模型生成解释总结文本
        explanation_text = get_llm_explanation(feature_importance_df)
        # explanation_text = '好'
        print("模型解释总结：\n", explanation_text)

        # 输出每一行的特征重要性
        shap_values_df = pd.DataFrame(shap_values_mean, columns=columns_to_select, index=X_test_df[:10].index, )
        # 将测试数据的标识信息（如债券代码、债券名称）提取出来，确保索引与 X_test 一致
        per_instance_info = test_identifiers.copy()
        # 合并标识信息、预测结果以及每条数据的特征重要性
        per_instance_importance = pd.concat([per_instance_info.reset_index(drop=True),
                                             X_test_df['预测结果'].reset_index(drop=True),
                                             shap_values_df.reset_index(drop=True)], axis=1)
        # y_test = y_test[:50]
        #accuracy = accuracy_score(y_test, y_pred)

        y_test_labels = y_test
        #y_pred_labels = label_encoder.inverse_transform(y_pred)
        y_pred_labels = test_predictions
        accuracy = accuracy_score(y_test_labels, y_pred_labels)
        f1 = f1_score(y_test_labels, y_pred_labels, average='macro')
        recall = recall_score(y_test_labels, y_pred_labels, average='macro')
        # 计算多分类任务评价指标（target_names 也可以直接使用 label_encoder.classes_）
        class_report = classification_report(y_test_labels, y_pred_labels,labels=all_labels)
        confusion_mat = confusion_matrix(y_test_labels, y_pred_labels)
        print(len(class_report))

        accuracy = round(accuracy, 5)
        f1 = round(f1, 5)
        recall = round(recall, 5)

        # print("准确率:", accuracy)
        # print("F1 得分:", f1)
        # print("召回率:", recall)
        # print("分类报告:\n", class_report)
        # print("混淆矩阵:\n", confusion_mat)

        metrics = {
            "准确率": accuracy,
            "召回率": recall,
            "F1 得分": f1,
            "分类报告": class_report
        }

    elif model_name == "XGboost":


        if data_type == "6W-财务+非财务":
            model_path = 'model/XGboost/xgb_model.pkl'
        elif data_type == "6W-仅财务":
            model_path = 'model/XGboost/xgb_model-6W-only.pkl'
        elif data_type == "20W-财务+非财务":
            model_path = 'model/XGboost/xgb_model-20W.pkl'

        loaded_model = joblib.load(model_path)
        test_predictions = loaded_model.predict(X_test2)
        test_predictions_2 = test_predictions
        test_predictions = label_encoder.inverse_transform(test_predictions)

        shap_values = get_shap_values_xgb(loaded_model, X_test2)
        X_test2['预测结果'] = test_predictions

        X_test_df = pd.DataFrame(X_test2, columns=columns_to_select)
        X_test_df['预测结果'] = test_predictions
        shap_values = np.mean(shap_values, axis=2)
        feature_importance = np.abs(shap_values).mean(axis=0)

        feature_importance_df = pd.DataFrame({
            'Feature': columns_to_select,
            'Importance': feature_importance
        }).sort_values(by='Importance', ascending=False).head(20)

        tezheng_df = pd.DataFrame({
            'Feature': columns_to_select,
            'Importance': feature_importance
        }).sort_values(by='Importance', ascending=False).head(100)

        mapping_df = pd.read_csv("file/content_tezheng.csv")  # 请确保文件路径正确
        # 假设 CSV 第一列名称为 "特征名"，第二列名称为 "实际含义"
        mapping_dict = dict(zip(mapping_df["特征名"], mapping_df["实际含义"]))
        feature_importance_df["特征含义"] = feature_importance_df["Feature"].map(mapping_dict)
        tezheng_df["特征含义"] = tezheng_df["Feature"].map(mapping_dict)
        # 调用大模型生成解释总结文本
        explanation_text = get_llm_explanation(feature_importance_df)
        #explanation_text = '好'
        print("模型解释总结：\n", explanation_text)

        # 输出每一行的特征重要性
        shap_values_df = pd.DataFrame(shap_values, columns=columns_to_select , index=X_test_df.index,)
        # 将测试数据的标识信息（如债券代码、债券名称）提取出来，确保索引与 X_test 一致
        per_instance_info = test_identifiers.copy()
        # 合并标识信息、预测结果以及每条数据的特征重要性
        per_instance_importance = pd.concat([per_instance_info.reset_index(drop=True),
                                             X_test_df['预测结果'].reset_index(drop=True),
                                             shap_values_df.reset_index(drop=True)], axis=1)

        accuracy = accuracy_score(y_test, test_predictions)
        y_test_labels = label_encoder.inverse_transform(y_test)
        y_pred_labels = label_encoder.inverse_transform(test_predictions_2)
        #y_pred_labels = test_predictions
        accuracy = accuracy_score(y_test_labels, y_pred_labels)
        f1 = f1_score(y_test_labels, y_pred_labels, average='macro')
        recall = recall_score(y_test_labels, y_pred_labels, average='macro')
        # 计算多分类任务评价指标（target_names 也可以直接使用 label_encoder.classes_）
        print("准确率:", accuracy)
        print("F1 得分:", f1)
        print("召回率:", recall)
        class_report = classification_report(y_test_labels, y_pred_labels, labels=all_labels)
        confusion_mat = confusion_matrix(y_test_labels, y_pred_labels)
        print(len(class_report))

        accuracy = round(accuracy, 5)
        f1 = round(f1, 5)
        recall = round(recall, 5)


        print("分类报告:\n", class_report)
       # print("混淆矩阵:\n", confusion_mat)

        metrics = {
            "准确率": accuracy,
            "召回率": recall,
            "F1 得分": f1,
            "分类报告": class_report
        }

    elif model_name == "Bert":
        def df_to_text(df):
            texts = []
            for _, row in df.iterrows():
                text = "When we have "
                # 添加B特征
                for i in range(1, 36):
                    text += f"NF{i}={row[f'NF{i}']:.4f}, "
                # 添加F特征
                for i in range(1, 48):
                    text += f"F{i}={row[f'F{i}']:.4f}, "
                # 添加M特征
                for i in range(1, 86):
                    text += f"M{i}={row[f'M{i}']:.4f}, "
                text = text.rstrip(", ") + " what should be the credit rating?###"
                texts.append(text)
            return texts

        # X_test2=X_test2[:100]
        # 转换测试数据
        #print("测试文本生成样例:", df_to_text(X_test2.head(1)))
        test_texts = df_to_text(X_test2)
        model_path = "model/Bert/saved_model_dir"
        # 加载模型和tokenizer
        tokenizer = BertTokenizer.from_pretrained(model_path)
        model = BertForSequenceClassification.from_pretrained(model_path)

        # 创建预测数据集
        class TestDataset(torch.utils.data.Dataset):
            def __init__(self, texts, tokenizer, max_length=512):
                self.texts = texts
                self.tokenizer = tokenizer
                self.max_length = max_length

            def __len__(self):
                return len(self.texts)

            def __getitem__(self, idx):
                encoding = self.tokenizer(
                    self.texts[idx],
                    max_length=self.max_length,
                    padding="max_length",
                    truncation=True,
                    return_tensors="pt"
                )
                return {k: v.squeeze() for k, v in encoding.items()}

        # 执行预测
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        model.eval()

        test_dataset = TestDataset(test_texts, tokenizer)
        test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=8)

        test_predictions = []
        with torch.no_grad():
            for batch in test_loader:
                inputs = {k: v.to(device) for k, v in batch.items()}
                outputs = model(**inputs)
                test_predictions.extend(torch.argmax(outputs.logits, dim=1).cpu().numpy())

        X_test_df = pd.DataFrame(X_test2, columns=columns_to_select)
        X_test_df['预测结果'] = test_predictions

        test_predictions = label_encoder.inverse_transform(test_predictions)
        y_test= y_test[:100]
        true_labels = label_encoder.inverse_transform(y_test)


        accuracy = accuracy_score(true_labels , test_predictions)
        f1 = f1_score(true_labels , test_predictions, average='macro')
        recall = recall_score(true_labels , test_predictions, average='macro')
        # 计算多分类任务评价指标（target_names 也可以直接使用 label_encoder.classes_）
        print("准确率:", accuracy)
        print("F1 得分:", f1)
        print("召回率:", recall)
        class_report = classification_report(true_labels , test_predictions, target_names=label_encoder.classes_)
        confusion_mat = confusion_matrix(true_labels , test_predictions)
        print(len(class_report))

        accuracy = round(accuracy, 5)
        f1 = round(f1, 5)
        recall = round(recall, 5)
        metrics = {
            "准确率": accuracy,
            "召回率": recall,
            "F1 得分": f1,
            "分类报告": class_report
        }


    biaoge_df = test_identifiers
        # biaoge_df = biaoge_df[:50]
    if model_name == "GNN":
        biaoge_df = pd.DataFrame(test_identifiers, columns=['债券代码', '债券名称','ym', '所属产业板块', '中信一级行业', '债券一级分类', '信用评级'])
        biaoge_df['预测结果'] = y_pred_labels
    else:
        biaoge_df['预测结果'] = test_predictions
    #biaoge_df = biaoge_df.reset_index(drop=True)
    biaoge_df = biaoge_df.sort_values('ym').reset_index(drop=True)

    biaoge_df.head(10)
    return X_test_df, biaoge_df, per_instance_importance,  columns_to_select,metrics,feature_importance_df,explanation_text,tezheng_df


def handle_credit_zhuti(model_name, data, data_type, industry_type):

    label_encoder = LabelEncoder()
    identifier_cols = ['stkcd','ym', '所属产业板块', '中信一级行业', '信用评级']
    identifier_cols = [col for col in identifier_cols if col in data.columns]
    columns_to_select = (
                [f'F{i}' for i in range(1, 48)] +
                [f'M{i}' for i in range(1, 86)] )


    columns_to_select = [col for col in columns_to_select if col in data.columns]

    data['month'] = pd.to_datetime(data['ym'], format='%Y-%m-%d')

    # 设置随机种子，确保结果可重复
    random_seed = 42

    # 打乱数据顺序
    #df = data.sample(frac=1, random_state=random_seed).reset_index(drop=True)
    df = data.sample(frac=1, random_state=random_seed)  # 保留原始索引
    # 数据划分比例
    train_ratio = 0.8  # 训练集比例
    val_ratio = 0.1  # 验证集比例
    test_ratio = 0.1  # 测试集比例

    # 计算样本数
    n = len(df)
    train_end = int(train_ratio * n)
    val_end = train_end + int(val_ratio * n)

    # 按比例划分数据集
    train_data = df.iloc[:train_end]
    val_data = df.iloc[train_end:val_end]
    test_data = df.iloc[val_end:]

    # 检查划分结果
    print(f"训练集样本数: {len(train_data)}")
    print(f"验证集样本数: {len(val_data)}")
    print(f"测试集样本数: {len(test_data)}")

    # 特征与目标变量
    X_train = train_data.iloc[:, 5:].drop(columns=['month'], errors='ignore').apply(pd.to_numeric,
                                                                                    errors='coerce').fillna(0)
    y_train = train_data['信用评级']

    X_val = val_data.iloc[:, 5:].drop(columns=['month'], errors='ignore').apply(pd.to_numeric, errors='coerce').fillna(
        0)
    y_val = val_data['信用评级']

    X_test2 = test_data.iloc[:, 5:].drop(columns=['month'], errors='ignore').apply(pd.to_numeric,
                                                                           errors='coerce').fillna(0)
    X_2=X_test2
    if model_name == 'MLP':
        scaler = StandardScaler()
        X_train, X_val, X_test2 = scaler.fit_transform(X_train), scaler.transform(X_val), scaler.transform(X_test2)

    y_test = test_data['信用评级']

    all_labels = ['AAA', 'AA+','AA','A','BBB', 'BB', 'B',  'CCC','CC', 'C']
    label_encoder.fit(all_labels)

    #test_identifiers = data.loc[X_2.index, identifier_cols].copy()
    #test_identifiers = data.loc[X_test2.index, identifier_cols].copy()
    test_identifiers = test_data[identifier_cols].copy()
    
    if model_name ==  "XGboost":
        loaded_model = joblib.load('model/主体/2 XGBoost分类_1000_model.pkl')
        X_test2 = X_test2

        y_pred = loaded_model.predict(X_test2)

        shap_values = get_shap_values_xgb(loaded_model, X_test2)
        shap_values_mean = np.mean(shap_values, axis=2)
        feature_importance_2 = np.abs(shap_values).mean(axis=0)
        feature_importance = np.abs(feature_importance_2).mean(axis=1)

        X_test_df = pd.DataFrame(X_test2, columns=columns_to_select)
        X_test_df['预测结果'] = y_pred
        feature_names = data[columns_to_select].columns.tolist()
        print(len(feature_importance))
        print(len(feature_names))
        feature_importance_df = pd.DataFrame({
            'Feature': feature_names,
            'Importance': feature_importance
        }).sort_values(by='Importance', ascending=False).head(20)

        tezheng_df = pd.DataFrame({
            'Feature': feature_names,
            'Importance': feature_importance
        }).sort_values(by='Importance', ascending=False).head(100)

        mapping_df = pd.read_csv("file/content_tezheng.csv")  # 请确保文件路径正确
        # 假设 CSV 第一列名称为 "特征名"，第二列名称为 "实际含义"
        mapping_dict = dict(zip(mapping_df["特征名"], mapping_df["实际含义"]))
        feature_importance_df["特征含义"] = feature_importance_df["Feature"].map(mapping_dict)
        tezheng_df["特征含义"] = tezheng_df["Feature"].map(mapping_dict)
        # 调用大模型生成解释总结文本
        explanation_text = get_llm_explanation(feature_importance_df)
        # explanation_text = '好'
        print("模型解释总结：\n", explanation_text)

        # 输出每一行的特征重要性
        shap_values_df = pd.DataFrame(shap_values_mean , columns=columns_to_select , index=X_test_df.index,)
        # 将测试数据的标识信息（如债券代码、债券名称）提取出来，确保索引与 X_test 一致
        per_instance_info = test_identifiers.copy()
        # 合并标识信息、预测结果以及每条数据的特征重要性
        per_instance_importance = pd.concat([per_instance_info.reset_index(drop=True),
                                             X_test_df['预测结果'].reset_index(drop=True),
                                             shap_values_df.reset_index(drop=True)], axis=1)

        #accuracy = accuracy_score(y_test, y_pred)
        y_test_labels = y_test
        y_pred_labels = label_encoder.inverse_transform(y_pred)


        # y_pred_labels = y_pred


        try:
            accuracy = accuracy_score(y_test_labels, y_pred_labels)
            f1 = f1_score(y_test_labels, y_pred_labels, average='macro')
            recall = recall_score(y_test_labels, y_pred_labels, average='macro')

        # 计算多分类任务评价指标（target_names 可直接使用 label_encoder.classes_）
            class_report = classification_report(y_test_labels, y_pred_labels,labels=all_labels)
            confusion_mat = confusion_matrix(y_test_labels, y_pred_labels)
            accuracy = round(accuracy, 5)
            f1 = round(f1, 5)
            recall = round(recall, 5)
        except:
            accuracy = ''
            f1 = ''
            recall = ''

            # 计算多分类任务评价指标（target_names 可直接使用 label_encoder.classes_）
            class_report = ''
            confusion_mat = ''



        # print("准确率:", accuracy)
        # print("F1 得分:", f1)
        # print("召回率:", recall)
        # print("分类报告:\n", class_report)
       # print("混淆矩阵:\n", confusion_mat)

        metrics = {
            "准确率": accuracy,
            "召回率": recall,
            "F1 得分": f1,
            "分类报告": class_report
        }

    elif model_name == "MLP":
        model_path='model/主体/3_MLP分类_1000_model.h5'
        loaded_model = models.load_model(model_path)
        X_test2 = X_test2
        X_test2 = X_test2.values if isinstance(X_test2, pd.DataFrame) else X_test2
        y_pred = loaded_model.predict(X_test2)
        y_pred = np.argmax(y_pred, axis=1)
        shap_values = get_shap_values_MLP_zhuti(loaded_model, X_train, X_test2)
        shap_values_mean = np.mean(shap_values, axis=2)
        feature_importance_2 = np.abs(shap_values).mean(axis=0)
        feature_importance = np.abs(feature_importance_2).mean(axis=1)

        X_test_df = pd.DataFrame(X_test2, columns=columns_to_select)

        X_test_df['预测结果'] = y_pred
        feature_names = data[columns_to_select].columns.tolist()
        print(len(feature_importance))
        print(len(feature_names))
        feature_importance_df = pd.DataFrame({
            'Feature': feature_names,
            'Importance': feature_importance
        }).sort_values(by='Importance', ascending=False).head(20)

        tezheng_df = pd.DataFrame({
            'Feature': feature_names,
            'Importance': feature_importance
        }).sort_values(by='Importance', ascending=False).head(100)


        mapping_df = pd.read_csv("file/content_tezheng.csv")  # 请确保文件路径正确
        # 假设 CSV 第一列名称为 "特征名"，第二列名称为 "实际含义"
        mapping_dict = dict(zip(mapping_df["特征名"], mapping_df["实际含义"]))
        feature_importance_df["特征含义"] = feature_importance_df["Feature"].map(mapping_dict)
        tezheng_df["特征含义"] = tezheng_df["Feature"].map(mapping_dict)
        # 调用大模型生成解释总结文本
        explanation_text = get_llm_explanation(feature_importance_df)
        # explanation_text = '好'
        print("模型解释总结：\n", explanation_text)
        # 输出每一行的特征重要性
        shap_values_df = pd.DataFrame(shap_values_mean, columns=columns_to_select, index=X_test_df[:100].index, )
        # 将测试数据的标识信息（如债券代码、债券名称）提取出来，确保索引与 X_test 一致
        per_instance_info = test_identifiers.copy()
        # 合并标识信息、预测结果以及每条数据的特征重要性
        per_instance_importance = pd.concat([per_instance_info.reset_index(drop=True),
                                             X_test_df['预测结果'].reset_index(drop=True),
                                             shap_values_df.reset_index(drop=True)], axis=1)

        #accuracy = accuracy_score(y_test, y_pred)
        y_test_labels = y_test
        y_pred_labels = label_encoder.inverse_transform(y_pred)

        # y_pred_labels = y_pred


        # 计算过滤后的指标
        try:
            accuracy = accuracy_score(y_test_labels, y_pred_labels)
            f1 = f1_score(y_test_labels, y_pred_labels, average='macro')
            recall = recall_score(y_test_labels, y_pred_labels, average='macro')

        # 计算多分类任务评价指标（target_names 可直接使用 label_encoder.classes_）
            class_report = classification_report(y_test_labels, y_pred_labels,labels=all_labels)
            confusion_mat = confusion_matrix(y_test_labels, y_pred_labels)
            accuracy = round(accuracy, 5)
            f1 = round(f1, 5)
            recall = round(recall, 5)
        except:
            accuracy = ''
            f1 = ''
            recall = ''

            # 计算多分类任务评价指标（target_names 可直接使用 label_encoder.classes_）
            class_report = ''
            confusion_mat = ''

        # print("准确率:", accuracy)
        # print("F1 得分:", f1)
        # print("召回率:", recall)
        # print("分类报告:\n", class_report)
        # print("混淆矩阵:\n", confusion_mat)

        metrics = {
            "准确率": accuracy,
            "召回率": recall,
            "F1 得分": f1,
            "分类报告": class_report
        }

    elif model_name == "RF":
        loaded_model = joblib.load('model/主体/1 RF分类_1000_model.pkl')
        #X_test2 = X_test2[:50]

        y_pred = loaded_model.predict(X_test2)

        shap_values = get_shap_values_xgb_pingjirf(loaded_model,X_test2)
        shap_values_mean = np.mean(shap_values, axis=2)
        feature_importance_2 = np.abs(shap_values).mean(axis=0)
        feature_importance = np.abs(feature_importance_2).mean(axis=1)

        X_test_df = pd.DataFrame(X_test2, columns=columns_to_select)
        X_test_df['预测结果'] = y_pred
        feature_names = data[columns_to_select].columns.tolist()
        print(len(feature_importance))
        print(len(feature_names))
        feature_importance_df = pd.DataFrame({
            'Feature': feature_names,
            'Importance': feature_importance
        }).sort_values(by='Importance', ascending=False).head(20)

        tezheng_df = pd.DataFrame({
            'Feature': feature_names,
            'Importance': feature_importance
        }).sort_values(by='Importance', ascending=False).head(100)

        mapping_df = pd.read_csv("file/content_tezheng.csv")  # 请确保文件路径正确
        # 假设 CSV 第一列名称为 "特征名"，第二列名称为 "实际含义"
        mapping_dict = dict(zip(mapping_df["特征名"], mapping_df["实际含义"]))
        feature_importance_df["特征含义"] = feature_importance_df["Feature"].map(mapping_dict)
        tezheng_df["特征含义"] = tezheng_df["Feature"].map(mapping_dict)
        # 调用大模型生成解释总结文本
        explanation_text = get_llm_explanation(feature_importance_df)
        # explanation_text = '好'
        print("模型解释总结：\n", explanation_text)

        # 输出每一行的特征重要性
        shap_values_df = pd.DataFrame(shap_values_mean, columns=columns_to_select, index=X_test_df[:10].index, )
        # 将测试数据的标识信息（如债券代码、债券名称）提取出来，确保索引与 X_test 一致
        per_instance_info = test_identifiers.copy()
        # 合并标识信息、预测结果以及每条数据的特征重要性
        per_instance_importance = pd.concat([per_instance_info.reset_index(drop=True),
                                             X_test_df['预测结果'].reset_index(drop=True),
                                             shap_values_df.reset_index(drop=True)], axis=1)
        y_test = y_test
        #accuracy = accuracy_score(y_test, y_pred)
        y_test_labels = y_test
        y_pred_labels = y_pred

        y_pred_labels = y_pred


        try:
            accuracy = accuracy_score(y_test_labels, y_pred_labels)
            f1 = f1_score(y_test_labels, y_pred_labels, average='macro')
            recall = recall_score(y_test_labels, y_pred_labels, average='macro')

        # 计算多分类任务评价指标（target_names 可直接使用 label_encoder.classes_）
            class_report = classification_report(y_test_labels, y_pred_labels)
            confusion_mat = confusion_matrix(y_test_labels, y_pred_labels)
            accuracy = round(accuracy, 5)
            f1 = round(f1, 5)
            recall = round(recall, 5)
        except:
            accuracy = ''
            f1 = ''
            recall = ''

            # 计算多分类任务评价指标（target_names 可直接使用 label_encoder.classes_）
            class_report = ''
            confusion_mat = ''
        print(len(class_report))
        # y_pred_labels = label_encoder.inverse_transform(y_pred)


        # print("准确率:", accuracy)
        # print("F1 得分:", f1)
        # print("召回率:", recall)
        # print("分类报告:\n", class_report)
        # print("混淆矩阵:\n", confusion_mat)

        metrics = {
            "准确率": accuracy,
            "召回率": recall,
            "F1 得分": f1,
            "分类报告": class_report
        }


    biaoge_df = test_identifiers
    #biaoge_df = biaoge_df[:50]
    biaoge_df['预测结果'] = y_pred_labels
    #biaoge_df = biaoge_df.reset_index(drop=True)
    biaoge_df = biaoge_df.sort_values('ym').reset_index(drop=True)

    return X_test_df, biaoge_df, per_instance_importance,  columns_to_select,metrics,feature_importance_df,explanation_text,tezheng_df

def get_shap_values_MLP(model, X_train, X_test):
    background = X_train[:500]  # 使用前500个样本作为背景
    explainer = shap.DeepExplainer(model, background)
    shap_values = explainer.shap_values(X_test[:100])
    return shap_values

def get_shap_values_MLP_zhuti(model, X_train, X_test):
    background = X_train[:500]  # 使用前500个样本作为背景
    explainer = shap.DeepExplainer(model, background)
    shap_values = explainer.shap_values(X_test[:100])
    return shap_values

def get_shap_values_MLP_2(model, X_train, X_test):
    # 使用KernelExplainer替代DeepExplainer
    # 先对背景数据进行聚类采样以加速计算（建议样本量50-100）
    background = shap.sample(X_train, 100)

    # 创建解释器（使用预测概率函数）
    explainer = shap.KernelExplainer(model.predict_proba, background)

    # 计算SHAP值（注意nsamples参数控制计算速度）
    shap_values = explainer.shap_values(X_test, nsamples=50)
    return shap_values
def get_shap_values_lasso(model, X_test):
    explainer = shap.LinearExplainer(model, X_test)
    shap_values = explainer.shap_values(X_test)
    return shap_values

def generate_plot(plot_data, output_path):
    """
    根据数据生成图并保存为 PNG 文件。

    参数:
    plot_data: 用于生成图的数据。
    output_path (str): 输出图片的路径。
    """
    font_path = "font/SimHei.ttf"
    my_font = fm.FontProperties(fname=font_path)
    plt.rcParams["axes.unicode_minus"] = False  # 正常显示负号

    mapping_df = pd.read_csv("./file/content_tezheng.csv")  # 请确保此文件路径正确
    mapping_dict = dict(zip(mapping_df["特征名"], mapping_df["实际含义"]))

    original_features = plot_data['Feature'].copy()
    plot_data['Feature'] = plot_data['Feature'].map(mapping_dict)
    plot_data['Feature'] = plot_data['Feature'].fillna(original_features)
    plot_data['Feature'] = plot_data['Feature'].astype(str)



    plt.figure(figsize=(10, 8))
    plt.barh(plot_data['Feature'][::-1], plot_data['Importance'][::-1])
    plt.yticks(fontproperties=my_font)

    # 隐藏 x 轴
    plt.xticks([])
    plt.xlabel('')
    plt.gca().axes.get_xaxis().set_visible(False)

    plt.title('前20个特征的重要性', fontproperties=my_font)

    # 自动调整子图参数，使图形适应屏幕
    plt.tight_layout()

    plt.savefig(output_path)
    plt.show()




################# 新加入RF的特征重要性 #################
def get_shap_values_RF(model, X_train, X_test):
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)
    # 如果是多分类，shap_values通常是一个列表，每个元素为一个类别的SHAP值，形状为 (n_samples, n_features)
    if isinstance(shap_values, list):
        # 转换为 numpy 数组，形状：(n_classes, n_samples, n_features)
        shap_values = np.array(shap_values)
        # 对所有类别、样本取绝对值平均，得到每个特征的重要性
        shap_aggregated = np.abs(shap_values).mean(axis=(0, 1))
    else:
        # 二分类或回归时直接计算
        shap_aggregated = np.abs(shap_values).mean(axis=0)
    return shap_values, shap_aggregated


################# ################# #################


def calculate_r_os2(y_true, y_pred, benchmark):
    numerator = np.sum((y_true - y_pred) ** 2)
    denominator = np.sum((y_true - benchmark) ** 2)
    return 1 - (numerator / denominator)


def get_shap_values_ada(model, X_test):
    explainer = shap.TreeExplainer(model.estimators_[0])  # 使用第一个基学习器
    shap_values = explainer.shap_values(X_test)
    return shap_values


def get_shap_values_cnn(model, X_train, X_test):
    explainer = shap.DeepExplainer(model, X_train[:100])  # 使用前500个样本作为背景数据
    shap_values = explainer.shap_values(X_test[:10])
    return shap_values




def get_shap_values_xgb(model, X_test):
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)
    return shap_values

def get_shap_values_xgb_pingjirf(model, X_test):
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test[:10])
    return shap_values




def Man_handle_row_click(row_index, origin_data, feature_columns, mapping_dict):
    original_index = biaoge_df.loc[row_index, '原始索引']
    instance_data = origin_data.loc[original_index, feature_columns]


def handle_row_click(row_index, per_instance_importance, feature_columns, mapping_dict):
    """
    处理用户点击表格行的交互操作，生成该行实例的特征重要性解释

    参数:
    row_index (int): 用户点击的行号（基于0的索引）
    per_instance_importance (pd.DataFrame): 每个实例的特征重要性数据（包含特征列）
    feature_columns (list): 特征列名称列表
    mapping_dict (dict): 特征名称到实际含义的映射字典

    返回:
    str: 大模型生成的解释文本
    """
    # 提取指定行的特征数据（排除标识列和预测结果列）
    row_data = per_instance_importance.iloc[row_index][feature_columns]

    # 创建特征重要性DataFrame（按绝对值排序）
    feature_importance_df = pd.DataFrame({
        'Feature': feature_columns,
        'Importance': row_data.values
    }).sort_values(by='Importance', key=lambda x: abs(x), ascending=False)


    # 添加特征含义映射
    feature_importance_df['特征含义'] = feature_importance_df['Feature'].map(mapping_dict)

    # 生成定制化提示词
    prompt = (
        "请根据以下特征重要性数据，分析该债券样本的预测结果：\n"
        "结合债券市场知识综合分析这些特征的影响\n"
        "数据如下：\n\n"
        f"{feature_importance_df.to_csv(index=False)}\n\n"
        "请用专业但易懂的中文成段说明，尽可能少的分条，但要有结构化一点。"
    )

    # 调用大模型接口
    try:
        response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "deepseek-chat"),
            messages=[
                {"role": "system", "content": "您是债券市场分析师，擅长用SHAP值解释模型预测，使用markdown格式输出内容，使用加粗来强调，加粗的**与文字之间要有空格"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            stream=False
        )
        model_text = response.choices[0].message.content
    except Exception as e:
        print(f"DeepSeek API 调用失败: {e}")
        model_text = "网络错误，请修复网络后重试"

    feature_importance_df = pd.DataFrame({
        'Feature': feature_columns,
        'Importance': row_data.values
    }).sort_values(by='Importance', ascending=False).head(20)

    return feature_importance_df, model_text


def get_model_name(input_desc, mapping):
    matches = []
    for model, desc in mapping:
        if input_desc in desc:
            matches.append(model)

    if not matches:
        return "未找到匹配的模型"
    # 如果只有一个匹配结果，则直接返回该字符串
    if len(matches) == 1:
        return matches[0]
    # 如果有多个匹配，可以用逗号分隔后返回字符串
    return ", ".join(matches)




# 示例调用
if __name__ == "__main__":
    start_time = time.time()
    task_type = '债项信用评级'  # 或 '信用评级'
    model_name = '基于随机森林的债项评估模型'  # 还有其他的一些

    simple_mapping = [
        ("XGboost", "基于梯度提升的信用预测模型"),
        ("Adaboost", "基于自适应增强的回归模型"),
        ("RF", "基于随机森林的信用评估模型"),
        ("GBDT", "基于梯度迭代的债务分析模型"),
        ("lasso", "基于稀疏回归的财务筛选模型"),
        ("CNN", "基于卷积神经网络的债项图谱模型"),
        ("MLP", "基于深度学习的跨周期评级模型"),
        ("GNN", "基于图神经网络的债务拓扑模型"),
        ("RF", "基于随机森林的债项评估模型"),
        ("XGboost", "基于梯度提升的债务结构模型"),
        ("Bert","基于大模型的智能评级模型"),
        ("RF", "基于随机森林的企业信用模型"),
        ("XGboost", "基于梯度提升的主体诊断模型"),
        ("MLP", "基于神经网络的非线性评级模型")
    ]

    model_name = get_model_name(model_name, simple_mapping)
    print(model_name)
    data_type = "20W-财务+非财务"  # 还可以选择 “仅财务”
    industry_type = "房地产"  #选择行业
    # file_path = r"C:\Users\zhoulab\1_beishida\25-0304 中期递归\zhaixiang6w.csv"
    if task_type == '信用利差预测':
        file_path = r"file/licha.csv"
    elif task_type == '债项信用评级':
        if data_type != "20W-财务+非财务":
            file_path = r"file/pingji.csv"
        else:
            file_path = r"file/pingji-20W.csv"
    elif task_type == "主体信用评级":
        file_path = r"file/主体信用评级1000_财务_模型训练.csv"

    if model_name == "Bert":
        file_path = 'file/债项信用评级_10000_财务+非财务_V2.csv'

    if task_type == '债项信用评级' and model_name == "RF":
        if industry_type != '全产业':
            if data_type != "20W-财务+非财务":
                file_path = f'file/分产业6w/债项信用评级_10000+非财务数据V3_{industry_type}.csv'
            else:
                file_path = f'file/分产业20W/债项信用评级10000_财务_20w_{industry_type}.csv'

    print(file_path)
    #file_path = r"file/pingji.csv"
    input_df = pd.read_csv(file_path)

    result_df,  biaoge, feature_import, columns ,risk ,all_plot_data, model_text ,tezheng_biao= main(task_type, model_name, input_df, data_type,industry_type)
    print("风险指标：",risk)

    print("feature_import type:", type(feature_import))

    # 点击的结果
    mapping_df = pd.read_csv("./file/content_tezheng.csv")  # 请确保此文件路径正确
    # 假设 CSV 第一列名称为 "代称"，第二列名称为 "真实含义"
    mapping_dict = dict(zip(mapping_df["特征名"], mapping_df["实际含义"]))
    Alex = True

    # if feature_import.empty or feature_import=="":
    #     # 添加特征含义映射
    #     Man_handle_row_click(
    #         row_index=4,
    #         data=input_df,
    #         feature_columns=columns,
    #         mapping_dict=mapping_dict)
    #
    # else:
    #     plot_data,abond = handle_row_click(
    #         row_index=4,
    #         per_instance_importance=feature_import,
    #         feature_columns=columns,
    #         mapping_dict=mapping_dict)


    #print(abond)
    all_plot_data.to_csv("22.csv",index=False)
    tezheng_biao.to_csv("tezhengbiao.csv",index=False)
    result_df.to_csv("result.csv", index=False)
    biaoge.to_csv("biaoge.csv", index=False)
    #feature_import.to_csv("feature.csv", index=False)
    # 生成并保存图
    #generate_plot(plot_data, "output_plot.png")
    generate_plot(all_plot_data, "all_output_plot.png")
    end_time = time.time()

    print("代码运行时间: {:.2f} 秒".format(end_time - start_time))
