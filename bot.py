import discord
from discord.ext import commands, tasks
import feedparser
from config import TOKEN

# Создаем объект intents для бота, чтобы бот мог получать сообщения
intents = discord.Intents.default()
intents.messages = True

# Создаем объект бота с префиксом '!' для команд
bot = commands.Bot(command_prefix='!', intents=intents)

# Словари для хранения подписок и новостей
subscriptions = {}
news_cache = {}

# Заранее определенный URL RSS-канала
rss_feed_url = "https://rssexport.rbc.ru/rbcnews/news/30/full.rss"

# Функция для получения новостей из RSS
def get_news(feed_url):
    feed = feedparser.parse(feed_url)
    return [{'title': entry.title, 'link': entry.link} for entry in feed.entries]

# Команда для показа новостей с заранее определенного источника
@bot.command()
async def news(ctx):
    news = get_news(rss_feed_url)
    if not news:
        await ctx.send("Не удалось получить новости с указанного источника.")
        return
    response = "\n".join([f"{entry['title']} - {entry['link']}" for entry in news[:5]])
    if response:
        await ctx.send(response)
    else:
        await ctx.send("Нет доступных новостей.")

# Команда для подписки на уведомления по ключевому слову
@bot.command()
async def subscribe(ctx, keyword):
    user_id = ctx.author.id
    if user_id not in subscriptions:
        subscriptions[user_id] = []
    if keyword not in subscriptions[user_id]:
        subscriptions[user_id].append(keyword)
        await ctx.send(f"Вы подписались на уведомления по ключевому слову: {keyword}")
    else:
        await ctx.send(f"Вы уже подписаны на уведомления по ключевому слову: {keyword}")

# Команда для отписки от уведомлений по ключевому слову
@bot.command()
async def unsubscribe(ctx, keyword):
    user_id = ctx.author.id
    if user_id in subscriptions and keyword in subscriptions[user_id]:
        subscriptions[user_id].remove(keyword)
        await ctx.send(f"Вы отписались от уведомлений по ключевому слову: {keyword}")
    else:
        await ctx.send(f"Вы не подписаны на уведомления по ключевому слову: {keyword}")

# Команда для показа текущих подписок
@bot.command()
async def notifications(ctx):
    user_id = ctx.author.id
    if user_id in subscriptions and subscriptions[user_id]:
        response = "Вы подписаны на следующие ключевые слова:\n" + "\n".join(subscriptions[user_id])
    else:
        response = "Вы не подписаны на какие-либо ключевые слова."
    await ctx.send(response)

# Команда для показа последних новостей по всем подпискам
@bot.command()
async def latest(ctx):
    user_id = ctx.author.id
    if user_id in subscriptions and subscriptions[user_id]:
        user_news = []
        for keyword in subscriptions[user_id]:
            if keyword in news_cache:
                user_news.extend(news_cache[keyword])
        response = "\n".join([f"{entry['title']} - {entry['link']}" for entry in user_news[:5]])
        if response:
            await ctx.send(response)
        else:
            await ctx.send("Нет новостей по вашим подпискам.")
    else:
        await ctx.send("Нет новостей по вашим подпискам.")

# Фоновая задача для обновления новостей каждые 10 минут
@tasks.loop(minutes=10)
async def update_news():
    news = get_news(rss_feed_url)
    for entry in news:
        for keyword in subscriptions.values():
            if any(word.lower() in entry['title'].lower() for word in keyword):
                if keyword not in news_cache:
                    news_cache[keyword] = []
                news_cache[keyword].append(entry)

# Команда для отображения информации о доступных командах
@bot.command()
async def info(ctx):
    response = (
        "Доступные команды:\n"
        "!news - показать последние новости с указанного источника.\n"
        "!subscribe <ключевое слово> - подписаться на уведомления по ключевому слову.\n"
        "!unsubscribe <ключевое слово> - отписаться от уведомлений по ключевому слову.\n"
        "!notifications - показать текущие подписки.\n"
        "!latest - показать последние новости по всем подпискам.\n"
        "!info - показать эту справочную информацию."
    )
    await ctx.send(response)

# Запуск фоновой задачи при запуске бота
@bot.event
async def on_ready():
    update_news.start()
    print(f'Logged in as {bot.user}')

# Запуск бота с токеном из config.py
bot.run(TOKEN)
