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

def adicionar_coluna_se_nao_existir(nome_coluna):

    cursor.execute("PRAGMA table_info(fichas)")

    colunas = [
        coluna[1]
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

    adicionar_coluna_se_nao_existir(
        coluna
    )


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

    "forca": (
        "💪",
        "Força"
    ),

    "destreza": (
        "🏹",
        "Destreza"
    ),

    "vigor": (
        "🛡️",
        "Vigor"
    ),

    "inteligencia": (
        "🧠",
        "Inteligência"
    ),

    "carisma": (
        "🎭",
        "Carisma"
    ),

    "raciocinio": (
        "💡",
        "Raciocínio"
    )

}


# ============================================================
# PERÍCIAS
# ============================================================

PERICIAS = {

    "academicos": (
        "📚",
        "Acadêmicos"
    ),

    "idiomas": (
        "🗣️",
        "Idiomas"
    ),

    "oficios": (
        "🔧",
        "Ofícios"
    ),

    "armas_brancas": (
        "⚔️",
        "Armas Brancas"
    ),

    "intimidacao": (
        "😠",
        "Intimidação"
    ),

    "ocultismo": (
        "🔮",
        "Ocultismo"
    ),

    "briga": (
        "👊",
        "Briga"
    ),

    "investigacao": (
        "🔎",
        "Investigação"
    ),

    "persuasao": (
        "🤝",
        "Persuasão"
    ),

    "ciencias": (
        "🧪",
        "Ciências"
    ),

    "labia": (
        "💬",
        "Lábia"
    ),

    "prontidao": (
        "👁️",
        "Prontidão"
    ),

    "conhecimentos_gerais": (
        "🌎",
        "Conhec. Gerais"
    ),

    "lideranca": (
        "👑",
        "Liderança"
    ),

    "sobrevivencia": (
        "🏕️",
        "Sobrevivência"
    ),

    "conducao": (
        "🚗",
        "Condução"
    ),

    "manha": (
        "🕵️",
        "Manha"
    ),

    "tecnologia": (
        "💻",
        "Tecnologia"
    ),

    "esportes": (
        "🏃",
        "Esportes"
    ),

    "medicina": (
        "⚕️",
        "Medicina"
    ),

    "mira": (
        "🎯",
        "Mira"
    ),

    "esquiva": (
        "💨",
        "Esquiva"
    ),

    "furtividade": (
        "🥷",
        "Furtividade"
    )

}


ORDEM_PERICIAS = list(
    PERICIAS.keys()
)


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
    """, (
        channel_id,
    ))

    db.commit()


def obter_mestre(channel_id):

    cursor.execute("""
        SELECT mestre_id
        FROM mesas
        WHERE channel_id = ?
    """, (
        channel_id,
    ))

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
        obter_mestre(
            interaction.channel.id
        )
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
    """, (
        ficha_id,
    ))

    return cursor.fetchone()


def transformar_ficha(dados):

    if dados is None:
        return None

    colunas = [

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

    ficha = {}

    for indice, coluna in enumerate(colunas):

        if indice < len(dados):

            ficha[coluna] = dados[indice]

    return ficha


# ============================================================
# REFLEXO DE COMBATE
# ============================================================

def calcular_rc(ficha):

    return (
        ficha["esquiva"]
        +
        ficha["destreza"]
        +
        5
    )


# ============================================================
# ESTADO DE RECURSO
# ============================================================

def estado_recurso(
    atual,
    maximo
):

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
# TEXTO DE STATUS
# ============================================================

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
        f"{simbolos.get(estado, '⚪')} "
        f"{atual}/{maximo} — {estado}"
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
        f"{simbolos.get(estado, '⚪')} "
        f"{atual}/{maximo} — {estado}"
    )


# ============================================================
# TEXTO DOS ATRIBUTOS
# ============================================================

def texto_atributos(f):

    linhas = []

    itens = list(
        ATRIBUTOS.items()
    )

    largura = 15

    for i in range(
        0,
        len(itens),
        2
    ):

        chave1, (
            emoji1,
            nome1
        ) = itens[i]

        valor1 = f[chave1]

        esquerda = (
            f"{emoji1} "
            f"{nome1:<{largura}} "
            f"{valor1:>2}"
        )

        if i + 1 < len(itens):

            chave2, (
                emoji2,
                nome2
            ) = itens[i + 1]

            valor2 = f[chave2]

            direita = (
                f"{emoji2} "
                f"{nome2:<{largura}} "
                f"{valor2:>2}"
            )

            linhas.append(
                f"{esquerda}    {direita}"
            )

        else:

            linhas.append(
                esquerda
            )

    return "\n".join(
        linhas
    )


