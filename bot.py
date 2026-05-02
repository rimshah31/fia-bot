import os
import requests
import logging
import datetime
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

BOT_TOKEN = "8629503335:AAHoTTStZLE29A7cdsXmwJB02wn4MVImDFc"
WEBSITE_URL = "https://darkred-peafowl-944680.hostingersite.com/index.php"
PDF_URL = "https://darkred-peafowl-944680.hostingersite.com/pdf.php"

ADMIN_ID = 1653583277

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WAITING_EXCEL = 1
WAITING_PHOTO = 2

user_coins = {1653583277: 9999}
user_data_store = {}

def is_admin(user_id):
    return user_id == ADMIN_ID

def is_allowed(user_id):
    return user_id in user_coins

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ *Access Denied!*\n\nAap authorized nahi hain.", parse_mode="Markdown")
        return ConversationHandler.END
    coins = user_coins.get(user_id, 0)
    await update.message.reply_text(
        f"🤖 *FIA Travel History Bot*\n\n💰 Tumhare coins: *{coins}*\n\nExcel file (.xlsx) bhejo!",
        parse_mode="Markdown"
    )
    return WAITING_EXCEL

async def my_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ *Access Denied!*", parse_mode="Markdown")
        return
    coins = user_coins.get(user_id, 0)
    await update.message.reply_text(f"💰 Tumhare coins: *{coins}*", parse_mode="Markdown")

