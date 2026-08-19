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

def adicionar_coluna_se_nao_existir(nome_coluna):
    cursor.execute("PRAGMA table_info(fichas)")
    colunas = [coluna[1] for coluna in cursor.fetchall()]

    if nome_coluna not in colunas:
        cursor.execute(
            f"""
            ALTER TABLE fichas
            ADD COLUMN {nome_coluna} INTEGER NOT NULL DEFAULT 0
            """
        )
        db.commit()


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
# COLUNAS DA FICHA
# ============================================================

COLUNAS_FICHA = [
    "id",
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


def buscar_ficha_jogador(channel_id, user_id):
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


def transformar_ficha(dados):
    if dados is None:
        return None

    ficha = {}

    for indice, coluna in enumerate(COLUNAS_FICHA):
        if indice < len(dados):
            ficha[coluna] = dados[indice]

    return ficha


def buscar_ficha_por_nome(channel_id, nome):
    cursor.execute("""
        SELECT *
        FROM fichas
        WHERE channel_id = ?
        AND nome = ?
        LIMIT 1
    """, (
        channel_id,
        nome
    ))

    resultado = cursor.fetchone()

    return transformar_ficha(resultado)


def buscar_ficha_por_id(channel_id, ficha_id):
    cursor.execute("""
        SELECT *
        FROM fichas
        WHERE channel_id = ?
        AND id = ?
        LIMIT 1
    """, (
        channel_id,
        ficha_id
    ))

    resultado = cursor.fetchone()

    return transformar_ficha(resultado)


# ============================================================
# REFLEXO DE COMBATE
# ============================================================

def calcular_rc(ficha):
    return (
        ficha["esquiva"]
        + ficha["destreza"]
        + 5
    )


# ============================================================
# ESTADO DOS RECURSOS
# ============================================================

def estado_recurso(atual, maximo):
    if atual <= 0 or maximo <= 0:
        return "ZERADO"

    percentual = (atual / maximo) * 100

    if percentual >= 70:
        return "BOM"

    if percentual >= 30:
        return "BAIXO"

    return "CRÍTICO"


def emoji_hp(atual, maximo):
    estado = estado_recurso(atual, maximo)

    return {
        "BOM": "🟢",
        "BAIXO": "🟡",
        "CRÍTICO": "🔴",
        "ZERADO": "⚫"
    }.get(estado, "⚪")


def emoji_mana(atual, maximo):
    estado = estado_recurso(atual, maximo)

    return {
        "BOM": "🔵",
        "BAIXO": "🟡",
        "CRÍTICO": "🔴",
        "ZERADO": "⚫"
    }.get(estado, "⚪")


# ============================================================
# ALINHAMENTO AUTOMÁTICO
# ============================================================

def alinhar_duas_colunas(itens):
    """
    Divide os itens em duas colunas e calcula
    automaticamente o espaçamento da primeira coluna.

    O valor da coluna nunca é usado para determinar
    a chave da segunda coluna. Isso evita o erro
    de alteração de perícias trocadas.
    """

    linhas = []

    metade = (len(itens) + 1) // 2

    coluna_esquerda = itens[:metade]
    coluna_direita = itens[metade:]

    esquerda_formatada = []

    for chave, dados in coluna_esquerda:
        emoji, nome = dados
        esquerda_formatada.append(
            f"{emoji} {nome}: {chave}"
        )

    largura = 0

    for texto in esquerda_formatada:
        if len(texto) > largura:
            largura = len(texto)

    largura += 2

    for indice in range(metade):

        esquerda = esquerda_formatada[indice]

        if indice < len(coluna_direita):
            chave, dados = coluna_direita[indice]

            emoji, nome = dados

            direita = f"{emoji} {nome}: {chave}"

            linhas.append(
                f"{esquerda:<{largura}}{direita}"
            )

        else:
            linhas.append(esquerda)

    return "\n".join(linhas)


# ============================================================
# TEXTO DOS ATRIBUTOS
# ============================================================

def texto_atributos(ficha):
    itens = []

    for chave, dados in ATRIBUTOS.items():
        itens.append(
            (
                str(ficha[chave]),
                (
                    dados[0],
                    f"{dados[1]}"
                )
            )
        )

    return alinhar_duas_colunas(itens)


# ============================================================
# TEXTO DAS PERÍCIAS
# ============================================================

def texto_pericias(ficha):
    """
    Usa uma estrutura independente para cada perícia.
    Não há qualquer associação por posição entre
    os valores das duas colunas.
    """

    itens = []

    for chave, dados in PERICIAS.items():
        itens.append(
            (
                str(ficha[chave]),
                (
                    dados[0],
                    dados[1]
                )
            )
        )

    return alinhar_duas_colunas(itens)


# ============================================================
# STATUS
# ============================================================

def texto_status(ficha):
    hp = (
        f"{emoji_hp(ficha['hp_atual'], ficha['hp_max'])} "
        f"HP: {ficha['hp_atual']}/{ficha['hp_max']}"
    )

    mana = (
        f"{emoji_mana(ficha['mana_atual'], ficha['mana_max'])} "
        f"Mana: {ficha['mana_atual']}/{ficha['mana_max']}"
    )

    xp = f"✨ XP: {ficha['xp']}"
    rc = f"⚡ RC: {calcular_rc(ficha)}"

    itens = [
        ("hp", (hp, "")),
        ("mana", (mana, "")),
        ("xp", (xp, "")),
        ("rc", (rc, ""))
    ]

    esquerda = [
        hp,
        xp
    ]

    direita = [
        mana,
        rc
    ]

    largura = max(
        len(texto)
        for texto in esquerda
    ) + 2

    linhas = []

    for i in range(2):
        linhas.append(
            f"{esquerda[i]:<{largura}}{direita[i]}"
        )

    return "\n".join(linhas)


# ============================================================
# EMBED STATUS
# ============================================================

def criar_pagina_status(ficha, jogador=None):

    tipo = "👤 JOGADOR" if ficha["tipo"] == "jogador" else "👹 NPC"

    if jogador:
        dono = f"Jogador: {jogador.mention}"
    else:
        dono = "Mestre: ficha de NPC"

    texto = (
        "```text\n"
        f"📜 FICHA: {ficha['nome']}\n"
        f"{tipo}\n"
        f"{dono}\n"
        "\n"
        "❤️ STATUS\n"
        "\n"
        f"{texto_status(ficha)}\n"
        "\n"
        "⚔️ ATRIBUTOS\n"
        "\n"
        f"{texto_atributos(ficha)}\n"
        "```"
    )

    embed = discord.Embed(
        description=texto,
        color=discord.Color.dark_red()
    )

    embed.set_footer(
        text="Página 1/2 • Status e Atributos"
    )

    return embed


# ============================================================
# EMBED PERÍCIAS
# ============================================================

def criar_pagina_pericias(ficha):

    texto = (
        "```text\n"
        f"📚 PERÍCIAS — {ficha['nome']}\n"
        "\n"
        f"{texto_pericias(ficha)}\n"
        "```"
    )

    embed = discord.Embed(
        description=texto,
        color=discord.Color.dark_red()
    )

    embed.set_footer(
        text="Página 2/2 • Perícias"
    )

    return embed


# ============================================================
# PAGINAÇÃO
# ============================================================

class FichaView(discord.ui.View):

    def __init__(self, ficha, jogador=None):
        super().__init__(timeout=120)

        self.ficha = ficha
        self.jogador = jogador

    @discord.ui.button(
        label="◀ Status",
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
        label="Perícias ▶",
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
# PERMISSÃO PARA ALTERAR FICHA
# ============================================================

def pode_alterar_ficha(interaction, ficha):

    if eh_admin(interaction):
        return True

    if eh_mestre(interaction):
        return True

    if ficha["tipo"] == "jogador":
        return ficha["dono_id"] == interaction.user.id

    return False


# ============================================================
# BOT ONLINE
# ============================================================

@bot.event
async def on_ready():

    print(f"Bot conectado como {bot.user}")

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
        f"👑 {jogador.mention} agora é o Mestre deste canal."
    )


# ============================================================
# PASSAR MESTRE
# ============================================================

@bot.tree.command(
    name="passarmestre",
    description="Passa o cargo de Mestre."
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
        f"👑 Mestre transferido para {jogador.mention}."
    )


# ============================================================
# VER MESTRE
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
            "👑 Este canal ainda não possui um Mestre."
        )

        return

    membro = interaction.guild.get_member(
        mestre_id
    )

    if membro:

        await interaction.response.send_message(
            f"👑 Mestre: {membro.mention}"
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
            xp,
            forca,
            destreza,
            vigor,
            inteligencia,
            carisma,
            raciocinio,
            academicos,
            idiomas,
            oficios,
            armas_brancas,
            intimidacao,
            ocultismo,
            briga,
            investigacao,
            persuasao,
            ciencias,
            labia,
            prontidao,
            conhecimentos_gerais,
            lideranca,
            sobrevivencia,
            conducao,
            manha,
            tecnologia,
            esportes,
            medicina,
            mira,
            esquiva,
            furtividade,
            aleatorio
        )
        VALUES (
            ?, ?, NULL, 'jogador', ?,
            ?, ?, ?, ?, 0,
            0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0,
            0
        )
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
        f"📜 Ficha de {nome} criada!\n\n"
        f"❤️ HP: {hp}/{hp}\n"
        f"🔵 Mana: {mana}/{mana}\n"
        f"✨ XP: 0\n"
        f"⚡ RC: 5"
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
    interaction: discord.Interaction,
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
# ALTERAR ATRIBUTO
# ============================================================

