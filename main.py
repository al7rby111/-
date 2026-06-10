import asyncio
import time
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

API_TOKEN = '8922210658:AAG0VrT3BwrE_vjBU-5JybIgjKUejVstXGM'
ADMIN_ID = 7439686186  

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# 🗄️ قواعد بيانات مؤقتة داخل الذاكرة
user_best_scores = {}  
user_privacy = {}      
leaderboard = []       

user_current_word = {}
user_start_time = {}
user_game_mode = {}    
user_last_category = {} 

class BotStates(StatesGroup):
    waiting_for_suggestion = State()
    waiting_for_privacy_choice = State()

# الكلمات العادية واسمائها بالعربي للأزرار
CATEGORIES = {
    "cities": ["الرياض", "مكة المكرمة", "المدينة المنورة", "جدة", "الدمام", "القصيم", "حائل", "تبوك", "الطائف", "الأحساء"],
    "food": ["القهوة السعودية", "التمر", "الكبسة", "الجريش", "القرصان", "المطازيز", "المندي", "السليق", "السمبوسة", "الشاورما"],
    "tech": ["البرمجة", "الذكاء الاصطناعي", "الكمبيوتر", "الإنترنت", "الأمن السيبراني", "التشفير", "التطبيق", "السحابة"],
    "mix": ["الكعبة المشرفة", "القرآن الكريم", "الحديث الشريف", "الرياضيات", "الفيزياء", "الكيمياء", "الهندسة", "الاقتصاد"]
}

CATEGORY_NAMES = {
    "cities": "مدن ومناطق 🇸🇦",
    "food": "أكلات ومشروبات 🍔",
    "tech": "تقنية وفضاء 💻",
    "mix": "كلمات منوعة 🧠",
    "world": "تحدي العالم 🌐"
}

# كلمات "تحدي العالم"
WORLD_WORDS = [
    "قسطنطينية المجد العظمى", "الذكاء الاصطناعي التوليدي", "المملكة العربية السعودية أولاً", 
    "الرؤية الرقمية المستدامة", "الأمن السيبراني وحماية البيانات", "التشفير المتناظر المتقدم",
    "سيرفرات الحوسبة السحابية", "سرعة الكتابة الخارقة"
]

def get_main_menu_keyboard(user_id):
    best_score_text = f"{user_best_scores[user_id]:.2f} ثانية ⚡" if user_id in user_best_scores else "لا يوجد بعد 🎯"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🌐 🏆 تحدي العالم (دخول التصنيف) 🏆 🌐", callback_data="play_world")
    builder.button(text="🇸🇦 مدن ومناطق", callback_data="play_cities")
    builder.button(text="🍔 أكلات ومشروبات", callback_data="play_food")
    builder.button(text="💻 تقنية وفضاء", callback_data="play_tech")
    builder.button(text="🧠 كلمات منوعة", callback_data="play_mix")
    builder.button(text="📊 لوحة الصدارة (التوب 10)", callback_data="show_leaderboard")
    builder.button(text="🔒 إعدادات الخصوصية", callback_data="toggle_privacy")
    builder.button(text="💡 إرسال اقتراح للمطور", callback_data="send_suggestion")
    
    builder.adjust(1, 2, 2, 1, 1, 1)
    return builder.as_markup(), best_score_text

