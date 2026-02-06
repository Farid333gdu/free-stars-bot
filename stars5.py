from telebot import TeleBot, types
import sqlite3, random
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread
import os
import sqlite3
from datetime import datetime
import time
import sqlite3
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("BOT_TOKEN")

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_web():
    app.run(host="0.0.0.0", port=8080)

Thread(target=run_web).start()


TOKEN = "8277024183:AAEr_pmQAw8ofdtsrWpLLruI4tMWShnyW6M"
SUPPORT_ID = "@im_Xo2"
ORDERS_CHANNEL = "@free_xStars"
CHANNELS = ["@stars_freex"]
OWNER_ID = 8589848955
ADMINS = [
    111111111,
    222222222,
]
TRANSFER_GROUP_ID = -1003529474317  # آیدی عددی گروه
TRANSFER_COOLDOWN = 15    # ثانیه (ضد اسپم)

WITHDRAW_COOLDOWN = 3600  # 1 ساعت (ثانیه)
ORDERS_CHANNEL = -1003595070275
bot = TeleBot(TOKEN)
withdraw_requests = {}

# ================= دیتابیس =================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "bot.db")

db = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    balance REAL DEFAULT 0,
    captcha_passed INTEGER DEFAULT 0,
    join_date TEXT,
    invite_count INTEGER DEFAULT 0,
    transfer_count INTEGER DEFAULT 0,
    order_count INTEGER DEFAULT 0,
    inviter INTEGER,
    last_active TEXT
)
""")
db.commit()

cur.execute("""
CREATE TABLE IF NOT EXISTS settings(
    key TEXT PRIMARY KEY,
    value TEXT
)
""")
db.commit()

# مقدار پیش‌فرض هدیه دعوت
cur.execute(
    "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
    ("invite_reward", "0.1")
)
db.commit()


# ستون pending_withdraw
try:
    cur.execute(
        "ALTER TABLE users ADD COLUMN pending_withdraw INTEGER DEFAULT 0"
    )
    db.commit()
except sqlite3.OperationalError:
    pass


# ستون last_transfer (ضد اسپم انتقال)
try:
    cur.execute(
        "ALTER TABLE users ADD COLUMN last_transfer INTEGER DEFAULT 0"
    )
    db.commit()
except sqlite3.OperationalError:
    pass


# ستون last_withdraw (کنترل فاصله برداشت)
try:
    cur.execute(
        "ALTER TABLE users ADD COLUMN last_withdraw INTEGER DEFAULT 0"
    )
    db.commit()
except sqlite3.OperationalError:
    pass


# تبدیل موجودی‌ها به عدد صحیح (حذف اعشار)
cur.execute(
    "UPDATE users SET balance = CAST(balance AS INTEGER)"
)
db.commit()

# ================= متغیرها =================
transfer_state = {}
withdraw_state = {}
admin_steps = {}

BOT_ACTIVE = True
withdraw_requests = {}

# ================= توابع =================
def is_admin(uid):
    return uid == OWNER_ID or uid in ADMINS

def update_last_active(user_id):
    cur.execute(
        "UPDATE users SET last_active=? WHERE user_id=?",
        (datetime.now().strftime("%Y-%m-%d"), user_id)
    )
    db.commit()
    
try:
    cur.execute(
        "ALTER TABLE users ADD COLUMN pending_withdraw INTEGER DEFAULT 0"
    )
    db.commit()
    print("✅ ستون pending_withdraw اضافه شد")
except sqlite3.OperationalError:
    print("ℹ️ ستون pending_withdraw از قبل وجود دارد")
except Exception as e:
    print("❌ خطای غیرمنتظره:", e)

    
def get_invite_reward():
    cur.execute("SELECT value FROM settings WHERE key='invite_reward'")
    return float(cur.fetchone()[0])
    
reward = get_invite_reward()


def catch_text(message):
    update_last_active(message.from_user.id)
    
def user_tag(user):
    if user.username:
        return f"@{user.username}"
    return user.first_name
    


# ================= منو =================
def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👤 حساب کاربری", "💰 انتقال موجودی")
    kb.add("⭐ برداشت استارز", "🎁 دعوت دوستان")
    kb.add("📘 راهنما", "📞 پشتیبانی")
    return kb

def back_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔙 برگشت")
    return kb

# ================= عضویت کانال =================
def check_channels(uid):
    for ch in CHANNELS:
        try:
            s = bot.get_chat_member(ch, uid).status
            if s not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def join_keyboard():
    kb = InlineKeyboardMarkup()
    for ch in CHANNELS:
        kb.add(InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{ch.replace('@','')}"))
    kb.add(InlineKeyboardButton("✅ بررسی عضویت", callback_data="check_join"))
    return kb

@bot.callback_query_handler(func=lambda c: c.data == "check_join")
def recheck(call):
    uid = call.from_user.id
    if check_channels(uid):
        bot.edit_message_text("✅ عضویت تایید شد", call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "🌟 به ربات استارز رایگان خوش آمدی همین الان شروع کن ", reply_markup=main_menu())
    else:
        bot.answer_callback_query(call.id, "❌ هنوز عضو نشدی", show_alert=True)

# ================= کپچا =================
captcha = {}

def send_captcha(message):
    code = str(random.randint(1000, 9999))
    captcha[message.from_user.id] = code
    bot.send_message(message.chat.id, f"🔐 کد امنیتی:\n{code}")

@bot.message_handler(func=lambda m: m.from_user.id in captcha and m.text.isdigit())
def check_captcha(message):
    uid = message.from_user.id

    if message.text != captcha[uid]:
        bot.send_message(message.chat.id, "❌ کد اشتباهه")
        return

    cur.execute("UPDATE users SET captcha_passed=1 WHERE user_id=?", (uid,))
    db.commit()
    captcha.pop(uid)

    # 🎁 جایزه دعوت (فقط یکبار)
    cur.execute("SELECT inviter FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    inviter = row[0] if row else None

    if inviter:
        reward = get_invite_reward()

        cur.execute(
            "UPDATE users SET balance=balance+?, invite_count=invite_count۷+1 WHERE user_id=?",
            (reward, inviter)
        )
        cur.execute("UPDATE users SET inviter=NULL WHERE user_id=?", (uid,))
        db.commit()

        try:
            bot.send_message(
                inviter,
                f"🎉 یک دعوت موفق داشتی\n⭐ {reward} استارز گرفتی"
            )
        except:
            pass

    # 📢 بررسی عضویت در کانال
    if not check_channels(uid):
        bot.send_message(
            message.chat.id,
            "📢 عضو کانال شو",
            reply_markup=join_keyboard()
        )
        return

    # ✅ ورود موفق
    bot.send_message(
        message.chat.id,
        "✅ ورود موفق",
        reply_markup=main_menu()
    )

# ================= start =================
@bot.message_handler(commands=["start"])
def start(message):
    uid = message.from_user.id
    inviter = None

    if len(message.text.split()) > 1:
        i = message.text.split()[1]
        if i.isdigit() and int(i) != uid:
            inviter = int(i)

    cur.execute("SELECT captcha_passed FROM users WHERE user_id=?", (uid,))
    user = cur.fetchone()

    if not user:
        cur.execute(
            "INSERT INTO users(user_id, join_date, inviter) VALUES(?,?,?)",
            (uid, datetime.now().strftime("%Y-%m-%d"), inviter)
        )
        db.commit()
        send_captcha(message)
        return

    if user[0] == 0:
        send_captcha(message)
        return

    if not check_channels(uid):
        bot.send_message(message.chat.id, "📢 عضو کانال شو", reply_markup=join_keyboard())
        return

    bot.send_message(message.chat.id, "🌟 به ربات استارز رایگان خوش آمدی همین الان شروع کن ", reply_markup=main_menu())

@bot.message_handler(func=lambda m: not BOT_ACTIVE and m.from_user.id != OWNER_ID)
def bot_is_off(message):
    return
    
# ================= پروفایل =================
@bot.message_handler(func=lambda m: m.text == "👤 حساب کاربری")
def profile(message):
    uid = message.from_user.id
    cur.execute("""
    SELECT balance, join_date, invite_count, transfer_count, order_count
    FROM users WHERE user_id=?
    """, (uid,))
    u = cur.fetchone()

    bot.send_message(message.chat.id, f"""
