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
# MIGRAÇÃO
# ============================================================

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
# BUSCAR FICHAS
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


def buscar_ficha_do_canal(
    channel_id,
    ficha_id
):

    cursor.execute("""
        SELECT *
        FROM fichas
        WHERE id = ?
        AND channel_id = ?
    """, (
        ficha_id,
        channel_id
    ))

    return cursor.fetchone()


# ============================================================
# CONVERTER FICHA
# ============================================================

def transformar_ficha(dados):

    if dados is None:
        return None

    # IMPORTANTE:
    # Agora a ficha é transformada usando o nome
    # das colunas do SQLite.
    #
    # Isso elimina o problema anterior em que
    # uma perícia podia acabar pegando o valor
    # da coluna ao lado.

    return {
        coluna: dados[coluna]
        for coluna in dados.keys()
    }


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
# STATUS
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


# ============================================================
# PERMISSÕES DE ALTERAÇÃO
# ============================================================

def pode_alterar_ficha(
    interaction,
    ficha
):

    if eh_admin(interaction):
        return True

    if eh_mestre(interaction):
        return True

    if ficha["tipo"] == "jogador":

        return (
            ficha["dono_id"]
            == interaction.user.id
        )

    return False


# ============================================================
# FORMATAÇÃO DE ATRIBUTOS
# ============================================================

def texto_atributos(f):

    largura = 18

    linhas = []

    itens = list(ATRIBUTOS.items())

    for i in range(0, len(itens), 2):

        chave1, (emoji1, nome1) = itens[i]

        chave2, (emoji2, nome2) = itens[i + 1]

        coluna1 = (
            f"{emoji1} "
            f"{nome1}: "
            f"{f[chave1]}"
        )

        coluna2 = (
            f"{emoji2} "
            f"{nome2}: "
            f"{f[chave2]}"
        )

        linhas.append(
            coluna1.ljust(largura)
            + "   "
            + coluna2
        )

    return "\n".join(linhas)


# ============================================================
# FORMATAÇÃO DAS PERÍCIAS
# ============================================================

def texto_pericias(f):

    # Fonte monoespaçada do Discord.
    #
    # O uso de ljust garante que as duas
    # colunas permaneçam alinhadas.

    largura = 23

    linhas = []

    itens = list(PERICIAS.items())

    for i in range(0, len(itens), 2):

        chave1, (emoji1, nome1) = itens[i]

        valor1 = f[chave1]

        coluna1 = (
            f"{emoji1} "
            f"{nome1}: "
            f"{valor1}"
        )

        if i + 1 < len(itens):

            chave2, (emoji2, nome2) = itens[i + 1]

            valor2 = f[chave2]

            coluna2 = (
                f"{emoji2} "
                f"{nome2}: "
                f"{valor2}"
            )

        else:

            coluna2 = ""

        linhas.append(
            coluna1.ljust(largura)
            + "   "
            + coluna2
        )

    return "\n".join(linhas)


# ============================================================
# PÁGINA DE STATUS
# ============================================================

