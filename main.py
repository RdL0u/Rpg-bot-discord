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

db = sqlite3.connect(
    "rpg_fichas.db",
    check_same_thread=False
)

cursor = db.cursor()


# ============================================================
# TABELA DE MESAS
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS mesas (
    channel_id INTEGER PRIMARY KEY,
    mestre_id INTEGER
)
""")


# ============================================================
# TABELA DE FICHAS
# ============================================================

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
    furtividade INTEGER NOT NULL DEFAULT 0,

    aleatorio INTEGER NOT NULL DEFAULT 0
)
""")

db.commit()


# ============================================================
# MIGRAÇÃO
# ============================================================

COLUNAS_FICHAS = [
    "channel_id",
    "dono_id",
    "mestre_id",
    "tipo",
    "nome",

    "hp_atual",
    "hp_max",

    "mana_atual",
    "mana_max",

    "xp",

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
    "furtividade",

    "aleatorio"
]


COLUNAS_INTEIRAS = [
    "xp",

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
    "furtividade",

    "aleatorio"
]


def adicionar_coluna_se_nao_existir(nome_coluna):

    cursor.execute("PRAGMA table_info(fichas)")

    colunas_existentes = [
        coluna[1]
        for coluna in cursor.fetchall()
    ]

    if nome_coluna not in colunas_existentes:

        if nome_coluna in COLUNAS_INTEIRAS:

            cursor.execute(
                f"""
                ALTER TABLE fichas
                ADD COLUMN {nome_coluna}
                INTEGER NOT NULL DEFAULT 0
                """
            )

        else:

            cursor.execute(
                f"""
                ALTER TABLE fichas
                ADD COLUMN {nome_coluna}
                TEXT
                """
            )

        db.commit()


for coluna in COLUNAS_FICHAS:
    adicionar_coluna_se_nao_existir(coluna)


# ============================================================
# BOT
# ============================================================

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# ============================================================
# ATRIBUTOS
# ============================================================

ATRIBUTOS = {
    "forca": ("💪", "Força"),
    "destreza": ("🏹", "Destreza"),
    "vigor": ("🛡️", "Vigor"),
    "inteligencia": ("🧠", "Inteligência"),
    "carisma": ("🎭", "Carisma"),
    "raciocinio": ("💡", "Raciocínio")
}


# ============================================================
# PERÍCIAS
# ============================================================

PERICIAS = {
    "academicos": ("📚", "Acadêmicos"),
    "idiomas": ("🗣️", "Idiomas"),
    "oficios": ("🔧", "Ofícios"),
    "armas_brancas": ("⚔️", "Armas Brancas"),
    "intimidacao": ("😠", "Intimidação"),
    "ocultismo": ("🔮", "Ocultismo"),
    "briga": ("👊", "Briga"),
    "investigacao": ("🔎", "Investigação"),
    "persuasao": ("🤝", "Persuasão"),
    "ciencias": ("🧪", "Ciências"),
    "labia": ("💬", "Lábia"),
    "prontidao": ("👁️", "Prontidão"),
    "conhecimentos_gerais": ("🌎", "Conhecimentos Gerais"),
    "lideranca": ("👑", "Liderança"),
    "sobrevivencia": ("🏕️", "Sobrevivência"),
    "conducao": ("🚗", "Condução"),
    "manha": ("🕵️", "Manha"),
    "tecnologia": ("💻", "Tecnologia"),
    "esportes": ("🏃", "Esportes"),
    "medicina": ("⚕️", "Medicina"),
    "mira": ("🎯", "Mira"),
    "esquiva": ("💨", "Esquiva"),
    "furtividade": ("🥷", "Furtividade")
}


ORDEM_PERICIAS = list(PERICIAS.keys())


# ============================================================
# FUNÇÕES DO BANCO
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


def buscar_ficha_por_id(ficha_id):

    colunas = ", ".join(
        ["id"] + COLUNAS_FICHAS
    )

    cursor.execute(
        f"""
        SELECT {colunas}
        FROM fichas
        WHERE id = ?
        """,
        (ficha_id,)
    )

    resultado = cursor.fetchone()

    return transformar_ficha(resultado)


