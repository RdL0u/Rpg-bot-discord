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
# MIGRAÇÃO DO BANCO ANTIGO
# ============================================================

COLUNAS_OBRIGATORIAS = {
    "mesas": {
        "channel_id": "INTEGER PRIMARY KEY",
        "mestre_id": "INTEGER"
    },

    "fichas": {
        "channel_id": "INTEGER NOT NULL DEFAULT 0",
        "dono_id": "INTEGER",
        "mestre_id": "INTEGER",
        "tipo": "TEXT NOT NULL DEFAULT 'jogador'",
        "nome": "TEXT NOT NULL DEFAULT 'Personagem'",

        "hp_atual": "INTEGER NOT NULL DEFAULT 0",
        "hp_max": "INTEGER NOT NULL DEFAULT 0",

        "mana_atual": "INTEGER NOT NULL DEFAULT 0",
        "mana_max": "INTEGER NOT NULL DEFAULT 0",

        "xp": "INTEGER NOT NULL DEFAULT 0",

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
        "furtividade": "INTEGER NOT NULL DEFAULT 0",

        "aleatorio": "INTEGER NOT NULL DEFAULT 0"
    }
}


def adicionar_colunas_faltantes(tabela, colunas):

    cursor.execute(f"PRAGMA table_info({tabela})")

    existentes = {
        coluna[1]
        for coluna in cursor.fetchall()
    }

    for nome_coluna, definicao in colunas.items():

        if nome_coluna not in existentes:

            # SQLite não aceita PRIMARY KEY em ALTER TABLE.
            if "PRIMARY KEY" in definicao:
                definicao = "INTEGER"

            cursor.execute(
                f"""
                ALTER TABLE {tabela}
                ADD COLUMN {nome_coluna} {definicao}
                """
            )

    db.commit()


adicionar_colunas_faltantes(
    "fichas",
    COLUNAS_OBRIGATORIAS["fichas"]
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
    "forca": ("💪", "Força", "For"),
    "destreza": ("🏹", "Destreza", "Des"),
    "vigor": ("🛡️", "Vigor", "Vig"),
    "inteligencia": ("🧠", "Inteligência", "Int"),
    "carisma": ("🎭", "Carisma", "Car"),
    "raciocinio": ("💡", "Raciocínio", "Rac")
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


def buscar_ficha_por_id(ficha_id):

    cursor.execute("""
        SELECT *
        FROM fichas
        WHERE id = ?
    """, (ficha_id,))

    return cursor.fetchone()


def buscar_npc(channel_id, nome):

    cursor.execute("""
        SELECT *
        FROM fichas
        WHERE channel_id = ?
        AND tipo = 'npc'
        AND LOWER(nome) = LOWER(?)
        LIMIT 1
    """, (
        channel_id,
        nome.strip()
    ))

    return cursor.fetchone()


def buscar_ficha_alvo(
    interaction,
    jogador=None,
    npc=None
):

    if jogador is not None:

        return buscar_ficha_jogador(
            interaction.channel.id,
            jogador.id
        )

    if npc:

        return buscar_npc(
            interaction.channel.id,
            npc
        )

    return buscar_ficha_jogador(
        interaction.channel.id,
        interaction.user.id
    )


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


def atualizar_ficha_do_banco(ficha_id, coluna, valor):

    colunas_permitidas = (
        set(ATRIBUTOS.keys())
        | set(PERICIAS.keys())
    )

    if coluna not in colunas_permitidas:
        raise ValueError("Coluna inválida.")

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


# ============================================================
# REFLEXO DE COMBATE
# RC = ESQUIVA + DESTREZA + 5
# ============================================================

def calcular_rc(ficha):

    return (
        ficha["esquiva"]
        + ficha["destreza"]
        + 5
    )


# ============================================================
# ESTADO DE RECURSOS
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


def emoji_estado_hp(atual, maximo):

    estado = estado_recurso(
        atual,
        maximo
    )

    return {
        "BOM": "🟢",
        "BAIXO": "🟡",
        "CRÍTICO": "🔴",
        "ZERADO": "⚫"
    }.get(
        estado,
        "⚪"
    )


def emoji_estado_mana(atual, maximo):

    estado = estado_recurso(
        atual,
        maximo
    )

    return {
        "BOM": "🔵",
        "BAIXO": "🟡",
        "CRÍTICO": "🔴",
        "ZERADO": "⚫"
    }.get(
        estado,
        "⚪"
    )


# ============================================================
# PERMISSÃO PARA ALTERAR FICHA
# ============================================================

def pode_alterar_ficha(interaction, ficha):

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
        )

    return False


