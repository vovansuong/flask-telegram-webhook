from flask import Flask, request
import requests
import os
import json

app = Flask(__name__)

# Thông tin thật của bạn
BOT_TOKEN = "7601479951:AAGUdGq7KUrKiWpRfemRkKbDjB3AxWvVRTw"
CHAT_ID = "6710869171"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})

def lamports_to_sol(lamports):
    return lamports / 1_000_000_000

def format_transaction_message(tx):
    signature = tx.get("signature", "N/A")
    events = tx.get("events", {})
    message = ""

    # Giao dịch SWAP
    if "swap" in events:
        swap = events["swap"]
        input_amt = swap.get("nativeInput") or swap.get("tokenInput", {})
        output_amt = swap.get("tokenOutput", {})

        amount1 = lamports_to_sol(input_amt.get("amount", 0))
        token1 = input_amt.get("mint", "Unknown Token")
        amount2 = lamports_to_sol(output_amt.get("amount", 0))
        token2 = output_amt.get("mint", "Unknown Token")

        message += "🔄 GIAO DỊCH SWAP\n\n"
        message += f"📤 BÁN: {amount1:.4f} ({token1})\n"
        message += f"📥 MUA: {amount2:.4f} ({token2})\n"

    # Giao dịch chuyển token SPL
    elif "tokenTransfers" in tx and tx["tokenTransfers"]:
        message += "🔁 CHUYỂN TOKEN\n\n"
        for t in tx["tokenTransfers"]:
            sender = t.get("fromUserAccount", "N/A")
            receiver = t.get("toUserAccount", "N/A")
            amount = lamports_to_sol(t.get("tokenAmount", {}).get("amount", 0))
            mint = t.get("mint", "Unknown Token")

            message += f"👤 Từ: {sender[:4]}...{sender[-4:]}\n"
            message += f"👥 Đến: {receiver[:4]}...{receiver[-4:]}\n"
            message += f"💰 Số lượng: {amount:.4f} ({mint})\n\n"

    # Giao dịch chuyển SOL
    elif "nativeTransfers" in tx and tx["nativeTransfers"]:
        message += "💸 CHUYỂN SOL\n\n"
        for t in tx["nativeTransfers"]:
            sender = t.get("fromUserAccount", "N/A")
            receiver = t.get("toUserAccount", "N/A")
            amount = lamports_to_sol(t.get("amount", 0))

            message += f"👤 Từ: {sender[:4]}...{sender[-4:]}\n"
            message += f"👥 Đến: {receiver[:4]}...{receiver[-4:]}\n"
            message += f"💰 Số lượng: {amount:.4f} SOL\n\n"

    else:
        # Giao dịch không xác định
        message += "🔔 GIAO DỊCH KHÁC\n\n"
        message += f"📄 Dữ liệu: {json.dumps(tx, indent=2)[:1000]}..."  # Giới hạn để không bị spam

    message += f"\n🔗 Signature: {signature[:6]}...{signature[-6:]}"
    return message

@app.route('/helius-webhook', methods=['POST'])
def helius_webhook():
    data = request.json

    transactions = []

    if isinstance(data, list):
        transactions = data
    elif isinstance(data, dict) and 'transactions' in data:
        transactions = data['transactions']

    for tx in transactions:
        try:
            message = format_transaction_message(tx)
            send_telegram_message(message)
        except Exception as e:
            print(f"Lỗi khi xử lý giao dịch: {e}")
            print(json.dumps(tx, indent=2))

    return '', 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Render truyền PORT qua biến môi trường
    app.run(host='0.0.0.0', port=port)
