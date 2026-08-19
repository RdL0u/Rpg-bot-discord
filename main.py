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


# ============================================================
# ATRIBUTOS
# ============================================================

ATRIBUTOS = {
    "forca": "Força",
    "destreza": "Destreza",
    "vigor": "Vigor",
    "inteligencia": "Inteligência",
    "carisma": "Carisma",
    "raciocinio": "Raciocínio"
}


# ============================================================
# PERÍCIAS
# ============================================================

PERICIAS = {
    "academicos": "Acadêmicos",
    "idiomas": "Idiomas",
    "oficios": "Ofícios",
    "armas_brancas": "Armas Brancas",
    "intimidacao": "Intimidação",
    "ocultismo": "Ocultismo",
    "briga": "Briga",
    "investigacao": "Investigação",
    "persuasao": "Persuasão",
    "ciencias": "Ciências",
    "labia": "Lábia",
    "prontidao": "Prontidão",
    "conhec_gerais": "Conhec. Gerais",
    "lideranca": "Liderança",
    "sobrevivencia": "Sobrevivência",
    "conducao": "Condução",
    "manha": "Manha",
    "tecnologia": "Tecnologia",
    "esportes": "Esportes",
    "medicina": "Medicina",
    "mira": "Mira",
    "esquiva": "Esquiva",
    "furtividade": "Furtividade"
}


# ============================================================
# MIGRAÇÃO DO BANCO
# ============================================================

def adicionar_colunas():

    cursor.execute("PRAGMA table_info(fichas)")
    colunas = {
        coluna[1]
        for coluna in cursor.fetchall()
    }

    for atributo in ATRIBUTOS:

        if atributo not in colunas:

            cursor.execute(
                f"""
                ALTER TABLE fichas
                ADD COLUMN {atributo} INTEGER NOT NULL DEFAULT 0
                """
            )

    for pericia in PERICIAS:

        if pericia not in colunas:

            cursor.execute(
                f"""
                ALTER TABLE fichas
                ADD COLUMN {pericia} INTEGER NOT NULL DEFAULT 0
                """
            )

    db.commit()


adicionar_colunas()


# ============================================================
# BOT
# ============================================================

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
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

    cursor.execute("PRAGMA table_info(fichas)")

    colunas = [
        coluna[1]
        for coluna in cursor.fetchall()
    ]

    ficha = dict(
        zip(colunas, dados)
    )

    return ficha


def calcular_rc(ficha):

    return (
        ficha["esquiva"]
        + ficha["destreza"]
        + 5
    )


# ============================================================
# ESTADO DE HP E MANA
# ============================================================

def estado_recurso(atual, maximo):

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

def pode_alterar_ficha(interaction, ficha):

    if eh_admin(interaction):
        return True

    if ficha["tipo"] == "jogador":
        return ficha["dono_id"] == interaction.user.id

    if ficha["tipo"] == "npc":
        return ficha["mestre_id"] == interaction.user.id

    return False


# ============================================================
# EMBEDS DAS FICHAS
# ============================================================

def embed_pagina_1(ficha, jogador=None):

    embed = discord.Embed(
        title=f"📜 FICHA DE {ficha['nome'].upper()}",
        color=discord.Color.dark_red()
    )

    if jogador:
        embed.description = (
            f"👤 Jogador: {jogador.mention}"
        )

    # ----------------------------
    # STATUS
    # ----------------------------

    embed.add_field(
        name="❤️ HP",
        value=mostrar_hp(
            ficha["hp_atual"],
            ficha["hp_max"]
        ),
        inline=True
    )

    embed.add_field(
        name="🔵 Mana",
        value=mostrar_mana(
            ficha["mana_atual"],
            ficha["mana_max"]
        ),
        inline=True
    )

    embed.add_field(
        name="✨ XP",
        value=str(ficha["xp"]),
        inline=True
    )

    embed.add_field(
        name="⚡ RC",
        value=str(calcular_rc(ficha)),
        inline=True
    )

    # ----------------------------
    # ATRIBUTOS
    # ----------------------------

    embed.add_field(
        name="⚔️ ATRIBUTOS",
        value=(
            f"💪 **For:** {ficha['forca']}    "
            f"🏹 **Des:** {ficha['destreza']}\n"
            f"🛡️ **Vig:** {ficha['vigor']}    "
            f"🧠 **Int:** {ficha['inteligencia']}\n"
            f"🎭 **Car:** {ficha['carisma']}    "
            f"💡 **Rac:** {ficha['raciocinio']}"
        ),
        inline=False
    )

    return embed


