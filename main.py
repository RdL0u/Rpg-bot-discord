import os
import sqlite3
import discord
from discord.ext import commands
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")

# =========================
# BANCO DE DADOS
# =========================

db = sqlite3.connect("fichas.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS fichas (
    user_id INTEGER PRIMARY KEY,
    nome_personagem TEXT NOT NULL DEFAULT 'Sem nome',
    hp_atual INTEGER NOT NULL DEFAULT 100,
    hp_max INTEGER NOT NULL DEFAULT 100,
    mana_atual INTEGER NOT NULL DEFAULT 100,
    mana_max INTEGER NOT NULL DEFAULT 100,
    xp INTEGER NOT NULL DEFAULT 0
)
""")

db.commit()

# =========================
# COMPATIBILIDADE COM BANCO ANTIGO
# =========================

# Se você já tinha criado fichas antes desta atualização,
# adicionamos a nova coluna automaticamente.

cursor.execute("PRAGMA table_info(fichas)")
colunas = [coluna[1] for coluna in cursor.fetchall()]

if "nome_personagem" not in colunas:
    cursor.execute("""
        ALTER TABLE fichas
        ADD COLUMN nome_personagem TEXT NOT NULL DEFAULT 'Sem nome'
    """)
    db.commit()


# =========================
# BOT
# =========================

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# =========================
# INICIALIZAÇÃO
# =========================

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

    try:
        comandos = await bot.tree.sync()
        print(f"{len(comandos)} comandos sincronizados.")
    except Exception as erro:
        print(f"Erro ao sincronizar comandos: {erro}")


# =========================
# COMANDO /CRIARFICHA
# =========================

@bot.tree.command(
    name="criarficha",
    description="Cria sua ficha de personagem."
)
@app_commands.describe(
    nome="Nome do seu personagem",
    hp="Quantidade de HP inicial",
    mana="Quantidade de Mana inicial"
)
async def criarficha(
    interaction: discord.Interaction,
    nome: str,
    hp: int,
    mana: int
):

    user_id = interaction.user.id

    # Impede valores inválidos
    if hp <= 0:
        await interaction.response.send_message(
            "❌ O HP inicial precisa ser maior que 0.",
            ephemeral=True
        )
        return

    if mana < 0:
        await interaction.response.send_message(
            "❌ A Mana inicial não pode ser negativa.",
            ephemeral=True
        )
        return

    # Verifica se o jogador já possui ficha
    cursor.execute(
        "SELECT user_id FROM fichas WHERE user_id = ?",
        (user_id,)
    )

    if cursor.fetchone() is not None:
        await interaction.response.send_message(
            "⚠️ Você já possui uma ficha.",
            ephemeral=True
        )
        return

    # Limita o nome para evitar fichas exageradamente grandes
    nome = nome[:50]

    # Cria a ficha
    cursor.execute("""
        INSERT INTO fichas
        (
            user_id,
            nome_personagem,
            hp_atual,
            hp_max,
            mana_atual,
            mana_max,
            xp
        )
        VALUES (?, ?, ?, ?, ?, ?, 0)
    """, (
        user_id,
        nome,
        hp,
        hp,
        mana,
        mana
    ))

    db.commit()

    await interaction.response.send_message(
        f"✅ Ficha criada com sucesso!\n\n"
        f"👤 **Personagem:** {nome}\n"
        f"❤️ **HP:** {hp}/{hp}\n"
        f"💧 **Mana:** {mana}/{mana}\n"
        f"⭐ **XP:** 0",
        ephemeral=True
    )


# =========================
# COMANDO /FICHA
# =========================

@bot.tree.command(
    name="ficha",
    description="Mostra sua ficha de personagem."
)
async def ficha(interaction: discord.Interaction):

    user_id = interaction.user.id

    cursor.execute("""
        SELECT
            nome_personagem,
            hp_atual,
            hp_max,
            mana_atual,
            mana_max,
            xp
        FROM fichas
        WHERE user_id = ?
    """, (user_id,))

    dados = cursor.fetchone()

    if dados is None:
        await interaction.response.send_message(
            "❌ Você ainda não possui uma ficha.\n"
            "Use `/criarficha` para criar uma.",
            ephemeral=True
        )
        return

    nome, hp, hp_max, mana, mana_max, xp = dados

    embed = discord.Embed(
        title=f"📜 {nome}",
        description=f"Ficha de {interaction.user.display_name}",
        color=discord.Color.dark_red()
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


# =========================
# COMANDO /SETHP
# =========================

@bot.tree.command(
    name="sethp",
    description="Altera seu HP atual."
)
@app_commands.describe(
    valor="Novo valor de HP"
)
async def sethp(
    interaction: discord.Interaction,
    valor: int
):

    user_id = interaction.user.id

    cursor.execute(
        "SELECT user_id FROM fichas WHERE user_id = ?",
        (user_id,)
    )

    if cursor.fetchone() is None:
        await interaction.response.send_message(
            "❌ Você ainda não possui uma ficha.",
            ephemeral=True
        )
        return

    if valor < 0:
        valor = 0

    cursor.execute("""
        UPDATE fichas
        SET hp_atual = ?
        WHERE user_id = ?
    """, (valor, user_id))

    db.commit()

    await interaction.response.send_message(
        f"❤️ Seu HP agora é **{valor}**.",
        ephemeral=True
    )


# =========================
# COMANDO /SETMANA
# =========================

@bot.tree.command(
    name="setmana",
    description="Altera sua Mana atual."
)
@app_commands.describe(
    valor="Novo valor de Mana"
)
async def setmana(
    interaction: discord.Interaction,
    valor: int
):

    user_id = interaction.user.id

    cursor.execute(
        "SELECT user_id FROM fichas WHERE user_id = ?",
        (user_id,)
    )

    if cursor.fetchone() is None:
        await interaction.response.send_message(
            "❌ Você ainda não possui uma ficha.",
            ephemeral=True
        )
        return

    if valor < 0:
        valor = 0

    cursor.execute("""
        UPDATE fichas
        SET mana_atual = ?
        WHERE user_id = ?
    """, (valor, user_id))

    db.commit()

    await interaction.response.send_message(
        f"💧 Sua Mana agora é **{valor}**.",
        ephemeral=True
    )


# =========================
# COMANDO /ADDXP
# =========================

@bot.tree.command(
    name="addxp",
    description="Adiciona XP à sua ficha."
)
@app_commands.describe(
    valor="Quantidade de XP recebida"
)
async def addxp(
    interaction: discord.Interaction,
    valor: int
):

    user_id = interaction.user.id

    cursor.execute(
        "SELECT user_id FROM fichas WHERE user_id = ?",
        (user_id,)
    )

    if cursor.fetchone() is None:
        await interaction.response.send_message(
            "❌ Você ainda não possui uma ficha.",
            ephemeral=True
        )
        return

    if valor <= 0:
        await interaction.response.send_message(
            "❌ O XP adicionado precisa ser maior que 0.",
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

    xp_atual = cursor.fetchone()[0]

    await interaction.response.send_message(
        f"⭐ Você recebeu **{valor} XP**!\n"
        f"XP atual: **{xp_atual}**",
        ephemeral=True
    )


# =========================
# INICIAR BOT
# =========================

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN não foi configurado."
    )

bot.run(TOKEN)
