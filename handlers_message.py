from bot_sender import send_message, edit_message, send_chat_action, send_sticker, delete_message, download_photo
from db_core import (add_user, save_chat_history, log_to_bigquery, check_access, 
                     increment_usage, revoke_premium, get_user_gender)
from search_logic import search_data, get_nearby_companies
from formatters import format_detail_message
from ai_core import handle_photo, chat_with_ai
from payments import process_successful_payment, get_premium_keyboard

SYMBAT_ID = 1042456426
EFFECT_HALAL = "5046509860389126442"
EFFECT_EXPIRED = "5104841245755180586"
LOADING_STICKER = "CAACAgIAAxkBAAID_mmzSRfbvjOYJ5KV8BFXy1aZQi8zAALsjAACAX2ISdhu-CgadkQqOgQ"

def handle_message(msg):
    chat_id = msg["chat"]["id"]
    first_name = msg["chat"].get("first_name", "Досым")
    username = msg["chat"].get("username", "жоқ")
    is_symbat = (chat_id == SYMBAT_ID)
    
    if "successful_payment" in msg:
        process_successful_payment(msg)
        return
        
    if "refunded_payment" in msg:
        revoke_premium(chat_id)
        send_message(chat_id, "⚠️ Сіз төлемді қайтарып алдыңыз. Premium статусыңыз өшірілді.")
        return
    
    if "photo" in msg:
        has_access, tier = check_access(chat_id, is_symbat)
        if not has_access:
            send_message(chat_id, tier, reply_markup=get_premium_keyboard())
            return
        
        sticker_msg_id = send_sticker(chat_id, LOADING_STICKER)
        send_chat_action(chat_id, "typing")
            
        photo_id = msg["photo"][-1]["file_id"]
        image_bytes = download_photo(photo_id)
        if image_bytes:
            result_msg, markup = handle_photo(image_bytes, chat_id, username)
            
            effect = None
            if tier in["premium", "VIP"]:
                if "✅" in result_msg: effect = EFFECT_HALAL
                elif "⚠️" in result_msg or "🚫" in result_msg: effect = EFFECT_EXPIRED
            
            send_message(chat_id, result_msg, reply_markup=markup, message_effect_id=effect)
            
            if sticker_msg_id:
                delete_message(chat_id, sticker_msg_id)
                
            save_chat_history(chat_id, "user", "Мен саған бір сурет жібердім")
            save_chat_history(chat_id, "model", result_msg)
            log_to_bigquery(chat_id, "photo_search", "Сурет", "Тексерілді")
            increment_usage(chat_id)

    elif "location" in msg:
        has_access, tier = check_access(chat_id, is_symbat)
        if not has_access:
            send_message(chat_id, tier, reply_markup=get_premium_keyboard())
            return
        
        sticker_msg_id = send_sticker(chat_id, LOADING_STICKER)
        send_chat_action(chat_id, "find_location")
            
        lat, lon = msg["location"]["latitude"], msg["location"]["longitude"]
        text, markup = get_nearby_companies(lat, lon, page=1)
        
        send_message(chat_id, text, reply_markup=markup)
        
        if sticker_msg_id:
            delete_message(chat_id, sticker_msg_id)
            
        log_to_bigquery(chat_id, "location_search", f"{lat}, {lon}", "Тізім берілді")
        increment_usage(chat_id)

    elif "text" in msg:
        text = msg["text"]

        if text == "/start":
            send_chat_action(chat_id, "typing")
            
            if is_symbat:
                welcome_text = f"Сәлем, Ботам! ❤️\n\nБұл сенің сүйікті жігітің жасаған ҚМДБ Халал боты ғой. Маған кез келген өнімнің атын жаз немесе суретін жібер, мен сен үшін бәрін тауып беремін! 😘"
                keyboard = {"keyboard": [[{"text": "📍 Тұрған орнымды жіберу", "request_location": True}]], "resize_keyboard": True}
                send_message(chat_id, welcome_text, reply_markup=keyboard)
                
                add_user(chat_id, first_name, username)
                save_chat_history(chat_id, "user", text)
                save_chat_history(chat_id, "model", welcome_text)
                log_to_bigquery(chat_id, "start", "/start", "Сымбат кірді")
            else:
                current_gender = get_user_gender(chat_id)
                
                if not current_gender:
                    welcome_text = f"Сәлем, {first_name}! 👋\n\nМен — кез келген өнімнің немесе дәмхананың халал екенін тез әрі нақты тексеріп беретін көмекшіңізбін.\n\nЖақынырақ танысу үшін, жынысыңызды таңдаңызшы:"
                    gender_markup = {"inline_keyboard": [[{"text": "🙎‍♂️ Ер азамат", "callback_data": "gender:male"},
                         {"text": "🙎‍♀️ Нәзік жанды", "callback_data": "gender:female"}]]}
                    send_message(chat_id, welcome_text, reply_markup=gender_markup)
                    
                    add_user(chat_id, first_name, username)
                    save_chat_history(chat_id, "user", text)
                    log_to_bigquery(chat_id, "start", "/start", "Жаңа қолданушы (Жыныс сұралды)")
                else:
                    welcome_text = f"Қайта оралуыңызбен, {first_name}! 👋\n\nМен жұмысқа дайынмын. Тексеретін өнім бар ма немесе тамақтанатын орын іздейміз бе?"
                    keyboard = {"keyboard": [[{"text": "📍 Тұрған орнымды жіберу", "request_location": True}]], "resize_keyboard": True}
                    send_message(chat_id, welcome_text, reply_markup=keyboard)
                    
                    save_chat_history(chat_id, "user", text)
                    save_chat_history(chat_id, "model", welcome_text)
                    log_to_bigquery(chat_id, "start", "/start", "Ескі қолданушы")
                    
        else:
            found_items = search_data(text)
            
            if found_items:
                has_access, tier = check_access(chat_id, is_symbat)
                if not has_access:
                    send_message(chat_id, tier, reply_markup=get_premium_keyboard())
                    return
                    
                send_chat_action(chat_id, "typing")
                
                if len(found_items) == 1:
                    reply_text, markup = format_detail_message(found_items[0])
                    
                    effect = None
                    if tier in["premium", "VIP"]:
                        status_text = found_items[0].get("status", "")
                        if "Белсенді" in status_text or "Рұқсат" in status_text: effect = EFFECT_HALAL
                        elif "Мерзімі" in status_text or "⚠️" in status_text or "Қайтарып" in status_text or "🚫" in status_text: effect = EFFECT_EXPIRED
                        
                    send_message(chat_id, reply_text, reply_markup=markup, message_effect_id=effect)
                    
                    save_chat_history(chat_id, "user", text)
                    save_chat_history(chat_id, "model", reply_text)
                    log_to_bigquery(chat_id, "text_search", text, "Табылды (1)")
                    increment_usage(chat_id)
                else:
                    reply_text = f"🔍 <b>Мен бірнеше нұсқа таптым. Сізге нақты қайсысы керек?</b>\n\n"
                    keyboard =[]
                    for idx, item in enumerate(found_items[:5]):
                        if item['type'] == 'Мекеме':
                            desc_text = f"📍 {item.get('address', '')}"
                        else:
                            desc_text = f"🏷 {item.get('desc', '')}"
                            
                        reply_text += f"<b>{idx+1}. «{item['title']}»</b>\n{desc_text}\n\n"
                        t_code = "c" if item['type'] == "Мекеме" else "i"
                        keyboard.append([{"text": f"{idx+1}. «{item['title']}»", "callback_data": f"itm:{t_code}:{item['id']}"}])
                        
                    send_message(chat_id, reply_text, reply_markup={"inline_keyboard": keyboard})
                    
                    save_chat_history(chat_id, "user", text)
                    save_chat_history(chat_id, "model", reply_text)
                    log_to_bigquery(chat_id, "text_search", text, "Табылды (Көп)")
                    increment_usage(chat_id)
            else:
                _, tier = check_access(chat_id, is_symbat)
                
                sticker_msg_id = send_sticker(chat_id, LOADING_STICKER)
                send_chat_action(chat_id, "typing")
                
                wait_msg_id = send_message(chat_id, "✍️...")
                
                if wait_msg_id:
                    ai_reply = chat_with_ai(chat_id, text, is_symbat, chat_id=chat_id, message_id=wait_msg_id)
                    keys = {"inline_keyboard": [[{"text": "👍 Пайдалы", "callback_data": "fb:good:ai"}, {"text": "👎 Қате", "callback_data": "fb:bad:ai"}]]}
                    
                    edit_message(chat_id, wait_msg_id, ai_reply, reply_markup=keys)
                    if sticker_msg_id:
                        delete_message(chat_id, sticker_msg_id)
                else:
                    ai_reply = chat_with_ai(chat_id, text, is_symbat)
                    keys = {"inline_keyboard": [[{"text": "👍 Пайдалы", "callback_data": "fb:good:ai"}, {"text": "👎 Қате", "callback_data": "fb:bad:ai"}]]}
                    
                    send_message(chat_id, ai_reply, reply_markup=keys)
                    if sticker_msg_id:
                        delete_message(chat_id, sticker_msg_id)
                    
                save_chat_history(chat_id, "user", text)    
                save_chat_history(chat_id, "model", ai_reply)
                log_to_bigquery(chat_id, "ai_chat", text, "Табылмады/AI жауап берді")