def buscar_ficha_jogador(
    channel_id,
    user_id
):

    colunas = ", ".join(
        ["id"] + COLUNAS_FICHAS
    )

    cursor.execute(
        f"""
        SELECT {colunas}
        FROM fichas
        WHERE channel_id = ?
        AND dono_id = ?
        AND tipo = 'jogador'
        LIMIT 1
        """,
        (
            channel_id,
            user_id
        )
    )

    resultado = cursor.fetchone()

    return transformar_ficha(resultado)


def buscar_npc_por_nome(
    channel_id,
    nome
):

    colunas = ", ".join(
        ["id"] + COLUNAS_FICHAS
    )

    cursor.execute(
        f"""
        SELECT {colunas}
        FROM fichas
        WHERE channel_id = ?
        AND tipo = 'npc'
        AND LOWER(nome) = LOWER(?)
        LIMIT 1
        """,
        (
            channel_id,
            nome
        )
    )

    resultado = cursor.fetchone()

    return transformar_ficha(resultado)


def buscar_todas_fichas(channel_id):

    colunas = ", ".join(
        ["id"] + COLUNAS_FICHAS
    )

    cursor.execute(
        f"""
        SELECT {colunas}
        FROM fichas
        WHERE channel_id = ?
        ORDER BY tipo, nome
        """,
        (channel_id,)
    )

    resultados = cursor.fetchall()

    return [
        transformar_ficha(resultado)
        for resultado in resultados
    ]


# ============================================================
# TRANSFORMAR FICHA
# ============================================================

def transformar_ficha(dados):

    if dados is None:
        return None

    nomes = ["id"] + COLUNAS_FICHAS

    ficha = {}

    for indice, nome in enumerate(nomes):

        ficha[nome] = dados[indice]

    return ficha


# ============================================================
# PERMISSÕES
# ============================================================

def eh_admin(interaction):

    if interaction.guild is None:
        return False

    return interaction.user.guild_permissions.administrator


def eh_mestre(interaction):

    return (
        obter_mestre(
            interaction.channel.id
        )
        == interaction.user.id
    )


# ============================================================
# RC
# ============================================================

def calcular_rc(ficha):

    return (
        ficha["esquiva"]
        + ficha["destreza"]
        + 5
    )


# ============================================================
# STATUS
# ============================================================

def estado_recurso(
    atual,
    maximo
):

    if atual <= 0 or maximo <= 0:
        return "ZERADO"

    percentual = (
        atual / maximo
    ) * 100

    if percentual >= 70:
        return "BOM"

    if percentual >= 30:
        return "BAIXO"

    return "CRÍTICO"


def mostrar_hp(
    atual,
    maximo
):

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
        f"{simbolos[estado]} "
        f"**{atual}/{maximo}** "
        f"— {estado}"
    )


def mostrar_mana(
    atual,
    maximo
):

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
        f"{simbolos[estado]} "
        f"**{atual}/{maximo}** "
        f"— {estado}"
    )


# ============================================================
# PERMISSÃO PARA ALTERAR FICHA
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
            or eh_mestre(interaction)
        )

    if ficha["tipo"] == "npc":

        return eh_mestre(interaction)

    return False


# ============================================================
# RESOLVER FICHA ALVO
# ============================================================

def obter_ficha_alvo(
    interaction,
    jogador=None,
    npc=None
):

    if jogador is not None and npc is not None:

        return None, (
            "❌ Escolha apenas um alvo: "
            "jogador ou NPC."
        )

    if jogador is None and npc is None:

        ficha = buscar_ficha_jogador(
            interaction.channel.id,
            interaction.user.id
        )

        if ficha is None:

            return None, (
                "❌ Você não possui uma ficha "
                "neste canal."
            )

        return ficha, None

    if jogador is not None:

        ficha = buscar_ficha_jogador(
            interaction.channel.id,
            jogador.id
        )

        if ficha is None:

            return None, (
                f"❌ **{jogador.display_name}** "
                f"não possui uma ficha neste canal."
            )

        if (
            ficha["dono_id"]
            != interaction.user.id
            and not eh_mestre(interaction)
            and not eh_admin(interaction)
        ):

            return None, (
                "❌ Você não pode alterar "
                "a ficha desse jogador."
            )

        return ficha, None

    ficha = buscar_npc_por_nome(
        interaction.channel.id,
        npc
    )

    if ficha is None:

        return None, (
            f"❌ NPC **{npc}** não encontrado."
        )

    if (
        not eh_mestre(interaction)
        and not eh_admin(interaction)
    ):

        return None, (
            "❌ Somente o Mestre ou um "
            "administrador pode alterar NPCs."
        )

    return ficha, None


