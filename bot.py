from telegram import Update, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, PreCheckoutQueryHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext
import os
import json
import asyncio
import nest_asyncio
import requests

# Apply the nest_asyncio patch
nest_asyncio.apply()

# The URL to your Flask app (the same Railway deployment)
API_URL = os.environ.get('API_URL', 'https://worker-production-b621.up.railway.app')

# Define available in-game items (same as in app.py)
GAME_ITEMS = {
    "coins_100": {
        "name": "100 Coins Pack",
        "description": "Get 100 in-game coins",
        "price": 5,  # 5 Stars
        "item_id": "coins_100"
    },
    "coins_500": {
        "name": "500 Coins Pack",
        "description": "Get 500 in-game coins",
        "price": 20,  # 20 Stars
        "item_id": "coins_500"
    },
    "special_character": {
        "name": "Special Character",
        "description": "Unlock a special character",
        "price": 50,  # 50 Stars
        "item_id": "special_character"
    }
}

# Telegram bot functions
async def start(update: Update, context: CallbackContext) -> None:
    if context.args and context.args[0].startswith('pay_'):
        # Extract item_id and user_id from the deep link
        parts = context.args[0].split('_')
        if len(parts) >= 3:
            item_id = parts[1]
            user_id = parts[2]
            return await initiate_telegram_payment(update, context, item_id, user_id)
    
    await update.message.reply_text('WELCOME TO THE LAST STRIP! Type /play_game to start playing or /shop to see available items.')

async def play_game(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Play TLS", callback_game=True)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_game(
        chat_id=update.effective_chat.id,
        game_short_name="TheLastStrip",
        reply_markup=reply_markup
    )

async def shop(update: Update, context: CallbackContext) -> None:
    keyboard = []
    for item_id, item in GAME_ITEMS.items():
        keyboard.append([InlineKeyboardButton(
            f"{item['name']} - {item['price']} Stars", 
            callback_data=f"buy_{item_id}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        'Welcome to the TLS Shop! Choose an item to purchase:',
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    
    if query.game_short_name:
        # Game button was pressed
        game_url = "https://vkss.itch.io/tls"
        await query.answer(url=game_url)
    elif query.data.startswith('buy_'):
        # Purchase button was pressed
        item_id = query.data.split('_')[1]
        user_id = str(query.from_user.id)
        await initiate_telegram_payment(update, context, item_id, user_id)
        await query.answer()
    else:
        await query.answer("Something went wrong")

async def initiate_telegram_payment(update: Update, context: CallbackContext, item_id, user_id) -> None:
    if item_id not in GAME_ITEMS:
        if hasattr(update, 'message'):
            await update.message.reply_text("Invalid item selection.")
        return
    
    item = GAME_ITEMS[item_id]
    
    # Create the invoice
    title = item["name"]
    description = item["description"]
    payload = f"{item_id}_{user_id}"
    provider_token = os.getenv("TELEGRAM_PAYMENT_TOKEN")
    currency = "STARS"  # Using Telegram Stars
    prices = [LabeledPrice(item["name"], item["price"] * 100)]  # Amount in cents
    
    # Notify our API about the pending purchase
    try:
        response = requests.post(
            f"{API_URL}/initiate_payment",
            json={"user_id": user_id, "item_id": item_id}
        )
        if not response.ok:
            error_msg = f"Failed to initiate payment: {response.text}"
            print(error_msg)
            if hasattr(update, 'message'):
                await update.message.reply_text("Error: Payment initiation failed.")
            return
    except Exception as e:
        print(f"Error notifying API: {str(e)}")
    
    chat_id = update.effective_chat.id
    
    # Send invoice
    await context.bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=description,
        payload=payload,
        provider_token=provider_token,
        currency=currency,
        prices=prices
    )

async def precheckout_callback(update: Update, context: CallbackContext) -> None:
    query = update.pre_checkout_query
    
    # Check if the payload is valid
    try:
        item_id, user_id = query.invoice_payload.split('_')
        if item_id in GAME_ITEMS:
            await query.answer(ok=True)
        else:
            await query.answer(ok=False, error_message="Invalid item")
    except Exception as e:
        await query.answer(ok=False, error_message="Invalid payment data")

async def successful_payment_callback(update: Update, context: CallbackContext) -> None:
    payment = update.message.successful_payment
    item_id, user_id = payment.invoice_payload.split('_')
    
    # Notify our API about the completed purchase
    try:
        response = requests.post(
            f"{API_URL}/update_payment_status",
            json={"user_id": user_id, "item_id": item_id, "status": "completed"}
        )
        if not response.ok:
            print(f"Failed to update payment status: {response.text}")
    except Exception as e:
        print(f"Error notifying API: {str(e)}")
    
    await update.message.reply_text(f"Payment successful! You've purchased {GAME_ITEMS[item_id]['name']}. Return to the game to claim your item.")

async def main() -> None:
    # Get the bot token from the environment variable
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("No token provided")
    
    application = Application.builder().token(token).build()
    
    # Register the command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("play_game", play_game))
    application.add_handler(CommandHandler("shop", shop))
    
    # Register callback query handler for buttons
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Register payment handlers
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    
    # Start the Bot
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
