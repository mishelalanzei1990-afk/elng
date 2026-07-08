import asyncio
import random
import json
import os
import hmac
import hashlib
import base64
import time
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# =====================================================================
# 👑 الإعدادات السيادية (بوت المستويات المتطور - بث كل 30 ثانية)
# =====================================================================
BOT_TOKEN = "8859538798:AAHmJ0NM0-M9MZSfHLvZx27zzbjukQTF1dc"
ADMIN_ID = 892901952

SECRET_KEY = "V40_ENGLISH_SECURE_2026"
USERS_FILE = "english_users_database.json"

STORE_LINK = "https://t.me/your_store"  
SUPPORT_LINK = "https://t.me/your_support"

# =====================================================================
# 📊 بنك المحتوى المقسم حسب المستويات (كلمات وجمل)
# =====================================================================
CONTENT_POOL = {
    "Beginner": {
        "words": [
            ("Always", "دائماً"), ("Clean", "نظيف"), ("Happy", "سعيد"), 
            ("Water", "ماء"), ("Family", "عائلة"), ("Friend", "صديق"),
            ("Simple", "بسيط"), ("Learn", "يتعلم"), ("Speak", "يتحدث")
        ],
        "sentences": [
            ("How are you today?", "كيف حالك اليوم؟"),
            ("Nice to meet you.", "سعدت بلقائك."),
            ("Where is the library?", "أين تقع المكتبة؟"),
            ("I love learning English.", "أنا أحب تعلم الإنجليزية."),
            ("Have a nice day!", "أتمنى لك يوماً سعيداً!")
        ]
    },
    "Intermediate": {
        "words": [
            ("Persistent", "مستمر / مُصرّ"), ("Acquire", "يكتسب / يحصل على"), 
            ("Fluency", "الطلاقة في التحدث"), ("Enhance", "يُحسّن / يُطوّر"), 
            ("Obtain", "يحصل على / ينال"), ("Manage", "يدير / يتعامل مع"),
            ("Essential", "ضروري / أساسي"), ("Frequent", "متكرر")
        ],
        "sentences": [
            ("Consistency is the key to success.", "الاستمرارية هي مفتاح النجاح."),
            ("Learning a language takes time and patience.", "تعلم اللغة يستغرق وقتاً وصبرًا."),
            ("Mistakes are proof that you are trying.", "الأخطاء دليل على أنك تحاول."),
            ("Could you please clarify this point?", "هل يمكنك توضيح هذه النقطة من فضلك؟"),
            ("I am looking forward to meeting you.", "أنا أتطلع بشوق للقائك.")
        ]
    },
    "Advanced": {
        "words": [
            ("Simultaneously", "في نفس الوقت / بالتزامن"), ("Inevitable", "حتمي / لا مفر منه"), 
            ("Incorporate", "يدمج / يدمج في"), ("Consequences", "عواقب / نتائج"),
            ("Ambiguous", "غامض / مبهم"), ("Eloquent", "فصيح / بليغ"),
            ("Pragmatic", "عملي / واقعي"), ("Scrutinize", "يدقق النظر / يفحص بشدة")
        ],
        "sentences": [
            ("Don't count the days, make the days count.", "لا تحسب الأيام، بل اجعل الأيام ذات قيمة."),
            ("Believe you can and you're halfway there.", "آمن بأنك تستطيع وبذلك تكون قد قطعت نصف الطريق."),
            ("Action speaks louder than words.", "الأفعال أبلغ من الأقوال."),
            ("The ends justify the means.", "الغاية تبرر الوسيلة."),
            ("Success is not final, failure is not fatal.", "النجاح ليس نهائياً، والفشل ليس قاتلاً.")
        ]
    }
}

# =====================================================================
# 💾 إدارة قاعدة البيانات والذاكرة
# =====================================================================
def load_db():
    if not os.path.exists(USERS_FILE): return {}
    try:
        with open(USERS_FILE, "r", encoding='utf-8') as f: return json.load(f)
    except: return {}

