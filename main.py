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

# ============================================================
# BANCO DE DADOS
# ============================================================

db = sqlite3.connect("rpg_fichas.db")
cursor = db.cursor()

# ------------------------------------------------------------
# MESAS / CANAIS
# ------------------------------------------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS mesas (
    channel_id INTEGER PRIMARY KEY,
    mestre_id INTEGER
)
""")

# ------------------------------------------------------------
# FICHAS
#
# tipo:
# jogador = ficha normal de jogador
# npc     = ficha criada pelo mestre
#
# A combinação channel_id + dono_id identifica a ficha
# de jogador naquele canal.
# ------------------------------------------------------------

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

db.commit()

# ============================================================
# CONFIGURAÇÃO DO BOT
# ============================================================

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def eh_admin(interaction):

    return (
        interaction.guild is not None
        and interaction.user.guild_permissions.administrator
    )


def obter_mestre(channel_id):

    cursor.execute("""
        SELECT mestre_id
        FROM mesas
        WHERE channel_id = ?
    """, (channel_id,))

    resultado = cursor.fetchone()

    if resultado is None:
        return None

    return resultado[0]


def garantir_mesa(channel_id):

    cursor.execute("""
        INSERT OR IGNORE INTO mesas (
            channel_id,
            mestre_id
        )
        VALUES (?, NULL)
    """, (channel_id,))

    db.commit()


def eh_mestre(interaction):

    mestre_id = obter_mestre(interaction.channel.id)

    return mestre_id == interaction.user.id


def pode_alterar_ficha(interaction, ficha):

    if eh_admin(interaction):
        return True

    if ficha["tipo"] == "jogador":
        return ficha["dono_id"] == interaction.user.id

    if ficha["tipo"] == "npc":
        return ficha["mestre_id"] == interaction.user.id

    return False


def buscar_ficha_jogador(channel_id, user_id):

    cursor.execute("""
        SELECT
            id,
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
        FROM fichas
        WHERE channel_id = ?
        AND dono_id = ?
        AND tipo = 'jogador'
    """, (
        channel_id,
        user_id
    ))

    resultado = cursor.fetchone()

    return resultado


def buscar_ficha_por_id(ficha_id):

    cursor.execute("""
        SELECT
            id,
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
        FROM fichas
        WHERE id = ?
    """, (ficha_id,))

    return cursor.fetchone()


def ficha_dict(dados):

    if dados is None:
        return None

    return {
        "id": dados[0],
        "channel_id": dados[1],
        "dono_id": dados[2],
        "mestre_id": dados[3],
        "tipo": dados[4],
        "nome": dados[5],
        "hp_atual": dados[6],
        "hp_max": dados[7],
        "mana_atual": dados[8],
        "mana_max": dados[9],
        "xp": dados[10],
        "aleatorio": dados[11]
    }


def buscar_alvos(channel_id):

    cursor.execute("""
        SELECT
            id,
            nome,
            tipo
        FROM fichas
        WHERE channel_id = ?
        ORDER BY tipo, nome
    """, (channel_id,))

    return cursor.fetchall()


def nome_alvo(ficha):

    return ficha["nome"]


# ============================================================
# MODAL PARA DIGITAR VALOR
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

        self.add_item(self.valor)

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        try:
            valor = int(self.valor.value)

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

        dados = buscar_ficha_por_id(
            self.ficha_id
        )

        if dados is None:

            await interaction.response.send_message(
                "❌ Essa ficha não existe mais.",
                ephemeral=True
            )

            return

        ficha = ficha_dict(dados)

        # ----------------------------------------------------
        # CONFIRMAR QUE A FICHA PERTENCE AO CANAL
        # ----------------------------------------------------

        if ficha["channel_id"] != interaction.channel.id:

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
                ficha["hp_atual"] - valor
            )

            cursor.execute("""
                UPDATE fichas
                SET hp_atual = ?
                WHERE id = ?
            """, (
                novo_hp,
                ficha["id"]
            ))

            db.commit()

            # ------------------------------------------------
            # NPC MORREU
            # ------------------------------------------------

            if ficha["tipo"] == "npc" and novo_hp <= 0:

                cursor.execute("""
                    DELETE FROM fichas
                    WHERE id = ?
                """, (ficha["id"],))

                db.commit()

                await interaction.response.send_message(
                    f"💥 **{interaction.user.display_name}** "
                    f"causou **{valor} de dano** em "
                    f"**{ficha['nome']}**!\n\n"
                    f"💀 **{ficha['nome']} morreu e sua ficha "
                    f"foi apagada.**"
                )

                return

            # ------------------------------------------------
            # DANO NORMAL
            # ------------------------------------------------

            await interaction.response.send_message(
                f"💥 **{interaction.user.display_name}** "
                f"causou **{valor} de dano** em "
                f"**{ficha['nome']}**!\n"
                f"❤️ HP: **{ficha['hp_max']}/{novo_hp}**"
            )

            return

        # ----------------------------------------------------
        # CURA
        # ----------------------------------------------------

        if self.acao == "cura":

            novo_hp = min(
                ficha["hp_max"],
                ficha["hp_atual"] + valor
            )

            recuperado = novo_hp - ficha["hp_atual"]

            cursor.execute("""
                UPDATE fichas
                SET hp_atual = ?
                WHERE id = ?
            """, (
                novo_hp,
                ficha["id"]
            ))

            db.commit()

            await interaction.response.send_message(
                f"💚 **{interaction.user.display_name}** "
                f"curou **{ficha['nome']}** em "
                f"**{recuperado} de HP**!\n"
                f"❤️ HP: **{ficha['hp_max']}/{novo_hp}**"
            )

            return

        # ----------------------------------------------------
        # RECUPERAR MANA
        # ----------------------------------------------------

        if self.acao == "recuperarmana":

            nova_mana = min(
                ficha["mana_max"],
                ficha["mana_atual"] + valor
            )

            recuperado = (
                nova_mana -
                ficha["mana_atual"]
            )

            cursor.execute("""
                UPDATE fichas
                SET mana_atual = ?
                WHERE id = ?
            """, (
                nova_mana,
                ficha["id"]
            ))

            db.commit()

            await interaction.response.send_message(
                f"💧 **{interaction.user.display_name}** "
                f"recuperou **{recuperado} de Mana** de "
                f"**{ficha['nome']}**!\n"
                f"💧 Mana: **{ficha['mana_max']}/{nova_mana}**"
            )

            return


# ============================================================
# SELECT DE ALVOS
# ============================================================

class AlvoSelect(discord.ui.Select):

    def __init__(
        self,
        interaction,
        acao
    ):

        self.acao = acao
        self.autor_id = interaction.user.id

        alvos = buscar_alvos(
            interaction.channel.id
        )

        opcoes = []

        for ficha_id, nome, tipo in alvos:

            if tipo == "npc":

                emoji = "👹"

            else:

                emoji = "👤"

            opcoes.append(
                discord.SelectOption(
                    label=nome[:100],
                    value=str(ficha_id),
                    emoji=emoji,
                    description=(
                        "NPC"
                        if tipo == "npc"
                        else
                        "Jogador"
                    )
                )
            )

        # Discord permite no máximo 25 opções
        opcoes = opcoes[:25]

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
                "❌ Somente quem abriu esta ação pode "
                "escolher o alvo.",
                ephemeral=True
            )

            return

        ficha_id = int(
            self.values[0]
        )

        # Abre a tela para digitar a quantidade
        if self.acao == "dano":

            titulo = "💥 Quantidade de dano"

        elif self.acao == "cura":

            titulo = "💚 Quantidade de cura"

        else:

            titulo = "💧 Mana recuperada"

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

        alvos = buscar_alvos(
            interaction.channel.id
        )

        if not alvos:

            return

        self.add_item(
            AlvoSelect(
                interaction,
                acao
            )
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
    jogador="Pessoa que será o Mestre"
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

    db.commit()

    await interaction.response.send_message(
        f"👑 **{jogador.display_name}** agora é o "
        f"Mestre deste canal!"
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
            f"👑 O Mestre deste canal é "
            f"**{membro.display_name}**."
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

    # Verificar se já existe ficha neste canal
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

    embed = discord.Embed(
        title="📜 Ficha criada!",
        color=discord.Color.green()
    )

    embed.add_field(
        name="👤 Personagem",
        value=nome,
        inline=False
    )

    embed.add_field(
        name="❤️ HP",
        value=f"{hp}/{hp}",
        inline=True
    )

    embed.add_field(
        name="💧 Mana",
        value=f"{mana}/{mana}",
        inline=True
    )

    embed.add_field(
        name="⭐ XP",
        value="0",
        inline=True
    )

    await interaction.response.send_message(
        embed=embed
    )


# ============================================================
# VER PRÓPRIA FICHA
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

    f = ficha_dict(dados)

    embed = discord.Embed(
        title=f"📜 {f['nome']}",
        description=(
            f"Jogador: "
            f"{interaction.user.mention}"
        ),
        color=discord.Color.dark_red()
    )

    embed.add_field(
        name="❤️ HP",
        value=f"{f['hp_max']}/{f['hp_atual']}",
        inline=True
    )

    embed.add_field(
        name="💧 Mana",
        value=f"{f['mana_max']}/{f['mana_atual']}",
        inline=True
    )

    embed.add_field(
        name="⭐ XP",
        value=str(f["xp"]),
        inline=True
    )

    await interaction.response.send_message(
        embed=embed
    )


# ============================================================
# APAGAR PRÓPRIA FICHA
# ============================================================

@bot.tree.command(
    name="apagarficha",
    description="Apaga sua ficha neste canal."
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
            "❌ Você não possui uma ficha neste canal.",
            ephemeral=True
        )

        return

    f = ficha_dict(dados)

    cursor.execute("""
        DELETE FROM fichas
        WHERE id = ?
    """, (f["id"],))

    db.commit()

    await interaction.response.send_message(
        f"🗑️ A ficha **{f['nome']}** foi apagada."
    )


# ============================================================
# ALTERAR FICHA DE JOGADOR
# ============================================================

@bot.tree.command(
    name="alterarficha",
    description="Altera sua ficha ou a de outro jogador."
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
            "❌ Esse jogador não possui uma ficha "
            "neste canal.",
            ephemeral=True
        )

        return

    f = ficha_dict(dados)

    if not pode_alterar_ficha(
        interaction,
        f
    ):

        await interaction.response.send_message(
            "❌ Você só pode alterar sua própria ficha.",
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
        f"⚙️ Ficha de **{f['nome']}** alterada!\n"
        f"❤️ HP: **{hp}/{hp}**\n"
        f"💧 Mana: **{mana}/{mana}**"
    )


# ============================================================
# DANO
# ============================================================

@bot.tree.command(
    name="dano",
    description="Escolha uma ficha para receber dano."
)
async def dano(
    interaction: discord.Interaction
):

    alvos = buscar_alvos(
        interaction.channel.id
    )

    if not alvos:

        await interaction.response.send_message(
            "❌ Não existem fichas neste canal.",
            ephemeral=True
        )

        return

    view = AlvoView(
        interaction,
        "dano"
    )

    await interaction.response.send_message(
        "💥 **Escolha quem receberá o dano:**",
        view=view,
        ephemeral=True
    )


# ============================================================
# CURA
# ============================================================

@bot.tree.command(
    name="cura",
    description="Escolha uma ficha para receber cura."
)
async def cura(
    interaction: discord.Interaction
):

    alvos = buscar_alvos(
        interaction.channel.id
    )

    if not alvos:

        await interaction.response.send_message(
            "❌ Não existem fichas neste canal.",
            ephemeral=True
        )

        return

    view = AlvoView(
        interaction,
        "cura"
    )

    await interaction.response.send_message(
        "💚 **Escolha quem receberá a cura:**",
        view=view,
        ephemeral=True
    )


# ============================================================
# RECUPERAR MANA
# ============================================================

@bot.tree.command(
    name="recuperarmana",
    description="Escolha uma ficha para recuperar Mana."
)
async def recuperarmana(
    interaction: discord.Interaction
):

    alvos = buscar_alvos(
        interaction.channel.id
    )

    if not alvos:

        await interaction.response.send_message(
            "❌ Não existem fichas neste canal.",
            ephemeral=True
        )

        return

    view = AlvoView(
        interaction,
        "recuperarmana"
    )

    await interaction.response.send_message(
        "💧 **Escolha quem recuperará Mana:**",
        view=view,
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
            "❌ Você não possui uma ficha neste canal.",
            ephemeral=True
        )

        return

    if valor <= 0:

        await interaction.response.send_message(
            "❌ O valor precisa ser maior que 0.",
            ephemeral=True
        )

        return

    f = ficha_dict(dados)

    if valor > f["mana_atual"]:

        await interaction.response.send_message(
            f"❌ Mana insuficiente!\n"
            f"💧 Mana: **{f['mana_max']}/{f['mana_atual']}**",
            ephemeral=True
        )

        return

    nova_mana = (
        f["mana_atual"] -
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
        f"🔮 **{f['nome']}** gastou "
        f"**{valor} de Mana**!\n"
        f"💧 Mana: **{f['mana_max']}/{nova_mana}**"
    )


# ============================================================
# ADICIONAR XP
# ============================================================

@bot.tree.command(
    name="addxp",
    description="Adiciona XP à sua ficha ou, sendo Mestre/Admin, a outra."
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
            "❌ Esse jogador não possui ficha neste canal.",
            ephemeral=True
        )

        return

    f = ficha_dict(dados)

    if not pode_alterar_ficha(
        interaction,
        f
    ):

        await interaction.response.send_message(
            "❌ Você só pode alterar seu próprio XP.",
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
    """, (f["id"],))

    xp_atual = cursor.fetchone()[0]

    await interaction.response.send_message(
        f"⭐ **{f['nome']}** recebeu **{valor} XP**!\n"
        f"⭐ XP atual: **{xp_atual}**"
    )


