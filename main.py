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
    aleatorio INTEGER NOT NULL DEFAULT 0,

    forca INTEGER NOT NULL DEFAULT 0,
    destreza INTEGER NOT NULL DEFAULT 0,
    vigor INTEGER NOT NULL DEFAULT 0,
    inteligencia INTEGER NOT NULL DEFAULT 0,
    carisma INTEGER NOT NULL DEFAULT 0,
    raciocinio INTEGER NOT NULL DEFAULT 0,

    academicos INTEGER NOT NULL DEFAULT 0,
    idiomas INTEGER NOT NULL DEFAULT 0,
    oficios INTEGER NOT NULL DEFAULT 0,
    armas_brancas INTEGER NOT NULL DEFAULT 0,
    intimidacao INTEGER NOT NULL DEFAULT 0,
    ocultismo INTEGER NOT NULL DEFAULT 0,
    briga INTEGER NOT NULL DEFAULT 0,
    investigacao INTEGER NOT NULL DEFAULT 0,
    persuasao INTEGER NOT NULL DEFAULT 0,
    ciencias INTEGER NOT NULL DEFAULT 0,
    labia INTEGER NOT NULL DEFAULT 0,
    prontidao INTEGER NOT NULL DEFAULT 0,
    conhecimentos_gerais INTEGER NOT NULL DEFAULT 0,
    lideranca INTEGER NOT NULL DEFAULT 0,
    sobrevivencia INTEGER NOT NULL DEFAULT 0,
    conducao INTEGER NOT NULL DEFAULT 0,
    manha INTEGER NOT NULL DEFAULT 0,
    tecnologia INTEGER NOT NULL DEFAULT 0,
    esportes INTEGER NOT NULL DEFAULT 0,
    medicina INTEGER NOT NULL DEFAULT 0,
    mira INTEGER NOT NULL DEFAULT 0,
    esquiva INTEGER NOT NULL DEFAULT 0,
    furtividade INTEGER NOT NULL DEFAULT 0
)
""")


# ============================================================
# MIGRAÇÃO DO BANCO ANTIGO
# ============================================================

# Caso o banco já exista da versão anterior, adicionamos
# automaticamente as novas colunas.

colunas_novas = {
    "forca": "INTEGER NOT NULL DEFAULT 0",
    "destreza": "INTEGER NOT NULL DEFAULT 0",
    "vigor": "INTEGER NOT NULL DEFAULT 0",
    "inteligencia": "INTEGER NOT NULL DEFAULT 0",
    "carisma": "INTEGER NOT NULL DEFAULT 0",
    "raciocinio": "INTEGER NOT NULL DEFAULT 0",

    "academicos": "INTEGER NOT NULL DEFAULT 0",
    "idiomas": "INTEGER NOT NULL DEFAULT 0",
    "oficios": "INTEGER NOT NULL DEFAULT 0",
    "armas_brancas": "INTEGER NOT NULL DEFAULT 0",
    "intimidacao": "INTEGER NOT NULL DEFAULT 0",
    "ocultismo": "INTEGER NOT NULL DEFAULT 0",
    "briga": "INTEGER NOT NULL DEFAULT 0",
    "investigacao": "INTEGER NOT NULL DEFAULT 0",
    "persuasao": "INTEGER NOT NULL DEFAULT 0",
    "ciencias": "INTEGER NOT NULL DEFAULT 0",
    "labia": "INTEGER NOT NULL DEFAULT 0",
    "prontidao": "INTEGER NOT NULL DEFAULT 0",
    "conhecimentos_gerais": "INTEGER NOT NULL DEFAULT 0",
    "lideranca": "INTEGER NOT NULL DEFAULT 0",
    "sobrevivencia": "INTEGER NOT NULL DEFAULT 0",
    "conducao": "INTEGER NOT NULL DEFAULT 0",
    "manha": "INTEGER NOT NULL DEFAULT 0",
    "tecnologia": "INTEGER NOT NULL DEFAULT 0",
    "esportes": "INTEGER NOT NULL DEFAULT 0",
    "medicina": "INTEGER NOT NULL DEFAULT 0",
    "mira": "INTEGER NOT NULL DEFAULT 0",
    "esquiva": "INTEGER NOT NULL DEFAULT 0",
    "furtividade": "INTEGER NOT NULL DEFAULT 0"
}


cursor.execute("PRAGMA table_info(fichas)")
colunas_existentes = {
    coluna[1]
    for coluna in cursor.fetchall()
}


for coluna, tipo in colunas_novas.items():

    if coluna not in colunas_existentes:

        cursor.execute(
            f"ALTER TABLE fichas ADD COLUMN {coluna} {tipo}"
        )


db.commit()


# ============================================================
# BOT
# ============================================================

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# ============================================================
# DADOS DOS ATRIBUTOS
# ============================================================

ATRIBUTOS = {
    "FOR": "forca",
    "DES": "destreza",
    "VIG": "vigor",
    "INT": "inteligencia",
    "CAR": "carisma",
    "RAC": "raciocinio"
}


# ============================================================
# DADOS DAS PERÍCIAS
# ============================================================

PERICIAS = {
    "ACA": "academicos",
    "IDI": "idiomas",
    "OFI": "oficios",
    "ABR": "armas_brancas",
    "INTI": "intimidacao",
    "OCU": "ocultismo",
    "BRI": "briga",
    "INV": "investigacao",
    "PER": "persuasao",
    "CIE": "ciencias",
    "LAB": "labia",
    "PRO": "prontidao",
    "GER": "conhecimentos_gerais",
    "LID": "lideranca",
    "SOB": "sobrevivencia",
    "CON": "conducao",
    "MAN": "manha",
    "TEC": "tecnologia",
    "ESP": "esportes",
    "MED": "medicina",
    "MIR": "mira",
    "ESQ": "esquiva",
    "FUR": "furtividade"
}


# ============================================================
# NOMES VISUAIS
# ============================================================

NOMES_ATRIBUTOS = {
    "forca": ("💪", "For"),
    "destreza": ("🏹", "Des"),
    "vigor": ("🛡️", "Vig"),
    "inteligencia": ("🧠", "Int"),
    "carisma": ("🎭", "Car"),
    "raciocinio": ("💡", "Rac")
}


NOMES_PERICIAS = {
    "academicos": ("📚", "Acadêmicos"),
    "idiomas": ("🌎", "Idiomas"),
    "oficios": ("🔧", "Ofícios"),
    "armas_brancas": ("⚔️", "Armas Brancas"),
    "intimidacao": ("😈", "Intimidação"),
    "ocultismo": ("🔮", "Ocultismo"),
    "briga": ("👊", "Briga"),
    "investigacao": ("🔎", "Investigação"),
    "persuasao": ("🗣️", "Persuasão"),
    "ciencias": ("🔬", "Ciências"),
    "labia": ("🃏", "Lábia"),
    "prontidao": ("👁️", "Prontidão"),
    "conhecimentos_gerais": ("📖", "Conhec. Gerais"),
    "lideranca": ("👑", "Liderança"),
    "sobrevivencia": ("🌲", "Sobrevivência"),
    "conducao": ("🚗", "Condução"),
    "manha": ("🕵️", "Manha"),
    "tecnologia": ("💻", "Tecnologia"),
    "esportes": ("🏃", "Esportes"),
    "medicina": ("⚕️", "Medicina"),
    "mira": ("🎯", "Mira"),
    "esquiva": ("💨", "Esquiva"),
    "furtividade": ("🥷", "Furtividade")
}


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def garantir_mesa(channel_id):

    cursor.execute("""
        INSERT OR IGNORE INTO mesas (
            channel_id,
            mestre_id
        )
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


