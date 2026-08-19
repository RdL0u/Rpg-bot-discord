import os
import sqlite3
import random
import discord

from discord.ext import commands
from discord import app_commands


# ============================================================
# CONFIGURAÇÃO
# ============================================================

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN não foi configurado.")


# ============================================================
# BANCO DE DADOS
# ============================================================

db = sqlite3.connect("rpg_fichas.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS mesas (
    channel_id INTEGER PRIMARY KEY,
    mestre_id INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS fichas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER NOT NULL,
    dono_id INTEGER,
    mestre_id INTEGER,
    tipo TEXT NOT NULL,
    nome TEXT NOT NULL,
    hp_atual INTEGER NOT NULL,
    hp_max INTEGER NOT NULL,
    mana_atual INTEGER NOT NULL,
    mana_max INTEGER NOT NULL,
    xp INTEGER NOT NULL DEFAULT 0,
    aleatorio INTEGER NOT NULL DEFAULT 0
)
""")

db.commit()


# ============================================================
# BOT
# ============================================================

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def garantir_mesa(channel_id):
    cursor.execute("""
        INSERT OR IGNORE INTO mesas (channel_id, mestre_id)
        VALUES (?, NULL)
    """, (channel_id,))
    db.commit()


def obter_mestre(channel_id):
    cursor.execute("""
        SELECT mestre_id
        FROM mesas
        WHERE channel_id = ?
    """, (channel_id,))

    resultado = cursor.fetchone()

    if resultado:
        return resultado[0]

    return None


def eh_admin(interaction):
    if interaction.guild is None:
        return False

    return interaction.user.guild_permissions.administrator


def eh_mestre(interaction):
    return (
        obter_mestre(interaction.channel.id)
        == interaction.user.id
    )


def buscar_ficha_jogador(channel_id, user_id):
    cursor.execute("""
        SELECT
            id,
            channel_id,
            dono_id,
            mestre_id,
            tipo,
            nome,
            hp_atual,
            hp_max,
            mana_atual,
            mana_max,
            xp,
            aleatorio
        FROM fichas
        WHERE channel_id = ?
        AND dono_id = ?
        AND tipo = 'jogador'
        LIMIT 1
    """, (channel_id, user_id))

    return cursor.fetchone()


def buscar_ficha(ficha_id):
    cursor.execute("""
        SELECT
            id,
            channel_id,
            dono_id,
            mestre_id,
            tipo,
            nome,
            hp_atual,
            hp_max,
            mana_atual,
            mana_max,
            xp,
            aleatorio
        FROM fichas
        WHERE id = ?
    """, (ficha_id,))

    return cursor.fetchone()


def transformar_ficha(dados):

    if dados is None:
        return None

    return {
        "id": dados[0],
        "channel_id": dados[1],
        "dono_id": dados[2],
        "mestre_id": dados[3],
        "tipo": dados[4],
        "nome": dados[5],
        "hp_atual": dados[6],
        "hp_max": dados[7],
        "mana_atual": dados[8],
        "mana_max": dados[9],
        "xp": dados[10],
        "aleatorio": dados[11]
    }


# ============================================================
# BARRAS DE HP E MANA
# ============================================================

def porcentagem(atual, maximo):

    if maximo <= 0:
        return 0

    return max(
        0,
        min(
            100,
            (atual / maximo) * 100
        )
    )


def criar_barra(atual, maximo, tamanho=20):

    if maximo <= 0:
        preenchido = 0
    else:
        preenchido = round(
            (atual / maximo) * tamanho
        )

    preenchido = max(
        0,
        min(tamanho, preenchido)
    )

    vazio = tamanho - preenchido

    return (
        "┃"
        + ("█" * preenchido)
        + ("░" * vazio)
        + "┃"
    )


def estado_recurso(atual, maximo):

    if atual <= 0:
        return "ZERADO"

    percentual = porcentagem(
        atual,
        maximo
    )

    if percentual >= 70:
        return "BOM"

    if percentual >= 30:
        return "BAIXO"

    return "CRÍTICO"


def mostrar_hp(atual, maximo):

    return (
        f"{criar_barra(atual, maximo)}\n"
        f"**{atual}/{maximo}** — "
        f"{estado_recurso(atual, maximo)}"
    )


def mostrar_mana(atual, maximo):

    return (
        f"{criar_barra(atual, maximo)}\n"
        f"**{atual}/{maximo}** — "
        f"{estado_recurso(atual, maximo)}"
    )


# ============================================================
# PERMISSÕES DE ALTERAÇÃO
# ============================================================

def pode_alterar_ficha(interaction, ficha):

    if eh_admin(interaction):
        return True

    if ficha["tipo"] == "jogador":
        return (
            ficha["dono_id"]
            == interaction.user.id
        )

    if ficha["tipo"] == "npc":
        return (
            ficha["mestre_id"]
            == interaction.user.id
        )

    return False


# ============================================================
# BOT ONLINE
# ============================================================

@bot.event
async def on_ready():

    print(
        f"Bot conectado como {bot.user}"
    )

    try:

        comandos = await bot.tree.sync()

        print(
            f"{len(comandos)} comandos sincronizados."
        )

    except Exception as erro:

        print(
            f"Erro ao sincronizar comandos: {erro}"
        )


# ============================================================
# DEFINIR MESTRE
# SOMENTE ADMINISTRADOR
# ============================================================

@bot.tree.command(
    name="definirmestre",
    description="Define o Mestre deste canal."
)
@app_commands.describe(
    jogador="Jogador que será o Mestre"
)
async def definirmestre(
    interaction: discord.Interaction,
    jogador: discord.Member
):

    if not eh_admin(interaction):

        await interaction.response.send_message(
            "❌ Somente administradores podem "
            "definir o Mestre.",
            ephemeral=True
        )

        return

    garantir_mesa(
        interaction.channel.id
    )

    cursor.execute("""
        UPDATE mesas
        SET mestre_id = ?
        WHERE channel_id = ?
    """, (
        jogador.id,
        interaction.channel.id
    ))

    cursor.execute("""
        UPDATE fichas
        SET mestre_id = ?
        WHERE channel_id = ?
        AND tipo = 'npc'
    """, (
        jogador.id,
        interaction.channel.id
    ))

    db.commit()

    await interaction.response.send_message(
        f"👑 **{jogador.display_name}** "
        f"agora é o Mestre deste canal!\n\n"
        f"👹 Os NPCs existentes também foram "
        f"atribuídos a ele."
    )


# ============================================================
# PASSAR MESTRE
# MESTRE ATUAL OU ADMINISTRADOR
# ============================================================

@bot.tree.command(
    name="passarmestre",
    description="Passa o cargo de Mestre para outro jogador."
)
@app_commands.describe(
    jogador="Jogador que será o novo Mestre"
)
async def passarmestre(
    interaction: discord.Interaction,
    jogador: discord.Member
):

    mestre_id = obter_mestre(
        interaction.channel.id
    )

    if (
        interaction.user.id != mestre_id
        and not eh_admin(interaction)
    ):

        await interaction.response.send_message(
            "❌ Somente o Mestre atual ou "
            "um administrador pode passar "
            "o cargo de Mestre.",
            ephemeral=True
        )

        return

    if jogador.id == interaction.user.id:

        await interaction.response.send_message(
            "❌ Você já é o Mestre deste canal.",
            ephemeral=True
        )

        return

    garantir_mesa(
        interaction.channel.id
    )

    cursor.execute("""
        UPDATE mesas
        SET mestre_id = ?
        WHERE channel_id = ?
    """, (
        jogador.id,
        interaction.channel.id
    ))

    cursor.execute("""
        UPDATE fichas
        SET mestre_id = ?
        WHERE channel_id = ?
        AND tipo = 'npc'
    """, (
        jogador.id,
        interaction.channel.id
    ))

    db.commit()

    await interaction.response.send_message(
        f"👑 **Mestre transferido!**\n\n"
        f"👑 Novo Mestre: {jogador.mention}\n"
        f"👹 Todos os NPCs deste canal "
        f"foram transferidos para o novo Mestre."
    )


# ============================================================
# MOSTRAR MESTRE
# ============================================================

@bot.tree.command(
    name="mestre",
    description="Mostra o Mestre deste canal."
)
async def mestre(
    interaction: discord.Interaction
):

    mestre_id = obter_mestre(
        interaction.channel.id
    )

    if mestre_id is None:

        await interaction.response.send_message(
            "👑 Este canal ainda não possui "
            "um Mestre."
        )

        return

    membro = interaction.guild.get_member(
        mestre_id
    )

    if membro:

        await interaction.response.send_message(
            f"👑 Mestre deste canal: "
            f"**{membro.display_name}**"
        )

    else:

        await interaction.response.send_message(
            f"👑 Mestre: <@{mestre_id}>"
        )


# ============================================================
# CRIAR FICHA DE JOGADOR
# ============================================================

@bot.tree.command(
    name="criarficha",
    description="Cria sua ficha neste canal."
)
@app_commands.describe(
    nome="Nome do personagem",
    hp="HP inicial e máximo",
    mana="Mana inicial e máxima"
)
async def criarficha(
    interaction: discord.Interaction,
    nome: str,
    hp: int,
    mana: int
):

    garantir_mesa(
        interaction.channel.id
    )

    existente = buscar_ficha_jogador(
        interaction.channel.id,
        interaction.user.id
    )

    if existente:

        await interaction.response.send_message(
            "⚠️ Você já possui uma ficha "
            "neste canal.",
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
            channel_id,
            dono_id,
            mestre_id,
            tipo,
            nome,
            hp_atual,
            hp_max,
            mana_atual,
            mana_max,
            xp,
            aleatorio
        )
        VALUES (?, ?, NULL, 'jogador', ?, ?, ?, ?, ?, 0, 0)
    """, (
        interaction.channel.id,
        interaction.user.id,
        nome,
        hp,
        hp,
        mana,
        mana
    ))

    db.commit()

    embed = discord.Embed(
        title=f"📜 {nome}",
        description="Ficha criada com sucesso!",
        color=discord.Color.green()
    )

    embed.add_field(
        name="❤️ HP",
        value=mostrar_hp(hp, hp),
        inline=False
    )

    embed.add_field(
        name="💧 Mana",
        value=mostrar_mana(mana, mana),
        inline=False
    )

    embed.add_field(
        name="⭐ XP",
        value="0",
        inline=False
    )

    await interaction.response.send_message(
        embed=embed
    )


