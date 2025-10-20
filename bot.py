import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import openai

# Настройки
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Настройка OpenAI
client = openai.OpenAI(api_key=OPENAI_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
Привет! 🔮 Я - AI-таролог. 
Просто напиши мне свой вопрос, и я посмотрю, что говорят карты.

Используй /card для случайной карты дня.
    """
    await update.message.reply_text(text)

async def card_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action(action="typing")
    
    # Общаемся с ИИ
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Ты - мудрый таролог. Дай краткое предсказание на день (2-3 предложения) в мистическом стиле."},
            {"role": "user", "content": "Вытащи случайную карту Таро и дай предсказание"}
        ],
        max_tokens=150
    )
    
    prediction = response.choices[0].message.content
    await update.message.reply_text(f"🃏 Карта дня: \n\n{prediction}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    if user_message.startswith('/'):
        return

    await update.message.chat.send_action(action="typing")
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", 
        messages=[
            {"role": "system", "content": "Ты - эзотерический таролог. Ответь на вопрос пользователя метафорично, как при гадании на картах. Будь загадочным."},
            {"role": "user", "content": user_message}
        ],
        max_tokens=200
    )
    
    answer = response.choices[0].message.content
    await update.message.reply_text(f"🔮 {answer}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("card", card_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