# ============================================================
# TEXTO DAS PERÍCIAS
# ============================================================

def texto_pericias(f):

    linhas = []

    itens = list(
        PERICIAS.items()
    )

    largura = 20

    for i in range(
        0,
        len(itens),
        2
    ):

        chave1, (
            emoji1,
            nome1
        ) = itens[i]

        valor1 = f[chave1]

        esquerda = (
            f"{emoji1} "
            f"{nome1:<{largura}} "
            f"{valor1:>2}"
        )

        if i + 1 < len(itens):

            chave2, (
                emoji2,
                nome2
            ) = itens[i + 1]

            valor2 = f[chave2]

            direita = (
                f"{emoji2} "
                f"{nome2:<{largura}} "
                f"{valor2:>2}"
            )

            linhas.append(
                f"{esquerda}    {direita}"
            )

        else:

            linhas.append(
                esquerda
            )

    return "\n".join(
        linhas
    )


# ============================================================
# PRIMEIRA PÁGINA
# STATUS + ATRIBUTOS
# ============================================================

def criar_pagina_status(
    f,
    jogador=None
):

    embed = discord.Embed(
        title=(
            f"📜 FICHA DE "
            f"{f['nome'].upper()}"
        ),
        color=discord.Color.dark_red()
    )

    if jogador:

        tipo = (
            f"Jogador: "
            f"{jogador.mention}"
        )

    else:

        tipo = "👹 NPC"

    embed.description = (

        f"{tipo}\n\n"

        f"❤️ STATUS\n\n"

        f"❤️ HP: "
        f"{mostrar_hp(f['hp_atual'], f['hp_max'])}\n"

        f"🔵 Mana: "
        f"{mostrar_mana(f['mana_atual'], f['mana_max'])}\n"

        f"✨ XP: {f['xp']}\n"

        f"⚡ RC: {calcular_rc(f)}\n\n"

        f"⚔️ ATRIBUTOS\n\n"

        f"```text\n"
        f"{texto_atributos(f)}\n"
        f"```"

    )

    embed.set_footer(
        text="Página 1/2 • Status e Atributos"
    )

    return embed


# ============================================================
# SEGUNDA PÁGINA
# PERÍCIAS
# ============================================================

def criar_pagina_pericias(f):

    embed = discord.Embed(
        title=(
            f"📚 PERÍCIAS — "
            f"{f['nome']}"
        ),
        color=discord.Color.dark_red()
    )

    embed.description = (

        "```text\n"
        f"{texto_pericias(f)}\n"
        "```"

    )

    embed.set_footer(
        text="Página 2/2 • Perícias"
    )

    return embed


# ============================================================
# PAGINAÇÃO DA FICHA
# ============================================================

class FichaView(
    discord.ui.View
):

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
        label="Status",
        emoji="◀",
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
        label="Perícias",
        emoji="▶",
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
        f"👑 {jogador.mention} "
        f"agora é o Mestre deste canal!"
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
    interaction,
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
    interaction
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
            f"👑 Mestre: {membro.mention}"
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

            ?,
            ?,
            NULL,
            'jogador',
            ?,

            ?,
            ?,

            ?,
            ?,

            0,

            0,
            0,
            0,
            0,
            0,
            0,

            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,

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
        f"⚡ RC: 5\n\n"

        f"Use /editarficha para definir "
        f"atributos e perícias."

    )


# ============================================================
# MOSTRAR PRÓPRIA FICHA
# ============================================================

@bot.tree.command(
    name="ficha",
    description="Mostra sua ficha."
)
async def ficha(
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

    f = transformar_ficha(
        dados
    )

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
            f"❌ {jogador.display_name} "
            f"não possui uma ficha.",
            ephemeral=True
        )

        return

    f = transformar_ficha(
        dados
    )

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
# ALTERAR FICHA — MODAL
# ============================================================

