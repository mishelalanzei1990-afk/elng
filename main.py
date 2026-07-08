import asyncio
import random
import json
import os
import hmac
import hashlib
import base64
import time
from datetime import datetime
import pytz
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# =====================================================================
# 👑 الإعدادات السيادية (بوت اللغة الإنجليزية المطور - بث كل ساعة)
# =====================================================================
BOT_TOKEN = "8859538798:AAHmJ0NM0-M9MZSfHLvZx27zzbjukQTF1dc"
ADMIN_ID = 892901952

SECRET_KEY = "V40_ENGLISH_SECURE_2026"
USERS_FILE = "english_users_database.json"

STORE_LINK = "https://t.me/your_store"  
SUPPORT_LINK = "https://t.me/your_support"

# توقيت البث (مكة المكرمة) للتسجيل فقط
TIMEZONE = pytz.timezone('Asia/Riyadh')

# 📊 بنك الكلمات (Word -> Meaning)
WORDS_POOL = [
    ("Persistent", "مستمر / مُصرّ"),
    ("Acquire", "يكتسب / يحصل على"),
    ("Fluency", "الطلاقة في التحدث"),
    ("Enhance", "يُحسّن / يُطوّر"),
    ("Simultaneously", "في نفس الوقت / بالتزامن"),
    ("Precise", "دقيق / محدد"),
    ("Inevitable", "حتمي / لا مفر منه"),
    ("Incorporate", "يدمج / يدمج في"),
    ("Obtain", "يحصل على / ينال"),
    ("Consequences", "عواقب / نتائج")
]

# 📝 بنك الجمل (Sentence -> Meaning)
SENTENCES_POOL = [
    ("Consistency is the key to success.", "الاستمرارية هي مفتاح النجاح."),
    ("Don't count the days, make the days count.", "لا تحسب الأيام، بل اجعل الأيام ذات قيمة."),
    ("Learning a language takes time and patience.", "تعلم اللغة يستغرق وقتاً وصبرًا."),
    ("Believe you can and you're halfway there.", "آمن بأنك تستطيع وبذلك تكون قد قطعت نصف الطريق."),
    ("Mistakes are proof that you are trying.", "الأخطاء دليل على أنك تحاول."),
    ("Action speaks louder than words.", "الأفعال أبلغ من الأقوال."),
    ("The sooner the better.", "كلما كان أسرع كان أفضل.")
]

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
    return str(user_id) in db and time.time() < float(db[str(user_id)])

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
# 📡 محرك البث التلقائي الجديد (كل ساعة: كلمتين وجملتين)
# =====================================================================
async def hourly_broadcaster(application: Application):
    """نظام بث يشتغل تلقائياً على مدار الساعة ويرسل المحتوى كل 60 دقيقة"""
    print("🔄 تم تشغيل نظام البث التلقائي الساعي (كل ساعة)...")
    
    while True:
        try:
            # انتظر ساعة كاملة (3600 ثانية) قبل البث التالي
            await asyncio.sleep(10)
            
            db = load_db()
            active_users = [uid for uid, exp in db.items() if time.time() < float(exp)]
            
            if not active_users:
                continue
                
            # اختيار كلمتين وجملتين عشوائيتين بدون تكرار
            selected_words = random.sample(WORDS_POOL, 2)
            selected_sentences = random.sample(SENTENCES_POOL, 2)
            
            # تجهيز نص الرسالة المرتب
            broadcast_msg = (
                "⏰ **التحديث الساعي للغة الإنجليزية | Hourly English Update**\n"
                "───────────────────\n"
                "💡 **الكلمات الجديدة:**\n\n"
                f"1️⃣ 🇬🇧 `{selected_words[0]^[0]}`\n🇸🇦 {selected_words[0]^[1]}\n\n"
                f"2️⃣ 🇬🇧 `{selected_words[1]^[0]}`\n🇸🇦 {selected_words[1]^[1]}\n"
                "───────────────────\n"
                "📝 **الجمل والمحادثة:**\n\n"
                f"💬 🇬🇧 `{selected_sentences[0]^[0]}`\n🇸🇦 {selected_sentences[0]^[1]}\n\n"
                f"💬 🇬🇧 `{selected_sentences[1]^[0]}`\n🇸🇦 {selected_sentences[1]^[1]}\n"
                "───────────────────\n"
                "🧠 استمر في المراجعة والممارسة اليومية لضمان الطلاقة!"
            )
            
            # إرسال الرسالة لكافة المشتركين نشطين
            for user_id in active_users:
                try:
                    await application.bot.send_message(chat_id=int(user_id), text=broadcast_msg, parse_mode="Markdown")
                    await asyncio.sleep(0.05)  # تفادي حظر التليجرام لـ Flood
                except:
                    pass
            print(f"✅ تم بث التحديث الساعي التلقائي بنجاح لجميع المشتركين.")
            
        except Exception as e:
            print(f"⚠️ خطأ في نظام البث الساعي: {e}")

# =====================================================================
# 🇬🇧 قوائم الأوامر والوظائف الأساسية لطلب اليدوي
# =====================================================================
MAIN_MENU = [
    ["📝 اختبار تحديد المستوى", "📖 الكلمات اليومية"],
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
            db[str(uid)] = exp
            save_db(db)
            await update.message.reply_text("✅ **Subscription activated successfully!**\nاضغط /start لتحديث القائمة.")
        else:
            await update.message.reply_text(exp)
        return

    if not is_subscribed(uid): return

    if text == "📖 الكلمات اليومية":
        w = random.choice(WORDS_POOL)
        await update.message.reply_text(f"💡 **طلب يدوي | Word:**\n\n🇬🇧 `{w[0]}`\n🇸🇦 {w[1]}")

    elif text == "🧠 نصيحة اليوم":
        s = random.choice(SENTENCES_POOL)
        await update.message.reply_text(f"🗣️ **طلب يدوي | Sentence:**\n\n🇬🇧 `{s[0]}`\n🇸🇦 {s[1]}")

    elif text == "📝 اختبار تحديد المستوى":
        await update.message.reply_text("📝 **Placement Test Coming Soon!**\nيجري حالياً إعداد تحديث شامل للاختبار التفاعلي، ترقبه قريباً.")

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

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.from_user.id != ADMIN_ID: return

    days = 30 if q.data == "gen_1m" else 365
    code = generate_code(days)
    await context.bot.send_message(
        chat_id=ADMIN_ID, 
        text=f"🎫 **New English Code Generated ({days} Days):**\n\n`{code}`\n\nCopy and send it to the user."
    )

# =====================================================================
# 🚀 محرك التشغيل الرئيسي مدمج معه البث التلقائي الساعي
# =====================================================================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    # تشغيل مهمة البث التلقائي المتوازي لتعمل كل ساعة في الخلفية
    loop = asyncio.get_event_loop()
    loop.create_task(hourly_broadcaster(app))
    
    print("🚀 بوت اللغة الإنجليزية المطور يعمل الآن! البث الساعي التلقائي (كلمتين + جملتين) نشط حالياً.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
