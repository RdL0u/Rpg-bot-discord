import os
import random

import discord

from discord.ext import commands
from discord import app_commands

from database import (
    db,
    cursor,
    garantir_mesa,
    obter_mestre,
    buscar_ficha_jogador,
    buscar_ficha
)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN não foi configurado."
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
# TRANSFORMAR FICHA
# ============================================================

def transformar_ficha(dados):

    if dados is None:
        return None

    # --------------------------------------------------------
    # IMPORTANTE:
    # Em vez de assumir cegamente a posição das colunas,
    # pegamos os nomes reais das colunas no SQLite.
    #
    # Isso evita o problema de atributos/perícias trocados
    # caso a ordem da tabela tenha sido alterada durante
    # alguma migração.
    # --------------------------------------------------------

    cursor.execute("PRAGMA table_info(fichas)")

    informacoes = cursor.fetchall()

    nomes_colunas = [
        coluna[1]
        for coluna in informacoes
    ]

    ficha = {}

    for indice, nome_coluna in enumerate(nomes_colunas):

        if indice < len(dados):
            ficha[nome_coluna] = dados[indice]

    return ficha


# ============================================================
# REFLEXO DE COMBATE
# ============================================================

def calcular_rc(ficha):

    return (
        ficha.get("esquiva", 0)
        + ficha.get("destreza", 0)
        + 5
    )


# ============================================================
# ESTADO DOS RECURSOS
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


# ============================================================
# PÁGINA 1
# STATUS + ATRIBUTOS
# ============================================================

def criar_pagina_status(f, jogador=None):

    embed = discord.Embed(
        title=f"📜 FICHA DE {f['nome'].upper()}",
        color=discord.Color.dark_red()
    )

    # --------------------------------------------------------
    # IDENTIFICAÇÃO
    # --------------------------------------------------------

    if jogador:
        identificacao = f"Jogador: {jogador.mention}"
    else:
        identificacao = "👹 NPC"

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    status = (
        f"❤️ HP: **{f['hp_atual']}/{f['hp_max']}**   "
        f"🔵 Mana: **{f['mana_atual']}/{f['mana_max']}**\n"
        f"✨ XP: **{f['xp']}**   "
        f"⚡ RC: **{calcular_rc(f)}**"
    )

    # --------------------------------------------------------
    # ATRIBUTOS
    # --------------------------------------------------------

    atributos = (
        f"💪 For: **{f['forca']}**   "
        f"🏹 Des: **{f['destreza']}**   "
        f"🛡️ Vig: **{f['vigor']}**\n"
        f"🧠 Int: **{f['inteligencia']}**   "
        f"🎭 Car: **{f['carisma']}**   "
        f"💡 Rac: **{f['raciocinio']}**"
    )

    # --------------------------------------------------------
    # DESCRIÇÃO
    # --------------------------------------------------------

    embed.description = (
        f"{identificacao}\n"
        f"❤️ **STATUS**\n"
        f"{status}\n"
        f"⚔️ **ATRIBUTOS**\n"
        f"{atributos}"
    )

    embed.set_footer(
        text="Página 1/2 • Status e Atributos"
    )

    return embed
# ============================================================
# PÁGINA 2
# PERÍCIAS — UMA COLUNA
# ============================================================

def criar_pagina_pericias(f):

    embed = discord.Embed(
        title=f"📚 PERÍCIAS — {f['nome']}",
        color=discord.Color.dark_red()
    )

    linhas = []

    for chave in ORDEM_PERICIAS:

        emoji, nome = PERICIAS[chave]

        linhas.append(
            f"{emoji} {nome}: **{f[chave]}**"
        )

    texto = "\n".join(linhas)

    embed.description = (
        "📚 **PERÍCIAS**\n\n"
        f"{texto}"
    )

    embed.set_footer(
        text="Página 2/2 • Perícias"
    )

    return embed


# ============================================================
# PAGINAÇÃO DA FICHA
# ============================================================