class AlterarValorModal(
    discord.ui.Modal
):

    def __init__(
        self,
        ficha_id,
        ficha,
        tipo,
        chave,
        nome_exibicao
    ):

        super().__init__(
            title=f"Alterar {nome_exibicao}"
        )

        self.ficha_id = ficha_id

        self.ficha = ficha

        self.tipo = tipo

        self.chave = chave

        self.nome_exibicao = nome_exibicao

        self.valor = discord.ui.TextInput(

            label="Novo valor",

            placeholder="Digite o novo valor",

            required=True,

            min_length=1,

            max_length=5

        )

        self.add_item(
            self.valor
        )


    async def on_submit(
        self,
        interaction
    ):

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

        # ====================================================
        # PERMISSÕES
        # ====================================================

        eh_dono = (
            f["tipo"] == "jogador"
            and
            f["dono_id"]
            == interaction.user.id
        )

        eh_mestre_usuario = (
            eh_mestre(interaction)
        )

        eh_administrador = (
            eh_admin(interaction)
        )

        if not (
            eh_dono
            or
            eh_mestre_usuario
            or
            eh_administrador
        ):

            await interaction.response.send_message(
                "❌ Você não possui permissão "
                "para alterar essa ficha.",
                ephemeral=True
            )

            return

        # ====================================================
        # CONVERTER VALOR
        # ====================================================

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

        if valor < 0:

            await interaction.response.send_message(
                "❌ O valor não pode ser negativo.",
                ephemeral=True
            )

            return

        # ====================================================
        # ALTERAR ATRIBUTO
        # ====================================================

        if self.tipo == "atributo":

            if self.chave not in ATRIBUTOS:

                await interaction.response.send_message(
                    "❌ Atributo inválido.",
                    ephemeral=True
                )

                return

            cursor.execute(
                f"""
                UPDATE fichas
                SET {self.chave} = ?
                WHERE id = ?
                """,
                (
                    valor,
                    self.ficha_id
                )
            )

            db.commit()

            await interaction.response.send_message(

                f"⚔️ Ficha atualizada!\n\n"

                f"📜 Ficha: {f['nome']}\n"

                f"⚔️ {self.nome_exibicao}: "
                f"{valor}"

            )

            return

        # ====================================================
        # ALTERAR PERÍCIA
        # ====================================================

        if self.tipo == "pericia":

            if self.chave not in PERICIAS:

                await interaction.response.send_message(
                    "❌ Perícia inválida.",
                    ephemeral=True
                )

                return

            cursor.execute(
                f"""
                UPDATE fichas
                SET {self.chave} = ?
                WHERE id = ?
                """,
                (
                    valor,
                    self.ficha_id
                )
            )

            db.commit()

            await interaction.response.send_message(

                f"📚 Ficha atualizada!\n\n"

                f"📜 Ficha: {f['nome']}\n"

                f"📚 {self.nome_exibicao}: "
                f"{valor}"

            )


# ============================================================
# SELEÇÃO DE ATRIBUTO
# ============================================================

class AtributoSelect(
    discord.ui.Select
):

    def __init__(
        self,
        ficha_id,
        ficha
    ):

        self.ficha_id = ficha_id

        self.ficha = ficha

        opcoes = []

        for chave, (
            emoji,
            nome
        ) in ATRIBUTOS.items():

            opcoes.append(
                discord.SelectOption(

                    label=nome,

                    value=chave,

                    emoji=emoji,

                    description=(
                        f"Atual: "
                        f"{ficha[chave]}"
                    )

                )
            )

        super().__init__(

            placeholder=(
                "⚔️ Escolha um atributo..."
            ),

            min_values=1,

            max_values=1,

            options=opcoes

        )


    async def callback(
        self,
        interaction
    ):

        chave = self.values[0]

        nome = ATRIBUTOS[
            chave
        ][1]

        await interaction.response.send_modal(

            AlterarValorModal(

                self.ficha_id,

                self.ficha,

                "atributo",

                chave,

                nome

            )
        )


# ============================================================
# VIEW DE ATRIBUTOS
# ============================================================

class EscolherAtributoView(
    discord.ui.View
):

    def __init__(
        self,
        ficha_id,
        ficha
    ):

        super().__init__(
            timeout=120
        )

        self.add_item(
            AtributoSelect(
                ficha_id,
                ficha
            )
        )


# ============================================================
# SELEÇÃO DE PERÍCIA
# ============================================================

