#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI科技资讯抓取与推送脚本
每日抓取过去24小时的AI相关新闻，通过Server酱推送到微信
"""

import os
import requests
import feedparser
from datetime import datetime, timedelta, timezone
from typing import List, Dict
import time


class AINewsFetcher:
    """AI新闻抓取器"""
    
    # AI科技相关RSS源列表
    RSS_SOURCES = [
        {
            "name": "MIT Technology Review - AI",
            "url": "https://www.technologyreview.com/feed/",
            "keywords": ["AI", "artificial intelligence", "machine learning", "GPT", "LLM"]
        },
        {
            "name": "VentureBeat AI",
            "url": "https://venturebeat.com/category/ai/feed/",
            "keywords": None  # 该源本身就是AI分类
        },
        {
            "name": "The Verge - AI",
            "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
            "keywords": None
        },
        {
            "name": "Ars Technica",
            "url": "https://feeds.arstechnica.com/arstechnica/index",
            "keywords": ["AI", "artificial intelligence", "ChatGPT", "OpenAI", "Google AI", "machine learning"]
        },
        {
            "name": "TechCrunch AI",
            "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
            "keywords": None
        },
        {
            "name": "Hacker News",
            "url": "https://hnrss.org/newest?q=AI+OR+LLM+OR+GPT+OR+artificial+intelligence",
            "keywords": None
        },
        {
            "name": "Reddit - Artificial Intelligence",
            "url": "https://www.reddit.com/r/artificial/.rss",
            "keywords": None
        },
        {
            "name": "AI News",
            "url": "https://www.artificialintelligence-news.com/feed/",
            "keywords": None
        },
    ]
    
    def __init__(self):
        self.news_items: List[Dict] = []
        # 24小时前的时间戳
        self.time_threshold = datetime.now(timezone.utc) - timedelta(hours=24)
    
    def fetch_from_rss(self, source: Dict) -> List[Dict]:
        """从单个RSS源抓取新闻"""
        items = []
        try:
            print(f"正在抓取: {source['name']}")
            feed = feedparser.parse(source['url'])
            
            for entry in feed.entries:
                # 解析发布时间
                pub_time = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    pub_time = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                
                # 检查是否在24小时内
                if pub_time and pub_time < self.time_threshold:
                    continue
                
                # 获取标题和链接
                title = entry.get('title', 'No Title')
                link = entry.get('link', '')
                summary = entry.get('summary', '')[:200] if entry.get('summary') else ''
                
                # 如果有关键词过滤，检查标题或摘要是否包含关键词
                if source['keywords']:
                    text_to_check = (title + ' ' + summary).lower()
                    if not any(kw.lower() in text_to_check for kw in source['keywords']):
                        continue
                
                items.append({
                    'title': title,
                    'link': link,
                    'source': source['name'],
                    'pub_time': pub_time.strftime('%Y-%m-%d %H:%M') if pub_time else 'Unknown',
                    'summary': summary
                })
            
            print(f"  → 获取到 {len(items)} 条相关新闻")
            
        except Exception as e:
            print(f"  ✗ 抓取失败: {str(e)}")
        
        return items
    
    def fetch_all(self) -> List[Dict]:
        """从所有RSS源抓取新闻"""
        all_items = []
        
        for source in self.RSS_SOURCES:
            items = self.fetch_from_rss(source)
            all_items.extend(items)
            time.sleep(1)  # 避免请求过快
        
        # 去重（基于标题相似度）
        seen_titles = set()
        unique_items = []
        for item in all_items:
            # 简单去重：检查标题的前30个字符
            title_key = item['title'][:30].lower()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_items.append(item)
        
        # 按时间排序（最新的在前）
        unique_items.sort(key=lambda x: x['pub_time'], reverse=True)
        
        self.news_items = unique_items[:30]  # 最多保留30条
        return self.news_items
    
    def format_for_wechat(self) -> tuple:
        """格式化新闻内容用于微信推送"""
        if not self.news_items:
            return "今日AI资讯", "暂无最新AI科技资讯"
        
        title = f"📰 AI科技日报 ({datetime.now().strftime('%Y-%m-%d')})"
        
        # 构建Markdown格式的内容
        content_lines = [
            f"## 过去24小时AI科技要闻\n",
            f"共收集到 **{len(self.news_items)}** 条相关资讯\n",
            "---\n"
        ]
        
        for i, item in enumerate(self.news_items, 1):
            content_lines.append(
                f"### {i}. {item['title']}\n"
                f"- 🔗 来源: {item['source']}\n"
                f"- 🕐 时间: {item['pub_time']}\n"
                f"- 📎 [阅读原文]({item['link']})\n\n"
            )
        
        content_lines.append("\n---\n")
        content_lines.append(f"*由 GitHub Actions 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        content = ''.join(content_lines)
        return title, content


class ServerChanPusher:
    """Server酱推送器"""
    
    def __init__(self, sendkey: str):
        """
        初始化Server酱推送器
        
        Args:
            sendkey: Server酱的SendKey，从 https://sctapi.ftqq.com 获取
        """
        self.sendkey = sendkey
        # Server酱 Turbo 版 API 地址
        self.api_url = f"https://sctapi.ftqq.com/{sendkey}.send"
    
    def push(self, title: str, content: str) -> bool:
        """
        推送消息到微信
        
        Args:
            title: 消息标题，最长256字符
            content: 消息内容，支持Markdown格式，最长64KB
            
        Returns:
            bool: 推送是否成功
        """
        try:
            # 截断标题（Server酱限制256字符）
            if len(title) > 256:
                title = title[:253] + "..."
            
            # Server酱支持 POST 请求
            data = {
                "title": title,
                "desp": content,  # desp 支持 Markdown
            }
            
            response = requests.post(self.api_url, data=data, timeout=30)
            result = response.json()
            
            if result.get('code') == 0:
                print(f"✓ 消息推送成功！")
                return True
            else:
                print(f"✗ 消息推送失败: {result.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"✗ 推送异常: {str(e)}")
            return False


def main():
    """主函数"""
    print("=" * 50)
    print("AI科技资讯抓取与推送")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 从环境变量获取 Server酱 SendKey
    sendkey = os.environ.get('SERVERCHAN_SENDKEY')
    
    if not sendkey:
        print("错误: 未设置 SERVERCHAN_SENDKEY 环境变量")
        print("请在 GitHub Secrets 中添加 SERVERCHAN_SENDKEY")
        exit(1)
    
    # 1. 抓取新闻
    print("\n📡 开始抓取AI科技资讯...\n")
    fetcher = AINewsFetcher()
    news = fetcher.fetch_all()
    
    print(f"\n✓ 共抓取到 {len(news)} 条AI相关新闻\n")
    
    # 2. 格式化内容
    title, content = fetcher.format_for_wechat()
    
    # 3. 推送到微信
    print("📤 正在推送到微信...")
    pusher = ServerChanPusher(sendkey)
    success = pusher.push(title, content)
    
    if success:
        print("\n🎉 任务完成！请查看微信消息。")
    else:
        print("\n❌ 推送失败，请检查配置。")
        exit(1)


if __name__ == "__main__":
    main()
