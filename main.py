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
db.row_factory = sqlite3.Row
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
# MIGRAÇÃO DO BANCO
# ============================================================

COLUNAS_NOVAS = [
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


def adicionar_coluna_se_nao_existir(nome_coluna):

    cursor.execute("PRAGMA table_info(fichas)")

    colunas = [
        coluna["name"]
        for coluna in cursor.fetchall()
    ]

    if nome_coluna not in colunas:

        cursor.execute(
            f"""
            ALTER TABLE fichas
            ADD COLUMN {nome_coluna}
            INTEGER NOT NULL DEFAULT 0
            """
        )

        db.commit()


for coluna in COLUNAS_NOVAS:
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
    "forca": ("💪", "For"),
    "destreza": ("🏹", "Des"),
    "vigor": ("🛡️", "Vig"),
    "inteligencia": ("🧠", "Int"),
    "carisma": ("🎭", "Car"),
    "raciocinio": ("💡", "Rac")
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
    "conhecimentos_gerais": ("🌎", "Conhec. Gerais"),
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
        return resultado["mestre_id"]

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


# ============================================================
# BUSCA DE FICHAS
# ============================================================

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


def buscar_ficha_por_nome(
    channel_id,
    nome
):

    cursor.execute("""
        SELECT *
        FROM fichas
        WHERE channel_id = ?
        AND LOWER(nome) = LOWER(?)
        LIMIT 1
    """, (
        channel_id,
        nome.strip()
    ))

    return cursor.fetchone()


def transformar_ficha(dados):

    if dados is None:
        return None

    return dict(dados)


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

        return (
            ficha["mestre_id"]
            == interaction.user.id
            or eh_mestre(interaction)
        )

    return False


# ============================================================
# REFLEXO DE COMBATE
# ============================================================

def calcular_rc(ficha):

    return (
        int(ficha["esquiva"])
        + int(ficha["destreza"])
        + 5
    )


# ============================================================
# ESTADO DE RECURSOS
# ============================================================

def estado_recurso(
    atual,
    maximo
):

    if maximo <= 0:
        return "ZERADO"

    if atual <= 0:
        return "ZERADO"

    percentual = (
        atual / maximo
    ) * 100

    if percentual >= 70:
        return "BOM"

    if percentual >= 30:
        return "BAIXO"

    return "CRÍTICO"


def emoji_estado(
    atual,
    maximo,
    tipo
):

    estado = estado_recurso(
        atual,
        maximo
    )

    if tipo == "hp":

        emojis = {
            "BOM": "🟢",
            "BAIXO": "🟡",
            "CRÍTICO": "🔴",
            "ZERADO": "⚫"
        }

    else:

        emojis = {
            "BOM": "🔵",
            "BAIXO": "🟡",
            "CRÍTICO": "🔴",
            "ZERADO": "⚫"
        }

    return emojis.get(
        estado,
        "⚪"
    )


# ============================================================
# ALINHAMENTO AUTOMÁTICO
# ============================================================

def montar_duas_colunas(
    esquerda,
    direita,
    largura=28
):

    resultado = []

    total = max(
        len(esquerda),
        len(direita)
    )

    for i in range(total):

        item_esquerda = (
            esquerda[i]
            if i < len(esquerda)
            else ""
        )

        item_direita = (
            direita[i]
            if i < len(direita)
            else ""
        )

        resultado.append(
            item_esquerda.ljust(
                largura
            )
            + item_direita
        )

    return "\n".join(resultado)


# ============================================================
# STATUS EM 2 COLUNAS
# ============================================================

def texto_status(f):

    hp_emoji = emoji_estado(
        f["hp_atual"],
        f["hp_max"],
        "hp"
    )

    mana_emoji = emoji_estado(
        f["mana_atual"],
        f["mana_max"],
        "mana"
    )

    esquerda = [
        f"{hp_emoji} HP   : {f['hp_atual']}/{f['hp_max']}",
        f"✨ XP   : {f['xp']}"
    ]

    direita = [
        f"{mana_emoji} Mana : {f['mana_atual']}/{f['mana_max']}",
        f"⚡ RC   : {calcular_rc(f)}"
    ]

    return montar_duas_colunas(
        esquerda,
        direita,
        28
    )


# ============================================================
# ATRIBUTOS EM 2 COLUNAS
# ============================================================

def texto_atributos(f):

    itens = list(
        ATRIBUTOS.items()
    )

    esquerda = []
    direita = []

    for chave, dados in itens[:3]:

        emoji, nome = dados

        esquerda.append(
            f"{emoji} {nome:<3}: {f[chave]}"
        )

    for chave, dados in itens[3:]:

        emoji, nome = dados

        direita.append(
            f"{emoji} {nome:<3}: {f[chave]}"
        )

    return montar_duas_colunas(
        esquerda,
        direita,
        28
    )


# ============================================================
# PERÍCIAS EM 2 COLUNAS
# ============================================================

def texto_pericias(f):

    itens = list(
        PERICIAS.items()
    )

    esquerda = []
    direita = []

    metade = (
        len(itens) + 1
    ) // 2

    grupo_esquerda = itens[:metade]
    grupo_direita = itens[metade:]

    for chave, dados in grupo_esquerda:

        emoji, nome = dados

        esquerda.append(
            f"{emoji} {nome:<17}: {f[chave]}"
        )

    for chave, dados in grupo_direita:

        emoji, nome = dados

        direita.append(
            f"{emoji} {nome:<17}: {f[chave]}"
        )

    return montar_duas_colunas(
        esquerda,
        direita,
        30
    )


# ============================================================
# PÁGINA STATUS
# ============================================================

def criar_pagina_status(
    f,
    jogador=None
):

    embed = discord.Embed(
        title=f"📜 FICHA — {f['nome']}",
        color=discord.Color.dark_red()
    )

    if f["tipo"] == "npc":

        identificacao = (
            "👹 Tipo: NPC"
        )

    else:

        if jogador:

            identificacao = (
                f"👤 Jogador: {jogador.mention}"
            )

        else:

            identificacao = "👤 Tipo: Jogador"

    conteudo = (
        f"{identificacao}\n\n"
        f"```text\n"
        f"╔════════════════════════════════════════════════════╗\n"
        f"║                    STATUS                         ║\n"
        f"╠════════════════════════════════════════════════════╣\n"
        f"{texto_status(f)}\n"
        f"╚════════════════════════════════════════════════════╝\n"
        f"```\n"
        f"```text\n"
        f"╔════════════════════════════════════════════════════╗\n"
        f"║                  ATRIBUTOS                        ║\n"
        f"╠════════════════════════════════════════════════════╣\n"
        f"{texto_atributos(f)}\n"
        f"╚════════════════════════════════════════════════════╝\n"
        f"```"
    )

    embed.description = conteudo

    embed.set_footer(
        text="Página 1/2 • Status e Atributos"
    )

    return embed


# ============================================================
# PÁGINA DE PERÍCIAS
# ============================================================

def criar_pagina_pericias(f):

    embed = discord.Embed(
        title=f"📚 PERÍCIAS — {f['nome']}",
        color=discord.Color.dark_red()
    )

    conteudo = (
        "```text\n"
        "╔════════════════════════════════════════════════════════════╗\n"
        "║                         PERÍCIAS                          ║\n"
        "╠════════════════════════════════════════════════════════════╣\n"
        f"{texto_pericias(f)}\n"
        "╚════════════════════════════════════════════════════════════╝\n"
        "```"
    )

    embed.description = conteudo

    embed.set_footer(
        text="Página 2/2 • Perícias"
    )

    return embed


# ============================================================
# PAGINAÇÃO
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

        self.ficha = ficha
        self.jogador = jogador

    @discord.ui.button(
        label="◀ Status",
        style=discord.ButtonStyle.primary
    )
    async def status(
        self,
        interaction,
        button
    ):

        await interaction.response.edit_message(
            embed=criar_pagina_status(
                self.ficha,
                self.jogador
            ),
            view=self
        )

    @discord.ui.button(
        label="Perícias ▶",
        style=discord.ButtonStyle.primary
    )
    async def pericias(
        self,
        interaction,
        button
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
    interaction,
    jogador: discord.Member
):

    if not eh_admin(interaction):

        await interaction.response.send_message(
            "❌ Somente administradores podem definir o Mestre.",
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
        f"👑 **{jogador.display_name}** agora é o Mestre deste canal!"
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
    interaction,
    jogador: discord.Member
):

    if (
        not eh_mestre(interaction)
        and not eh_admin(interaction)
    ):

        await interaction.response.send_message(
            "❌ Somente o Mestre atual ou um administrador pode fazer isso.",
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
# VER MESTRE
# ============================================================

@bot.tree.command(
    name="mestre",
    description="Mostra o Mestre deste canal."
)
async def mestre(interaction):

    mestre_id = obter_mestre(
        interaction.channel.id
    )

    if mestre_id is None:

        await interaction.response.send_message(
            "👑 Este canal ainda não possui um Mestre."
        )

        return

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
    hp="HP inicial",
    mana="Mana inicial"
)
async def criarficha(
    interaction,
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
            "⚠️ Você já possui uma ficha neste canal.",
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
            xp
        )
        VALUES (?, ?, NULL, 'jogador', ?, ?, ?, ?, ?, 0)
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

    await interaction.response.send_message(
        f"📜 Ficha de **{nome}** criada!\n\n"
        f"❤️ HP: **{hp}/{hp}**\n"
        f"🔵 Mana: **{mana}/{mana}**\n"
        f"✨ XP: **0**\n"
        f"⚡ RC: **5**"
    )


# ============================================================
# VER PRÓPRIA FICHA
# ============================================================

@bot.tree.command(
    name="ficha",
    description="Mostra sua ficha."
)
async def ficha(interaction):

    dados = buscar_ficha_jogador(
        interaction.channel.id,
        interaction.user.id
    )

    if dados is None:

        await interaction.response.send_message(
            "❌ Você não possui uma ficha neste canal.",
            ephemeral=True
        )

        return

    f = transformar_ficha(dados)

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
# VER FICHA DE JOGADOR
# ============================================================

@bot.tree.command(
    name="verficha",
    description="Visualiza a ficha de outro jogador."
)
@app_commands.describe(
    jogador="Jogador"
)
async def verficha(
    interaction,
    jogador: discord.Member
):

    dados = buscar_ficha_jogador(
        interaction.channel.id,
        jogador.id
    )

    if dados is None:

        await interaction.response.send_message(
            "❌ Esse jogador não possui uma ficha.",
            ephemeral=True
        )

        return

    f = transformar_ficha(dados)

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
# ATRIBUTO
#
# Sem personagem = altera a própria ficha.
#
# Mestre/Admin:
# /atributo atributo valor personagem
#
# O personagem pode ser jogador ou NPC.
# ============================================================

atributo_choices = [
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


@bot.tree.command(
    name="atributo",
    description="Altera um atributo."
)
@app_commands.describe(
    atributo="Atributo",
    valor="Novo valor",
    personagem="Nome da ficha. Deixe vazio para usar sua ficha."
)
@app_commands.choices(
    atributo=atributo_choices
)
async def atributo(
    interaction,
    atributo: app_commands.Choice[str],
    valor: int,
    personagem: str = None
):

    if valor < 0:

        await interaction.response.send_message(
            "❌ O valor não pode ser negativo.",
            ephemeral=True
        )

        return

    if personagem:

        if (
            not eh_mestre(interaction)
            and not eh_admin(interaction)
        ):

            await interaction.response.send_message(
                "❌ Somente o Mestre ou administrador pode escolher outra ficha.",
                ephemeral=True
            )

            return

        dados = buscar_ficha_por_nome(
            interaction.channel.id,
            personagem
        )

    else:

        dados = buscar_ficha_jogador(
            interaction.channel.id,
            interaction.user.id
        )

    if dados is None:

        await interaction.response.send_message(
            "❌ Ficha não encontrada.",
            ephemeral=True
        )

        return

    f = transformar_ficha(dados)

    if not pode_alterar_ficha(
        interaction,
        f
    ):

        await interaction.response.send_message(
            "❌ Você não pode alterar essa ficha.",
            ephemeral=True
        )

        return

    coluna = atributo.value

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

    nome_atributo = ATRIBUTOS[
        coluna
    ][1]

    await interaction.response.send_message(
        f"⚔️ **{f['nome']}** — {nome_atributo} alterado para **{valor}**."
    )


# ============================================================
# PERÍCIA
#
# Sem personagem = própria ficha.
#
# Mestre/Admin:
# /pericia pericia valor personagem
#
# Isso permite alterar NPC ou jogador.
# ============================================================

pericia_choices = [
    app_commands.Choice(
        name=nome,
        value=chave
    )
    for chave, (
        emoji,
        nome
    ) in PERICIAS.items()
]


@bot.tree.command(
    name="pericia",
    description="Altera uma perícia."
)
@app_commands.describe(
    pericia="Perícia",
    valor="Novo valor",
    personagem="Nome da ficha. Deixe vazio para usar sua ficha."
)
@app_commands.choices(
    pericia=pericia_choices
)
async def pericia(
    interaction,
    pericia: app_commands.Choice[str],
    valor: int,
    personagem: str = None
):

    if valor < 0:

        await interaction.response.send_message(
            "❌ O valor não pode ser negativo.",
            ephemeral=True
        )

        return

    if personagem:

        if (
            not eh_mestre(interaction)
            and not eh_admin(interaction)
        ):

            await interaction.response.send_message(
                "❌ Somente o Mestre ou administrador pode escolher outra ficha.",
                ephemeral=True
            )

            return

        dados = buscar_ficha_por_nome(
            interaction.channel.id,
            personagem
        )

    else:

        dados = buscar_ficha_jogador(
            interaction.channel.id,
            interaction.user.id
        )

    if dados is None:

        await interaction.response.send_message(
            "❌ Ficha não encontrada.",
            ephemeral=True
        )

        return

    f = transformar_ficha(dados)

    if not pode_alterar_ficha(
        interaction,
        f
    ):

        await interaction.response.send_message(
            "❌ Você não pode alterar essa ficha.",
            ephemeral=True
        )

        return

    coluna = pericia.value

    # ========================================================
    # CORREÇÃO DO ERRO DAS PERÍCIAS
    #
    # O comando altera EXATAMENTE a coluna escolhida.
    # Não existe índice de coluna esquerda/direita aqui.
    # ========================================================

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

    nome_pericia = PERICIAS[
        coluna
    ][1]

    await interaction.response.send_message(
        f"📚 **{f['nome']}** — {nome_pericia} alterada para **{valor}**."
    )


# ============================================================
# ALTERAR HP E MANA MÁXIMOS
# ============================================================

@bot.tree.command(
    name="alterarficha",
    description="Altera HP e Mana máximos de um jogador."
)
@app_commands.describe(
    jogador="Jogador",
    hp="Novo HP máximo",
    mana="Nova Mana máxima"
)
async def alterarficha(
    interaction,
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
            "❌ Ficha não encontrada.",
            ephemeral=True
        )

        return

    f = transformar_ficha(dados)

    if not pode_alterar_ficha(
        interaction,
        f
    ):

        await interaction.response.send_message(
            "❌ Você não pode alterar essa ficha.",
            ephemeral=True
        )

        return

    if hp <= 0 or mana < 0:

        await interaction.response.send_message(
            "❌ Valores inválidos.",
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
        f"⚙️ **{f['nome']}** atualizada!\n"
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
    interaction
):

    dados = buscar_ficha_jogador(
        interaction.channel.id,
        interaction.user.id
    )

    if dados is None:

        await interaction.response.send_message(
            "❌ Você não possui uma ficha.",
            ephemeral=True
        )

        return

    f = transformar_ficha(dados)

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
#
# Pode ser usado pelo jogador em outra ficha.
# Mestre/Admin também pode.
# ============================================================

@bot.tree.command(
    name="dano",
    description="Aplica dano a um jogador."
)
@app_commands.describe(
    jogador="Jogador que receberá o dano",
    valor="Quantidade de dano"
)
async def dano(
    interaction,
    jogador: discord.Member,
    valor: int
):

    if valor <= 0:

        await interaction.response.send_message(
            "❌ O dano precisa ser maior que 0.",
            ephemeral=True
        )

        return

    dados = buscar_ficha_jogador(
        interaction.channel.id,
        jogador.id
    )

    if dados is None:

        await interaction.response.send_message(
            "❌ Ficha não encontrada.",
            ephemeral=True
        )

        return

    f = transformar_ficha(dados)

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
        f"💥 **{f['nome']}** recebeu **{valor} de dano**!\n"
        f"❤️ HP: **{novo_hp}/{f['hp_max']}**"
    )


# ============================================================
# CURA
#
# Jogador pode curar outro jogador.
# ============================================================

@bot.tree.command(
    name="cura",
    description="Cura um jogador."
)
@app_commands.describe(
    jogador="Jogador que receberá a cura",
    valor="Quantidade de cura"
)
async def cura(
    interaction,
    jogador: discord.Member,
    valor: int
):

    if valor <= 0:

        await interaction.response.send_message(
            "❌ A cura precisa ser maior que 0.",
            ephemeral=True
        )

        return

    dados = buscar_ficha_jogador(
        interaction.channel.id,
        jogador.id
    )

    if dados is None:

        await interaction.response.send_message(
            "❌ Ficha não encontrada.",
            ephemeral=True
        )

        return

    f = transformar_ficha(dados)

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
        f"💚 **{f['nome']}** recuperou **{recuperado} HP**!\n"
        f"❤️ HP: **{novo_hp}/{f['hp_max']}**"
    )


