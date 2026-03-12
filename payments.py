from bot_sender import send_message, send_invoice, answer_pre_checkout_query
from db_core import grant_premium, record_payment, log_to_bigquery

def get_premium_keyboard():
    """Лимит біткенде шығатын батырма"""
    return {
        "inline_keyboard": [
            [{"text": "⭐️ Premium алу (100 ⭐️)", "callback_data": "buy_premium"}]
        ]
    }

def handle_buy_premium_callback(chat_id, callback_id):
    """Адам батырманы басқанда шот жіберу"""
    send_invoice(chat_id)

def process_pre_checkout(update):
    """Телеграм 'Төлемді қабылдайсың ба?' деп сұрағанда"""
    query_id = update["pre_checkout_query"]["id"]
    answer_pre_checkout_query(query_id, ok=True)

def process_successful_payment(message):
    """Төлем сәтті өткендегі әрекет"""
    chat_id = message["chat"]["id"]
    username = message["chat"].get("username", "Belgisiz")
    payment_info = message["successful_payment"]
    
    amount = payment_info["total_amount"]
    payload = payment_info["invoice_payload"]
    charge_id = payment_info["telegram_payment_charge_id"]
    
    # 1. Базаға 30 күн қосу
    grant_premium(chat_id, days=30)
    
    # 2. Тарихты сақтау
    record_payment(chat_id, username, amount, payload, charge_id)
    
    # 3. Статистикаға жазу
    log_to_bigquery(chat_id, "payment", f"{amount} Stars", "Сәтті төлем")
    
    # 4. Құттықтау мәтіні (Креативті)
    success_text = (
        "🎉 <b>ҚҰТТЫҚТАЙМЫЗ! Төлем сәтті өтті!</b> 🎉\n\n"
        "Сіз енді <b>Premium</b> қолданушысыз! 👑\n"
        "Алдағы 30 күн бойы сіз үшін барлық шектеулер алынып тасталды. "
        "Суреттерді, мәтіндерді және локацияларды еш алаңдамай шексіз тексере беріңіз!\n\n"
        "<i>Біздің жобаны қолдағаныңыз үшін үлкен рақмет! ❤️</i>"
    )
    send_message(chat_id, success_text)