import os
import pandas as pd
import matplotlib
import json

matplotlib.use("Agg")  # 设置非交互式后端在导入pyplot之前
import matplotlib.pyplot as plt

def generate_row_visualization(hash_value, index, result_dir):
    """为特定行生成可视化图像和文本"""
    # 创建行子目录
    row_dir = os.path.join(result_dir, "row")
    os.makedirs(row_dir, exist_ok=True)
    
    # 检查文件是否已存在
    if os.path.exists(f"{row_dir}/{index}.txt") and os.path.exists(f"{row_dir}/{index}.png"):
        return True
    
    # 加载所需数据
    feature_import_path = os.path.join(result_dir, "feature_importance.csv")
    feature_columns_path = os.path.join(result_dir, "feature_columns.json")
    
    if not os.path.exists(feature_import_path) or not os.path.exists(feature_columns_path):
        return False
    
    # 读取特征重要性和数据集文件
    feature_import = pd.read_csv(feature_import_path)
    
    # 获取特征列（数据集中除目标外的所有列）
    feature_columns = json.load(open(feature_columns_path, "r", encoding="utf-8"))
    
    # 确保映射文件路径存在
    content_tezheng_path = "./file/content_tezheng.csv"
    if not os.path.exists(content_tezheng_path):
        # 如果文件不存在，创建一个空的映射字典
        mapping_dict = {}
    else:
        # 导入映射数据
        mapping_df = pd.read_csv(content_tezheng_path)
        mapping_dict = dict(zip(mapping_df["特征名"], mapping_df["实际含义"]))
    
    # 导入handle_row_click函数
    from main import handle_row_click, generate_plot
    
    # 调用handle_row_click函数处理数据
    plot_data, abond = handle_row_click(
        row_index=index,
        per_instance_importance=feature_import,
        feature_columns=feature_columns,
        mapping_dict=mapping_dict,
    )
    
    # 生成并保存图像
    plot_path = f"{row_dir}/{index}.png"
    generate_plot(plot_data, plot_path)
    
    # 保存文本
    with open(f"{row_dir}/{index}.txt", "w", encoding="utf-8") as model_file:
        model_file.write(abond)
    
    return True 