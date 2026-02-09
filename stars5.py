# -*- coding: utf-8 -*-

from telebot import TeleBot, types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3, os, time, re, random
from datetime import datetime
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta
import sqlite3
from telebot import types
# ================== تنظیمات ==================

TOKEN = "8277024183:AAHivVlZVU0WjvaEziprI9W-zmD9H8ndWP4"

SUPPORT_ID = "@im_Xo2"
ORDERS_CHANNEL = -1003595070275
CHANNELS = ["@stars_freex"]

TASK_CHANNEL_ID = -1003804837780

TRANSFER_GROUP_ID = -1003529474317
TRANSFER_COOLDOWN = 15
WITHDRAW_COOLDOWN = 3600

OWNER_ID = 8589848955
ADMINS = [111111111, 222222222]

POINTS_PER_INVITE = 1
POINTS_TO_STAR = 10

BOT_ACTIVE = True

# ================== Flask ==================

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_web():
    app.run(host="0.0.0.0", port=8080)

Thread(target=run_web, daemon=True).start()

# ================== ربات ==================

bot = TeleBot(TOKEN, parse_mode="HTML")

# ================== دیتابیس ==================


# ================== توابع کمکی ==================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "bot.db")

db = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = db.cursor()

# ================= USERS =================
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance REAL DEFAULT 0,
    points INTEGER DEFAULT 0,
    join_date TEXT,
    last_active TEXT,
    invite_count INTEGER DEFAULT 0,
    transfer_count INTEGER DEFAULT 0,
    order_count INTEGER DEFAULT 0,
    invited_by INTEGER,
    last_transfer INTEGER DEFAULT 0,
    last_withdraw INTEGER DEFAULT 0,
    captcha_passed INTEGER DEFAULT 0
)
""")

# ================= SETTINGS =================
cur.execute("""
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
)
""")

cur.execute("""
INSERT OR IGNORE INTO settings (key, value)
VALUES ('invite_reward', '1')
""")

# ================= TASKS =================
cur.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    link TEXT,
    reward INTEGER NOT NULL,
    daily INTEGER DEFAULT 0,
    active INTEGER DEFAULT 1
)
""")
cur.execute("""
SELECT user_id, invite_count
FROM users
ORDER BY invite_count DESC
LIMIT 10
""")
top_users = cur.fetchall()

# ================= TASK REQUESTS (SHOTS) =================
cur.execute("""
CREATE TABLE IF NOT EXISTS task_requests (
    user_id INTEGER,
    task_id INTEGER,
    photo_id TEXT,
    status TEXT DEFAULT 'pending', -- pending / approved / rejected
    created_at TEXT,
    PRIMARY KEY (user_id, task_id)
)
""")
cur.execute("""
UPDATE users
SET invite_count = invite_count + 1
WHERE user_id = ?
""", (inviter_id,))
db.commit()

db.commit()
def is_admin(uid):
    return uid == OWNER_ID or uid in ADMINS

def admin_only(message, *, allow_when_off=True, private_only=False):
    uid = message.from_user.id

    if not is_admin(uid):
        return False

    if private_only and message.chat.type != "private":
        bot.send_message(message.chat.id, "این دستور فقط در پیوی قابل اجراست")
        return False

    if not BOT_ACTIVE and not allow_when_off:
        bot.send_message(message.chat.id, "ربات خاموش است")
        return False

    return True

def user_tag(user):
    return f"@{user.username}" if user.username else user.first_name

