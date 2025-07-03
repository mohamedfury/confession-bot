
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = '7787936953:AAHI6UWGZeddq76Dny5FNFtqTgXm5OFvSpA'
DEVELOPER_ID = 674291793
GROUP_ID = -1001201718722

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

admissions_open = False

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply("اهلا بك في بوت الاعترافات 🌚\nاذا الاعترافات مفتوحة اكدر استلم منك رسالتك.")

@dp.message_handler(lambda message: message.chat.type == 'supergroup')
async def group_commands(message: types.Message):
    global admissions_open
    if message.from_user.id == DEVELOPER_ID:
        if message.text == "فتح الاعترافات":
            admissions_open = True
            await message.reply("✅ تم فتح الاعترافات.")
        elif message.text == "ايقاف الاعترافات":
            admissions_open = False
            await message.reply("⛔ تم ايقاف الاعترافات.")

@dp.message_handler(lambda message: message.chat.type == 'private')
async def handle_confession(message: types.Message):
    if not admissions_open:
        await message.reply("🚫 الاعترافات مغلقة حالياً.")
        return

    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("نشر", callback_data=f"publish|{message.message_id}"),
        InlineKeyboardButton("حذف", callback_data=f"delete|{message.message_id}")
    )
    await bot.send_message(DEVELOPER_ID, f"📝 اعتراف جديد:\n\n{message.text}", reply_markup=keyboard)

@dp.callback_query_handler()
async def handle_decision(call: types.CallbackQuery):
    action, msg_id = call.data.split("|")

    if action == "publish":
        confession_text = call.message.text.replace("📝 اعتراف جديد:\n\n", "")
        await bot.send_message(GROUP_ID, f"💭 اعتراف مجهول:\n\n{confession_text}")
        await call.message.edit_text("✅ تم نشر الاعتراف.")
    elif action == "delete":
        await call.message.edit_text("❌ تم حذف الاعتراف.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
  