class PericiaSelect(
    discord.ui.Select
):

    def __init__(
        self,
        ficha_id,
        ficha,
        pagina=0
    ):

        self.ficha_id = ficha_id

        self.ficha = ficha

        self.pagina = pagina

        todas = list(
            PERICIAS.items()
        )

        inicio = pagina * 25

        fim = inicio + 25

        itens = todas[
            inicio:fim
        ]

        opcoes = []

        for chave, (
            emoji,
            nome
        ) in itens:

            opcoes.append(
                discord.SelectOption(

                    label=nome,

                    value=chave,

                    emoji=emoji,

                    description=(
                        f"Atual: "
                        f"{ficha[chave]}"
                    )

                )
            )

        super().__init__(

            placeholder=(
                "📚 Escolha uma perícia..."
            ),

            min_values=1,

            max_values=1,

            options=opcoes

        )


    async def callback(
        self,
        interaction
    ):

        chave = self.values[0]

        nome = PERICIAS[
            chave
        ][1]

        await interaction.response.send_modal(

            AlterarValorModal(

                self.ficha_id,

                self.ficha,

                "pericia",

                chave,

                nome

            )
        )


# ============================================================
# VIEW DE PERÍCIAS
# ============================================================

class EscolherPericiaView(
    discord.ui.View
):

    def __init__(
        self,
        ficha_id,
        ficha,
        pagina=0
    ):

        super().__init__(
            timeout=120
        )

        self.ficha_id = ficha_id

        self.ficha = ficha

        self.pagina = pagina

        self.atualizar()


    def atualizar(self):

        self.clear_items()

        self.add_item(
            PericiaSelect(
                self.ficha_id,
                self.ficha,
                self.pagina
            )
        )

        total = len(
            PERICIAS
        )

        total_paginas = (
            (total - 1) // 25
        ) + 1

        if self.pagina > 0:

            self.add_item(
                BotaoPericiaAnterior(
                    self
                )
            )

        if self.pagina < (
            total_paginas - 1
        ):

            self.add_item(
                BotaoPericiaProxima(
                    self
                )
            )


# ============================================================
# BOTÃO PERÍCIA ANTERIOR
# ============================================================

class BotaoPericiaAnterior(
    discord.ui.Button
):

    def __init__(
        self,
        view_original
    ):

        self.view_original = (
            view_original
        )

        super().__init__(
            label="Anterior",
            emoji="◀",
            style=discord.ButtonStyle.secondary
        )


    async def callback(
        self,
        interaction
    ):

        self.view_original.pagina -= 1

        self.view_original.atualizar()

        await interaction.response.edit_message(
            view=self.view_original
        )


# ============================================================
# BOTÃO PRÓXIMA PERÍCIA
# ============================================================

class BotaoPericiaProxima(
    discord.ui.Button
):

    def __init__(
        self,
        view_original
    ):

        self.view_original = (
            view_original
        )

        super().__init__(
            label="Próxima",
            emoji="▶",
            style=discord.ButtonStyle.secondary
        )


    async def callback(
        self,
        interaction
    ):

        self.view_original.pagina += 1

        self.view_original.atualizar()

        await interaction.response.edit_message(
            view=self.view_original
        )


# ============================================================
# ESCOLHER O TIPO DE EDIÇÃO
# ============================================================

class EscolherTipoEdicaoView(
    discord.ui.View
):

    def __init__(
        self,
        ficha_id,
        ficha
    ):

        super().__init__(
            timeout=120
        )

        self.ficha_id = ficha_id

        self.ficha = ficha


    @discord.ui.button(
        label="Atributo",
        emoji="⚔️",
        style=discord.ButtonStyle.primary
    )
    async def atributo(
        self,
        interaction,
        button
    ):

        await interaction.response.edit_message(

            content=(
                f"📜 Ficha: {self.ficha['nome']}\n\n"
                f"⚔️ Escolha o atributo:"
            ),

            view=EscolherAtributoView(
                self.ficha_id,
                self.ficha
            )

        )


    @discord.ui.button(
        label="Perícia",
        emoji="📚",
        style=discord.ButtonStyle.primary
    )
    async def pericia(
        self,
        interaction,
        button
    ):

        await interaction.response.edit_message(

            content=(
                f"📜 Ficha: {self.ficha['nome']}\n\n"
                f"📚 Escolha a perícia:"
            ),

            view=EscolherPericiaView(
                self.ficha_id,
                self.ficha
            )

        )


# ============================================================
# SELEÇÃO DE FICHA DO MESTRE
# ============================================================

