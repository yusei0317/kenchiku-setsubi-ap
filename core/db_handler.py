# get_notion_data 関数内を以下のように強化
def get_notion_data():
    # ...（前段のURL取得等は同じ）
    results = res.json().get("results", [])
    
    formatted_data = []
    for item in results:
        p = item.get("properties", {})
        
        def get_t(name):
            prop = p.get(name, {})
            if not prop: return ""
            ptype = prop.get("type")
            if ptype == "rich_text":
                return prop.get("rich_text", [{}])[0].get("plain_text", "").strip() if prop.get("rich_text") else ""
            elif ptype == "title":
                return prop.get("title", [{}])[0].get("plain_text", "").strip() if prop.get("title") else ""
            return ""

        qid = get_t("id")
        if not qid: continue

        # 数値データが空（None）の場合のガード
        def get_n(name, default=0):
            val = p.get(name, {}).get("number")
            return val if val is not None else default

        formatted_data.append({
            "page_id": item.get("id"),
            "q_id": qid,
            "question": get_t("question"),
            "answer": get_t("answer"),
            "choices": [get_t("choice_1"), get_t("choice_2"), get_t("choice_3"), get_t("choice_4")],
            "exps": [get_t("exp_1"), get_t("exp_2"), get_t("exp_3"), get_t("exp_4")],
            "image_url": p.get("image_url", {}).get("url", ""),
            "interval": get_n("interval", 0),
            "ease_factor": get_n("ease_factor", 2.5),
            "reps": get_n("reps", 0),
            "next_date": p.get("next_date", {}).get("date", {}).get("start", "未学習") if p.get("next_date", {}).get("date") else "未学習"
        })
    return formatted_data
