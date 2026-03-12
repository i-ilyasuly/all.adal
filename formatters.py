import uuid

def format_item_dict(data, type_name):
    if type_name == "Мекеме":
        d_start = data.get("certificate_date_start", "")
        d_end = data.get("certificate_date_end", "")
        cert_status = str(data.get("certificate_status", "active")).strip().lower()
        if cert_status == "active":
            st = "✅ Белсенді"
        elif cert_status == "expired":
            st = "❌ Мерзімі аяқталған"
        elif cert_status == "revoked":
            st = "🚫 Қайтарып алынған"
        else:
            st = f"⚠️ {cert_status}"
            
        return {
            "id": str(data.get("id", uuid.uuid4().hex[:8])),
            "type": "Мекеме",
            "title": data.get("title") or data.get("legal_name", "Белгісіз"),
            "desc": data.get("legal_name", ""),
            "address": data.get("address") or data.get("legal_address", "Мекенжай көрсетілмеген"),
            "map_link": data.get("map_link", ""),
            "date_start": d_start,
            "date_end": d_end,
            "status": st
        }
    else:
        st = "✅ Рұқсат етілген" if data.get("status", {}).get("name") == "Халяль" else "🚫 Күдікті"
        
        # Егер базада title жоқ болса, оның орнына slug-ты үлкен әріппен шығарамыз (мысалы e132 -> E132)
        item_title = data.get("title", "")
        if not item_title:
            item_title = str(data.get("slug", "")).upper()
            
        return {
            "id": str(data.get("id", uuid.uuid4().hex[:8])),
            "type": "Қоспа",
            "title": item_title,
            "desc": data.get("name", ""),
            "info": data.get("desc", ""), # ЖАҢА ҚАТАР: Қоспаның толық түсіндірмесі осында сақталады
            "status": st
        }

def format_detail_message(item):
    clean_title = str(item['title']).strip('«»"\' ')
    
    if item['type'] == 'Мекеме':
        if "Белсенді" in item['status']:
            msg = f"✅ Тамаша! <b>«{clean_title}»</b> мекемесі/өнімі ҚМДБ базасында тіркелген.\n\n"
        else:
            msg = f"⚠️ <b>ЕСКЕРТУ!</b> <b>«{clean_title}»</b> сертификаты қазір ЖАРАМСЫЗ!\n\n"
            
        if item['desc'] and item['desc'] != "Белгісіз":
            msg += f"🏢 <b>Өндіруші:</b> {item['desc']}\n"
        msg += f"📊 <b>Статус:</b> {item['status']}\n"
        
        d_start = item.get('date_start')
        d_end = item.get('date_end')
        if d_start and d_end:
            msg += f"📅 <b>Жарамдылығы:</b> {d_start} - {d_end}\n"
        elif d_end:
            msg += f"📅 <b>Жарамдылығы:</b> {d_end} дейін\n"
            
        msg += f"📍 <b>Мекенжайы:</b> {item.get('address', 'Көрсетілмеген')}"
        
        keys =[]
        if item.get('map_link'):
            keys.append([{"text": "🗺️ Картадан көру", "url": item['map_link']}])
        keys.append([{"text": "👍 Пайдалы", "callback_data": "fb:good"}, {"text": "👎 Қате", "callback_data": "fb:bad"}])
        return msg, {"inline_keyboard": keys}
        
    else:
        if "Рұқсат" in item['status']:
            msg = f"✅ <b>«{clean_title}»</b> қоспасы ҚМДБ тарапынан рұқсат етілген.\n\n"
        else:
            msg = f"🚫 <b>ЕСКЕРТУ!</b> <b>«{clean_title}»</b> қоспасы күдікті тізімінде!\n\n"
            
        msg += f"🏷 <b>Ғылыми атауы:</b> {item['desc']}\n"
        msg += f"📊 <b>Статус:</b> {item['status']}"
        
        # ЖАҢА БЛОК: Егер базада қосымша ақпарат (desc) болса, соны шығарып береді
        if item.get('info'):
            msg += f"\n\n📝 <b>Ақпарат:</b> {item['info']}"
        
        keys = [[{"text": "👍 Пайдалы", "callback_data": "fb:good"}, {"text": "👎 Қате", "callback_data": "fb:bad"}]]
        return msg, {"inline_keyboard": keys}