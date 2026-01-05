import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from settings import *
from details.handlers import *

app = Application.builder().token(TOKEN).build()


app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, text))
app.add_handler(CallbackQueryHandler(button_handler))



if __name__ == "__main__":
    print("Pooling ishlayapti...")
    app.run_polling(
    allowed_updates=[Update.MESSAGE, Update.CALLBACK_QUERY],
    drop_pending_updates=True,
    )