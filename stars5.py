from telebot import TeleBot, types
import sqlite3, random
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

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

bot = TeleBot(TOKEN)

# ================= دیتابیس =================
db = sqlite3.connect("bot.db", check_same_thread=False)
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

# ================= متغیرها =================
transfer_state = {}
withdraw_state = {}
admin_steps = {}
INVITE_REWARD = 0.5
BOT_ACTIVE = True

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
    cur.execute("ALTER TABLE users ADD COLUMN last_active TEXT")
    db.commit()
    print("✅ ستون last_active اضافه شد")
except sqlite3.OperationalError:
    print("ℹ️ ستون last_active از قبل وجود دارد")

    
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
    inviter = cur.fetchone()[0]

    if inviter:
        cur.execute(
            "UPDATE users SET balance=balance+0.5, invite_count=invite_count+1 WHERE user_id=?",
            (inviter,)
        )
        cur.execute("UPDATE users SET inviter=NULL WHERE user_id=?", (uid,))
        db.commit()
        try:
            bot.send_message(inviter, "🎉 یک دعوت موفق داشتی\n⭐ 0.5 استارز گرفتی")
        except:
            pass

    if not check_channels(uid):
        bot.send_message(message.chat.id, "📢 عضو کانال شو", reply_markup=join_keyboard())
        return

    bot.send_message(message.chat.id, "✅ ورود موفق", reply_markup=main_menu())

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
⭐ موجودی: {u[0]}
👥 دعوت‌ها: {u[2]}
🔁 انتقال‌ها: {u[3]}
🛒 برداشت‌ها: {u[4]}
""")

# ================= برداشت =================
@bot.message_handler(func=lambda m: m.text == "⭐ برداشت استارز")
def withdraw_start(message):
    msg = bot.send_message(
        message.chat.id,
        "💰 مقدار برداشت را بفرست",
        reply_markup=back_menu()
    )
    bot.register_next_step_handler(msg, withdraw_amount)
def withdraw_amount(message):

    if message.text == "🔙 برگشت":
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
            "❌ مقدار نامعتبره، عدد صحیح بفرست",
            reply_markup=back_menu()
        )
        bot.register_next_step_handler(msg, withdraw_amount)
        return

    uid = message.from_user.id

    cur.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()

    if not row or row[0] < amount:
        bot.send_message(
            message.chat.id,
            "❌ موجودی کافی نیست",
            reply_markup=main_menu()
        )
        return

    # ذخیره مقدار
    withdraw_state[uid] = {"amount": amount}

    msg = bot.send_message(
        message.chat.id,
        "🔗 حالا لینک پست را بفرست",
        reply_markup=back_menu()
    )
    bot.register_next_step_handler(msg, withdraw_link)
def withdraw_link(message):

    if message.text == "🔙 برگشت":
        withdraw_state.pop(message.from_user.id, None)
        bot.send_message(
            message.chat.id,
            "🔙 برگشتی به منوی اصلی",
            reply_markup=main_menu()
        )
        return

    link = message.text.strip()
    uid = message.from_user.id

    if not link.startswith("http"):
        msg = bot.send_message(
            message.chat.id,
            "❌ لینک نامعتبره، لینک صحیح بفرست",
            reply_markup=back_menu()
        )
        bot.register_next_step_handler(msg, withdraw_link)
        return

    data = withdraw_state.get(uid)
    if not data:
        bot.send_message(message.chat.id, "❌ خطا در ثبت برداشت", reply_markup=main_menu())
        return

    amount = data["amount"]

    # کسر موجودی
    cur.execute(
        "UPDATE users SET balance = balance - ?, order_count = order_count + 1 WHERE user_id=?",
        (amount, uid)
    )
    db.commit()

    withdraw_state.pop(uid, None)

    # دکمه‌های ادمین
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✅ انجام شد", callback_data=f"ok_{uid}_{amount}"),
        InlineKeyboardButton("❌ انجام نشد", callback_data=f"no_{uid}_{amount}")
    )

    bot.send_message(
        ORDERS_CHANNEL,
        f"""
