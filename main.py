import telebot import json import time import threading import random

TOKEN = "7787936953:AAFPyBi4QPJWQKQB9qM3dBzQwizFYh3XjU0" DEVELOPER_ID = 674291793  # حط ايديك هنا

bot = telebot.TeleBot(TOKEN)

--- تحميل البيانات ---

def load_json(filename): try: with open(filename, 'r', encoding='utf-8') as f: return json.load(f) except: return {}

def save_json(filename, data): with open(filename, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)

--- قواعد بيانات ---

groups = load_json('groups.json') banned = load_json('banned.json') confession_locks = load_json('confession_locks.json') last_confession_time = load_json('last_confession_time.json') messages = load_json('messages.json') pending_selections = {}

START_MSG = "أهلاً بك في بوت الاعترافات💫. أرسل اعترافك هنا."

--- التحقق من الحظر ---

def is_banned(user_id): return str(user_id) in banned and banned[str(user_id)] == True

def is_confession_locked(group_id): return str(group_id) in confession_locks and confession_locks[str(group_id)] == True

def can_send_confession(user_id): now = time.time() last = last_confession_time.get(str(user_id), 0) if now - last >= 60: last_confession_time[str(user_id)] = now save_json('last_confession_time.json', last_confession_time) return True return False

def get_random_message(): return random.choice(messages) if messages else "اعترف الآن بصدق وأمانة"

@bot.message_handler(commands=['start']) def send_welcome(message): if message.chat.type == 'private': bot.send_message(message.chat.id, START_MSG)

@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'] and m.new_chat_members) def register_group(message): for member in message.new_chat_members: if member.id == bot.get_me().id: try: chat = bot.get_chat(message.chat.id) chat_member = bot.get_chat_member(message.chat.id, bot.get_me().id) if chat_member.status in ['administrator', 'creator']: groups[str(chat.id)] = chat.title save_json('groups.json', groups) bot.send_message(chat.id, "✅ تم تسجيل المجموعة بنجاح!") except Exception as e: print("خطأ في تسجيل المجموعة:", e)

@bot.message_handler(func=lambda m: m.chat.type == 'private', content_types=['text', 'photo', 'audio', 'voice', 'video', 'document']) def handle_confession(message): user_id = message.from_user.id

if is_banned(user_id):
    return bot.send_message(user_id, "🚫 أنت محظور من استخدام البوت.")

if not can_send_confession(user_id):
    return bot.send_message(user_id, "⏳ انتظر 60 ثانية بين كل اعتراف.")

user_groups = []
for gid in groups.keys():
    try:
        member = bot.get_chat_member(int(gid), user_id)
        if member.status not in ['left', 'kicked']:
            user_groups.append(gid)
    except:
        continue

if not user_groups:
    return bot.send_message(user_id, "❌ لا توجد مجموعات مشتركة لإرسال اعتراف.")

if len(user_groups) == 1:
    group_id = user_groups[0]
    if is_confession_locked(group_id):
        return bot.send_message(user_id, "🔒 الاعترافات مقفلة في هذه المجموعة.")
    return send_confession_to_owner(group_id, message)

markup = telebot.types.InlineKeyboardMarkup()
for gid in user_groups:
    try:
        title = bot.get_chat(int(gid)).title
        markup.add(telebot.types.InlineKeyboardButton(title, callback_data=f"select_group_{gid}"))
    except:
        continue

pending_selections[user_id] = message
bot.send_message(user_id, "اختر المجموعة لإرسال الاعتراف:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_group_")) def confirm_group(call): gid = call.data.split("_")[-1] uid = call.from_user.id if is_confession_locked(gid): return bot.answer_callback_query(call.id, "❌ الاعترافات مغلقة في هذه المجموعة.")

if uid in pending_selections:
    msg = pending_selections.pop(uid)
    send_confession_to_owner(gid, msg)
    bot.answer_callback_query(call.id, "✅ تم إرسال الاعتراف.")

--- إرسال الاعتراف للمالك ---

def send_confession_to_owner(group_id, message): try: caption = f"📢 اعتراف جديد لمجموعة {group_id}\n\n" if message.content_type == 'text': bot.send_message(DEVELOPER_ID, caption + message.text) elif message.content_type == 'photo': bot.send_photo(DEVELOPER_ID, message.photo[-1].file_id, caption=caption) elif message.content_type == 'voice': bot.send_voice(DEVELOPER_ID, message.voice.file_id, caption=caption) elif message.content_type == 'video': bot.send_video(DEVELOPER_ID, message.video.file_id, caption=caption) elif message.content_type == 'audio': bot.send_audio(DEVELOPER_ID, message.audio.file_id, caption=caption) elif message.content_type == 'document': bot.send_document(DEVELOPER_ID, message.document.file_id, caption=caption) bot.send_message(message.chat.id, "✅ تم إرسال الاعتراف بنجاح") except Exception as e: bot.send_message(message.chat.id, "❌ حدث خطأ أثناء الإرسال.") print("خطأ بالإرسال:", e)

--- رسائل تحفيزية ---

def send_motivations(): for gid in groups.keys(): try: bot.send_message(int(gid), get_random_message()) except: continue threading.Timer(7200, send_motivations).start()

send_motivations()

print("🤖 البوت يعمل الآن...") bot.infinity_polling()

