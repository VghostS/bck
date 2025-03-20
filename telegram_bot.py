from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
import os

# Define the start function
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('HI')

async def main() -> None:
    # Get the bot token from the environment variable
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("No token provided")

    application = Application.builder().token(token).build()

    # Register the /start command handler
    application.add_handler(CommandHandler("start", start))

    # Start the Bot
    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