def buscar_ficha_jogador(
    channel_id,
    user_id
):

    cursor.execute("""
        SELECT *
        FROM fichas
        WHERE channel_id = ?
        AND dono_id = ?
        AND tipo = 'jogador'
        LIMIT 1
    """, (
        channel_id,
        user_id
    ))

    return cursor.fetchone()


def buscar_ficha(ficha_id):

    cursor.execute("""
        SELECT *
        FROM fichas
        WHERE id = ?
    """, (ficha_id,))

    return cursor.fetchone()


def obter_colunas_ficha():

    cursor.execute("PRAGMA table_info(fichas)")

    return [
        coluna[1]
        for coluna in cursor.fetchall()
    ]


def transformar_ficha(dados):

    if dados is None:
        return None

    colunas = obter_colunas_ficha()

    ficha = {}

    for indice, coluna in enumerate(colunas):

        ficha[coluna] = dados[indice]

    return ficha


# ============================================================
# CALCULAR RC
# ============================================================

def calcular_rc(ficha):

    return (
        ficha["destreza"]
        + ficha["esquiva"]
        + 5
    )


# ============================================================
# ESTADO DE HP E MANA
# ============================================================

def estado_recurso(atual, maximo):

    if atual <= 0:
        return "ZERADO"

    if maximo <= 0:
        return "ZERADO"

    percentual = (
        atual / maximo
    ) * 100

    if percentual >= 70:
        return "BOM"

    if percentual >= 30:
        return "BAIXO"

    return "CRÍTICO"


def mostrar_hp(atual, maximo):

    estado = estado_recurso(
        atual,
        maximo
    )

    simbolos = {
        "BOM": "🟢",
        "BAIXO": "🟡",
        "CRÍTICO": "🔴",
        "ZERADO": "⚫"
    }

    return (
        f"{simbolos.get(estado, '⚪')} "
        f"**{atual}/{maximo}** — **{estado}**"
    )


def mostrar_mana(atual, maximo):

    estado = estado_recurso(
        atual,
        maximo
    )

    simbolos = {
        "BOM": "🔵",
        "BAIXO": "🟡",
        "CRÍTICO": "🔴",
        "ZERADO": "⚫"
    }

    return (
        f"{simbolos.get(estado, '⚪')} "
        f"**{atual}/{maximo}** — **{estado}**"
    )


# ============================================================
# PERMISSÕES
# ============================================================

def pode_alterar_ficha(
    interaction,
    ficha
):

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
# EMBED — PÁGINA 1
# STATUS + ATRIBUTOS
# ============================================================

def criar_embed_status(
    ficha,
    jogador=None
):

    embed = discord.Embed(
        title=f"📜 FICHA DE {ficha['nome'].upper()}",
        color=discord.Color.dark_red()
    )

    if jogador:

        embed.description = (
            f"👤 Jogador: {jogador.mention}"
        )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    status = (
        f"❤️ **HP:** {mostrar_hp(ficha['hp_atual'], ficha['hp_max'])}\n"
        f"🔵 **Mana:** {mostrar_mana(ficha['mana_atual'], ficha['mana_max'])}\n\n"
        f"✨ **XP:** {ficha['xp']}\n"
        f"⚡ **RC:** {calcular_rc(ficha)}"
    )

    embed.add_field(
        name="❤️ STATUS",
        value=status,
        inline=False
    )

    # --------------------------------------------------------
    # ATRIBUTOS
    # --------------------------------------------------------

    atributos_esquerda = (
        f"💪 **For:** {ficha['forca']}\n"
        f"🛡️ **Vig:** {ficha['vigor']}\n"
        f"🎭 **Car:** {ficha['carisma']}"
    )

    atributos_direita = (
        f"🏹 **Des:** {ficha['destreza']}\n"
        f"🧠 **Int:** {ficha['inteligencia']}\n"
        f"💡 **Rac:** {ficha['raciocinio']}"
    )

    embed.add_field(
        name="⚔️ ATRIBUTOS",
        value=atributos_esquerda,
        inline=True
    )

    embed.add_field(
        name="\u200b",
        value=atributos_direita,
        inline=True
    )

    embed.set_footer(
        text="Página 1/2 • BotRPG"
    )

    return embed


# ============================================================
# EMBED — PÁGINA 2
# PERÍCIAS
# ============================================================

