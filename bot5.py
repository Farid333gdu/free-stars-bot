import telebot
from telebot import types
import sqlite3
import random
from PIL import Image, ImageDraw
import time
import os
TOKEN = "8327002490:AAEAExmXciV-5ss9FQ9WDeu2h05oXsioXTA"
WITHDRAW_CHANNEL_ID = -1003712489004
FORCE_CHANNELS = ["@BNPREMIUMFREE", "@AxNetv", "@rfral_Azad", "@ZDGmail", "@BNBPREMIUMFREE"]
SUPPORT_USERNAME = "BNBPremium"
SPECIAL_USERS = [6902426681, 8589848955, 8010675451,7892579687,8224877957]

TOKEN = os.getenv("TOKEN")

bot = telebot.TeleBot(TOKEN, threaded=False)


BOT_USERNAME = bot.get_me().username

# ------------------- ایجاد جداول -------------------

conn = sqlite3.connect("bot510.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    ref_by INTEGER,
    balance INTEGER DEFAULT 0,
    referrals INTEGER DEFAULT 0,
    captcha_verified INTEGER DEFAULT 0,
    ref_rewarded INTEGER DEFAULT 0,
    withdraw_step INTEGER DEFAULT 0,
    withdraw_amount INTEGER DEFAULT 0,
    withdraw_target TEXT DEFAULT ''
)
""")

conn.commit()
conn.close()

# اضافه کردن کاربران ویژه
conn = sqlite3.connect("bot5130.db", check_same_thread=False)
cursor = conn.cursor()

for uid in SPECIAL_USERS:
    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    user = cursor.fetchone()

    if not user:
        cursor.execute(
            "INSERT INTO users (user_id, balance, captcha_verified) VALUES (?, ?, ?)",
            (uid, 25, 0)
        )
    else:
        cursor.execute(
            "UPDATE users SET balance = ? WHERE user_id=?",
            (25, uid)
        )

conn.commit()
conn.close()

captcha_dict = {}

# ------------------- توابع کمکی -------------------
def generate_captcha():
    code = str(random.randint(1000, 9999))

    img = Image.new("RGB", (300, 120), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((110, 40), code, fill=(0, 0, 0))

    path = f"captcha_{code}_{int(time.time())}.png"
    img.save(path)

    return code, path


def check_join(user_id):
    for ch in FORCE_CHANNELS:
        try:
            member = bot.get_chat_member(ch, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception:
            return False
    return True


def main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("حساب کاربری", "دعوت دوستان")
    markup.add("پشتیبانی", "برداشت پریمیوم")

    bot.send_message(
        chat_id,
        "به ربات خوش آمدید 👋\nاز منوی زیر انتخاب کنید:",
        reply_markup=markup
    )
# ------------------- استارت -------------------
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    args = message.text.split()

    conn = sqlite3.connect("bot5130.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("SELECT captcha_verified FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    # اگر کاربر جدید بود
    if not user:
        ref_by = None

        if len(args) > 1:
            try:
                inviter_id = int(args[1])
                if inviter_id != user_id:
                    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (inviter_id,))
                    if cursor.fetchone():
                        ref_by = inviter_id
            except Exception:
                pass

        cursor.execute(
            "INSERT INTO users (user_id, ref_by) VALUES (?, ?)",
            (user_id, ref_by)
        )
        conn.commit()

    # دوباره وضعیت کپچا را بگیر
    cursor.execute("SELECT captcha_verified FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    conn.close()

    # اگر قبلاً تایید شده بود
    if user and user[0] == 1:
        main_menu(message.chat.id)
        return

    # بررسی عضویت اجباری
    if not check_join(user_id):
        markup = types.InlineKeyboardMarkup(row_width=1)
        for ch in FORCE_CHANNELS:
            markup.add(
                types.InlineKeyboardButton(
                    f"عضویت در {ch}",
                    url=f"https://t.me/{ch.replace('@', '')}"
                )
            )
        markup.add(types.InlineKeyboardButton("✅ عضو شدم", callback_data="check_join"))

        bot.send_message(
            message.chat.id,
            "⚠️ برای استفاده از ربات باید در کانال‌های زیر عضو شوید:",
            reply_markup=markup
        )
        return

    send_captcha(message.chat.id, user_id)
def send_captcha(chat_id, user_id):
    code, path = generate_captcha()
    captcha_dict[user_id] = code

    with open(path, 'rb') as photo:
        bot.send_photo(
            chat_id,
            photo,
            caption="🔐 لطفاً کد نمایش داده شده در تصویر را وارد کنید:"
        )

    os.remove(path)  # حذف فایل بعد از ارسال
    
# ------------------- بررسی عضویت ------------------
@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    try:
        if check_join(user_id):
            bot.delete_message(chat_id, call.message.message_id)

            # بررسی اینکه قبلاً تایید نشده باشه
            conn = sqlite3.connect("bot5130.db", check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("SELECT captcha_verified FROM users WHERE user_id=?", (user_id,))
            user = cursor.fetchone()
            conn.close()

            if user and user[0] == 1:
                main_menu(chat_id)
            else:
                send_captcha(chat_id, user_id)

        else:
            bot.answer_callback_query(
                call.id,
                "❌ شما هنوز در همه کانال‌ها عضو نشده‌اید!",
                show_alert=True
            )

    except Exception as e:
        print("Join callback error:", e)

# ------------------- تایید کپچا -------------------
@bot.message_handler(func=lambda m: m.from_user.id in captcha_dict)
def verify_captcha(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if message.text.strip() != captcha_dict[user_id]:
        bot.send_message(chat_id, "❌ کد اشتباه است. دوباره امتحان کنید:")
        return

    conn = sqlite3.connect("bot5130.db", check_same_thread=False)
    cursor = conn.cursor()

    # تایید کپچا
    cursor.execute(
        "UPDATE users SET captcha_verified = 1 WHERE user_id=?",
        (user_id,)
    )

    # بررسی و پرداخت پاداش رفرال
    cursor.execute(
        "SELECT ref_by, ref_rewarded FROM users WHERE user_id=?",
        (user_id,)
    )
    data = cursor.fetchone()

    if data and data[0] and data[1] == 0:
        inviter_id = data[0]

        cursor.execute(
            "UPDATE users SET balance = balance + 1, referrals = referrals + 1 WHERE user_id=?",
            (inviter_id,)
        )

        cursor.execute(
            "UPDATE users SET ref_rewarded = 1 WHERE user_id=?",
            (user_id,)
        )

        cursor.execute(
            "SELECT balance FROM users WHERE user_id=?",
            (inviter_id,)
        )
        new_balance = cursor.fetchone()[0]

        try:
            bot.send_message(
                inviter_id,
                f"🎉 یک کاربر جدید با لینک شما عضو شد!\n💰 موجودی جدید: {new_balance}"
            )
        except Exception:
            pass

    conn.commit()
    conn.close()

    del captcha_dict[user_id]

    bot.send_message(chat_id, "✅ کپچا با موفقیت تایید شد!")
    main_menu(chat_id)
# ------------------- منوی اصلی -------------------
@bot.message_handler(func=lambda m: m.text == "حساب کاربری")
def account(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    conn = sqlite3.connect("bot5130.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT balance, referrals FROM users WHERE user_id=?",
        (user_id,)
    )
    user = cursor.fetchone()

    conn.close()

    if user:
        balance, referrals = user
        text = f"""