👤 حساب کاربری
📅 عضویت: {u[1]}
⭐ موجودی: {int(u[0])} استارز
👥 دعوت‌ها: {u[2]}
🔁 انتقال‌ها: {u[3]}
🛒 برداشت‌ها: {u[4]}
""")



# ================= راهنما =================
@bot.message_handler(func=lambda m: m.text == "📘 راهنما")
def help_section(message):
    bot.send_message(
        message.chat.id,
        """📘 راهنمای ربات استارز

🔐 مرحله ورود:
1️⃣ ارسال /start
2️⃣ حل کپچا
3️⃣ عضویت در کانال
4️⃣ ورود به منوی اصلی

🎁 دعوت دوستان:
⭐ هر دعوت موفق = 0.N استارز
⚠️ هر کاربر فقط یک‌بار حساب می‌شود

💰 انتقال موجودی:
🔹 فقط آیدی عددی
🔹 نیاز به موجودی کافی

⭐ برداشت استارز:
🔹 بررسی توسط ادمین
🔹 ارسال به کانال سفارشات
🔹برای برداشت انتقال استارز فقط از اعداد صحیح بدون اعشار استفاده کنید
❌ تقلب باعث مسدودی می‌شود

📞 پشتیبانی از منوی ربات
""",
        reply_markup=main_menu()
    )

# ================= پشتیبانی =================
@bot.message_handler(func=lambda m: m.text == "📞 پشتیبانی")
def support(message):
    bot.send_message(message.chat.id, f"📞 پشتیبانی:\n{SUPPORT_ID}")
    
    
#===== راهنمایی داخل گروه ===
@bot.message_handler(commands=["help_transfer"])
def help_transfer(message):
    bot.send_message(
        message.chat.id,
        """
