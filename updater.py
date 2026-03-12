import requests
from google.cloud import firestore

db = firestore.Client()

def extract_list(api_data):
    """API-дан келген мәліметтің ішінен нақты тізімді (list) тауып алатын ақылды функция"""
    if isinstance(api_data, list):
        return api_data
    elif isinstance(api_data, dict):
        # Егер мәлімет қорап (dict) болса, ішінен тізімді іздейміз
        for key, value in api_data.items():
            if isinstance(value, list):
                return value
    # Егер ешнәрсе табылмаса, бос тізім қайтарады
    return []

def update_database():
    """ҚМДБ базасынан мекемелер мен қоспаларды көшіру"""
    result_text = "Жаңарту басталды...\n"
    
    # 1. МЕКЕМЕЛЕРДІ ЖАҢАРТУ
    try:
        comp_url = "https://halaldamu.kz/wp-json/map/v1/active-companies?lang=kz&show_all=1"
        comp_resp = requests.get(comp_url, timeout=150)
        raw_companies = comp_resp.json()
        
        # Ақылды функциямызбен тікелей тізімді суырып аламыз
        companies = extract_list(raw_companies)
        
        count_c = 0
        for comp in companies:
            # Тек сөздік (dict) болса ғана оқимыз (қатенің алдын алу)
            if isinstance(comp, dict):
                doc_id = str(comp.get("id", count_c))
                db.collection("companies").document(doc_id).set(comp, merge=True)
                count_c += 1
            
        result_text += f"- Мекемелер ({count_c} дана) сақталды.\n"
    except Exception as e:
        result_text += f"ҚАТЕ (Мекемелер): {e}\n"

    # 2. ҚОСПАЛАРДЫ ЖАҢАРТУ
    try:
        ing_url = "https://old.halaldamu.kz/ru/api/qospalar/1/1"
        ing_resp = requests.get(ing_url, timeout=150)
        raw_ingredients = ing_resp.json()
        
        ingredients = extract_list(raw_ingredients)
        
        count_i = 0
        for ing in ingredients:
            if isinstance(ing, dict):
                doc_id = str(ing.get("id", count_i))
                db.collection("ingredients").document(doc_id).set(ing, merge=True)
                count_i += 1
            
        result_text += f"- Қоспалар ({count_i} дана) сақталды.\n"
    except Exception as e:
        result_text += f"ҚАТЕ (Қоспалар): {e}\n"

    return result_text