👤 حساب کاربری شما

🆔 آیدی: {user_id}
💰 موجودی: {balance} امتیاز
👥 تعداد زیرمجموعه: {referrals}
"""
        bot.send_message(chat_id, text)
    else:
        bot.send_message(chat_id, "❌ خطا در دریافت اطلاعات")
        
@bot.message_handler(func=lambda m: m.text == "دعوت دوستان")
def invite(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    link = f"https://t.me/{BOT_USERNAME}?start={user_id}"

    text = f"""
🔗 لینک دعوت شما:

{link}

با ارسال این لینک به دوستانتان،
به ازای هر عضویت ۱ امتیاز دریافت می‌کنید 🎁
"""

    bot.send_message(chat_id, text)
    

@bot.message_handler(func=lambda m: m.text == "پشتیبانی")
def support(message):
    chat_id = message.chat.id

    username = SUPPORT_USERNAME.replace("@", "")
    support_link = f"https://t.me/{username}"

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            "📞 ارتباط با پشتیبانی",
            url=support_link
        )
    )

    bot.send_message(
        chat_id,
        "برای ارتباط با پشتیبانی روی دکمه زیر کلیک کنید:",
        reply_markup=markup
    )

# ------------------- برداشت پریمیوم (با ریپلای باتن) -------------------
@bot.message_handler(func=lambda m: m.text == "برداشت پریمیوم")
def withdraw_start(message):
    user_id = message.from_user.id
    
    # ریست کردن مرحله برداشت
    cursor.execute(
        "UPDATE users SET withdraw_step = 0, withdraw_amount = 0, withdraw_target = '' WHERE user_id=?",
        (user_id,)
    )
    db.commit()
    
    # نمایش منوی پلن‌ها با ریپلای کیبورد
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        "⭐ پلن ۳ ماهه (۲۵ امتیاز)",
        "⭐ پلن ۶ ماهه (۴۵ امتیاز)",
        "⭐ پلن ۱ ساله (۶۵ امتیاز)",
        "🔙 بازگشت به منوی اصلی"
    )
    
    msg = bot.send_message(
        message.chat.id,
        "🎁 لطفاً پلن مورد نظر خود را انتخاب کنید:",
        reply_markup=markup
    )
    
    # ست کردن مرحله 1: انتخاب پلن
    cursor.execute(
        "UPDATE users SET withdraw_step = 1 WHERE user_id=?",
        (user_id,)
    )
    db.commit()

# ------------------- پردازش مراحل برداشت -------------------
@bot.message_handler(func=lambda m: True)
def handle_withdraw_steps(message):
    user_id = message.from_user.id
    text = message.text
    chat_id = message.chat.id

    conn = sqlite3.connect("bot5130.db", check_same_thread=False)
    cursor = conn.cursor()

    # دریافت مرحله فعلی کاربر
    cursor.execute(
        "SELECT withdraw_step, withdraw_amount, balance FROM users WHERE user_id=?",
        (user_id,)
    )
    result = cursor.fetchone()

    if not result:
        conn.close()
        return

    step, amount, balance = result
    
# اگر کاربر در مرحله برداشت نیست و دکمه بازگشت زده
    if step == 0 and text == "🔙 بازگشت به منوی اصلی":
        conn.close()
        main_menu(message.chat.id)
        return

    # پردازش مراحل برداشت
    if step == 1:  # مرحله انتخاب پلن
        plans = {
            "⭐ پلن ۳ ماهه (۲۵ امتیاز)": 25,
            "⭐ پلن ۶ ماهه (۴۵ امتیاز)": 45,
            "⭐ پلن ۱ ساله (۶۵ امتیاز)": 65
        }

        if text in plans:
            need = plans[text]

            if balance < need:
                bot.send_message(
                    message.chat.id,
                    f"❌ امتیاز شما کافی نیست!\n"
                    f"موجودی شما: {balance}\n"
                    f"امتیاز مورد نیاز: {need}",
                    reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🔙 بازگشت به منوی اصلی")
                )

                cursor.execute(
                    "UPDATE users SET withdraw_step = 0 WHERE user_id=?",
                    (user_id,)
                )
                conn.commit()
                conn.close()
                return

            # رفتن به مرحله بعد (دریافت یوزرنیم)
            cursor.execute(
                "UPDATE users SET withdraw_step = 2, withdraw_amount = ? WHERE user_id=?",
                (need, user_id)
            )
            conn.commit()
            conn.close()

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("🔙 انصراف و بازگشت")

            bot.send_message(
                message.chat.id,
                "📝 لطفاً یوزرنیم (با @) یا آیدی عددی اکانت مقصد را ارسال کنید:\n\n"
                "مثال: @username یا 123456789",
                reply_markup=markup
            )
            return
        elif text == "🔙 بازگشت به منوی اصلی":
            cursor.execute(
                "UPDATE users SET withdraw_step = 0 WHERE user_id=?",
                (user_id,)
            )
            conn.commit()
            conn.close()

            main_menu(message.chat.id)
            return

        else:
            conn.close()
            bot.send_message(message.chat.id, "❌ لطفاً یک گزینه معتبر انتخاب کنید!")
            return

    # ---------------- مرحله 2 ----------------
    elif step == 2:

        if text == "🔙 انصراف و بازگشت":
            cursor.execute(
                "UPDATE users SET withdraw_step = 0, withdraw_amount = 0 WHERE user_id=?",
                (user_id,)
            )
            conn.commit()
            conn.close()

            main_menu(message.chat.id)
            return

        target = text.strip()

        # اعتبارسنجی ساده
        if not (target.startswith("@") or target.isdigit()):
            conn.close()
            bot.send_message(
                message.chat.id,
                "❌ فرمت وارد شده صحیح نیست!\n"
                "لطفاً یوزرنیم با @ یا آیدی عددی ارسال کنید:"
            )
            return

        if len(target) > 50:
            conn.close()
            bot.send_message(
                message.chat.id,
                "❌ مقدار وارد شده بیش از حد مجاز است!"
            )
            return

        # ذخیره یوزرنیم
        cursor.execute(
            "UPDATE users SET withdraw_step = 3, withdraw_target = ? WHERE user_id=?",
            (target, user_id)
        )
        conn.commit()

        # دریافت مقدار پلن
        cursor.execute(
            "SELECT withdraw_amount FROM users WHERE user_id=?",
            (user_id,)
        )
        amount = cursor.fetchone()[0]

        conn.close()

        plans_name = {
            25: "۳ ماهه",
            45: "۶ ماهه",
            65: "۱ ساله"
        }
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add("✅ تایید و ارسال", "❌ لغو")
        
        bot.send_message(
            message.chat.id,
            f"📋 اطلاعات درخواست شما:\n\n"
            f"🎁 پلن: {plans_name.get(amount, 'نامشخص')}\n"
            f"💰 امتیاز: {amount}\n"
            f"🎯 مقصد: {target}\n\n"
            f"آیا برای ثبت درخواست اطمینان دارید؟",
            reply_markup=markup
        )
    
    elif step == 3:  # مرحله تایید نهایی
        if text == "✅ تایید و ارسال":
            # دریافت اطلاعات نهایی
            cursor.execute(
                "SELECT withdraw_amount, withdraw_target, referrals FROM users WHERE user_id=?",
                (user_id,)
            )
            amount, target, referrals = cursor.fetchone()
            
            # کسر امتیاز
            cursor.execute(
                "UPDATE users SET balance = balance - ?, withdraw_step = 0, withdraw_amount = 0, withdraw_target = '' WHERE user_id=?",
                (amount, user_id)
            )
            db.commit()
            
            # ارسال به کانال
            username = message.from_user.username
            username_display = f"@{username}" if username else "ندارد"
            
            plans = {
                25: "پریمیوم ۳ ماهه",
                45: "پریمیوم ۶ ماهه",
                65: "پریمیوم ۱ ساله"
            }
            
            channel_text = f"""