@dp.message(Command("start", "challenge"))
async def start_challenge(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    
    if user_id not in user_privacy:
        user_privacy[user_id] = True
        
    reply_markup, best_score_text = get_main_menu_keyboard(user_id)
    
    await message.reply(
        f"مرحباً بك في تحدي السرعة الخارق! ⚡\n\n"
        f"⏱️ **أفضل وقت شخصي لك:** {best_score_text}\n"
        f"👤 **حالة ظهور يوزرك في التوب:** {'ظاهر ✅' if user_privacy[user_id] else 'مخفي ❌'}\n\n"
        f"اختر اللعب العادي، أو اضغط على **تحدي العالم** لتدخل قائمة التوب 1! 👇", 
        reply_markup=reply_markup
    )

@dp.callback_query()
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    action = callback_query.data
    
    if action == "send_suggestion":
        await state.set_state(BotStates.waiting_for_suggestion)
        await callback_query.message.edit_text("💡 فضلاً اكتب اقتراحك في رسالة واحدة الآن:")
        
    elif action == "toggle_privacy":
        user_privacy[user_id] = not user_privacy[user_id]
        status = "ظاهر الآن ✅" if user_privacy[user_id] else "مخفي الآن (سيظهر كـ لاعب مخفي) ❌"
        await callback_query.message.reply(f"تم تحديث خصوصيتك! يوزرك في التوب أصبح: {status}\nأرسل /challenge لتحديث القائمة.")
        
    elif action == "show_leaderboard":
        if not leaderboard:
            await callback_query.message.reply("القائمة فارغة حالياً! كن أول من يتربع على عرش التوب 1 في 'تحدي العالم'.")
        else:
            sorted_board = sorted(leaderboard, key=lambda x: x['time'])[:10]
            board_text = "🏆 **لوحة الصدارة العالمية (أسرع 10 لاعبين):** 🏆\n\n"
            for index, player in enumerate(sorted_board, 1):
                medal = "🥇" if index == 1 else "🥈" if index == 2 else "🥉" if index == 3 else "🏅"
                board_text += f"{medal} **توب {index}:** {player['name']} ({player['username']}) -> ⏱️ `{player['time']:.2f}ث`\n"
            await callback_query.message.reply(board_text, parse_mode="Markdown")

    elif action == "play_world":
        chosen_word = random.choice(WORLD_WORDS)
        user_current_word[user_id] = chosen_word
        user_start_time[user_id] = time.time()
        user_game_mode[user_id] = "world"
        user_last_category[user_id] = "world"
        await callback_query.message.edit_text(f"🚨 **وضع تحدي العالم!** 🚨\nاكتبها بسرعة الصاروخ لتدخل التوب:\n\n`{chosen_word}`", parse_mode="Markdown")

    elif action.startswith("play_"):
        category_key = action.split("_")[1]
        if category_key in CATEGORIES:
            chosen_word = random.choice(CATEGORIES[category_key])
            user_current_word[user_id] = chosen_word
            user_start_time[user_id] = time.time()
            user_game_mode[user_id] = "normal"
            user_last_category[user_id] = category_key
            await callback_query.message.edit_text(f"تم اختيار القسم! اكتب بأسرع ما يمكن:\n\n`{chosen_word}`", parse_mode="Markdown")
            
    elif action == "continue_yes":
        category_key = user_last_category.get(user_id)
        if category_key == "world":
            chosen_word = random.choice(WORLD_WORDS)
            user_game_mode[user_id] = "world"
        elif category_key in CATEGORIES:
            chosen_word = random.choice(CATEGORIES[category_key])
            user_game_mode[user_id] = "normal"
        else:
            await callback_query.message.edit_text("حدث خطأ ما، يرجى البدء من جديد عبر /challenge")
            await callback_query.answer()
            return
            
        user_current_word[user_id] = chosen_word
        user_start_time[user_id] = time.time()
        await callback_query.message.edit_text(f"مستعد؟ اكتب الكلمة التالية بأسرع ما يمكن:\n\n`{chosen_word}`", parse_mode="Markdown")

    elif action == "continue_no":
        if user_id in user_last_category: del user_last_category[user_id]
        reply_markup, best_score_text = get_main_menu_keyboard(user_id)
        await callback_query.message.edit_text(
            f"تم الرجوع للقائمة الرئيسية. 🏠\n\n"
            f"⏱️ **أفضل وقت شخصي لك:** {best_score_text}\n"
            f"👤 **حالة ظهور يوزرك في التوب:** {'ظاهر ✅' if user_privacy[user_id] else 'مخفي ❌'}\n\n"
            f"اختر اللعب العادي، أو اضغط على **تحدي العالم**! 👇", 
            reply_markup=reply_markup
        )

    await callback_query.answer()

@dp.message(BotStates.waiting_for_suggestion)
async def receive_suggestion(message: types.Message, state: FSMContext):
    user_info = message.from_user
    admin_alert = f"📥 **اقتراح جديد!**\n\n👤 {user_info.full_name}\n🆔 `{user_info.id}`\n📝 {message.text}"
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_alert)
        await message.reply("✅ تم إرسال اقتراحك للمطور بنجاح! أرسل /challenge للعب.")
    except:
        await message.reply("❌ فشل الإرسال.")
    await state.clear()