def embed_pagina_2(ficha):

    embed = discord.Embed(
        title=f"📚 PERÍCIAS — {ficha['nome']}",
        color=discord.Color.dark_red()
    )

    linhas = []

    for chave, nome in PERICIAS.items():

        linhas.append(
            f"• **{nome}:** {ficha[chave]}"
        )

    metade = (len(linhas) + 1) // 2

    coluna_1 = "\n".join(
        linhas[:metade]
    )

    coluna_2 = "\n".join(
        linhas[metade:]
    )

    embed.add_field(
        name="📖 Perícias",
        value=coluna_1,
        inline=True
    )

    embed.add_field(
        name="📖 Perícias",
        value=coluna_2,
        inline=True
    )

    return embed


# ============================================================
# PAGINAÇÃO DA FICHA
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
        label="📜 Status",
        style=discord.ButtonStyle.danger
    )
    async def status(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.edit_message(
            embed=embed_pagina_1(
                self.ficha,
                self.jogador
            ),
            view=self
        )

    @discord.ui.button(
        label="📚 Perícias",
        style=discord.ButtonStyle.primary
    )
    async def pericias(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.edit_message(
            embed=embed_pagina_2(
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
        f"👑 **{jogador.display_name}** agora é o Mestre!"
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

    mestre_id = obter_mestre(
        interaction.channel.id
    )

    if (
        interaction.user.id != mestre_id
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
        f"👑 Mestre transferido para {jogador.mention}!"
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

    nome = (
        membro.display_name
        if membro
        else f"<@{mestre_id}>"
    )

    await interaction.response.send_message(
        f"👑 Mestre deste canal: **{nome}**"
    )


# ============================================================
# CRIAR FICHA DE JOGADOR
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

    if buscar_ficha_jogador(
        interaction.channel.id,
        interaction.user.id
    ):

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

    dados = buscar_ficha_jogador(
        interaction.channel.id,
        interaction.user.id
    )

    ficha = transformar_ficha(dados)

    await interaction.response.send_message(
        embed=embed_pagina_1(
            ficha,
            interaction.user
        ),
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
            "❌ Você não possui uma ficha neste canal.",
            ephemeral=True
        )

        return

    f = transformar_ficha(dados)

    await interaction.response.send_message(
        embed=embed_pagina_1(
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
    interaction: discord.Interaction,
    jogador: discord.Member
):

    dados = buscar_ficha_jogador(
        interaction.channel.id,
        jogador.id
    )

    if dados is None:

        await interaction.response.send_message(
            "❌ Esse jogador não possui uma ficha neste canal.",
            ephemeral=True
        )

        return

    f = transformar_ficha(dados)

    await interaction.response.send_message(
        embed=embed_pagina_1(
            f,
            jogador
        ),
        view=FichaView(
            f,
            jogador
        )
    )


# ============================================================
# ALTERAR ATRIBUTO DO JOGADOR
# ============================================================

atributo_choices = [
    app_commands.Choice(
        name=nome,
        value=chave
    )
    for chave, nome in ATRIBUTOS.items()
]


@bot.tree.command(
    name="atributo",
    description="Altera um atributo da sua ficha."
)
@app_commands.describe(
    atributo="Atributo que será alterado",
    valor="Novo valor"
)
@app_commands.choices(
    atributo=atributo_choices
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
            "❌ Você não possui uma ficha neste canal.",
            ephemeral=True
        )

        return

    if valor < 0:

        await interaction.response.send_message(
            "❌ O valor não pode ser negativo.",
            ephemeral=True
        )

        return

    chave = atributo.value

    cursor.execute(
        f"""
        UPDATE fichas
        SET {chave} = ?
        WHERE id = ?
        """,
        (
            valor,
            dados[0]
        )
    )

    db.commit()

    await interaction.response.send_message(
        f"⚔️ **{ATRIBUTOS[chave]}** alterado para **{valor}**!"
    )


# ============================================================
# ALTERAR PERÍCIA DO JOGADOR
# ============================================================

pericia_choices = [
    app_commands.Choice(
        name=nome,
        value=chave
    )
    for chave, nome in PERICIAS.items()
]


@bot.tree.command(
    name="pericia",
    description="Altera uma perícia da sua ficha."
)
@app_commands.describe(
    pericia="Perícia que será alterada",
    valor="Novo valor"
)
@app_commands.choices(
    pericia=pericia_choices
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
            "❌ Você não possui uma ficha neste canal.",
            ephemeral=True
        )

        return

    if valor < 0:

        await interaction.response.send_message(
            "❌ O valor não pode ser negativo.",
            ephemeral=True
        )

        return

    chave = pericia.value

    cursor.execute(
        f"""
        UPDATE fichas
        SET {chave} = ?
        WHERE id = ?
        """,
        (
            valor,
            dados[0]
        )
    )

    db.commit()

    await interaction.response.send_message(
        f"📚 **{PERICIAS[chave]}** alterada para **{valor}**!"
    )


# ============================================================
# ALTERAR FICHA DE JOGADOR
# ============================================================

@bot.tree.command(
    name="alterarficha",
    description="Altera HP e Mana máximos de uma ficha."
)
@app_commands.describe(
    jogador="Jogador",
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
        f"⚙️ Ficha de **{f['nome']}** alterada!"
    )


# ============================================================
# LISTAR FICHAS
# ============================================================

@bot.tree.command(
    name="fichas",
    description="Mostra as fichas dos jogadores."
)
async def fichas(
    interaction: discord.Interaction
):

    cursor.execute("""
        SELECT *
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
            "📜 Não existem fichas neste canal."
        )

        return

    embed = discord.Embed(
        title="📜 Fichas dos jogadores",
        color=discord.Color.dark_red()
    )

    for dados in resultados:

        f = transformar_ficha(dados)

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

    f = transformar_ficha(dados)

    cursor.execute(
        "DELETE FROM fichas WHERE id = ?",
        (f["id"],)
    )

    db.commit()

    await interaction.response.send_message(
        f"🗑️ A ficha **{f['nome']}** foi apagada."
    )


# ============================================================
# ADICIONAR XP
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
            "❌ Esse jogador não possui uma ficha.",
            ephemeral=True
        )

        return

    f = transformar_ficha(dados)

    if (
        f["dono_id"] != interaction.user.id
        and not eh_admin(interaction)
    ):

        await interaction.response.send_message(
            "❌ Você só pode alterar o XP da sua própria ficha.",
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
    hp="HP",
    mana="Mana"
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

        aleatorio_valor = 1

    else:

        if not nome:

            await interaction.response.send_message(
                "❌ Informe o nome do NPC.",
                ephemeral=True
            )

            return

        if hp is None or hp <= 0:

            await interaction.response.send_message(
                "❌ Informe um HP válido.",
                ephemeral=True
            )

            return

        if mana is None or mana < 0:

            await interaction.response.send_message(
                "❌ Informe uma Mana válida.",
                ephemeral=True
            )

            return

        nome = nome[:50]

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

    # --------------------------------------------------------
    # ATRIBUTOS
    # --------------------------------------------------------

    atributos = {}

    for chave in ATRIBUTOS:

        if aleatorio_valor:

            atributos[chave] = random.randint(
                0,
                5
            )

        else:

            atributos[chave] = 0

    # --------------------------------------------------------
    # PERÍCIAS
    # --------------------------------------------------------

    pericias = {}

    for chave in PERICIAS:

        if aleatorio_valor:

            pericias[chave] = random.randint(
                0,
                5
            )

        else:

            pericias[chave] = 0

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
        "xp",
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
        0,
        aleatorio_valor
    ]

    colunas.extend(
        atributos.keys()
    )

    valores.extend(
        atributos.values()
    )

    colunas.extend(
        pericias.keys()
    )

    valores.extend(
        pericias.values()
    )

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

    ficha_id = cursor.lastrowid

    ficha = transformar_ficha(
        buscar_ficha(ficha_id)
    )

    await interaction.response.send_message(
        embed=embed_pagina_1(
            ficha
        ),
        view=FichaView(
            ficha
        ),
        ephemeral=True
    )


# ============================================================
# ALTERAR ATRIBUTO DO NPC
# ============================================================

@bot.tree.command(
    name="atributonpc",
    description="Altera um atributo de um NPC."
)
@app_commands.describe(
    nome="Nome do NPC",
    atributo="Atributo",
    valor="Novo valor"
)
@app_commands.choices(
    atributo=atributo_choices
)
async def atributonpc(
    interaction: discord.Interaction,
    nome: str,
    atributo: app_commands.Choice[str],
    valor: int
):

    if (
        not eh_mestre(interaction)
        and not eh_admin(interaction)
    ):

        await interaction.response.send_message(
            "❌ Somente o Mestre pode alterar NPCs.",
            ephemeral=True
        )

        return

    cursor.execute("""
        SELECT *
        FROM fichas
        WHERE channel_id = ?
        AND tipo = 'npc'
        AND nome = ?
        LIMIT 1
    """, (
        interaction.channel.id,
        nome
    ))

    dados = cursor.fetchone()

    if dados is None:

        await interaction.response.send_message(
            "❌ NPC não encontrado.",
            ephemeral=True
        )

        return

    if valor < 0:

        await interaction.response.send_message(
            "❌ O valor não pode ser negativo.",
            ephemeral=True
        )

        return

    chave = atributo.value

    cursor.execute(
        f"""
        UPDATE fichas
        SET {chave} = ?
        WHERE id = ?
        """,
        (
            valor,
            dados[0]
        )
    )

    db.commit()

    await interaction.response.send_message(
        f"👹 **{nome}** — "
        f"**{ATRIBUTOS[chave]}:** {valor}"
    )


# ============================================================
# ALTERAR PERÍCIA DO NPC
# ============================================================

@bot.tree.command(
    name="pericianpc",
    description="Altera uma perícia de um NPC."
)
@app_commands.describe(
    nome="Nome do NPC",
    pericia="Perícia",
    valor="Novo valor"
)
@app_commands.choices(
    pericia=pericia_choices
)
async def pericianpc(
    interaction: discord.Interaction,
    nome: str,
    pericia: app_commands.Choice[str],
    valor: int
):

    if (
        not eh_mestre(interaction)
        and not eh_admin(interaction)
    ):

        await interaction.response.send_message(
            "❌ Somente o Mestre pode alterar NPCs.",
            ephemeral=True
        )

        return

    cursor.execute("""
        SELECT *
        FROM fichas
        WHERE channel_id = ?
        AND tipo = 'npc'
        AND nome = ?
        LIMIT 1
    """, (
        interaction.channel.id,
        nome
    ))

    dados = cursor.fetchone()

    if dados is None:

        await interaction.response.send_message(
            "❌ NPC não encontrado.",
            ephemeral=True
        )

        return

    if valor < 0:

        await interaction.response.send_message(
            "❌ O valor não pode ser negativo.",
            ephemeral=True
        )

        return

    chave = pericia.value

    cursor.execute(
        f"""
        UPDATE fichas
        SET {chave} = ?
        WHERE id = ?
        """,
        (
            valor,
            dados[0]
        )
    )

    db.commit()

    await interaction.response.send_message(
        f"👹 **{nome}** — "
        f"**{PERICIAS[chave]}:** {valor}"
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

    embed = discord.Embed(
        title="👹 NPCs da mesa",
        color=discord.Color.orange()
    )

    for dados in resultados:

        f = transformar_ficha(dados)

        texto = (
            f"❤️ HP: **{f['hp_atual']}/{f['hp_max']}**\n"
            f"🔵 Mana: **{f['mana_atual']}/{f['mana_max']}**\n"
            f"✨ XP: **{f['xp']}**\n"
            f"⚡ RC: **{calcular_rc(f)}**"
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
    description="Altera HP e Mana de um NPC."
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
            "❌ Somente o Mestre pode alterar NPCs.",
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
        resultado[0]
    ))

    db.commit()

    await interaction.response.send_message(
        f"⚙️ NPC **{nome}** alterado!"
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
        f"🗑️ NPC **{nome}** apagado!"
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

        f = transformar_ficha(dados)

        if (
            f["channel_id"]
            != interaction.channel.id
        ):

            await interaction.response.send_message(
                "❌ Essa ficha pertence a outro canal.",
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
                    f"💥 **{f['nome']} morreu!**"
                )

                return

            await interaction.response.send_message(
                f"💥 **{f['nome']}** recebeu "
                f"**{valor} de dano**!\n\n"
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
                f"💚 **{f['nome']}** recuperou "
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
                f"💧 **{f['nome']}** recuperou "
                f"**{recuperado} Mana**!\n\n"
                f"💧 Mana: "
                f"{mostrar_mana(nova_mana, f['mana_max'])}"
            )


# ============================================================
# SELEÇÃO DE ALVO
# ============================================================

class AlvoSelect(discord.ui.Select):

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
                    description=descricao
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

        if interaction.user.id != self.autor_id:

            await interaction.response.send_message(
                "❌ Somente quem iniciou a ação pode escolher o alvo.",
                ephemeral=True
            )

            return

        ficha_id = int(
            self.values[0]
        )

        titulo = {
            "dano": "Quantidade de dano",
            "cura": "Quantidade de cura",
            "recuperarmana": "Quantidade de Mana"
        }[self.acao]

        await interaction.response.send_modal(
            ValorModal(
                titulo,
                self.acao,
                ficha_id
            )
        )


class AlvoView(discord.ui.View):

    def __init__(
        self,
        interaction,
        acao
    ):

        super().__init__(
            timeout=60
        )

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
            "❌ Não existem fichas neste canal.",
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
    description="Recupera Mana de uma ficha."
)
async def recuperarmana(
    interaction: discord.Interaction
):

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
    description="Gasta Mana da sua ficha."
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

    f = transformar_ficha(dados)

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
        f"🔮 **{f['nome']}** gastou **{valor} Mana**!\n"
        f"💧 Mana: {mostrar_mana(nova_mana, f['mana_max'])}"
    )


# ============================================================
# HELP
# ============================================================

@bot.tree.command(
    name="help",
    description="Mostra os comandos."
)
async def help(
    interaction: discord.Interaction
):

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
            "`/apagarficha`\n"
            "`/alterarficha`\n"
            "`/atributo`\n"
            "`/pericia`\n"
            "`/gastarmana`\n"
            "`/dano`\n"
            "`/cura`\n"
            "`/recuperarmana`\n"
            "`/addxp`"
        ),
        inline=False
    )

    embed.add_field(
        name="👹 Mestre / NPC",
        value=(
            "`/criarnpc`\n"
            "`/npcs`\n"
            "`/alternpc`\n"
            "`/atributonpc`\n"
            "`/pericianpc`\n"
            "`/apagarnpc`"
        ),
        inline=False
    )

    embed.add_field(
        name="👑 Mestre",
        value=(
            "`/mestre`\n"
            "`/passarmestre`\n"
            "`/definirmestre`"
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
# INICIAR
# ============================================================

bot.run(TOKEN)