# ============================================================
# MOSTRAR PRÓPRIA FICHA
# ============================================================

@bot.tree.command(
    name="ficha",
    description="Mostra sua ficha neste canal."
)
async def ficha(
    interaction: discord.Interaction
):

    dados = buscar_ficha_jogador(
        interaction.channel.id,
        interaction.user.id
    )

    if dados is None:

        await interaction.response.send_message(
            "❌ Você não possui uma ficha "
            "neste canal.",
            ephemeral=True
        )

        return

    f = transformar_ficha(dados)

    embed = discord.Embed(
        title=f"⚔️ {f['nome']}",
        description=(
            f"Jogador: {interaction.user.mention}"
        ),
        color=discord.Color.dark_red()
    )

    embed.add_field(
        name="❤️ HP",
        value=mostrar_hp(
            f["hp_atual"],
            f["hp_max"]
        ),
        inline=False
    )

    embed.add_field(
        name="💧 Mana",
        value=mostrar_mana(
            f["mana_atual"],
            f["mana_max"]
        ),
        inline=False
    )

    embed.add_field(
        name="⭐ XP",
        value=str(f["xp"]),
        inline=False
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


# ============================================================
# LISTAR FICHAS DE JOGADORES
# ============================================================

@bot.tree.command(
    name="fichas",
    description="Mostra as fichas dos jogadores deste canal."
)
async def fichas(
    interaction: discord.Interaction
):

    cursor.execute("""
        SELECT
            nome,
            hp_atual,
            hp_max,
            mana_atual,
            mana_max,
            xp,
            dono_id
        FROM fichas
        WHERE channel_id = ?
        AND tipo = 'jogador'
        ORDER BY nome
    """, (
        interaction.channel.id,
    ))

    dados = cursor.fetchall()

    if not dados:

        await interaction.response.send_message(
            "📜 Não existem fichas de "
            "jogadores neste canal."
        )

        return

    embed = discord.Embed(
        title="📜 Fichas dos jogadores",
        color=discord.Color.dark_red()
    )

    for (
        nome,
        hp_atual,
        hp_max,
        mana_atual,
        mana_max,
        xp,
        dono_id
    ) in dados:

        membro = interaction.guild.get_member(
            dono_id
        )

        jogador = (
            membro.mention
            if membro
            else f"<@{dono_id}>"
        )

        texto = (
            f"👤 {jogador}\n\n"
            f"❤️ **HP**\n"
            f"{mostrar_hp(hp_atual, hp_max)}\n\n"
            f"💧 **Mana**\n"
            f"{mostrar_mana(mana_atual, mana_max)}\n\n"
            f"⭐ **XP:** {xp}"
        )

        embed.add_field(
            name=f"⚔️ {nome}",
            value=texto,
            inline=False
        )

    await interaction.response.send_message(
        embed=embed
    )
