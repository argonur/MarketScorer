from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
from dotenv import load_dotenv

load_dotenv()
# Carga el token desde variable de entorno o directamente
TOKEN = os.getenv('BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    chat_type = chat.type  # 'private', 'group', 'supergroup', etc.
    chat_id = chat.id

    if chat_type == "private":
        await update.message.reply_text(
            f"Hola {user.first_name}! Tu chat_id es: <code>{chat_id}</code>",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            f"Este grupo tiene chat_id: <code>{chat_id}</code>\n"
            f"Comando invocado por: <b>{user.first_name}</b> (ID: <code>{user.id}</code>)",
            parse_mode="HTML"
        )

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("Bot corriendo... Esperando comandos.")
    app.run_polling()