import discord

from database import (
    cursor,
)

from fichas import (
    transformar_ficha,
    criar_pagina_status,
    FichaView,
)

from comando.permissoes import (
    pode_usar_painel,
)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

ITENS_POR_PAGINA = 5


# ============================================================
# BUSCAR FICHAS
# ============================================================

def buscar_fichas_painel(
    channel_id,
    filtro="ambos"
):

    if filtro == "jogadores":

        cursor.execute("""
            SELECT *
            FROM fichas
            WHERE channel_id = ?
            AND tipo = 'jogador'
            ORDER BY nome
        """, (
            channel_id,
        ))

    elif filtro == "npcs":

        cursor.execute("""
            SELECT *
            FROM fichas
            WHERE channel_id = ?
            AND tipo = 'npc'
            ORDER BY nome
        """, (
            channel_id,
        ))

    else:

        cursor.execute("""
            SELECT *
            FROM fichas
            WHERE channel_id = ?
            ORDER BY tipo, nome
        """, (
            channel_id,
        ))

    return [
        transformar_ficha(
            dados
        )
        for dados in cursor.fetchall()
    ]


# ============================================================
# BUSCAR FICHA PELO ID
# ============================================================

def buscar_ficha_painel(
    channel_id,
    ficha_id
):

    cursor.execute("""
        SELECT *
        FROM fichas
        WHERE channel_id = ?
        AND id = ?
        LIMIT 1
    """, (
        channel_id,
        ficha_id
    ))

    dados = cursor.fetchone()

    if dados is None:

        return None

    return transformar_ficha(
        dados
    )


# ============================================================
# CRIAR TEXTO DO PAINEL
# ============================================================

def criar_texto_painel(
    fichas,
    pagina,
    filtro
):

    total = len(
        fichas
    )

    if total == 0:

        return (
            "📋 **PAINEL DA MESA**\n\n"
            "Nenhuma ficha encontrada "
            "com este filtro."
        )

    total_paginas = max(
        1,
        (
            total
            + ITENS_POR_PAGINA
            - 1
        )
        // ITENS_POR_PAGINA
    )

    pagina = max(
        0,
        min(
            pagina,
            total_paginas - 1
        )
    )

    inicio = (
        pagina
        * ITENS_POR_PAGINA
    )

    fim = (
        inicio
        + ITENS_POR_PAGINA
    )

    fichas_pagina = fichas[
        inicio:fim
    ]

    nomes_filtros = {
        "ambos": "Jogadores + NPCs",
        "jogadores": "Jogadores",
        "npcs": "NPCs",
    }

    linhas = [
        "📋 **PAINEL DA MESA**",
        "",
        (
            "🔎 Filtro: "
            f"**{nomes_filtros.get(filtro, 'Ambos')}**"
        ),
        (
            f"📄 Página: "
            f"**{pagina + 1}/{total_paginas}**"
        ),
        (
            f"📚 Fichas encontradas: "
            f"**{total}**"
        ),
        "",
    ]

    for ficha in fichas_pagina:

        if (
            ficha.get("tipo")
            == "npc"
        ):

            identificacao = (
                f"👹 **{ficha.get('nome', 'NPC')} "
                f"#{ficha.get('id', '?')}**"
            )

        else:

            identificacao = (
                f"👤 **{ficha.get('nome', 'Jogador')}**"
            )

        linhas.append(
            identificacao
        )

        linhas.append(
            (
                f"❤️ {ficha.get('hp_atual', 0)}/"
                f"{ficha.get('hp_max', 0)}"
                "  •  "
                f"🔵 {ficha.get('mana_atual', 0)}/"
                f"{ficha.get('mana_max', 0)}"
                "  •  "
                f"✨ {ficha.get('xp', 0)} XP"
            )
        )

        linhas.append(
            ""
        )

    return "\n".join(
        linhas
    )


# ============================================================
# SELECT DE FICHAS
# ============================================================