# ============================================================
# ALVO DA FICHA
# ============================================================

def texto_tipo_ficha(ficha):

    if ficha["tipo"] == "npc":
        return "👹 NPC"

    return "👤 Jogador"


def obter_membro_dono(ficha, guild):

    if ficha["tipo"] != "jogador":
        return None

    if ficha["dono_id"] is None:
        return None

    return guild.get_member(
        ficha["dono_id"]
    )


# ============================================================
# TEXTO DOS ATRIBUTOS
# ============================================================

def texto_atributos_bloco(f):

    valores = []

    for chave, dados in ATRIBUTOS.items():

        emoji = dados[0]
        abreviacao = dados[2]

        valores.append(
            (
                f"{emoji} {abreviacao}",
                f"{f[chave]}"
            )
        )

    linhas = []

    largura_nome = 8

    for i in range(0, len(valores), 2):

        esquerda = valores[i]

        direita = valores[i + 1]

        nome_e = esquerda[0]
        valor_e = esquerda[1]

        nome_d = direita[0]
        valor_d = direita[1]

        linha = (
            f"{nome_e:<{largura_nome}} "
            f"{valor_e:<5}"
            f"    "
            f"{nome_d:<{largura_nome}} "
            f"{valor_d}"
        )

        linhas.append(linha)

    return "\n".join(linhas)


# ============================================================
# TEXTO DAS PERÍCIAS
# ============================================================

def texto_pericias_bloco(f):

    valores = []

    for chave in ORDEM_PERICIAS:

        emoji, nome = PERICIAS[chave]

        valores.append(
            (
                f"{emoji} {nome}",
                str(f[chave])
            )
        )

    linhas = []

    largura_coluna = 20

    for i in range(0, len(valores), 2):

        esquerda = valores[i]

        nome_e = esquerda[0]
        valor_e = esquerda[1]

        if i + 1 < len(valores):

            direita = valores[i + 1]

            nome_d = direita[0]
            valor_d = direita[1]

            linha = (
                f"{nome_e:<{largura_coluna}} "
                f"{valor_e:<3}"
                f"    "
                f"{nome_d:<{largura_coluna}} "
                f"{valor_d}"
            )

        else:

            linha = (
                f"{nome_e:<{largura_coluna}} "
                f"{valor_e}"
            )

        linhas.append(linha)

    return "\n".join(linhas)


# ============================================================
# PÁGINA DE STATUS E ATRIBUTOS
# ============================================================

