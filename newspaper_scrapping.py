#!/usr/bin/env python
# coding: utf-8

# In[1]:


from playwright.async_api import async_playwright
import asyncio
from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://localhost:27017/") # need to on env. for local can't do it right now.
db = client["bd-newspaper-collection"]
collection = db["articles"]

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
            news_list.append((title, href))
            
        await browser.close()
    return news_list

def save_mongo(news_list):
    for title,url in news_list:
        if not collection.find_one({"url": url}):
            collection.insert_one({
                "title": title,
                "url": url,
                "media_name": "prothomalo",
                "scraped_at": datetime.now()
            })
            #print(f"Inserted: {title}")
        
async def main():
    news_list = await fetch_with_playwright()
    save_mongo(news_list)
    print("done", datetime.now())

if __name__ == "__main__":
    asyncio.run(main())