class PainelFichaSelect(
    discord.ui.Select
):

    def __init__(
        self,
        view_painel
    ):

        self.view_painel = (
            view_painel
        )

        fichas = (
            view_painel.fichas_pagina()
        )

        opcoes = []

        for ficha in fichas:

            if (
                ficha.get("tipo")
                == "npc"
            ):

                label = (
                    f"{ficha.get('nome', 'NPC')} "
                    f"#{ficha.get('id', '?')}"
                )

                emoji = "👹"

            else:

                label = ficha.get(
                    "nome",
                    "Jogador"
                )

                emoji = "👤"

            opcoes.append(
                discord.SelectOption(
                    label=label[:100],
                    value=str(
                        ficha["id"]
                    ),
                    emoji=emoji
                )
            )

        if not opcoes:

            opcoes.append(
                discord.SelectOption(
                    label="Nenhuma ficha",
                    value="nenhuma",
                    emoji="❌"
                )
            )

        super().__init__(
            placeholder=(
                "Selecione uma ficha "
                "para visualizar..."
            ),
            min_values=1,
            max_values=1,
            options=opcoes,
            disabled=(
                len(fichas) == 0
            )
        )


    async def callback(
        self,
        interaction: discord.Interaction
    ):

        if (
            self.values[0]
            == "nenhuma"
        ):

            return

        ficha_id = int(
            self.values[0]
        )

        ficha = buscar_ficha_painel(
            interaction.channel.id,
            ficha_id
        )

        if ficha is None:

            await interaction.response.send_message(
                "❌ Esta ficha não existe mais.",
                ephemeral=True
            )

            return

        jogador = None

        if (
            ficha.get("tipo")
            == "jogador"
        ):

            dono_id = ficha.get(
                "dono_id"
            )

            if (
                dono_id is not None
                and interaction.guild
                is not None
            ):

                jogador = (
                    interaction.guild
                    .get_member(
                        dono_id
                    )
                )

        await interaction.response.send_message(
            embed=criar_pagina_status(
                ficha,
                jogador
            ),
            view=FichaView(
                ficha,
                jogador
            ),
            ephemeral=True
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
        usuario_id,
        filtro="ambos",
        pagina=0
    ):

        super().__init__(
            timeout=300
        )

        self.channel_id = (
            channel_id
        )

        self.usuario_id = (
            usuario_id
        )

        self.filtro = filtro
        self.pagina = pagina

        self.fichas = []

        self.recarregar()


    # ========================================================
    # CONTROLE DE USUÁRIO
    # ========================================================

    async def interaction_check(
        self,
        interaction: discord.Interaction
    ):

        if (
            interaction.user.id
            != self.usuario_id
        ):

            await interaction.response.send_message(
                "❌ Somente quem abriu este painel "
                "pode usar os controles.",
                ephemeral=True
            )

            return False

        return True


    # ========================================================
    # RECARREGAR
    # ========================================================

    def recarregar(
        self
    ):

        self.fichas = (
            buscar_fichas_painel(
                self.channel_id,
                self.filtro
            )
        )

        total_paginas = (
            self.total_paginas()
        )

        if (
            self.pagina
            >= total_paginas
        ):

            self.pagina = max(
                0,
                total_paginas - 1
            )

        self.reconstruir()


    # ========================================================
    # TOTAL DE PÁGINAS
    # ========================================================

    def total_paginas(
        self
    ):

        if not self.fichas:

            return 1

        return (
            len(self.fichas)
            + ITENS_POR_PAGINA
            - 1
        ) // ITENS_POR_PAGINA


    # ========================================================
    # FICHAS DA PÁGINA
    # ========================================================

    def fichas_pagina(
        self
    ):

        inicio = (
            self.pagina
            * ITENS_POR_PAGINA
        )

        fim = (
            inicio
            + ITENS_POR_PAGINA
        )

        return self.fichas[
            inicio:fim
        ]


    # ========================================================
    # RECONSTRUIR COMPONENTES
    # ========================================================

    def reconstruir(
        self
    ):

        self.clear_items()

        self.add_item(
            PainelFiltroSelect(
                self
            )
        )

        self.add_item(
            PainelFichaSelect(
                self
            )
        )

        anterior = discord.ui.Button(
            label="◀ Anterior",
            style=(
                discord.ButtonStyle.secondary
            ),
            disabled=(
                self.pagina <= 0
            )
        )

        proxima = discord.ui.Button(
            label="Próxima ▶",
            style=(
                discord.ButtonStyle.secondary
            ),
            disabled=(
                self.pagina
                >= self.total_paginas() - 1
            )
        )

        atualizar = discord.ui.Button(
            label="Atualizar",
            emoji="🔄",
            style=(
                discord.ButtonStyle.primary
            )
        )

        anterior.callback = (
            self.ir_anterior
        )

        proxima.callback = (
            self.ir_proxima
        )

        atualizar.callback = (
            self.atualizar
        )

        self.add_item(
            anterior
        )

        self.add_item(
            proxima
        )

        self.add_item(
            atualizar
        )


    # ========================================================
    # EDITAR PAINEL
    # ========================================================

    async def editar(
        self,
        interaction
    ):

        await interaction.response.edit_message(
            content=criar_texto_painel(
                self.fichas,
                self.pagina,
                self.filtro
            ),
            view=self
        )


    # ========================================================
    # ANTERIOR
    # ========================================================

    async def ir_anterior(
        self,
        interaction
    ):

        if self.pagina > 0:

            self.pagina -= 1

        self.reconstruir()

        await self.editar(
            interaction
        )


    # ========================================================
    # PRÓXIMA
    # ========================================================

    async def ir_proxima(
        self,
        interaction
    ):

        if (
            self.pagina
            < self.total_paginas() - 1
        ):

            self.pagina += 1

        self.reconstruir()

        await self.editar(
            interaction
        )


    # ========================================================
    # ATUALIZAR
    # ========================================================

    async def atualizar(
        self,
        interaction
    ):

        self.recarregar()

        await self.editar(
            interaction
        )