class FichaSelect(
    discord.ui.Select
):

    def __init__(
        self,
        fichas
    ):

        opcoes = []

        for (
            ficha_id,
            nome,
            tipo
        ) in fichas:

            if tipo == "jogador":

                emoji = "👤"

                descricao = "Jogador"

            else:

                emoji = "👹"

                descricao = "NPC"

            opcoes.append(

                discord.SelectOption(

                    label=nome[:100],

                    value=str(
                        ficha_id
                    ),

                    emoji=emoji,

                    description=descricao

                )

            )

        super().__init__(

            placeholder=(
                "📜 Escolha a ficha..."
            ),

            min_values=1,

            max_values=1,

            options=opcoes

        )


    async def callback(
        self,
        interaction
    ):

        ficha_id = int(
            self.values[0]
        )

        dados = buscar_ficha(
            ficha_id
        )

        if dados is None:

            await interaction.response.send_message(
                "❌ Ficha não encontrada.",
                ephemeral=True
            )

            return

        ficha = transformar_ficha(
            dados
        )

        await interaction.response.edit_message(

            content=(

                f"📜 Ficha selecionada: "
                f"{ficha['nome']}\n\n"

                f"Escolha o que deseja alterar:"

            ),

            view=EscolherTipoEdicaoView(
                ficha_id,
                ficha
            )

        )


# ============================================================
# VIEW PARA ESCOLHER FICHA
# ============================================================

class EscolherFichaView(
    discord.ui.View
):

    def __init__(
        self,
        fichas
    ):

        super().__init__(
            timeout=120
        )

        self.add_item(
            FichaSelect(
                fichas
            )
        )


# ============================================================
# EDITAR FICHA
# ============================================================

@bot.tree.command(
    name="editarficha",
    description="Edita sua ficha ou, como Mestre, qualquer ficha."
)
async def editarficha(
    interaction
):

    # ========================================================
    # MESTRE / ADMINISTRADOR
    # ========================================================

    if (
        eh_mestre(interaction)
        or
        eh_admin(interaction)
    ):

        cursor.execute("""
            SELECT
                id,
                nome,
                tipo
            FROM fichas
            WHERE channel_id = ?
            ORDER BY tipo, nome
        """, (
            interaction.channel.id,
        ))

        fichas = cursor.fetchall()

        if not fichas:

            await interaction.response.send_message(
                "❌ Não existem fichas neste canal.",
                ephemeral=True
            )

            return

        # Discord permite no máximo 25
        # opções por Select.

        if len(fichas) > 25:

            fichas = fichas[:25]

        await interaction.response.send_message(

            "📜 EDITOR DE FICHAS\n\n"
            "Escolha a ficha que deseja editar:",

            view=EscolherFichaView(
                fichas
            ),

            ephemeral=True
        )

        return

    # ========================================================
    # JOGADOR
    # ========================================================

    dados = buscar_ficha_jogador(

        interaction.channel.id,

        interaction.user.id

    )

    if dados is None:

        await interaction.response.send_message(

            "❌ Você ainda não possui uma ficha.\n\n"
            "Use /criarficha para criar uma.",

            ephemeral=True

        )

        return

    ficha = transformar_ficha(
        dados
    )

    await interaction.response.send_message(

        f"📜 Sua ficha: "
        f"{ficha['nome']}\n\n"

        f"O que deseja alterar?",

        view=EscolherTipoEdicaoView(

            ficha["id"],

            ficha

        ),

        ephemeral=True

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
            "❌ Esse jogador não possui ficha.",
            ephemeral=True
        )

        return

    f = transformar_ficha(
        dados
    )

    permitido = (

        f["dono_id"]
        == interaction.user.id

        or

        eh_mestre(interaction)

        or

        eh_admin(interaction)

    )

    if not permitido:

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

        SET
            hp_atual = ?,
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

        f"⚙️ Ficha de {f['nome']} atualizada!\n\n"

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

    f = transformar_ficha(
        dados
    )

    cursor.execute(
        "DELETE FROM fichas WHERE id = ?",
        (
            f["id"],
        )
    )

    db.commit()

    await interaction.response.send_message(

        f"🗑️ A ficha {f['nome']} "
        f"foi apagada."

    )


# ============================================================
# DANO
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

    f = transformar_ficha(
        dados
    )

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

        f"💥 {f['nome']} recebeu "
        f"{valor} de dano!\n\n"

        f"❤️ HP: "
        f"{novo_hp}/{f['hp_max']}"

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
    interaction,
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

    f = transformar_ficha(
        dados
    )

    novo_hp = min(

        f["hp_max"],

        f["hp_atual"] + valor

    )

    recuperado = (
        novo_hp
        -
        f["hp_atual"]
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

        f"💚 {f['nome']} recuperou "
        f"{recuperado} de HP!\n\n"

        f"❤️ HP: "
        f"{novo_hp}/{f['hp_max']}"

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

    f = transformar_ficha(
        dados
    )

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
        f["mana_atual"]
        -
        valor
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

        f"🔮 {f['nome']} gastou "
        f"{valor} de Mana!\n\n"

        f"🔵 Mana: "
        f"{nova_mana}/{f['mana_max']}"

    )


