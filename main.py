import telebot
import json
import time
import threading
import random

TOKEN = "7787936953:AAFPyBi4QPJWQKQB9qM3dBzQwizFYh3XjU0"  # استبدله بتوكنك الصحيح
DEVELOPER_ID = 674291793     # ID مال المطور (استبدله إذا لازم)

bot = telebot.TeleBot(TOKEN)

# --- تحميل البيانات ---
def load_json(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

groups = load_json('groups.json')
banned = load_json('banned.json')
confession_locks = load_json('confession_locks.json')
last_confession_time = load_json('last_confession_time.json')
messages = load_json('messages.json')

pending_selections = {}

START_MSG = "أهلاً بك في بوت الاعترافات. أرسل اعترافك هنا."

# --- وظائف ---
def is_banned(user_id):
    return str(user_id) in banned and banned[str(user_id)] == True

def is_confession_locked(group_id):
    return str(group_id) in confession_locks and confession_locks[str(group_id)] == True

def can_send_confession(user_id):
    now = time.time()
    last = last_confession_time.get(str(user_id), 0)
    if now - last >= 60:
        last_confession_time[str(user_id)] = now
        save_json('last_confession_time.json', last_confession_time)
        return True
    return False

def get_random_message():
    return random.choice(messages) if messages else "اعترف الآن بسر دفين… 😌"

# --- /start ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.type == 'private':
        bot.send_message(message.chat.id, START_MSG)

# --- انضمام البوت كمشرف للمجموعة ---
@bot.message_handler(func=lambda m: m.chat.type != 'private' and m.new_chat_members)
def bot_added(message):
    for member in message.new_chat_members:
        if member.id == bot.get_me().id:
            chat_member = bot.get_chat_member(message.chat.id, bot.get_me().id)
            if chat_member.status in ['administrator', 'creator']:
                groups[str(message.chat.id)] = message.chat.title
                save_json('groups.json', groups)
                bot.send_message(message.chat.id, "✅ تم تفعيل البوت بنجاح.")
            else:
                bot.send_message(message.chat.id, "⚠️ يجب تعيين البوت كمشرف.")

# --- استقبال الاعترافات ---
@bot.message_handler(func=lambda m: m.chat.type == 'private', content_types=['text', 'photo', 'audio', 'voice', 'video', 'document'])
def handle_confession(message):
    user_id = message.from_user.id

    if is_banned(user_id):
        bot.send_message(user_id, "🚫 أنت محظور.")
        return

    if not can_send_confession(user_id):
        bot.send_message(user_id, "⏳ يمكنك إرسال اعتراف جديد بعد 60 ثانية.")
        return

    user_groups = []
    for gid in groups:
        try:
            member = bot.get_chat_member(int(gid), user_id)
            if member.status not in ['left', 'kicked']:
                user_groups.append(gid)
        except:
            pass

    if len(user_groups) == 0:
        bot.send_message(user_id, "❌ لا توجد مجموعات مشتركة.")
    elif len(user_groups) == 1:
        group_id = user_groups[0]
        if is_confession_locked(group_id):
            bot.send_message(user_id, "🔒 هذه المجموعة مغلقة للاعترافات.")
            return
        forward_to_owner(group_id, message)
    else:
        markup = telebot.types.InlineKeyboardMarkup()
        for gid in user_groups:
            try:
                title = bot.get_chat(int(gid)).title
                markup.add(telebot.types.InlineKeyboardButton(title, callback_data=f"choose_{gid}"))
            except:
                pass
        pending_selections[user_id] = message
        bot.send_message(user_id, "📌 اختر المجموعة التي تريد الإرسال إليها:", reply_markup=markup)

# --- اختيار المجموعة ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("choose_"))
def choose_group(call):
    user_id = call.from_user.id
    group_id = call.data.split("_")[1]

    if is_confession_locked(group_id):
        bot.answer_callback_query(call.id, "🔒 هذه المجموعة مغلقة.")
        return

    if user_id in pending_selections:
        msg = pending_selections.pop(user_id)
        forward_to_owner(group_id, msg)
        bot.send_message(user_id, "✅ تم إرسال اعترافك.")

# --- إرسال الاعتراف للمالك فقط ---
def forward_to_owner(group_id, message):
    try:
        caption = f"📨 اعتراف جديد من مجموعة {groups.get(group_id, group_id)}:"
        if message.content_type == 'text':
            bot.send_message(DEVELOPER_ID, f"{caption}\n\n{message.text}")
        elif message.content_type == 'photo':
            bot.send_photo(DEVELOPER_ID, message.photo[-1].file_id, caption=caption)
        elif message.content_type == 'voice':
            bot.send_voice(DEVELOPER_ID, message.voice.file_id, caption=caption)
        elif message.content_type == 'audio':
            bot.send_audio(DEVELOPER_ID, message.audio.file_id, caption=caption)
        elif message.content_type == 'video':
            bot.send_video(DEVELOPER_ID, message.video.file_id, caption=caption)
        elif message.content_type == 'document':
            bot.send_document(DEVELOPER_ID, message.document.file_id, caption=caption)
        else:
            bot.send_message(DEVELOPER_ID, f"{caption}\n\n[مرفق غير مدعوم]")
    except Exception as e:
        print("❌ خطأ أثناء الإرسال:", e)

# --- أوامر القفل والفتح ---
@bot.message_handler(commands=['قفل', 'فتح'])
def lock_unlock(message):
    user_id = message.from_user.id
    if user_id != DEVELOPER_ID:
        bot.reply_to(message, "❌ فقط المطور يملك صلاحية تنفيذ هذا الأمر.")
        return
    try:
        group_id = str(message.text.split()[1])
        if message.text.startswith('/قفل'):
            confession_locks[group_id] = True
            msg = "🔒 تم قفل الاعترافات في هذه المجموعة."
        else:
            confession_locks[group_id] = False
            msg = "🔓 تم فتح الاعترافات."
        save_json('confession_locks.json', confession_locks)
        bot.reply_to(message, msg)
    except:
        bot.reply_to(message, "❗ استخدم الأمر بهذا الشكل: /قفل <ID>")

# --- حظر / رفع حظر ---
@bot.message_handler(commands=['حظر', 'الغاء_الحظر'])
def manage_ban(message):
    if message.from_user.id != DEVELOPER_ID:
        bot.reply_to(message, "🚫 فقط المطور يستطيع تنفيذ هذا.")
        return
    try:
        user_id = message.text.split()[1]
        if message.text.startswith('/حظر'):
            banned[user_id] = True
            msg = "🚫 تم حظر المستخدم."
        else:
            banned[user_id] = False
            msg = "✅ تم رفع الحظر."
        save_json('banned.json', banned)
        bot.reply_to(message, msg)
    except:
        bot.reply_to(message, "❗ استخدم الأمر بهذا الشكل: /حظر <user_id>")

# --- إذاعة ---
@bot.message_handler(commands=['اذاعة'])
def broadcast(message):
    if message.from_user.id != DEVELOPER_ID:
        return
    try:
        text = message.text.split(maxsplit=1)[1]
        for gid in groups:
            try:
                bot.send_message(int(gid), f"📢 {text}")
            except:
                pass
        bot.reply_to(message, "✅ تمت الإذاعة بنجاح.")
    except:
        bot.reply_to(message, "❗ اكتب النص بعد الأمر: /اذاعة <النص>")

# --- رسائل تحفيزية ---
def send_motivation():
    for gid in groups:
        try:
            msg = get_random_message()
            bot.send_message(int(gid), f"💌 {msg}")
        except:
            pass
    threading.Timer(7200, send_motivation).start()

send_motivation()

print("✅ البوت شغال الآن...")
bot.infinity_polling()