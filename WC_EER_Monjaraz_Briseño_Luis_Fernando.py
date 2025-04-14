import asyncpraw
from telegram import Bot, error
import asyncio
from datetime import datetime, timezone
import aiofiles

# Huerta Gomez Ethan Antonio
# Monjaraz Briseño Luis Fernando

# Configuración
REDDIT_CLIENT_ID = "VFabCzKXhmICbHRVwTGKpQ"
REDDIT_CLIENT_SECRET = "IehD72-gqkKjrGOuimJEwU17NSJzuA"
REDDIT_USER_AGENT = "AcademicProject:SecretHunter v1.0 (by /u/Capital-Draft-174)"
TELEGRAM_TOKEN = "7575592106:AAFd94JFmQZmSuqh4eXb9y6jqJDhkRer45c"
CHAT_ID = "6297622552"
ARCHIVO_TXT = "secretos_juegos.txt"

# Configuración de búsqueda
KEYWORDS = [
    # English
    "easter egg", "hidden secret", "secret ending",
    "unlockable", "lore", "glitch", "hidden room",
    # Español
    "huevo de pascua", "secreto oculto", "final secreto",
    "desbloqueable", "historia oculta", "fallo", "sala oculta"
]

SUBREDDITS = [
    "FinalFantasy",    # Para FFX
    "residentevil",    # RE2 Remake, RE4, RE4 Remake
    "nier"             # Nier: Automata
]

JUEGOS = {
    "FinalFantasy": ["Final Fantasy X", "FFX"],
    "residentevil": ["RE2 Remake", "RE4", "RE4 Remake"],
    "nier": ["Nier: Automata"]
}

LIMITE = 20  # Posts por subreddit
DELAY = 2    # Segundos entre requests
TELEGRAM_DELAY = 20  # Segundos entre mensajes de Telegram

async def buscar_secretos():
    """Busca secretos usando Async PRAW"""
    reddit = asyncpraw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )
    
    resultados = []
    for subreddit in SUBREDDITS:
        try:
            sub = await reddit.subreddit(subreddit)
            # Búsqueda con frases exactas entrecomilladas
            query = " OR ".join(f'"{kw}"' for kw in KEYWORDS)
            async for post in sub.search(query=query, limit=LIMITE):
                contenido = f"{post.title} {post.selftext}".lower()
                if any(kw.lower() in contenido for kw in KEYWORDS):
                    juegos_mencionados = [
                        juego for juego in JUEGOS[subreddit]
                        if juego.lower() in contenido
                    ]
                    if not juegos_mencionados:
                        continue
                    
                    fecha = datetime.fromtimestamp(post.created_utc, tz=timezone.utc)
                    resultados.append({
                        "subreddit": subreddit,
                        "juegos": ", ".join(juegos_mencionados),
                        "titulo": post.title,
                        "autor": str(post.author),
                        "fecha": fecha.strftime("%Y-%m-%d"),
                        "url": post.url,
                        "spoiler": post.spoiler
                    })
                await asyncio.sleep(DELAY)
        except Exception as e:
            print(f"🚨 Error en r/{subreddit}: {str(e)}")
    
    await reddit.close()
    return resultados

async def guardar_en_txt(post):
    """Guarda resultados en TXT de forma asíncrona"""
    async with aiofiles.open(ARCHIVO_TXT, "a", encoding="utf-8") as f:
        await f.write(
            f"🎮 Juego: {post['juegos']}\n"
            f"📌 Título: {post['titulo']}\n"
            f"🕵️ Autor: u/{post['autor']}\n"
            f"📅 Fecha: {post['fecha']}\n"
            f"🔗 Enlace: {post['url']}\n"
            f"🚨 Spoiler: {'Sí' if post['spoiler'] else 'No'}\n"
            f"{'-'*60}\n\n"
        )

async def enviar_alerta(bot: Bot, post: dict):
    """Envía alertas a Telegram con manejo de límites"""
    try:
        mensaje = (
            f"🔍 **r/{post['subreddit']}**\n"
            f"🎮 {post['juegos']}\n"
            f"📌 {post['titulo']}\n"
            f"👤 u/{post['autor']}\n"
            f"🔗 {post['url']}"
        )
        await bot.send_message(chat_id=CHAT_ID, text=mensaje)
    except error.RetryAfter as e:
        print(f"⏳ Esperando {e.retry_after} segundos (límite de Telegram)")
        await asyncio.sleep(e.retry_after)
        return await enviar_alerta(bot, post)  # Reintentar después de esperar
    except Exception as e:
        print(f"❌ Error enviando alerta: {str(e)}")

async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    try:
        await bot.send_message(chat_id=CHAT_ID, text="🚀 Iniciando búsqueda...")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return
    
    print("🔎 Buscando en Reddit...")
    posts = await buscar_secretos()
    
    if posts:
        print(f"✅ {len(posts)} hallazgos. Guardando y enviando...")
        for post in posts:
            await guardar_en_txt(post)
            await enviar_alerta(bot, post)
            await asyncio.sleep(TELEGRAM_DELAY)  # Mayor delay entre mensajes
    else:
        print("❌ No se encontraron resultados.")
    
    try:
        await bot.send_message(chat_id=CHAT_ID, text="✅ Búsqueda completada.")
    except error.RetryAfter as e:
        await asyncio.sleep(e.retry_after)
        await bot.send_message(chat_id=CHAT_ID, text="✅ Búsqueda completada.")
    await bot.close()

if __name__ == "__main__":
    asyncio.run(main())