async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Sirf admin ye command use kar sakta hai!")
        return
    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: /adduser 123456789 10")
        return
    try:
        new_user = int(context.args[0])
        coins = int(context.args[1])
        user_coins[new_user] = coins
        await update.message.reply_text(f"✅ User `{new_user}` add ho gaya!\n💰 Coins: *{coins}*", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ Galat format! /adduser 123456789 10")

async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Sirf admin ye command use kar sakta hai!")
        return
    if not context.args:
        await update.message.reply_text("❌ Usage: /removeuser 123456789")
        return
    try:
        rem_user = int(context.args[0])
        if rem_user == ADMIN_ID:
            await update.message.reply_text("❌ Admin ko remove nahi kar sakte!")
            return
        if rem_user in user_coins:
            del user_coins[rem_user]
            await update.message.reply_text(f"✅ User `{rem_user}` remove ho gaya!", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Ye user exist nahi karta!")
    except ValueError:
        await update.message.reply_text("❌ Galat ID!")

async def add_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Sirf admin ye command use kar sakta hai!")
        return
    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: /addcoins 123456789 10")
        return
    try:
        target_user = int(context.args[0])
        coins = int(context.args[1])
        if target_user not in user_coins:
            await update.message.reply_text("❌ Ye user exist nahi karta! Pehle /adduser karo.")
            return
        user_coins[target_user] += coins
        await update.message.reply_text(
            f"✅ User `{target_user}` ko *{coins}* coins add ho gaye!\n💰 Total: *{user_coins[target_user]}*",
            parse_mode="Markdown"
        )
    except ValueError:
        await update.message.reply_text("❌ Galat format! /addcoins 123456789 10")

async def remove_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Sirf admin ye command use kar sakta hai!")
        return
    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: /removecoins 123456789 5")
        return
    try:
        target_user = int(context.args[0])
        coins = int(context.args[1])
        if target_user not in user_coins:
            await update.message.reply_text("❌ Ye user exist nahi karta!")
            return
        user_coins[target_user] = max(0, user_coins[target_user] - coins)
        await update.message.reply_text(
            f"✅ User `{target_user}` se *{coins}* coins remove ho gaye!\n💰 Remaining: *{user_coins[target_user]}*",
            parse_mode="Markdown"
        )
    except ValueError:
        await update.message.reply_text("❌ Galat format! /removecoins 123456789 5")

async def check_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Sirf admin ye command use kar sakta hai!")
        return
    if not context.args:
        await update.message.reply_text("❌ Usage: /checkcoins 123456789")
        return
    try:
        target_user = int(context.args[0])
        coins = user_coins.get(target_user, None)
        if coins is None:
            await update.message.reply_text("❌ Ye user exist nahi karta!")
        else:
            await update.message.reply_text(f"💰 User `{target_user}` ke coins: *{coins}*", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ Galat ID!")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Sirf admin ye command use kar sakta hai!")
        return
    if not user_coins:
        await update.message.reply_text("❌ Koi user nahi hai!")
        return
    users = "\n".join([f"`{u}` — 💰 *{c}* coins {'👑' if u == ADMIN_ID else ''}" for u, c in user_coins.items()])
    await update.message.reply_text(f"👥 *All Users:*\n\n{users}", parse_mode="Markdown")

async def handle_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ *Access Denied!*", parse_mode="Markdown")
        return ConversationHandler.END
    coins = user_coins.get(user_id, 0)
    if coins <= 0 and not is_admin(user_id):
        await update.message.reply_text("❌ *Coins khatam ho gaye!*\n\nAdmin se coins lо.", parse_mode="Markdown")
        return ConversationHandler.END
    doc = update.message.document
    if not doc.file_name.endswith('.xlsx'):
        await update.message.reply_text("❌ Sirf .xlsx file bhejo!")
        return WAITING_EXCEL
    user_data_store[user_id] = {
        'excel_file_id': doc.file_id,
        'excel_name': doc.file_name,
        'photo_file_id': None
    }
    await update.message.reply_text(
        f"✅ *Excel mil gayi!*\n💰 Coins: *{coins}*\n\n📸 Photo bhejo ya /skip karo",
        parse_mode="Markdown"
    )
    return WAITING_PHOTO

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ *Access Denied!*", parse_mode="Markdown")
        return ConversationHandler.END
    if user_id not in user_data_store:
        await update.message.reply_text("❌ Pehle Excel file bhejo!")
        return WAITING_EXCEL
    photo = update.message.photo[-1]
    user_data_store[user_id]['photo_file_id'] = photo.file_id
    await update.message.reply_text("✅ *Photo mil gayi!*\n\n⚡ PDF ban rahi hai...", parse_mode="Markdown")
    await generate_and_send_pdf(update, context, user_id)
    return WAITING_EXCEL

async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ *Access Denied!*", parse_mode="Markdown")
        return ConversationHandler.END
    if user_id not in user_data_store:
        await update.message.reply_text("❌ Pehle Excel file bhejo!")
        return WAITING_EXCEL
    await update.message.reply_text("⚡ *PDF ban rahi hai (bina photo)...*", parse_mode="Markdown")
    await generate_and_send_pdf(update, context, user_id)
    return WAITING_EXCEL

async def generate_and_send_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    data = user_data_store.get(user_id)
    if not data:
        await update.message.reply_text("❌ Kuch galat hua, dobara try karo!")
        return

    photo_status = "✅ Included" if data['photo_file_id'] else "❌ Not included"
    status_msg = await update.message.reply_text(
        f"🖼️ *Photo Status:* {photo_status}\n📥 Downloading your file...",
        parse_mode="Markdown"
    )

    try:
        # Download Excel
        excel_file = await context.bot.get_file(data['excel_file_id'])
        excel_bytes = await excel_file.download_as_bytearray()

        files = {
            'excel': (data['excel_name'], bytes(excel_bytes), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }

        # Download photo if provided
        if data['photo_file_id']:
            photo_file = await context.bot.get_file(data['photo_file_id'])
            photo_bytes = await photo_file.download_as_bytearray()
            files['photo'] = ('photo.jpg', bytes(photo_bytes), 'image/jpeg')

        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=status_msg.message_id,
            text=f"🖼️ *Photo Status:* {photo_status}\n⚡ Processing... please wait.",
            parse_mode="Markdown"
        )

        # Step 1: Generate images on website
        response = requests.post(WEBSITE_URL, files=files, timeout=300)
        if response.status_code != 200:
            await update.message.reply_text("❌ Website se images generate nahi hui. Dobara try karo.")
            return

        excel_name = os.path.splitext(data['excel_name'])[0]

        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=status_msg.message_id,
            text=f"🖼️ *Photo Status:* {photo_status}\n📄 Generating PDF...",
            parse_mode="Markdown"
        )

        # Step 2: Generate PDF from images
        images = [f"{excel_name}_page{i}.png" for i in range(1, 20)]
        pdf_response = requests.post(
            PDF_URL,
            data=[('make_pdf', '1')] + [('images[]', img) for img in images],
            timeout=300
        )

        # ✅ FIX: Check by content length and PDF magic bytes, not just Content-Type
        content = pdf_response.content
        is_pdf = (
            pdf_response.status_code == 200 and
            len(content) > 100 and
            content[:4] == b'%PDF'
        )

        if is_pdf:
            # ✅ FIX: Coin deduct karo - admin ka nahi, baaki sab ka
            if not is_admin(user_id):
                user_coins[user_id] = max(0, user_coins[user_id] - 1)

            remaining = user_coins.get(user_id, 0)
            now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            filename = f"FIA_Travel_History_{excel_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=status_msg.message_id,
                text=(
                    f"✅ *FIA Travel History*\n\n"
                    f"📁 File: `{excel_name}`\n"
                    f"{'📸 With Photo' if data['photo_file_id'] else '🚫 Without Photo'}\n"
                    f"📅 Generated: {now}\n"
                    f"💰 Remaining Coins: *{remaining}*"
                ),
                parse_mode="Markdown"
            )

            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=content,
                filename=filename,
                caption="✅ *Document ready for printing!*",
                parse_mode="Markdown"
            )
            await update.message.reply_text(
                "✅ *Process completed! Aap doosri Excel file bhej sakte hain.*",
                parse_mode="Markdown"
            )
        else:
            logger.error(f"PDF response status: {pdf_response.status_code}, content start: {content[:50]}")
            await update.message.reply_text("⚠️ PDF generate nahi hui. Dobara try karo.")

    except requests.exceptions.Timeout:
        await update.message.reply_text("⏱️ Timeout! Dobara try karo.")
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        if user_id in user_data_store:
            del user_data_store[user_id]

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_data_store:
        del user_data_store[user_id]
    await update.message.reply_text("❌ Cancel ho gaya. /start karo.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Document.FileExtension("xlsx"), handle_excel)
        ],
        states={
            WAITING_EXCEL: [MessageHandler(filters.Document.FileExtension("xlsx"), handle_excel)],
            WAITING_PHOTO: [
                MessageHandler(filters.PHOTO, handle_photo),
                CommandHandler("skip", skip_photo),
                MessageHandler(filters.Document.FileExtension("xlsx"), handle_excel),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("adduser", add_user))
    app.add_handler(CommandHandler("removeuser", remove_user))
    app.add_handler(CommandHandler("addcoins", add_coins))
    app.add_handler(CommandHandler("removecoins", remove_coins))
    app.add_handler(CommandHandler("checkcoins", check_coins))
    app.add_handler(CommandHandler("users", list_users))
    app.add_handler(CommandHandler("mycoins", my_coins))
    print("Bot chal raha hai...")
    app.run_polling()

if __name__ == "__main__":
    main()
