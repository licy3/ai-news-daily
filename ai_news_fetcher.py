#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI科技资讯抓取与推送脚本（带中文翻译版）
每日抓取过去24小时的AI相关新闻，翻译后通过Server酱推送到微信
"""

import os
import requests
import feedparser
from datetime import datetime, timedelta, timezone
from typing import List, Dict
import time
import re

# 使用 deep-translator，免费且无需API Key
from deep_translator import GoogleTranslator


class Translator:
    """翻译器类 - 使用 deep-translator"""
    
    def __init__(self):
        self.translator = GoogleTranslator(source='auto', target='zh-CN')
        self.cache = {}  # 简单缓存，避免重复翻译
    
    def is_chinese(self, text: str) -> bool:
        """检测文本是否主要是中文"""
        if not text:
            return True
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        return chinese_chars / len(text) > 0.3
    
    def translate(self, text: str) -> str:
        """翻译文本到中文"""
        if not text or self.is_chinese(text):
            return ""  # 已经是中文，不需要翻译
        
        # 检查缓存
        cache_key = text[:100]  # 用前100字符作为缓存key
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # 限制翻译文本长度，避免超时
            text_to_translate = text[:500] if len(text) > 500 else text
            translated = self.translator.translate(text_to_translate)
            
            # 缓存结果
            self.cache[cache_key] = translated
            
            # 添加延迟，避免请求过快
            time.sleep(0.5)
            
            return translated
        except Exception as e:
            print(f"  翻译失败: {str(e)}")
            return ""


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
            "keywords": None
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
            "name": "AI News",
            "url": "https://www.artificialintelligence-news.com/feed/",
            "keywords": None
        },
    ]
    
    def __init__(self):
        self.news_items: List[Dict] = []
        self.time_threshold = datetime.now(timezone.utc) - timedelta(hours=24)
        self.translator = Translator()
    
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
                summary = entry.get('summary', '')[:300] if entry.get('summary') else ''
                
                # 如果有关键词过滤
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
    
    def translate_news(self):
        """为所有新闻添加中文翻译"""
        print("\n🌐 正在翻译新闻标题...")
        
        for i, item in enumerate(self.news_items):
            print(f"  翻译进度: {i+1}/{len(self.news_items)}")
            
            # 翻译标题
            item['title_cn'] = self.translator.translate(item['title'])
            
            # 翻译摘要（如果有的话）
            if item.get('summary'):
                item['summary_cn'] = self.translator.translate(item['summary'])
            else:
                item['summary_cn'] = ""
        
        print("✓ 翻译完成")
    
    def fetch_all(self) -> List[Dict]:
        """从所有RSS源抓取新闻"""
        all_items = []
        
        for source in self.RSS_SOURCES:
            items = self.fetch_from_rss(source)
            all_items.extend(items)
            time.sleep(1)
        
        # 去重
        seen_titles = set()
        unique_items = []
        for item in all_items:
            title_key = item['title'][:30].lower()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_items.append(item)
        
        # 按时间排序
        unique_items.sort(key=lambda x: x['pub_time'], reverse=True)
        
        self.news_items = unique_items[:20]  # 限制20条以控制翻译时间
        
        # 翻译新闻
        self.translate_news()
        
        return self.news_items
    
    def format_for_wechat(self) -> tuple:
        """格式化新闻内容用于微信推送（中英双语版）"""
        if not self.news_items:
            return "今日AI资讯", "暂无最新AI科技资讯"
        
        title = f"📰 AI科技日报 ({datetime.now().strftime('%Y-%m-%d')})"
        
        content_lines = [
            f"## 🤖 过去24小时AI科技要闻\n",
            f"共收集到 **{len(self.news_items)}** 条相关资讯（中英双语）\n",
            "---\n"
        ]
        
        for i, item in enumerate(self.news_items, 1):
            # 英文原标题
            content_lines.append(f"### {i}. {item['title']}\n")
            
            # 中文翻译标题（如果有）
            if item.get('title_cn'):
                content_lines.append(f"**📝 中文：** {item['title_cn']}\n\n")
            
            # 摘要（如果有）
            if item.get('summary_cn'):
                # 清理HTML标签
                summary_clean = re.sub(r'<[^>]+>', '', item['summary_cn'])[:150]
                content_lines.append(f"> 💡 {summary_clean}...\n\n")
            
            content_lines.append(
                f"- 🔗 来源: {item['source']}\n"
                f"- 🕐 时间: {item['pub_time']}\n"
                f"- 📎 [阅读原文]({item['link']})\n\n"
            )
        
        content_lines.append("\n---\n")
        content_lines.append(f"*由 GitHub Actions 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        content_lines.append("*翻译由 Google Translate 提供*")
        
        content = ''.join(content_lines)
        return title, content


class ServerChanPusher:
    """Server酱推送器"""
    
    def __init__(self, sendkey: str):
        self.sendkey = sendkey
        self.api_url = f"https://sctapi.ftqq.com/{sendkey}.send"
    
    def push(self, title: str, content: str) -> bool:
        """推送消息到微信"""
        try:
            if len(title) > 256:
                title = title[:253] + "..."
            
            data = {
                "title": title,
                "desp": content,
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
    print("AI科技资讯抓取与推送（中英双语版）")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    sendkey = os.environ.get('SERVERCHAN_SENDKEY')
    
    if not sendkey:
        print("错误: 未设置 SERVERCHAN_SENDKEY 环境变量")
        exit(1)
    
    # 1. 抓取新闻
    print("\n📡 开始抓取AI科技资讯...\n")
    fetcher = AINewsFetcher()
    news = fetcher.fetch_all()
    
    print(f"\n✓ 共处理 {len(news)} 条AI相关新闻\n")
    
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
