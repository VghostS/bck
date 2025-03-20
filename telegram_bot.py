from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext
import os
import asyncio
import nest_asyncio

# Apply the nest_asyncio patch
nest_asyncio.apply()

# Define the start function
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('HI')

# Define the play game function
async def play_game(update: Update, context: CallbackContext) -> None:
    # Create an inline keyboard with a button to launch the game
    keyboard = [
        [InlineKeyboardButton("Play TLS", url="https://vkss.itch.io/tls")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Click the button below to play TLS!", 
        reply_markup=reply_markup
    )

async def main() -> None:
    # Get the bot token from the environment variable
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("No token provided")
    
    application = Application.builder().token(token).build()
    
    # Register the command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("play", play_game))
    
    # Start the Bot
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
