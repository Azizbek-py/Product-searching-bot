from telegram import InlineKeyboardButton

start_but = [
    ['🔍 Qidirish'],
    ["Qidiruv tarixi💡",'📊 Statistika']
]

back_but = [
    ["Ortga🔙"]
]

but_10 = [
    [InlineKeyboardButton("10 ta✅", callback_data='10'), InlineKeyboardButton("20 ta", callback_data='20'), InlineKeyboardButton("50 ta", callback_data='50')]
]

but_20 = [
    [InlineKeyboardButton("10 ta", callback_data='10'), InlineKeyboardButton("20 ta✅", callback_data='20'), InlineKeyboardButton("50 ta", callback_data='50')]
]

but_50 = [
    [InlineKeyboardButton("10 ta", callback_data='10'), InlineKeyboardButton("20 ta", callback_data='20'), InlineKeyboardButton("50 ta✅", callback_data='50')]
]