# ============================================================
# SELECT DE FILTRO
# ============================================================

class PainelFiltroSelect(
    discord.ui.Select
):

    def __init__(
        self,
        view_painel
    ):

        self.view_painel = (
            view_painel
        )

        super().__init__(
            placeholder="Filtrar fichas...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Jogadores + NPCs",
                    value="ambos",
                    emoji="📋",
                    default=(
                        view_painel.filtro
                        == "ambos"
                    )
                ),
                discord.SelectOption(
                    label="Jogadores",
                    value="jogadores",
                    emoji="👤",
                    default=(
                        view_painel.filtro
                        == "jogadores"
                    )
                ),
                discord.SelectOption(
                    label="NPCs",
                    value="npcs",
                    emoji="👹",
                    default=(
                        view_painel.filtro
                        == "npcs"
                    )
                ),
            ]
        )


    async def callback(
        self,
        interaction: discord.Interaction
    ):

        self.view_painel.filtro = (
            self.values[0]
        )

        self.view_painel.pagina = 0

        self.view_painel.recarregar()

        await self.view_painel.editar(
            interaction
        )


# ============================================================
# REGISTRAR COMANDO
# ============================================================

def registrar_comandos_painel(
    bot
):

    @bot.tree.command(
        name="painel",
        description="Mostra o painel de fichas da mesa."
    )
    async def painel(
        interaction: discord.Interaction
    ):

        if not pode_usar_painel(
            interaction
        ):

            await interaction.response.send_message(
                "❌ Você não possui permissão "
                "para utilizar o painel.",
                ephemeral=True
            )

            return

        view = PainelView(
            interaction.channel.id,
            interaction.user.id
        )

        await interaction.response.send_message(
            criar_texto_painel(
                view.fichas,
                view.pagina,
                view.filtro
            ),
            view=view
        )