📥 سفارش جدید پریمیوم

👤 کاربر: {user_id}
🔗 یوزرنیم: {username_display}
👥 رفرال: {referrals}
💰 امتیاز مصرف شده: {amount}

🎯 مقصد: {target}
🎁 پلن: {plans.get(amount, 'نامشخص')}
"""
            
            try:
                bot.send_message(WITHDRAW_CHANNEL_ID, channel_text)
                
                # برگشت به منوی اصلی با پیام موفقیت
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                markup.add("حساب کاربری", "دعوت دوستان")
                markup.add("پشتیبانی", "برداشت پریمیوم")
                
                bot.send_message(
                    message.chat.id,
                    "✅ درخواست شما با موفقیت ثبت شد!\n\n"
                    "📞 برای پیگیری و دریافت پریمیوم به پشتیبانی مراجعه کنید.",
                    reply_markup=markup
                )
                
            except Exception as e:
                print(f"Error sending to channel: {e}")
                # برگرداندن امتیاز در صورت خطا
                cursor.execute(
                    "UPDATE users SET balance = balance + ?, withdraw_step = 0 WHERE user_id=?",
                    (amount, user_id)
                )
                db.commit()
                
                bot.send_message(
                    message.chat.id,
                    "❌ خطا در ثبت درخواست. لطفاً دوباره تلاش کنید یا به پشتیبانی پیام دهید.",
                    reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("برداشت پریمیوم")
                )
        
        elif text == "❌ لغو":
            cursor.execute(
                "UPDATE users SET withdraw_step = 0, withdraw_amount = 0, withdraw_target = '' WHERE user_id=?",
                (user_id,)
            )
            db.commit()
            main_menu(message.chat.id)
        
        else:
            bot.send_message(
                message.chat.id,
                "❌ لطفاً یکی از گزینه‌های تایید یا لغو را انتخاب کنید:"
            )

# ------------------- اجرای ربات -------------------

if __name__ == "__main__":
    print("ربات با موفقیت شروع به کار کرد...")

    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"خطا در اجرای ربات: {e}")
            print("⏳ تلاش مجدد تا 5 ثانیه دیگر...")
            time.sleep(5)