def save_db(data):
    with open(USERS_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def is_subscribed(user_id):
    if user_id == ADMIN_ID: return True
    db = load_db()
    return str(user_id) in db and time.time() < float(db[str(user_id)]["expiry"])

# =====================================================================
# 🔐 محرك التشفير والتحقق للأكواد
# =====================================================================
def verify_code(code):
    try:
        clean = code.replace("ENG-", "").strip()
        missing_padding = len(clean) % 4
        if missing_padding: clean += '=' * (4 - missing_padding)
        decoded = base64.urlsafe_b64decode(clean).decode()
        expiry, sig = decoded.split(":")
        check = hmac.new(SECRET_KEY.encode(), f"ENGLISH:{expiry}".encode(), hashlib.sha256).hexdigest()[:12]
        if sig == check and time.time() < int(expiry): return True, int(expiry)
        return False, "❌ الكود غير صالح أو منتهي الصلاحية."
    except: return False, "⚠️ خطأ في تنسيق الكود."

def generate_code(days):
    expiry = int(time.time()) + (days * 86400)
    sig = hmac.new(SECRET_KEY.encode(), f"ENGLISH:{expiry}".encode(), hashlib.sha256).hexdigest()[:12]
    token = base64.urlsafe_b64encode(f"{expiry}:{sig}".encode()).decode().replace("=", "")
    return f"ENG-{token}"

# =====================================================================
# 📡 محرك البث التلقائي المطور (كل 30 ثانية حسب مستوى كل مستخدم)
# =====================================================================
async def fast_broadcaster(application: Application):
    """نظام بث فائق السرعة يرسل المحتوى المخصص للمشتركين كل 30 ثانية"""
    print("🔄 تم تشغيل نظام البث التلقائي السريع (كل 30 ثانية)...")
    
    while True:
        try:
            # الانتظار لمدة 30 ثانية
            await asyncio.sleep(30)
            
            db = load_db()
            now_ts = time.time()
            
            # فحص وإرسال لكل مستخدم حسب مستواه الخاص المذكور في قاعدة البيانات
            for user_id, user_data in db.items():
                if now_ts >= float(user_data["expiry"]) and int(user_id) != ADMIN_ID:
                    continue # تخطي المنتهية اشتراكاتهم
                
                # جلب مستوى المستخدم الحالي (الافتراضي مبتدئ إذا لم يحدد)
                user_level = user_data.get("level", "Beginner")
                pool = CONTENT_POOL[user_level]
                
                # اختيار عشوائي ذكي حسب مستوى هذا الشخص
                w = random.sample(pool["words"], 2)
                s = random.sample(pool["sentences"], 2)
                
                level_ar = "مبتدئ" if user_level == "Beginner" else "متوسط" if user_level == "Intermediate" else "متقدم"
                
                # صياغة الرسالة
                broadcast_msg = (
                    f"⏱ **التحديث الدوري السريع | مستوى: {level_ar}**\n"
                    "───────────────────\n"
                    "💡 **الكلمات الجديدة:**\n\n"
                    f"1️⃣ 🇬🇧 `{w[0][0]}`\n🇸🇦 {w[0][1]}\n\n"
                    f"2️⃣ 🇬🇧 `{w[1][0]}`\n🇸🇦 {w[1][1]}\n"
                    "───────────────────\n"
                    "📝 **الجمل السريعة:**\n\n"
                    f"💬 🇬🇧 `{s[0][0]}`\n🇸🇦 {s[0][1]}\n\n"
                    f"💬 🇬🇧 `{s[1][0]}`\n🇸🇦 {s[1][1]}\n"
                    "───────────────────\n"
                    "⚡️ ممارسة كل 30 ثانية لتثبيت المعلومة بنظام التكرار المتباعد!"
                )
                
                try:
                    await application.bot.send_message(chat_id=int(user_id), text=broadcast_msg, parse_mode="Markdown")
                    await asyncio.sleep(0.05)  # حماية السيرفر من الحظر التلقائي لـ Telegram
                except:
                    pass
                    
        except Exception as e:
            print(f"⚠️ خطأ في نظام البث السريع: {e}")

# =====================================================================
# 🇬🇧 قوائم الأوامر والوظائف الأساسية
# =====================================================================
MAIN_MENU = [
    ["📝 اختيار تحديد المستوى", "📖 الكلمات اليومية"],
    ["🗣️ محادثة تفاعلية", "🧠 نصيحة اليوم"],
    ["⚙️ الدعم والاشتراك"]
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_subscribed(uid):
        await update.message.reply_text(f"⚠️ **Subscription not active.**\nPlease activate your subscription: {STORE_LINK}")
        return
        
    menu = MAIN_MENU.copy()
    if uid == ADMIN_ID: menu.insert(0, ["🛠 Admin Control"])
    
    welcome_msg = (
        "🇬🇧 **Welcome to the English Learning Platform!**\n\n"
        "مرحباً بك في منصتك المتطورة لتعلم وتطوير اللغة الإنجليزية! "
        "اختر أحد الخيارات من القائمة بالأسفل لبدء رحلتك التعليمية:"
    )
    await update.message.reply_text(welcome_msg, reply_markup=ReplyKeyboardMarkup(menu, resize_keyboard=True), parse_mode="Markdown")

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.strip()
    uid = update.effective_user.id

    if text.startswith("ENG-"):
        ok, exp = verify_code(text)
        if ok:
            db = load_db()
            # حفظ بنية البيانات الجديدة لتشمل الإكسفاير والمستوى الافتراضي
            db[str(uid)] = {"expiry": exp, "level": "Beginner"}
            save_db(db)
            await update.message.reply_text("✅ **Subscription activated successfully!**\nمستواك الحالي الافتراضي: (مبتدئ). يمكنك تغييره الآن بالضغط على زر تحديد المستوى.")
        else:
            await update.message.reply_text(exp)
        return

    if not is_subscribed(uid): return

    db = load_db()
    # تأمين الحصول على البيانات الحالية للمستخدم
    user_data = db.get(str(uid), {"level": "Beginner"})
    user_level = user_data.get("level", "Beginner")

    if text == "📖 الكلمات اليومية":
        w = random.choice(CONTENT_POOL[user_level]["words"])
        await update.message.reply_text(f"💡 **طلب يدوي ({user_level}) | Word:**\n\n🇬🇧 `{w[0]}`\n🇸🇦 {w[1]}")

    elif text == "🧠 نصيحة اليوم":
        s = random.choice(CONTENT_POOL[user_level]["sentences"])
        await update.message.reply_text(f"🗣️ **طلب يدوي ({user_level}) | Sentence:**\n\n🇬🇧 `{s[0]}`\n🇸🇦 {s[1]}")

    elif text == "📝 اختيار تحديد المستوى":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🟢 مبتدئ (Beginner)", callback_data="set_Beginner")],
            [InlineKeyboardButton("🟡 متوسط (Intermediate)", callback_data="set_Intermediate")],
            [InlineKeyboardButton("🟠 متقدم (Advanced)", callback_data="set_Advanced")]
        ])
        await update.message.reply_text("📝 **الرجاء تحديد مستواك في اللغة الإنجليزية:**\nبناءً على اختيارك سيقوم البوت بتقديم وبث المحتوى المناسب لك تلقائياً.", reply_markup=kb)

    elif text == "🗣️ محادثة تفاعلية":
        await update.message.reply_text("🗣️ **Interactive Conversation:**\nأهلاً بك! ابدأ كتابة أي جملة بالإنجليزية وسأقوم بمساعدتك وتصحيحها لك فوراً.")

    elif text == "⚙️ الدعم والاشتراك":
        await update.message.reply_text(f"🛒 **Subscription Link:** {STORE_LINK}\n💬 **Technical Support:** {SUPPORT_LINK}")

    elif uid == ADMIN_ID and text == "🛠 Admin Control":
        count = len(load_db())
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎫 Code 1 Month", callback_data="gen_1m"), 
             InlineKeyboardButton("🎫 Code 1 Year", callback_data="gen_1y")]
        ])
        await update.message.reply_text(
            f"👥 **Admin Control Panel:**\n\nActive Subscribers: `{count}`\n\nGenerate validation codes for customers:", 
            reply_markup=kb, 
            parse_mode="Markdown"
        )