# ============================================================
# PÁGINA 1 — STATUS E ATRIBUTOS
# ============================================================

def criar_pagina_status(
    ficha,
    jogador=None
):

    if ficha["tipo"] == "npc":

        identificacao = "👹 NPC"

    else:

        if jogador:

            identificacao = (
                f"👤 Jogador: {jogador.mention}"
            )

        else:

            identificacao = "👤 Jogador"

    embed = discord.Embed(
        title=f"📜 {ficha['nome'].upper()}",
        color=discord.Color.dark_red()
    )

    embed.description = (
        f"{identificacao}\n\n"
        f"❤️ HP: {mostrar_hp(ficha['hp_atual'], ficha['hp_max'])}\n"
        f"🔵 Mana: {mostrar_mana(ficha['mana_atual'], ficha['mana_max'])}\n"
        f"✨ XP: **{ficha['xp']}**\n"
        f"⚡ RC: **{calcular_rc(ficha)}**"
    )

    embed.add_field(
        name="⚔️ ATRIBUTOS",
        value=" ",
        inline=False
    )

    # ========================================================
    # ATRIBUTOS EM 2 COLUNAS NATIVAS DO DISCORD
    # ========================================================

    for chave in [
        "forca",
        "destreza",
        "vigor",
        "inteligencia",
        "carisma",
        "raciocinio"
    ]:

        emoji, nome = ATRIBUTOS[chave]

        embed.add_field(
            name=f"{emoji} {nome}",
            value=f"**{ficha[chave]}**",
            inline=True
        )

    embed.set_footer(
        text="Página 1/2 • Status e Atributos"
    )

    return embed


# ============================================================
# PÁGINA 2 — PERÍCIAS
# ============================================================

