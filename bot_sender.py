import requests
from config import BOT_TOKEN

def send_message(chat_id, text, reply_markup=None, message_effect_id=None, reply_to_message_id=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    
    if reply_markup: 
        payload["reply_markup"] = reply_markup
        
    if message_effect_id: 
        payload["message_effect_id"] = str(message_effect_id)
        
    if reply_to_message_id:
        payload["reply_parameters"] = {"message_id": reply_to_message_id}
    
    resp = requests.post(url, json=payload).json()
    
    if resp.get("ok"):
        return resp["result"]["message_id"]
        
    elif message_effect_id:
        print(f"Telegram Эффект қабылдамады: {resp}")
        del payload["message_effect_id"]
        resp2 = requests.post(url, json=payload).json()
        if resp2.get("ok"):
            return resp2["result"]["message_id"]
        else:
            print(f"[send_message] Қате: {resp2}")
            
    else:
        print(f"[send_message] Қате: {resp}")
        
    return None

def edit_message(chat_id=None, message_id=None, text=None, reply_markup=None, inline_message_id=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
    payload = {"text": text, "parse_mode": "HTML"}
    if inline_message_id:
        payload["inline_message_id"] = inline_message_id
    else:
        payload["chat_id"] = chat_id
        payload["message_id"] = message_id
    if reply_markup:
        payload["reply_markup"] = reply_markup
    resp = requests.post(url, json=payload).json()
    if not resp.get("ok"):
        print(f"[edit_message] Қате: {resp}")

def edit_reply_markup(chat_id=None, message_id=None, reply_markup=None, inline_message_id=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageReplyMarkup"
    payload = {}
    if inline_message_id:
        payload["inline_message_id"] = inline_message_id
    else:
        payload["chat_id"] = chat_id
        payload["message_id"] = message_id
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    resp = requests.post(url, json=payload).json()
    if not resp.get("ok"):
        print(f"[edit_reply_markup] Қате: {resp}")

def answer_callback(callback_query_id, text=None, show_alert=False):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
    payload = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
        payload["show_alert"] = show_alert
    resp = requests.post(url, json=payload).json()
    if not resp.get("ok"):
        print(f"[answer_callback] Қате: {resp}")

def answer_inline_query(inline_query_id, results, button=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerInlineQuery"
    payload = {"inline_query_id": inline_query_id, "results": results, "cache_time": 300}
    if button:
        payload["button"] = button
    resp = requests.post(url, json=payload).json()
    if not resp.get("ok"):
        print(f"[answer_inline_query] Қате: {resp}")

def download_photo(file_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"
    resp = requests.get(url).json()
    if not resp.get("ok"):
        print(f"[download_photo] getFile қатесі: {resp}")
        return None
    file_path = resp["result"]["file_path"]
    download_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    return requests.get(download_url).content

def send_invoice(chat_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendInvoice"
    payload = {
        "chat_id": chat_id,
        "title": "⭐️ Premium Жазылым (30 күн)",
        "description": "Шексіз іздеу, суретпен тану және жақын маңдағы орындарды шектеусіз көру мүмкіндігі!",
        "payload": "premium_30_days",
        "provider_token": "", 
        "currency": "XTR",    
        "prices": [{"label": "Premium", "amount": 100}]
    }
    resp = requests.post(url, json=payload).json()
    if not resp.get("ok"):
        print(f"[send_invoice] Қате: {resp}")

def answer_pre_checkout_query(pre_checkout_query_id, ok=True, error_message=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerPreCheckoutQuery"
    payload = {"pre_checkout_query_id": pre_checkout_query_id, "ok": ok}
    if not ok and error_message:
        payload["error_message"] = error_message
    resp = requests.post(url, json=payload).json()
    if not resp.get("ok"):
        print(f"[answer_pre_checkout_query] Қате: {resp}")

def send_chat_action(chat_id, action="typing"):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendChatAction"
    payload = {"chat_id": chat_id, "action": action}
    requests.post(url, json=payload)

def delete_message(chat_id, message_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage"
    payload = {"chat_id": chat_id, "message_id": message_id}
    resp = requests.post(url, json=payload).json()
    if not resp.get("ok"):
        print(f"[delete_message] Қате: {resp}")

def set_message_reaction(chat_id, message_id, emoji, is_big=True):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setMessageReaction"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "reaction": [{"type": "emoji", "emoji": emoji}],
        "is_big": is_big
    }
    requests.post(url, json=payload)

def send_gift_invoice(chat_id, gift_type, recipient_username=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendInvoice"

    if gift_type == "inline":
        desc = "Төлем жасалғаннан кейін сіз сыйлықты досыңыздың чатына тікелей (инлайн қорап қылып) жібере аласыз."
        invoice_payload = "gift_premium_30_days_inline"
    elif gift_type == "username" and recipient_username:
        clean = recipient_username.lstrip("@")
        desc = f"Төлем жасалғаннан кейін @{clean} пайдаланушысына сыйлық автоматты жіберіледі."
        invoice_payload = f"gift_premium_30_days_username:{clean}"
    else:
        desc = "Төлем жасалғаннан кейін сізге арнайы сыйлық сілтемесі беріледі. Соны досыңызға жібересіз."
        invoice_payload = "gift_premium_30_days_link"

    payload = {
        "chat_id": chat_id,
        "title": "🎁 Premium Сыйлық (30 күн)",
        "description": desc,
        "payload": invoice_payload,
        "provider_token": "", 
        "currency": "XTR",    
        "prices": [{"label": "Premium Сыйлық", "amount": 100}]
    }
    resp = requests.post(url, json=payload).json()
    if not resp.get("ok"):
        print(f"[send_gift_invoice] Қате: {resp}")