class FichaView(discord.ui.View):

    def __init__(self, ficha, jogador=None):

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
# PERMISSÕES
# ============================================================

def eh_admin(interaction):

    if interaction.guild is None:
        return False

    return interaction.user.guild_permissions.administrator


def eh_mestre(interaction):

    mestre_id = obter_mestre(
        interaction.channel.id
    )

    return mestre_id == interaction.user.id


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
        f"👑 **{jogador.display_name}** "
        f"agora é o Mestre deste canal!"
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
        f"👑 Novo Mestre: {jogador.mention}\n"
        f"👹 Os NPCs foram transferidos para ele."
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
            aleatorio
        )
        VALUES (
            ?, ?, NULL, 'jogador', ?,
            ?, ?, ?, ?, 0,
            0, 0, 0, 0, 0, 0, 0
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
            f"não possui uma ficha.",
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
    description="Define ou altera um atributo da sua ficha."
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
        f"⚔️ **{ATRIBUTOS[atributo.value][1]}** "
        f"alterado para **{valor}**!"
    )


# ============================================================
# ALTERAR PERÍCIA
# ============================================================

@bot.tree.command(
    name="pericia",
    description="Define ou altera uma perícia da sua ficha."
)
@app_commands.describe(
    pericia="Perícia",
    valor="Novo valor"
)
@app_commands.choices(
    pericia=[
        app_commands.Choice(
            name="Acadêmicos",
            value="academicos"
        ),
        app_commands.Choice(
            name="Idiomas",
            value="idiomas"
        ),
        app_commands.Choice(
            name="Ofícios",
            value="oficios"
        ),
        app_commands.Choice(
            name="Armas Brancas",
            value="armas_brancas"
        ),
        app_commands.Choice(
            name="Intimidação",
            value="intimidacao"
        ),
        app_commands.Choice(
            name="Ocultismo",
            value="ocultismo"
        ),
        app_commands.Choice(
            name="Briga",
            value="briga"
        ),
        app_commands.Choice(
            name="Investigação",
            value="investigacao"
        ),
        app_commands.Choice(
            name="Persuasão",
            value="persuasao"
        ),
        app_commands.Choice(
            name="Ciências",
            value="ciencias"
        ),
        app_commands.Choice(
            name="Lábia",
            value="labia"
        ),
        app_commands.Choice(
            name="Prontidão",
            value="prontidao"
        ),
        app_commands.Choice(
            name="Conhecimentos Gerais",
            value="conhecimentos_gerais"
        ),
        app_commands.Choice(
            name="Liderança",
            value="lideranca"
        ),
        app_commands.Choice(
            name="Sobrevivência",
            value="sobrevivencia"
        ),
        app_commands.Choice(
            name="Condução",
            value="conducao"
        ),
        app_commands.Choice(
            name="Manha",
            value="manha"
        ),
        app_commands.Choice(
            name="Tecnologia",
            value="tecnologia"
        ),
        app_commands.Choice(
            name="Esportes",
            value="esportes"
        ),
        app_commands.Choice(
            name="Medicina",
            value="medicina"
        ),
        app_commands.Choice(
            name="Mira",
            value="mira"
        ),
        app_commands.Choice(
            name="Esquiva",
            value="esquiva"
        ),
        app_commands.Choice(
            name="Furtividade",
            value="furtividade"
        )
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
        SET {pericia.value} = ?
        WHERE id = ?
        """,
        (
            valor,
            f["id"]
        )
    )

    db.commit()

    await interaction.response.send_message(
        f"📚 **{PERICIAS[pericia.value][1]}** "
        f"alterada para **{valor}**!"
    )


# ============================================================
# ALTERAR HP E MANA
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
        (
            f["id"],
        )
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
        f"**{valor} de dano**!\n"
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
        f"**{recuperado} de HP**!\n"
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
        f"🔮 **{f['nome']}** gastou "
        f"**{valor} de Mana**!\n"
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
        f"**{recuperado} de Mana**!\n"
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

    cursor.execute("""
        SELECT xp
        FROM fichas
        WHERE id = ?
    """, (
        f["id"],
    ))

    resultado = cursor.fetchone()

    xp_atual = resultado[0]

    await interaction.response.send_message(
        f"✨ **{f['nome']}** recebeu "
        f"**{valor} XP**!\n"
        f"✨ XP atual: **{xp_atual}**"
    )


# ============================================================
# CRIAR NPC
# ============================================================

class NPCNomeModal(discord.ui.Modal):

    def __init__(
        self,
        view_original,
        aleatorio_nome
    ):

        super().__init__(
            title="Criar NPC"
        )

        self.view_original = view_original
        self.aleatorio_nome = aleatorio_nome

        self.nome = discord.ui.TextInput(
            label="Nome do NPC",
            placeholder="Digite o nome do NPC",
            required=True,
            max_length=50
        )

        self.hp = discord.ui.TextInput(
            label="HP",
            placeholder="Digite o HP",
            required=True
        )

        self.mana = discord.ui.TextInput(
            label="Mana",
            placeholder="Digite a Mana",
            required=True
        )

        self.add_item(self.nome)
        self.add_item(self.hp)
        self.add_item(self.mana)

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        try:

            hp = int(self.hp.value)
            mana = int(self.mana.value)

        except ValueError:

            await interaction.response.send_message(
                "❌ HP e Mana precisam ser números.",
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

        self.view_original.nome = self.nome.value[:50]
        self.view_original.hp = hp
        self.view_original.mana = mana

        await interaction.response.edit_message(
            content=(
                "👹 **Criação de NPC**\n\n"
                "Agora escolha se os **atributos** "
                "serão aleatórios."
            ),
            view=NPCAtributosView(
                self.view_original
            )
        )


class NPCConfiguracaoInicialView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=180
        )

        self.nome = None
        self.hp = None
        self.mana = None

        self.aleatorio_nome = False

    @discord.ui.button(
        label="🎲 Nome / HP / Mana Aleatórios",
        style=discord.ButtonStyle.primary
    )
    async def aleatorio(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

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

        self.nome = random.choice(nomes)
        self.hp = random.randint(20, 150)
        self.mana = random.randint(0, 100)

        self.aleatorio_nome = True

        await interaction.response.edit_message(
            content=(
                "👹 **Criação de NPC**\n\n"
                f"Nome: **{self.nome}**\n"
                f"❤️ HP: **{self.hp}**\n"
                f"🔵 Mana: **{self.mana}**\n\n"
                "Agora escolha se os **atributos** "
                "serão aleatórios."
            ),
            view=NPCAtributosView(self)
        )

    @discord.ui.button(
        label="✏️ Definir Nome / HP / Mana",
        style=discord.ButtonStyle.secondary
    )
    async def personalizado(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.send_modal(
            NPCNomeModal(
                self,
                False
            )
        )


class NPCAtributosView(discord.ui.View):

    def __init__(
        self,
        dados
    ):

        super().__init__(
            timeout=180
        )

        self.dados = dados

    @discord.ui.button(
        label="🎲 Atributos Aleatórios",
        style=discord.ButtonStyle.primary
    )
    async def aleatorios(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        self.dados.atributos_aleatorios = True

        await interaction.response.edit_message(
            content=(
                "👹 **Criação de NPC**\n\n"
                "Atributos: 🎲 Aleatórios\n\n"
                "Agora escolha se as **perícias** "
                "serão aleatórias."
            ),
            view=NPCPericiasView(
                self.dados
            )
        )

    @discord.ui.button(
        label="✏️ Atributos em 0",
        style=discord.ButtonStyle.secondary
    )
    async def normais(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        self.dados.atributos_aleatorios = False

        await interaction.response.edit_message(
            content=(
                "👹 **Criação de NPC**\n\n"
                "Atributos: **0**\n\n"
                "Agora escolha se as **perícias** "
                "serão aleatórias."
            ),
            view=NPCPericiasView(
                self.dados
            )
        )


class NPCPericiasView(discord.ui.View):

    def __init__(
        self,
        dados
    ):

        super().__init__(
            timeout=180
        )

        self.dados = dados

    @discord.ui.button(
        label="🎲 Perícias Aleatórias",
        style=discord.ButtonStyle.primary
    )
    async def aleatorias(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        self.dados.pericias_aleatorias = True

        await finalizar_criacao_npc(
            interaction,
            self.dados
        )

    @discord.ui.button(
        label="✏️ Perícias em 0",
        style=discord.ButtonStyle.secondary
    )
    async def normais(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        self.dados.pericias_aleatorias = False

        await finalizar_criacao_npc(
            interaction,
            self.dados
        )


async def finalizar_criacao_npc(
    interaction,
    dados
):

    nome = dados.nome
    hp = dados.hp
    mana = dados.mana

    atributos = {}

    for chave in ATRIBUTOS:

        if getattr(
            dados,
            "atributos_aleatorios",
            False
        ):

            atributos[chave] = random.randint(
                0,
                5
            )

        else:

            atributos[chave] = 0

    pericias = {}

    for chave in PERICIAS:

        if getattr(
            dados,
            "pericias_aleatorias",
            False
        ):

            pericias[chave] = random.randint(
                0,
                5
            )

        else:

            pericias[chave] = 0

    garantir_mesa(
        interaction.channel.id
    )

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
        +
        valores
        +
        [
            1
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

    atributos_status = (
        "🎲 Aleatórios"
        if getattr(
            dados,
            "atributos_aleatorios",
            False
        )
        else "0"
    )

    pericias_status = (
        "🎲 Aleatórias"
        if getattr(
            dados,
            "pericias_aleatorias",
            False
        )
        else "0"
    )

    await interaction.response.edit_message(
        content=(
            f"👹 **NPC {nome} criado com sucesso!**\n\n"
            f"❤️ HP: **{hp}/{hp}**\n"
            f"🔵 Mana: **{mana}/{mana}**\n"
            f"⚡ RC: **{rc}**\n\n"
            f"⚔️ Atributos: **{atributos_status}**\n"
            f"📚 Perícias: **{pericias_status}**"
        ),
        view=None
    )


# ============================================================
# COMANDO CRIAR NPC
# ============================================================

@bot.tree.command(
    name="criarnpc",
    description="Inicia a criação de um NPC."
)
async def criarnpc(
    interaction: discord.Interaction
):

    if (
        not eh_mestre(interaction)
        and not eh_admin(interaction)
    ):

        await interaction.response.send_message(
            "❌ Somente o Mestre ou um administrador "
            "pode criar NPCs.",
            ephemeral=True
        )

        return

    view = NPCConfiguracaoInicialView()

    await interaction.response.send_message(
        (
            "👹 **CRIAR NPC**\n\n"
            "Escolha primeiro como serão definidos "
            "o **nome, HP e Mana**."
        ),
        view=view,
        ephemeral=True
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
        f"👹 **NPCs da mesa — "
        f"{len(resultados)} encontrados**"
    )

    for dados in resultados:

        f = transformar_ficha(dados)

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
        f"🗑️ NPC **{nome}** apagado."
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
            "`/verficha` — Ver ficha de outro jogador\n"
            "`/atributo` — Alterar atributo\n"
            "`/pericia` — Alterar perícia\n"
            "`/alterarficha` — Alterar HP/Mana\n"
            "`/apagarficha` — Apagar ficha\n"
            "`/gastarmana` — Gastar Mana\n"
            "`/cura` — Curar outro jogador\n"
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
            "`/mestre` — Ver Mestre"
        ),
        inline=False
    )

    embed.add_field(
        name="🛡️ Administrador",
        value=(
            "`/definirmestre` — Definir Mestre\n"
            "Permissões administrativas também "
            "permitem alterar fichas."
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
