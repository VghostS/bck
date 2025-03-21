from telegram import Update, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, PreCheckoutQueryHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext
import os
import json
import asyncio
import nest_asyncio
from flask import Flask, request, jsonify
import threading

# Apply the nest_asyncio patch
nest_asyncio.apply()

# Create a Flask app for webhooks from Unity game
app = Flask(__name__)

# Store user sessions and pending purchases
user_sessions = {}
pending_purchases = {}

# Define available in-game items
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

# Setup webhook for Unity to call
@app.route('/initiate_payment', methods=['POST'])
def initiate_payment():
    data = request.json
    user_id = data.get('user_id')
    item_id = data.get('item_id')
    
    if not user_id or not item_id:
        return jsonify({"success": False, "message": "Missing user_id or item_id"}), 400
    
    if item_id not in GAME_ITEMS:
        return jsonify({"success": False, "message": "Invalid item_id"}), 400
    
    # Store the pending purchase
    pending_purchases[user_id] = {
        "item_id": item_id,
        "status": "pending"
    }
    
    # The actual payment will be initiated when the user returns to Telegram
    return jsonify({
        "success": True, 
        "message": "Payment initiated",
        "telegram_link": f"https://t.me/YourBotUsername?start=pay_{item_id}_{user_id}"
    })

@app.route('/check_payment_status', methods=['POST'])
def check_payment_status():
    data = request.json
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({"success": False, "message": "Missing user_id"}), 400
    
    purchase = pending_purchases.get(user_id, {})
    status = purchase.get("status", "not_found")
    
    if status == "completed":
        # Clear the purchase record after reporting completion
        item_id = purchase.get("item_id")
        pending_purchases.pop(user_id, None)
        return jsonify({"success": True, "status": status, "item_id": item_id})
    
    return jsonify({"success": True, "status": status})

# Start Flask in a separate thread
def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

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
    
    # Store in pending purchases
    pending_purchases[user_id] = {
        "item_id": item_id,
        "status": "pending"
    }
    
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
    
    # Mark purchase as completed
    if user_id in pending_purchases:
        pending_purchases[user_id]["status"] = "completed"
    
    await update.message.reply_text(f"Payment successful! You've purchased {GAME_ITEMS[item_id]['name']}. Return to the game to claim your item.")

async def main() -> None:
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
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
