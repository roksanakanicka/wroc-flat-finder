import requests
from bs4 import BeautifulSoup
import re
from functools import lru_cache

def parse_wroclaw_wiki():
    """Parsuje informacje o Wrocławiu z Wikipedii"""
    
    fallback_pl = {
        'text': 'Wrocław - miasto na prawach powiatu w południowo-zachodniej Polsce, siedziba władz województwa dolnośląskiego, czwarte co do zaludnienia miasto w Polsce.',
        'population': '672545',
        'area': '293'
    }
    
    fallback_en = {
        'text': 'Wrocław is a city in southwestern Poland and the largest city in the historical region of Silesia.',
        'population': '672545',
        'area': '293'
    }
    
    data = {'pl': fallback_pl.copy(), 'en': fallback_en.copy()}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    # parsing PL - wszystkie <p>
    try:
        response = requests.get("https://pl.wikipedia.org/wiki/Wrocław", headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        all_paragraphs = soup.find_all('p')
        texts = []
        for p in all_paragraphs:
            text = p.get_text().strip()
            # tylko długie, bez [n] na początku
            if len(text) > 60 and not text.startswith('['):
                clean = re.sub(r'\[.*?\]', '', text)
                texts.append(clean)
        
        if len(texts) >= 3:
            data['pl']['text'] = ' '.join(texts[:3])
        
        # regex dla liczb
        full_text = soup.get_text()
        
        pop = re.search(r'(\d+(?:\s+\d+)*)\s+mieszkańc', full_text)
        if pop:
            data['pl']['population'] = pop.group(1).replace(' ', '')
        
        area = re.search(r'(\d+(?:[,\.]\d+)?)\s*km[²2]', full_text)
        if area:
            data['pl']['area'] = area.group(1).replace(',', '.')
        
            
    except Exception as e:
        print(f"Błąd: {e}")
        pass
    
    # parsing EN
    try:
        response = requests.get("https://en.wikipedia.org/wiki/Wrocław", headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        all_paragraphs = soup.find_all('p')
        texts = []
        for p in all_paragraphs:
            text = p.get_text().strip()
            if len(text) > 60 and not text.startswith('['):
                clean = re.sub(r'\[.*?\]', '', text)
                texts.append(text)
        
        if len(texts) >= 3:
            data['en']['text'] = ' '.join(texts[:3])
    except:
        pass
    
    return data

@lru_cache(maxsize=1)
def get_city_description():
    wiki_data = parse_wroclaw_wiki()
    
    # ciekawostki dla UI
    interesting_facts_pl = [
        'Miasto 12 wysp - Wrocław leży na 12 wyspach połączonych ponad 100 mostami',
        'Stolica krasnali - ponad 1000 małych figurek krasnali rozmieszczonych po całym mieście',
        'Ostrów Tumski - najstarsza część miasta, zaczątki Wrocławia z X wieku',
        'Europejska Stolica Kultury 2016',
        'Hala Stulecia - obiekt UNESCO z 1913 roku'
    ]
    
    attractions_pl = [
        'Rynek - jeden z największych rynków średniowiecznych w Europie',
        'Ostrów Tumski - wyspa katedralna z zabytkami',
        'Panorama Racławicka - monumentalny obraz bitwy',
        'ZOO Wrocław - najstarsze zoo w Polsce',
        'Fontanna Multimedialna'
    ]
    
    return {
        'pl': wiki_data['pl']['text'],
        'en': wiki_data['en']['text'],
        'population': wiki_data['pl']['population'],
        'area': wiki_data['pl']['area'],
        'interesting_facts_pl': interesting_facts_pl,
        'attractions_pl': attractions_pl
    }