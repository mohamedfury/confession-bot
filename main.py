import telebot
import json
import time
import threading
import random

TOKEN = "7787936953:AAFPyBi4QPJWQKQB9qM3dBzQwizFYh3XjU0"
DEVELOPER_ID = 123456789  # حط ايديك هنا

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

# --- متغيرات إضافية ---
pending_selections = {}  # تخزين اختيار المجموعة مؤقتًا

START_MSG = "أهلاً بك في بوت الاعترافات. أرسل اعترافك هنا."

# --- وظائف التحقق ---
def is_banned(user_id):
    return str(user_id) in banned and banned[str(user_id)] == True

def is_confession_locked(group_id):
    return str(group_id) in confession_locks and confession_locks[str(group_id)] == True

def can_send_confession(user_id):
    now = time.time()
    last = last_confession_time.get(str(user_id), 0)
    if now - last >= 60:  # 60 ثانية بين كل اعتراف
        last_confession_time[str(user_id)] = now
        save_json('last_confession_time.json', last_confession_time)
        return True
    else:
        return False

def get_random_message():
    if messages:
        return random.choice(messages)
    else:
        return "اعترف الآن بصدق وأمانة"

# --- أوامر البوت ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.type == 'private':
        bot.send_message(message.chat.id, START_MSG)

# --- تسجيل المجموعات عند انضمام البوت كمشرف ---
@bot.message_handler(func=lambda m: m.chat.type != 'private' and m.new_chat_members)
def check_bot_added_as_admin(message):
    for member in message.new_chat_members:
        if member.id == bot.get_me().id:
            try:
                chat_member = bot.get_chat_member(message.chat.id, bot.get_me().id)
                if chat_member.status not in ['administrator', 'creator']:
                    bot.send_message(message.chat.id, "⚠️ يجب أن أكون مشرفًا في المجموعة لأتمكن من العمل.")
                    return
                group_id = str(message.chat.id)
                groups[group_id] = message.chat.title
                save_json('groups.json', groups)
                bot.send_message(message.chat.id, "✅ تم إضافة البوت بنجاح كمشرف!")
            except:
                pass

# --- معالجة الاعترافات ---
@bot.message_handler(func=lambda m: m.chat.type == 'private', content_types=['text', 'photo', 'audio', 'voice', 'video', 'document'])
def handle_confession(message):
    user_id = message.from_user.id

    if user_id in pending_selections:
        group_id = pending_selections.pop(user_id)
        send_confession_to_owner(group_id, message)
        return

    if is_banned(user_id):
        bot.send_message(user_id, "🚫 أنت محظور من استخدام البوت.")
        return

    if not can_send_confession(user_id):
        bot.send_message(user_id, "⏳ يرجى الانتظار 60 ثانية بين كل اعتراف.")
        return

    user_groups = []
    for gid in groups.keys():
        try:
            member = bot.get_chat_member(int(gid), user_id)
            if member.status not in ['left', 'kicked']:
                user_groups.append(gid)
        except:
            pass

    if len(user_groups) == 0:
        bot.send_message(user_id, "❌ لا توجد لديك مجموعات مشتركة لإرسال اعتراف.")
        return
    elif len(user_groups) == 1:
        group_id = user_groups[0]
        if is_confession_locked(group_id):
            bot.send_message(user_id, "🔒 تم إغلاق استقبال الاعترافات في هذه المجموعة.")
            return
        send_confession_to_owner(group_id, message)
    else:
        markup = telebot.types.InlineKeyboardMarkup()
        for gid in user_groups:
            try:
                chat = bot.get_chat(int(gid))
                btn = telebot.types.InlineKeyboardButton(chat.title, callback_data=f"select_group_{gid}")
                markup.add(btn)
            except:
                pass
        bot.send_message(user_id, "📌 اختر المجموعة التي تريد إرسال الاعتراف لها:", reply_markup=markup)

# --- اختيار المجموعة عبر الزر ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("select_group_"))
def callback_select_group(call):
    user_id = call.from_user.id
    group_id = call.data.split("_")[-1]

    if is_banned(user_id):
        bot.answer_callback_query(call.id, "🚫 أنت محظور من استخدام البوت.")
        return

    if is_confession_locked(group_id):
        bot.answer_callback_query(call.id, "🔒 المجموعة مغلقة أمام الاعترافات.")
        return

    pending_selections[user_id] = group_id
    bot.answer_callback_query(call.id, "✅ تم اختيار المجموعة، الرجاء إعادة إرسال اعترافك.")
    bot.send_message(user_id, "📩 الرجاء إعادة إرسال اعترافك الآن.")

