import os
import json
import pandas as pd
import numpy as np
import datetime

def ensure_directory_exists(directory_path):
    """确保目录存在，如果不存在则创建"""
    os.makedirs(directory_path, exist_ok=True)

def save_dataframe_to_csv(df, file_path):
    """保存DataFrame到CSV文件"""
    df.to_csv(file_path, index=False)

def save_text_to_file(text, file_path):
    """保存文本到文件"""
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(text)

def save_json_to_file(data, file_path):
    """保存JSON数据到文件"""
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def save_config_file(result_dir, task_type, model_name, data_type, industry_type, filename):
    """创建配置文件保存参数和处理时间戳"""
    config_data = {
        "task_type": task_type,
        "model_name": model_name,
        "data_type": data_type,
        "industry_type": industry_type,
        "processing_time": datetime.datetime.now().isoformat(),
        "original_filename": filename,
    }
    
    save_json_to_file(config_data, f"{result_dir}/config.json")

def prepare_risk_data_for_serialization(risk):
    """将风险数据准备为可序列化格式"""
    serializable_risk = {}
    for key, value in risk.items():
        if isinstance(value, pd.DataFrame):
            serializable_risk[key] = value.to_dict(orient="records")
        elif isinstance(value, np.ndarray):
            serializable_risk[key] = value.tolist()
        else:
            serializable_risk[key] = value
    return serializable_risk 