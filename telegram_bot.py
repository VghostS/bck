from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import os

# Define the start function
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('HI')

def EXE(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('EXE')

def main() -> None:
    # Get the bot token from the environment variable
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("No token provided")

    updater = Updater(token)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register the /start command handler
    dispatcher.add_handler(CommandHandler("start", start))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    updater.idle()

if __name__ == '__main__':
    main()