💸 انتقال داخل گروه

1️⃣ روی پیام کاربر ریپلای کن
2️⃣ بنویس:
انتقال 1

⚠️ فقط در گروه رسمی
⚠️ فقط کاربران ثبت‌نام‌شده
⏳ محدودیت زمانی برای ضد اسپم
"""
    )
    
#===== انتقال در گروه===
@bot.message_handler(
    func=lambda m: (
        m.chat.type in ["group", "supergroup"]
        and m.chat.id == TRANSFER_GROUP_ID
        and m.reply_to_message
        and m.text
        and m.text.startswith("انتقال")
    )
)
def group_transfer(message):
    sender_user = message.from_user
    receiver_user = message.reply_to_message.from_user
    sender = sender_user.id
    receiver = receiver_user.id

    if sender == receiver:
        bot.reply_to(message, "❌ نمی‌تونی به خودت انتقال بدی")
        return

    cur.execute("SELECT balance, last_transfer FROM users WHERE user_id=?", (sender,))
    s = cur.fetchone()
    cur.execute("SELECT user_id FROM users WHERE user_id=?", (receiver,))
    r = cur.fetchone()

    if not s or not r:
        bot.reply_to(message, "❌ هر دو کاربر باید ربات را start کرده باشند")
        return

    now = int(time.time())
    if now - s[1] < TRANSFER_COOLDOWN:
        bot.reply_to(
            message,
            f"⏳ لطفاً {TRANSFER_COOLDOWN} ثانیه بین انتقال‌ها صبر کن"
        )
        return

    try:
        amount = int(message.text.split()[1])
        if amount <= 0:
            raise ValueError
    except:
        bot.reply_to(message, "❌ فرمت صحیح: انتقال 5")
        return

    if s[0] < amount:
        bot.reply_to(
            message,
            f"❌ موجودی کافی نیست\n💰 موجودی شما: {s[0]}"
        )
        return

    # انتقال
    cur.execute(
        "UPDATE users SET balance=balance-?, last_transfer=? WHERE user_id=?",
        (amount, now, sender)
    )
    cur.execute(
        "UPDATE users SET balance=balance+? WHERE user_id=?",
        (amount, receiver)
    )
    db.commit()

    group_text = f"""
💰 مقدار {amount} STARS  
👤 از: {user_tag(sender_user)} (ID: {sender})  
👤 به: {user_tag(receiver_user)} (ID: {receiver})  