# ============================================================
# CURAR NPC
# ============================================================

@bot.tree.command(
    name="curarnpc",
    description="Cura um NPC."
)
@app_commands.describe(
    nome="Nome exato do NPC",
    valor="Quantidade de cura"
)
async def curarnpc(
    interaction,
    nome: str,
    valor: int
):

    if valor <= 0:

        await interaction.response.send_message(
            "❌ A cura precisa ser maior que 0.",
            ephemeral=True
        )

        return

    dados = buscar_ficha_por_nome(
        interaction.channel.id,
        nome
    )

    if dados is None:

        await interaction.response.send_message(
            "❌ NPC não encontrado.",
            ephemeral=True
        )

        return

    f = transformar_ficha(dados)

    if f["tipo"] != "npc":

        await interaction.response.send_message(
            "❌ Essa ficha não é um NPC.",
            ephemeral=True
        )

        return

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
        f"💚 **{f['nome']}** recuperou **{recuperado} HP**!\n"
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
    interaction,
    valor: int
):

    dados = buscar_ficha_jogador(
        interaction.channel.id,
        interaction.user.id
    )

    if dados is None:

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

    f = transformar_ficha(dados)

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
        f"🔮 **{f['nome']}** gastou **{valor} Mana**!\n"
        f"🔵 Mana: **{nova_mana}/{f['mana_max']}**"
    )