📥 سفارش برداشت جدید

👤 آیدی: `{uid}`
💰 مقدار: `{amount}`
🔗 لینک پست:
{link}
""",
        parse_mode="Markdown",
        reply_markup=kb
    )

    bot.send_message(
        message.chat.id,
        "✅ درخواست برداشت ثبت شد و برای بررسی ارسال شد",
        reply_markup=main_menu()
    )
@bot.callback_query_handler(func=lambda c: c.data.startswith(("ok_", "no_")))
def admin_order_action(call):

    data = call.data.split("_")
    action = data[0]      # ok یا no
    uid = int(data[1])    # آیدی کاربر
    amount = float(data[2])

    # فقط ادمین اجازه دارد
    if call.from_user.id != OWNER_ID:
        bot.answer_callback_query(call.id, "⛔ دسترسی نداری", show_alert=True)
        return

    # ✅ انجام شد
    if action == "ok":
        bot.edit_message_text(
            call.message.text + "\n\n✅ وضعیت: انجام شد",
            call.message.chat.id,
            call.message.message_id
        )

        try:
            bot.send_message(uid, "✅ برداشت شما با موفقیت انجام شد 🎉")
        except:
            pass

    # ❌ انجام نشد → برگشت موجودی
    elif action == "no":

        cur.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id=?",
            (amount, uid)
        )
        db.commit()

        bot.edit_message_text(
            call.message.text + "\n\n❌ وضعیت: رد شد (موجودی برگشت داده شد)",
            call.message.chat.id,
            call.message.message_id
        )

        try:
            bot.send_message(
                uid,
                f"❌ برداشت شما رد شد\n💰 مقدار {amount} به موجودی شما برگشت داده شد"
            )
        except:
            pass

    bot.answer_callback_query(call.id)
# ================= مدیریت سفارش =================
@bot.callback_query_handler(func=lambda c: c.data.startswith(("done_", "reject_", "refund_")))
def order_actions(call):
    if call.from_user.id != OWNER_ID:
        return

    action, uid, amount = call.data.split("_")
    uid = int(uid)
    amount = float(amount)

    if action in ["reject", "refund"]:
        cur.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (amount, uid))
        db.commit()

    bot.edit_message_text(
        f"📌 وضعیت: {action}\n👤 {uid}\n⭐ {amount}",
        call.message.chat.id,
        call.message.message_id
    )

    try:
        bot.send_message(uid, f"📌 وضعیت برداشت: {action}")
    except:
        pass

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
⭐ هر دعوت موفق = 0.5 استارز
⚠️ هر کاربر فقط یک‌بار حساب می‌شود

💰 انتقال موجودی:
🔹 فقط آیدی عددی
🔹 نیاز به موجودی کافی

⭐ برداشت استارز:
🔹 بررسی توسط ادمین
🔹 ارسال به کانال سفارشات

❌ تقلب باعث مسدودی می‌شود

📞 پشتیبانی از منوی ربات
""",
        reply_markup=main_menu()
    )

# ================= پشتیبانی =================
@bot.message_handler(func=lambda m: m.text == "📞 پشتیبانی")
def support(message):
    bot.send_message(message.chat.id, f"📞 پشتیبانی:\n{SUPPORT_ID}")
    
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

# ================= دعوت دوستان =================
@bot.message_handler(func=lambda m: m.text == "🎁 دعوت دوستان")
def invite_friends(message):
    uid = message.from_user.id
    link = f"https://t.me/{bot.get_me().username}?start={uid}"

    bot.send_message(
        message.chat.id,
        f"""
🎁 دعوت دوستان

⭐ هر دعوت موفق = {INVITE_REWARD} استارز
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

# ===== اجرا =====
print("🤖 Bot is running...")
bot.infinity_polling()
