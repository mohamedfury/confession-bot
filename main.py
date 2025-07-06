import telebot
import json
import time
import threading
import random

TOKEN = "AAFPyBi4QPJWQKQB9qM3dBzQwizFYh3XjU0"
DEVELOPER_ID = 123456789  # حط ايديك هنا

bot = telebot.TeleBot(TOKEN)

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

START_MSG = "أهلاً بك في بوت الاعترافات. أرسل اعترافك هنا."

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
    else:
        return False

def get_random_message():
    if messages:
        return random.choice(messages)
    else:
        return "اعترف الآن بصدق وأمانة"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.type == 'private':
        bot.send_message(message.chat.id, START_MSG)

# حذف هذا الجزء لأننا ما نريد البوت يرد في الكروبات على الرسائل العادية
# @bot.message_handler(func=lambda m: m.chat.type != 'private')
# def reply_group_message(message):
#     bot.reply_to(message, "يرجى إرسال اعترافك لي في الخاص.")

@bot.message_handler(func=lambda m: m.chat.type == 'private', content_types=['text', 'photo', 'audio', 'voice', 'video', 'document'])
def handle_confession(message):
    user_id = message.from_user.id

    if is_banned(user_id):
        bot.send_message(user_id, "أنت محظور من استخدام البوت.")
        return

    if not can_send_confession(user_id):
        bot.send_message(user_id, "يرجى الانتظار 60 ثانية بين كل اعتراف.")
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
        bot.send_message(user_id, "لا توجد لديك مجموعات مشتركة مع البوت لإرسال الاعتراف.")
        return
    elif len(user_groups) == 1:
        group_id = user_groups[0]
        if is_confession_locked(group_id):
            bot.send_message(user_id, "تم إغلاق استقبال الاعترافات في هذه المجموعة.")
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
        bot.send_message(user_id, "اختر المجموعة التي تريد إرسال الاعتراف لها:", reply_markup=markup)
        # تطلب منه يعيد إرسال الاعتراف بعد الاختيار
        return

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_group_"))
def callback_select_group(call):
    user_id = call.from_user.id
    group_id = call.data.split("_")[-1]

    if is_banned(user_id):
        bot.answer_callback_query(call.id, "أنت محظور من استخدام البوت.")
        return

    if is_confession_locked(group_id):
        bot.answer_callback_query(call.id, "تم إغلاق استقبال الاعترافات في هذه المجموعة.")
        return

    bot.answer_callback_query(call.id, "تم اختيار المجموعة، الرجاء إعادة إرسال اعترافك الآن.")
    bot.send_message(user_id, "الرجاء إعادة إرسال اعترافك الآن.")

def send_confession_to_owner(group_id, message):
    group_owner_id = DEVELOPER_ID  # عدل هنا إذا عندك مالك مختلف لكل مجموعة

    try:
        content_type = message.content_type
        text = ""

        if content_type == 'text':
            text = message.text
        elif content_type == 'photo':
            text = "[صورة مرفقة]"
        elif content_type == 'audio':
            text = "[صوت مرفق]"
        elif content_type == 'voice':
            text = "[رسالة صوتية]"
        elif content_type == 'video':
            text = "[فيديو مرفق]"
        elif content_type == 'document':
            text = "[ملف مرفق]"
        else:
            text = "[نوع رسالة غير مدعوم]"

        caption = f"📢 اعتراف جديد في المجموعة: {group_id}\n\n" \
                  f"من: {message.from_user.first_name} (id: {message.from_user.id})\n\n" \
                  f"المحتوى:\n{text}"

        bot.send_message(group_owner_id, caption)
        bot.send_message(message.from_user.id, "تم إرسال اعترافك إلى مالك المجموعة بنجاح.")
    except Exception as e:
        bot.send_message(message.from_user.id, "حدث خطأ أثناء إرسال اعترافك.")
        print("Error sending confession:", e)

@bot.message_handler(commands=['lockconfession', 'unlockconfession'])
def lock_unlock_confession(message):
    user_id = message.from_user.id
    if user_id != DEVELOPER_ID:
        bot.reply_to(message, "هذا الأمر فقط للمطور.")
        return

    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "استخدم الأمر مع معرف المجموعة: /lockconfession <group_id> أو /unlockconfession <group_id>")
        return

    group_id = args[1]

    if message.text.startswith('/lockconfession'):
        confession_locks[group_id] = True
        save_json('confession_locks.json', confession_locks)
        bot.reply_to(message, f"تم قفل الاعترافات في المجموعة {group_id}")
    else:
        confession_locks[group_id] = False
        save_json('confession_locks.json', confession_locks)
        bot.reply_to(message, f"تم فتح الاعترافات في المجموعة {group_id}")

@bot.message_handler(commands=['ban', 'unban'])
def ban_unban(message):
    user_id = message.from_user.id
    if user_id != DEVELOPER_ID:
        bot.reply_to(message, "هذا الأمر فقط للمطور.")
        return

    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "استخدم الأمر مع معرف المستخدم: /ban <user_id> أو /unban <user_id>")
        return

    target_id = args[1]

    if message.text.startswith('/ban'):
        banned[target_id] = True
        save_json('banned.json', banned)
        bot.reply_to(message, f"تم حظر المستخدم {target_id}")
    else:
        banned[target_id] = False
        save_json('banned.json', banned)
        bot.reply_to(message, f"تم رفع الحظر عن المستخدم {target_id}")

def send_motivational_messages():
    for gid in groups.keys():
        try:
            msg = get_random_message()
            bot.send_message(int(gid), f"📢 رسالة تحفيزية:\n{msg}")
        except:
            pass
    threading.Timer(7200, send_motivational_messages).start()

send_motivational_messages()

print("بوت الاعترافات شغال...")

bot.infinity_polling()