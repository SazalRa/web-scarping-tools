#!/usr/bin/env python
# coding: utf-8

# In[1]:


from playwright.async_api import async_playwright
import asyncio
from pymongo import MongoClient
from datetime import datetime, timedelta

client = MongoClient("mongodb://localhost:27017/") # need to on env. for local can't do it right now.
db = client["bd-newspaper-collection"]
collection = db["articles"]


# Helper Function for calculated published Time


# Mapping Bengali digits to English
bn_digit_map = {
    '০': '0', '১': '1', '২': '2', '৩': '3', '৪': '4',
    '৫': '5', '৬': '6', '৭': '7', '৮': '8', '৯': '9'
}

def bn_to_en_digits(bn_str):
    return ''.join([bn_digit_map.get(ch, ch) for ch in bn_str])
    
###########################################################################
# Function for convert bangla time english and return real published time    
###########################################################################

def parse_bengali_relative_time(bn_time_str):
    if "No time found" in bn_time_str:
        return "No time found"
        
    now = datetime.now()
    
    bn_time_str = bn_time_str.strip()
    
    # Extract number
    num_str = ''.join([bn_digit_map.get(ch, ch) for ch in bn_time_str if ch in bn_digit_map or ch.isdigit()])
    num = int(num_str) if num_str else 0

    if 'সেকেন্ড' in bn_time_str:
        delta = timedelta(seconds=num)
    elif 'মিনিট' in bn_time_str:
        delta = timedelta(minutes=num)
    elif 'ঘণ্টা' in bn_time_str:
        delta = timedelta(hours=num)
    elif 'দিন' in bn_time_str:
        delta = timedelta(days=num)
    else:
        delta = timedelta()  # fallback

    return now - delta



async def fetch_with_playwright():
    news_list = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        page = await browser.new_page()
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
        })
        await page.goto("https://www.prothomalo.com/collection/latest", timeout=60000)
        await page.wait_for_selector("#container", timeout=15000)
        #Wait for a card to appear inside container
        await page.wait_for_selector("#container div.news_with_item", timeout=10000)
        elements = await page.locator("h3.headline-title").all()
        for el in elements:
            link_el  =  el.locator("a.title-link")
            href = await link_el.get_attribute("href")
            title = (await el.inner_text()).strip()
            time_locator = el.locator("xpath=following::time[contains(@class, 'published-time')]")
        
            # Check if it exists
            if await time_locator.count() > 0:
                published_time = await time_locator.first.inner_text()
            else:
                published_time = "No time found"
            print("published_time", published_time)
            news_list.append((title, href, published_time))
            
        await browser.close()
    return news_list

def save_mongo(news_list):
    for title, url, published_time in news_list:
        if not collection.find_one({"url": url}):
            published_time = parse_bengali_relative_time(published_time)
            collection.insert_one({
                "title": title,
                "url": url,
                "media_name": "prothomalo",
                "published_time": published_time,
                "scraped_at": datetime.now()
            })
            #print(f"Inserted: {title}")
        
async def main():
    news_list = await fetch_with_playwright()
    save_mongo(news_list)
    print("done", datetime.now())

if __name__ == "__main__":
    asyncio.run(main())