# ============================================================
# RECUPERAR MANA DE OUTRO JOGADOR
# ============================================================

@bot.tree.command(
    name="recuperarmana",
    description="Recupera Mana de um jogador."
)
@app_commands.describe(
    jogador="Jogador que receberá Mana",
    valor="Quantidade de Mana"
)
async def recuperarmana(
    interaction,
    jogador: discord.Member,
    valor: int
):

    if valor <= 0:

        await interaction.response.send_message(
            "❌ O valor precisa ser maior que 0.",
            ephemeral=True
        )

        return

    dados = buscar_ficha_jogador(
        interaction.channel.id,
        jogador.id
    )

    if dados is None:

        await interaction.response.send_message(
            "❌ Ficha não encontrada.",
            ephemeral=True
        )

        return

    f = transformar_ficha(dados)

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
        f"💧 **{f['nome']}** recuperou **{recuperado} Mana**!\n"
        f"🔵 Mana: **{nova_mana}/{f['mana_max']}**"
    )


# ============================================================
# RECUPERAR MANA DE NPC
# ============================================================

@bot.tree.command(
    name="recuperarmananpc",
    description="Recupera Mana de um NPC."
)
@app_commands.describe(
    nome="Nome exato do NPC",
    valor="Quantidade de Mana"
)
async def recuperarmananpc(
    interaction,
    nome: str,
    valor: int
):

    if valor <= 0:

        await interaction.response.send_message(
            "❌ O valor precisa ser maior que 0.",
            ephemeral=True
        )

        return

    dados = buscar_ficha_por_nome(
        interaction.channel.id,
        nome
    )

    if dados is None:

        await interaction.response.send_message(
            "❌ NPC não encontrado.",
            ephemeral=True
        )

        return

    f = transformar_ficha(dados)

    if f["tipo"] != "npc":

        await interaction.response.send_message(
            "❌ Essa ficha não é um NPC.",
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
        f"💧 **{f['nome']}** recuperou **{recuperado} Mana**!\n"
        f"🔵 Mana: **{nova_mana}/{f['mana_max']}**"
    )


