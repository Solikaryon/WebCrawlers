# Código creado por:
# Monjaraz Briseño Luis Fernando

import requests
from bs4 import BeautifulSoup
import time
import random
from datetime import datetime
import csv
import os

# Configuración ------------------- #
GENRE = "Action"                  # Género / Genre
MAX_PRICE_USD = 30                # Precio máximo USD / Max price USD
MIN_REVIEWS = "Very Positive"     # Mínimo de reseñas requerido / Minimum required reviews
MAX_GAMES = 5                     # Límite de juegos / Games limit
DELAY_MIN = 10                    # Delay mínimo / Minimum delay
DELAY_MAX = 20                    # Delay máximo / Maximum delay
BASE_URL = "https://store.steampowered.com/search/"
TIMEOUT = 30                     
MAX_RETRIES = 3                  
SAVE_PATH = r"PATH\TO\SAVE"  # RUTA (No iba a dejar la mia xdn't) / PATH (I wasn't going to leave mine xdn't)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://store.steampowered.com/',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
}

# Funciones -------------------------- #
def random_delay():
    """Delay aleatorio con variación humana"""
    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX) + random.random())

def safe_request(url, params=None, session=None, retries=MAX_RETRIES):
    """Realiza solicitudes con reintentos y manejo de errores"""
    for attempt in range(retries):
        try:
            if session:
                response = session.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
            else:
                response = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Intento {attempt + 1}/{retries} fallido para {url}: {str(e)}")
            if attempt < retries - 1:
                wait_time = (attempt + 1) * 10  # Backoff exponencial / Exponential backoff
                print(f"Esperando {wait_time} segundos antes de reintentar...")
                time.sleep(wait_time)
            else:
                raise
    return None

def get_price(game_element): # Precios / Prices
    try:
        # Priorizar descuentos / Prioritize discounts
        price_element = game_element.find('div', class_='discount_final_price')
        
        # No descuento = precio normal / No discount = normal price
        if not price_element:
            price_element = game_element.find('div', class_='discount_original_price')
        
        # Si no precio = Gratis / If no price = Free
        if not price_element:
            if game_element.find('div', class_='search_discount_block free'):
                return 0.0
            return None
        
        price_text = price_element.text.strip()
        if 'Free' in price_text or '$0' in price_text:
            return 0.0
        
        # Diferentes formatos de precio / Differents price formats
        clean_price = price_text.replace('$', '').replace(',', '').strip()
        return float(clean_price) if clean_price else None
        
    except Exception as e:
        print(f"⚠️ Error extrayendo precio: {str(e)}")
        return None

def get_reviews(game_url): # Reseñas / Reviews
    random_delay()
    try:
        response = safe_request(game_url, session=None)
        if not response:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        review_element = soup.find('div', class_='user_reviews_summary_row')
        
        if review_element:
            # Resumen de reseñas / Review summary
            summary_span = review_element.find('span', class_='game_review_summary')
            if summary_span:
                return summary_span.text.strip()
                
            # Si no se encuentra el span, usar la información del tooltip / If not found, use tooltip info
            if 'data-tooltip-html' in review_element.attrs:
                tooltip = review_element['data-tooltip-html']
                # Extraer la primera parte / Extract the first part
                return tooltip.split('<br>')[0].strip()
                
        return None
    except Exception as e:
        print(f"⚠️ Error obteniendo reseñas: {str(e)}")
        return None

# Tipos de reseña Steam / Types of Steam reviews
REVIEW_ORDER = [
    "Overwhelmingly Negative",
    "Very Negative",
    "Negative",
    "Mostly Negative",
    "Mixed",
    "Mostly Positive",
    "Positive",
    "Very Positive",
    "Overwhelmingly Positive",
]

def is_review_acceptable(review_summary, min_review):
    review_summary = review_summary.strip()
    min_review = min_review.strip().title()  # Normalizamos mayúsculas/minúsculas

    if review_summary not in REVIEW_ORDER:
        print(f"Resumen de reseñas '{review_summary}' no reconocido - Saltando")
        return False

    if REVIEW_ORDER.index(review_summary) < REVIEW_ORDER.index(min_review):
        return False

    return True

# Main --------------------------- #
def main(): 
    print(f"Buscando {MAX_GAMES} {GENRE} juegos (≤${MAX_PRICE_USD})...\n")
    resultados = []
    session = requests.Session()
    
    try:
        for page in range(0, 3):  # Reducido a 3 páginas para evitar timeouts / Reduced to 3 pages to avoid timeouts
            if len(resultados) >= MAX_GAMES:
                break
                
            print(f"\n📖 Procesando página {page + 1}...")
            random_delay()
            
            # Parámetros de búsqueda / Search parameters
            params = {
                'tags': GENRE,
                'page': page,
                'maxprice': MAX_PRICE_USD,
                'supportedlang': 'english',
                'filter': 'popularnew',
                'cc': 'us'
            }
            
            response = safe_request(BASE_URL, params=params, session=session)
            if not response:
                continue
                
            soup = BeautifulSoup(response.text, 'html.parser')
            games = soup.find_all('a', class_='search_result_row')
            
            for game in games:
                if len(resultados) >= MAX_GAMES:
                    break
                    
                name = game.find('span', class_='title')
                if not name:
                    continue
                    
                name = name.text.strip()
                link = game.get('href')
                
                if not link:
                    continue
                    
                print(f"\nProcesando: {name}")
                
                price = get_price(game)
                if price is None:
                    print("Precio no encontrado - Saltando")
                    continue
                
                print(f"Precio: {'Free' if price == 0 else f'${price:.2f}'}")
                
                print("Buscando reseñas...")
                reviews = get_reviews(link)
                
                if not reviews:
                    print("No se pudieron obtener reseñas - Saltando")
                    continue
                
                # Comprobación de reseñas / Review check
                if not is_review_acceptable(reviews, MIN_REVIEWS):
                    print(f"Reseñas no alcanzan el mínimo requerido ({reviews}) - Saltando")
                    continue
                
                resultados.append({
                    'Name': name,
                    'Price': f"${price:.2f}" if price > 0 else "Free",
                    'Reviews': reviews,
                    'Link': link
                })
                
                print(f"Añadido | Reseñas: {reviews}")

    except Exception as e:
        print(f"\nError crítico: {str(e)}")
    finally:
        session.close()
        print("\nBúsqueda completada")
    
    if resultados:
        filename = f"steam_{GENRE}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        filepath = os.path.join(SAVE_PATH, filename)
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['Name', 'Price', 'Reviews', 'Link'])
            writer.writeheader()
            writer.writerows(resultados)
        print(f"\n{len(resultados)} juegos guardados en '{filepath}'")

if __name__ == "__main__":
    main()