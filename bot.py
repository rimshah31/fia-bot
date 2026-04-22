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
WEBSITE_URL = "http://ababil.infinityfree.me/ababiil.php"
PDF_URL = "http://ababil.infinityfree.me/pdf.php"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WAITING_EXCEL = 1
WAITING_PHOTO = 2

user_data_store = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *FIA Travel History Bot*\n\nExcel file (.xlsx) bhejo!",
        parse_mode="Markdown"
    )
    return WAITING_EXCEL

async def handle_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    doc = update.message.document
    if not doc.file_name.endswith('.xlsx'):
        await update.message.reply_text("❌ Sirf .xlsx file bhejo!")
        return WAITING_EXCEL
    user_data_store[user_id] = {
        'excel_file_id': doc.file_id,
        'excel_name': doc.file_name,
        'photo_file_id': None
    }
    await update.message.reply_text("✅ *Excel mil gayi!*\n\n📸 Photo bhejo ya /skip karo", parse_mode="Markdown")
    return WAITING_PHOTO

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
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
        excel_file = await context.bot.get_file(data['excel_file_id'])
        excel_bytes = await excel_file.download_as_bytearray()
        files = {
            'excel': (data['excel_name'], bytes(excel_bytes), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
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
        response = requests.post(WEBSITE_URL, files=files, timeout=300)
        excel_name = os.path.splitext(data['excel_name'])[0]
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=status_msg.message_id,
            text=f"🖼️ *Photo Status:* {photo_status}\n📄 Generating PDF...",
            parse_mode="Markdown"
        )
        images = []
        for i in range(1, 20):
            images.append(f"{excel_name}_page{i}.png")
        pdf_response = requests.post(
            PDF_URL,
            data=[('make_pdf', '1')] + [('images[]', img) for img in images],
            timeout=300
        )
        if pdf_response.status_code == 200 and 'application/pdf' in pdf_response.headers.get('Content-Type', ''):
            now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            filename = f"FIA_Travel_History_{excel_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=status_msg.message_id,
                text=f"✅ *FIA Travel History*\n\n📁 File: `{excel_name}`\n{'📸 With Photo' if data['photo_file_id'] else '🚫 Without Photo'}\n📅 Generated: {now}",
                parse_mode="Markdown"
            )
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=pdf_response.content,
                filename=filename,
                caption="✅ *Document ready for printing!*",
                parse_mode="Markdown"
            )
            await update.message.reply_text("✅ *Process completed! Aap doosri Excel file bhej sakte hain.*", parse_mode="Markdown")
        else:
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
    print("Bot chal raha hai...")
    app.run_polling()

if __name__ == "__main__":
    main()
