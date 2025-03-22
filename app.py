from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Store pending purchases
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

@app.route('/', methods=['GET'])
def home():
    # Health check endpoint
    return jsonify({"status": "ok", "message": "Server is running"})

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
        "telegram_link": f"https://t.me/TheLastStrip?start=pay_{item_id}_{user_id}"
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

if __name__ == '__main__':
    # Make sure to use the PORT environment variable provided by Railway
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port)
