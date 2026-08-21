import math
import discord

from discord import app_commands

from database import cursor

from fichas import (
    transformar_ficha,
    estado_hp,
    estado_mana,
)


# ============================================================
# CONFIGURAÇÃO DO PAINEL
# ============================================================

ITENS_POR_PAGINA = 5


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

    membro = None

    if (
        guild is not None
        and dono_id is not None
    ):

        membro = guild.get_member(
            dono_id
        )

    if membro is not None:

        titulo = (
            f"👤 **{nome}** "
            f"• {membro.mention}"
        )

    else:

        titulo = (
            f"👤 **{nome}**"
        )

    return (
        f"{titulo}\n"
        f"❤️ HP: **{hp_atual}/{hp_max}** "
        f"• {hp_estado}\n"
        f"🔵 Mana: **{mana_atual}/{mana_max}** "
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

    nome_visual = (
        f"{nome} #{ficha_id}"
    )

    return (
        f"👹 **{nome_visual}**\n"
        f"❤️ HP: **{hp_atual}/{hp_max}** "
        f"• {hp_estado}\n"
        f"🔵 Mana: **{mana_atual}/{mana_max}** "
        f"• {mana_estado}"
    )


# ============================================================
# MONTAR ITENS DO PAINEL
# ============================================================

def montar_itens_painel(
    jogadores,
    npcs,
    tipo
):

    itens = []

    # ========================================================
    # SOMENTE JOGADORES
    # ========================================================

    if tipo == "jogadores":

        for ficha in jogadores:

            itens.append(
                (
                    "jogador",
                    ficha
                )
            )

        return itens

    # ========================================================
    # SOMENTE NPCS
    # ========================================================

    if tipo == "npcs":

        for ficha in npcs:

            itens.append(
                (
                    "npc",
                    ficha
                )
            )

        return itens

    # ========================================================
    # AMBOS
    # ========================================================

    for ficha in jogadores:

        itens.append(
            (
                "jogador",
                ficha
            )
        )

    for ficha in npcs:

        itens.append(
            (
                "npc",
                ficha
            )
        )

    return itens


# ============================================================
# TOTAL DE PÁGINAS
# ============================================================

def calcular_total_paginas(
    quantidade
):

    if quantidade <= 0:

        return 1

    return math.ceil(
        quantidade
        / ITENS_POR_PAGINA
    )


# ============================================================
# TÍTULO DO PAINEL
# ============================================================

def obter_titulo_painel(
    tipo
):

    if tipo == "jogadores":

        return (
            "👤 PAINEL DE JOGADORES"
        )

    if tipo == "npcs":

        return (
            "👹 PAINEL DE NPCs"
        )

    return (
        "📋 PAINEL DA MESA"
    )


# ============================================================
# DESCRIÇÃO DO PAINEL
# ============================================================

def obter_descricao_painel(
    jogadores,
    npcs,
    tipo
):

    if tipo == "jogadores":

        return (
            f"👤 Jogadores ativos: "
            f"**{len(jogadores)}**"
        )

    if tipo == "npcs":

        return (
            f"👹 NPCs ativos: "
            f"**{len(npcs)}**"
        )

    total = (
        len(jogadores)
        + len(npcs)
    )

    return (
        f"📊 **Resumo da mesa**\n\n"
        f"👤 Jogadores: **{len(jogadores)}**\n"
        f"👹 NPCs: **{len(npcs)}**\n"
        f"📜 Total de fichas: **{total}**"
    )


# ============================================================
# CRIAR PÁGINA DO PAINEL
# ============================================================

def criar_pagina_painel(
    channel_id,
    guild,
    pagina,
    tipo
):

    jogadores, npcs = (
        buscar_fichas_painel(
            channel_id
        )
    )

    itens = montar_itens_painel(
        jogadores,
        npcs,
        tipo
    )

    total_itens = len(
        itens
    )

    total_paginas = (
        calcular_total_paginas(
            total_itens
        )
    )

    if pagina < 0:

        pagina = 0

    if pagina >= total_paginas:

        pagina = (
            total_paginas - 1
        )

    inicio = (
        pagina
        * ITENS_POR_PAGINA
    )

    fim = (
        inicio
        + ITENS_POR_PAGINA
    )

    itens_pagina = itens[
        inicio:fim
    ]

    embed = discord.Embed(
        title=obter_titulo_painel(
            tipo
        ),
        description=obter_descricao_painel(
            jogadores,
            npcs,
            tipo
        ),
        color=discord.Color.dark_red()
    )

    jogadores_pagina = []

    npcs_pagina = []

    for tipo_ficha, ficha in itens_pagina:

        if tipo_ficha == "jogador":

            jogadores_pagina.append(
                ficha
            )

        elif tipo_ficha == "npc":

            npcs_pagina.append(
                ficha
            )

    # ========================================================
    # JOGADORES
    # ========================================================

    if jogadores_pagina:

        texto_jogadores = []

        for ficha in jogadores_pagina:

            texto_jogadores.append(
                formatar_jogador(
                    ficha,
                    guild
                )
            )

        embed.add_field(
            name="👤 JOGADORES",
            value="\n\n".join(
                texto_jogadores
            ),
            inline=False
        )

    # ========================================================
    # NPCS
    # ========================================================

    if npcs_pagina:

        texto_npcs = []

        for ficha in npcs_pagina:

            texto_npcs.append(
                formatar_npc(
                    ficha
                )
            )

        embed.add_field(
            name="👹 NPCs",
            value="\n\n".join(
                texto_npcs
            ),
            inline=False
        )

    # ========================================================
    # LISTA VAZIA
    # ========================================================

    if not itens_pagina:

        if tipo == "jogadores":

            mensagem_vazia = (
                "Nenhum jogador possui "
                "ficha nesta mesa."
            )

        elif tipo == "npcs":

            mensagem_vazia = (
                "Nenhum NPC ativo "
                "nesta mesa."
            )

        else:

            mensagem_vazia = (
                "Não existem fichas "
                "nesta mesa."
            )

        embed.add_field(
            name="📭 Nenhuma ficha",
            value=mensagem_vazia,
            inline=False
        )

    embed.set_footer(
        text=(
            f"Página {pagina + 1}/{total_paginas} "
            f"• {total_itens} ficha(s)"
        )
    )

    return (
        embed,
        total_paginas
    )


# ============================================================
# VIEW DO PAINEL
# ============================================================

class PainelView(
    discord.ui.View
):

    def __init__(
        self,
        channel_id,
        guild,
        autor_id,
        tipo,
        pagina=0
    ):

        super().__init__(
            timeout=300
        )

        self.channel_id = (
            channel_id
        )

        self.guild = guild

        self.autor_id = (
            autor_id
        )

        self.tipo = (
            tipo
        )

        self.pagina = (
            pagina
        )

        self.atualizar_total_paginas()

        self.atualizar_botoes()


    # ========================================================
    # RECALCULAR TOTAL DE PÁGINAS
    # ========================================================

    def atualizar_total_paginas(
        self
    ):

        jogadores, npcs = (
            buscar_fichas_painel(
                self.channel_id
            )
        )

        itens = montar_itens_painel(
            jogadores,
            npcs,
            self.tipo
        )

        self.total_paginas = (
            calcular_total_paginas(
                len(itens)
            )
        )


    # ========================================================
    # ATUALIZAR BOTÕES
    # ========================================================

    def atualizar_botoes(
        self
    ):

        self.anterior.disabled = (
            self.pagina <= 0
        )

        self.proxima.disabled = (
            self.pagina
            >= self.total_paginas - 1
        )


    # ========================================================
    # VERIFICAR USUÁRIO
    # ========================================================

    async def interaction_check(
        self,
        interaction: discord.Interaction
    ):

        if (
            interaction.user.id
            != self.autor_id
        ):

            await interaction.response.send_message(
                "❌ Somente quem abriu o painel "
                "pode usar estes botões.",
                ephemeral=True
            )

            return False

        return True


    # ========================================================
    # ATUALIZAR PAINEL
    # ========================================================

    async def atualizar_painel(
        self,
        interaction
    ):

        self.atualizar_total_paginas()

        if (
            self.pagina
            >= self.total_paginas
        ):

            self.pagina = max(
                0,
                self.total_paginas - 1
            )

        embed, total_paginas = (
            criar_pagina_painel(
                self.channel_id,
                self.guild,
                self.pagina,
                self.tipo
            )
        )

        self.total_paginas = (
            total_paginas
        )

        self.atualizar_botoes()

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )


    # ========================================================
    # BOTÃO ANTERIOR
    # ========================================================

    @discord.ui.button(
        label="◀ Anterior",
        style=discord.ButtonStyle.secondary
    )
    async def anterior(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if self.pagina > 0:

            self.pagina -= 1

        await self.atualizar_painel(
            interaction
        )


    # ========================================================
    # BOTÃO PRÓXIMA
    # ========================================================

    @discord.ui.button(
        label="Próxima ▶",
        style=discord.ButtonStyle.secondary
    )
    async def proxima(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if (
            self.pagina
            < self.total_paginas - 1
        ):

            self.pagina += 1

        await self.atualizar_painel(
            interaction
        )


# ============================================================
# REGISTRAR COMANDOS DO PAINEL
# ============================================================

def registrar_comandos_painel(
    bot
):

    @bot.tree.command(
        name="painel",
        description=(
            "Mostra as fichas ativas da mesa."
        )
    )
    @app_commands.describe(
        tipo=(
            "Escolha quais fichas deseja visualizar"
        )
    )
    @app_commands.choices(
        tipo=[
            app_commands.Choice(
                name="📋 Ambos",
                value="ambos"
            ),
            app_commands.Choice(
                name="👤 Jogadores",
                value="jogadores"
            ),
            app_commands.Choice(
                name="👹 NPCs",
                value="npcs"
            )
        ]
    )
    async def painel(
        interaction: discord.Interaction,
        tipo: app_commands.Choice[str] = None
    ):

        if interaction.channel is None:

            await interaction.response.send_message(
                "❌ Este comando precisa ser usado "
                "em um canal da mesa.",
                ephemeral=True
            )

            return

        # ====================================================
        # PADRÃO = AMBOS
        # ====================================================

        if tipo is None:

            tipo_escolhido = (
                "ambos"
            )

        else:

            tipo_escolhido = (
                tipo.value
            )

        jogadores, npcs = (
            buscar_fichas_painel(
                interaction.channel.id
            )
        )

        itens = montar_itens_painel(
            jogadores,
            npcs,
            tipo_escolhido
        )

        # ====================================================
        # NENHUMA FICHA PARA O FILTRO
        # ====================================================

        if not itens:

            if tipo_escolhido == "jogadores":

                mensagem = (
                    "👤 Nenhum jogador possui "
                    "ficha nesta mesa."
                )

            elif tipo_escolhido == "npcs":

                mensagem = (
                    "👹 Não existem NPCs ativos "
                    "nesta mesa."
                )

            else:

                mensagem = (
                    "📋 Esta mesa ainda não "
                    "possui fichas."
                )

            await interaction.response.send_message(
                mensagem,
                ephemeral=True
            )

            return

        # ====================================================
        # CRIAR PAINEL
        # ====================================================

        embed, total_paginas = (
            criar_pagina_painel(
                interaction.channel.id,
                interaction.guild,
                0,
                tipo_escolhido
            )
        )

        view = PainelView(
            interaction.channel.id,
            interaction.guild,
            interaction.user.id,
            tipo_escolhido,
            pagina=0
        )

        await interaction.response.send_message(
            embed=embed,
            view=view
        )