@dp.message()
async def check_speed(message: types.Message):
    user_id = message.from_user.id
    end_time = time.time()
    
    if not message.text or user_id not in user_start_time:
        return

    target_word = user_current_word.get(user_id)
    mode = user_game_mode.get(user_id, "normal")

    if message.text.strip() == target_word:
        elapsed_time = end_time - user_start_time[user_id]
        reply_msg = f"صح! ⚡\nالوقت الحالي: **{elapsed_time:.2f} ثانية**\n"
        
        if user_id in user_best_scores:
            old_best = user_best_scores[user_id]
            if elapsed_time < old_best:
                reply_msg += f"\n🔥 **يا رباااه! حطمت محاولتك الأولى وأعلى رقم قياسي لك!**\n(رقمك القديم: {old_best:.2f}ث 💥 رقمك الجديد: {elapsed_time:.2f}ث)"
                user_best_scores[user_id] = elapsed_time
            else:
                reply_msg += f"\n⏱️ محاولتك لم تتخطى أعلى رقم قياسي لك الحالي: ({old_best:.2f} ثانية)."
        else:
            reply_msg += "\n🎯 هذي أول محاولة لك! تم تسجيل وقتك كأعلى رقم قياسي لك حالياً."
            user_best_scores[user_id] = elapsed_time

        if mode == "world":
            player_name = message.from_user.full_name
            player_username = f"@{message.from_user.username}" if message.from_user.username and user_privacy.get(user_id, True) else "👤 لاعب مخفي"
            
            player_exists = False
            for player in leaderboard:
                if player['user_id'] == user_id:
                    player_exists = True
                    if elapsed_time < player['time']:
                        player['time'] = elapsed_time
                        player['name'] = player_name
                        player['username'] = player_username
                    break
            
            if not player_exists:
                leaderboard.append({
                    'user_id': user_id,
                    'name': player_name,
                    'username': player_username,
                    'time': elapsed_time
                })
            reply_msg += "\n\n🌍 دخلت تصنيف 'تحدي العالم'! اضغط على زر لوحة الصدارة لتشوف ترتيبك الحين."

        current_cat_key = user_last_category.get(user_id, "normal")
        cat_name = CATEGORY_NAMES.get(current_cat_key, "هذا القسم")
        
        reply_msg += f"\n\nهل تريد التكملة في قسم (**{cat_name}**)؟"
        
        continue_builder = InlineKeyboardBuilder()
        continue_builder.button(text="✅ نعم، استمر", callback_data="continue_yes")
        continue_builder.button(text="❌ لا، القائمة الرئيسية", callback_data="continue_no")
        continue_builder.adjust(2)
        
        await message.reply(reply_msg, parse_mode="Markdown", reply_markup=continue_builder.as_markup())
        
        del user_start_time[user_id]
        del user_current_word[user_id]
        del user_game_mode[user_id]
    else:
        await message.reply("خطأ في الكتابة! أرسل /challenge وحاول مرة أخرى وعينك على الوقت ⏳")

async def main():
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    asyncio.run(main())
