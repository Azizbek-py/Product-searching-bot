import asyncio
from playwright.async_api import async_playwright
from database.db import *
from deep_translator import GoogleTranslator


async def search_product(product_name, user_id, product_count=20):
    url = f"https://market.yandex.uz/search?text={product_name}"

    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=False, slow_mo=80)
    page = await browser.new_page()

    await page.goto(url, timeout=0)
    await page.wait_for_selector("article", timeout=60000)

    await page.keyboard.press("Escape")
    await asyncio.sleep(1)

    products = []
    scrolls = 0
    num = 1

    while len(products) < product_count and scrolls < 12:
        cards = page.locator("article")
        count = await cards.count()

        for i in range(count):
            card = cards.nth(i)

            title_el = card.locator("span[data-auto='snippet-title']")
            link_el = card.locator("a[data-auto='snippet-link']")
            price_el = card.locator("span[data-auto='snippet-price-current']")
            img_el = card.locator("img")

            if await title_el.count() == 0 or await link_el.count() == 0:
                continue

            title = await title_el.first.inner_text()
            link = await link_el.first.get_attribute("href")
            price = await price_el.first.inner_text() if await price_el.count() > 0 else None
            image = await img_el.first.get_attribute("src") if await img_el.count() > 0 else None

            data = {
                "num": num,
                "title": title,
                "price": price,
                "image_url": image,
                "product_url": f"https://market.yandex.uz{link}",
                "status": "Hozir sotuvda bor",
                "user_id": user_id,
                "product_name": product_name
            }

            if data not in products:
                products.append(data)
                num += 1

        await page.mouse.wheel(0, 2500)
        await asyncio.sleep(2)
        scrolls += 1

    await browser.close()
    await p.stop()

    if not products:
        return False

    insert(table="products", data=products[:product_count], user_id=user_id)
    return True


async def get_product_details(url):
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=False, slow_mo=80)
    page = await browser.new_page()

    await page.goto(url, timeout=0)
    await page.wait_for_selector("h1", timeout=60000)

    await page.keyboard.press("Escape")
    await asyncio.sleep(1)

    data = {}

    title_el = page.locator("h1")
    data["title"] = await title_el.inner_text() if await title_el.count() > 0 else "Mahsulot nomida muammo bo'lishi mumkin, Keyingi tovarga o'ting."

    price_el = page.locator("span[data-auto='price'], span[data-auto='snippet-price-current']")
    data["price"] = await price_el.first.inner_text() if await price_el.count() > 0 else "Narxi yozilmagan."

    rating_block = page.locator("a[href*='reviews']")
    if await rating_block.count() > 0:
        text = await rating_block.first.inner_text()
        parts = text.replace("·", "").split()

        data["rating"] = parts[0] if len(parts) > 0 else "Reyting ko'rsatilmagan."

        if "(" in text and ")" in text:
            data["votes_count"] = text[text.find("(")+1:text.find(")")]
        else:
            data["votes_count"] = "Ovoz berganlar soni ko'rsatilmagan"
    else:
        data["rating"] = "Reyting ko'rsatilmagan."
        data["votes_count"] = "Ovoz berganlar soni ko'rsatilmagan"

    bought_el = page.locator("span:has-text('купили')")
    data["bought_count"] = await bought_el.first.inner_text() if await bought_el.count() > 0 else "Sotib olganlar soni noma'lum"
    
    seller_name = "Yandex Market"

    blocks = page.locator("div")
    count = await blocks.count()

    for i in range(count):
        block = blocks.nth(i)
        text = await block.inner_text()

        if "Магазин" in text and "\n" in text:
            if " оценок" in text:
                lines = [l.strip() for l in text.splitlines() if l.strip()]
                seller_name = lines[-5]
        
    data["seller_name"] = seller_name



    shop_rating_el = page.locator("span[data-auto='shop-rating']")
    data["shop_rating"] = await shop_rating_el.first.inner_text() if await shop_rating_el.count() > 0 else "Mavjud emas"

    shop_votes_el = page.locator("span:has-text('оцен')")
    data["shop_votes"] = await shop_votes_el.first.inner_text() if await shop_votes_el.count() > 0 else "Mavjud emas"

    desc_el = page.locator("div[data-auto='product-description']")
    translate_text = GoogleTranslator(source='auto', target='uz').translate(await desc_el.inner_text() if await desc_el.count() > 0 else "не написано.")
    data["description"] = translate_text




    await page.evaluate("""
        const el = document.querySelector("a[href='#fullSpecsAnchorId']");
        if (el) el.click();
    """)

    await asyncio.sleep(1)

    specs_el = page.locator("div[data-auto='specifications']")
    data["specifications"] = await specs_el.inner_text() if await specs_el.count() > 0 else "yozilmagan."

    await browser.close()
    await p.stop()

    return data