@bot.tree.command(
    name="atributo",
    description="Altera um atributo."
)
@app_commands.describe(
    atributo="Atributo",
    valor="Novo valor",
    ficha="ID da ficha, opcional para o Mestre"
)
@app_commands.choices(
    atributo=[
        app_commands.Choice(name="Força", value="forca"),
        app_commands.Choice(name="Destreza", value="destreza"),
        app_commands.Choice(name="Vigor", value="vigor"),
        app_commands.Choice(name="Inteligência", value="inteligencia"),
        app_commands.Choice(name="Carisma", value="carisma"),
        app_commands.Choice(name="Raciocínio", value="raciocinio")
    ]
)
async def atributo(
    interaction: discord.Interaction,
    atributo: app_commands.Choice[str],
    valor: int,
    ficha: int = None
):

    if valor < 0:

        await interaction.response.send_message(
            "❌ O valor não pode ser negativo.",
            ephemeral=True
        )

        return

    if ficha is None:

        dados = buscar_ficha_jogador(
            interaction.channel.id,
            interaction.user.id
        )

    else:

        dados = buscar_ficha_por_id(
            interaction.channel.id,
            ficha
        )

    if dados is None:

        await interaction.response.send_message(
            "❌ Ficha não encontrada.",
            ephemeral=True
        )

        return

    if not pode_alterar_ficha(
        interaction,
        dados
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
            dados["id"]
        )
    )

    db.commit()

    await interaction.response.send_message(
        f"⚔️ {dados['nome']} — "
        f"{ATRIBUTOS[coluna][1]} alterado para {valor}."
    )