# ============================================================
# CRIAR NPC
# ============================================================

@bot.tree.command(
    name="criarnpc",
    description="Cria um NPC neste canal."
)
@app_commands.describe(
    aleatorio="Escolha SIM para gerar o NPC automaticamente",
    nome="Nome do NPC, se não for aleatório",
    hp="HP do NPC, se não for aleatório",
    mana="Mana do NPC, se não for aleatório"
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
    nome: str | None = None,
    hp: int | None = None,
    mana: int | None = None
):

    garantir_mesa(
        interaction.channel.id
    )

    if not eh_mestre(interaction) and not eh_admin(interaction):

        await interaction.response.send_message(
            "❌ Somente o Mestre deste canal "
            "pode criar NPCs.",
            ephemeral=True
        )

        return

    # --------------------------------------------------------
    # NPC ALEATÓRIO
    # --------------------------------------------------------

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

        foi_aleatorio = 1

    # --------------------------------------------------------
    # NPC PERSONALIZADO
    # --------------------------------------------------------

    else:

        if not nome:

            await interaction.response.send_message(
                "❌ Digite o nome do NPC.",
                ephemeral=True
            )

            return

        if hp is None:

            await interaction.response.send_message(
                "❌ Digite o HP do NPC.",
                ephemeral=True
            )

            return

        if mana is None:

            await interaction.response.send_message(
                "❌ Digite a Mana do NPC.",
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

        foi_aleatorio = 0

    # --------------------------------------------------------
    # CRIAR NPC
    # --------------------------------------------------------

    mestre_id = obter_mestre(
        interaction.channel.id
    )

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
        VALUES (?, NULL, ?, 'npc', ?, ?, ?, ?, ?, 0, ?)
    """, (
        interaction.channel.id,
        mestre_id,
        nome,
        hp,
        hp,
        mana,
        mana,
        foi_aleatorio
    ))

    db.commit()

    # --------------------------------------------------------
    # SOMENTE O MESTRE RECEBE A FICHA COMPLETA
    # --------------------------------------------------------

    embed = discord.Embed(
        title="👹 NPC criado!",
        color=discord.Color.orange()
    )

    embed.add_field(
        name="👤 Nome",
        value=nome,
        inline=False
    )

    embed.add_field(
        name="❤️ HP",
        value=f"{hp}/{hp}",
        inline=True
    )

    embed.add_field(
        name="💧 Mana",
        value=f"{mana}/{mana}",
        inline=True
    )

    embed.add_field(
        name="🎲 Tipo",
        value=(
            "Aleatório"
            if foi_aleatorio
            else
            "Personalizado"
        ),
        inline=True
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


# ============================================================
# LISTAR NPCs
# SOMENTE MESTRE
# ============================================================

@bot.tree.command(
    name="npcs",
    description="Mostra os NPCs deste canal."
)
async def npcs(
    interaction: discord.Interaction
):

    if not eh_mestre(interaction) and not eh_admin(interaction):

        await interaction.response.send_message(
            "❌ Somente o Mestre pode visualizar "
            "as fichas dos NPCs.",
            ephemeral=True
        )

        return

    cursor.execute("""
        SELECT
            nome,
            hp_atual,
            hp_max,
            mana_atual,
            mana_max,
            xp
        FROM fichas
        WHERE channel_id = ?
        AND tipo = 'npc'
        ORDER BY nome
    """, (
        interaction.channel.id,
    ))

    dados = cursor.fetchall()

    if not dados:

        await interaction.response.send_message(
            "👹 Não existem NPCs neste canal.",
            ephemeral=True
        )

        return

    embed = discord.Embed(
        title="👹 NPCs da mesa",
        color=discord.Color.orange()
    )

    for (
        nome,
        hp,
        hp_max,
        mana,
        mana_max,
        xp
    ) in dados:

        embed.add_field(
            name=f"👹 {nome}",
            value=(
                f"❤️ HP: **{hp_max}/{hp}**\n"
                f"💧 Mana: **{mana_max}/{mana}**\n"
                f"⭐ XP: **{xp}**"
            ),
            inline=False
        )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


# ============================================================
# APAGAR NPC
# SOMENTE MESTRE
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

    if not eh_mestre(interaction) and not eh_admin(interaction):

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

    cursor.execute("""
        DELETE FROM fichas
        WHERE id = ?
    """, (
        resultado[0],
    ))

    db.commit()

    await interaction.response.send_message(
        f"🗑️ O NPC **{nome}** foi apagado."
    )


# ============================================================
# ALTERAR NPC
# SOMENTE MESTRE
# ============================================================

@bot.tree.command(
    name="alternpc",
    description="Altera os valores de um NPC."
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

    if not eh_mestre(interaction) and not eh_admin(interaction):

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
        resultado[0]
    ))

    db.commit()

    await interaction.response.send_message(
        f"⚙️ NPC **{nome}** alterado!\n"
        f"❤️ HP: **{hp}/{hp}**\n"
        f"💧 Mana: **{mana}/{mana}**"
    )


# ============================================================
# INICIAR BOT
# ============================================================

if not TOKEN:

    raise RuntimeError(
        "DISCORD_TOKEN não foi configurado."
    )

bot.run(TOKEN)