✅ انتقال با موفقیت انجام شد
❤️‍🔥 @FreeStarsxbot ❤️‍🔥
"""

    bot.reply_to(message, group_text)

    # نوتیف خصوصی
    try:
        bot.send_message(
            sender,
            f"✅ شما {amount} STARS به {user_tag(receiver_user)} انتقال دادید"
        )
    except:
        pass

    try:
        bot.send_message(
            receiver,
            f"🎉 {user_tag(sender_user)} مقدار {amount} STARS به شما انتقال داد"
        )
    except:
        pass
        
#=====انتقال موجودی =====
@bot.message_handler(func=lambda m: m.text == "💰 انتقال موجودی")
def transfer_start(message):
    msg = bot.send_message(
        message.chat.id,
        "🆔 آیدی عددی مقصد را بفرست",
        reply_markup=back_menu()
    )
    bot.register_next_step_handler(msg, get_target)
def get_target(message):

    # 🔙 برگشت
    if message.text == "🔙 برگشت":
        bot.send_message(
            message.chat.id,
            "🔙 برگشتی به منوی اصلی",
            reply_markup=main_menu()
        )
        return

    if not message.text.isdigit():
        msg = bot.send_message(
            message.chat.id,
            "❌ آیدی نامعتبره، فقط عدد بفرست",
            reply_markup=back_menu()
        )
        bot.register_next_step_handler(msg, get_target)
        return

    target = int(message.text)

    cur.execute("SELECT user_id FROM users WHERE user_id=?", (target,))
    if not cur.fetchone():
        msg = bot.send_message(
            message.chat.id,
            "❌ این کاربر وجود ندارد",
            reply_markup=back_menu()
        )
        bot.register_next_step_handler(msg, get_target)
        return

    transfer_state[message.from_user.id] = {"target": target}

    msg = bot.send_message(
        message.chat.id,
        "💰 مقدار انتقال را بفرست",
        reply_markup=back_menu()
    )
    bot.register_next_step_handler(msg, transfer_amount) 
def transfer_amount(message):

    # 🔙 برگشت
    if message.text == "🔙 برگشت":
        transfer_state.pop(message.from_user.id, None)
        bot.send_message(
            message.chat.id,
            "🔙 برگشتی به منوی اصلی",
            reply_markup=main_menu()
        )
        return

    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError
    except:
        msg = bot.send_message(
            message.chat.id,
            "❌ مبلغ نامعتبره",
            reply_markup=back_menu()
        )
        bot.register_next_step_handler(msg, transfer_amount)
        return

    uid = message.from_user.id
    target = transfer_state.get(uid, {}).get("target")

    if not target:
        bot.send_message(message.chat.id, "❌ خطا در انتقال", reply_markup=main_menu())
        return

    cur.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    bal = cur.fetchone()[0]

    if bal < amount:
        bot.send_message(
            message.chat.id,
            "❌ موجودی کافی نیست",
            reply_markup=main_menu()
        )
        return

    # انجام انتقال
    cur.execute(
        "UPDATE users SET balance=balance-?, transfer_count=transfer_count+1 WHERE user_id=?",
        (amount, uid)
    )
    cur.execute(
        "UPDATE users SET balance=balance+? WHERE user_id=?",
        (amount, target)
    )
    db.commit()

    transfer_state.pop(uid, None)

    bot.send_message(
        message.chat.id,
        "✅ انتقال با موفقیت انجام شد",
        reply_markup=main_menu()
    )
#====برداشت====
@bot.message_handler(func=lambda m: m.text == "⭐ برداشت استارز")
def withdraw_start(message):
    uid = message.from_user.id
    now = int(time.time())

    cur.execute(
        "SELECT balance, last_withdraw FROM users WHERE user_id=?",
        (uid,)
    )
    row = cur.fetchone()

    if not row:
        bot.send_message(message.chat.id, "❌ ابتدا /start را بزن")
        return

    balance, last_withdraw = row

    if balance <= 0:
        bot.send_message(
            message.chat.id,
            "❌ موجودی شما صفر است",
            reply_markup=main_menu()
        )
        return

    if now - last_withdraw < WITHDRAW_COOLDOWN:
        remain = WITHDRAW_COOLDOWN - (now - last_withdraw)
        bot.send_message(
            message.chat.id,
            f"⏳ هر ۱ ساعت فقط یک برداشت مجاز است\n"
            f"⏱ زمان باقی‌مانده: {remain // 60} دقیقه",
            reply_markup=main_menu()
        )
        return

    msg = bot.send_message(
        message.chat.id,
        f"💰 موجودی شما: {balance}\n\n"
        "📤 مقدار برداشت را ارسال کن (عدد صحیح):",
        reply_markup=back_menu()
    )
    bot.register_next_step_handler(msg, withdraw_get_amount)
def withdraw_get_amount(message):
    uid = message.from_user.id

    if message.text == "🔙 برگشت":
        bot.send_message(message.chat.id, "لغو شد", reply_markup=main_menu())
        return

    try:
        amount = int(message.text)
        if amount <= 0:
            raise ValueError
    except:
        msg = bot.send_message(
            message.chat.id,
            "❌ مقدار باید عدد صحیح باشد",
            reply_markup=back_menu()
        )
        bot.register_next_step_handler(msg, withdraw_get_amount)
        return

    cur.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    balance = cur.fetchone()[0]

    if amount > balance:
        bot.send_message(
            message.chat.id,
            "❌ موجودی کافی نیست",
            reply_markup=main_menu()
        )
        return

    withdraw_requests[uid] = {"amount": amount}

    msg = bot.send_message(
        message.chat.id,
        "🔗 لینک پست یا توضیح پرداخت را ارسال کن:",
        reply_markup=back_menu()
    )
    bot.register_next_step_handler(msg, withdraw_get_link)
def withdraw_get_link(message):
    uid = message.from_user.id

    if uid not in withdraw_requests:
        bot.send_message(message.chat.id, "❌ خطا، دوباره تلاش کن", reply_markup=main_menu())
        return

    if message.text == "🔙 برگشت":
        withdraw_requests.pop(uid, None)
        bot.send_message(message.chat.id, "لغو شد", reply_markup=main_menu())
        return

    amount = withdraw_requests[uid]["amount"]
    link = message.text
    now = int(time.time())

    cur.execute(
        "UPDATE users SET last_withdraw=? WHERE user_id=?",
        (now, uid)
    )
    db.commit()

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✅ تأیید", callback_data=f"wd_ok_{uid}_{amount}"),
        InlineKeyboardButton("❌ رد", callback_data=f"wd_no_{uid}_{amount}")
    )

    bot.send_message(
        ORDERS_CHANNEL,
        f"""📤 درخواست برداشت جدید

