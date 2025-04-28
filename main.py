import discord
from discord.ext import commands
import requests

# Leer token desde archivo .env
with open(".env") as f:
    DISCORD_TOKEN = f.read().strip()

# Configuración
CANAL_CONTROL_ID = 123456789012345678  # ID del canal donde controlas todo
ADMIN_IDS = [123456789012345678]        # IDs de los administradores

# Intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

# Crear bot
bot = commands.Bot(command_prefix='/', intents=intents)

# Monedas soportadas
alias_monedas = {
    "btc": "bitcoin", "eth": "ethereum", "bnb": "binancecoin",
    "xrp": "ripple", "sol": "solana", "ada": "cardano"
}

# Colores riesgo
colores_riesgo = {
    1: "🟣 (Muy bajo)", 2: "🔵 (Bajo)", 3: "🔹 (Moderado bajo)",
    4: "🟢 (Moderado)", 5: "💚 (Medio)", 6: "💛 (Medio-alto)",
    7: "🟡 (Alto)", 8: "🟠 (Muy alto)", 9: "🔴 (Riesgoso)", 10: "🔥 (Extremo)"
}

# Bases de datos temporales
niveles_riesgo = {}
imagenes_riesgo = {}

def obtener_precio(moneda):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={moneda}&vs_currencies=usd"
        response = requests.get(url)
        data = response.json()
        return data[moneda]["usd"] if moneda in data else None
    except Exception:
        return None

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

@bot.command()
async def precio(ctx, cripto: str):
    if ctx.channel.id != CANAL_CONTROL_ID:
        return
    moneda = alias_monedas.get(cripto.lower(), cripto.lower())
    if moneda not in alias_monedas.values():
        await ctx.send("❌ Moneda no soportada.")
        return
    precio_actual = obtener_precio(moneda)
    if precio_actual:
        await ctx.send(f"💰 Precio de {moneda.upper()}: ${precio_actual:,.2f}")
    else:
        await ctx.send("❌ Error al obtener el precio.")

@bot.command()
async def riesgo(ctx, cripto: str, nivel: int):
    if ctx.channel.id != CANAL_CONTROL_ID:
        return
    if ctx.author.id not in ADMIN_IDS:
        await ctx.send("❌ No tienes permisos para asignar riesgos.")
        return
    moneda = alias_monedas.get(cripto.lower(), cripto.lower())
    if moneda not in alias_monedas.values():
        await ctx.send("❌ Moneda no soportada.")
        return
    if nivel < 1 or nivel > 10:
        await ctx.send("❌ Nivel debe estar entre 1 y 10.")
        return

    niveles_riesgo[moneda] = nivel
    color = colores_riesgo.get(nivel, "")
    await ctx.send(f"✅ Riesgo de *{moneda.upper()}* asignado a {nivel} {color}.\nEnvía ahora una imagen para este riesgo.")

@bot.command()
async def mostrar_riesgo(ctx, cripto: str):
    if ctx.channel.id != CANAL_CONTROL_ID:
        return
    moneda = alias_monedas.get(cripto.lower(), cripto.lower())
    if moneda not in alias_monedas.values():
        await ctx.send("❌ Moneda no soportada.")
        return
    nivel = niveles_riesgo.get(moneda, "No asignado")
    color = colores_riesgo.get(nivel, "") if isinstance(nivel, int) else ""
    if moneda in imagenes_riesgo:
        await ctx.send(file=discord.File(imagenes_riesgo[moneda]))
        await ctx.send(f"⚠️ Riesgo de *{moneda.upper()}*: {nivel}/10 {color}")
    else:
        await ctx.send(f"⚠️ Riesgo de *{moneda.upper()}*: {nivel}/10 {color}")

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.channel.id != CANAL_CONTROL_ID:
        return
    if message.author.bot:
        return

    # Si el admin envía una imagen
    if message.author.id in ADMIN_IDS and message.attachments:
        moneda_actual = next((k for k, v in niveles_riesgo.items() if v is not None), None)
        if moneda_actual:
            imagen = message.attachments[0]
            imagen_path = f"{moneda_actual}.png"
            await imagen.save(imagen_path)
            imagenes_riesgo[moneda_actual] = imagen_path
            await message.channel.send(f"✅ Imagen para riesgo de {moneda_actual.upper()} guardada correctamente.")

bot.run(DISCORD_TOKEN)