def criar_pagina_status(
    f,
    jogador=None
):

    embed = discord.Embed(
        title=f"📜 FICHA DE {f['nome'].upper()}",
        color=discord.Color.dark_red()
    )

    if f["tipo"] == "jogador":

        if jogador:

            dono = jogador.mention

        else:

            dono = f"<@{f['dono_id']}>"

        tipo = (
            f"👤 Jogador: {dono}"
        )

    else:

        tipo = "👹 NPC"

    descricao = (
        f"ID da ficha: `{f['id']}`\n"
        f"{tipo}\n\n"

        f"❤️ STATUS\n"
        f"```text\n"
        f"HP:   {f['hp_atual']}/{f['hp_max']}\n"
        f"Mana: {f['mana_atual']}/{f['mana_max']}\n"
        f"XP:   {f['xp']}\n"
        f"RC:   {calcular_rc(f)}\n"
        f"```\n"

        f"⚔️ ATRIBUTOS\n"
        f"```text\n"
        f"{texto_atributos(f)}\n"
        f"```"
    )

    embed.description = descricao

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

    embed.description = (
        f"ID da ficha: `{f['id']}`\n\n"
        f"📚 PERÍCIAS\n"
        f"```text\n"
        f"{texto_pericias(f)}\n"
        f"```"
    )

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
            timeout=120
        )

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
        f"👑 Mestre transferido!\n\n"
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
        f"📜 Ficha de **{nome}** criada!\n\n"
        f"ID da ficha: `{cursor.lastrowid}`\n"
        f"❤️ HP: **{hp}/{hp}**\n"
        f"🔵 Mana: **{mana}/{mana}**\n"
        f"✨ XP: **0**\n"
        f"⚡ RC: **5**\n\n"
        f"Use `/atributo` e `/pericia` "
        f"para definir os valores."
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
# ATRIBUTO DO PRÓPRIO JOGADOR
# ============================================================