🆔 آیدی کاربر: {uid}
⭐ مقدار: {amount}

🔗 توضیح / لینک:
{link}
""",
        reply_markup=kb
    )

    bot.send_message(
        message.chat.id,
        "✅ درخواست برداشت ثبت شد\n⏳ منتظر تأیید ادمین باشید",
        reply_markup=main_menu()
    )

    withdraw_requests.pop(uid, None)
@bot.callback_query_handler(func=lambda c: c.data.startswith("wd_ok_"))
def approve_withdraw(c):
    if not is_admin(c.from_user.id):
        bot.answer_callback_query(c.id, "⛔ دسترسی نداری", show_alert=True)
        return

    _, _, uid, amount = c.data.split("_")
    uid = int(uid)
    amount = int(amount)

    cur.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    balance = cur.fetchone()[0]

    if balance < amount:
        bot.edit_message_text(
            "❌ موجودی کاربر کافی نیست",
            c.message.chat.id,
            c.message.message_id
        )
        return

    cur.execute(
        "UPDATE users SET balance=balance-? WHERE user_id=?",
        (amount, uid)
    )
    db.commit()

    bot.edit_message_text(
        "✅ برداشت تأیید شد",
        c.message.chat.id,
        c.message.message_id
    )

    bot.send_message(uid, f"🎉 برداشت شما تأیید شد\n⭐ مقدار: {amount}")
@bot.callback_query_handler(func=lambda c: c.data.startswith("wd_no_"))
def reject_withdraw(c):
    if not is_admin(c.from_user.id):
        bot.answer_callback_query(c.id, "⛔ دسترسی نداری", show_alert=True)
        return

    _, _, uid, amount = c.data.split("_")

    bot.edit_message_text(
        "❌ برداشت رد شد",
        c.message.chat.id,
        c.message.message_id
    )

    bot.send_message(
        int(uid),
        f"❌ برداشت شما رد شد\n⭐ مقدار: {amount}"
    )
    
# ================= دعوت دوستان =================
@bot.message_handler(func=lambda m: m.text == "🎁 دعوت دوستان")
def invite_friends(message):
    uid = message.from_user.id
    link = f"https://t.me/{bot.get_me().username}?start={uid}"
    reward = get_invite_reward()

    bot.send_message(
        message.chat.id,
        f"""
