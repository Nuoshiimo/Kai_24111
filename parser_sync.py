import requests
import csv
from bs4 import BeautifulSoup

# Корректный User-Agent, чтобы притвориться обычным браузером
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
}

def parse_news():
    """Парсинг новостей с Lenta.ru"""
    URL = 'https://lenta.ru/'
    news_data = []
    
    print("Начинаем парсинг новостей...")
    try:
        response = requests.get(URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Ошибка при подключении к Lenta.ru: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    # Парсим маленькие карточки
    for card in soup.find_all('a', class_='card-mini'):
        title_tag = card.find('span', class_='card-mini__title')
        if title_tag:
            clean_title = title_tag.get_text(strip=True)
            link = card.get('href')
            if link:
                full_link = link if link.startswith('http') else URL.rstrip('/') + link
                news_data.append({'title': clean_title, 'url': full_link})

    # Парсим большие карточки
    for card in soup.find_all('a', class_='card-big'):
        # Ищем заголовок внутри h3 или span
        title_tag = card.find(['h3', 'span'], class_=['card-big__title', 'card-feature__title'])
        if not title_tag:
            # Иногда класс может отличаться, пробуем просто найти текст в h3
            title_tag = card.find('h3')
            
        if title_tag:
            clean_title = title_tag.get_text(strip=True)
            link = card.get('href')
            if link:
                full_link = link if link.startswith('http') else URL.rstrip('/') + link
                news_data.append({'title': clean_title, 'url': full_link})

    if news_data:
        with open('lenta_news.csv', mode='w', encoding='utf-8-sig', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['title', 'url'])
            writer.writeheader()
            writer.writerows(news_data)
        print(f"Сохранено {len(news_data)} новостей в lenta_news.csv")
    else:
        print("Новости не найдены. Возможно, структура сайта Lenta.ru изменилась.")

parse_news()
print("Парсер новостей закончил работу")