def criar_pagina_status(f, jogador=None):

    embed = discord.Embed(
        title=f"📜 FICHA — {f['nome'].upper()}",
        color=discord.Color.dark_red()
    )

    if f["tipo"] == "jogador":

        if jogador:

            identificacao = (
                f"👤 Jogador: {jogador.mention}"
            )

        else:

            identificacao = (
                f"👤 Jogador: <@{f['dono_id']}>"
            )

    else:

        identificacao = "👹 NPC"

    hp_estado = (
        f"{emoji_estado_hp(f['hp_atual'], f['hp_max'])} "
        f"{f['hp_atual']}/{f['hp_max']}"
    )

    mana_estado = (
        f"{emoji_estado_mana(f['mana_atual'], f['mana_max'])} "
        f"{f['mana_atual']}/{f['mana_max']}"
    )

    status_bloco = (
        "❤️ STATUS\n\n"
        f"❤️ HP        {hp_estado:<12} "
        f"🔵 Mana      {mana_estado}\n"
        f"✨ XP        {f['xp']:<12} "
        f"⚡ RC        {calcular_rc(f)}"
    )

    atributos_bloco = (
        "⚔️ ATRIBUTOS\n\n"
        f"{texto_atributos_bloco(f)}"
    )

    embed.description = (
        f"{identificacao}\n\n"
        f"~~~\n"
        f"{status_bloco}\n\n"
        f"{atributos_bloco}\n"
        f"~~~"
    )

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
        "~~~\n"
        "📚 PERÍCIAS\n\n"
        f"{texto_pericias_bloco(f)}\n"
        "~~~"
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

        super().__init__(
            timeout=180
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

        # Atualiza os dados antes de mostrar
        dados = buscar_ficha_por_id(
            self.ficha["id"]
        )

        if dados:

            self.ficha = transformar_ficha(
                dados
            )

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

        dados = buscar_ficha_por_id(
            self.ficha["id"]
        )

        if dados:

            self.ficha = transformar_ficha(
                dados
            )

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
        f"👑 **{jogador.display_name}** agora é o Mestre deste canal!\n\n"
        f"👹 Os NPCs existentes também foram atribuídos a ele."
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
            "❌ Somente o Mestre atual ou um administrador pode passar o cargo.",
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
        f"👹 Todos os NPCs deste canal foram transferidos."
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
            "👑 Este canal ainda não possui um Mestre."
        )

        return

    membro = interaction.guild.get_member(
        mestre_id
    )

    if membro:

        await interaction.response.send_message(
            f"👑 Mestre deste canal: **{membro.display_name}**"
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
        VALUES (
            ?, ?, NULL, 'jogador', ?,
            ?, ?, ?, ?, 0
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
        f"❤️ HP: **{hp}/{hp}**\n"
        f"🔵 Mana: **{mana}/{mana}**\n"
        f"✨ XP: **0**\n"
        f"⚡ RC: **5**"
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
            "❌ Você não possui uma ficha neste canal.",
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
    jogador="Jogador cuja ficha deseja visualizar"
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
            f"❌ **{jogador.display_name}** não possui uma ficha neste canal.",
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
# ALTERAR ATRIBUTO
#
# Jogador:
# /atributo atributo valor
#
# Mestre/Admin:
# /atributo atributo valor jogador:@Pessoa
# ou
# /atributo atributo valor npc:"Nome do NPC"
# ============================================================

@bot.tree.command(
    name="atributo",
    description="Altera um atributo da sua ficha ou de outra ficha."
)
@app_commands.describe(
    atributo="Atributo que será alterado",
    valor="Novo valor",
    jogador="Opcional: jogador cuja ficha será alterada",
    npc="Opcional: nome exato do NPC"
)
@app_commands.choices(
    atributo=[
        app_commands.Choice(
            name="💪 Força",
            value="forca"
        ),
        app_commands.Choice(
            name="🏹 Destreza",
            value="destreza"
        ),
        app_commands.Choice(
            name="🛡️ Vigor",
            value="vigor"
        ),
        app_commands.Choice(
            name="🧠 Inteligência",
            value="inteligencia"
        ),
        app_commands.Choice(
            name="🎭 Carisma",
            value="carisma"
        ),
        app_commands.Choice(
            name="💡 Raciocínio",
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

    if jogador is not None and npc is not None:

        await interaction.response.send_message(
            "❌ Escolha jogador OU NPC, não os dois.",
            ephemeral=True
        )

        return

    dados = buscar_ficha_alvo(
        interaction,
        jogador,
        npc
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

    # Se o alvo é outra pessoa/NPC,
    # somente Mestre ou Admin pode alterar.
    alvo_diferente = (
        jogador is not None
        or npc is not None
    )

    if alvo_diferente:

        if (
            not eh_mestre(interaction)
            and not eh_admin(interaction)
        ):

            await interaction.response.send_message(
                "❌ Somente o Mestre ou administrador pode alterar a ficha de outra pessoa ou de um NPC.",
                ephemeral=True
            )

            return

    else:

        if not pode_alterar_ficha(
            interaction,
            f
        ):

            await interaction.response.send_message(
                "❌ Você não pode alterar essa ficha.",
                ephemeral=True
            )

            return

    atualizar_ficha_do_banco(
        f["id"],
        atributo.value,
        valor
    )

    emoji, nome_atributo, abreviacao = ATRIBUTOS[
        atributo.value
    ]

    await interaction.response.send_message(
        f"{emoji} **{nome_atributo}** de **{f['nome']}** "
        f"alterado para **{valor}**."
    )


# ============================================================
# ALTERAR PERÍCIA
#
# Jogador:
# /pericia pericia valor
#
# Mestre/Admin:
# /pericia pericia valor jogador:@Pessoa
# ou
# /pericia pericia valor npc:"Nome do NPC"
#
# IMPORTANTE:
# A coluna visual NÃO determina a coluna do banco.
# A chave escolhida é usada diretamente.
# ============================================================

@bot.tree.command(
    name="pericia",
    description="Altera uma perícia da sua ficha ou de outra ficha."
)
@app_commands.describe(
    pericia="Perícia que será alterada",
    valor="Novo valor",
    jogador="Opcional: jogador cuja ficha será alterada",
    npc="Opcional: nome exato do NPC"
)
@app_commands.choices(
    pericia=[
        app_commands.Choice(name="📚 Acadêmicos", value="academicos"),
        app_commands.Choice(name="🗣️ Idiomas", value="idiomas"),
        app_commands.Choice(name="🔧 Ofícios", value="oficios"),
        app_commands.Choice(name="⚔️ Armas Brancas", value="armas_brancas"),
        app_commands.Choice(name="😠 Intimidação", value="intimidacao"),
        app_commands.Choice(name="🔮 Ocultismo", value="ocultismo"),
        app_commands.Choice(name="👊 Briga", value="briga"),
        app_commands.Choice(name="🔎 Investigação", value="investigacao"),
        app_commands.Choice(name="🤝 Persuasão", value="persuasao"),
        app_commands.Choice(name="🧪 Ciências", value="ciencias"),
        app_commands.Choice(name="💬 Lábia", value="labia"),
        app_commands.Choice(name="👁️ Prontidão", value="prontidao"),
        app_commands.Choice(name="🌎 Conhec. Gerais", value="conhecimentos_gerais"),
        app_commands.Choice(name="👑 Liderança", value="lideranca"),
        app_commands.Choice(name="🏕️ Sobrevivência", value="sobrevivencia"),
        app_commands.Choice(name="🚗 Condução", value="conducao"),
        app_commands.Choice(name="🕵️ Manha", value="manha"),
        app_commands.Choice(name="💻 Tecnologia", value="tecnologia"),
        app_commands.Choice(name="🏃 Esportes", value="esportes"),
        app_commands.Choice(name="⚕️ Medicina", value="medicina"),
        app_commands.Choice(name="🎯 Mira", value="mira"),
        app_commands.Choice(name="💨 Esquiva", value="esquiva"),
        app_commands.Choice(name="🥷 Furtividade", value="furtividade")
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

    if jogador is not None and npc is not None:

        await interaction.response.send_message(
            "❌ Escolha jogador OU NPC, não os dois.",
            ephemeral=True
        )

        return

    dados = buscar_ficha_alvo(
        interaction,
        jogador,
        npc
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

    alvo_diferente = (
        jogador is not None
        or npc is not None
    )

    if alvo_diferente:

        if (
            not eh_mestre(interaction)
            and not eh_admin(interaction)
        ):

            await interaction.response.send_message(
                "❌ Somente o Mestre ou administrador pode alterar a ficha de outra pessoa ou de um NPC.",
                ephemeral=True
            )

            return

    else:

        if not pode_alterar_ficha(
            interaction,
            f
        ):

            await interaction.response.send_message(
                "❌ Você não pode alterar essa ficha.",
                ephemeral=True
            )

            return

    # CORREÇÃO DEFINITIVA:
    # usa diretamente a chave da perícia.
    # Não usa posição da coluna visual.
    atualizar_ficha_do_banco(
        f["id"],
        pericia.value,
        valor
    )

    emoji, nome_pericia = PERICIAS[
        pericia.value
    ]

    await interaction.response.send_message(
        f"{emoji} **{nome_pericia}** de **{f['nome']}** "
        f"alterada para **{valor}**."
    )


# ============================================================
# ALTERAR HP E MANA MÁXIMOS
# ============================================================

@bot.tree.command(
    name="alterarficha",
    description="Altera HP e Mana máximos de uma ficha."
)
@app_commands.describe(
    jogador="Jogador cuja ficha será alterada",
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

    f = transformar_ficha(
        dados
    )

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
# APAGAR FICHA DO JOGADOR
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
            "❌ Você não possui uma ficha.",
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
        f"🗑️ A ficha **{f['nome']}** foi apagada."
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
    valor="Quantidade de dano",
    npc="Opcional: nome exato do NPC"
)
async def dano(
    interaction: discord.Interaction,
    valor: int,
    jogador: discord.Member = None,
    npc: str = None
):

    if jogador is not None and npc is not None:

        await interaction.response.send_message(
            "❌ Escolha jogador OU NPC.",
            ephemeral=True
        )

        return

    if jogador is None and npc is None:

        jogador = interaction.user

    dados = buscar_ficha_alvo(
        interaction,
        jogador,
        npc
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
        f"💥 **{f['nome']}** recebeu **{valor} de dano**!\n\n"
        f"❤️ HP: **{novo_hp}/{f['hp_max']}**"
    )


# ============================================================
# CURA
#
# Pode curar:
# - própria ficha
# - outro jogador
# - NPC
# ============================================================

@bot.tree.command(
    name="cura",
    description="Cura um jogador ou NPC."
)
@app_commands.describe(
    valor="Quantidade de cura",
    jogador="Jogador que receberá a cura",
    npc="Nome exato do NPC que receberá a cura"
)
async def cura(
    interaction: discord.Interaction,
    valor: int,
    jogador: discord.Member = None,
    npc: str = None
):

    if jogador is not None and npc is not None:

        await interaction.response.send_message(
            "❌ Escolha jogador OU NPC.",
            ephemeral=True
        )

        return

    if jogador is None and npc is None:

        jogador = interaction.user

    dados = buscar_ficha_alvo(
        interaction,
        jogador,
        npc
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
        f"💚 **{f['nome']}** recuperou **{recuperado} de HP**!\n\n"
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
        f"🔮 **{f['nome']}** gastou **{valor} de Mana**!\n\n"
        f"🔵 Mana: **{nova_mana}/{f['mana_max']}**"
    )


# ============================================================
# RECUPERAR MANA
#
# Pode recuperar:
# - própria ficha
# - outro jogador
# - NPC
# ============================================================

@bot.tree.command(
    name="recuperarmana",
    description="Recupera Mana de um jogador ou NPC."
)
@app_commands.describe(
    valor="Quantidade de Mana",
    jogador="Jogador que recuperará Mana",
    npc="Nome exato do NPC que recuperará Mana"
)
async def recuperarmana(
    interaction: discord.Interaction,
    valor: int,
    jogador: discord.Member = None,
    npc: str = None
):

    if jogador is not None and npc is not None:

        await interaction.response.send_message(
            "❌ Escolha jogador OU NPC.",
            ephemeral=True
        )

        return

    if jogador is None and npc is None:

        jogador = interaction.user

    dados = buscar_ficha_alvo(
        interaction,
        jogador,
        npc
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
        f"💧 **{f['nome']}** recuperou **{recuperado} de Mana**!\n\n"
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

    f = transformar_ficha(
        dados
    )

    if (
        f["dono_id"] != interaction.user.id
        and not eh_admin(interaction)
        and not eh_mestre(interaction)
    ):

        await interaction.response.send_message(
            "❌ Você não pode alterar o XP dessa ficha.",
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

        for atributo_nome in ATRIBUTOS:

            atributos[atributo_nome] = random.randint(
                0,
                5
            )

        pericias = {}

        for pericia_nome in PERICIAS:

            pericias[pericia_nome] = random.randint(
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
        f"👹 **NPCs da mesa: {len(resultados)}**"
    )

    for dados in resultados:

        f = transformar_ficha(
            dados
        )

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

    resultado = buscar_npc(
        interaction.channel.id,
        nome
    )

    if resultado is None:

        await interaction.response.send_message(
            "❌ NPC não encontrado.",
            ephemeral=True
        )

        return

    f = transformar_ficha(
        resultado
    )

    cursor.execute(
        "DELETE FROM fichas WHERE id = ?",
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
            "`/ficha` — Ver ficha\n"
            "`/verficha` — Ver outra ficha\n"
            "`/atributo` — Alterar atributo\n"
            "`/pericia` — Alterar perícia\n"
            "`/alterarficha` — Alterar HP/Mana\n"
            "`/apagarficha` — Apagar sua ficha\n"
            "`/gastarmana` — Gastar Mana\n"
            "`/cura` — Curar jogador/NPC\n"
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
            "`/passarmestre` — Passar Mestre\n"
            "`/mestre` — Ver Mestre\n\n"
            "O Mestre pode usar `/atributo` e `/pericia` "
            "informando `jogador` ou `npc` para alterar qualquer ficha."
        ),
        inline=False
    )

    embed.add_field(
        name="🛡️ Administrador",
        value=(
            "`/definirmestre` — Definir Mestre\n"
            "Administradores também podem alterar fichas e NPCs."
        ),
        inline=False
    )

    embed.add_field(
        name="🎯 Exemplos",
        value=(
            "`/atributo atributo:Força valor:5`\n"
            "`/pericia pericia:Briga valor:3`\n"
            "`/atributo atributo:Força valor:5 jogador:@Nome`\n"
            "`/pericia pericia:Briga valor:4 npc:Goblin`\n"
            "`/cura valor:10 jogador:@Nome`\n"
            "`/cura valor:10 npc:Goblin`\n"
            "`/recuperarmana valor:5 jogador:@Nome`\n"
            "`/recuperarmana valor:5 npc:Goblin`"
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