🎁 دعوت دوستان

⭐ هر دعوت موفق = {reward} استارز
⚠️ هر کاربر فقط یک‌بار حساب می‌شود

🔗 لینک دعوت شما:
{link}
""",
        reply_markup=main_menu()
    )

@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if not is_admin(message.from_user.id):
        return

    bot.send_message(
    message.chat.id,
    "👑 پنل ادمین\n\n"
    "/stats – آمار ربات\n"
    "/users – لیست کاربران\n"
    "/user ID – اطلاعات کاربر\n"
    "/addadmin ID – افزودن ادمین\n"
    "/deladmin ID – حذف ادمین\n"
    "/addchannel @id – افزودن کانال\n"
    "/delchannel @id – حذف کانال\n"
    "/broadcast – پیام همگانی\n"
    "/invite_reward VALUE – تنظیم هدیه دعوت\n"
    "/off – خاموش ربات\n"
    "/on – روشن ربات"
)
    
#=====ادمین====
@bot.message_handler(commands=["addadmin"])
def add_admin_cmd(message):
    if message.from_user.id != OWNER_ID:
        return

    try:
        uid = int(message.text.split()[1])
        if uid not in ADMINS:
            ADMINS.append(uid)
            bot.send_message(message.chat.id, f"✅ ادمین اضافه شد\n🆔 {uid}")
        else:
            bot.send_message(message.chat.id, "⚠️ این کاربر از قبل ادمین است")
    except:
        bot.send_message(message.chat.id, "❌ مثال صحیح:\n/addadmin 123456789")
@bot.message_handler(commands=["deladmin"])
def del_admin_cmd(message):
    if message.from_user.id != OWNER_ID:
        return

    try:
        uid = int(message.text.split()[1])
        if uid in ADMINS:
            ADMINS.remove(uid)
            bot.send_message(message.chat.id, f"🗑 ادمین حذف شد\n🆔 {uid}")
        else:
            bot.send_message(message.chat.id, "❌ این کاربر ادمین نیست")
    except:
        bot.send_message(message.chat.id, "❌ مثال صحیح:\n/deladmin 123456789")

#====جایزه دعوت=====
@bot.message_handler(commands=["invite_reward"])
def set_invite_reward(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "⛔ دسترسی نداری")
        return

    parts = message.text.split()

    if len(parts) == 1:
        current = get_invite_reward()
        bot.send_message(
            message.chat.id,
            f"📊 مقدار فعلی هدیه دعوت:\n⭐ {current} استارز\n\n"
            "✏️ تغییر:\n/invite_reward 0.1"
        )
        return

    try:
        value = float(parts[1])
        if value <= 0:
            raise ValueError
    except:
        bot.send_message(message.chat.id, "❌ مقدار نامعتبر")
        return

    cur.execute(
        "UPDATE settings SET value=? WHERE key='invite_reward'",
        (str(value),)
    )
    db.commit()

    bot.send_message(
        message.chat.id,
        f"✅ هدیه دعوت تنظیم شد\n⭐ هر دعوت = {value} استارز"
    )
#===== چنل =====
@bot.message_handler(commands=["addchannel"])
def add_channel_cmd(message):
    if not is_admin(message.from_user.id):
        return

    try:
        ch = message.text.split()[1]
        if not ch.startswith("@"):
            bot.send_message(message.chat.id, "❌ آیدی کانال باید با @ شروع شود")
            return

        if ch not in CHANNELS:
            CHANNELS.append(ch)
            bot.send_message(message.chat.id, f"✅ کانال {ch} اضافه شد")
        else:
            bot.send_message(message.chat.id, "⚠️ این کانال قبلاً اضافه شده")
    except:
        bot.send_message(message.chat.id, "❌ مثال:\n/addchannel @channel")
@bot.message_handler(commands=["delchannel"])
def del_channel_cmd(message):
    if not is_admin(message.from_user.id):
        return

    try:
        ch = message.text.split()[1]
        if ch in CHANNELS:
            CHANNELS.remove(ch)
            bot.send_message(message.chat.id, f"🗑 کانال {ch} حذف شد")
        else:
            bot.send_message(message.chat.id, "❌ کانال پیدا نشد")
    except:
        bot.send_message(message.chat.id, "❌ مثال:\n/delchannel @channel")
@bot.message_handler(commands=["channels"])
def list_channels_cmd(message):
    if not is_admin(message.from_user.id):
        return

    if not CHANNELS:
        bot.send_message(message.chat.id, "📡 کانالی ثبت نشده")
        return

    text = "📡 کانال‌های اجباری:\n\n"
    for ch in CHANNELS:
        text += f"• {ch}\n"

    bot.send_message(message.chat.id, text)
    
    
#==== پیام همگانی =====
broadcast_state = {}

@bot.message_handler(commands=["bc"])
def broadcast_start(message):
    if not is_admin(message.from_user.id):
        return

    broadcast_state[message.from_user.id] = True
    bot.send_message(message.chat.id, "✉️ پیام همگانی را ارسال کن")
@bot.message_handler(func=lambda m: broadcast_state.get(m.from_user.id))
def send_broadcast(message):
    if not is_admin(message.from_user.id):
        return

    cur.execute("SELECT user_id FROM users")
    users = cur.fetchall()

    sent = 0
    for (uid,) in users:
        try:
            bot.send_message(uid, message.text)
            sent += 1
        except:
            pass

    broadcast_state.pop(message.from_user.id, None)
    bot.send_message(
        message.chat.id,
        f"✅ پیام همگانی ارسال شد\n👥 تعداد: {sent}"
    )
    
#=====آمار=====
@bot.message_handler(commands=["stats"])
def admin_stats(message):
    if not is_admin(message.from_user.id):
        return

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    week = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    month = (now - timedelta(days=30)).strftime("%Y-%m-%d")

    # کل کاربران
    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]

    # کاربران جدید امروز
    cur.execute("SELECT COUNT(*) FROM users WHERE join_date=?", (today,))
    new_today = cur.fetchone()[0]

    # فعال امروز
    cur.execute("SELECT COUNT(*) FROM users WHERE last_active LIKE ?", (f"{today}%",))
    active_today = cur.fetchone()[0]

    # فعال 7 روز اخیر
    cur.execute("SELECT COUNT(*) FROM users WHERE last_active >= ?", (week,))
    active_week = cur.fetchone()[0]

    # فعال 30 روز اخیر
    cur.execute("SELECT COUNT(*) FROM users WHERE last_active >= ?", (month,))
    active_month = cur.fetchone()[0]

    bot.send_message(
        message.chat.id,
        f"""
