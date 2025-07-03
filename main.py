import telebot

API_TOKEN = "7787936953:AAHI6UWGZeddq76Dny5FNFtqTgXm5OFvSpA"
GROUP_CHAT_ID = -1001201718722  # رقم الكروب
ADMIN_ID = 674291793  # إيديك

bot = telebot.TeleBot(API_TOKEN)

confessions_open = False
pending_confession = None

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "أهلاً! أرسل لي اعترافك سرا وأنا راح أبلّغ المسؤول.")

@bot.message_handler(func=lambda m: m.chat.id == GROUP_CHAT_ID)
def handle_group(message):
    global confessions_open
    text = message.text.lower()
    if message.from_user.id != ADMIN_ID:
        return  # فقط للمطور

    if text == "فتح الاعترافات":
        confessions_open = True
        bot.reply_to(message, "تم فتح الاعترافات.")
    elif text == "ايقاف الاعترافات":
        confessions_open = False
        bot.reply_to(message, "تم إيقاف الاعترافات.")

@bot.message_handler(func=lambda m: m.chat.type == 'private')
def handle_private(message):
    global confessions_open, pending_confession
    if not confessions_open:
        bot.reply_to(message, "الاعترافات مغلقة حالياً.")
        return

    # سجل الاعتراف مؤقتًا
    pending_confession = {
        "user_id": message.from_user.id,
        "username": message.from_user.username or "غير معروف",
        "text": message.text
    }
    # أرسل للمطور خيارات نشر أو حذف
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("نشر", callback_data="publish"),
        telebot.types.InlineKeyboardButton("حذف", callback_data="delete")
    )
    bot.send_message(ADMIN_ID,
        f"اعتراف جديد من @{pending_confession['username']}:\n\n{pending_confession['text']}",
        reply_markup=markup
    )
    bot.reply_to(message, "تم استلام اعترافك وسيراجعه المسؤول.")

@bot.callback_query_handler(func=lambda call: call.from_user.id == ADMIN_ID)
def callback_handler(call):
    global pending_confession, confessions_open
    if call.data == "publish" and pending_confession:
        bot.send_message(GROUP_CHAT_ID, f"اعتراف مجهول:\n\n{pending_confession['text']}")
        bot.answer_callback_query(call.id, "تم نشر الاعتراف.")
        pending_confession = None
    elif call.data == "delete" and pending_confession:
        bot.answer_callback_query(call.id, "تم حذف الاعتراف.")
        pending_confession = None

bot.infinity_polling()
