import os
import sqlite3
import discord
from discord.ext import commands
from discord import app_commands

# ==================================================
# CONFIGURAÇÃO
# ==================================================

TOKEN = os.getenv("DISCORD_TOKEN")

# ==================================================
# BANCO DE DADOS
# ==================================================

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

# ==================================================
# MIGRAÇÃO DE BANCO ANTIGO
# ==================================================

cursor.execute("PRAGMA table_info(fichas)")
colunas = [coluna[1] for coluna in cursor.fetchall()]

if "nome_personagem" not in colunas:
    cursor.execute("""
        ALTER TABLE fichas
        ADD COLUMN nome_personagem TEXT NOT NULL DEFAULT 'Sem nome'
    """)
    db.commit()

# ==================================================
# BOT
# ==================================================

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# ==================================================
# BOT ONLINE
# ==================================================

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

    try:
        comandos = await bot.tree.sync()
        print(f"{len(comandos)} comandos sincronizados.")
    except Exception as erro:
        print(f"Erro ao sincronizar comandos: {erro}")

# ==================================================
# CRIAR FICHA
# ==================================================

@bot.tree.command(
    name="criarficha",
    description="Cria sua ficha de personagem."
)
@app_commands.describe(
    nome="Nome do personagem",
    hp="HP inicial",
    mana="Mana inicial"
)
async def criarficha(
    interaction: discord.Interaction,
    nome: str,
    hp: int,
    mana: int
):

    user_id = interaction.user.id

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

    if hp <= 0:
        await interaction.response.send_message(
            "❌ O HP precisa ser maior que 0.",
            ephemeral=True
        )
        return

    if mana < 0:
        await interaction.response.send_message(
            "❌ A Mana não pode ser negativa.",
            ephemeral=True
        )
        return

    nome = nome[:50]

    cursor.execute("""
        INSERT INTO fichas (
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
        f"✅ **Ficha criada!**\n\n"
        f"👤 Personagem: **{nome}**\n"
        f"❤️ HP: **{hp}/{hp}**\n"
        f"💧 Mana: **{mana}/{mana}**\n"
        f"⭐ XP: **0**",
        ephemeral=True
    )

# ==================================================
# MOSTRAR FICHA
# ==================================================

@bot.tree.command(
    name="ficha",
    description="Mostra sua ficha."
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
        description=f"Jogador: {interaction.user.display_name}",
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

# ==================================================
# APAGAR FICHA
# ==================================================

@bot.tree.command(
    name="apagarficha",
    description="Apaga sua ficha."
)
async def apagarficha(interaction: discord.Interaction):

    user_id = interaction.user.id

    cursor.execute(
        "SELECT nome_personagem FROM fichas WHERE user_id = ?",
        (user_id,)
    )

    ficha = cursor.fetchone()

    if ficha is None:
        await interaction.response.send_message(
            "❌ Você não possui uma ficha.",
            ephemeral=True
        )
        return

    nome = ficha[0]

    cursor.execute(
        "DELETE FROM fichas WHERE user_id = ?",
        (user_id,)
    )

    db.commit()

    await interaction.response.send_message(
        f"🗑️ A ficha **{nome}** foi apagada.\n"
        "Você pode criar uma nova usando `/criarficha`.",
        ephemeral=True
    )

# ==================================================
# ALTERAR HP E MANA MÁXIMOS
# ==================================================

@bot.tree.command(
    name="alterarficha",
    description="Altera o HP e a Mana máximos."
)
@app_commands.describe(
    hp="Novo HP máximo",
    mana="Nova Mana máxima"
)
async def alterarficha(
    interaction: discord.Interaction,
    hp: int,
    mana: int
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

    if hp <= 0:
        await interaction.response.send_message(
            "❌ O HP precisa ser maior que 0.",
            ephemeral=True
        )
        return

    if mana < 0:
        await interaction.response.send_message(
            "❌ A Mana não pode ser negativa.",
            ephemeral=True
        )
        return

    cursor.execute("""
        UPDATE fichas
        SET
            hp_atual = ?,
            hp_max = ?,
            mana_atual = ?,
            mana_max = ?
        WHERE user_id = ?
    """, (
        hp,
        hp,
        mana,
        mana,
        user_id
    ))

    db.commit()

    await interaction.response.send_message(
        f"✅ Ficha atualizada!\n\n"
        f"❤️ HP: **{hp}/{hp}**\n"
        f"💧 Mana: **{mana}/{mana}**",
        ephemeral=True
    )

# ==================================================
# DANO
# ==================================================

@bot.tree.command(
    name="dano",
    description="Causa dano ao seu personagem."
)
@app_commands.describe(
    valor="Quantidade de dano"
)
async def dano(
    interaction: discord.Interaction,
    valor: int
):

    user_id = interaction.user.id

    cursor.execute("""
        SELECT hp_atual, hp_max
        FROM fichas
        WHERE user_id = ?
    """, (user_id,))

    dados = cursor.fetchone()

    if dados is None:
        await interaction.response.send_message(
            "❌ Você ainda não possui uma ficha.",
            ephemeral=True
        )
        return

    if valor <= 0:
        await interaction.response.send_message(
            "❌ O dano precisa ser maior que 0.",
            ephemeral=True
        )
        return

    hp_atual, hp_max = dados

    novo_hp = max(0, hp_atual - valor)

    cursor.execute("""
        UPDATE fichas
        SET hp_atual = ?
        WHERE user_id = ?
    """, (novo_hp, user_id))

    db.commit()

    await interaction.response.send_message(
        f"💥 Você recebeu **{valor} de dano**!\n"
        f"❤️ HP: **{novo_hp}/{hp_max}**",
        ephemeral=True
    )

# ==================================================
# CURA
# ==================================================

@bot.tree.command(
    name="cura",
    description="Cura seu personagem."
)
@app_commands.describe(
    valor="Quantidade de HP recuperado"
)
async def cura(
    interaction: discord.Interaction,
    valor: int
):

    user_id = interaction.user.id

    cursor.execute("""
        SELECT hp_atual, hp_max
        FROM fichas
        WHERE user_id = ?
    """, (user_id,))

    dados = cursor.fetchone()

    if dados is None:
        await interaction.response.send_message(
            "❌ Você ainda não possui uma ficha.",
            ephemeral=True
        )
        return

    if valor <= 0:
        await interaction.response.send_message(
            "❌ A cura precisa ser maior que 0.",
            ephemeral=True
        )
        return

    hp_atual, hp_max = dados

    novo_hp = min(hp_max, hp_atual + valor)

    recuperado = novo_hp - hp_atual

    cursor.execute("""
        UPDATE fichas
        SET hp_atual = ?
        WHERE user_id = ?
    """, (novo_hp, user_id))

    db.commit()

    await interaction.response.send_message(
        f"💚 Você recuperou **{recuperado} de HP**!\n"
        f"❤️ HP: **{novo_hp}/{hp_max}**",
        ephemeral=True
    )

# ==================================================
# DEFINIR HP ATUAL
# ==================================================

@bot.tree.command(
    name="sethp",
    description="Define seu HP atual."
)
@app_commands.describe(
    valor="Novo HP atual"
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

# ==================================================
# DEFINIR MANA ATUAL
# ==================================================

@bot.tree.command(
    name="setmana",
    description="Define sua Mana atual."
)
@app_commands.describe(
    valor="Nova Mana atual"
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

# ==================================================
# ADICIONAR XP
# ==================================================

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
            "❌ O XP precisa ser maior que 0.",
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
        f"⭐ XP atual: **{xp_atual}**",
        ephemeral=True
    )
@bot.tree.command(
    name="recuperarmana",
    description="Recupera Mana do seu personagem."
)
@app_commands.describe(
    valor="Quantidade de Mana recuperada"
)
async def recuperarmana(
    interaction: discord.Interaction,
    valor: int
):

    user_id = interaction.user.id

    cursor.execute("""
        SELECT mana_atual, mana_max
        FROM fichas
        WHERE user_id = ?
    """, (user_id,))

    dados = cursor.fetchone()

    if dados is None:
        await interaction.response.send_message(
            "❌ Você ainda não possui uma ficha.",
            ephemeral=True
        )
        return

    if valor <= 0:
        await interaction.response.send_message(
            "❌ A recuperação precisa ser maior que 0.",
            ephemeral=True
        )
        return

    mana_atual, mana_max = dados

    nova_mana = min(
        mana_max,
        mana_atual + valor
    )

    recuperado = nova_mana - mana_atual

    cursor.execute("""
        UPDATE fichas
        SET mana_atual = ?
        WHERE user_id = ?
    """, (nova_mana, user_id))

    db.commit()

    await interaction.response.send_message(
        f"💧 Você recuperou **{recuperado} de Mana**!\n"
        f"💧 Mana: **{nova_mana}/{mana_max}**",
        ephemeral=True
    )
# ==================================================
# INICIAR BOT
# ==================================================

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN não foi configurado."
    )

bot.run(TOKEN)