📊 آمار حرفه‌ای ربات

👥 کل کاربران: {total}
🆕 ثبت‌نام امروز: {new_today}

✅ فعال امروز: {active_today}
📆 فعال ۷ روز اخیر: {active_week}
📅 فعال ۳۰ روز اخیر: {active_month}
"""
    )
    
@bot.message_handler(commands=["off"])
def bot_off(message):
    global BOT_ACTIVE

    if message.from_user.id != OWNER_ID:
        return

    BOT_ACTIVE = False
    bot.send_message(message.chat.id, "🔴 ربات خاموش شد")
    
@bot.message_handler(commands=["on"])
def bot_on(message):
    global BOT_ACTIVE

    if message.from_user.id != OWNER_ID:
        return

    BOT_ACTIVE = True
    bot.send_message(message.chat.id, "🟢 ربات فعال شد")
    
@bot.message_handler(func=lambda m: not BOT_ACTIVE)
def off_message(message):
    if message.from_user.id != OWNER_ID:
        bot.send_message(message.chat.id, "⛔ ربات موقتاً خاموش است")
        
@bot.message_handler(commands=["users"])
def list_users(message):
    if not is_admin(message.from_user.id):
        return

    cur.execute("SELECT user_id FROM users ORDER BY join_date DESC LIMIT 50")
    rows = cur.fetchall()

    if not rows:
        bot.send_message(message.chat.id, "❌ کاربری وجود ندارد")
        return

    kb = InlineKeyboardMarkup()
    for (uid,) in rows:
        kb.add(InlineKeyboardButton(f"👤 {uid}", callback_data=f"user_{uid}"))

    bot.send_message(
        message.chat.id,
        "👥 لیست کاربران (۵۰ نفر آخر):",
        reply_markup=kb
    )
@bot.callback_query_handler(func=lambda c: c.data.startswith("user_"))
def show_user(c):
    if not is_admin(c.from_user.id):
        return

    uid = int(c.data.split("_")[1])

    cur.execute("""
    SELECT balance, join_date, invite_count, transfer_count, order_count
    FROM users WHERE user_id=?
    """, (uid,))
    u = cur.fetchone()

    if not u:
        bot.answer_callback_query(c.id, "❌ کاربر یافت نشد", show_alert=True)
        return

    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("➕ افزایش موجودی", callback_data=f"addbal_{uid}"),
        InlineKeyboardButton("➖ کاهش موجودی", callback_data=f"minbal_{uid}")
    )
    kb.add(
        InlineKeyboardButton("✏️ تنظیم موجودی", callback_data=f"setbal_{uid}")
    )
    kb.add(
        InlineKeyboardButton("🗑 حذف کاربر", callback_data=f"deluser_{uid}")
    )

    bot.edit_message_text(
        f"""
