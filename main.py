import os
import random
import discord

from discord.ext import commands
from discord import app_commands

from database import (
    garantir_mesa,
    obter_mestre,
    definir_mestre,
    transferir_npcs,
    buscar_ficha_jogador,
    buscar_ficha,
    buscar_npcs,
    buscar_npc_por_nome,
    criar_ficha_jogador,
    criar_npc,
    alterar_hp,
    alterar_hp_e_maximo,
    alterar_mana,
    alterar_mana_e_maximo,
    adicionar_xp,
    alterar_atributo,
    alterar_pericia,
    apagar_ficha,
    apagar_npc_por_nome
)

from permissoes import (
    eh_admin,
    eh_mestre,
    pode_alterar_ficha
)

from fichas import (
    transformar_ficha
)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN não foi configurado.")


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


# ============================================================
# PÁGINA 1
# STATUS + ATRIBUTOS
# ============================================================

def criar_pagina_status(f, jogador=None):

    embed = discord.Embed(
        title=f"📜 FICHA DE {f['nome'].upper()}",
        color=discord.Color.dark_red()
    )

    if jogador:
        identificacao = f"Jogador: {jogador.mention}"
    else:
        identificacao = "👹 NPC"

    status = (
        f"❤️ HP: **{f['hp_atual']}/{f['hp_max']}**    "
        f"🔵 Mana: **{f['mana_atual']}/{f['mana_max']}**\n"
        f"✨ XP: **{f['xp']}**    "
        f"⚡ RC: **{calcular_rc(f)}**"
    )

    atributos = (
        f"💪 For: **{f['forca']}**    "
        f"🏹 Des: **{f['destreza']}**\n"
        f"🛡️ Vig: **{f['vigor']}**    "
        f"🧠 Int: **{f['inteligencia']}**\n"
        f"🎭 Car: **{f['carisma']}**    "
        f"💡 Rac: **{f['raciocinio']}**"
    )

    embed.description = (
        f"{identificacao}\n\n"
        f"❤️ **STATUS**\n"
        f"{status}\n\n"
        f"⚔️ **ATRIBUTOS**\n"
        f"{atributos}"
    )

    embed.set_footer(
        text="Página 1/2 • Status e Atributos"
    )

    return embed


# ============================================================
# PÁGINA 2
# PERÍCIAS
# ============================================================

def criar_pagina_pericias(f):

    embed = discord.Embed(
        title=f"📚 PERÍCIAS — {f['nome']}",
        color=discord.Color.dark_red()
    )

    linhas = []

    for chave, (emoji, nome) in PERICIAS.items():

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

    definir_mestre(
        interaction.channel.id,
        jogador.id
    )

    transferir_npcs(
        interaction.channel.id,
        jogador.id
    )

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
            "❌ Somente o Mestre atual ou um administrador pode fazer isso.",
            ephemeral=True
        )

        return

    garantir_mesa(
        interaction.channel.id
    )

    definir_mestre(
        interaction.channel.id,
        jogador.id
    )

    transferir_npcs(
        interaction.channel.id,
        jogador.id
    )

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

    criar_ficha_jogador(
        interaction.channel.id,
        interaction.user.id,
        nome,
        hp,
        mana
    )

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
            f"❌ **{jogador.display_name}** não possui uma ficha.",
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

    alterar_atributo(
        f["id"],
        atributo.value,
        valor
    )

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

    alterar_pericia(
        f["id"],
        pericia.value,
        valor
    )

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

    alterar_hp_e_maximo(
        f["id"],
        hp,
        hp
    )

    alterar_mana_e_maximo(
        f["id"],
        mana,
        mana
    )

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

    apagar_ficha(
        f["id"]
    )

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
            "❌ Esse jogador não possui uma ficha neste canal.",
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

    alterar_hp(
        f["id"],
        novo_hp
    )

    await interaction.response.send_message(
        f"💥 **{f['nome']}** recebeu **{valor} de dano**!\n"
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
            "❌ Esse jogador não possui uma ficha neste canal.",
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

    recuperado = novo_hp - f["hp_atual"]

    alterar_hp(
        f["id"],
        novo_hp
    )

    await interaction.response.send_message(
        f"💚 **{f['nome']}** recuperou **{recuperado} de HP**!\n"
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

    nova_mana = f["mana_atual"] - valor

    alterar_mana(
        f["id"],
        nova_mana
    )

    await interaction.response.send_message(
        f"🔮 **{f['nome']}** gastou **{valor} de Mana**!\n"
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
            "❌ Esse jogador não possui uma ficha neste canal.",
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

    recuperado = nova_mana - f["mana_atual"]

    alterar_mana(
        f["id"],
        nova_mana
    )

    await interaction.response.send_message(
        f"💧 **{f['nome']}** recuperou **{recuperado} de Mana**!\n"
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

    novo_xp = adicionar_xp(
        f["id"],
        valor
    )

    await interaction.response.send_message(
        f"✨ **{f['nome']}** recebeu **{valor} XP**!\n"
        f"✨ XP atual: **{novo_xp}**"
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

        atributos = {}

        for chave in ATRIBUTOS:
            atributos[chave] = random.randint(0, 5)

        pericias = {}

        for chave in PERICIAS:
            pericias[chave] = random.randint(0, 5)

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

        definir_mestre(
            interaction.channel.id,
            mestre_id
        )

    criar_npc(
        interaction.channel.id,
        mestre_id,
        nome,
        hp,
        mana,
        atributos,
        pericias,
        aleatorio_valor
    )

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

    resultados = buscar_npcs(
        interaction.channel.id
    )

    if not resultados:

        await interaction.response.send_message(
            "👹 Não existem NPCs neste canal.",
            ephemeral=True
        )

        return

    await interaction.response.send_message(
        f"👹 **NPCs da mesa — {len(resultados)} encontrados**"
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

    resultado = buscar_npc_por_nome(
        interaction.channel.id,
        nome
    )

    if resultado is None:

        await interaction.response.send_message(
            "❌ NPC não encontrado.",
            ephemeral=True
        )

        return

    apagados = apagar_npc_por_nome(
        interaction.channel.id,
        nome
    )

    if apagados == 0:

        await interaction.response.send_message(
            "❌ Não foi possível apagar o NPC.",
            ephemeral=True
        )

        return

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