# ============================================================
# ALTERAR PERÍCIA
# ============================================================

@bot.tree.command(
    name="pericia",
    description="Altera uma perícia."
)
@app_commands.describe(
    pericia="Perícia",
    valor="Novo valor",
    ficha="ID da ficha, opcional para o Mestre"
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
    ficha: int = None
):

    if valor < 0:

        await interaction.response.send_message(
            "❌ O valor não pode ser negativo.",
            ephemeral=True
        )

        return

    if ficha is None:

        dados = buscar_ficha_jogador(
            interaction.channel.id,
            interaction.user.id
        )

    else:

        dados = buscar_ficha_por_id(
            interaction.channel.id,
            ficha
        )

    if dados is None:

        await interaction.response.send_message(
            "❌ Ficha não encontrada.",
            ephemeral=True
        )

        return

    if not pode_alterar_ficha(
        interaction,
        dados
    ):

        await interaction.response.send_message(
            "❌ Você não pode alterar essa ficha.",
            ephemeral=True
        )

        return

    coluna = pericia.value

    cursor.execute(
        f"""
        UPDATE fichas
        SET {coluna} = ?
        WHERE id = ?
        """,
        (
            valor,
            dados["id"]
        )
    )

    db.commit()

    await interaction.response.send_message(
        f"📚 {dados['nome']} — "
        f"{PERICIAS[coluna][1]} alterada para {valor}."
    )


# ============================================================
# ALTERAR HP E MANA MÁXIMOS
# ============================================================

