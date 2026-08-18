
import os
import sqlite3
import discord
from discord.ext import commands
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")

# Banco de dados
db = sqlite3.connect("fichas.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS fichas (
    user_id INTEGER PRIMARY KEY,
    hp_atual INTEGER DEFAULT 100,
    hp_max INTEGER DEFAULT 100,
    mana_atual INTEGER DEFAULT 100,
    mana_max INTEGER DEFAULT 100,
    xp INTEGER DEFAULT 0
)
""")

db.commit()

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


def criar_ficha(user_id):
    cursor.execute(
        "SELECT user_id FROM fichas WHERE user_id = ?",
        (user_id,)
    )

    if cursor.fetchone() is None:
        cursor.execute("""
        INSERT INTO fichas
        (user_id, hp_atual, hp_max, mana_atual, mana_max, xp)
        VALUES (?, 100, 100, 100, 100, 0)
        """, (user_id,))

        db.commit()


@bot.event
async def on_ready():
    print(f"Bot conectado: {bot.user}")

    try:
        comandos = await bot.tree.sync()
        print(f"{len(comandos)} comandos sincronizados.")
    except Exception as erro:
        print(f"Erro: {erro}")


@bot.tree.command(
    name="criarficha",
    description="Cria sua ficha de personagem."
)
async def criarficha(interaction: discord.Interaction):

    user_id = interaction.user.id

    cursor.execute(
        "SELECT user_id FROM fichas WHERE user_id = ?",
        (user_id,)
    )

    if cursor.fetchone():
        await interaction.response.send_message(
            "⚠️ Você já possui uma ficha!",
            ephemeral=True
        )
        return

    criar_ficha(user_id)

    await interaction.response.send_message(
        "✅ Ficha criada com sucesso!\n"
        "Use `/ficha` para visualizar.",
        ephemeral=True
    )


@bot.tree.command(
    name="ficha",
    description="Mostra sua ficha."
)
async def ficha(interaction: discord.Interaction):

    user_id = interaction.user.id

    criar_ficha(user_id)

    cursor.execute("""
    SELECT hp_atual, hp_max, mana_atual, mana_max, xp
    FROM fichas
    WHERE user_id = ?
    """, (user_id,))

    hp, hp_max, mana, mana_max, xp = cursor.fetchone()

    embed = discord.Embed(
        title=f"📜 Ficha de {interaction.user.display_name}",
        color=discord.Color.red()
    )

    embed.add_field(
        name="❤️ HP",
        value=f"{hp}/{hp_max}",
        inline=True
    )

    embed.add_field(
        name="💧 Mana",
        value=f"{mana}/{mana_max}",
        inline=True
    )

    embed.add_field(
        name="⭐ XP",
        value=str(xp),
        inline=True
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


@bot.tree.command(
    name="sethp",
    description="Altera seu HP."
)
@app_commands.describe(valor="Novo HP")
async def sethp(
    interaction: discord.Interaction,
    valor: int
):

    user_id = interaction.user.id

    criar_ficha(user_id)

    cursor.execute("""
    UPDATE fichas
    SET hp_atual = ?
    WHERE user_id = ?
    """, (max(0, valor), user_id))

    db.commit()

    await interaction.response.send_message(
        f"❤️ HP alterado para **{max(0, valor)}**.",
        ephemeral=True
    )


@bot.tree.command(
    name="setmana",
    description="Altera sua Mana."
)
@app_commands.describe(valor="Nova Mana")
async def setmana(
    interaction: discord.Interaction,
    valor: int
):

    user_id = interaction.user.id

    criar_ficha(user_id)

    cursor.execute("""
    UPDATE fichas
    SET mana_atual = ?
    WHERE user_id = ?
    """, (max(0, valor), user_id))

    db.commit()

    await interaction.response.send_message(
        f"💧 Mana alterada para **{max(0, valor)}**.",
        ephemeral=True
    )


@bot.tree.command(
    name="addxp",
    description="Adiciona XP à sua ficha."
)
@app_commands.describe(valor="Quantidade de XP")
async def addxp(
    interaction: discord.Interaction,
    valor: int
):

    user_id = interaction.user.id

    criar_ficha(user_id)

    if valor < 0:
        await interaction.response.send_message(
            "❌ O XP não pode ser negativo.",
            ephemeral=True
        )
        return

    cursor.execute("""
    UPDATE fichas
    SET xp = xp + ?
    WHERE user_id = ?
    """, (valor, user_id))

    db.commit()

    cursor.execute(
        "SELECT xp FROM fichas WHERE user_id = ?",
        (user_id,)
    )

    xp = cursor.fetchone()[0]

    await interaction.response.send_message(
        f"⭐ Você recebeu **{valor} XP**!\n"
        f"XP atual: **{xp}**",
        ephemeral=True
    )


if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN não configurado."
    )

bot.run(TOKEN)
