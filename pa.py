import requests
from lxml import etree
import json
import time
from typing import List, Dict

# 目标视频 BV 号（从 URL 中提取）
BV_ID = "BV1w7UsBZErd"
# 保存文件路径
DANMU_SAVE_PATH = "bilibili_danmu.txt"
COMMENT_SAVE_PATH = "bilibili_comment.txt"

# 请求头（模拟浏览器，避免 403 禁止访问）
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
    "Accept-Language": "zh-CN,zh;q=0.9"
}

def get_video_cid(bv_id: str) -> str:
    """
    通过 BV 号获取视频的 cid（弹幕/评论接口必需参数）
    :param bv_id: 视频 BV 号
    :return: 视频 cid
    """
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bv_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()  # 抛出 HTTP 错误
        data = response.json()
        if data.get("code") == 0:
            cid = str(data["data"]["cid"])
            print(f"成功获取视频 cid: {cid}")
            return cid
        else:
            print(f"获取 cid 失败：{data.get('message', '未知错误')}")
            return ""
    except Exception as e:
        print(f"获取 cid 异常：{str(e)}")
        return ""

def crawl_danmu(cid: str) -> List[str]:
    """
    爬取视频弹幕（XML 接口）
    :param cid: 视频 cid
    :return: 弹幕列表
    """
    danmu_url = f"https://comment.bilibili.com/{cid}.xml"
    danmu_list = []
    try:
        response = requests.get(danmu_url, headers=HEADERS, timeout=10)
        response.encoding = "utf-8"  # 避免中文乱码
        response.raise_for_status()
        
        # 解析 XML 格式的弹幕
        xml_tree = etree.fromstring(response.content)
        # 提取所有 <d> 标签的文本内容（弹幕内容）
        for d_tag in xml_tree.xpath("//d"):
            danmu_content = d_tag.text.strip()
            if danmu_content:  # 过滤空弹幕
                danmu_list.append(danmu_content)
        
        print(f"成功爬取弹幕 {len(danmu_list)} 条")
    except Exception as e:
        print(f"爬取弹幕异常：{str(e)}")
    return danmu_list

def crawl_comments(cid: str) -> List[Dict]:
    """
    爬取评论区留言（支持分页，获取所有评论）
    :param cid: 视频 cid（评论接口中叫 oid）
    :return: 评论列表（包含用户名、内容、时间、点赞数）
    """
    comment_list = []
    page = 0  # 分页参数（从 0 开始）
    max_page = 100  # 防止无限循环（实际不会超过这个页数）
    
    while page < max_page:
        # 评论 API（mode=3 为热门评论，mode=1 为最新评论）
        comment_url = (
            f"https://api.bilibili.com/x/v2/reply/main?jsonp=jsonp"
            f"&next={page}&type=1&oid={cid}&mode=3&plat=1"
            f"&_={int(time.time() * 1000)}"  # 时间戳，避免缓存
        )
        
        try:
            response = requests.get(comment_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != 0:
                print(f"获取评论失败：{data.get('message', '未知错误')}")
                break
            
            # 提取评论核心数据
            replies = data.get("data", {}).get("replies", [])
            if not replies:  # 没有更多评论
                print("评论已全部获取完毕")
                break
            
            for reply in replies:
                comment_info = {
                    "用户名": reply.get("member", {}).get("uname", "未知用户"),
                    "评论内容": reply.get("content", {}).get("message", "").strip(),
                    "发布时间": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(reply.get("ctime", 0))),
                    "点赞数": reply.get("like", 0),
                    "回复数": reply.get("rcount", 0)
                }
                if comment_info["评论内容"]:  # 过滤空评论
                    comment_list.append(comment_info)
            
            print(f"已获取第 {page+1} 页评论，累计 {len(comment_list)} 条")
            page += 1
            time.sleep(1)  # 延时，避免请求过快被反爬
        
        except Exception as e:
            print(f"爬取评论异常（第 {page+1} 页）：{str(e)}")
            time.sleep(3)  # 异常时延时重试
            continue
    
    return comment_list

def save_data(data: List, save_path: str, data_type: str = "danmu") -> None:
    """
    保存数据到本地文件
    :param data: 要保存的数据
    :param save_path: 保存路径
    :param data_type: 数据类型（danmu/comment）
    """
    try:
        with open(save_path, "w", encoding="utf-8") as f:
            if data_type == "danmu":
                # 弹幕按行保存
                for idx, danmu in enumerate(data, 1):
                    f.write(f"{idx}. {danmu}\n")
            elif data_type == "comment":
                # 评论格式化保存
                for idx, comment in enumerate(data, 1):
                    f.write(f"===== 评论 {idx} =====\n")
                    f.write(f"用户名：{comment['用户名']}\n")
                    f.write(f"发布时间：{comment['发布时间']}\n")
                    f.write(f"点赞数：{comment['点赞数']} | 回复数：{comment['回复数']}\n")
                    f.write(f"评论内容：{comment['评论内容']}\n\n")
        
        print(f"数据已保存到：{save_path}")
    except Exception as e:
        print(f"保存数据失败：{str(e)}")

def main():
    print("开始爬取 B 站视频数据...")
    print(f"目标视频：https://www.bilibili.com/video/{BV_ID}/")
    
    # 1. 获取 cid
    cid = get_video_cid(BV_ID)
    if not cid:
        print("获取 cid 失败，程序退出")
        return
    
    # 2. 爬取弹幕
    print("\n开始爬取弹幕...")
    danmu_list = crawl_danmu(cid)
    if danmu_list:
        save_data(danmu_list, DANMU_SAVE_PATH, data_type="danmu")
    
    # 3. 爬取评论
    print("\n开始爬取评论...")
    comment_list = crawl_comments(cid)
    if comment_list:
        save_data(comment_list, COMMENT_SAVE_PATH, data_type="comment")
    
    print("\n爬取任务完成！")

if __name__ == "__main__":
    main()