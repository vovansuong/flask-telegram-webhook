from flask import Flask, request
import requests
import re
import os

app = Flask(__name__)

# Thay thông tin thật của bạn
BOT_TOKEN = "7601479951:AAGUdGq7KUrKiWpRfemRkKbDjB3AxWvVRTw"
CHAT_ID = "6710869171"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})

def format_transaction_message(description, signature):
    # Pattern để tìm thông tin swap
    # Tìm mẫu: [địa chỉ] swapped [số lượng1] [token1] for [số lượng2] [token2]
    pattern = r"(\w+) swapped ([\d\.]+) (\w+) for ([\d\.]+) (.+)$"
    match = re.search(pattern, description)
    
    if match:
        wallet = match.group(1)
        amount1 = float(match.group(2))
        token1 = match.group(3)
        amount2 = float(match.group(4))
        token2 = match.group(5)
        
        # Rút gọn địa chỉ ví
        short_wallet = wallet[:4] + "..." + wallet[-4:]
        
        # Tạo thông báo theo định dạng mới
        message = f"🔄 GIAO DỊCH SWAP\n\n"
        message += f"👤 Ví: {short_wallet}\n"
        message += f"📤 BÁN: {amount1} {token1}\n"
        message += f"📥 MUA: {amount2} {token2}\n"
        message += f"🔗 Signature: {signature[:6]}...{signature[-6:]}"
        
        return message
    
    # Nếu không phải giao dịch swap hoặc không khớp pattern
    return f"🔔 Giao dịch mới:\n- Signature: {signature[:6]}...{signature[-6:]}\n- Tên Ví: {description}"

@app.route('/helius-webhook', methods=['POST'])
def helius_webhook():
    data = request.json
    
    # Xử lý trường hợp data là list
    if isinstance(data, list):
        for tx in data:
            try:
                if isinstance(tx, dict):
                    sig = tx.get('signature', 'N/A')
                    desc = tx.get('description', 'Giao dịch mới')
                    message = format_transaction_message(desc, sig)
                    send_telegram_message(message)
            except Exception as e:
                print(f"Lỗi khi xử lý giao dịch: {e}")
    # Xử lý trường hợp data là dict và có transactions
    elif isinstance(data, dict) and 'transactions' in data:
        for tx in data['transactions']:
            try:
                if isinstance(tx, dict):
                    sig = tx.get('signature', 'N/A')
                    desc = tx.get('description', 'Giao dịch mới')
                    message = format_transaction_message(desc, sig)
                    send_telegram_message(message)
            except Exception as e:
                print(f"Lỗi khi xử lý giao dịch: {e}")
    else:
        print("Định dạng dữ liệu không như mong đợi:", data)
        
    return '', 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Render sẽ truyền PORT qua biến môi trường
    app.run(host='0.0.0.0', port=port)