import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import openai
from datetime import date

# Настройки
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Храним последние бесплатные запросы
user_last_free_date = {}

# Настройка OpenAI (старая версия)
openai.api_key = OPENAI_API_KEY

def can_use_free(user_id):
    """Проверяет, может ли пользователь использовать бесплатный запрос сегодня"""
    today = date.today()
    
    if user_id not in user_last_free_date:
        user_last_free_date[user_id] = today
        return True
    
    if user_last_free_date[user_id] == today:
        return False
    else:
        user_last_free_date[user_id] = today
        return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    text = f"""
Привет, {update.effective_user.first_name}! 🔮 

Я - AI-таролог. У тебя есть **1 бесплатный запрос в день**.

После этого каждый запрос стоит **50 рублей**.

💫 Команды:
/card - получить карту дня (использует бесплатный запрос)
/balance - проверить баланс
/buy - купить дополнительные запросы

Просто напиши свой вопрос - и я посмотрю, что говорят карты!
    """
    await update.message.reply_text(text)

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает статус запросов"""
    user_id = update.effective_user.id
    
    if can_use_free(user_id):
        status = "✅ У тебя есть бесплатный запрос на сегодня!"
    else:
        status = "❌ Бесплатный запрос на сегодня использован"
    
    text = f"""
{status}

💳 Чтобы купить дополнительные запросы, используй /buy
    """
    await update.message.reply_text(text)

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для покупки запросов"""
    text = """
💳 **Покупка дополнительных запросов**

🎯 Тарифы:
• 5 запросов - 200 рублей
• 15 запросов - 500 рублей  
• 30 запросов - 800 рублей

💸 **Способы оплаты:**
1. СБП (по номеру телефона)
2. Карта (Tinkoff, Сбер)

📨 Для оплаты напишите @ваш_логин

После оплаты вы получите запросы в течение 5 минут!
    """
    await update.message.reply_text(text)

async def get_ai_prediction(prompt):
    """Функция для работы со старой версией OpenAI"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты - мудрый таролог. Дай краткое предсказание (2-3 предложения) в мистическом стиле. Назови конкретную карту Таро и ее значение."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"OpenAI error: {e}")
        return "К сожалению, карты пока молчат. Попробуйте позже."

async def card_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выдает карту дня с проверкой лимита"""
    user_id = update.effective_user.id
    
    if not can_use_free(user_id):
        await update.message.reply_text(
            "❌ Бесплатный запрос на сегодня уже использован!\n\n"
            "💳 Используй /buy чтобы купить дополнительные запросы\n"
            "📊 Или проверь /balance"
        )
        return
    
    await update.message.chat.send_action(action="typing")
    
    prediction = await get_ai_prediction("Вытащи случайную карту Таро и дай предсказание на сегодня")
    await update.message.reply_text(f"🃏 Карта дня: \n\n{prediction}\n\n✨ Бесплатный запрос использован")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает обычные сообщения с проверкой лимита"""
    user_message = update.message.text
    user_id = update.effective_user.id
    
    if user_message.startswith('/'):
        return
    
    if not can_use_free(user_id):
        await update.message.reply_text(
            "❌ Бесплатный запрос на сегодня уже использован!\n\n"
            f"💫 Твой вопрос: '{user_message}'\n\n"
            "💳 Чтобы получить ответ, используй /buy для покупки запросов\n"
            "📊 Или проверь /balance"
        )
        return
    
    await update.message.chat.send_action(action="typing")
    
    prediction = await get_ai_prediction(user_message)
    await update.message.reply_text(
        f"🔮 В ответ на твой вопрос: \n\n{prediction}\n\n"
        f"✨ Бесплатный запрос использован"
    )

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("card", card_command))
    app.add_handler(CommandHandler("balance", balance_command))
    app.add_handler(CommandHandler("buy", buy_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
