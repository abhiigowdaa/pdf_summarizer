import re

def extract_keywords(text):
    words = re.findall(r'\b\w+\b', text.lower())
    stopwords = set(['the', 'and', 'is', 'in', 'to', 'of', 'for', 'on', 'with', 'as', 'by', 'an', 'at', 'from'])
    keywords = [word for word in words if word not in stopwords and len(word) > 3]
    return list(set(keywords))