@bot.tree.command(
    name="atributo",
    description="Altera um atributo da sua própria ficha."
)
@app_commands.describe(
    atributo="Atributo",
    valor="Novo valor"
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

    if atributo.value not in ATRIBUTOS:

        await interaction.response.send_message(
            "❌ Atributo inválido.",
            ephemeral=True
        )

        return

    if valor < 0:

        await interaction.response.send_message(
            "❌ O valor não pode ser negativo.",
            ephemeral=True
        )

        return

    f = transformar_ficha(dados)

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

    await interaction.response.send_message(
        f"⚔️ {ATRIBUTOS[atributo.value][1]} "
        f"alterado para **{valor}**."
    )


# ============================================================
# PERÍCIA DO PRÓPRIO JOGADOR
# ============================================================

@bot.tree.command(
    name="pericia",
    description="Altera uma perícia da sua própria ficha."
)
@app_commands.describe(
    pericia="Perícia",
    valor="Novo valor"
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
        app_commands.Choice(name="Conhec. Gerais", value="conhecimentos_gerais"),
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

    if pericia.value not in PERICIAS:

        await interaction.response.send_message(
            "❌ Perícia inválida.",
            ephemeral=True
        )

        return

    if valor < 0:

        await interaction.response.send_message(
            "❌ O valor não pode ser negativo.",
            ephemeral=True
        )

        return

    f = transformar_ficha(dados)

    # A coluna é escolhida exclusivamente
    # entre as colunas existentes no dicionário
    # PERICIAS.
    #
    # Isso corrige o problema anterior das
    # perícias trocando valores entre colunas.

    coluna = pericia.value

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

    await interaction.response.send_message(
        f"📚 {PERICIAS[coluna][1]} "
        f"alterada para **{valor}**."
    )


# ============================================================
# ALTERAR ATRIBUTO DE QUALQUER FICHA
# MESTRE / ADMIN
# ============================================================

@bot.tree.command(
    name="alteraratributo",
    description="Mestre ou administrador altera atributo de qualquer ficha."
)
@app_commands.describe(
    ficha_id="ID da ficha",
    atributo="Atributo",
    valor="Novo valor"
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
async def alteraratributo(
    interaction: discord.Interaction,
    ficha_id: int,
    atributo: app_commands.Choice[str],
    valor: int
):

    if (
        not eh_mestre(interaction)
        and not eh_admin(interaction)
    ):

        await interaction.response.send_message(
            "❌ Somente o Mestre ou um "
            "administrador pode usar este comando.",
            ephemeral=True
        )

        return

    ficha_dados = buscar_ficha_do_canal(
        interaction.channel.id,
        ficha_id
    )

    if ficha_dados is None:

        await interaction.response.send_message(
            "❌ Ficha não encontrada neste canal.",
            ephemeral=True
        )

        return

    if valor < 0:

        await interaction.response.send_message(
            "❌ O valor não pode ser negativo.",
            ephemeral=True
        )

        return

    if atributo.value not in ATRIBUTOS:

        await interaction.response.send_message(
            "❌ Atributo inválido.",
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
            ficha_id
        )
    )

    db.commit()

    nome = ficha_dados["nome"]

    await interaction.response.send_message(
        f"⚔️ Ficha **{nome}** atualizada.\n\n"
        f"{ATRIBUTOS[atributo.value][1]}: "
        f"**{valor}**"
    )


# ============================================================
# ALTERAR PERÍCIA DE QUALQUER FICHA
# MESTRE / ADMIN
# ============================================================

@bot.tree.command(
    name="alterarpericia",
    description="Mestre ou administrador altera perícia de qualquer ficha."
)
@app_commands.describe(
    ficha_id="ID da ficha",
    pericia="Perícia",
    valor="Novo valor"
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
        app_commands.Choice(name="Conhec. Gerais", value="conhecimentos_gerais"),
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
async def alterarpericia(
    interaction: discord.Interaction,
    ficha_id: int,
    pericia: app_commands.Choice[str],
    valor: int
):

    if (
        not eh_mestre(interaction)
        and not eh_admin(interaction)
    ):

        await interaction.response.send_message(
            "❌ Somente o Mestre ou um "
            "administrador pode usar este comando.",
            ephemeral=True
        )

        return

    ficha_dados = buscar_ficha_do_canal(
        interaction.channel.id,
        ficha_id
    )

    if ficha_dados is None:

        await interaction.response.send_message(
            "❌ Ficha não encontrada neste canal.",
            ephemeral=True
        )

        return

    if pericia.value not in PERICIAS:

        await interaction.response.send_message(
            "❌ Perícia inválida.",
            ephemeral=True
        )

        return

    if valor < 0:

        await interaction.response.send_message(
            "❌ O valor não pode ser negativo.",
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
            ficha_id
        )
    )

    db.commit()

    await interaction.response.send_message(
        f"📚 Ficha **{ficha_dados['nome']}** atualizada.\n\n"
        f"{PERICIAS[coluna][1]}: **{valor}**"
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
            "❌ Esse jogador não possui uma ficha.",
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
        f"⚙️ Ficha de **{f['nome']}** atualizada!\n\n"
        f"❤️ HP: **{hp}/{hp}**\n"
        f"🔵 Mana: **{mana}/{mana}**"
    )


# ============================================================
# APAGAR A PRÓPRIA FICHA
# ============================================================

@bot.tree.command(
    name="apagarficha",
    description="Apaga sua própria ficha."
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

    f = transformar_ficha(dados)

    cursor.execute(
        """
        DELETE FROM fichas
        WHERE id = ?
        AND dono_id = ?
        AND tipo = 'jogador'
        """,
        (
            f["id"],
            interaction.user.id
        )
    )

    db.commit()

    await interaction.response.send_message(
        f"🗑️ Sua ficha **{f['nome']}** "
        f"foi apagada."
    )


# ============================================================
# DANO
# ============================================================

@bot.tree.command(
    name="dano",
    description="Aplica dano a uma ficha de jogador."
)
@app_commands.describe(
    jogador="Jogador que receberá o dano",
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
        f"💥 **{f['nome']}** recebeu "
        f"**{valor} de dano**!\n\n"
        f"❤️ HP: **{novo_hp}/{f['hp_max']}**"
    )


# ============================================================
# CURA
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
        f"💚 **{f['nome']}** recuperou "
        f"**{recuperado} de HP**!\n\n"
        f"❤️ HP: **{novo_hp}/{f['hp_max']}**"
    )


# ============================================================
# GASTAR MANA
# ============================================================

@bot.tree.command(
    name="gastarmana",
    description="Gasta Mana da sua própria ficha."
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
        f"🔮 **{f['nome']}** gastou "
        f"**{valor} de Mana**!\n\n"
        f"🔵 Mana: **{nova_mana}/{f['mana_max']}**"
    )


# ============================================================
# RECUPERAR MANA
# ============================================================

@bot.tree.command(
    name="recuperarmana",
    description="Recupera Mana de um jogador."
)
@app_commands.describe(
    jogador="Jogador que recuperará Mana",
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
        f"💧 **{f['nome']}** recuperou "
        f"**{recuperado} de Mana**!\n\n"
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
            "❌ Ficha não encontrada.",
            ephemeral=True
        )

        return

    f = transformar_ficha(dados)

    if (
        f["dono_id"] != interaction.user.id
        and not eh_admin(interaction)
        and not eh_mestre(interaction)
    ):

        await interaction.response.send_message(
            "❌ Você não pode alterar "
            "o XP dessa ficha.",
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
        """
        SELECT xp
        FROM fichas
        WHERE id = ?
        """,
        (f["id"],)
    )

    xp_atual = cursor.fetchone()["xp"]

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
            "❌ Somente o Mestre pode "
            "criar NPCs.",
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

    colunas = (
        list(ATRIBUTOS.keys())
        + ORDEM_PERICIAS
    )

    valores = (
        [
            atributos[chave]
            for chave in ATRIBUTOS
        ]
        +
        [
            pericias[chave]
            for chave in ORDEM_PERICIAS
        ]
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
        + [
            aleatorio_valor
        ]
    )

    db.commit()

    ficha_id = cursor.lastrowid

    rc = (
        pericias["esquiva"]
        + atributos["destreza"]
        + 5
    )

    await interaction.response.send_message(
        f"👹 NPC **{nome}** criado!\n\n"
        f"ID da ficha: `{ficha_id}`\n"
        f"❤️ HP: **{hp}/{hp}**\n"
        f"🔵 Mana: **{mana}/{mana}**\n"
        f"⚡ RC: **{rc}**\n\n"
        f"🎲 Atributos e perícias "
        f"{'foram gerados aleatoriamente' if aleatorio_valor else 'começaram em 0'}."
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
            "❌ Somente o Mestre pode "
            "visualizar os NPCs.",
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

        f = transformar_ficha(dados)

        if primeiro:

            await interaction.response.send_message(
                embed=criar_pagina_status(f),
                view=FichaView(f),
                ephemeral=True
            )

            primeiro = False

        else:

            await interaction.followup.send(
                embed=criar_pagina_status(f),
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
    interaction: discord.Interaction,
    nome: str
):

    if (
        not eh_mestre(interaction)
        and not eh_admin(interaction)
    ):

        await interaction.response.send_message(
            "❌ Somente o Mestre pode "
            "apagar NPCs.",
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
        """
        DELETE FROM fichas
        WHERE id = ?
        """,
        (resultado["id"],)
    )

    db.commit()

    await interaction.response.send_message(
        f"🗑️ NPC **{nome}** apagado."
    )


# ============================================================
# AJUDA
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
            "`/verficha` — Ver ficha de outro jogador\n"
            "`/atributo` — Alterar seu atributo\n"
            "`/pericia` — Alterar sua perícia\n"
            "`/alterarficha` — Alterar HP/Mana\n"
            "`/apagarficha` — Apagar sua ficha\n"
            "`/gastarmana` — Gastar Mana\n"
            "`/cura` — Curar\n"
            "`/dano` — Aplicar dano\n"
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
            "`/alteraratributo` — Alterar atributo de qualquer ficha\n"
            "`/alterarpericia` — Alterar perícia de qualquer ficha\n"
            "`/passarmestre` — Passar Mestre\n"
            "`/mestre` — Ver Mestre"
        ),
        inline=False
    )

    embed.add_field(
        name="🛡️ Administrador",
        value=(
            "`/definirmestre` — Definir Mestre\n"
            "Administradores possuem controle total."
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
