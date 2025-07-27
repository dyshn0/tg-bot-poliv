import telebot
import os
import re
from types import SimpleNamespace

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = 717909579

bot = telebot.TeleBot(TOKEN)

products = {
    "Hunter ProS-04": {
        "url": "https://poliv-shop.ru/shop/pros-04",
        "price": "419₽",
        "image": "https://poliv-shop.ru/media/pros-04.jpg"
    },
    "Клапан PGV-101": {
        "url": "https://poliv-shop.ru/klapany/pgv-101",
        "price": "3700₽",
        "image": "https://poliv-shop.ru/media/pgv-101.jpg"
    },
    "Ёмкость ATV-3000": {
        "url": "https://poliv-shop.ru/emkost/atv-3000",
        "price": "42400₽",
        "image": "https://poliv-shop.ru/media/atv-3000.jpg"
    }
}

SAVE_PATH = "Z:/tg_bot_poliv/numbers.txt"
os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)

user_states = {}
user_temp_data = {}

start_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
start_markup.add("📋 Меню", "🔄 Перезапуск")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = (
        "👋 *Привет!* Я бот магазина Полив-Шоп. Нажми кнопку ниже, чтобы открыть меню."
    )
    bot.send_message(
        message.chat.id,
        text,
        parse_mode="Markdown",
        reply_markup=start_markup
    )

@bot.message_handler(func=lambda m: m.text == "📋 Меню")
def send_menu(message):
    chat_id = message.chat.id
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🛒 Каталог товаров", callback_data="catalog"))
    markup.add(telebot.types.InlineKeyboardButton("🔍 Поиск товара", callback_data="search"))
    markup.add(telebot.types.InlineKeyboardButton("📞 Заказать звонок", callback_data="call_request"))
    bot.send_message(
        chat_id,
        "*Главное меню*",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text == "🔄 Перезапуск")
def handle_restart(message):
    send_welcome(message)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    data = call.data
    chat_id = call.message.chat.id

    if data == "catalog":
        for name, info in products.items():
            caption = f"*{name}*\nЦена: {info['price']}"
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("Перейти на сайт", url=info['url']))
            bot.send_photo(chat_id, info['image'], caption=caption, parse_mode="Markdown", reply_markup=markup)
        bot.send_message(chat_id, "Чтобы вернуться, нажми /start", reply_markup=start_markup)

    elif data == "search":
        user_states[chat_id] = 'awaiting_search'
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("🔙 Назад")
        bot.send_message(chat_id, "Введите слово для поиска товара:", reply_markup=markup)

    elif data == "call_request":
        user_states[chat_id] = "awaiting_name"
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("🔙 Назад")
        bot.send_message(chat_id, "Введите ваше имя:", reply_markup=markup)

def cancel_and_back(chat_id):
    user_states.pop(chat_id, None)
    user_temp_data.pop(chat_id, None)
    fake = SimpleNamespace(chat=SimpleNamespace(id=chat_id))
    send_menu(fake)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id
    text = message.text.strip()

    if text in ["📋 Меню", "/start"]:
        send_menu(message)
        return
    if text == "🔄 Перезапуск":
        send_welcome(message)
        return
    if text == "🔙 Назад":
        cancel_and_back(chat_id)
        return

    state = user_states.get(chat_id)

    if state == 'awaiting_search':
        query = text.lower()
        results = {n: inf for n, inf in products.items() if query in n.lower()}
        if not results:
            bot.send_message(chat_id, "🔍 Ничего не найдено. Попробуйте ещё раз.")
            return
        for name, info in results.items():
            caption = f"*{name}*\nЦена: {info['price']}"
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("Перейти на сайт", url=info['url']))
            bot.send_photo(chat_id, info['image'], caption=caption, parse_mode="Markdown", reply_markup=markup)
        bot.send_message(chat_id, "🔍 Поиск завершён.", reply_markup=start_markup)
        user_states.pop(chat_id, None)
        return

    if state == "awaiting_name":
        user_temp_data[chat_id] = {"name": text}
        user_states[chat_id] = "awaiting_phone"
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("🔙 Назад")
        bot.send_message(
            chat_id,
            "Введите номер телефона для обратной связи (только в формате +7XXXXXXXXXX):",
            reply_markup=markup
        )
        return

    if state == "awaiting_phone":
        if not re.match(r'^\+7\d{10}$', text):
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add("🔙 Назад")
            bot.send_message(
                chat_id,
                "❗ Пожалуйста, введите номер только в формате +7XXXXXXXXXX",
                reply_markup=markup
            )
            return

        phone = text
        existing = ""
        if os.path.exists(SAVE_PATH):
            with open(SAVE_PATH, "r", encoding="utf-8") as f:
                existing = f.read()
        if phone in existing:
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add("🔙 Назад")
            bot.send_message(
                chat_id,
                "⚠️ Этот номер уже был отправлен. Пожалуйста, используйте другой.",
                reply_markup=markup
            )
            return

        name = user_temp_data[chat_id]["name"]
        with open(SAVE_PATH, "a", encoding="utf-8") as f:
            f.write(f"{phone} - {name}\n")

        bot.send_message(
            ADMIN_CHAT_ID,
            f"🆕 Новая заявка:\nИмя: {name}\nТелефон: {phone}"
        )

        bot.send_message(
            chat_id,
            "✅ Спасибо! Мы скоро с вами свяжемся.",
            reply_markup=start_markup
        )

        user_states.pop(chat_id, None)
        user_temp_data.pop(chat_id, None)
        return

    bot.send_message(chat_id, "Не понял. Нажми 📋 Меню", reply_markup=start_markup)

bot.polling()
