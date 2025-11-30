from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import json
import re
import os

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)  # 允许跨域请求

# 加载JSON数据
with open('word_freq_data.json', 'r', encoding='utf-8') as f:
    word_freq_data = json.load(f)

with open('sentiment_data.json', 'r', encoding='utf-8') as f:
    sentiment_data = json.load(f)

# 加载原始弹幕数据
with open('bilibili_danmu.txt', 'r', encoding='utf-8') as f:
    bilibili_danmu = f.readlines()

@app.route('/api/word-frequency', methods=['GET'])
def get_word_frequency():
    """
    获取高频词数据接口
    """
    # 返回前100个高频词，用于词云图展示
    top_words = word_freq_data[:100]
    return jsonify({
        'status': 'success',
        'data': top_words
    })

@app.route('/api/sentiment-data', methods=['GET'])
def get_sentiment_data():
    """
    获取情感分析数据接口
    """
    return jsonify({
        'status': 'success',
        'data': sentiment_data
    })

@app.route('/api/search', methods=['GET'])
def search_keyword():
    """
    关键词搜索接口
    """
    keyword = request.args.get('keyword', '')
    limit = request.args.get('limit', 50, type=int)
    
    if not keyword:
        return jsonify({
            'status': 'error',
            'message': '请输入关键词'
        })
    
    # 搜索包含关键词的弹幕
    results = []
    for i, line in enumerate(bilibili_danmu, 1):
        # 解析弹幕内容
        try:
            dot_pos = line.find('.')
            if dot_pos != -1:
                content = line[dot_pos + 1:].strip()
            else:
                content = line.strip()
            
            # 使用正则表达式搜索关键词
            if re.search(re.escape(keyword), content):
                results.append({
                    'index': i,
                    'content': content
                })
                
                # 限制返回数量
                if len(results) >= limit:
                    break
        except Exception as e:
            print(f"解析弹幕时出错：{e}")
    
    return jsonify({
        'status': 'success',
        'keyword': keyword,
        'total': len(results),
        'data': results
    })

@app.route('/')
def index():
    """提供index.html首页"""
    return send_from_directory('.', 'index.html')

@app.route('/index.html')
def index_html():
    """提供index.html文件"""
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    # 安装必要的依赖
    try:
        import flask_cors
    except ImportError:
        print("正在安装flask-cors...")
        import subprocess
        subprocess.call(['pip', 'install', 'flask-cors'])
        import flask_cors
    
    try:
        import flask
    except ImportError:
        print("正在安装flask...")
        import subprocess
        subprocess.call(['pip', 'install', 'flask'])
        import flask
    
    print("启动Flask服务器...")
    print("访问地址: http://127.0.0.1:5000")
    print("可用接口:")
    print("  GET /api/word-frequency - 获取高频词数据")
    print("  GET /api/sentiment-data - 获取情感分析数据")
    print("  GET /api/search?keyword=关键词 - 搜索关键词")
    
    # 启动服务器
    app.run(debug=True, host='0.0.0.0', port=5000)