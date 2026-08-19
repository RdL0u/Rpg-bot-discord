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

db.commit()


# ============================================================
# BOT
# ============================================================

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def garantir_mesa(channel_id):
    cursor.execute("""
        INSERT OR IGNORE INTO mesas (channel_id, mestre_id)
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
        LIMIT 1
    """, (channel_id, user_id))

    return cursor.fetchone()


def buscar_ficha(ficha_id):
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


def transformar_ficha(dados):

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


# ============================================================
# BARRAS DE HP E MANA
# ============================================================

def porcentagem(atual, maximo):

    if maximo <= 0:
        return 0

    return max(
        0,
        min(
            100,
            (atual / maximo) * 100
        )
    )


def criar_barra(atual, maximo, tamanho=20):

    if maximo <= 0:
        preenchido = 0
    else:
        preenchido = round(
            (atual / maximo) * tamanho
        )

    preenchido = max(
        0,
        min(tamanho, preenchido)
    )

    vazio = tamanho - preenchido

    return (
        "┃"
        + ("█" * preenchido)
        + ("░" * vazio)
        + "┃"
    )


def estado_recurso(atual, maximo):

    if atual <= 0:
        return "ZERADO"

    percentual = porcentagem(
        atual,
        maximo
    )

    if percentual >= 70:
        return "BOM"

    if percentual >= 30:
        return "BAIXO"

    return "CRÍTICO"


def mostrar_hp(atual, maximo):
    return (
        f"**{atual}/{maximo}** — "
        f"{estado_recurso(atual, maximo)}"
    )


def mostrar_mana(atual, maximo):
    return (
        f"**{atual}/{maximo}** — "
        f"{estado_recurso(atual, maximo)}"
    )
# ============================================================
# PERMISSÕES DE ALTERAÇÃO
# ============================================================

