import telebot

API_TOKEN = "7787936953:AAHN8i_5q3u0RVuEaHDvKi7TqhyUmtxbuMc"
GROUP_CHAT_ID = -1001201718722  # رقم الكروب
ADMIN_ID = 674291793  # إيديك

bot = telebot.TeleBot(API_TOKEN)

confessions_open = False
pending_confessions = {}  # يخزن الاعترافات مع معرفها

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "أهلاً! أرسل لي اعترافك سرا وأنا راح أبلّغ المسؤول.")

@bot.message_handler(func=lambda m: m.chat.id == GROUP_CHAT_ID)
def handle_group(message):
    global confessions_open
    if message.from_user.id != ADMIN_ID:
        return
    text = message.text.lower()
    if text == "فتح الاعترافات":
        confessions_open = True
        bot.reply_to(message, "تم فتح الاعترافات.")
    elif text == "ايقاف الاعترافات":
        confessions_open = False
        bot.reply_to(message, "تم إيقاف الاعترافات.")

@bot.message_handler(func=lambda m: m.chat.type == 'private')
def handle_private(message):
    global confessions_open, pending_confessions
    if not confessions_open:
        bot.reply_to(message, "الاعترافات مغلقة حالياً.")
        return

    confession_id = message.message_id  # مفتاح فريد لكل اعتراف
    pending_confessions[confession_id] = {
        "text": message.text
    }

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("نشر", callback_data=f"publish_{confession_id}"),
        telebot.types.InlineKeyboardButton("حذف", callback_data=f"delete_{confession_id}")
    )

    bot.send_message(ADMIN_ID,
                     f"اعتراف جديد:\n\n{message.text}",
                     reply_markup=markup)
    bot.reply_to(message, "تم استلام اعترافك وسيراجعه المسؤول.")

@bot.callback_query_handler(func=lambda call: call.from_user.id == ADMIN_ID)
def callback_handler(call):
    global
