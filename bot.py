import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎉 Бот работает! Тест успешен!")

async def card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🃏 Тестовая карта: Удача сегодня с вами!")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("card", card))
    app.run_polling()

if __name__ == '__main__':
    main()