def criar_pagina_pericias(ficha):

    embed = discord.Embed(
        title=f"📚 PERÍCIAS — {ficha['nome']}",
        color=discord.Color.dark_red()
    )

    embed.description = (
        "Perícias do personagem:"
    )

    # ========================================================
    # UMA PERÍCIA POR LINHA
    # ========================================================

    for chave in ORDEM_PERICIAS:

        emoji, nome = PERICIAS[chave]

        embed.add_field(
            name=f"{emoji} {nome}",
            value=f"**{ficha[chave]}**",
            inline=False
        )

    embed.set_footer(
        text="Página 2/2 • Perícias"
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
            timeout=180
        )

        self.ficha = ficha
        self.jogador = jogador

    @discord.ui.button(
        label="Status",
        emoji="❤️",
        style=discord.ButtonStyle.primary
    )
    async def status(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.edit_message(
            embed=criar_pagina_status(
                self.ficha,
                self.jogador
            ),
            view=self
        )

    @discord.ui.button(
        label="Perícias",
        emoji="📚",
        style=discord.ButtonStyle.primary
    )
    async def pericias(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.edit_message(
            embed=criar_pagina_pericias(
                self.ficha
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
        f"agora é o Mestre deste canal."
    )


# ============================================================
# PASSAR MESTRE
# ============================================================

@bot.tree.command(
    name="passarmestre",
    description="Passa o cargo de Mestre para outro jogador."
)
@app_commands.describe(
    jogador="Novo Mestre"
)
async def passarmestre(
    interaction: discord.Interaction,
    jogador: discord.Member
):

    if (
        not eh_mestre(interaction)
        and not eh_admin(interaction)
    ):

        await interaction.response.send_message(
            "❌ Somente o Mestre atual ou "
            "um administrador pode fazer isso.",
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
        f"👑 Novo Mestre: {jogador.mention}"
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
            "👑 Este canal ainda não possui Mestre."
        )

        return

    membro = interaction.guild.get_member(
        mestre_id
    )

    if membro:

        await interaction.response.send_message(
            f"👑 Mestre: **{membro.display_name}**"
        )

    else:

        await interaction.response.send_message(
            f"👑 Mestre: <@{mestre_id}>"
        )


# ============================================================
# CRIAR FICHA
# ============================================================

@bot.tree.command(
    name="criarficha",
    description="Cria sua ficha."
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

    colunas = [
        "channel_id",
        "dono_id",
        "mestre_id",
        "tipo",
        "nome",
        "hp_atual",
        "hp_max",
        "mana_atual",
        "mana_max",
        "xp"
    ] + list(ATRIBUTOS.keys()) + ORDEM_PERICIAS + [
        "aleatorio"
    ]

    valores = [
        interaction.channel.id,
        interaction.user.id,
        None,
        "jogador",
        nome,
        hp,
        hp,
        mana,
        mana,
        0
    ]

    valores += [0] * len(ATRIBUTOS)
    valores += [0] * len(PERICIAS)
    valores += [0]

    placeholders = ", ".join(
        ["?"] * len(valores)
    )

    cursor.execute(
        f"""
        INSERT INTO fichas (
            {", ".join(colunas)}
        )
        VALUES (
            {placeholders}
        )
        """,
        valores
    )

    db.commit()

    await interaction.response.send_message(
        f"📜 Ficha de **{nome}** criada!\n\n"
        f"❤️ HP: **{hp}/{hp}**\n"
        f"🔵 Mana: **{mana}/{mana}**\n"
        f"✨ XP: **0**\n"
        f"⚡ RC: **5**"
    )


# ============================================================
# MOSTRAR FICHA
# ============================================================

@bot.tree.command(
    name="ficha",
    description="Mostra sua ficha."
)
async def ficha(
    interaction: discord.Interaction
):

    f = buscar_ficha_jogador(
        interaction.channel.id,
        interaction.user.id
    )

    if f is None:

        await interaction.response.send_message(
            "❌ Você não possui uma ficha.",
            ephemeral=True
        )

        return

    await interaction.response.send_message(
        embed=criar_pagina_status(
            f,
            interaction.user
        ),
        view=FichaView(
            f,
            interaction.user
        ),
        ephemeral=True
    )


# ============================================================
# VER FICHA
# ============================================================

@bot.tree.command(
    name="verficha",
    description="Visualiza a ficha de um jogador."
)
@app_commands.describe(
    jogador="Jogador"
)
async def verficha(
    interaction: discord.Interaction,
    jogador: discord.Member
):

    f = buscar_ficha_jogador(
        interaction.channel.id,
        jogador.id
    )

    if f is None:

        await interaction.response.send_message(
            "❌ Esse jogador não possui uma ficha.",
            ephemeral=True
        )

        return

    await interaction.response.send_message(
        embed=criar_pagina_status(
            f,
            jogador
        ),
        view=FichaView(
            f,
            jogador
        )
    )


# ============================================================
# ALTERAR ATRIBUTO
# ============================================================

@bot.tree.command(
    name="atributo",
    description="Altera um atributo da ficha."
)
@app_commands.describe(
    atributo="Atributo",
    valor="Novo valor",
    jogador="Opcional: jogador alvo",
    npc="Opcional: nome exato do NPC"
)
@app_commands.choices(
    atributo=[
        app_commands.Choice(
            name="Força",
            value="forca"
        ),
        app_commands.Choice(
            name="Destreza",
            value="destreza"
        ),
        app_commands.Choice(
            name="Vigor",
            value="vigor"
        ),
        app_commands.Choice(
            name="Inteligência",
            value="inteligencia"
        ),
        app_commands.Choice(
            name="Carisma",
            value="carisma"
        ),
        app_commands.Choice(
            name="Raciocínio",
            value="raciocinio"
        )
    ]
)
async def atributo(
    interaction: discord.Interaction,
    atributo: app_commands.Choice[str],
    valor: int,
    jogador: discord.Member = None,
    npc: str = None
):

    if valor < 0:

        await interaction.response.send_message(
            "❌ O valor não pode ser negativo.",
            ephemeral=True
        )

        return

    f, erro = obter_ficha_alvo(
        interaction,
        jogador,
        npc
    )

    if erro:

        await interaction.response.send_message(
            erro,
            ephemeral=True
        )

        return

    if not pode_alterar_ficha(
        interaction,
        f
    ):

        await interaction.response.send_message(
            "❌ Você não pode alterar essa ficha.",
            ephemeral=True
        )

        return

    cursor.execute(
        f"""
        UPDATE fichas
        SET {atributo.value} = ?
        WHERE id = ?
        """,
        (
            valor,
            f["id"]
        )
    )

    db.commit()

    nome = ATRIBUTOS[
        atributo.value
    ][1]

    await interaction.response.send_message(
        f"⚔️ **{f['nome']}**\n"
        f"{nome}: **{valor}**"
    )


# ============================================================
# ALTERAR PERÍCIA
# ============================================================

@bot.tree.command(
    name="pericia",
    description="Altera uma perícia da ficha."
)
@app_commands.describe(
    pericia="Perícia",
    valor="Novo valor",
    jogador="Opcional: jogador alvo",
    npc="Opcional: nome exato do NPC"
)
@app_commands.choices(
    pericia=[
        app_commands.Choice(name="Acadêmicos", value="academicos"),
        app_commands.Choice(name="Idiomas", value="idiomas"),
        app_commands.Choice(name="Ofícios", value="oficios"),
        app_commands.Choice(name="Armas Brancas", value="armas_brancas"),
        app_commands.Choice(name="Intimidação", value="intimidacao"),
        app_commands.Choice(name="Ocultismo", value="ocultismo"),
        app_commands.Choice(name="Briga", value="briga"),
        app_commands.Choice(name="Investigação", value="investigacao"),
        app_commands.Choice(name="Persuasão", value="persuasao"),
        app_commands.Choice(name="Ciências", value="ciencias"),
        app_commands.Choice(name="Lábia", value="labia"),
        app_commands.Choice(name="Prontidão", value="prontidao"),
        app_commands.Choice(name="Conhecimentos Gerais", value="conhecimentos_gerais"),
        app_commands.Choice(name="Liderança", value="lideranca"),
        app_commands.Choice(name="Sobrevivência", value="sobrevivencia"),
        app_commands.Choice(name="Condução", value="conducao"),
        app_commands.Choice(name="Manha", value="manha"),
        app_commands.Choice(name="Tecnologia", value="tecnologia"),
        app_commands.Choice(name="Esportes", value="esportes"),
        app_commands.Choice(name="Medicina", value="medicina"),
        app_commands.Choice(name="Mira", value="mira"),
        app_commands.Choice(name="Esquiva", value="esquiva"),
        app_commands.Choice(name="Furtividade", value="furtividade")
    ]
)
async def pericia(
    interaction: discord.Interaction,
    pericia: app_commands.Choice[str],
    valor: int,
    jogador: discord.Member = None,
    npc: str = None
):

    if valor < 0:

        await interaction.response.send_message(
            "❌ O valor não pode ser negativo.",
            ephemeral=True
        )

        return

    f, erro = obter_ficha_alvo(
        interaction,
        jogador,
        npc
    )

    if erro:

        await interaction.response.send_message(
            erro,
            ephemeral=True
        )

        return

    if not pode_alterar_ficha(
        interaction,
        f
    ):

        await interaction.response.send_message(
            "❌ Você não pode alterar essa ficha.",
            ephemeral=True
        )

        return

    # ========================================================
    # CORREÇÃO IMPORTANTE
    #
    # O nome da coluna vem diretamente da Choice.
    # Não usamos mais posição da tabela.
    # ========================================================

    coluna = pericia.value

    if coluna not in PERICIAS:

        await interaction.response.send_message(
            "❌ Perícia inválida.",
            ephemeral=True
        )

        return

    cursor.execute(
        f"""
        UPDATE fichas
        SET {coluna} = ?
        WHERE id = ?
        """,
        (
            valor,
            f["id"]
        )
    )

    db.commit()

    nome = PERICIAS[
        coluna
    ][1]

    await interaction.response.send_message(
        f"📚 **{f['nome']}**\n"
        f"{nome}: **{valor}**"
    )


# ============================================================
# ALTERAR HP E MANA MÁXIMOS
# ============================================================

@bot.tree.command(
    name="alterarficha",
    description="Altera HP e Mana máximos de uma ficha."
)
@app_commands.describe(
    hp="Novo HP máximo",
    mana="Nova Mana máxima",
    jogador="Opcional: jogador alvo",
    npc="Opcional: nome exato do NPC"
)
async def alterarficha(
    interaction: discord.Interaction,
    hp: int,
    mana: int,
    jogador: discord.Member = None,
    npc: str = None
):

    if hp <= 0 or mana < 0:

        await interaction.response.send_message(
            "❌ Valores inválidos.",
            ephemeral=True
        )

        return

    f, erro = obter_ficha_alvo(
        interaction,
        jogador,
        npc
    )

    if erro:

        await interaction.response.send_message(
            erro,
            ephemeral=True
        )

        return

    if not pode_alterar_ficha(
        interaction,
        f
    ):

        await interaction.response.send_message(
            "❌ Você não pode alterar essa ficha.",
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
        f"⚙️ **{f['nome']}** atualizada!\n\n"
        f"❤️ HP: **{hp}/{hp}**\n"
        f"🔵 Mana: **{mana}/{mana}**"
    )


# ============================================================
# APAGAR PRÓPRIA FICHA
# ============================================================

@bot.tree.command(
    name="apagarficha",
    description="Apaga sua própria ficha."
)
async def apagarficha(
    interaction: discord.Interaction
):

    f = buscar_ficha_jogador(
        interaction.channel.id,
        interaction.user.id
    )

    if f is None:

        await interaction.response.send_message(
            "❌ Você não possui uma ficha.",
            ephemeral=True
        )

        return

    cursor.execute(
        """
        DELETE FROM fichas
        WHERE id = ?
        """,
        (f["id"],)
    )

    db.commit()

    await interaction.response.send_message(
        f"🗑️ A ficha **{f['nome']}** foi apagada."
    )


# ============================================================
# DANO
# ============================================================

@bot.tree.command(
    name="dano",
    description="Aplica dano a um jogador ou NPC."
)
@app_commands.describe(
    valor="Quantidade de dano",
    jogador="Jogador que receberá o dano",
    npc="Nome exato do NPC"
)
async def dano(
    interaction: discord.Interaction,
    valor: int,
    jogador: discord.Member = None,
    npc: str = None
):

    if valor <= 0:

        await interaction.response.send_message(
            "❌ O dano precisa ser maior que 0.",
            ephemeral=True
        )

        return

    f, erro = obter_ficha_alvo(
        interaction,
        jogador,
        npc
    )

    if erro:

        await interaction.response.send_message(
            erro,
            ephemeral=True
        )

        return

    # Dano pode ser aplicado pelo Mestre,
    # administrador ou pelo próprio jogador.
    if (
        f["tipo"] == "npc"
        and not eh_mestre(interaction)
        and not eh_admin(interaction)
    ):

        await interaction.response.send_message(
            "❌ Somente o Mestre pode aplicar "
            "dano a NPCs.",
            ephemeral=True
        )

        return

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

    await interaction.response.send_message(
        f"💥 **{f['nome']}** recebeu "
        f"**{valor} de dano**!\n\n"
        f"❤️ HP: **{novo_hp}/{f['hp_max']}**"
    )


# ============================================================
# CURA
# ============================================================

@bot.tree.command(
    name="cura",
    description="Cura um jogador ou NPC."
)
@app_commands.describe(
    valor="Quantidade de cura",
    jogador="Jogador que será curado",
    npc="Nome exato do NPC"
)
async def cura(
    interaction: discord.Interaction,
    valor: int,
    jogador: discord.Member = None,
    npc: str = None
):

    if valor <= 0:

        await interaction.response.send_message(
            "❌ A cura precisa ser maior que 0.",
            ephemeral=True
        )

        return

    f, erro = obter_ficha_alvo(
        interaction,
        jogador,
        npc
    )

    if erro:

        await interaction.response.send_message(
            erro,
            ephemeral=True
        )

        return

    # ========================================================
    # JOGADORES PODEM CURAR OUTROS JOGADORES E NPCs
    # ========================================================

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
        f"💚 **{f['nome']}** recuperou "
        f"**{recuperado} de HP**!\n\n"
        f"❤️ HP: **{novo_hp}/{f['hp_max']}**"
    )


# ============================================================
# GASTAR MANA
# ============================================================

@bot.tree.command(
    name="gastarmana",
    description="Gasta Mana da sua ficha."
)
@app_commands.describe(
    valor="Quantidade de Mana"
)
async def gastarmana(
    interaction: discord.Interaction,
    valor: int
):

    f = buscar_ficha_jogador(
        interaction.channel.id,
        interaction.user.id
    )

    if f is None:

        await interaction.response.send_message(
            "❌ Você não possui uma ficha.",
            ephemeral=True
        )

        return

    if valor <= 0:

        await interaction.response.send_message(
            "❌ O valor precisa ser maior que 0.",
            ephemeral=True
        )

        return

    if valor > f["mana_atual"]:

        await interaction.response.send_message(
            "❌ Mana insuficiente.",
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
        f"🔵 Mana: **{nova_mana}/{f['mana_max']}**"
    )


# ============================================================
# RECUPERAR MANA
# ============================================================

@bot.tree.command(
    name="recuperarmana",
    description="Recupera Mana de um jogador ou NPC."
)
@app_commands.describe(
    valor="Quantidade de Mana",
    jogador="Jogador que recuperará Mana",
    npc="Nome exato do NPC"
)
async def recuperarmana(
    interaction: discord.Interaction,
    valor: int,
    jogador: discord.Member = None,
    npc: str = None
):

    if valor <= 0:

        await interaction.response.send_message(
            "❌ O valor precisa ser maior que 0.",
            ephemeral=True
        )

        return

    f, erro = obter_ficha_alvo(
        interaction,
        jogador,
        npc
    )

    if erro:

        await interaction.response.send_message(
            erro,
            ephemeral=True
        )

        return

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
        f"💧 **{f['nome']}** recuperou "
        f"**{recuperado} de Mana**!\n\n"
        f"🔵 Mana: **{nova_mana}/{f['mana_max']}**"
    )


# ============================================================
# XP
# ============================================================

@bot.tree.command(
    name="addxp",
    description="Adiciona XP a um jogador."
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

    if valor <= 0:

        await interaction.response.send_message(
            "❌ O XP precisa ser maior que 0.",
            ephemeral=True
        )

        return

    f = buscar_ficha_jogador(
        interaction.channel.id,
        jogador.id
    )

    if f is None:

        await interaction.response.send_message(
            "❌ Jogador não possui ficha.",
            ephemeral=True
        )

        return

    if (
        f["dono_id"] != interaction.user.id
        and not eh_mestre(interaction)
        and not eh_admin(interaction)
    ):

        await interaction.response.send_message(
            "❌ Você não pode alterar "
            "o XP dessa ficha.",
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

    f_atualizada = buscar_ficha_por_id(
        f["id"]
    )

    await interaction.response.send_message(
        f"✨ **{f['nome']}** recebeu "
        f"**{valor} XP**!\n"
        f"✨ XP atual: **{f_atualizada['xp']}**"
    )


# ============================================================
# CRIAR NPC
# ============================================================

@bot.tree.command(
    name="criarnpc",
    description="Cria um NPC."
)
@app_commands.describe(
    aleatorio="NPC aleatório ou personalizado",
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
            "❌ Somente o Mestre pode criar NPCs.",
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

        atributos = {
            chave: random.randint(0, 5)
            for chave in ATRIBUTOS
        }

        pericias = {
            chave: random.randint(0, 5)
            for chave in PERICIAS
        }

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

        if hp <= 0 or mana < 0:

            await interaction.response.send_message(
                "❌ Valores inválidos.",
                ephemeral=True
            )

            return

        atributos = {
            chave: 0
            for chave in ATRIBUTOS
        }

        pericias = {
            chave: 0
            for chave in PERICIAS
        }

        aleatorio_valor = 0

    nome = nome[:50]

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

    colunas = [
        "channel_id",
        "dono_id",
        "mestre_id",
        "tipo",
        "nome",
        "hp_atual",
        "hp_max",
        "mana_atual",
        "mana_max",
        "xp"
    ] + list(ATRIBUTOS.keys()) + ORDEM_PERICIAS + [
        "aleatorio"
    ]

    valores = [
        interaction.channel.id,
        None,
        mestre_id,
        "npc",
        nome,
        hp,
        hp,
        mana,
        mana,
        0
    ]

    valores += [
        atributos[chave]
        for chave in ATRIBUTOS
    ]

    valores += [
        pericias[chave]
        for chave in ORDEM_PERICIAS
    ]

    valores += [
        aleatorio_valor
    ]

    placeholders = ", ".join(
        ["?"] * len(valores)
    )

    cursor.execute(
        f"""
        INSERT INTO fichas (
            {", ".join(colunas)}
        )
        VALUES (
            {placeholders}
        )
        """,
        valores
    )

    db.commit()

    rc = (
        pericias["esquiva"]
        + atributos["destreza"]
        + 5
    )

    await interaction.response.send_message(
        f"👹 NPC **{nome}** criado!\n\n"
        f"❤️ HP: **{hp}/{hp}**\n"
        f"🔵 Mana: **{mana}/{mana}**\n"
        f"⚡ RC: **{rc}**"
    )


# ============================================================
# LISTAR NPCs
# ============================================================

@bot.tree.command(
    name="npcs",
    description="Mostra os NPCs da mesa."
)
async def npcs(
    interaction: discord.Interaction
):

    if (
        not eh_mestre(interaction)
        and not eh_admin(interaction)
    ):

        await interaction.response.send_message(
            "❌ Somente o Mestre pode visualizar NPCs.",
            ephemeral=True
        )

        return

    fichas = buscar_todas_fichas(
        interaction.channel.id
    )

    fichas_npc = [
        f
        for f in fichas
        if f["tipo"] == "npc"
    ]

    if not fichas_npc:

        await interaction.response.send_message(
            "👹 Não existem NPCs neste canal.",
            ephemeral=True
        )

        return

    await interaction.response.defer(
        ephemeral=True
    )

    for f in fichas_npc:

        await interaction.followup.send(
            embed=criar_pagina_status(f),
            view=FichaView(f)
        )


# ============================================================
# APAGAR NPC
# ============================================================

@bot.tree.command(
    name="apagarnpc",
    description="Apaga um NPC."
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
            "❌ Somente o Mestre pode apagar NPCs.",
            ephemeral=True
        )

        return

    f = buscar_npc_por_nome(
        interaction.channel.id,
        nome
    )

    if f is None:

        await interaction.response.send_message(
            "❌ NPC não encontrado.",
            ephemeral=True
        )

        return

    cursor.execute(
        """
        DELETE FROM fichas
        WHERE id = ?
        """,
        (f["id"],)
    )

    db.commit()

    await interaction.response.send_message(
        f"🗑️ NPC **{f['nome']}** apagado."
    )


# ============================================================
# HELP
# ============================================================

@bot.tree.command(
    name="help",
    description="Mostra os comandos do bot."
)
async def help(
    interaction: discord.Interaction
):

    embed = discord.Embed(
        title="📖 BotRPG",
        description="Comandos disponíveis:",
        color=discord.Color.dark_red()
    )

    embed.add_field(
        name="👤 Jogador",
        value=(
            "`/criarficha` — Criar ficha\n"
            "`/ficha` — Ver sua ficha\n"
            "`/verficha` — Ver ficha de jogador\n"
            "`/atributo` — Alterar atributo\n"
            "`/pericia` — Alterar perícia\n"
            "`/alterarficha` — Alterar HP/Mana\n"
            "`/apagarficha` — Apagar sua ficha\n"
            "`/dano` — Aplicar dano\n"
            "`/cura` — Curar jogador ou NPC\n"
            "`/gastarmana` — Gastar Mana\n"
            "`/recuperarmana` — Recuperar Mana\n"
            "`/addxp` — Adicionar XP"
        ),
        inline=False
    )

    embed.add_field(
        name="👑 Mestre",
        value=(
            "`/criarnpc` — Criar NPC\n"
            "`/npcs` — Ver NPCs\n"
            "`/apagarnpc` — Apagar NPC\n"
            "`/definirmestre` — Definir Mestre\n"
            "`/passarmestre` — Passar Mestre\n"
            "`/mestre` — Ver Mestre"
        ),
        inline=False
    )

    embed.add_field(
        name="🛠️ Alteração de fichas",
        value=(
            "Jogadores podem alterar sua própria ficha "
            "normalmente.\n\n"
            "O Mestre pode informar um jogador ou o "
            "nome de um NPC nos comandos de alteração."
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