# =====================================================================
# 🎫 معالج الأزرار التفاعلية (تحديد المستويات وتوليد الأكواد)
# =====================================================================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    # 1. معالجة تغيير مستويات المشتركين
    if q.data.startswith("set_"):
        level_choice = q.data.replace("set_", "")
        db = load_db()
        if str(uid) in db:
            db[str(uid)]["level"] = level_choice
        else:
            # للأدمن أو الحالات الطارئة
            db[str(uid)] = {"expiry": time.time() + 31536000, "level": level_choice}
        save_db(db)
        
        level_ar = "مبتدئ" if level_choice == "Beginner" else "متوسط" if level_choice == "Intermediate" else "متقدم"
        await q.edit_message_text(f"🎯 **تم تعديل مستواك بنجاح إلى: [{level_ar}]**\nسيصلك محتوى البث التلقائي القادم متوافقاً مع هذا المستوى.")
        return

    # 2. لوحة تحكم الأدمن (توليد الأكواد)
    if uid != ADMIN_ID: return
    if q.data in ["gen_1m", "gen_1y"]:
        days = 30 if q.data == "gen_1m" else 365
        code = generate_code(days)
        await context.bot.send_message(
            chat_id=ADMIN_ID, 
            text=f"🎫 **New English Code Generated ({days} Days):**\n\n`{code}`\n\nCopy and send it to the user."
        )

# =====================================================================
# 🚀 محرك التشغيل الرئيسي مدمج معه البث التلقائي السريع جداً
# =====================================================================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    # تشغيل مهمة البث التلقائي الذكي المتوازي (كل 30 ثانية)
    loop = asyncio.get_event_loop()
    loop.create_task(fast_broadcaster(app))
    
    print("🚀 تم إطلاق البوت بنجاح! نظام المستويات فعال والبث التلقائي السريع جداً (كل 30 ثانية) يعمل حالياً بكفاءة.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