def remove_emojis(text):
    emoji_pattern = re.compile(
        "[\U0001F300-\U0001FAFF\U00002600-\U000027BF]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub("", text)

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = [i[0] for i in c.fetchall()]
    conn.close()
    return users
def get_users(limit, offset):
    conn = sqlite3.connect("data.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT user_id, username, score
        FROM users
        ORDER BY score DESC
        LIMIT ? OFFSET ?
    """, (limit, offset))

    users = cur.fetchall()
    conn.close()
    return users
    
def init_db():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    
cur.execute("""
def init_db():
    conn = sqlite3.connect("data.db", check_same_thread=False)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS task_requests (
        user_id INTEGER,
        task_id INTEGER,
        photo_id TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, task_id),
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (task_id) REFERENCES tasks(id)
    )
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_task_requests_status
    ON task_requests(status)
    """)

    conn.commit()
    conn.close()
    
# ================== متغیرهای حالت ==================
init_db()
transfer_state = {}
withdraw_requests = {}
admin_steps = {}
convert_state = {}
broadcast_data = {}
USERS_PER_PAGE = 50
WHERE invite_count > 0
# ================= منو =================

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("🆔حساب کاربری")
    kb.add("⭐ برداشت استارز", "🎁 دعوت دوستان")
    kb.add("🔄 تبدیل امتیاز به استارز")
    kb.add("📘 راهنما", "📞 پشتیبانی")
    kb.add("🧩 تسک‌ها")
    return kb

# ================= بررسی عضویت =================

def check_channels(uid):
    for ch in CHANNELS:
        try:
            status = bot.get_chat_member(ch, uid).status
            if status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def join_keyboard():
    kb = InlineKeyboardMarkup()
    for ch in CHANNELS:
        kb.add(
            InlineKeyboardButton(
                "عضویت در کانال",
                url=f"https://t.me/{ch.replace('@','')}"
            )
        )
    kb.add(InlineKeyboardButton("بررسی عضویت", callback_data="check_join"))
    return kb

@bot.callback_query_handler(func=lambda c: c.data == "check_join")
def recheck_join(c):
    uid = c.from_user.id

    if check_channels(uid):
        bot.edit_message_text(
            "عضویت تایید شد",
            c.message.chat.id,
            c.message.message_id
        )
        bot.send_message(
            c.message.chat.id,
            "خوش آمدی",
            reply_markup=main_menu()
        )
    else:
        bot.answer_callback_query(c.id, "هنوز عضو کانال نیستی", show_alert=True)

# ================= کپچا =================

captcha = {}

def send_captcha(message):
    code = str(random.randint(1000, 9999))
    captcha[message.from_user.id] = code

    bot.send_message(
        message.chat.id,
        f"کد امنیتی را ارسال کن:\n{code}"
    )

@bot.message_handler(func=lambda m: m.from_user.id in captcha)
def check_captcha(message):
    uid = message.from_user.id

    if message.text != captcha.get(uid):
        bot.send_message(message.chat.id, "کد اشتباه است")
        return

    captcha.pop(uid)

    # ثبت عبور از کپچا
    cur.execute(
        "UPDATE users SET captcha_passed=1 WHERE user_id=?",
        (uid,)
    )
    db.commit()

    # ===== جایزه دعوت (فقط یک‌بار) =====
    cur.execute(
        "SELECT invited_by FROM users WHERE user_id=?",
        (uid,)
    )
    row = cur.fetchone()
    invited_by = row[0]

    if invited_by:
        INVITE_POINTS = 1

        cur.execute("""
        UPDATE users
        SET points = points + ?,
            invite_count = invite_count + 1
        WHERE user_id=?
        """, (INVITE_POINTS, invited_by))

        # مهم: پاک کردن invited_by تا دیگه تکرار نشه
        cur.execute(
            "UPDATE users SET invited_by=NULL WHERE user_id=?",
            (uid,)
        )
        db.commit()

        try:
            bot.send_message(
                invited_by,
                f"یک دعوت موفق داشتی\n+{INVITE_POINTS} امتیاز"
            )
        except:
            pass

    # ===== بررسی عضویت =====
    if not check_channels(uid):
        bot.send_message(
            message.chat.id,
            "برای ادامه عضو کانال شو",
            reply_markup=join_keyboard()
        )
        return

    bot.send_message(
        message.chat.id,
        "ورود موفق",
        reply_markup=main_menu()
    )

# ================= /start =================

@bot.message_handler(commands=["start"])
def start(message):
    uid = message.from_user.id
    invited_by = None

    # لینک دعوت
    parts = message.text.split()
    if len(parts) > 1 and parts[1].isdigit():
        ref = int(parts[1])
        if ref != uid:
            invited_by = ref

    cur.execute(
        "SELECT captcha_passed FROM users WHERE user_id=?",
        (uid,)
    )
    user = cur.fetchone()

    # کاربر جدید
    if not user:
        cur.execute("""
        INSERT INTO users (user_id, join_date, invited_by)
        VALUES (?, ?, ?)
        """, (
            uid,
            datetime.now().strftime("%Y-%m-%d"),
            invited_by
        ))
        db.commit()

        send_captcha(message)
        return

    # کپچا رد نشده
    if user[0] == 0:
        send_captcha(message)
        return

    # عضو کانال نیست
    if not check_channels(uid):
        bot.send_message(
            message.chat.id,
            "برای ادامه عضو کانال شو",
            reply_markup=join_keyboard()
        )
        return

    # ورود مستقیم
    bot.send_message(
        message.chat.id,
        "خوش آمدی! از منوی پایین استفاده کن",
        reply_markup=main_menu()
    )
    
#==== پروفایل ===
@bot.message_handler(func=lambda m: m.text == "حساب کاربری")
def profile(message):
    uid = message.from_user.id

    cur.execute("""
    SELECT balance, points, join_date, invite_count, transfer_count, order_count
    FROM users WHERE user_id=?
    """, (uid,))
    u = cur.fetchone()

    if not u:
        bot.send_message(
            message.chat.id,
            "اطلاعات حساب پيدا نشد. دستور /start را ارسال کن"
        )
        return

    bot.send_message(
        message.chat.id,
        f"""
حساب کاربري

تاريخ عضويت: {u[2]}
استارز: {int(u[0])}
امتياز: {u[1]}
تعداد دعوت ها: {u[3]}
تعداد انتقال ها: {u[4]}
تعداد برداشت ها: {u[5]}
"""
    )
    
#==== راهنما ======  
@bot.message_handler(func=lambda m: m.text == "راهنما")
def help_handler(message):
    text = (
        "راهنمای استفاده از ربات\n\n"
        "خوش آمدی‌\n"
        "با این ربات می‌تونی امتیاز جمع کنی و به استارز تبدیلش کنی.\n\n"

        "مراحل شروع:\n"
        "1- ارسال /start\n"
        "2- حل کپچا\n"
        "3- عضویت در کانال\n"
        "4- فعال شدن منو\n\n"

        "امتیاز و استارز:\n"
        "- هر 10 امتیاز = 1 استارز\n"
        "- تبدیل از منوی «تبدیل امتیاز به استارز»\n\n"

        "انتقال امتیاز:\n"
        "- فقط داخل گپ مخصوص انتقال انجام می‌شود\n\n"

        "پشتیبانی:\n"
        "از بخش پشتیبانی پیام بده"
    )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=main_menu()
    )
#===== تبدیل امتیاز به استارز ====
@bot.message_handler(func=lambda m: m.text == "تبدیل امتیاز به استارز")
def start_convert(message):
    uid = message.from_user.id

    cur.execute(
        "SELECT points FROM users WHERE user_id=?",
        (uid,)
    )
    row = cur.fetchone()

    if not row or row[0] < 10:
        bot.send_message(
            message.chat.id,
            "حداقل ۱۰ امتیاز برای تبدیل لازم است",
            reply_markup=main_menu()
        )
        return

    convert_state[uid] = True

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(" لغو", callback_data="cancel_convert"))

    bot.send_message(
        message.chat.id,
        f"""
 تبدیل امتیاز به استارز

 امتیاز شما: {row[0]}

عدد مورد نظر را ارسال کن:
مثال: 10 / 20 / 30
(فقط مضرب ۱۰)
""",
        reply_markup=kb
    )
@bot.message_handler(func=lambda m: m.from_user.id in convert_state and m.text.isdigit())
def do_convert(message):
    uid = message.from_user.id
    amount = int(message.text)

    cur.execute(
        "SELECT points FROM users WHERE user_id=?",
        (uid,)
    )
    points = cur.fetchone()[0]

    # قوانین
    if amount < 10:
        bot.send_message(message.chat.id, "حداقل مقدار ۱۰ است")
        return

    if amount % 10 != 0:
        bot.send_message(message.chat.id, "فقط مضرب ۱۰ مجاز است")
        return

    if amount > points:
        bot.send_message(message.chat.id, "امتیاز کافی نیست")
        return

    stars = amount // 10

    cur.execute(
        """
        UPDATE users
        SET points = points - ?,
            balance = balance + ?
        WHERE user_id=?
        """,
        (amount, stars, uid)
    )
    db.commit()

    convert_state.pop(uid, None)

    bot.send_message(
        message.chat.id,
        f"""
 تبدیل با موفقیت انجام شد

 امتیاز کم شده: {amount}
 استارز اضافه شده: {stars}
""",
        reply_markup=main_menu()
    )
@bot.callback_query_handler(func=lambda c: c.data == "cancel_convert")
def cancel_convert(call):
    convert_state.pop(call.from_user.id, None)

    bot.edit_message_text(
        "عملیات تبدیل لغو شد",
        call.message.chat.id,
        call.message.message_id
    )

    bot.send_message(
        call.message.chat.id,
        "منوی اصلی",
        reply_markup=main_menu()
    )
    
#==== تسک =====
@bot.message_handler(func=lambda m: m.text == "تسک‌ها")
def show_tasks(message):
    cur.execute("SELECT id, title, reward FROM tasks WHERE active=1")
    rows = cur.fetchall()

    if not rows:
        bot.send_message(message.chat.id, "تسکی وجود ندارد")
        return

    kb = InlineKeyboardMarkup()
    for t in rows:
        kb.add(
            InlineKeyboardButton(
                f"{t[1]} |  {t[2]} امتیاز",
                callback_data=f"task_{t[0]}"
            )
        )

    bot.send_message(
        message.chat.id,
        " لیست تسک‌ها:",
        reply_markup=kb
    )
@bot.callback_query_handler(func=lambda c: c.data.startswith("task_"))
def task_detail(call):
    uid = call.from_user.id
    task_id = int(call.data.split("_")[1])

    #  قبلاً انجام داده؟
    cur.execute("""
    SELECT id FROM task_submits
    WHERE task_id=? AND user_id=? AND status='approved'
    """, (task_id, uid))

    if cur.fetchone():
        bot.answer_callback_query(
            call.id,
            " این تسک رو قبلاً انجام دادی",
            show_alert=True
        )
        return

    cur.execute(
        "SELECT title, description, link, reward FROM tasks WHERE id=?",
        (task_id,)
    )
    t = cur.fetchone()

    if not t:
        return

    task_state[uid] = task_id

    bot.send_message(
        call.message.chat.id,
        f" {t[0]}\n\n"
        f" {t[1]}\n"
        f" {t[2]}\n"
        f" جایزه: {t[3]} امتیاز\n\n"
        " بعد از انجام، عکس بفرست"
    )
@bot.message_handler(content_types=["photo"])
def receive_task_photo(message):
    uid = message.from_user.id

    if uid not in task_state:
        return

    task_id = task_state.pop(uid)
    photo_id = message.photo[-1].file_id

    cur.execute("""
    INSERT INTO task_submits (task_id, user_id, photo_id, status)
    VALUES (?, ?, ?, 'pending')
    """, (task_id, uid, photo_id))
    db.commit()

    submit_id = cur.lastrowid

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(" تایید", callback_data=f"task_ok_{submit_id}"),
        InlineKeyboardButton(" رد", callback_data=f"task_no_{submit_id}")
    )

    bot.send_photo(
        TASK_CHANNEL_ID,
        photo_id,
        caption=(
            f" درخواست تسک\n\n"
            f" کاربر: {uid}\n"
            f" تسک ID: {task_id}"
        ),
        reply_markup=kb
    )

    bot.send_message(
        message.chat.id,
        " درخواستت ارسال شد، منتظر بررسی ادمین باش"
    )
@bot.callback_query_handler(func=lambda c: c.data.startswith("task_ok_"))
def approve_task(call):
    submit_id = int(call.data.split("_")[2])

    cur.execute("""
    SELECT task_id, user_id FROM task_submits
    WHERE id=? AND status='pending'
    """, (submit_id,))
    row = cur.fetchone()

    if not row:
        return

    task_id, uid = row

    cur.execute("SELECT reward FROM tasks WHERE id=?", (task_id,))
    reward = cur.fetchone()[0]

    cur.execute(
        "UPDATE users SET points = points + ? WHERE user_id=?",
        (reward, uid)
    )
    cur.execute(
        "UPDATE task_submits SET status='approved' WHERE id=?",
        (submit_id,)
    )
    db.commit()

    bot.answer_callback_query(call.id, " تایید شد")
    bot.send_message(uid, f" تسکت تایید شد\n➕ {reward} امتیاز گرفتی")
@bot.callback_query_handler(func=lambda c: c.data.startswith("task_no_"))
def reject_task(call):
    submit_id = int(call.data.split("_")[2])

    cur.execute("""
    SELECT user_id FROM task_submits
    WHERE id=? AND status='pending'
    """, (submit_id,))
    row = cur.fetchone()

    if not row:
        return

    uid = row[0]

    cur.execute(
        "UPDATE task_submits SET status='rejected' WHERE id=?",
        (submit_id,)
    )
    db.commit()

    bot.answer_callback_query(call.id, "رد شد")
    bot.send_message(uid, "تسکت رد شد")
  # ================= پشتیبانی =================
@bot.message_handler(func=lambda m: m.text == " پشتیبانی")
def support(message):
    bot.send_message(message.chat.id, f" پشتیبانی:\n{SUPPORT_ID}")

#====برداشت====
@bot.message_handler(func=lambda m: m.text == "برداشت استارز")
def withdraw_start(message):
    uid = message.from_user.id
    now = int(time.time())

    cur.execute(
        "SELECT balance, last_withdraw FROM users WHERE user_id=?",
        (uid,)
    )
    row = cur.fetchone()

    if not row:
        bot.send_message(message.chat.id, " ابتدا /start را بزن")
        return

    balance, last_withdraw = row

    if balance <= 0:
        bot.send_message(
            message.chat.id,
            " استارزی برای برداشت نداری",
            reply_markup=main_menu()
        )
        return

    if now - last_withdraw < WITHDRAW_COOLDOWN:
        remain = WITHDRAW_COOLDOWN - (now - last_withdraw)
        bot.send_message(
            message.chat.id,
            f" هر ۱ ساعت فقط یک برداشت مجاز است\n"
            f" زمان باقی‌مانده: {remain // 60} دقیقه",
            reply_markup=main_menu()
        )
        return

    msg = bot.send_message(
        message.chat.id,
        f" موجودی استارز شما: {balance}\n\n"
        " مقدار برداشت استارز را ارسال کن:",
        reply_markup=back_menu()
    )
    bot.register_next_step_handler(msg, withdraw_get_amount)
def withdraw_get_amount(message):
    uid = message.from_user.id

    if message.text == " برگشت":
        bot.send_message(message.chat.id, "لغو شد", reply_markup=main_menu())
        return

    if not message.text.isdigit() or int(message.text) <= 0:
        msg = bot.send_message(
            message.chat.id,
            " مقدار باید عدد صحیح باشد",
            reply_markup=back_menu()
        )
        bot.register_next_step_handler(msg, withdraw_get_amount)
        return

    amount = int(message.text)

    cur.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    balance = cur.fetchone()[0]

    if amount > balance:
        bot.send_message(
            message.chat.id,
            "استارز کافی نداری",
            reply_markup=main_menu()
        )
        return

    withdraw_requests[uid] = {"amount": amount}

    msg = bot.send_message(
        message.chat.id,
        "🔗 لینک پست / توضیح پرداخت را ارسال کن:",
        reply_markup=back_menu()
    )
    bot.register_next_step_handler(msg, withdraw_get_link)
def withdraw_get_link(message):
    uid = message.from_user.id

    if uid not in withdraw_requests:
        bot.send_message(message.chat.id, " خطا، دوباره تلاش کن", reply_markup=main_menu())
        return

    if message.text == " برگشت":
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
        InlineKeyboardButton(" تأیید", callback_data=f"wd_ok_{uid}_{amount}"),
        InlineKeyboardButton(" رد", callback_data=f"wd_no_{uid}_{amount}")
    )

    bot.send_message(
    ORDERS_CHANNEL,
    f"""
درخواست برداشت استارز

ID کاربر: {uid}
مقدار استارز: {amount}

توضيح / لينک:
{link}
""",
    reply_markup=kb
)

    bot.send_message(
        message.chat.id,
        " درخواست برداشت ثبت شد\n منتظر تأیید ادمین باشید",
        reply_markup=main_menu()
    )

    withdraw_requests.pop(uid, None)
@bot.callback_query_handler(func=lambda c: c.data.startswith("wd_ok_"))
def approve_withdraw(c):
    if not is_admin(c.from_user.id):
        bot.answer_callback_query(c.id, " دسترسی نداری", show_alert=True)
        return

    _, _, uid, amount = c.data.split("_")
    uid = int(uid)
    amount = int(amount)

    cur.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    balance = cur.fetchone()[0]

    if balance < amount:
        bot.edit_message_text(
            " موجودی کاربر کافی نیست",
            c.message.chat.id,
            c.message.message_id
        )
        return

    cur.execute(
        "UPDATE users SET balance = balance - ? WHERE user_id=?",
        (amount, uid)
    )
    db.commit()

    bot.edit_message_text(
        " برداشت استارز تأیید شد",
        c.message.chat.id,
        c.message.message_id
    )

    bot.send_message(
        uid,
        f" برداشت استارز شما تأیید شد\n مقدار: {amount}"
    )
@bot.callback_query_handler(func=lambda c: c.data.startswith("wd_no_"))
def reject_withdraw(c):
    if not is_admin(c.from_user.id):
        bot.answer_callback_query(c.id, " دسترسی نداری", show_alert=True)
        return

    _, _, uid, amount = c.data.split("_")

    bot.edit_message_text(
        " برداشت استارز رد شد",
        c.message.chat.id,
        c.message.message_id
    )

    bot.send_message(
        int(uid),
        f" برداشت استارز شما رد شد\n مقدار: {amount}"
    )
# ================= دعوت دوستان =================
@bot.message_handler(func=lambda m: m.text == " دعوت دوستان")
def invite_friends(message):
    uid = message.from_user.id
    link = f"https://t.me/{bot.get_me().username}?start={uid}"

    bot.send_message(
        message.chat.id,
        f"""
"🎁 دعوت دوستان"

"🏆 هر دعوت  = امتیاز بیشتر"
"⭐ هر 10 امتیاز = 1 استارز"
"⚠️ هر کاربر فقط یک‌بار حساب می‌شود"

"🔗 لینک دعوت شما:"
{link}
""",
        reply_markup=main_menu()
    )
#====== بخش مدیریت =====
#==== انتقال گروه چت =====
@bot.message_handler(commands=["setgroup"])
def set_transfer_group(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, " دسترسی نداری")
        return

    if message.chat.type not in ["group", "supergroup"]:
        bot.reply_to(message, " این دستور فقط داخل گروه اجرا می‌شود")
        return

    group_id = message.chat.id

    # ذخیره در دیتابیس (پایدار)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS config (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)
    cur.execute(
        "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
        ("TRANSFER_GROUP_ID", str(group_id))
    )
    db.commit()

    bot.reply_to(
        message,
        f"✅ این گروه به عنوان گروه انتقال ثبت شد\n"
        f"🆔 آیدی گروه: `{group_id}`"
    )
    
# ================= حذف کاربر =================
@bot.callback_query_handler(func=lambda c: c.data.startswith("deluser_"))
def delete_user(c):
    if not is_admin(c.from_user.id):
        return

    uid = int(c.data.split("_")[1])
    cur.execute("DELETE FROM users WHERE user_id=?", (uid,))
    db.commit()

    bot.edit_message_text(
        "کاربر با موفقیت حذف شد",
        c.message.chat.id,
        c.message.message_id)
       
#==== اطلاعات کاربر =====
@bot.callback_query_handler(func=lambda c: c.data.startswith("user_"))
def show_user(c):
    if not is_admin(c.from_user.id):
        return

    uid = int(c.data.split("_")[1])

    cur.execute(
        "SELECT points, join_date, invite_count, transfer_count "
        "FROM users WHERE user_id=?",
        (uid,)
    )
    u = cur.fetchone()

    if not u:
        bot.answer_callback_query(c.id, "کاربر یافت نشد", show_alert=True)
        return

    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("افزایش امتیاز", callback_data=f"addpt_{uid}"),
        InlineKeyboardButton("کاهش امتیاز", callback_data=f"minpt_{uid}")
    )
    kb.add(
        InlineKeyboardButton("تنظیم امتیاز", callback_data=f"setpt_{uid}")
    )
    kb.add(
        InlineKeyboardButton("حذف کاربر", callback_data=f"deluser_{uid}")
    )

    bot.edit_message_text(
        f"اطلاعات کاربر\n\n"
        f"آیدی: {uid}\n"
        f"امتیاز: {u[0]}\n"
        f"تاریخ عضویت: {u[1]}\n"
        f"تعداد دعوت: {u[2]}\n"
        f"تعداد انتقال: {u[3]}",
        c.message.chat.id,
        c.message.message_id,
        reply_markup=kb
    )       
#====== تغییر امتیاز======
@bot.callback_query_handler(func=lambda c: c.data.startswith(("addpt_", "minpt_", "setpt_")))
def point_action(c):
    if not is_admin(c.from_user.id):
        return

    action, uid = c.data.split("_")
    admin_steps[c.from_user.id] = (action, int(uid))

    bot.send_message(
        c.from_user.id,
        "مقدار امتیاز را به صورت عدد صحیح ارسال کن:"
    )

@bot.message_handler(func=lambda m: m.from_user.id in admin_steps)
def apply_point_change(message):
    if not is_admin(message.from_user.id):
        return

    try:
        amount = int(message.text)
        if amount < 0:
            raise ValueError
    except:
        bot.send_message(message.chat.id, "فقط عدد صحیح مثبت بفرست")
        return

    action, uid = admin_steps.pop(message.from_user.id)

    if action == "addpt":
        cur.execute(
            "UPDATE users SET points = points + ? WHERE user_id=?",
            (amount, uid)
        )
        text = "امتیاز اضافه شد"

    elif action == "minpt":
        cur.execute(
            "UPDATE users SET points = CASE WHEN points >= ? THEN points - ? ELSE 0 END WHERE user_id=?",
            (amount, amount, uid)
        )
        text = "امتیاز کسر شد"

    else:
        cur.execute(
            "UPDATE users SET points = ? WHERE user_id=?",
            (amount, uid)
        )
        text = "امتیاز تنظیم شد"

    db.commit()

    bot.send_message(
        message.chat.id,
        f"{text}\nآیدی کاربر: {uid}"
    )

    try:
        cur.execute("SELECT points FROM users WHERE user_id=?", (uid,))
        new_points = cur.fetchone()[0]
        bot.send_message(
            uid,
            f"امتیاز شما توسط ادمین تغییر کرد\nامتیاز فعلی: {new_points}"
        )
    except:
        pass

# ================= لیست کاربران =================
@bot.message_handler(commands=["Users"])
def list_users(message):
    if not is_admin(message.from_user.id):
        return
    send_users_page(message.chat.id, page=0)

def send_users_page(chat_id, page):
    offset = page * USERS_PER_PAGE

    cur.execute(
        "SELECT user_id FROM users ORDER BY join_date DESC LIMIT ? OFFSET ?",
        (USERS_PER_PAGE, offset)
    )
    rows = cur.fetchall()

    if not rows:
        bot.send_message(chat_id, "کاربری برای نمایش وجود ندارد")
        return

    kb = InlineKeyboardMarkup(row_width=1)
    for (uid,) in rows:
        kb.add(
            InlineKeyboardButton(f"کاربر {uid}", callback_data=f"user_{uid}")
        )

    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]

    nav = []
    if page > 0:
        nav.append(
            InlineKeyboardButton("قبلی", callback_data=f"users_{page-1}")
        )
    if offset + USERS_PER_PAGE < total:
        nav.append(
            InlineKeyboardButton("بعدی", callback_data=f"users_{page+1}")
        )

    if nav:
        kb.row(*nav)

    bot.send_message(
        chat_id,
        f"لیست کاربران - صفحه {page + 1}",
        reply_markup=kb
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("users_"))
def users_pagination(c):
    if not is_admin(c.from_user.id):
        return

    page = int(c.data.split("_")[1])
    bot.delete_message(c.message.chat.id, c.message.message_id)
    send_users_page(c.message.chat.id, page)

        # ================= روشن / خاموش کردن ربات =================
@bot.message_handler(commands=["off"])
def bot_off(message):
    global BOT_ACTIVE
    if not is_admin(message.from_user.id):
        return
    BOT_ACTIVE = False
    bot.send_message(message.chat.id, "ربات خاموش شد")

@bot.message_handler(commands=["on"])
def bot_on(message):
    global BOT_ACTIVE

    if not is_admin(message.from_user.id):
        return

    BOT_ACTIVE = True
    bot.send_message(message.chat.id, "✅ ربات فعال شد")

    
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
    cur.execute(
        "SELECT COUNT(*) FROM users WHERE last_active LIKE ?",
        (today + "%",)
    )
    active_today = cur.fetchone()[0]

    # فعال 7 روز اخیر
    cur.execute(
        "SELECT COUNT(*) FROM users WHERE last_active >= ?",
        (week,)
    )
    active_week = cur.fetchone()[0]

    # فعال 30 روز اخیر
    cur.execute(
        "SELECT COUNT(*) FROM users WHERE last_active >= ?",
        (month,)
    )
    active_month = cur.fetchone()[0]

    text = (
        "==== آمار حرفه‌ای ربات ====\n\n"
        f"کل کاربران: {total}\n"
        f"ثبت نام امروز: {new_today}\n"
        f"فعال امروز: {active_today}\n"
        f"فعال 7 روز اخیر: {active_week}\n"
        f"فعال 30 روز اخیر: {active_month}"
    )

    bot.send_message(message.chat.id, text)
    
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
  
#=====تغییر مقدار دعوت===
@bot.message_handler(commands=["invite_points"])
def set_invite_points(message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        bot.send_message(
            message.chat.id,
            "❌ فرمت صحیح:\n/invite_points 5"
        )
        return

    value = int(parts[1])

    cur.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        ("invite_points", str(value))
    )
    db.commit()

    bot.send_message(
        message.chat.id,
        f"✅ امتیاز دعوت تنظیم شد روی: {value} امتیاز"
    )
    

#=====ادمین====
@bot.message_handler(commands=["addadmin"])
def add_admin_cmd(message):
   if not is_admin(message.from_user.id):
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
#===== پیام همگانی ====

@bot.message_handler(commands=['broadcast'])
def start_broadcast(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "⛔ این دستور فقط برای ادمین است")
        return

    bot.send_message(
        message.chat.id,
        "📢 پیام همگانی\n\n"
        "پیام / عکس / ویدیو / لینک رو بفرست"
    )
    broadcast_data[message.chat.id] = {}
@bot.message_handler(content_types=['text', 'photo', 'video'])
def get_broadcast_content(message):
    if not is_admin(message.from_user.id):
        return

    if message.chat.id not in broadcast_data:
        return

    broadcast_data[message.chat.id]['message'] = message

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ ارسال", callback_data="confirm_broadcast"),
        InlineKeyboardButton("❌ لغو", callback_data="cancel_broadcast")
    )

    bot.send_message(
        message.chat.id,
        "⚠️ پیش‌نمایش پیام\nارسال شود؟",
        reply_markup=markup
    )
@bot.callback_query_handler(func=lambda c: c.data in ['confirm_broadcast', 'cancel_broadcast'])
def broadcast_confirm(call):
    if not is_admin(call.from_user.id):
        return

    if call.data == 'cancel_broadcast':
        broadcast_data.pop(call.message.chat.id, None)
        bot.edit_message_text(
            "❌ لغو شد",
            call.message.chat.id,
            call.message.message_id
        )
        return

    msg = broadcast_data[call.message.chat.id]['message']
    users = get_all_users()

    sent = 0
    for uid in users:
        try:
            if msg.content_type == 'text':
                bot.send_message(uid, msg.text)
            elif msg.content_type == 'photo':
                bot.send_photo(uid, msg.photo[-1].file_id, caption=msg.caption)
            elif msg.content_type == 'video':
                bot.send_video(uid, msg.video.file_id, caption=msg.caption)
            sent += 1
        except:
            pass

    bot.edit_message_text(
        f"✅ پیام همگانی ارسال شد\n📨 ارسال‌شده: {sent}",
        call.message.chat.id,
        call.message.message_id
    )

    broadcast_data.pop(call.message.chat.id, None)

#====== برترین دعوت کننده ====
@bot.message_handler(commands=["topinvites"])
def top_invites(message):
    if not is_admin(message.from_user.id):
        return

    cur.execute("""
    SELECT user_id, invite_count 
    FROM users 
    ORDER BY invite_count DESC 
    LIMIT 10
    """)
    rows = cur.fetchall()

    if not rows:
        bot.send_message(message.chat.id, "❌ داده‌ای وجود ندارد")
        return

    text = "🏆 برترین دعوت‌کنندگان:\n\n"
    kb = InlineKeyboardMarkup()

    for i, (uid, count) in enumerate(rows, start=1):
        text += f"{i}. 👤 {uid} | 👥 {count} دعوت\n"
        kb.add(
            InlineKeyboardButton(
                f"🎁 پاداش به {i}",
                callback_data=f"reward_invite_{uid}"
            )
        )

    bot.send_message(message.chat.id, text, reply_markup=kb)
@bot.callback_query_handler(func=lambda c: c.data.startswith("reward_invite_"))
def reward_invite_user(c):
    if not is_admin(c.from_user.id):
        return

    uid = int(c.data.split("_")[2])
    admin_steps[c.from_user.id] = ("reward_invite", uid)

    bot.send_message(
        c.from_user.id,
        f"🎁 مقدار امتیاز برای کاربر {uid} را ارسال کن:"
    )
@bot.message_handler(func=lambda m: m.from_user.id in admin_steps)
def apply_reward(message):
    if not is_admin(message.from_user.id):
        return

    try:
        amount = int(message.text)
        if amount <= 0:
            raise ValueError
    except:
        bot.send_message(message.chat.id, "❌ فقط عدد صحیح مثبت بفرست")
        return

    action, uid = admin_steps.pop(message.from_user.id)

    if action == "reward_invite":
        cur.execute(
            "UPDATE users SET points = points + ? WHERE user_id=?",
            (amount, uid)
        )
        db.commit()

        bot.send_message(
            message.chat.id,
            f"✅ {amount} امتیاز به کاربر {uid} داده شد"
        )

        try:
            bot.send_message(
                uid,
                f"🎉 تبریک!\n🏆 به‌عنوان برترین دعوت‌کننده، {amount} امتیاز گرفتی"
            )
        except:
            pass
  
#====== اضافه کردن تسک ======          
@bot.message_handler(commands=["addtask"])
def add_task(message):
    if not is_admin(message.from_user.id):
        return

    # ساده‌ترین نسخه
    cur.execute("""
    INSERT INTO tasks (title, description, link, reward)
    VALUES ('عضویت در کانال', 'عضو شو و اسکرین بفرست', 'https://t.me/test', 5)
    """)
    db.commit()

    bot.send_message(message.chat.id, "✅ تسک نمونه اضافه شد")
    
@bot.message_handler(commands=["tasks"])
def admin_tasks(message):
    if not is_admin(message.from_user.id):
        return

    cur.execute("""
    SELECT id, title, reward, active FROM tasks
    """)
    rows = cur.fetchall()

    if not rows:
        bot.send_message(message.chat.id, "❌ تسکی وجود ندارد")
        return

    text = "📋 لیست تسک‌ها:\n\n"
    for t in rows:
        status = "✅ فعال" if t[3] else "⛔ غیرفعال"
        text += f"""
🧩 ID: {t[0]}
📌 {t[1]}
🎁 {t[2]} امتیاز
📍 وضعیت: {status}
────────────
"""
    bot.send_message(message.chat.id, text)
    
@bot.message_handler(commands=["edittask"])
def edit_task_menu(message):
    if not is_admin(message.from_user.id):
        return

    cur.execute("SELECT id, title FROM tasks")
    rows = cur.fetchall()

    kb = InlineKeyboardMarkup()
    for t in rows:
        kb.add(
            InlineKeyboardButton(
                f"{t[1]} (ID:{t[0]})",
                callback_data=f"edit_task_{t[0]}"
            )
        )

    bot.send_message(
        message.chat.id,
        "✏️ انتخاب تسک برای ویرایش:",
        reply_markup=kb
    )
edit_state = {}

@bot.callback_query_handler(func=lambda c: c.data.startswith("edit_task_"))
def edit_task_options(call):
    task_id = int(call.data.split("_")[2])
    edit_state[call.from_user.id] = {"task_id": task_id}

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✏️ تغییر عنوان", callback_data="edit_title"),
        InlineKeyboardButton("📝 تغییر توضیح", callback_data="edit_desc")
    )
    kb.add(
        InlineKeyboardButton("🔗 تغییر لینک", callback_data="edit_link"),
        InlineKeyboardButton("🎁 تغییر جایزه", callback_data="edit_reward")
    )
    kb.add(
        InlineKeyboardButton("🔄 فعال / غیرفعال", callback_data="edit_toggle")
    )

    bot.send_message(
        call.message.chat.id,
        "⚙️ چه چیزی ویرایش شود؟",
        reply_markup=kb
    )
@bot.callback_query_handler(func=lambda c: c.data.startswith("edit_"))
def set_edit_field(call):
    uid = call.from_user.id
    if uid not in edit_state:
        return

    field = call.data.replace("edit_", "")
    edit_state[uid]["field"] = field

    bot.send_message(
        call.message.chat.id,
        "✍️ مقدار جدید را ارسال کن"
    )
@bot.message_handler(func=lambda m: m.from_user.id in edit_state)
def save_edit(message):
    uid = message.from_user.id
    data = edit_state[uid]

    task_id = data["task_id"]
    field = data["field"]
    value = message.text

    if field == "title":
        cur.execute("UPDATE tasks SET title=? WHERE id=?", (value, task_id))

    elif field == "desc":
        cur.execute("UPDATE tasks SET description=? WHERE id=?", (value, task_id))

    elif field == "link":
        cur.execute("UPDATE tasks SET link=? WHERE id=?", (value, task_id))

    elif field == "reward":
        if not value.isdigit():
            bot.send_message(message.chat.id, "❌ فقط عدد")
            return
        cur.execute("UPDATE tasks SET reward=? WHERE id=?", (int(value), task_id))

    elif field == "toggle":
        cur.execute("""
        UPDATE tasks
        SET active = CASE WHEN active=1 THEN 0 ELSE 1 END
        WHERE id=?
        """, (task_id,))

    db.commit()
    edit_state.pop(uid)

    bot.send_message(message.chat.id, "✅ تغییرات ذخیره شد")
#====== انتقالات گروه ======
@bot.message_handler(func=lambda m: m.chat.id == TRANSFER_GROUP_ID and m.reply_to_message)
def transfer_by_reply(message):
    if not message.text:
        return

    text = message.text.strip()

    # فقط "انتقال عدد"
    if not text.startswith("انتقال"):
        return

    parts = text.split()
    if len(parts) != 2:
        bot.reply_to(message, "❌ فرمت درست:\nانتقال 15")
        return

    try:
        amount = int(parts[1])
        if amount <= 0:
            raise ValueError
    except:
        bot.reply_to(message, "❌ مقدار انتقال نامعتبره")
        return

    sender_id = message.from_user.id
    receiver_id = message.reply_to_message.from_user.id

    if sender_id == receiver_id:
        bot.reply_to(message, "❌ نمی‌تونی به خودت انتقال بدی")
        return

    # موجودی فرستنده
    cur.execute("SELECT points FROM users WHERE user_id=?", (sender_id,))
    row = cur.fetchone()
    if not row or row[0] < amount:
        bot.reply_to(message, "❌ امتیاز کافی نداری")
        return

    # انجام انتقال
    cur.execute("UPDATE users SET points = points - ? WHERE user_id=?", (amount, sender_id))
    cur.execute("UPDATE users SET points = points + ? WHERE user_id=?", (amount, receiver_id))
    db.commit()

    sender_tag = user_tag(message.from_user)
    receiver_tag = user_tag(message.reply_to_message.from_user)

    # نوتیف خصوصی
    try:
        bot.send_message(sender_id, f"➖ {amount} امتیاز به {receiver_tag} منتقل شد")
        bot.send_message(receiver_id, f"➕ {amount} امتیاز از {sender_tag} دریافت کردی")
    except:
        pass

    # لاگ داخل گروه
    bot.reply_to(
        message,
        f"🔄 انتقال انجام شد\n"
        f"👤 فرستنده: {sender_tag}\n"
        f"👥 گیرنده: {receiver_tag}\n"
        f"⭐ مقدار: {amount}"
    )

#===== انتقال امتیاز در گروه =====
def user_tag(user):
    return f"@{user.username}" if user.username else user.first_name

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
        bot.reply_to(message, "❌ نمی‌تونی به خودت امتیاز انتقال بدی")
        return

    cur.execute(
        "SELECT points, last_transfer FROM users WHERE user_id=?",
        (sender,)
    )
    s = cur.fetchone()

    cur.execute(
        "SELECT user_id FROM users WHERE user_id=?",
        (receiver,)
    )
    r = cur.fetchone()

    if not s or not r:
        bot.reply_to(message, "❌ هر دو کاربر باید ربات را استارت کرده باشند")
        return

    points, last_transfer = s
    now = int(time.time())

    # ⏳ ضد اسپم
    if now - last_transfer < TRANSFER_COOLDOWN:
        bot.reply_to(
            message,
            f"⏳ لطفاً {TRANSFER_COOLDOWN} ثانیه بین انتقال‌ها صبر کن"
        )
        return

    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        bot.reply_to(message, "❌ فرمت صحیح:\nانتقال 5")
        return

    amount = int(parts[1])
    if amount <= 0:
        bot.reply_to(message, "❌ مقدار نامعتبره")
        return

    if points < amount:
        bot.reply_to(
            message,
            f"❌ امتیاز کافی نیست\n⭐ امتیاز شما: {points}"
        )
        return

    # ✅ انجام انتقال امتیاز
    cur.execute(
        """
        UPDATE users
        SET points = points - ?, last_transfer = ?, transfer_count = transfer_count + 1
        WHERE user_id=?
        """,
        (amount, now, sender)
    )

    cur.execute(
        "UPDATE users SET points = points + ? WHERE user_id=?",
        (amount, receiver)
    )
    db.commit()

    group_text = f"""
مقدار: {amount} امتياز
از: {user_tag(sender_user)}
به: {user_tag(receiver_user)}

انتقال امتياز با موفقيت انجام شد
@FreeStarsxbot
"""

    bot.send_message(
        message.chat.id,
        group_text,
        reply_to_message_id=message.reply_to_message.message_id
    )

    # 📩 نوتیف خصوصی
    try:
        bot.send_message(
            sender,
            f"✅ {amount} امتیاز به {user_tag(receiver_user)} انتقال دادی"
        )
    except:
        pass

    try:
        bot.send_message(
            receiver,
            f"🎉 {amount} امتیاز از {user_tag(sender_user)} دریافت کردی"
        )
    except:
        pass
def user_tag(user):
    return f"@{user.username}" if user.username else user.first_name


@bot.message_handler(
    func=lambda m: (
        m.chat.type in ["group", "supergroup"]
        and m.chat.id == TRANSFER_GROUP_ID
        and m.text
        and m.text.startswith("انتقال")
    )
)
def group_transfer_username(message):
    sender_user = message.from_user
    sender = sender_user.id

    parts = message.text.split()

    # انتقال 5 @user
    if len(parts) != 3 or not parts[1].isdigit():
        bot.reply_to(
            message,
            "❌ فرمت صحیح:\nانتقال 5 @username"
        )
        return

    amount = int(parts[1])
    username = parts[2].replace("@", "").lower()

    if amount <= 0:
        bot.reply_to(message, "❌ مقدار نامعتبره")
        return

    # گرفتن اطلاعات فرستنده
    cur.execute(
        "SELECT points, last_transfer FROM users WHERE user_id=?",
        (sender,)
    )
    s = cur.fetchone()

    if not s:
        bot.reply_to(message, "❌ اول ربات رو استارت کن")
        return

    points, last_transfer = s
    now = int(time.time())

    if points < amount:
        bot.reply_to(
            message,
            f"❌ امتیاز کافی نیست\n⭐ امتیاز شما: {points}"
        )
        return

    if now - last_transfer < TRANSFER_COOLDOWN:
        bot.reply_to(
            message,
            f"⏳ لطفاً {TRANSFER_COOLDOWN} ثانیه صبر کن"
        )
        return

    # پیدا کردن گیرنده از طریق یوزرنیم
    try:
        receiver_user = bot.get_chat_member(
            message.chat.id,
            username
        ).user
    except:
        bot.reply_to(message, "❌ کاربر پیدا نشد")
        return

    receiver = receiver_user.id

    if sender == receiver:
        bot.reply_to(message, "❌ نمی‌تونی به خودت انتقال بدی")
        return

    # گیرنده باید استارت کرده باشد
    cur.execute(
        "SELECT user_id FROM users WHERE user_id=?",
        (receiver,)
    )
    if not cur.fetchone():
        bot.reply_to(
            message,
            "❌ این کاربر هنوز ربات رو استارت نکرده"
        )
        return

    # ✅ انجام انتقال
    cur.execute(
        """
        UPDATE users
        SET points = points - ?, last_transfer = ?, transfer_count = transfer_count + 1
        WHERE user_id=?
        """,
        (amount, now, sender)
    )

    cur.execute(
        "UPDATE users SET points = points + ? WHERE user_id=?",
        (amount, receiver)
    )
    db.commit()

    bot.send_message(
        message.chat.id,
        f"""
✅ انتقال موفق

مقدار: {amount} امتیاز
از: {user_tag(sender_user)}
به: {user_tag(receiver_user)}
"""
    )

    # نوتیف خصوصی
    try:
        bot.send_message(
            sender,
            f"✅ {amount} امتیاز به {user_tag(receiver_user)} دادی"
        )
    except:
        pass

    try:
        bot.send_message(
            receiver,
            f"🎉 {amount} امتیاز از {user_tag(sender_user)} گرفتی"
        )
    except:
        pass    

# ================= اجرای ربات =================
bot.infinity_polling(skip_pending=True)