def criar_embed_pericias(ficha):

    embed = discord.Embed(
        title=f"🎯 PERÍCIAS — {ficha['nome']}",
        color=discord.Color.dark_red()
    )

    nomes = list(NOMES_PERICIAS.keys())

    metade = (len(nomes) + 1) // 2

    coluna_esquerda = nomes[:metade]
    coluna_direita = nomes[metade:]

    texto_esquerda = ""

    for nome in coluna_esquerda:

        emoji, nome_visual = NOMES_PERICIAS[nome]

        texto_esquerda += (
            f"{emoji} **{nome_visual}:** "
            f"{ficha[nome]}\n"
        )

    texto_direita = ""

    for nome in coluna_direita:

        emoji, nome_visual = NOMES_PERICIAS[nome]

        texto_direita += (
            f"{emoji} **{nome_visual}:** "
            f"{ficha[nome]}\n"
        )

    embed.add_field(
        name="\u200b",
        value=texto_esquerda,
        inline=True
    )

    embed.add_field(
        name="\u200b",
        value=texto_direita,
        inline=True
    )

    embed.set_footer(
        text="Página 2/2 • BotRPG"
    )

    return embed


# ============================================================
# VIEW DA FICHA
# ============================================================

class FichaView(discord.ui.View):

    def __init__(
        self,
        ficha,
        jogador=None
    ):

        super().__init__(
            timeout=300
        )

        self.ficha_id = ficha["id"]
        self.jogador_id = (
            jogador.id
            if jogador
            else None
        )

    async def interaction_check(
        self,
        interaction: discord.Interaction
    ):

        if (
            self.jogador_id is not None
            and interaction.user.id != self.jogador_id
            and not eh_admin(interaction)
            and not eh_mestre(interaction)
        ):

            await interaction.response.send_message(
                "❌ Você não pode controlar "
                "esta ficha.",
                ephemeral=True
            )

            return False

        return True

    @discord.ui.button(
        label="🎯 Perícias",
        style=discord.ButtonStyle.primary
    )
    async def pericias(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        dados = buscar_ficha(
            self.ficha_id
        )

        if dados is None:

            await interaction.response.send_message(
                "❌ Esta ficha não existe mais.",
                ephemeral=True
            )

            return

        ficha = transformar_ficha(
            dados
        )

        await interaction.response.edit_message(
            embed=criar_embed_pericias(ficha),
            view=self
        )

    @discord.ui.button(
        label="📜 Voltar",
        style=discord.ButtonStyle.secondary
    )
    async def voltar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        dados = buscar_ficha(
            self.ficha_id
        )

        if dados is None:

            await interaction.response.send_message(
                "❌ Esta ficha não existe mais.",
                ephemeral=True
            )

            return

        ficha = transformar_ficha(
            dados
        )

        jogador = None

        if ficha["dono_id"]:

            jogador = interaction.guild.get_member(
                ficha["dono_id"]
            )

        await interaction.response.edit_message(
            embed=criar_embed_status(
                ficha,
                jogador
            ),
            view=self
        )


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
        f"foram transferidos."
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
# INTERPRETAR VALORES DA CRIAÇÃO
# ============================================================

def interpretar_valores(texto):

    valores = {}

    if not texto:
        return None, "Nenhum valor foi informado."

    partes = texto.replace(",", " ").split()

    for parte in partes:

        if "=" not in parte:

            return None, (
                f"❌ Formato inválido: `{parte}`.\n"
                f"Use, por exemplo: `FOR=3`."
            )

        chave, valor = parte.split(
            "=",
            1
        )

        chave = chave.upper().strip()

        try:

            valor = int(
                valor.strip()
            )

        except ValueError:

            return None, (
                f"❌ O valor de `{chave}` "
                f"precisa ser um número."
            )

        if valor < 0:

            return None, (
                f"❌ O valor de `{chave}` "
                f"não pode ser negativo."
            )

        if chave in ATRIBUTOS:

            coluna = ATRIBUTOS[chave]

        elif chave in PERICIAS:

            coluna = PERICIAS[chave]

        else:

            return None, (
                f"❌ Código desconhecido: `{chave}`."
            )

        valores[coluna] = valor

    # Verifica atributos obrigatórios

    faltando_atributos = [
        chave
        for chave in ATRIBUTOS
        if ATRIBUTOS[chave] not in valores
    ]

    if faltando_atributos:

        return None, (
            "❌ Faltam atributos:\n"
            + ", ".join(faltando_atributos)
        )

    # Verifica perícias obrigatórias

    faltando_pericias = [
        chave
        for chave in PERICIAS
        if PERICIAS[chave] not in valores
    ]

    if faltando_pericias:

        return None, (
            "❌ Faltam perícias:\n"
            + ", ".join(faltando_pericias)
        )

    return valores, None


# ============================================================
# CRIAR FICHA
# ============================================================

@bot.tree.command(
    name="criarficha",
    description="Cria sua ficha completa."
)
@app_commands.describe(
    nome="Nome do personagem",
    hp="HP inicial e máximo",
    mana="Mana inicial e máxima",
    valores=(
        "Valores. Ex: FOR=3 DES=4 VIG=2 INT=3 CAR=4 RAC=2 "
        "ACA=3 IDI=2 OFI=4..."
    )
)
async def criarficha(
    interaction: discord.Interaction,
    nome: str,
    hp: int,
    mana: int,
    valores: str
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

    valores_lidos, erro = interpretar_valores(
        valores
    )

    if erro:

        await interaction.response.send_message(
            erro,
            ephemeral=True
        )

        return

    nome = nome[:50]

    colunas = [
        "forca",
        "destreza",
        "vigor",
        "inteligencia",
        "carisma",
        "raciocinio",

        "academicos",
        "idiomas",
        "oficios",
        "armas_brancas",
        "intimidacao",
        "ocultismo",
        "briga",
        "investigacao",
        "persuasao",
        "ciencias",
        "labia",
        "prontidao",
        "conhecimentos_gerais",
        "lideranca",
        "sobrevivencia",
        "conducao",
        "manha",
        "tecnologia",
        "esportes",
        "medicina",
        "mira",
        "esquiva",
        "furtividade"
    ]

    valores_sql = [
        valores_lidos[coluna]
        for coluna in colunas
    ]

    placeholders = ", ".join(
        ["?"] * (
            12 + len(colunas)
        )
    )

    sql = f"""
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
            aleatorio,
            {", ".join(colunas)}
        )
        VALUES (
            {placeholders}
        )
    """

    parametros = [
        interaction.channel.id,
        interaction.user.id,
        None,
        "jogador",
        nome,
        hp,
        hp,
        mana,
        mana,
        0,
        0
    ]

    parametros.extend(
        valores_sql
    )

    cursor.execute(
        sql,
        parametros
    )

    db.commit()

    ficha_id = cursor.lastrowid

    ficha = transformar_ficha(
        buscar_ficha(ficha_id)
    )

    embed = criar_embed_status(
        ficha,
        interaction.user
    )

    await interaction.response.send_message(
        embed=embed,
        view=FichaView(
            ficha,
            interaction.user
        )
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

    f = transformar_ficha(
        dados
    )

    embed = criar_embed_status(
        f,
        interaction.user
    )

    await interaction.response.send_message(
        embed=embed,
        view=FichaView(
            f,
            interaction.user
        ),
        ephemeral=True
    )


# ============================================================
# VER FICHA DE OUTRO JOGADOR
# ============================================================

@bot.tree.command(
    name="verficha",
    description="Visualiza a ficha de outro jogador."
)
@app_commands.describe(
    jogador="Jogador cuja ficha você deseja visualizar"
)
async def verficha(
    interaction: discord.Interaction,
    jogador: discord.Member
):

    dados = buscar_ficha_jogador(
        interaction.channel.id,
        jogador.id
    )

    if dados is None:

        await interaction.response.send_message(
            f"❌ **{jogador.display_name}** "
            f"não possui uma ficha neste canal.",
            ephemeral=True
        )

        return

    f = transformar_ficha(
        dados
    )

    embed = criar_embed_status(
        f,
        jogador
    )

    await interaction.response.send_message(
        embed=embed,
        view=FichaView(
            f,
            jogador
        )
    )


# ============================================================
# LISTAR FICHAS
# ============================================================

@bot.tree.command(
    name="fichas",
    description="Mostra as fichas dos jogadores deste canal."
)
async def fichas(
    interaction: discord.Interaction
):

    cursor.execute("""
        SELECT id
        FROM fichas
        WHERE channel_id = ?
        AND tipo = 'jogador'
        ORDER BY nome
    """, (
        interaction.channel.id,
    ))

    resultados = cursor.fetchall()

    if not resultados:

        await interaction.response.send_message(
            "📜 Não existem fichas de "
            "jogadores neste canal."
        )

        return

    embed = discord.Embed(
        title="📜 Fichas dos jogadores",
        color=discord.Color.dark_red()
    )

    for resultado in resultados:

        f = transformar_ficha(
            buscar_ficha(resultado[0])
        )

        membro = interaction.guild.get_member(
            f["dono_id"]
        )

        jogador = (
            membro.mention
            if membro
            else f"<@{f['dono_id']}>"
        )

        texto = (
            f"👤 {jogador}\n"
            f"❤️ HP: **{f['hp_atual']}/{f['hp_max']}**\n"
            f"🔵 Mana: **{f['mana_atual']}/{f['mana_max']}**\n"
            f"✨ XP: **{f['xp']}**\n"
            f"⚡ RC: **{calcular_rc(f)}**"
        )

        embed.add_field(
            name=f"⚔️ {f['nome']}",
            value=texto,
            inline=False
        )

    await interaction.response.send_message(
        embed=embed
    )


# ============================================================
# APAGAR PRÓPRIA FICHA
# ============================================================

@bot.tree.command(
    name="apagarficha",
    description="Apaga sua ficha deste canal."
)
async def apagarficha(
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

    f = transformar_ficha(
        dados
    )

    cursor.execute(
        "DELETE FROM fichas WHERE id = ?",
        (f["id"],)
    )

    db.commit()

    await interaction.response.send_message(
        f"🗑️ A ficha **{f['nome']}** "
        f"foi apagada."
    )


# ============================================================
# ALTERAR ATRIBUTOS
# ============================================================

@bot.tree.command(
    name="alteraratributos",
    description="Altera os atributos da sua ficha."
)
@app_commands.describe(
    valores=(
        "Ex: FOR=3 DES=4 VIG=2 INT=3 CAR=4 RAC=2"
    )
)
async def alteraratributos(
    interaction: discord.Interaction,
    valores: str
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

    ficha = transformar_ficha(
        dados
    )

    if not pode_alterar_ficha(
        interaction,
        ficha
    ):

        await interaction.response.send_message(
            "❌ Você não pode alterar "
            "esta ficha.",
            ephemeral=True
        )

        return

    partes = valores.replace(",", " ").split()

    novos = {}

    for parte in partes:

        if "=" not in parte:

            await interaction.response.send_message(
                f"❌ Formato inválido: `{parte}`.",
                ephemeral=True
            )

            return

        chave, valor = parte.split(
            "=",
            1
        )

        chave = chave.upper()

        if chave not in ATRIBUTOS:

            await interaction.response.send_message(
                f"❌ `{chave}` não é um atributo válido.",
                ephemeral=True
            )

            return

        try:

            valor = int(valor)

        except ValueError:

            await interaction.response.send_message(
                f"❌ Valor inválido para `{chave}`.",
                ephemeral=True
            )

            return

        if valor < 0:

            await interaction.response.send_message(
                "❌ Os valores não podem ser negativos.",
                ephemeral=True
            )

            return

        novos[
            ATRIBUTOS[chave]
        ] = valor

    if not novos:

        await interaction.response.send_message(
            "❌ Nenhum atributo foi informado.",
            ephemeral=True
        )

        return

    sets = ", ".join(
        f"{coluna} = ?"
        for coluna in novos
    )

    cursor.execute(
        f"""
        UPDATE fichas
        SET {sets}
        WHERE id = ?
        """,
        [
            *novos.values(),
            ficha["id"]
        ]
    )

    db.commit()

    await interaction.response.send_message(
        "📊 **Atributos atualizados!**\n\n"
        + "\n".join(
            f"**{chave}:** {valor}"
            for chave, valor in novos.items()
        )
    )


# ============================================================
# ALTERAR PERÍCIAS
# ============================================================

@bot.tree.command(
    name="alterarpericias",
    description="Altera as perícias da sua ficha."
)
@app_commands.describe(
    valores=(
        "Ex: ACA=3 IDI=2 OFI=4 ESQ=3 MIR=2"
    )
)
async def alterarpericias(
    interaction: discord.Interaction,
    valores: str
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

    ficha = transformar_ficha(
        dados
    )

    if not pode_alterar_ficha(
        interaction,
        ficha
    ):

        await interaction.response.send_message(
            "❌ Você não pode alterar "
            "esta ficha.",
            ephemeral=True
        )

        return

    partes = valores.replace(",", " ").split()

    novos = {}

    for parte in partes:

        if "=" not in parte:

            await interaction.response.send_message(
                f"❌ Formato inválido: `{parte}`.",
                ephemeral=True
            )

            return

        chave, valor = parte.split(
            "=",
            1
        )

        chave = chave.upper()

        if chave not in PERICIAS:

            await interaction.response.send_message(
                f"❌ `{chave}` não é uma perícia válida.",
                ephemeral=True
            )

            return

        try:

            valor = int(valor)

        except ValueError:

            await interaction.response.send_message(
                f"❌ Valor inválido para `{chave}`.",
                ephemeral=True
            )

            return

        if valor < 0:

            await interaction.response.send_message(
                "❌ Os valores não podem ser negativos.",
                ephemeral=True
            )

            return

        novos[
            PERICIAS[chave]
        ] = valor

    if not novos:

        await interaction.response.send_message(
            "❌ Nenhuma perícia foi informada.",
            ephemeral=True
        )

        return

    sets = ", ".join(
        f"{coluna} = ?"
        for coluna in novos
    )

    cursor.execute(
        f"""
        UPDATE fichas
        SET {sets}
        WHERE id = ?
        """,
        [
            *novos.values(),
            ficha["id"]
        ]
    )

    db.commit()

    await interaction.response.send_message(
        "🎯 **Perícias atualizadas!**\n\n"
        + "\n".join(
            f"**{chave}:** {valor}"
            for chave, valor in novos.items()
        )
    )


# ============================================================
# ALTERAR HP E MANA
# ============================================================

@bot.tree.command(
    name="alterarficha",
    description="Altera HP e Mana máximos de uma ficha."
)
@app_commands.describe(
    jogador="Jogador da ficha",
    hp="Novo HP máximo",
    mana="Nova Mana máxima"
)
async def alterarficha(
    interaction: discord.Interaction,
    jogador: discord.Member,
    hp: int,
    mana: int
):

    dados = buscar_ficha_jogador(
        interaction.channel.id,
        jogador.id
    )

    if dados is None:

        await interaction.response.send_message(
            "❌ Esse jogador não possui "
            "uma ficha neste canal.",
            ephemeral=True
        )

        return

    f = transformar_ficha(
        dados
    )

    if not pode_alterar_ficha(
        interaction,
        f
    ):

        await interaction.response.send_message(
            "❌ Você só pode alterar "
            "sua própria ficha.",
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
        SET hp_atual = ?,
            hp_max = ?,
            mana_atual = ?,
            mana_max = ?
        WHERE id = ?
    """, (
        hp,
        hp,
        mana,
        mana,
        f["id"]
    ))

    db.commit()

    await interaction.response.send_message(
        f"⚙️ Ficha de **{f['nome']}** alterada!\n\n"
        f"❤️ HP: **{hp}/{hp}**\n"
        f"🔵 Mana: **{mana}/{mana}**"
    )


# ============================================================
# MODAL DE VALOR
# ============================================================

class ValorModal(discord.ui.Modal):

    def __init__(
        self,
        titulo,
        acao,
        ficha_id
    ):

        super().__init__(
            title=titulo
        )

        self.acao = acao
        self.ficha_id = ficha_id

        self.valor = discord.ui.TextInput(
            label="Quantidade",
            placeholder="Digite um número",
            required=True,
            max_length=10
        )

        self.add_item(
            self.valor
        )

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        try:

            valor = int(
                self.valor.value
            )

        except ValueError:

            await interaction.response.send_message(
                "❌ Digite somente números.",
                ephemeral=True
            )

            return

        if valor <= 0:

            await interaction.response.send_message(
                "❌ O valor precisa ser maior que 0.",
                ephemeral=True
            )

            return

        dados = buscar_ficha(
            self.ficha_id
        )

        if dados is None:

            await interaction.response.send_message(
                "❌ Essa ficha não existe mais.",
                ephemeral=True
            )

            return

        f = transformar_ficha(
            dados
        )

        if (
            f["channel_id"]
            != interaction.channel.id
        ):

            await interaction.response.send_message(
                "❌ Essa ficha pertence "
                "a outro canal.",
                ephemeral=True
            )

            return

        if not pode_alterar_ficha(
            interaction,
            f
        ):

            await interaction.response.send_message(
                "❌ Você não pode alterar "
                "esta ficha.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # DANO
        # ----------------------------------------------------

        if self.acao == "dano":

            novo_hp = max(
                0,
                f["hp_atual"] - valor
            )

            cursor.execute("""
                UPDATE fichas
                SET hp_atual = ?
                WHERE id = ?
            """, (
                novo_hp,
                f["id"]
            ))

            db.commit()

            if (
                f["tipo"] == "npc"
                and novo_hp <= 0
            ):

                cursor.execute(
                    "DELETE FROM fichas WHERE id = ?",
                    (f["id"],)
                )

                db.commit()

                await interaction.response.send_message(
                    f"💥 **{interaction.user.display_name}** "
                    f"causou **{valor} de dano** em "
                    f"**{f['nome']}**!\n\n"
                    f"💀 **{f['nome']} morreu!**"
                )

                return

            await interaction.response.send_message(
                f"💥 **{interaction.user.display_name}** "
                f"causou **{valor} de dano** em "
                f"**{f['nome']}**!\n\n"
                f"❤️ HP: "
                f"{mostrar_hp(novo_hp, f['hp_max'])}"
            )

            return

        # ----------------------------------------------------
        # CURA
        # ----------------------------------------------------

        if self.acao == "cura":

            novo_hp = min(
                f["hp_max"],
                f["hp_atual"] + valor
            )

            recuperado = (
                novo_hp - f["hp_atual"]
            )

            cursor.execute("""
                UPDATE fichas
                SET hp_atual = ?
                WHERE id = ?
            """, (
                novo_hp,
                f["id"]
            ))

            db.commit()

            await interaction.response.send_message(
                f"💚 **{interaction.user.display_name}** "
                f"curou **{f['nome']}** em "
                f"**{recuperado} HP**!\n\n"
                f"❤️ HP: "
                f"{mostrar_hp(novo_hp, f['hp_max'])}"
            )

            return

        # ----------------------------------------------------
        # RECUPERAR MANA
        # ----------------------------------------------------

        if self.acao == "recuperarmana":

            nova_mana = min(
                f["mana_max"],
                f["mana_atual"] + valor
            )

            recuperado = (
                nova_mana - f["mana_atual"]
            )

            cursor.execute("""
                UPDATE fichas
                SET mana_atual = ?
                WHERE id = ?
            """, (
                nova_mana,
                f["id"]
            ))

            db.commit()

            await interaction.response.send_message(
                f"💧 **{interaction.user.display_name}** "
                f"recuperou **{recuperado} Mana** "
                f"de **{f['nome']}**!\n\n"
                f"🔵 Mana: "
                f"{mostrar_mana(nova_mana, f['mana_max'])}"
            )

            return


# ============================================================
# SELEÇÃO DE ALVO
# ============================================================

class AlvoSelect(
    discord.ui.Select
):

    def __init__(
        self,
        interaction,
        acao
    ):

        self.acao = acao
        self.autor_id = interaction.user.id

        cursor.execute("""
            SELECT id, nome, tipo
            FROM fichas
            WHERE channel_id = ?
            ORDER BY tipo, nome
            LIMIT 25
        """, (
            interaction.channel.id,
        ))

        resultados = cursor.fetchall()

        opcoes = []

        for indice, (
            ficha_id,
            nome,
            tipo
        ) in enumerate(
            resultados,
            start=1
        ):

            if tipo == "npc":

                emoji = "👹"
                label = f"NPC {indice}"
                descricao = "NPC — ficha oculta"

            else:

                emoji = "👤"
                label = nome[:100]
                descricao = "Jogador"

            opcoes.append(
                discord.SelectOption(
                    label=label,
                    value=str(ficha_id),
                    emoji=emoji,
                    description=descricao[:100]
                )
            )

        super().__init__(
            placeholder="Escolha o alvo...",
            min_values=1,
            max_values=1,
            options=opcoes
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        if (
            interaction.user.id
            != self.autor_id
        ):

            await interaction.response.send_message(
                "❌ Somente quem iniciou "
                "a ação pode escolher o alvo.",
                ephemeral=True
            )

            return

        ficha_id = int(
            self.values[0]
        )

        dados = buscar_ficha(
            ficha_id
        )

        if dados is None:

            await interaction.response.send_message(
                "❌ Essa ficha não existe mais.",
                ephemeral=True
            )

            return

        f = transformar_ficha(
            dados
        )

        if (
            f["channel_id"]
            != interaction.channel.id
        ):

            await interaction.response.send_message(
                "❌ Esse alvo pertence "
                "a outro canal.",
                ephemeral=True
            )

            return

        # Dano pode ser aplicado pelo Mestre,
        # administrador ou dono da ficha.

        if self.acao == "dano":

            titulo = "Quantidade de dano"

        elif self.acao == "cura":

            titulo = "Quantidade de cura"

        else:

            titulo = "Quantidade de Mana"

        await interaction.response.send_modal(
            ValorModal(
                titulo,
                self.acao,
                ficha_id
            )
        )


class AlvoView(
    discord.ui.View
):

    def __init__(
        self,
        interaction,
        acao
    ):

        super().__init__(
            timeout=60
        )

        cursor.execute("""
            SELECT id
            FROM fichas
            WHERE channel_id = ?
            LIMIT 25
        """, (
            interaction.channel.id,
        ))

        resultados = cursor.fetchall()

        if resultados:

            self.add_item(
                AlvoSelect(
                    interaction,
                    acao
                )
            )


# ============================================================
# DANO
# ============================================================

@bot.tree.command(
    name="dano",
    description="Escolhe uma ficha para receber dano."
)
async def dano(
    interaction: discord.Interaction
):

    cursor.execute("""
        SELECT id
        FROM fichas
        WHERE channel_id = ?
        LIMIT 25
    """, (
        interaction.channel.id,
    ))

    if not cursor.fetchall():

        await interaction.response.send_message(
            "❌ Não existem fichas "
            "neste canal.",
            ephemeral=True
        )

        return

    await interaction.response.send_message(
        "💥 **Escolha quem receberá o dano:**",
        view=AlvoView(
            interaction,
            "dano"
        ),
        ephemeral=True
    )


# ============================================================
# CURA
# ============================================================

@bot.tree.command(
    name="cura",
    description="Escolhe uma ficha para receber cura."
)
async def cura(
    interaction: discord.Interaction
):

    cursor.execute("""
        SELECT id
        FROM fichas
        WHERE channel_id = ?
        LIMIT 25
    """, (
        interaction.channel.id,
    ))

    if not cursor.fetchall():

        await interaction.response.send_message(
            "❌ Não existem fichas "
            "neste canal.",
            ephemeral=True
        )

        return

    await interaction.response.send_message(
        "💚 **Escolha quem receberá a cura:**",
        view=AlvoView(
            interaction,
            "cura"
        ),
        ephemeral=True
    )


# ============================================================
# RECUPERAR MANA
# ============================================================

@bot.tree.command(
    name="recuperarmana",
    description="Escolhe uma ficha para recuperar Mana."
)
async def recuperarmana(
    interaction: discord.Interaction
):

    cursor.execute("""
        SELECT id
        FROM fichas
        WHERE channel_id = ?
        LIMIT 25
    """, (
        interaction.channel.id,
    ))

    if not cursor.fetchall():

        await interaction.response.send_message(
            "❌ Não existem fichas "
            "neste canal.",
            ephemeral=True
        )

        return

    await interaction.response.send_message(
        "💧 **Escolha quem recuperará Mana:**",
        view=AlvoView(
            interaction,
            "recuperarmana"
        ),
        ephemeral=True
    )


# ============================================================
# GASTAR MANA
# ============================================================

@bot.tree.command(
    name="gastarmana",
    description="Gasta Mana da sua própria ficha."
)
@app_commands.describe(
    valor="Quantidade de Mana gasta"
)
async def gastarmana(
    interaction: discord.Interaction,
    valor: int
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

    if valor <= 0:

        await interaction.response.send_message(
            "❌ O valor precisa ser maior que 0.",
            ephemeral=True
        )

        return

    f = transformar_ficha(
        dados
    )

    if valor > f["mana_atual"]:

        await interaction.response.send_message(
            "❌ Você não possui Mana suficiente.",
            ephemeral=True
        )

        return

    nova_mana = (
        f["mana_atual"] - valor
    )

    cursor.execute("""
        UPDATE fichas
        SET mana_atual = ?
        WHERE id = ?
    """, (
        nova_mana,
        f["id"]
    ))

    db.commit()

    await interaction.response.send_message(
        f"🔮 **{f['nome']}** gastou "
        f"**{valor} de Mana**!\n\n"
        f"🔵 Mana: "
        f"{mostrar_mana(nova_mana, f['mana_max'])}"
    )


# ============================================================
# ADICIONAR XP
# ============================================================

@bot.tree.command(
    name="addxp",
    description="Adiciona XP a uma ficha de jogador."
)
@app_commands.describe(
    jogador="Jogador que receberá XP",
    valor="Quantidade de XP"
)
async def addxp(
    interaction: discord.Interaction,
    jogador: discord.Member,
    valor: int
):

    dados = buscar_ficha_jogador(
        interaction.channel.id,
        jogador.id
    )

    if dados is None:

        await interaction.response.send_message(
            "❌ Esse jogador não possui "
            "uma ficha neste canal.",
            ephemeral=True
        )

        return

    f = transformar_ficha(
        dados
    )

    if not eh_admin(interaction):

        if f["dono_id"] != interaction.user.id:

            await interaction.response.send_message(
                "❌ Você só pode alterar o XP "
                "da sua própria ficha.",
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
        WHERE id = ?
    """, (
        valor,
        f["id"]
    ))

    db.commit()

    cursor.execute(
        "SELECT xp FROM fichas WHERE id = ?",
        (f["id"],)
    )

    xp_atual = cursor.fetchone()[0]

    await interaction.response.send_message(
        f"✨ **{f['nome']}** recebeu "
        f"**{valor} XP**!\n"
        f"✨ XP atual: **{xp_atual}**"
    )


# ============================================================
# CRIAR NPC
# ============================================================

@bot.tree.command(
    name="criarnpc",
    description="Cria um NPC neste canal."
)
@app_commands.describe(
    aleatorio="Escolha se o NPC será aleatório",
    nome="Nome do NPC",
    hp="HP do NPC",
    mana="Mana do NPC"
)
@app_commands.choices(
    aleatorio=[
        app_commands.Choice(
            name="Sim",
            value="sim"
        ),
        app_commands.Choice(
            name="Não",
            value="nao"
        )
    ]
)
async def criarnpc(
    interaction: discord.Interaction,
    aleatorio: app_commands.Choice[str],
    nome: str = None,
    hp: int = None,
    mana: int = None
):

    garantir_mesa(
        interaction.channel.id
    )

    if (
        not eh_mestre(interaction)
        and not eh_admin(interaction)
    ):

        await interaction.response.send_message(
            "❌ Somente o Mestre deste canal "
            "pode criar NPCs.",
            ephemeral=True
        )

        return

    if aleatorio.value == "sim":

        nomes = [
            "Goblin",
            "Orc",
            "Esqueleto",
            "Bandido",
            "Lobo",
            "Zumbi",
            "Slime",
            "Aranha Gigante",
            "Cultista",
            "Guardião",
            "Golem",
            "Morcego Gigante",
            "Troll",
            "Ladrão",
            "Cavaleiro Sombrio"
        ]

        nome = random.choice(nomes)

        hp = random.randint(
            20,
            150
        )

        mana = random.randint(
            0,
            100
        )

        aleatorio_valor = 1

    else:

        if not nome:

            await interaction.response.send_message(
                "❌ Informe o nome do NPC.",
                ephemeral=True
            )

            return

        if hp is None:

            await interaction.response.send_message(
                "❌ Informe o HP do NPC.",
                ephemeral=True
            )

            return

        if mana is None:

            await interaction.response.send_message(
                "❌ Informe a Mana do NPC.",
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

        aleatorio_valor = 0

    mestre_id = obter_mestre(
        interaction.channel.id
    )

    if mestre_id is None:

        mestre_id = interaction.user.id

        cursor.execute("""
            UPDATE mesas
            SET mestre_id = ?
            WHERE channel_id = ?
        """, (
            mestre_id,
            interaction.channel.id
        ))

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
        VALUES (
            ?, ?, ?, 'npc',
            ?, ?, ?, ?, ?, 0, ?
        )
    """, (
        interaction.channel.id,
        None,
        mestre_id,
        nome[:50],
        hp,
        hp,
        mana,
        mana,
        aleatorio_valor
    ))

    db.commit()

    await interaction.response.send_message(
        f"👹 **NPC criado!**\n\n"
        f"👹 **{nome}**\n"
        f"❤️ HP: **{hp}/{hp}**\n"
        f"🔵 Mana: **{mana}/{mana}**",
        ephemeral=True
    )


# ============================================================
# LISTAR NPCS
# ============================================================

@bot.tree.command(
    name="npcs",
    description="Mostra as fichas completas dos NPCs."
)
async def npcs(
    interaction: discord.Interaction
):

    if (
        not eh_mestre(interaction)
        and not eh_admin(interaction)
    ):

        await interaction.response.send_message(
            "❌ Somente o Mestre pode visualizar "
            "as fichas dos NPCs.",
            ephemeral=True
        )

        return

    cursor.execute("""
        SELECT id
        FROM fichas
        WHERE channel_id = ?
        AND tipo = 'npc'
        ORDER BY nome
    """, (
        interaction.channel.id,
    ))

    resultados = cursor.fetchall()

    if not resultados:

        await interaction.response.send_message(
            "👹 Não existem NPCs neste canal.",
            ephemeral=True
        )

        return

    embed = discord.Embed(
        title="👹 NPCs da mesa",
        color=discord.Color.orange()
    )

    for resultado in resultados:

        f = transformar_ficha(
            buscar_ficha(resultado[0])
        )

        texto = (
            f"❤️ HP: **{f['hp_atual']}/{f['hp_max']}**\n"
            f"🔵 Mana: **{f['mana_atual']}/{f['mana_max']}**\n"
            f"✨ XP: **{f['xp']}**"
        )

        embed.add_field(
            name=f"👹 {f['nome']}",
            value=texto,
            inline=False
        )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


# ============================================================
# ALTERAR NPC
# ============================================================

@bot.tree.command(
    name="alternpc",
    description="Altera um NPC."
)
@app_commands.describe(
    nome="Nome atual do NPC",
    hp="Novo HP máximo",
    mana="Nova Mana máxima"
)
async def alternpc(
    interaction: discord.Interaction,
    nome: str,
    hp: int,
    mana: int
):

    if (
        not eh_mestre(interaction)
        and not eh_admin(interaction)
    ):

        await interaction.response.send_message(
            "❌ Somente o Mestre pode "
            "alterar NPCs.",
            ephemeral=True
        )

        return

    cursor.execute("""
        SELECT id
        FROM fichas
        WHERE channel_id = ?
        AND tipo = 'npc'
        AND nome = ?
        LIMIT 1
    """, (
        interaction.channel.id,
        nome
    ))

    resultado = cursor.fetchone()

    if resultado is None:

        await interaction.response.send_message(
            "❌ NPC não encontrado.",
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
        SET hp_atual = ?,
            hp_max = ?,
            mana_atual = ?,
            mana_max = ?
        WHERE id = ?
    """, (
        hp,
        hp,
        mana,
        mana,
        resultado[0]
    ))

    db.commit()

    await interaction.response.send_message(
        f"⚙️ NPC **{nome}** alterado!\n\n"
        f"❤️ HP: **{hp}/{hp}**\n"
        f"🔵 Mana: **{mana}/{mana}**"
    )


# ============================================================
# APAGAR NPC
# ============================================================

@bot.tree.command(
    name="apagarnpc",
    description="Apaga um NPC deste canal."
)
@app_commands.describe(
    nome="Nome exato do NPC"
)
async def apagarnpc(
    interaction: discord.Interaction,
    nome: str
):

    if (
        not eh_mestre(interaction)
        and not eh_admin(interaction)
    ):

        await interaction.response.send_message(
            "❌ Somente o Mestre ou um administrador "
            "pode apagar NPCs.",
            ephemeral=True
        )

        return

    cursor.execute("""
        SELECT id
        FROM fichas
        WHERE channel_id = ?
        AND tipo = 'npc'
        AND nome = ?
        LIMIT 1
    """, (
        interaction.channel.id,
        nome
    ))

    resultado = cursor.fetchone()

    if resultado is None:

        await interaction.response.send_message(
            f"❌ Não encontrei um NPC chamado "
            f"**{nome}** neste canal.",
            ephemeral=True
        )

        return

    cursor.execute(
        "DELETE FROM fichas WHERE id = ?",
        (resultado[0],)
    )

    db.commit()

    await interaction.response.send_message(
        f"🗑️ O NPC **{nome}** foi apagado."
    )


# ============================================================
# HELP
# ============================================================

@bot.tree.command(
    name="help",
    description="Mostra todos os comandos disponíveis."
)
async def help(
    interaction: discord.Interaction
):

    embed = discord.Embed(
        title="📖 Comandos do BotRPG",
        description=(
            "Sistema de fichas da mesa."
        ),
        color=discord.Color.dark_red()
    )

    embed.add_field(
        name="👤 Jogador",
        value=(
            "`/criarficha` — Cria sua ficha completa.\n"
            "`/ficha` — Mostra sua ficha.\n"
            "`/verficha` — Visualiza outra ficha.\n"
            "`/fichas` — Lista as fichas.\n"
            "`/apagarficha` — Apaga sua ficha.\n"
            "`/alterarficha` — Altera HP e Mana.\n"
            "`/alteraratributos` — Altera atributos.\n"
            "`/alterarpericias` — Altera perícias.\n"
            "`/gastarmana` — Gasta Mana.\n"
            "`/dano` — Aplica dano.\n"
            "`/cura` — Cura uma ficha.\n"
            "`/recuperarmana` — Recupera Mana.\n"
            "`/addxp` — Adiciona XP."
        ),
        inline=False
    )

    embed.add_field(
        name="👑 Mestre",
        value=(
            "`/criarnpc` — Cria um NPC.\n"
            "`/npcs` — Mostra os NPCs.\n"
            "`/alternpc` — Altera um NPC.\n"
            "`/apagarnpc` — Apaga um NPC.\n"
            "`/passarmestre` — Passa o cargo.\n"
            "`/mestre` — Mostra o Mestre."
        ),
        inline=False
    )

    embed.add_field(
        name="🛡️ Administrador",
        value=(
            "`/definirmestre` — Define o Mestre.\n"
            "`/passarmestre` — Transfere o Mestre.\n"
            "`/alterarficha` — Altera fichas.\n"
            "`/criarnpc` — Cria NPCs.\n"
            "`/alternpc` — Altera NPCs.\n"
            "`/apagarnpc` — Apaga NPCs."
        ),
        inline=False
    )

    embed.add_field(
        name="📊 Códigos de criação",
        value=(
            "**Atributos:**\n"
            "`FOR` `DES` `VIG` `INT` `CAR` `RAC`\n\n"
            "**Perícias:**\n"
            "`ACA` `IDI` `OFI` `ABR` `INTI` `OCU` "
            "`BRI` `INV` `PER` `CIE` `LAB` `PRO` "
            "`GER` `LID` `SOB` `CON` `MAN` `TEC` "
            "`ESP` `MED` `MIR` `ESQ` `FUR`"
        ),
        inline=False
    )

    embed.set_footer(
        text="BotRPG • Sistema de fichas"
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


# ============================================================
# INICIAR BOT
# ============================================================

bot.run(TOKEN)
