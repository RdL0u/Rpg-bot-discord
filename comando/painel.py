import discord

from database import cursor

from fichas import (
    transformar_ficha,
    estado_hp,
    estado_mana,
)


# ============================================================
# CONFIGURAÇÃO INICIAL DO PAINEL
# ============================================================

LIMITE_JOGADORES = 10
LIMITE_NPCS = 10


# ============================================================
# BUSCAR FICHAS DA MESA
# ============================================================

def buscar_fichas_painel(channel_id):

    cursor.execute("""
        SELECT *
        FROM fichas
        WHERE channel_id = ?
        ORDER BY
            tipo DESC,
            nome COLLATE NOCASE,
            id
    """, (
        channel_id,
    ))

    resultados = cursor.fetchall()

    jogadores = []
    npcs = []

    for dados in resultados:

        ficha = transformar_ficha(
            dados
        )

        if ficha["tipo"] == "jogador":

            jogadores.append(
                ficha
            )

        elif ficha["tipo"] == "npc":

            npcs.append(
                ficha
            )

    return jogadores, npcs


# ============================================================
# FORMATAR JOGADOR
# ============================================================

def formatar_jogador(
    ficha,
    guild
):

    nome = ficha.get(
        "nome",
        "Sem nome"
    )

    dono_id = ficha.get(
        "dono_id"
    )

    membro = None

    if (
        guild is not None
        and dono_id is not None
    ):

        membro = guild.get_member(
            dono_id
        )

    hp_atual = ficha.get(
        "hp_atual",
        0
    )

    hp_max = ficha.get(
        "hp_max",
        0
    )

    mana_atual = ficha.get(
        "mana_atual",
        0
    )

    mana_max = ficha.get(
        "mana_max",
        0
    )

    hp_estado = estado_hp(
        hp_atual,
        hp_max
    )

    mana_estado = estado_mana(
        mana_atual,
        mana_max
    )

    if membro is not None:

        identificacao = (
            f"👤 **{nome}** • {membro.mention}"
        )

    else:

        identificacao = (
            f"👤 **{nome}**"
        )

    return (
        f"{identificacao}\n"
        f"❤️ **{hp_atual}/{hp_max}** "
        f"• {hp_estado}\n"
        f"🔵 **{mana_atual}/{mana_max}** "
        f"• {mana_estado}"
    )


# ============================================================
# FORMATAR NPC
# ============================================================

def formatar_npc(
    ficha
):

    ficha_id = ficha.get(
        "id"
    )

    nome = ficha.get(
        "nome",
        "Sem nome"
    )

    hp_atual = ficha.get(
        "hp_atual",
        0
    )

    hp_max = ficha.get(
        "hp_max",
        0
    )

    mana_atual = ficha.get(
        "mana_atual",
        0
    )

    mana_max = ficha.get(
        "mana_max",
        0
    )

    hp_estado = estado_hp(
        hp_atual,
        hp_max
    )

    mana_estado = estado_mana(
        mana_atual,
        mana_max
    )

    return (
        f"👹 **{nome} #{ficha_id}**\n"
        f"❤️ **{hp_atual}/{hp_max}** "
        f"• {hp_estado}\n"
        f"🔵 **{mana_atual}/{mana_max}** "
        f"• {mana_estado}"
    )


# ============================================================
# CRIAR TEXTO DOS JOGADORES
# ============================================================

def criar_texto_jogadores(
    jogadores,
    guild
):

    if not jogadores:

        return (
            "*Nenhum jogador possui ficha "
            "nesta mesa.*"
        )

    linhas = []

    jogadores_visiveis = (
        jogadores[
            :LIMITE_JOGADORES
        ]
    )

    for ficha in jogadores_visiveis:

        linhas.append(
            formatar_jogador(
                ficha,
                guild
            )
        )

    restantes = (
        len(jogadores)
        - len(jogadores_visiveis)
    )

    if restantes > 0:

        linhas.append(
            f"*... e mais "
            f"**{restantes} jogador(es)**.*"
        )

    return "\n\n".join(
        linhas
    )


# ============================================================
# CRIAR TEXTO DOS NPCS
# ============================================================

def criar_texto_npcs(
    npcs
):

    if not npcs:

        return (
            "*Nenhum NPC ativo "
            "nesta mesa.*"
        )

    linhas = []

    npcs_visiveis = (
        npcs[
            :LIMITE_NPCS
        ]
    )

    for ficha in npcs_visiveis:

        linhas.append(
            formatar_npc(
                ficha
            )
        )

    restantes = (
        len(npcs)
        - len(npcs_visiveis)
    )

    if restantes > 0:

        linhas.append(
            f"*... e mais "
            f"**{restantes} NPC(s)**.*"
        )

    return "\n\n".join(
        linhas
    )


# ============================================================
# CRIAR EMBED DO PAINEL
# ============================================================

def criar_painel(
    channel_id,
    guild
):

    jogadores, npcs = (
        buscar_fichas_painel(
            channel_id
        )
    )

    total = (
        len(jogadores)
        + len(npcs)
    )

    embed = discord.Embed(
        title="📋 PAINEL DA MESA",
        description=(
            f"**{total} ficha(s) ativa(s)**\n"
            f"👤 Jogadores: **{len(jogadores)}**\n"
            f"👹 NPCs: **{len(npcs)}**"
        ),
        color=discord.Color.dark_red()
    )

    embed.add_field(
        name=(
            f"👤 JOGADORES "
            f"({len(jogadores)})"
        ),
        value=criar_texto_jogadores(
            jogadores,
            guild
        ),
        inline=False
    )

    embed.add_field(
        name=(
            f"👹 NPCs "
            f"({len(npcs)})"
        ),
        value=criar_texto_npcs(
            npcs
        ),
        inline=False
    )

    embed.set_footer(
        text=(
            "Painel da Mesa • "
            "HP e Mana em tempo real"
        )
    )

    return embed


# ============================================================
# REGISTRAR COMANDOS DO PAINEL
# ============================================================

def registrar_comandos_painel(
    bot
):

    @bot.tree.command(
        name="painel",
        description=(
            "Mostra jogadores e NPCs "
            "ativos da mesa."
        )
    )
    async def painel(
        interaction: discord.Interaction
    ):

        if interaction.channel is None:

            await interaction.response.send_message(
                "❌ Este comando precisa ser usado "
                "em um canal da mesa.",
                ephemeral=True
            )

            return

        jogadores, npcs = (
            buscar_fichas_painel(
                interaction.channel.id
            )
        )

        if (
            not jogadores
            and not npcs
        ):

            await interaction.response.send_message(
                "📋 Esta mesa ainda não possui fichas.",
                ephemeral=True
            )

            return

        embed = criar_painel(
            interaction.channel.id,
            interaction.guild
        )

        await interaction.response.send_message(
            embed=embed
        )
