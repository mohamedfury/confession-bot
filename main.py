import telebot
import json
import time
import threading
import random

TOKEN = "7787936953:AAFPyBi4QPJWQKQB9qM3dBzQwizFYh3XjU0"
DEVELOPER_ID = 674291793  # غيره لأيديك

bot = telebot.TeleBot(TOKEN)

# --- ملفات JSON ---
def load_json(file):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_json(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

groups = load_json('groups.json')
banned = load_json('banned.json')
confession_locks = load_json('confession_locks.json')
last_time = load_json('n_time.json')
messages = load_json('messages.json')

pending = {}

# --- رسائل تحفيزية كل ساعتين ---
def send_motivations():
    for gid in groups.keys():
        try:
            msg = random.choice(messages) if messages else "اعترف الآن بصدق وأمانة"
            bot.send_message(int(gid), f"✨ {msg}")
        except:
            pass
    threading.Timer(7200, send_motivations).start()

send_motivations()

# --- أمر التفعيل من الكالك ---
@bot.callback_query_handler(func=lambda call: call.data == "تفعيل")
def activate(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    try:
        admin = bot.get_chat_member(chat_id, user_id)
        if admin.status in ['administrator', 'creator']:
            groups[str(chat_id)] = bot.get_chat(chat_id).title
            save_json('groups.json', groups)
            bot.send_message(chat_id, "✅ تم تفعيل البوت في هذه المجموعة.")
        else:
            bot.send_message(chat_id, "🚫 فقط المشرفين يمكنهم تفعيل البوت.")
    except:
        bot.send_message(chat_id, "❌ حدث خطأ أثناء التفعيل.")

# --- رسالة خاصة: اعتراف ---
@bot.message_handler(func=lambda m: m.chat.type == "private", content_types=['text', 'photo', 'voice', 'audio', 'video', 'document'])
def confession(message):
    uid = str(message.from_user.id)

    if uid in pending:
        gid = pending.pop(uid)
        if confession_locks.get(gid):
            bot.send_message(uid, "🔒 الاعترافات مغلقة في هذه المجموعة.")
            return
        return send_confession(gid, message)

    if banned.get(uid):
        return bot.send_message(uid, "🚫 أنت محظور من استخدام البوت.")

    now = time.time()
    if now - last_time.get(uid, 0) < 60:
        return bot.send_message(uid, "⏳ يجب الانتظار 60 ثانية بين كل اعتراف.")
    last_time[uid] = now
    save_json("n_time.json", last_time)

    shared = []
    for gid in groups:
        try:
            mem = bot.get_chat_member(int(gid), int(uid))
            if mem.status not in ['left', 'kicked']:
                shared.append(gid)
        except:
            continue

    if len(shared) == 0:
        return bot.send_message(uid, "❌ لا توجد مجموعات مشتركة.")

    if len(shared) == 1:
        if confession_locks.get(shared[0]):
            return bot.send_message(uid, "🔒 الاعترافات مغلقة لهذه المجموعة.")
        return send_confession(shared[0], message)

    markup = telebot.types.InlineKeyboardMarkup()
    for gid in shared:
        chat = bot.get_chat(int(gid))
        markup.add(telebot.types.InlineKeyboardButton(chat.title, callback_data=f"group_{gid}"))
    bot.send_message(uid, "📌 اختر المجموعة لإرسال الاعتراف:", reply_markup=markup)

# --- اختيار مجموعة من الزر ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("group_"))
def choose_group(call):
    user_id = str(call.from_user.id)
    group_id = call.data.split("_")[1]

    if banned.get(user_id):
        bot.answer_callback_query(call.id, "🚫 أنت محظور من استخدام البوت.")
        return

    if confession_locks.get(group_id):
        bot.answer_callback_query(call.id, "🔒 الاعترافات مغلقة في هذه المجموعة.")
        return

    pending[user_id] = group_id
    bot.answer_callback_query(call.id, "✅ تم اختيار المجموعة، أعد إرسال اعترافك.")
    bot.send_message(call.from_user.id, "📩 أرسل اعترافك الآن.")

# --- إرسال الاعتراف للمطور ---
def send_confession(group_id, message):
    try:
        caption = f"📢 اعتراف جديد في المجموعة: {groups.get(group_id, group_id)}\n" \
                  f"من: {message.from_user.first_name} (ID: {message.from_user.id})\n\n"
        if message.content_type == 'text':
            bot.send_message(DEVELOPER_ID, caption + message.text)
        elif message.content_type == 'photo':
            file_id = message.photo[-1].file_id
            bot.send_photo(DEVELOPER_ID, file_id, caption=caption + "[صورة مرفقة]")
        elif message.content_type == 'voice':
            bot.send_voice(DEVELOPER_ID, message.voice.file_id, caption=caption + "[رسالة صوتية]")
        elif message.content_type == 'audio':
            bot.send_audio(DEVELOPER_ID, message.audio.file_id, caption=caption + "[ملف صوتي]")
        elif message.content_type == 'video':
            bot.send_video(DEVELOPER_ID, message.video.file_id, caption=caption + "[فيديو مرفق]")
        elif message.content_type == 'document':
            bot.send_document(DEVELOPER_ID, message.document.file_id, caption=caption + "[ملف مرفق]")
        else:
            bot.send_message(DEVELOPER_ID, caption + "[نوع رسالة غير مدعوم]")

        bot.send_message(message.from_user.id, "✅ تم إرسال اعترافك بنجاح.")
    except Exception as e:
        bot.send_message(message.from_user.id, "❌ حدث خطأ أثناء إرسال اعترافك.")
        print("Error sending confession:", e)

# --- أوامر القفل والفتح ---
@bot.message_handler(commands=['قفل', 'فتح'])
def lock_unlock_confession(message):
    user_id = message.from_user.id
    chat_id = str(message.chat.id)

    try:
        admin = bot.get_chat_member(message.chat.id, user_id)
        if user_id != DEVELOPER_ID and admin.status not in ['administrator', 'creator']:
            bot.reply_to(message, "🚫 هذا الأمر فقط للمطور أو مدراء المجموعة.")
            return
    except:
        bot.reply_to(message, "❌ حدث خطأ أثناء التحقق.")
        return

    args = message.text.split()
    if len(args) == 1:
        bot.reply_to(message, "🔢 استخدم الأمر مع معرف المجموعة: /قفل <group_id> أو /فتح <group_id>")
        return

    group_id = args[1]

    if message.text.startswith('/قفل'):
        confession_locks[group_id] = True
        save_json('confession_locks.json', confession_locks)
        bot.reply_to(message, f"✅ تم قفل الاعترافات في المجموعة {group_id}")
    elif message.text.startswith('/فتح'):
        confession_locks[group_id] = False
        save_json('confession_locks.json', confession_locks)
        bot.reply_to(message, f"✅ تم فتح الاعترافات في المجموعة {group_id}")

# --- أوامر الحظر ورفع الحظر ---
@bot.message_handler(commands=['حظر', 'الغاء_الحظر'])
def ban_unban(message):
    user_id = message.from_user.id
    if user_id != DEVELOPER_ID:
        bot.reply_to(message, "🚫 هذا الأمر فقط للمطور.")
        return

    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "🔢 استخدم الأمر مع معرف المستخدم: /حظر <user_id> أو /الغاء_الحظر <user_id>")
        return

    target_id = args[1]

    if message.text.startswith('/حظر'):
        banned[target_id] = True
        save_json('banned.json', banned)
        bot.reply_to(message, f"✅ تم حظر المستخدم {target_id}")
    elif message.text.startswith('/الغاء_الحظر'):
        banned[target_id] = False
        save_json('banned.json', banned)
        bot.reply_to(message, f"✅ تم رفع الحظر عن المستخدم {target_id}")

print("✅ بوت الاعترافات شغال...")
bot.infinity_polling()