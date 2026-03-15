import requests
from bot_sender import send_message, send_invoice, answer_pre_checkout_query
from db_core import grant_premium, record_payment, log_to_bigquery, create_gift_code
from config import BOT_TOKEN

def get_premium_keyboard():
    return {
        "inline_keyboard": [[{"text": "⭐️ Premium алу (100 ⭐️)", "callback_data": "buy_premium", "style": "primary"}]]
    }

def handle_buy_premium_callback(chat_id, callback_id):
    send_invoice(chat_id)

def process_pre_checkout(update):
    query_id = update["pre_checkout_query"]["id"]
    answer_pre_checkout_query(query_id, ok=True)

def get_telegram_user_id_by_username(username):
    """
    Telegram Bot API арқылы @username-нен user_id алу.
    Ескерту: бот сол адаммен бұрын сөйлескен болса ғана жұмыс істейді.
    """
    clean = username.lstrip("@")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChat"
    resp = requests.get(url, params={"chat_id": f"@{clean}"}).json()
    if resp.get("ok"):
        return resp["result"].get("id")
    return None

def send_gift_invoice_to_username(chat_id, gift_type, recipient_username):
    """Username арқылы сыйлық — шотты жіберу"""
    from bot_sender import send_gift_invoice
    send_gift_invoice(chat_id, gift_type, recipient_username=recipient_username)

def process_successful_payment(message):
    chat_id = message["chat"]["id"]
    username = message["chat"].get("username", message["chat"].get("first_name", "Жақсы адам"))
    payment_info = message["successful_payment"]
    
    amount = payment_info["total_amount"]
    payload = payment_info["invoice_payload"]
    charge_id = payment_info["telegram_payment_charge_id"]
    
    record_payment(chat_id, username, amount, payload, charge_id)
    log_to_bigquery(chat_id, "payment", f"{amount} Stars", "Сәтті төлем")
    
    # 1. ӨЗІНЕ АЛСА
    if payload == "premium_30_days":
        grant_premium(chat_id, days=30)
        success_text = (
            "🎉 <b>Төлем сәтті өтті! Құттықтаймыз!</b>\n\n"
            "Сіз енді <b>Premium</b> қолданушысыз 👑\n"
            "Алдағы 30 күн бойы барлық шектеулер алынып тасталды. Жобамызды қолдағаныңыз үшін үлкен рақмет! ❤️"
        )
        send_message(chat_id, success_text, message_effect_id="5046509860389126442")
        
    # 2. СІЛТЕМЕ АРҚЫЛЫ СЫЙЛЫҚҚА АЛСА
    elif payload == "gift_premium_30_days_link":
        code = create_gift_code(chat_id, username)
        bot_username = "alladalbot" 
        gift_link = f"https://t.me/{bot_username}?start={code}"
        
        success_text = (
            "🎁 <b>Сыйлық сәтті сатып алынды!</b>\n\n"
            "Төмендегі сілтемені көшіріп, сыйлағыңыз келген адамға (WhatsApp, Telegram арқылы) жіберіңіз:\n\n"
            f"👉 {gift_link}\n\n"
            "<i>Ескерту: Бұл сілтемені тек 1 адам ғана қолдана алады!</i>"
        )
        send_message(chat_id, success_text, message_effect_id="5046509860389126442")

    # 3. ТЕЛЕГРАМ АРҚЫЛЫ (ИНЛАЙН) СЫЙЛЫҚҚА АЛСА
    elif payload == "gift_premium_30_days_inline":
        code = create_gift_code(chat_id, username)
        
        success_text = (
            "🎁 <b>Сыйлық сәтті сатып алынды!</b>\n\n"
            "Төмендегі <b>«🎁 Сыйлықты жіберу»</b> батырмасын басып, досыңызды таңдаңыз. "
            "Сыйлық тікелей чатқа әдемі қорап болып барады!\n\n"
            "<i>Ескерту: Бұл сыйлықты тек 1 адам ғана аша алады!</i>"
        )
        gift_markup = {
            "inline_keyboard": [[
                {"text": "🎁 Сыйлықты жіберу", "switch_inline_query": f"giftbox_{code}", "style": "success"}
            ]]
        }
        send_message(chat_id, success_text, reply_markup=gift_markup, message_effect_id="5046509860389126442")

    # 4. @USERNAME АРҚЫЛЫ СЫЙЛЫҚҚА АЛСА
    elif payload.startswith("gift_premium_30_days_username:"):
        recipient_username = payload.split(":", 1)[1]
        bot_username = "alladalbot"

        recipient_id = get_telegram_user_id_by_username(recipient_username)
        direct_sent = False

        if recipient_id:
            # Алушы ботқа бұрын жазған — тікелей хабар жіберуге болады
            code = create_gift_code(chat_id, username, recipient_username=recipient_username)
            gift_link = f"https://t.me/{bot_username}?start={code}"
            recipient_text = (
                f"🎁 <b>Сізге сыйлық келді!</b>\n\n"
                f"Бір жанашыр сізге <b>30 күн Premium</b> сыйлады!\n\n"
                f"Сыйлықты қабылдау үшін төмендегі батырманы басыңыз 👇\n\n"
                f"<i>Батырманы басқан сәтте Premium 30 күнге автоматты іске қосылады.</i>"
            )
            recipient_markup = {
                "inline_keyboard": [[
                    {"text": "🎁 Сыйлықты қабылдау", "url": gift_link}
                ]]
            }
            result = send_message(recipient_id, recipient_text, reply_markup=recipient_markup, message_effect_id="5046509860389126442")
            direct_sent = result is not None
        else:
            # Алушы ботқа жазбаған — pending_gifts-ке сақтаймыз, алғаш жазғанда автоматты береді
            code = create_gift_code(chat_id, username, recipient_username=recipient_username)
            gift_link = f"https://t.me/{bot_username}?start={code}"

        # Сатып алушыға хабар — тікелей жетті ме жетпеді ме соған қарай
        if direct_sent:
            success_text = (
                f"🎁 <b>Сыйлық сәтті жіберілді!</b>\n\n"
                f"<b>@{recipient_username}</b> пайдаланушысына хабар жетті. "
                f"Ол «Сыйлықты қабылдау» батырмасын басқан сәтте Premium автоматты іске қосылады.\n\n"
                f"<i>Запасқа сілтеме (егер хабарды көрмесе жіберіңіз):</i>\n"
                f"👉 {gift_link}\n\n"
                f"<i>Ескерту: Бұл сілтемені тек 1 адам ғана қолдана алады!</i>"
            )
        else:
            # Тікелей хабар жетпеді — @username ботқа бұрын жазбаған
            success_text = (
                f"🎁 <b>Сыйлық сәтті сатып алынды!</b>\n\n"
                f"<b>@{recipient_username}</b> пайдаланушысы ботқа бұрын жазбағандықтан, "
                f"хабар тікелей жете алмады.\n\n"
                f"📎 Төмендегі сілтемені досыңызға жіберіңіз:\n"
                f"👉 {gift_link}\n\n"
                f"⭐️ <b>Маңызды:</b> Досыңыз осы сілтемені басқан сәтте Premium <b>автоматты 30 күнге іске қосылады</b> — "
                f"ешқандай қосымша әрекет қажет емес!\n\n"
                f"<i>Ескерту: Бұл сілтемені тек 1 адам ғана қолдана алады!</i>"
            )
        send_message(chat_id, success_text, message_effect_id="5046509860389126442")
