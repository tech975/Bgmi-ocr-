def clean_text(text_list):
    cleaned = []
    for text in text_list:
        text = text.strip()
        # Only remove if completely empty
        if len(text) > 0:
            cleaned.append(text)
    return cleaned