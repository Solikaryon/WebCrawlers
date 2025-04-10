import tweepy
import requests
import os
import time

# API de Twitter / Twitter API
# Obviamente no voy a dejar la mia para el envio... / Of course I'm not going to leave mine for the sending...
BEARER_TOKEN = "AAAA"  # Reemplaza con tu Bearer Token / Replace with your Bearer Token

# Autenticación de la API / API Authentication
client = tweepy.Client(bearer_token=BEARER_TOKEN)

# Parametros de búsqueda / Search parameters
query = "#HonkaiStarRail has:images -is:retweet"
max_results = 10  # Limite de resultados / Result limit
delay_seconds = 10  # Retraso entre solicitudes / Delay between requests

# Carpeta donde guardar las imágenes / Folder to save images
os.makedirs("Honkai_Images", exist_ok=True)

# Descargar imagenes de Twitter / Download Twitter images
def download_images():
    try:
        # Buscar tweets recientes con imágenes / Search for recent tweets with images
        tweets = client.search_recent_tweets(
            query=query,
            tweet_fields=["entities", "attachments"],
            expansions="attachments.media_keys",
            media_fields=["url", "type"],
            max_results=max_results
        )

        # Hay twits? / Are there tweets?
        if not tweets.data:
            print("No se encontraron tweets recientes con imágenes.")
            return

        # Descargar imágenes de cada tweet / Download images from each tweet
        for index, tweet in enumerate(tweets.data):
            print(f"Procesando tweet {index + 1}: {tweet.text}")

            # Verificar si el tweet tiene medios adjuntos / Check if the tweet has attached media
            if hasattr(tweet, "attachments") and "media_keys" in tweet.attachments:
                media_keys = tweet.attachments["media_keys"]
                print(f"Medios encontrados en el tweet {tweet.id}: {media_keys}")

                # Crear una carpeta para el tweet si tiene varias imágenes / Create a folder for the tweet if it has multiple images
                if len(media_keys) > 1:
                    tweet_folder = os.path.join("Honkai_Images", f"tweet_{tweet.id}")
                    os.makedirs(tweet_folder, exist_ok=True)
                else:
                    tweet_folder = "Honkai_Images"  # Guardar en la carpeta principal si solo hay una imagen / Save in the main folder if there is only one image

                # Buscar los medios en la sección includes del tweet / Search for media in the tweet's includes section
                for media_index, media_key in enumerate(media_keys):
                    for media in tweets.includes["media"]:
                        if media["media_key"] == media_key and media["type"] == "photo":
                            img_url = media["url"]
                            try:
                                # Descargar la imagen / Download the image
                                response = requests.get(img_url, timeout=10)
                                response.raise_for_status()
                                img_data = response.content

                                # Guardar la imagen  / Save the image
                                if len(media_keys) > 1:
                                    filename = os.path.join(tweet_folder, f"imagen_{media_index + 1}.jpg")
                                else:
                                    filename = os.path.join(tweet_folder, f"honkai_{index}.jpg")

                                with open(filename, "wb") as img_file:
                                    img_file.write(img_data)

                                print(f"Imagen guardada: {filename}")
                            except requests.exceptions.RequestException as e:
                                print(f"Error al descargar la imagen {img_url}: {e}")
            else:
                print(f"El tweet {tweet.id} no contiene imágenes.")

            # Agregar retraso para evitar bloqueos / Add delay to avoid rate limits
            time.sleep(delay_seconds)

    except tweepy.errors.TooManyRequests as e:
        # Si se alcanza el límite de tasa, esperar hasta que se restablezca / If rate limit is reached, wait until it resets
        reset_time = int(e.response.headers.get("x-rate-limit-reset", 0))
        wait_time = max(reset_time - time.time(), 0) 
        print(f"Error 429: Demasiadas solicitudes. Esperando {int(wait_time)} segundos antes de reintentar...")

        # Cooldown del tiempo de espera en tiempo real + 10 segundos adicionale / Real-time wait cooldown + 10 additional seconds
        for remaining in range(int(wait_time) + 10, 0, -1):
            print(f"\rReintentando en {remaining} segundos...", end="")
            time.sleep(1)
        print("")

        input("Presiona Enter para reintentar la descarga de imágenes...")
        download_images() 

    except Exception as e:
        print(f"Error inesperado: {e}")

download_images()

print("Descarga finalizada.")