# ============================================================
# RECUPERAR MANA
# ============================================================

@bot.tree.command(
    name="recuperarmana",
    description="Recupera Mana de um jogador."
)
@app_commands.describe(
    jogador="Jogador",
    valor="Quantidade de Mana"
)
async def recuperarmana(
    interaction,
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

    f = transformar_ficha(
        dados
    )

    nova_mana = min(

        f["mana_max"],

        f["mana_atual"] + valor

    )

    recuperado = (
        nova_mana
        -
        f["mana_atual"]
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

        f"💧 {f['nome']} recuperou "
        f"{recuperado} de Mana!\n\n"

        f"🔵 Mana: "
        f"{nova_mana}/{f['mana_max']}"

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

    f = transformar_ficha(
        dados
    )

    permitido = (

        f["dono_id"]
        == interaction.user.id

        or

        eh_mestre(interaction)

        or

        eh_admin(interaction)

    )

    if not permitido:

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
        (
            f["id"],
        )
    )

    xp_atual = cursor.fetchone()[0]

    await interaction.response.send_message(

        f"✨ {f['nome']} recebeu "
        f"{valor} XP!\n\n"

        f"✨ XP atual: "
        f"{xp_atual}"

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
        and
        not eh_admin(interaction)
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

        atributos = {}

        for chave in ATRIBUTOS:

            atributos[chave] = random.randint(
                0,
                5
            )

        pericias = {}

        for chave in PERICIAS:

            pericias[chave] = random.randint(
                0,
                5
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
                "❌ Informe o HP.",
                ephemeral=True
            )

            return

        if mana is None:

            await interaction.response.send_message(
                "❌ Informe a Mana.",
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

        list(
            ATRIBUTOS.keys()
        )
        +
        list(
            PERICIAS.keys()
        )

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

            ?,
            NULL,
            ?,
            'npc',
            ?,

            ?,
            ?,

            ?,
            ?,

            0,

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

        +

        valores

        +

        [

            aleatorio_valor

        ]

    )

    db.commit()

    rc = (

        pericias["esquiva"]
        +
        atributos["destreza"]
        +
        5

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
    interaction
):

    if (
        not eh_mestre(interaction)
        and
        not eh_admin(interaction)
    ):

        await interaction.response.send_message(
            "❌ Somente o Mestre pode visualizar NPCs.",
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

    primeira = True

    for dados in resultados:

        f = transformar_ficha(
            dados
        )

        embed = criar_pagina_status(
            f
        )

        view = FichaView(
            f
        )

        if primeira:

            await interaction.response.send_message(
                embed=embed,
                view=view,
                ephemeral=True
            )

            primeira = False

        else:

            await interaction.followup.send(
                embed=embed,
                view=view,
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
        and
        not eh_admin(interaction)
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

        (
            resultado[0],
        )

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
    interaction
):

    embed = discord.Embed(

        title="📖 BotRPG",

        description=(
            "Comandos disponíveis:"
        ),

        color=discord.Color.dark_red()

    )

    embed.add_field(

        name="👤 Jogador",

        value=(

            "/criarficha — Criar ficha\n"

            "/ficha — Ver sua ficha\n"

            "/verficha — Ver outra ficha\n"

            "/editarficha — Editar sua ficha\n"

            "/alterarficha — Alterar HP/Mana\n"

            "/apagarficha — Apagar ficha\n"

            "/gastarmana — Gastar Mana\n"

            "/cura — Curar\n"

            "/dano — Aplicar dano\n"

            "/recuperarmana — Recuperar Mana\n"

            "/addxp — Adicionar XP"

        ),

        inline=False

    )

    embed.add_field(

        name="👑 Mestre",

        value=(

            "/editarficha — Editar qualquer ficha\n"

            "/criarnpc — Criar NPC\n"

            "/npcs — Ver NPCs\n"

            "/apagarnpc — Apagar NPC\n"

            "/passarmestre — Passar Mestre\n"

            "/mestre — Ver Mestre"

        ),

        inline=False

    )

    embed.add_field(

        name="🛡️ Administrador",

        value=(

            "/definirmestre — Definir Mestre\n"

            "Administradores podem editar fichas "
            "e NPCs."

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