def pode_alterar_ficha(interaction, ficha):

    if eh_admin(interaction):
        return True

    if ficha["tipo"] == "jogador":
        return (
            ficha["dono_id"]
            == interaction.user.id
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
# SOMENTE ADMINISTRADOR
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
# MESTRE ATUAL OU ADMINISTRADOR
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

    if jogador.id == interaction.user.id:

        await interaction.response.send_message(
            "❌ Você já é o Mestre deste canal.",
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
        f"👑 **Mestre transferido!**\n\n"
        f"👑 Novo Mestre: {jogador.mention}\n"
        f"👹 Todos os NPCs deste canal "
        f"foram transferidos para o novo Mestre."
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
        title=f"📜 {nome}",
        description="Ficha criada com sucesso!",
        color=discord.Color.green()
    )

    embed.add_field(
        name="❤️ HP",
        value=mostrar_hp(hp, hp),
        inline=False
    )

    embed.add_field(
        name="💧 Mana",
        value=mostrar_mana(mana, mana),
        inline=False
    )

    embed.add_field(
        name="⭐ XP",
        value="0",
        inline=False
    )

    await interaction.response.send_message(
        embed=embed
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

    embed = discord.Embed(
        title=f"⚔️ {f['nome']}",
        description=(
            f"Jogador: {interaction.user.mention}"
        ),
        color=discord.Color.dark_red()
    )

    embed.add_field(
        name="❤️ HP",
        value=mostrar_hp(
            f["hp_atual"],
            f["hp_max"]
        ),
        inline=False
    )

    embed.add_field(
        name="💧 Mana",
        value=mostrar_mana(
            f["mana_atual"],
            f["mana_max"]
        ),
        inline=False
    )

    embed.add_field(
        name="⭐ XP",
        value=str(f["xp"]),
        inline=False
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


# ============================================================
# LISTAR FICHAS DE JOGADORES
# ============================================================

@bot.tree.command(
    name="fichas",
    description="Mostra as fichas dos jogadores deste canal."
)
async def fichas(
    interaction: discord.Interaction
):

    cursor.execute("""
        SELECT
            nome,
            hp_atual,
            hp_max,
            mana_atual,
            mana_max,
            xp,
            dono_id
        FROM fichas
        WHERE channel_id = ?
        AND tipo = 'jogador'
        ORDER BY nome
    """, (
        interaction.channel.id,
    ))

    dados = cursor.fetchall()

    if not dados:

        await interaction.response.send_message(
            "📜 Não existem fichas de "
            "jogadores neste canal."
        )

        return

    embed = discord.Embed(
        title="📜 Fichas dos jogadores",
        color=discord.Color.dark_red()
    )

    for (
        nome,
        hp_atual,
        hp_max,
        mana_atual,
        mana_max,
        xp,
        dono_id
    ) in dados:

        membro = interaction.guild.get_member(
            dono_id
        )

        jogador = (
            membro.mention
            if membro
            else f"<@{dono_id}>"
        )

        texto = (
            f"👤 {jogador}\n\n"
            f"❤️ **HP**\n"
            f"{mostrar_hp(hp_atual, hp_max)}\n\n"
            f"💧 **Mana**\n"
            f"{mostrar_mana(mana_atual, mana_max)}\n\n"
            f"⭐ **XP:** {xp}"
        )

        embed.add_field(
            name=f"⚔️ {nome}",
            value=texto,
            inline=False
        )

    await interaction.response.send_message(
        embed=embed
    )
    # ============================================================
# APAGAR PRÓPRIA FICHA
# ============================================================

@bot.tree.command(
    name="apagarficha",
    description="Apaga sua ficha deste canal."
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
        "DELETE FROM fichas WHERE id = ?",
        (f["id"],)
    )

    db.commit()

    await interaction.response.send_message(
        f"🗑️ A ficha **{f['nome']}** "
        f"foi apagada."
    )


# ============================================================
# ALTERAR FICHA DE JOGADOR
# DONO OU ADMIN
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
            "❌ Esse jogador não possui "
            "uma ficha neste canal.",
            ephemeral=True
        )

        return

    f = transformar_ficha(dados)

    if not pode_alterar_ficha(
        interaction,
        f
    ):

        await interaction.response.send_message(
            "❌ Você só pode alterar "
            "sua própria ficha.",
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
        f"⚙️ Ficha de **{f['nome']}** alterada!\n\n"
        f"❤️ **HP**\n"
        f"{mostrar_hp(hp, hp)}\n\n"
        f"💧 **Mana**\n"
        f"{mostrar_mana(mana, mana)}"
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

        f = transformar_ficha(
            dados
        )

        if (
            f["channel_id"]
            != interaction.channel.id
        ):

            await interaction.response.send_message(
                "❌ Essa ficha pertence "
                "a outro canal.",
                ephemeral=True
            )

            return

        # ====================================================
        # DANO
        # ====================================================

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

            # NPC MORRE E É APAGADO
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
                    f"💥 **{interaction.user.display_name}** "
                    f"causou **{valor} de dano** em "
                    f"**{f['nome']}**!\n\n"
                    f"💀 **{f['nome']} morreu!**\n"
                    f"🗑️ A ficha do NPC foi apagada."
                )

                return

            await interaction.response.send_message(
                f"💥 **{interaction.user.display_name}** "
                f"causou **{valor} de dano** em "
                f"**{f['nome']}**!\n\n"
                f"❤️ **HP**\n"
                f"{mostrar_hp(novo_hp, f['hp_max'])}"
            )

            return

        # ====================================================
        # CURA
        # ====================================================

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
                f"💚 **{interaction.user.display_name}** "
                f"curou **{f['nome']}** em "
                f"**{recuperado} de HP**!\n\n"
                f"❤️ **HP**\n"
                f"{mostrar_hp(novo_hp, f['hp_max'])}"
            )

            return

        # ====================================================
        # RECUPERAÇÃO DE MANA
        # ====================================================

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
                f"💧 **{interaction.user.display_name}** "
                f"recuperou **{recuperado} de Mana** "
                f"de **{f['nome']}**!\n\n"
                f"💧 **Mana**\n"
                f"{mostrar_mana(nova_mana, f['mana_max'])}"
            )

            return