# --- إرسال الاعتراف للمالك ---
def send_confession_to_owner(group_id, message):
    group_owner_id = DEVELOPER_ID

    try:
        caption = f"📢 اعتراف جديد في المجموعة: {group_id}\n\n" \
                  f"من: {message.from_user.first_name} (ID: {message.from_user.id})\n\n"

        if message.content_type == 'text':
            bot.send_message(group_owner_id, caption + message.text)
        elif message.content_type == 'photo':
            file_id = message.photo[-1].file_id
            bot.send_photo(group_owner_id, file_id, caption=caption + "[صورة مرفقة]")
        elif message.content_type == 'voice':
            bot.send_voice(group_owner_id, message.voice.file_id, caption=caption + "[رسالة صوتية]")
        elif message.content_type == 'video':
            bot.send_video(group_owner_id, message.video.file_id, caption=caption + "[فيديو مرفق]")
        elif message.content_type == 'audio':
            bot.send_audio(group_owner_id, message.audio.file_id, caption=caption + "[ملف صوتي]")
        elif message.content_type == 'document':
            bot.send_document(group_owner_id, message.document.file_id, caption=caption + "[ملف مرفق]")
        else:
            bot.send_message(group_owner_id, caption + "[نوع رسالة غير مدعوم]")

        bot.send_message(message.from_user.id, "✅ تم إرسال اعترافك بنجاح.")
    except Exception as e:
        bot.send_message(message.from_user.id, "❌ حدث خطأ أثناء إرسال اعترافك.")
        print("Error sending confession:", e)

# --- أوامر باللغة العربية ---
# --- قفل/فتح الاعترافات ---
@bot.message_handler(commands=['قفل', 'فتح'])
def lock_unlock_confession(message):
    user_id = message.from_user.id
    if user_id != DEVELOPER_ID and message.from_user.id not in [int(x) for x in groups.keys() if groups[x] in [bot.get_chat_member(int(x), user_id).status in ['administrator', 'creator']]]:
        bot.reply_to(message, "🚫 هذا الأمر فقط للمطور أو مدراء المجموعة.")
        return

    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "🔢 استخدم الأمر مع معرف المجموعة: /قفل <group_id>")
        return

    group_id = args[1]

    if message.text.startswith('/قفل'):
        confession_locks[group_id] = True
    else:
        confession_locks[group_id] = False

    save_json('confession_locks.json', confession_locks)
    action = "تم قفل" if message.text.startswith('/قفل') else "تم فتح"
    bot.reply_to(message, f"✅ {action} الاعترافات في المجموعة {group_id}")

# --- حظر/رفع حظر ---
@bot.message_handler(commands=['حظر', 'الغاء_الحظر'])
def ban_unban(message):
    user_id = message.from_user.id
    if user_id != DEVELOPER_ID:
        bot.reply_to(message, "🚫 هذا الأمر فقط للمطور.")
        return

    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "🔢 استخدم الأمر مع معرف المستخدم: /حظر <user_id>")
        return

    target_id = args[1]

    if message.text.startswith('/حظر'):
        banned[target_id] = True
    else:
        banned[target_id] = False

    save_json('banned.json', banned)
    action = "تم حظر" if message.text.startswith('/حظر') else "تم رفع الحظر عن"
    bot.reply_to(message, f"✅ {action} المستخدم {target_id}")

# --- إضافة رسالة تحفيزية جديدة ---
@bot.message_handler(commands=['اضافة_رسالة'])
def add_motivational_message(message):
    user_id = message.from_user.id
    if user_id != DEVELOPER_ID:
        bot.reply_to(message, "🚫 هذا الأمر فقط للمطور.")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "✍️ يرجى كتابة الرسالة بعد الأمر: /اضافة_رسالة نص الرسالة")
        return

    msg_text = args[1]
    messages.append(msg_text)
    save_json('messages.json', messages)
    bot.reply_to(message, "✅ تمت إضافة الرسالة التحفيزية بنجاح.")

# --- رسائل تحفيزية دورية ---
def send_motivational_messages():
    for gid in groups.keys():
        try:
            msg = get_random_message()
            bot.send_message(int(gid), f"✨ رسالة تحفيزية:\n{msg}")
        except:
            pass
    threading.Timer(7200, send_motivational_messages).start()

send_motivational_messages()

print("✅ بوت الاعترافات شغال...")
bot.infinity_polling()