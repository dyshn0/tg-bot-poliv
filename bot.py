import telebot
import os
import re
from types import SimpleNamespace

TOKEN = os.getenv("BOT_TOKEN") or "8366584658:AAHnsTMoPKV7bASNcDmuKqW_1z-jpp54IZs"
ADMIN_CHAT_ID = 717909579
SAVE_PATH = "numbers.txt"
os.makedirs(os.path.dirname(SAVE_PATH) or ".", exist_ok=True)

bot = telebot.TeleBot(TOKEN)

main_kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
main_kb.add("📋 Меню", "🔄 Перезапуск")

links = {
    "🏠 Главная": "https://poliv-shop.ru/",
    "🌿 Газоны": "https://poliv-shop.ru/gazon",
    "💳 Оплата": "https://poliv-shop.ru/pay",
    "📜 Сертификаты": "https://poliv-shop.ru/sertifikat",
    "📖 О компании": "https://poliv-shop.ru/about-company",
    "☎️ Контакты": "https://poliv-shop.ru/contacts"
}
EXTRA = ["🛒 Каталог", "📲 Заказать звонок"]

catalog_sections = {
    "⚙️ Автоматизация": "https://poliv-shop.ru/autom",
    "💦 Форсунки статических дождевателей": "https://poliv-shop.ru/fors-stat-dojd",
    "🔄 Роторные дождеватели": "https://poliv-shop.ru/shop",
    "🔧 Клапаны для систем полива": "https://poliv-shop.ru/klapany",
    "💧 Капельный полив": "https://poliv-shop.ru/kap-poliv",
    "💧 Статические дождеватели": "https://poliv-shop.ru/stat-dojd",
    "🚰 Насосы и комплектующие": "https://poliv-shop.ru/nasos",
    "🔩 Комплектующие": "https://poliv-shop.ru/accessories",
    "🔗 Трубы ПНД": "https://poliv-shop.ru/trub-pnd",
    "🛢️ Емкости": "https://poliv-shop.ru/emkost",
    "📦 Клапанные боксы": "https://poliv-shop.ru/klap-box"
}

user_states = {}
user_temp = {}

@bot.message_handler(commands=['start'])
def cmd_start(msg):
    bot.send_message(
        msg.chat.id,
        "👋 *Добро пожаловать в бот Полив-Шоп!*\nНажмите на кнопку Меню, чтобы начать.",
        parse_mode="Markdown",
        reply_markup=main_kb
    )

@bot.message_handler(func=lambda m: m.text in ["📋 Меню", "🔙 Меню"])
def show_main(msg):
    kb = telebot.types.InlineKeyboardMarkup(row_width=2)
    for label, url in links.items():
        kb.add(telebot.types.InlineKeyboardButton(label, url=url))
    kb.add(
        telebot.types.InlineKeyboardButton(EXTRA[0], callback_data="main:catalog"),
        telebot.types.InlineKeyboardButton(EXTRA[1], callback_data="main:call")
    )
    bot.send_message(
        msg.chat.id,
        "*Выберите раздел:*",
        parse_mode="Markdown",
        reply_markup=kb
    )

@bot.message_handler(func=lambda m: m.text == "🔄 Перезапуск")
def cmd_restart(msg):
    cmd_start(msg)

@bot.callback_query_handler(func=lambda c: True)
def on_callback(c):
    data = c.data
    cid = c.message.chat.id

    if data == "main:catalog":
        kb = telebot.types.InlineKeyboardMarkup(row_width=1)
        for label, url in catalog_sections.items():
            kb.add(telebot.types.InlineKeyboardButton(label, url=url))
        kb.add(telebot.types.InlineKeyboardButton("🔙 Меню", callback_data="main:back"))
        bot.send_message(
            cid,
            "*Каталог разделов:*",
            parse_mode="Markdown",
            reply_markup=kb
        )
        return

    if data == "main:call":
        user_states[cid] = "await_name"
        kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        kb.add("🔙 Меню")
        bot.send_message(cid, "📋 Введите ваше имя:", reply_markup=kb)
        return

    if data == "main:back":
        show_main(c.message)
        return

@bot.message_handler(func=lambda m: True)
def on_text(msg):
    cid = msg.chat.id
    txt = msg.text.strip()
    state = user_states.get(cid, "")

    if txt in ["📋 Меню", "🔙 Меню"]:
        user_states.pop(cid, None)
        show_main(msg)
        return
    if txt == "🔄 Перезапуск":
        cmd_start(msg)
        return

    if state == "await_name":
        user_temp[cid] = {"name": txt}
        user_states[cid] = "await_phone"
        kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        kb.add("🔙 Меню")
        bot.send_message(cid, "📞 Теперь введите телефон (+7XXXXXXXXXX):", reply_markup=kb)
        return

    if state == "await_phone":
        if txt in ["📋 Меню", "🔙 Меню"]:
            user_states.pop(cid, None)
            show_main(msg)
            return
        if not re.match(r'^\+7\d{10}$', txt):
            kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            kb.add("🔙 Меню")
            bot.send_message(cid, "❗ Неверный формат. Используйте +7XXXXXXXXXX", reply_markup=kb)
            return
        existing = []
        if os.path.exists(SAVE_PATH):
            with open(SAVE_PATH, "r", encoding="utf-8") as f:
                existing = [line.split(" - ")[0] for line in f if " - " in line]
        if txt in existing:
            bot.send_message(cid,
                             "⚠️ Этот номер уже есть в нашей базе. Попробуйте другой.",
                             reply_markup=main_kb)
            return
        name = user_temp[cid]["name"]
        with open(SAVE_PATH, "a", encoding="utf-8") as f:
            f.write(f"{txt} - {name}\n")
        bot.send_message(ADMIN_CHAT_ID, f"🆕 Заявка: {name}, {txt}")
        bot.send_message(cid, "✅ Спасибо! Мы скоро свяжемся.", reply_markup=main_kb)
        user_states.pop(cid, None)
        user_temp.pop(cid, None)
        return

    bot.send_message(cid, "👉 Нажмите 📋 Меню", reply_markup=main_kb)

if __name__ == "__main__":
    bot.polling()
