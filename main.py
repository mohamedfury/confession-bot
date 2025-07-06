import telebot
import json
import time
import threading
import random

TOKEN = "7787936953:AAFPyBi4QPJWQKQB9qM3dBzQwizFYh3XjU0"
DEVELOPER_ID = 674291793  # عدلها على إيديك

bot = telebot.TeleBot(TOKEN)

GROUPS_FILE = "groups.json"
BANNED_FILE = "banned.json"
LOCKS_FILE = "confession_locks.json"
LAST_CONF_FILE = "last_confession_time.json"
MESSAGES_FILE = "messages.json"

def load_json(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return {}

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

groups = load_json(GROUPS_FILE)
banned_users = load_json(BANNED_FILE)
locks = load_json(LOCKS_FILE)
last_conf = load_json(LAST_CONF_FILE)
messages = load_json(MESSAGES_FILE)

def can_send_confession(user_id):
    now = time.time()
    if str(user_id) in last_conf:
        elapsed = now - last_conf[str(user_id)]
        if elapsed < 60:
            return False, 60 - int(elapsed)
    last_conf[str(user_id)] = now
    save_json(LAST_CONF_FILE, last_conf)
    return True, 0

def is_owner(user_id, chat_id):
    try:
        admins = bot.get_chat_administrators(chat_id)
        for admin in admins:
            if admin.status == 'creator' and admin.user.id == user_id:
                return True
    except:
        return False
    return False

def is_admin(user_id, chat_id):
    try:
        admins = bot.get_chat_administrators(chat_id)
        for admin in admins:
            if admin.user.id == user_id:
                return True
    except:
        return False
    return False

def send_confession_to_owner(chat_id, confession, sender):
    # تأكد إذا القفل مفتوح
    if locks.get(str(chat_id), False):
        return False

    # نرسل رسالة للمؤسس مع زر للموافقة
    markup = telebot.types.InlineKeyboardMarkup()
    approve_btn = telebot.types.InlineKeyboardButton("✅ قبول الاعتراف", callback_data=f"approve_{chat_id}_{sender.id}")
    markup.add(approve_btn)

    owner_id = None
    admins = bot.get_chat_administrators(chat_id)
    for admin in admins:
        if admin.status == 'creator':
            owner_id = admin.user.id
            break
    if owner_id is None:
        return False

    text = f"📢 اعتراف جديد من مجهول في المجموعة:\n\n{confession}"

    bot.send_message(owner_id, text, reply_markup=markup)
    return True

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
def callback_approve(call):
    data = call.data.split("_")
    if len(data) != 3:
        return
    chat_id = int(data[1])
    sender_id = int(data[2])

    if call.from_user.id != sender_id and not is_owner(call.from_user.id, chat_id):
        bot.answer_callback_query(call.id, "أنت غير مخول للموافقة.")
        return

    # إرسال الاعتراف للمجموعة
    text = f"💬 اعتراف مجهول:\n\n{call.message.text.split('\\n\n',1)[1]}"
    bot.send_message(chat_id, text)

    bot.answer_callback_query(call.id, "تم نشر الاعتراف.")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً! أرسل لي اعترافك وأنا أديرها مع مالك المجموعة.")

@bot.message_handler(commands=['lock'])
def lock_confession(message):
    if message.chat.type not in ['group', 'supergroup']:
        bot.reply_to(message, "هذا الأمر فقط في المجموعات.")
        return
    if not is_owner(message.from_user.id, message.chat.id):
        bot.reply_to(message, "أنت مو مالك الكروب.")
        return
    locks[str(message.chat.id)] = True
    save_json(LOCKS_FILE, locks)
    bot.reply_to(message, "تم قفل الاعترافات في المجموعة.")

@bot.message_handler(commands=['unlock'])
def unlock_confession(message):
    if message.chat.type not in ['group', 'supergroup']:
        bot.reply_to(message, "هذا الأمر فقط في المجموعات.")
        return
    if not is_owner(message.from_user.id, message.chat.id):
        bot.reply_to(message, "أنت مو مالك الكروب.")
        return
    locks[str(message.chat.id)] = False
    save_json(LOCKS_FILE, locks)
    bot.reply_to(message, "تم فتح الاعترافات في المجموعة.")

@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.chat.type not in ['group', 'supergroup']:
        bot.reply_to(message, "هذا الأمر فقط في المجموعات.")
        return
    if not is_owner(message.from_user.id, message.chat.id):
        bot.reply_to(message, "أنت مو مالك الكروب.")
        return
    if not message.reply_to_message:
        bot.reply_to(message, "قم بالرد على رسالة العضو اللي تريد تحظره.")
        return
    user_id = message.reply_to_message.from_user.id
    banned_users[str(user_id)] = True
    save_json(BANNED_FILE, banned_users)
    bot.reply_to(message, f"تم حظر العضو بنجاح.")

@bot.message_handler(commands=['unban'])
def unban_user(message):
    if message.chat.type not in ['group', 'supergroup']:
        bot.reply_to(message, "هذا الأمر فقط في المجموعات.")
        return
    if not is_owner(message.from_user.id, message.chat.id):
        bot.reply_to(message, "أنت مو مالك الكروب.")
        return
    if not message.reply_to_message:
        bot.reply_to(message, "قم بالرد على رسالة العضو اللي تريد ترفع عنه الحظر.")
        return
    user_id = message.reply_to_message.from_user.id
    if str(user_id) in banned_users:
        del banned_users[str(user_id)]
        save_json(BANNED_FILE, banned_users)
        bot.reply_to(message, "تم رفع الحظر عنه.")
    else:
        bot.reply_to(message, "هذا العضو غير محظور.")

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    if message.from_user.id != DEVELOPER_ID:
        bot.reply_to(message, "هذا الأمر خاص بالمطور فقط.")
        return
    text = message.text[10:]
    for group_id in groups.keys():
        try:
            bot.send_message(int(group_id), text)
        except:
            pass
    bot.reply_to(message, "تم إرسال الرسالة لجميع المجموعات.")

@bot.message_handler(func=lambda m: True)
def handle_confession(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if str(user_id) in banned_users:
        bot.reply_to(message, "أنت محظور من استخدام البوت.")
        return

    if message.chat.type == 'private':
        # تحقق وقت الإرسال
        can_send, wait_time = can_send_confession(user_id)
        if not can_send:
            bot.reply_to(message, f"⏳ انتظر {wait_time} ثانية قبل إرسال اعتراف جديد.")
            return

        # تحقق من الاشتراك في مجموعات البوت
        user_chats = []
        for g_id in groups.keys():
            try:
                member = bot.get_chat_member(int(g_id), user_id)
                if member.status in ['member', 'administrator', 'creator']:
                    user_chats.append(int(g_id))
            except:
                continue

        if len(user_chats) == 0:
            bot.reply_to(message, "✖️ أنت لست مشترك بأي من مجموعاتنا.")
            return
        elif len(user_chats) == 1:
            send_confession_to_owner(user_chats[0], message.text, message.from_user)
            bot.reply_to(message, "تم إرسال اعترافك وسيتم مراجعته من قبل مالك المجموعة.")
        else:
            markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            for gid in user_chats:
                markup.add(telebot.types.KeyboardButton(f"مجوعة: {gid}"))
            msg = bot.reply_to(message, "اختر المجموعة التي تريد إرسال الاعتراف إليها:", reply_markup=markup)

            bot.register_next_step_handler(msg, lambda m: handle_group_choice(m, message))

def handle_group_choice(msg, original_message):
    selected_text = msg.text
    group_id = None
    if selected_text.startswith("مجوعة: "):
        group_id = selected_text.split(" ")[1]
    else:
        bot.reply_to(msg, "اختيار غير صالح.")
        return
    send_confession_to_owner(int(group_id), original_message.text, original_message)
    bot.reply_to(msg, "تم إرسال اعترافك وسيتم مراجعته من قبل مالك المجموعة.")

def auto_send_messages():
    for group_id in groups.keys():
        if locks.get(group_id, False):
            continue
        try:
            msg = random.choice(messages)
            bot.send_message(int(group_id), f"🔔 رسالة تحفيزية:\n{msg}")
        except:
            continue
    threading.Timer(7200, auto_send_messages).start()  # كل ساعتين

auto_send_messages()

print("بوت الاعترافات شغال...")

bot.polling()