# ============================================================
# XP
# ============================================================

@bot.tree.command(
    name="addxp",
    description="Adiciona XP a uma ficha."
)
@app_commands.describe(
    jogador="Jogador",
    valor="Quantidade de XP"
)
async def addxp(
    interaction,
    jogador: discord.Member,
    valor: int
):

    if valor <= 0:

        await interaction.response.send_message(
            "❌ O XP precisa ser maior que 0.",
            ephemeral=True
        )

        return

    if (
        not eh_mestre(interaction)
        and not eh_admin(interaction)
        and jogador.id != interaction.user.id
    ):

        await interaction.response.send_message(
            "❌ Você não pode alterar o XP desse jogador.",
            ephemeral=True
        )

        return

    dados = buscar_ficha_jogador(
        interaction.channel.id,
        jogador.id
    )

    if dados is None:

        await interaction.response.send_message(
            "❌ Ficha não encontrada.",
            ephemeral=True
        )

        return

    f = transformar_ficha(dados)

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
        """
        SELECT xp
        FROM fichas
        WHERE id = ?
        """,
        (f["id"],)
    )

    xp_atual = cursor.fetchone()["xp"]

    await interaction.response.send_message(
        f"✨ **{f['nome']}** recebeu **{valor} XP**!\n"
        f"✨ XP atual: **{xp_atual}**"
    )


