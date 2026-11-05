import hashlib

def calculate_hash(task_type, model_name, data_type, industry_type, file_content):
    """计算参数组合的SHA256哈希值"""
    # 将所有参数组合成单个字节列表
    combined = (
        task_type.encode()
        + model_name.encode()
        + data_type.encode()
        + industry_type.encode()
        + file_content
    )

    # 计算SHA256哈希
    hash_object = hashlib.sha256(combined)
    hash_value = hash_object.hexdigest()

    return hash_value 