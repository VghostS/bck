from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext
import os
import asyncio
import nest_asyncio

# Apply the nest_asyncio patch
nest_asyncio.apply()

# Define the start function
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('HI WELCOME TO THE LAST STRIP')

# Define the play game function
async def play_game(update: Update, context: CallbackContext) -> None:
    # Create an inline keyboard with a button to launch the game
    keyboard = [
        [InlineKeyboardButton("Play TLS", callback_game=True)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send a game message
    await context.bot.send_game(
        chat_id=update.effective_chat.id,
        game_short_name="TheLastStrip",  # This must match the short_name you set with @BotFather
        reply_markup=reply_markup
    )

# Handle the callback when the game button is pressed
async def button_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    
    if query.game_short_name:
        # URL to your game - this should be an HTTPS URL
        game_url = "https://vkss.itch.io/tls"
        await query.answer(url=game_url)
    else:
        await query.answer("Something went wrong")

async def main() -> None:
    # Get the bot token from the environment variable
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("No token provided")
    
    application = Application.builder().token(token).build()
    
    # Register the command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("play_game", play_game))
    
    # Register callback query handler for the game button
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Start the Bot
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