# ============================================================
# CRIAR NPC
# ============================================================

@bot.tree.command(
    name="criarnpc",
    description="Cria um NPC."
)
@app_commands.describe(
    aleatorio="NPC aleatório?",
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
    interaction,
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

        nome = random.choice(
            nomes
        )

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

    colunas = (
        list(ATRIBUTOS.keys())
        + list(PERICIAS.keys())
    )

    valores = (
        [
            atributos[chave]
            for chave in ATRIBUTOS
        ]
        +
        [
            pericias[chave]
            for chave in PERICIAS
        ]
    )

    nomes_colunas = ", ".join(
        colunas
    )

    placeholders = ", ".join(
        ["?"] * len(valores)
    )

    cursor.execute(
        f"""
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
            {nomes_colunas},
            aleatorio
        )
        VALUES (
            ?, NULL, ?, 'npc', ?,
            ?, ?, ?, ?, 0,
            {placeholders},
            ?
        )
        """,
        [
            interaction.channel.id,
            mestre_id,
            nome,
            hp,
            hp,
            mana,
            mana
        ]
        + valores
        + [
            aleatorio_valor
        ]
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
        f"⚡ RC: **{rc}**\n\n"
        f"🎲 Atributos e perícias "
        f"{'gerados aleatoriamente' if aleatorio_valor else 'iniciados em 0'}."
    )


# ============================================================
# LISTAR NPCS
# ============================================================

@bot.tree.command(
    name="npcs",
    description="Mostra os NPCs da mesa."
)
async def npcs(interaction):

    if (
        not eh_mestre(interaction)
        and not eh_admin(interaction)
    ):

        await interaction.response.send_message(
            "❌ Somente o Mestre pode visualizar os NPCs.",
            ephemeral=True
        )

        return

    cursor.execute("""
        SELECT *
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

    await interaction.response.send_message(
        f"👹 **NPCs da mesa — {len(resultados)} encontrados**",
        ephemeral=True
    )

    for dados in resultados:

        f = transformar_ficha(
            dados
        )

        await interaction.followup.send(
            embed=criar_pagina_status(
                f
            ),
            view=FichaView(f),
            ephemeral=True
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
    interaction,
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

    dados = buscar_ficha_por_nome(
        interaction.channel.id,
        nome
    )

    if dados is None:

        await interaction.response.send_message(
            "❌ NPC não encontrado.",
            ephemeral=True
        )

        return

    f = transformar_ficha(
        dados
    )

    if f["tipo"] != "npc":

        await interaction.response.send_message(
            "❌ Essa ficha não é um NPC.",
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
# AJUDA
# ============================================================

@bot.tree.command(
    name="help",
    description="Mostra os comandos do bot."
)
async def help(interaction):

    embed = discord.Embed(
        title="📖 BotRPG",
        description="Comandos disponíveis",
        color=discord.Color.dark_red()
    )

    embed.add_field(
        name="👤 Jogador",
        value=(
            "`/criarficha`\n"
            "`/ficha`\n"
            "`/verficha`\n"
            "`/atributo`\n"
            "`/pericia`\n"
            "`/apagarficha`\n"
            "`/gastarmana`\n"
            "`/cura`\n"
            "`/dano`\n"
            "`/recuperarmana`\n"
            "`/addxp`"
        ),
        inline=False
    )

    embed.add_field(
        name="👹 NPC / Mestre",
        value=(
            "`/criarnpc`\n"
            "`/npcs`\n"
            "`/apagarnpc`\n"
            "`/curarnpc`\n"
            "`/recuperarmananpc`\n"
            "`/alterarficha`"
        ),
        inline=False
    )

    embed.add_field(
        name="👑 Mesa",
        value=(
            "`/definirmestre`\n"
            "`/passarmestre`\n"
            "`/mestre`"
        ),
        inline=False
    )

    embed.add_field(
        name="⚔️ Alteração de ficha pelo Mestre",
        value=(
            "O Mestre pode alterar qualquer ficha "
            "usando o nome do personagem.\n\n"
            "`/atributo` → escolha o personagem\n"
            "`/pericia` → escolha o personagem"
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
# ENCERRAMENTO SEGURO DO BANCO
# ============================================================

import atexit


@atexit.register
def fechar_banco():

    try:
        db.close()
    except Exception:
        pass


# ============================================================
# INICIAR BOT
# ============================================================

bot.run(TOKEN)