# ============================================================
# SELEÇÃO DE ALVO
# ============================================================

class AlvoSelect(
    discord.ui.Select
):

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
                    description=descricao[:100]
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

        if (
            interaction.user.id
            != self.autor_id
        ):

            await interaction.response.send_message(
                "❌ Somente quem iniciou "
                "a ação pode escolher o alvo.",
                ephemeral=True
            )

            return

        ficha_id = int(
            self.values[0]
        )

        dados = buscar_ficha(
            ficha_id
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

        if (
            f["channel_id"]
            != interaction.channel.id
        ):

            await interaction.response.send_message(
                "❌ Esse alvo pertence "
                "a outro canal.",
                ephemeral=True
            )

            return

        if self.acao == "dano":

            titulo = "Quantidade de dano"

        elif self.acao == "cura":

            titulo = "Quantidade de cura"

        else:

            titulo = "Quantidade de Mana"

        await interaction.response.send_modal(
            ValorModal(
                titulo,
                self.acao,
                ficha_id
            )
        )


class AlvoView(
    discord.ui.View
):

    def __init__(
        self,
        interaction,
        acao
    ):

        super().__init__(
            timeout=60
        )

        cursor.execute("""
            SELECT id
            FROM fichas
            WHERE channel_id = ?
            LIMIT 25
        """, (
            interaction.channel.id,
        ))

        resultados = cursor.fetchall()

        if resultados:

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
            "❌ Não existem fichas "
            "neste canal.",
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
            "❌ Não existem fichas "
            "neste canal.",
            ephemeral=True
        )

        return

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
    description="Escolhe uma ficha para recuperar Mana."
)
async def recuperarmana(
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
            "❌ Não existem fichas "
            "neste canal.",
            ephemeral=True
        )

        return

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
    description="Gasta Mana da sua própria ficha."
)
@app_commands.describe(
    valor="Quantidade de Mana gasta"
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
            "❌ Você não possui uma ficha "
            "neste canal.",
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

    if valor > f["mana_atual"]:

        await interaction.response.send_message(
            "❌ Você não possui Mana suficiente.\n\n"
            f"💧 **Mana**\n"
            f"{mostrar_mana(f['mana_atual'], f['mana_max'])}",
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
        f"🔮 **{f['nome']}** "
        f"gastou **{valor} de Mana**!\n\n"
        f"💧 **Mana**\n"
        f"{mostrar_mana(nova_mana, f['mana_max'])}"
    )
    # ============================================================
# ADICIONAR XP
# ============================================================

@bot.tree.command(
    name="addxp",
    description="Adiciona XP a uma ficha de jogador."
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
            "❌ Esse jogador não possui "
            "uma ficha neste canal.",
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
            "❌ Você só pode alterar o XP "
            "da sua própria ficha.",
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
        f"⭐ **{f['nome']}** recebeu "
        f"**{valor} XP**!\n"
        f"⭐ XP atual: **{xp_atual}**"
    )


# ============================================================
# CRIAR NPC
# MESTRE OU ADMIN
# ============================================================

@bot.tree.command(
    name="criarnpc",
    description="Cria um NPC neste canal."
)
@app_commands.describe(
    aleatorio="Escolha se o NPC será aleatório",
    nome="Nome do NPC, caso não seja aleatório",
    hp="HP do NPC, caso não seja aleatório",
    mana="Mana do NPC, caso não seja aleatório"
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
            "❌ Somente o Mestre deste canal "
            "pode criar NPCs.",
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
            ?
        )
    """, (
        interaction.channel.id,
        mestre_id,
        nome,
        hp,
        hp,
        mana,
        mana,
        aleatorio_valor
    ))

    db.commit()

    embed = discord.Embed(
        title=f"👹 NPC — {nome}",
        description="NPC criado com sucesso.",
        color=discord.Color.orange()
    )

    embed.add_field(
        name="❤️ HP",
        value=mostrar_hp(hp, hp),
        inline=False
    )

    embed.add_field(
        name="💧 Mana",
        value=mostrar_mana(mana, mana),
        inline=False
    )

    embed.add_field(
        name="🎲 Criação",
        value=(
            "Aleatória"
            if aleatorio_valor
            else "Personalizada"
        ),
        inline=False
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


# ============================================================
# LISTAR NPCS
# SOMENTE MESTRE OU ADMIN
# ============================================================

@bot.tree.command(
    name="npcs",
    description="Mostra as fichas completas dos NPCs."
)
async def npcs(
    interaction: discord.Interaction
):

    if (
        not eh_mestre(interaction)
        and not eh_admin(interaction)
    ):

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

    for (
        nome,
        hp_atual,
        hp_max,
        mana_atual,
        mana_max,
        xp
    ) in resultados:

        texto = (
            f"❤️ **HP**\n"
            f"{mostrar_hp(hp_atual, hp_max)}\n\n"
            f"💧 **Mana**\n"
            f"{mostrar_mana(mana_atual, mana_max)}\n\n"
            f"⭐ **XP:** {xp}"
        )

        embed.add_field(
            name=f"👹 {nome}",
            value=texto,
            inline=False
        )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


# ============================================================
# ALTERAR NPC
# SOMENTE MESTRE OU ADMIN
# ============================================================

@bot.tree.command(
    name="alternpc",
    description="Altera um NPC."
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
            "❌ Somente o Mestre pode "
            "alterar NPCs.",
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
        f"⚙️ NPC **{nome}** alterado!\n\n"
        f"❤️ **HP**\n"
        f"{mostrar_hp(hp, hp)}\n\n"
        f"💧 **Mana**\n"
        f"{mostrar_mana(mana, mana)}"
    )


# ============================================================
# APAGAR NPC
# SOMENTE MESTRE OU ADMIN
# ============================================================

@bot.tree.command(
    name="apagarnpc",
    description="Apaga um NPC deste canal."
)
@app_commands.describe(
    nome="Nome exato do NPC"
)
async def apagarnpc(
    interaction: discord.Interaction,
    nome: str
):

    # Verifica se é o Mestre ou administrador
    if (
        not eh_mestre(interaction)
        and not eh_admin(interaction)
    ):

        await interaction.response.send_message(
            "❌ Somente o Mestre ou um administrador "
            "pode apagar NPCs.",
            ephemeral=True
        )

        return

    # Procura o NPC neste canal
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

    # NPC não encontrado
    if resultado is None:

        await interaction.response.send_message(
            f"❌ Não encontrei um NPC chamado "
            f"**{nome}** neste canal.",
            ephemeral=True
        )

        return

    # Apaga o NPC
    cursor.execute(
        "DELETE FROM fichas WHERE id = ?",
        (resultado[0],)
    )

    db.commit()

    # Confirmação
    await interaction.response.send_message(
        f"🗑️ O NPC **{nome}** foi apagado."
    )
    # ============================================================
# VER FICHA DE OUTRO JOGADOR
# ============================================================

@bot.tree.command(
    name="verficha",
    description="Visualiza individualmente a ficha de outro jogador."
)
@app_commands.describe(
    jogador="Jogador cuja ficha você deseja visualizar"
)
async def verficha(
    interaction: discord.Interaction,
    jogador: discord.Member
):

    # Procura a ficha do jogador neste canal
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

    # Cria a ficha visível
    embed = discord.Embed(
        title=f"⚔️ {f['nome']}",
        description=(
            f"👤 Jogador: {jogador.mention}"
        ),
        color=discord.Color.dark_red()
    )

    embed.add_field(
        name="❤️ HP",
        value=mostrar_hp(
            f["hp_atual"],
            f["hp_max"]
        ),
        inline=False
    )

    embed.add_field(
        name="💧 Mana",
        value=mostrar_mana(
            f["mana_atual"],
            f["mana_max"]
        ),
        inline=False
    )

    embed.add_field(
        name="⭐ XP",
        value=str(f["xp"]),
        inline=False
    )

    await interaction.response.send_message(
        embed=embed
    )
    # ============================================================
# INICIAR O BOT
# ============================================================

bot.run(TOKEN)
