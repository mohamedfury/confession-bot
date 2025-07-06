import telebot
import json
import time

TOKEN = "7787936953:AAFPyBi4QPJWQKQB9qM3dBzQwizFYh3XjU0"
DEVELOPER_ID = 674291793  # عدلها على إيديك

bot = telebot.TeleBot(TOKEN)

GROUPS_FILE = "groups.json"
BANNED_FILE = "banned.json"
LOCKS_FILE = "confession_locks.json"
LAST_CONF_FILE = "last_confession_time.json"

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

def can_send_confession(user_id):
    now = time.time()
    if str(user_id) in last_conf:
        elapsed = now - last_conf[str(user_id)]
        if elapsed < 60:
            return False, 60 - int(elapsed)
    last_conf[str(user_id)] = now
    save_json(LAST_CONF_FILE, last_conf)
    return True, 0

def is_owner(message):
    admins = bot.get_chat_administrators(message.chat.id)
    for admin in admins:
        if admin.status == 'creator' and admin.user.id == message.from_user.id:
            return True
    return False

@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.chat.type not in ['group', 'supergroup']:
        bot.reply_to(message, "هذا الأمر فقط في المجموعات.")
        return
    if not is_owner(message):
        bot.reply_to(message, "أنت مو مالك الكروب.")
        return
    if not message.reply_to_message:
        bot.reply_to(message, "قم بالرد على رسالة العضو اللي تريد تحظره.")
        return
    user_id = message.reply_to_message.from_user.id
    banned_users[str(user_id)] = True
    save_json(BANNED_FILE, banned_users)
    bot.reply_to(message, f"تم حظر العضو {user_id} بنجاح.")

bot.polling()