@bot.tree.command(
    name="alterarficha",
    description="Altera HP e Mana máximos."
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
            "❌ Esse jogador não possui uma ficha.",
            ephemeral=True
        )

        return

    if not pode_alterar_ficha(
        interaction,
        dados
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
        dados["id"]
    ))

    db.commit()

    await interaction.response.send_message(
        f"⚙️ Ficha de {dados['nome']} atualizada.\n\n"
        f"❤️ HP: {hp}/{hp}\n"
        f"🔵 Mana: {mana}/{mana}"
    )


# ============================================================
# APAGAR FICHA
# ============================================================

@bot.tree.command(
    name="apagarficha",
    description="Apaga sua ficha."
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
            "❌ Você não possui uma ficha.",
            ephemeral=True
        )

        return

    cursor.execute(
        "DELETE FROM fichas WHERE id = ?",
        (dados["id"],)
    )

    db.commit()

    await interaction.response.send_message(
        f"🗑️ A ficha {dados['nome']} foi apagada."
    )


# ============================================================
# DANO
# ============================================================

@bot.tree.command(
    name="dano",
    description="Aplica dano a um jogador."
)
@app_commands.describe(
    jogador="Jogador que receberá dano",
    valor="Quantidade de dano"
)
async def dano(
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
            "❌ Ficha não encontrada.",
            ephemeral=True
        )

        return

    if valor <= 0:

        await interaction.response.send_message(
            "❌ O dano precisa ser maior que 0.",
            ephemeral=True
        )

        return

    novo_hp = max(
        0,
        dados["hp_atual"] - valor
    )

    cursor.execute("""
        UPDATE fichas
        SET hp_atual = ?
        WHERE id = ?
    """, (
        novo_hp,
        dados["id"]
    ))

    db.commit()

    await interaction.response.send_message(
        f"💥 {dados['nome']} recebeu {valor} de dano.\n"
        f"❤️ HP: {novo_hp}/{dados['hp_max']}"
    )


# ============================================================
# CURA
# ============================================================

@bot.tree.command(
    name="cura",
    description="Cura um jogador."
)
@app_commands.describe(
    jogador="Jogador que receberá cura",
    valor="Quantidade de cura"
)
async def cura(
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
            "❌ Ficha não encontrada.",
            ephemeral=True
        )

        return

    if valor <= 0:

        await interaction.response.send_message(
            "❌ A cura precisa ser maior que 0.",
            ephemeral=True
        )

        return

    novo_hp = min(
        dados["hp_max"],
        dados["hp_atual"] + valor
    )

    recuperado = novo_hp - dados["hp_atual"]

    cursor.execute("""
        UPDATE fichas
        SET hp_atual = ?
        WHERE id = ?
    """, (
        novo_hp,
        dados["id"]
    ))

    db.commit()

    await interaction.response.send_message(
        f"💚 {dados['nome']} recuperou {recuperado} de HP.\n"
        f"❤️ HP: {novo_hp}/{dados['hp_max']}"
    )


# ============================================================
# GASTAR MANA
# ============================================================