👤 اطلاعات کاربر

🆔 {uid}
⭐ موجودی: {u[0]}
📅 عضویت: {u[1]}
👥 دعوت‌ها: {u[2]}
🔁 انتقال‌ها: {u[3]}
🛒 برداشت‌ها: {u[4]}
""",
        c.message.chat.id,
        c.message.message_id,
        reply_markup=kb
    )
@bot.callback_query_handler(func=lambda c: c.data.startswith(("addbal_", "minbal_", "setbal_")))
def balance_action(c):
    if not is_admin(c.from_user.id):
        return

    action, uid = c.data.split("_")
    admin_steps[c.from_user.id] = (action, int(uid))

    bot.send_message(
        c.from_user.id,
        "💰 مقدار را ارسال کن:"
    )
@bot.message_handler(func=lambda m: m.from_user.id in admin_steps)
def apply_balance_change(message):
    if not is_admin(message.from_user.id):
        return

    try:
        amount = float(message.text)
    except:
        bot.send_message(message.chat.id, "❌ فقط عدد بفرست")
        return

    action, uid = admin_steps.pop(message.from_user.id)

    if action == "addbal":
        cur.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (amount, uid))

    elif action == "minbal":
        cur.execute("UPDATE users SET balance=balance-? WHERE user_id=?", (amount, uid))

    elif action == "setbal":
        cur.execute("UPDATE users SET balance=? WHERE user_id=?", (amount, uid))

    db.commit()

    bot.send_message(
        message.chat.id,
        f"✅ موجودی کاربر {uid} بروزرسانی شد"
    )
@bot.callback_query_handler(func=lambda c: c.data.startswith("deluser_"))
def delete_user(c):
    if not is_admin(c.from_user.id):
        return

    uid = int(c.data.split("_")[1])

    cur.execute("DELETE FROM users WHERE user_id=?", (uid,))
    db.commit()

    bot.answer_callback_query(c.id, "🗑 کاربر حذف شد")
    bot.edit_message_text("✅ کاربر حذف شد", c.message.chat.id, c.message.message_id)
#====گروه====
@bot.message_handler(commands=["setgroup"])
def set_transfer_group(message):
    if not is_admin(message.from_user.id):
        return

    if message.chat.type not in ["group", "supergroup"]:
        bot.send_message(message.chat.id, "❌ این دستور فقط داخل گروه اجرا می‌شود")
        return

    global TRANSFER_GROUP_ID
    TRANSFER_GROUP_ID = message.chat.id

    bot.send_message(
        message.chat.id,
        f"✅ این گروه به عنوان گروه انتقال ثبت شد\n🆔 {TRANSFER_GROUP_ID}"
    )

# ===== اجرا =====
print("🤖 Bot is running...")
bot.infinity_polling()
