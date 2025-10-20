import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import openai
from datetime import date

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Настройки
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Храним последние бесплатные запросы (временное решение)
user_last_free_date = {}

# Настройка OpenAI
client = openai.OpenAI(api_key=OPENAI_API_KEY)

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

💫 Команды:
/card - получить карту дня
/balance - проверить баланс
/buy - купить дополнительные запросы

Просто напиши свой вопрос!
    """
    await update.message.reply_text(text)

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает статус запросов"""
    user_id = update.effective_user.id
    
    if can_use_free(user_id):
        status = "✅ У тебя есть бесплатный запрос на сегодня!"
    else:
        status = "❌ Бесплатный запрос на сегодня использован"
    
    await update.message.reply_text(status)

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для покупки запросов"""
    text = """
💳 **Покупка дополнительных запросов**

🎯 Тарифы:
• 5 запросов - 200 рублей

📨 Для оплаты напишите @ваш_логин
    """
    await update.message.reply_text(text)

async def get_ai_prediction(user_question=None):
    """Получить предсказание от ИИ"""
    try:
        if user_question is None:
            prompt = "Вытащи случайную карту Таро и дай краткое предсказание на сегодня (2 предложения)"
        else:
            prompt = f"Как таролог, ответь на вопрос: {user_question} (2-3 предложения, мистически)"
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты мудрый таролог. Отвечай кратко и мистически."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return "Карты пока молчат... Попробуйте позже."

async def card_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выдает карту дня"""
    user_id = update.effective_user.id
    
    if not can_use_free(user_id):
        await update.message.reply_text("❌ Бесплатный запрос использован. Используй /buy")
        return
    
    await update.message.chat.send_action(action="typing")
    prediction = await get_ai_prediction()
    await update.message.reply_text(f"🃏 Карта дня:\n\n{prediction}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает сообщения"""
    user_message = update.message.text
    user_id = update.effective_user.id
    
    if user_message.startswith('/'):
        return
    
    if not can_use_free(user_id):
        await update.message.reply_text("❌ Бесплатный запрос использован. Используй /buy")
        return
    
    await update.message.chat.send_action(action="typing")
    prediction = await get_ai_prediction(user_message)
    await update.message.reply_text(f"🔮 {prediction}")

def main():
    """Запуск бота"""
    try:
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("card", card_command))
        application.add_handler(CommandHandler("balance", balance_command))
        application.add_handler(CommandHandler("buy", buy_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Запускаем бота
        logger.info("Бот запускается...")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Ошибка запуска: {e}")

if __name__ == '__main__':
    main()
