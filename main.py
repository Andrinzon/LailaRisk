import discord
from discord.ext import commands
import requests
import asyncio
from config import DISCORD_TOKEN, CANAL_CONTROL_ID, ADMIN_IDS

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

usuarios = set()
niveles_riesgo = {}
imagenes_riesgo = {}
esperando_imagen_para = {}

alias_monedas = {
    "btc": "bitcoin", "eth": "ethereum", "bnb": "binancecoin",
    "xrp": "ripple", "sol": "solana", "ada": "cardano"
}

colores_riesgo = {
    1: "🟣 (Muy bajo)", 2: "🔵 (Bajo)", 3: "🔹 (Moderado bajo)",
    4: "🟢 (Moderado)", 5: "💚 (Medio)", 6: "💛 (Medio-alto)",
    7: "🟡 (Alto)", 8: "🟠 (Muy alto)", 9: "🔴 (Riesgoso)", 10: "🔥 (Extremo)"
}

# Función para obtener precio
def obtener_precio(moneda):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={moneda}&vs_currencies=usd"
        response = requests.get(url)
        data = response.json()
        return data[moneda]["usd"] if moneda in data else None
    except Exception:
        return None

# Evento al iniciar el bot
@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

# Comando para establecer riesgo
@bot.slash_command(name="riesgo", description="Establece el nivel de riesgo de una moneda")
async def riesgo(ctx, moneda: str, nivel: int):
    if ctx.author.id not in ADMIN_IDS:
        await ctx.respond("❌ No tienes permiso para usar este comando.", ephemeral=True)
        return

    moneda = alias_monedas.get(moneda.lower(), moneda.lower())
    if moneda not in alias_monedas.values():
        await ctx.respond("❌ Moneda no soportada.", ephemeral=True)
        return

    if not (1 <= nivel <= 10):
        await ctx.respond("❌ Nivel debe estar entre 1 y 10.", ephemeral=True)
        return

    niveles_riesgo[moneda] = nivel
    esperando_imagen_para[ctx.author.id] = moneda

    await ctx.respond(
        f"✅ Riesgo de **{moneda.upper()}** asignado a {nivel} {colores_riesgo[nivel]}\n"
        f"📷 Ahora envía una imagen en este canal para representar este riesgo."
    )

# Detectar imagen subida
@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.channel.id != CANAL_CONTROL_ID:
        return

    if message.author.bot:
        return

    if message.author.id in esperando_imagen_para:
        moneda = esperando_imagen_para.pop(message.author.id)
        if message.attachments:
            imagen_url = message.attachments[0].url
            imagenes_riesgo[moneda] = imagen_url

            await message.channel.send(
                f"✅ Imagen asociada al riesgo de **{moneda.upper()}** correctamente."
            )

            # Enviar la imagen a los usuarios
            for member in message.guild.members:
                if not member.bot:
                    try:
                        await member.send(
                            f"⚠️ El riesgo de **{moneda.upper()}** ha cambiado.",
                            file=await message.attachments[0].to_file()
                        )
                    except Exception:
                        continue

# Botón de precio BTC
@bot.slash_command(name="precio_btc", description="Mostrar el precio actual de BTC")
async def precio_btc(ctx):
    price = obtener_precio("bitcoin")
    if price:
        await ctx.respond(f"💰 **BTC**: ${price:,.2f}")
    else:
        await ctx.respond("❌ Error al obtener el precio.")

# Botón de riesgo BTC
@bot.slash_command(name="riesgo_btc", description="Mostrar el riesgo actual de BTC")
async def riesgo_btc(ctx):
    await ctx.respond("🔎 Revisando riesgo...")
    await asyncio.sleep(2)

    nivel = niveles_riesgo.get("bitcoin", "No asignado")
    color = colores_riesgo.get(nivel, "❔") if isinstance(nivel, int) else ""

    if "bitcoin" in imagenes_riesgo:
        embed = discord.Embed(title=f"⚠️ Riesgo de BTC: {nivel}/10 {color}")
        embed.set_image(url=imagenes_riesgo["bitcoin"])
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"⚠️ Riesgo de BTC: {nivel}/10 {color}")

bot.run(DISCORD_TOKEN)