@bot.tree.command(
    name="gastarmana",
    description="Gasta Mana."
)
@app_commands.describe(
    valor="Quantidade de Mana"
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

    if valor > dados["mana_atual"]:

        await interaction.response.send_message(
            "❌ Mana insuficiente.",
            ephemeral=True
        )

        return

    nova_mana = dados["mana_atual"] - valor

    cursor.execute("""
        UPDATE fichas
        SET mana_atual = ?
        WHERE id = ?
    """, (
        nova_mana,
        dados["id"]
    ))

    db.commit()

    await interaction.response.send_message(
        f"🔮 {dados['nome']} gastou {valor} de Mana.\n"
        f"🔵 Mana: {nova_mana}/{dados['mana_max']}"
    )


# ============================================================
# RECUPERAR MANA
# ============================================================

@bot.tree.command(
    name="recuperarmana",
    description="Recupera Mana de jogador ou NPC."
)
@app_commands.describe(
    jogador="Jogador que receberá Mana",
    valor="Quantidade de Mana"
)
async def recuperarmana(
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
            "❌ Ficha não encontrada.",
            ephemeral=True
        )

        return

    if valor <= 0:

        await interaction.response.send_message(
            "❌ O valor precisa ser maior que 0.",
            ephemeral=True
        )

        return

    nova_mana = min(
        dados["mana_max"],
        dados["mana_atual"] + valor
    )

    recuperado = nova_mana - dados["mana_atual"]

    cursor.execute("""
        UPDATE fichas
        SET mana_atual = ?
        WHERE id = ?
    """, (
        nova_mana,
        dados["id"]
    ))

    db.commit()

    await interaction.response.send_message(
        f"💧 {dados['nome']} recuperou {recuperado} de Mana.\n"
        f"🔵 Mana: {nova_mana}/{dados['mana_max']}"
    )


# ============================================================
# CURAR / RECUPERAR NPC OU QUALQUER FICHA
# ============================================================

@bot.tree.command(
    name="curarficha",
    description="Cura qualquer ficha pelo ID. Mestre pode usar em NPCs."
)
@app_commands.describe(
    ficha="ID da ficha",
    valor="Quantidade de HP"
)
async def curarficha(
    interaction: discord.Interaction,
    ficha: int,
    valor: int
):

    dados = buscar_ficha_por_id(
        interaction.channel.id,
        ficha
    )

    if dados is None:

        await interaction.response.send_message(
            "❌ Ficha não encontrada.",
            ephemeral=True
        )

        return

    if valor <= 0:

        await interaction.response.send_message(
            "❌ O valor precisa ser maior que 0.",
            ephemeral=True
        )

        return

    if (
        dados["tipo"] == "npc"
        and not eh_mestre(interaction)
        and not eh_admin(interaction)
    ):

        await interaction.response.send_message(
            "❌ Somente o Mestre pode alterar NPCs.",
            ephemeral=True
        )

        return

    if (
        dados["tipo"] == "jogador"
        and dados["dono_id"] != interaction.user.id
        and not eh_mestre(interaction)
        and not eh_admin(interaction)
    ):

        await interaction.response.send_message(
            "❌ Você não pode alterar essa ficha.",
            ephemeral=True
        )

        return

    novo_hp = min(
        dados["hp_max"],
        dados["hp_atual"] + valor
    )

    recuperado = novo_hp - dados["hp_atual"]

    cursor.execute("""
        UPDATE fichas
        SET hp_atual = ?
        WHERE id = ?
    """, (
        novo_hp,
        dados["id"]
    ))

    db.commit()

    await interaction.response.send_message(
        f"💚 {dados['nome']} recuperou {recuperado} de HP.\n"
        f"❤️ HP: {novo_hp}/{dados['hp_max']}"
    )


# ============================================================
# RECUPERAR MANA POR ID
# ============================================================

@bot.tree.command(
    name="manaficha",
    description="Recupera Mana de qualquer ficha pelo ID."
)
@app_commands.describe(
    ficha="ID da ficha",
    valor="Quantidade de Mana"
)
async def manaficha(
    interaction: discord.Interaction,
    ficha: int,
    valor: int
):

    dados = buscar_ficha_por_id(
        interaction.channel.id,
        ficha
    )

    if dados is None:

        await interaction.response.send_message(
            "❌ Ficha não encontrada.",
            ephemeral=True
        )

        return

    if valor <= 0:

        await interaction.response.send_message(
            "❌ O valor precisa ser maior que 0.",
            ephemeral=True
        )

        return

    if (
        dados["tipo"] == "npc"
        and not eh_mestre(interaction)
        and not eh_admin(interaction)
    ):

        await interaction.response.send_message(
            "❌ Somente o Mestre pode alterar NPCs.",
            ephemeral=True
        )

        return

    if (
        dados["tipo"] == "jogador"
        and dados["dono_id"] != interaction.user.id
        and not eh_mestre(interaction)
        and not eh_admin(interaction)
    ):

        await interaction.response.send_message(
            "❌ Você não pode alterar essa ficha.",
            ephemeral=True
        )

        return

    nova_mana = min(
        dados["mana_max"],
        dados["mana_atual"] + valor
    )

    recuperado = nova_mana - dados["mana_atual"]

    cursor.execute("""
        UPDATE fichas
        SET mana_atual = ?
        WHERE id = ?
    """, (
        nova_mana,
        dados["id"]
    ))

    db.commit()

    await interaction.response.send_message(
        f"💧 {dados['nome']} recuperou {recuperado} de Mana.\n"
        f"🔵 Mana: {nova_mana}/{dados['mana_max']}"
    )


# ============================================================
# XP
# ============================================================

@bot.tree.command(
    name="addxp",
    description="Adiciona XP."
)
@app_commands.describe(
    jogador="Jogador",
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
            "❌ Ficha não encontrada.",
            ephemeral=True
        )

        return

    if valor <= 0:

        await interaction.response.send_message(
            "❌ O XP precisa ser maior que 0.",
            ephemeral=True
        )

        return

    if (
        dados["dono_id"] != interaction.user.id
        and not eh_mestre(interaction)
        and not eh_admin(interaction)
    ):

        await interaction.response.send_message(
            "❌ Você não pode alterar o XP dessa ficha.",
            ephemeral=True
        )

        return

    cursor.execute("""
        UPDATE fichas
        SET xp = xp + ?
        WHERE id = ?
    """, (
        valor,
        dados["id"]
    ))

    db.commit()

    cursor.execute(
        "SELECT xp FROM fichas WHERE id = ?",
        (dados["id"],)
    )

    xp_atual = cursor.fetchone()[0]

    await interaction.response.send_message(
        f"✨ {dados['nome']} recebeu {valor} XP.\n"
        f"✨ XP atual: {xp_atual}"
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

        hp = random.randint(20, 150)

        mana = random.randint(0, 100)

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
        + ORDEM_PERICIAS
    )

    valores = (
        [atributos[chave] for chave in ATRIBUTOS]
        + [pericias[chave] for chave in ORDEM_PERICIAS]
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
            {", ".join(colunas)},
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
        + [aleatorio_valor]
    )

    db.commit()

    rc = (
        pericias["esquiva"]
        + atributos["destreza"]
        + 5
    )

    await interaction.response.send_message(
        f"👹 NPC {nome} criado!\n\n"
        f"❤️ HP: {hp}/{hp}\n"
        f"🔵 Mana: {mana}/{mana}\n"
        f"⚡ RC: {rc}"
    )


# ============================================================
# LISTAR NPCS
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

    primeiro = True

    for dados in resultados:

        ficha_npc = transformar_ficha(dados)

        if primeiro:

            await interaction.response.send_message(
                embed=criar_pagina_status(
                    ficha_npc
                ),
                view=FichaView(
                    ficha_npc
                ),
                ephemeral=True
            )

            primeiro = False

        else:

            await interaction.followup.send(
                embed=criar_pagina_status(
                    ficha_npc
                ),
                view=FichaView(
                    ficha_npc
                ),
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

    cursor.execute(
        "DELETE FROM fichas WHERE id = ?",
        (resultado[0],)
    )

    db.commit()

    await interaction.response.send_message(
        f"🗑️ NPC {nome} apagado."
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
            "`/ficha` — Ver ficha\n"
            "`/verficha` — Ver outra ficha\n"
            "`/atributo` — Alterar atributo\n"
            "`/pericia` — Alterar perícia\n"
            "`/alterarficha` — Alterar HP/Mana\n"
            "`/apagarficha` — Apagar ficha\n"
            "`/dano` — Aplicar dano\n"
            "`/cura` — Curar jogador\n"
            "`/gastarmana` — Gastar Mana\n"
            "`/recuperarmana` — Recuperar Mana\n"
            "`/addxp` — Adicionar XP"
        ),
        inline=False
    )

    embed.add_field(
        name="👑 Mestre",
        value=(
            "`/definirmestre` — Definir Mestre\n"
            "`/passarmestre` — Passar Mestre\n"
            "`/mestre` — Ver Mestre\n"
            "`/criarnpc` — Criar NPC\n"
            "`/npcs` — Ver NPCs\n"
            "`/apagarnpc` — Apagar NPC\n"
            "`/curarficha` — Curar por ID\n"
            "`/manaficha` — Recuperar Mana por ID"
        ),
        inline=False
    )

    embed.add_field(
        name="🛡️ Alterações por ficha",
        value=(
            "O Mestre pode usar `/atributo` e `/pericia` "
            "informando o ID da ficha para alterar "
            "qualquer jogador ou NPC."
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
