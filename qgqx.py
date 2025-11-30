import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from snownlp import SnowNLP  # 需安装：pip install snownlp

# 设置中文字体，防止乱码
plt.rcParams["font.sans-serif"] = ["SimHei"]  # 用黑体显示中文
plt.rcParams["axes.unicode_minus"] = False  # 正常显示负号

# 1. 读取弹幕文件
def read_danmu_file(file_path):
    """
    读取B站弹幕文件
    格式：每行一条弹幕，前面有数字序号
    """
    danmu_list = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            # 解析弹幕内容，去掉前面的序号和句点
            try:
                # 查找第一个句点的位置
                dot_pos = line.find('.')
                if dot_pos != -1:
                    content = line[dot_pos + 1:].strip()
                else:
                    content = line.strip()
                
                # 模拟时间戳（由于原数据没有时间信息，这里使用行号模拟）
                # 假设视频时长为1000秒，均匀分布弹幕
                time_stamp = (i - 1) % 1000
                
                danmu_list.append({
                    'content': content,
                    'time': time_stamp
                })
            except Exception as e:
                print(f"解析第{i}行弹幕失败：{e}")
    
    return pd.DataFrame(danmu_list)

# 2. 情感打分（SnowNLP返回0-1，越接近1越正面）
def get_sentiment_score(text):
    try:
        return SnowNLP(text).sentiments
    except:
        return 0.5  # 异常文本视为中性

# 3. 情感分类（正面：>0.6，中性：0.4-0.6，负面：<0.4）
def classify_sentiment(score):
    if score > 0.6:
        return "正面"
    elif score < 0.4:
        return "负面"
    else:
        return "中性"

# 4. 执行情感分析
def analyze_danmu_sentiment(file_path):
    """
    对B站弹幕文件进行情感分析
    """
    print(f"正在读取弹幕文件：{file_path}")
    df = read_danmu_file(file_path)
    print(f"成功读取{len(df)}条弹幕")
    
    # 进行情感分析
    print("正在进行情感分析...")
    df["情感得分"] = df["content"].apply(get_sentiment_score)
    df["情感类型"] = df["情感得分"].apply(classify_sentiment)
    
    # 整体情感分布
    print("\n整体情感分布：")
    sentiment_dist = df["情感类型"].value_counts(normalize=True).round(3) * 100
    print(sentiment_dist)
    
    # 统计平均情感得分
    avg_score = df["情感得分"].mean()
    print(f"\n平均情感得分：{avg_score:.3f}")
    
    # 生成情感柱状图
    plt.figure(figsize=(10, 6))
    sentiment_counts = df["情感类型"].value_counts()
    colors = ['red', 'gray', 'green']  # 负面-红色，中性-灰色，正面-绿色
    bars = plt.bar(sentiment_counts.index, sentiment_counts.values, color=colors)
    
    # 添加数值标签
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 5,
                 f'{int(height)}', ha='center', va='bottom')
    
    plt.title("B站弹幕情感分布")
    plt.xlabel("情感类型")
    plt.ylabel("弹幕数量")
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    
    # 绘制情感时序图（由于原数据没有真实时间戳，仅供参考）
    plt.figure(figsize=(12, 4))
    df["time_bin"] = pd.cut(df["time"], bins=np.arange(0, 1001, 50), right=False)
    sentiment_time = df.groupby("time_bin")["情感类型"].apply(
        lambda x: (x == "正面").sum() / len(x) * 100 if len(x) > 0 else 0
    ).reset_index(name="正面情感占比")
    
    plt.plot(sentiment_time["time_bin"].astype(str), sentiment_time["正面情感占比"], marker='s', color='green', linewidth=2)
    plt.xlabel("模拟视频时间区间（秒）")
    plt.ylabel("正面情感占比（%）")
    plt.title("B站视频弹幕情感时序变化")
    plt.xticks(rotation=45)
    plt.grid(alpha=0.3)
    plt.ylim(0, 100)
    plt.tight_layout()
    
    # 显示图表
    plt.show()
    
    # 返回分析结果，便于进一步使用
    return df

# 导出情感分析数据为JSON格式
def export_sentiment_data(df, output_file="sentiment_data.json"):
    """
    将情感分析结果导出为JSON格式
    """
    # 准备要导出的数据
    export_data = {
        "total_danmu": len(df),
        "sentiment_distribution": df["情感类型"].value_counts(normalize=True).round(3).to_dict(),
        "avg_sentiment_score": float(df["情感得分"].mean().round(3))
    }
    
    # 导出部分代表性弹幕数据（前100条），确保可序列化
    sample_danmu = []
    for _, row in df.head(100).iterrows():
        danmu_dict = {
            "content": row["content"],
            "sentiment_score": float(row["情感得分"]),
            "sentiment_type": row["情感类型"]
        }
        # 添加时间信息
        if "time" in row.index:
            danmu_dict["time"] = float(row["time"])
        sample_danmu.append(danmu_dict)
    
    export_data["sample_danmu"] = sample_danmu
    
    # 保存为JSON文件
    import json
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    print(f"情感分析数据已导出到：{output_file}")
    return export_data

# 导出高频词数据为JSON格式
def export_word_freq_data(file_path="saichaozi_top300_高频词.txt", output_file="word_freq_data.json"):
    """
    将高频词数据导出为JSON格式
    """
    word_freq_list = []
    with open(file_path, 'r', encoding='utf-8') as f:
        # 跳过标题信息
        for i, line in enumerate(f):
            # 跳过前两行注释和分隔线
            if i < 2:
                continue
            
            # 跳过列名行
            if '词语' in line and '词频' in line:
                continue
                
            if line.strip():
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    try:
                        word_freq_list.append({
                            "word": parts[0],
                            "freq": int(parts[1]),
                            "pos": parts[2] if len(parts) > 2 else "未知"
                        })
                    except ValueError:
                        # 如果无法转换为整数，跳过此行
                        continue
    
    # 保存为JSON文件
    import json
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(word_freq_list, f, ensure_ascii=False, indent=2)
    
    print(f"高频词数据已导出到：{output_file}")
    return word_freq_list

# 主函数
def main():
    # 默认分析当前目录下的bilibili_danmu.txt文件
    file_path = "bilibili_danmu.txt"
    df = analyze_danmu_sentiment(file_path)
    
    # 导出数据
    export_sentiment_data(df)
    export_word_freq_data()

# 如果直接运行此脚本，则执行主函数
if __name__ == "__main__":
    main()