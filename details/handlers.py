from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, ReplyKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CallbackContext
from settings import *
from details.buttons import *
from details.messages import *
from database.db import *
from parsing.parser import *
import re
from pprint import pprint

bot = Bot(token=TOKEN)

async def loading_animation(message, msg):
    await asyncio.sleep(2)
    texts = [
        f"{msg} qidirilmoqda 🔎",
        f"{msg} qidirilmoqda 🔍"
    ]
    i = 0

    try:
        while True:
            await message.edit_text(texts[i % 2])
            i += 1
            await asyncio.sleep(0.5)
    except asyncio.CancelledError:
        pass

async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_msg_id = update.message.message_id
    insert(table="users", user_id=update.effective_chat.id, data={"stage": "start", "len_products": 20, "index": 0})
    bot_msg = await bot.send_message(
        chat_id=chat_id,
        text=start_message.format(update.effective_user.first_name),
        reply_markup=ReplyKeyboardMarkup(start_but, resize_keyboard=True),
        parse_mode=ParseMode.HTML
    )

async def text(update: Update, context: CallbackContext):
    text    = update.message.text
    user_id = update.effective_chat.id
    stage   = get(table="users", user_id=user_id)["stage"]

    if text == "📊 Statistika":
        stats = get(table="statistics")[0]
        total_users = len(get(table="users"))
        total_searchs = stats["total_searchs"]
        total_products = stats["total_products"]

        msg = await update.message.reply_text(
            text=stats_mes.format(total_users, total_searchs, total_products),
            reply_markup=ReplyKeyboardMarkup(back_but, resize_keyboard=True),
            parse_mode=ParseMode.HTML
        )
        context.user_data.setdefault("messages", []).append(update.message.message_id)
        context.user_data.setdefault("messages", []).append(msg.message_id)
        return

    if text == "Qidiruv tarixi💡":
        index = get(table="users", user_id=user_id)['index']
        context.user_data.setdefault("messages", []).append(update.message.message_id)
        history = get(table="products", user_id=user_id)
        if not history:
            msg = await update.message.reply_text(
                text="Siz hali hech qanday mahsulot qidiruvidan foydalanmagansiz.⚠️",
                reply_markup=ReplyKeyboardMarkup(back_but, resize_keyboard=True)
            )
            context.user_data.setdefault("messages", []).append(msg.message_id)
            return
        
        products    = history[0]["items"]
        product     = products[index]
        product_url = product['product_url']
        product_but = [
            [InlineKeyboardButton("Batafsil ℹ️", callback_data="info")],
            [InlineKeyboardButton("⏮️", callback_data='prev'), InlineKeyboardButton("Yandex🟡", url=product_url), InlineKeyboardButton("⏭️", callback_data='next')]
        ]
        digits = ''.join(c for c in product['price'] if c.isdigit())
        price = f"{int(digits):,}".replace(",", ".")

        title       = product['title']
        image_url   = product['image_url']
        status      = product['status']
        product_name= product['product_name']
        num         = index + 1
        total       = len(products)

        bot_msg = await update.message.reply_photo(
            photo=image_url,
            caption=product_mes.format(title, price, status, product_name, num, total),
            reply_markup=InlineKeyboardMarkup(product_but),
            parse_mode=ParseMode.HTML
        )

        context.user_data.setdefault("messages", []).append(bot_msg.message_id)
        bot_msg = await update.message.reply_text(
            text="Oxirgi qidiruvingiz: {}".format(product_name),
            reply_markup=ReplyKeyboardMarkup(back_but, resize_keyboard=True)
        )

        upd(table="users", user_id=user_id, data={"stage": "history"})
        context.user_data.setdefault("messages", []).append(bot_msg.message_id)
        return

    if text == "🔍 Qidirish":
        upd(table="users", user_id=user_id, data={"stage": "search"})

        context.user_data.setdefault("messages", []).append(update.message.message_id)

        msg = await update.message.reply_text(
            text=search_mode_mes,
            reply_markup=ReplyKeyboardMarkup(back_but, resize_keyboard=True)
        )
        context.user_data.setdefault("messages", []).append(msg.message_id)

        lens = get(table="users", user_id=user_id)['len_products']
        if lens == 10:
            button = but_10
        elif lens == 20:
            button = but_20
        else:
            button = but_50

        msg = await update.message.reply_text(
            text="Qaytariladigan mahsulotlar sonini o'zgartirishingiz mumkin:",
            reply_markup=InlineKeyboardMarkup(button)
        )
        context.user_data.setdefault("messages", []).append(msg.message_id)
        return

    if text == "Ortga🔙":
        upd(table="users", user_id=user_id, data={"stage": "start"})

        context.user_data.setdefault("messages", []).append(update.message.message_id)
        messages = context.user_data.get("messages", [])
        for msg_id in messages:
            try:
                await bot.delete_message(chat_id=user_id, message_id=msg_id)
            except:
                pass
        context.user_data["messages"] = []

        msg = await update.message.reply_text(
            text=back_mes,
            reply_markup=ReplyKeyboardMarkup(start_but, resize_keyboard=True)
        )
        context.user_data.setdefault("messages", []).append(msg.message_id)
        return


    if stage == "search" and stage != "waiting":
        upd(table="users", user_id=user_id, data={"index": 0, "stage": "waiting"})
        context.user_data.setdefault("messages", []).append(update.message.message_id)
        loading_msg = await update.message.reply_text(
            text=f"{text} 👍"
        )

        task = asyncio.create_task(
            loading_animation(loading_msg, msg=text)
        )

        lens = get(table="users", user_id=user_id)['len_products']
        natija = await search_product(text, user_id=user_id, product_count=lens)

        if natija == False:
            task.cancel()
            await loading_msg.delete()

            bot_msg = await update.message.reply_text(
                text="Kechirasiz, siz qidirgan mahsulot yetarlicha topilmadi.⚠️ Iltimos, boshqa mahsulot nomini kiriting.❕",
                reply_markup=ReplyKeyboardMarkup(back_but, resize_keyboard=True)
            )
        elif natija == True:
            task.cancel()
            await loading_msg.delete()

            products = get(table="products", user_id=user_id)[0]["items"]
            index = get(table="users", user_id=user_id)['index']  
            product = products[index]
            product_url = product['product_url']

            product_but = [
                [InlineKeyboardButton("Batafsil ℹ️", callback_data="info")],
                [InlineKeyboardButton("⏮️", callback_data='prev'), InlineKeyboardButton("Yandex🟡", url=product_url), InlineKeyboardButton("⏭️", callback_data='next')]
            ]

            digits = ''.join(c for c in product['price'] if c.isdigit())
            price = f"{int(digits):,}".replace(",", ".")

            title       = product['title']
            image_url   = product['image_url']
            status      = product['status']
            product_name= product['product_name']
            num         = product['num']
            total       = len(products)

            all_searchs = get(table="statistics")[0]["total_searchs"]
            all_products = get(table="statistics")[0]["total_products"]
            upd(table="statistics", user_id=1, data={"total_searchs": all_searchs + 1, "total_products": all_products + total})

            bot_msg = await update.message.reply_photo(
                photo=image_url,
                caption=product_mes.format(title, price, status, product_name, num, total),
                reply_markup=InlineKeyboardMarkup(product_but),
                parse_mode=ParseMode.HTML
            )
        upd(table="users", user_id=user_id, data={"stage": "search"})
        context.user_data.setdefault("messages", []).append(bot_msg.message_id)
    
    if stage == "waiting":
        await update.message.reply_text(
            text="Iltimos, Sabrli bo'ling, ma'lumotlar yig'ilmoqda...❗️",
            reply_markup=ReplyKeyboardMarkup(back_but, resize_keyboard=True)
        )
                
            
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.message.chat.id
    data = query.data
    stage = get(table="users", user_id=user_id)["stage"]
    print(stage)

    if stage == "waiting":
        await query.answer("So'rovingiz bo'yicha ma'lumotlar yig'ilmoqda...❗️", show_alert=True)
        return
    if data == '10':
        upd(table="users", user_id=user_id, data={"stage": "search", "len_products": 10})
        await query.answer()
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(but_10)
        )
    elif data == '20':
        upd(table="users", user_id=user_id, data={"stage": "search", "len_products": 20})
        await query.answer()
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(but_20)
        )
    elif data == '50':
        upd(table="users", user_id=user_id, data={"stage": "search", "len_products": 50})
        await query.answer()
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(but_50)
        )
    elif data == 'info':
        
        if stage == "waiting":
            await query.answer("Sabrli bo'ling!", show_alert=True)
            return
    

        
        message = query.message.caption

        if len(message) > 600:
            await query.answer("Yanayam ko'proq ma'lumot olish uchun 'Yandex🟡' knopkasini bosing!", show_alert=True)
            return
        
        upd(table="users", user_id=user_id, data={"stage": "waiting"})
        msg = await query.message.reply_text(text="⚠️Ushbu mahsulot bo'yicha ma'lumotlar yig'ish boshlandi...\nSabrli bo'ling, bu 5-15soniya vaqt davom etadi.❗️")
        context.user_data["alert"] = msg.message_id


        last_line = message.strip().splitlines()[-1]
        value = last_line.split("|")[0].split()[-1]
        user_id = query.message.chat.id

        index = int(value) - 1

        products = get(table="products", user_id=user_id)[0]["items"]
        product = products[index]
        product_url = product['product_url']
        nat = await get_product_details(product_url)

        if nat:
            upd(table="users", user_id=user_id, data={"stage": "search"})
            digits = ''.join(c for c in nat.get('price') if c.isdigit())
            price = f"{int(digits):,}".replace(",", ".")+" so'm"
            mes = nat.get("shop_votes","N/A")
            lines = mes.splitlines()

            index = get(table="users", user_id=user_id)['index']
            products = get(table="products", user_id=user_id)[0]["items"]
            product_name= products[index]['product_name']
            product_url = products[index]['product_url']
            num         = index + 1
            total = len(products)

            product_but = [
                [InlineKeyboardButton("⏮️", callback_data='prev'), InlineKeyboardButton("Yandex🟡", url=product_url), InlineKeyboardButton("⏭️", callback_data='next')]
            ]

            try:
                shop_rating = lines[2]
                shop_votes = lines[3].replace("оценок","")
            except:
                shop_rating = 0
                shop_votes = 0
            
            description = nat.get("description")
            if len(description) > 600:
                description = description[:600] + "..."
            details_mes = detail_mes.format(
                nat.get("title"),
                price,
                nat.get("rating","Yo'q"),
                nat.get("votes_count", 0),
                nat.get("bought_count").replace("купили",""),
                nat.get("seller_name"),
                shop_rating,
                shop_votes,
                description,
                product_name, num, total
            )
            await query.message.edit_caption(
                caption=details_mes,
                parse_mode=ParseMode.HTML
            )
            await query.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup(product_but)
            )
            msg_id = context.user_data.get("alert")
            if msg_id:
                try:
                    await bot.delete_message(chat_id=user_id, message_id=msg_id)
                except:
                    pass
                context.user_data["alert"] = None
        else:
            upd(table="users", user_id=user_id, data={"stage": "search"})
            await query.message.reply_text(
                text="Kechirasiz, mahsulot haqida batafsil ma'lumot olishning imkoni bo'lmadi.",
                parse_mode=ParseMode.HTML,
            )
            msg_id = context.user_data.get("alert")
            if msg_id:
                try:
                    await bot.delete_message(chat_id=user_id, message_id=msg_id)
                except:
                    pass
                context.user_data["alert"] = None
        

    elif data == 'next' or data == 'prev':
        products = get(table="products", user_id=user_id)[0]["items"]
        index = get(table="users", user_id=user_id)['index']
        total = len(products)

        if data == 'next':
            if index + 1 >= total:
                await query.answer("Ro'yxat boshiga qaytdinhiz!")
                index = 0
            else:
                index += 1
        else:
            if index - 1 < 0:
                await query.answer("Ro'yxat oxiriga qaytdingiz!")
                index = total-1
            else:
                index -= 1

        upd(table="users", user_id=user_id, data={"index": index})
        product = products[index]
        product_url = product['product_url']

        digits = ''.join(c for c in product['price'] if c.isdigit())
        price = f"{int(digits):,}".replace(",", ".")

        title       = product['title']
        image_url   = product['image_url']
        status      = product['status']
        product_name= product['product_name']
        num         = index + 1

        product_but = [
            [InlineKeyboardButton("Batafsil ℹ️", callback_data="info")],
            [InlineKeyboardButton("⏮️", callback_data='prev'), InlineKeyboardButton("Yandex🟡", url=product_url), InlineKeyboardButton("⏭️", callback_data='next')]
        ]

        await query.message.edit_media(
            media=InputMediaPhoto(
                media=image_url,
                caption=product_mes.format(title, price, status, product_name, num, total),
                parse_mode=ParseMode.HTML
            ),
            reply_markup=InlineKeyboardMarkup(product_but)
        )










