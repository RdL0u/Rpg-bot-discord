import discord

from datetime import (
    datetime,
    timezone,
)

from database import (
    buscar_historico,
)

from comando.permissoes import (
    pode_ver_historico,
)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

ITENS_POR_PAGINA = 5


# ============================================================
# FILTROS
# ============================================================

FILTROS = {
    "tudo": "Tudo",
    "jogadores": "Jogadores",
    "npcs": "NPCs",
    "hp": "HP",
    "mana": "Mana",
    "xp": "XP",
    "atributos": "Atributos",
    "pericias": "Perícias",
    "rolagens": "Rolagens",
}


# ============================================================
# NORMALIZAR REGISTRO
# ============================================================

def normalizar_registro(
    registro
):

    if isinstance(
        registro,
        dict
    ):

        return registro

    colunas = [
        "id",
        "channel_id",
        "ficha_id",
        "ficha_nome",
        "ficha_tipo",
        "usuario_id",
        "acao",
        "campo",
        "valor_anterior",
        "valor_novo",
        "descricao",
        "criado_em",
    ]

    resultado = {}

    for indice, valor in enumerate(
        registro
    ):

        if indice < len(
            colunas
        ):

            resultado[
                colunas[indice]
            ] = valor

    return resultado


# ============================================================
# BUSCAR HISTÓRICO DA MESA
# ============================================================

def carregar_historico(
    channel_id
):

    registros = buscar_historico(
        channel_id,
        limite=500
    )

    return [
        normalizar_registro(
            registro
        )
        for registro in registros
    ]


# ============================================================
# APLICAR FILTRO
# ============================================================

def filtrar_historico(
    registros,
    filtro
):

    if filtro == "tudo":

        return registros

    if filtro == "jogadores":

        return [
            registro
            for registro in registros
            if (
                registro.get(
                    "ficha_tipo"
                )
                == "jogador"
            )
        ]

    if filtro == "npcs":

        return [
            registro
            for registro in registros
            if (
                registro.get(
                    "ficha_tipo"
                )
                == "npc"
            )
        ]

    if filtro == "hp":

        return [
            registro
            for registro in registros
            if (
                registro.get("campo")
                == "hp"
                or registro.get("acao")
                in {
                    "dano",
                    "cura",
                    "npc_derrotado",
                }
            )
        ]

    if filtro == "mana":

        return [
            registro
            for registro in registros
            if (
                registro.get("campo")
                == "mana"
                or "mana"
                in str(
                    registro.get(
                        "acao",
                        ""
                    )
                ).lower()
            )
        ]

    if filtro == "xp":

        return [
            registro
            for registro in registros
            if (
                registro.get("campo")
                == "xp"
                or registro.get("acao")
                == "xp"
            )
        ]

    if filtro == "atributos":

        return [
            registro
            for registro in registros
            if (
                registro.get("acao")
                == "atributo"
                or registro.get("campo")
                in {
                    "forca",
                    "destreza",
                    "vigor",
                    "inteligencia",
                    "carisma",
                    "raciocinio",
                }
            )
        ]

    if filtro == "pericias":

        return [
            registro
            for registro in registros
            if (
                registro.get("acao")
                == "pericia"
            )
        ]

    if filtro == "rolagens":

        return [
            registro
            for registro in registros
            if (
                registro.get("acao")
                == "rolagem"
            )
        ]

    return registros


# ============================================================
# FORMATAR DATA PARA DISCORD
# ============================================================

def timestamp_discord(
    valor
):

    if not valor:

        return "Data desconhecida"

    try:

        if isinstance(
            valor,
            datetime
        ):

            data = valor

        else:

            texto = str(
                valor
            )

            data = datetime.fromisoformat(
                texto
            )

        if (
            data.tzinfo
            is None
        ):

            data = data.replace(
                tzinfo=timezone.utc
            )

        unix = int(
            data.timestamp()
        )

        return (
            f"<t:{unix}:R>"
        )

    except Exception:

        return str(
            valor
        )


# ============================================================
# NOME DA FICHA
# ============================================================

def nome_ficha_historico(
    registro
):

    nome = registro.get(
        "ficha_nome"
    ) or "Ficha"

    if (
        registro.get(
            "ficha_tipo"
        )
        == "npc"
    ):

        ficha_id = registro.get(
            "ficha_id"
        )

        if ficha_id is not None:

            return (
                f"{nome} #{ficha_id}"
            )

    return nome


# ============================================================
# EMOJI DA AÇÃO
# ============================================================

def emoji_acao(
    registro
):

    acao = str(
        registro.get(
            "acao",
            ""
        )
    ).lower()

    campo = str(
        registro.get(
            "campo",
            ""
        )
    ).lower()

    if acao == "rolagem":

        return "🎲"

    if (
        acao == "dano"
        or (
            campo == "hp"
            and "cura" not in acao
        )
    ):

        return "❤️"

    if acao == "cura":

        return "💚"

    if (
        campo == "mana"
        or "mana" in acao
    ):

        return "🔵"

    if (
        campo == "xp"
        or acao == "xp"
    ):

        return "✨"

    if acao == "atributo":

        return "⚔️"

    if acao == "pericia":

        return "📚"

    if acao in {
        "npc_apagado",
        "ficha_apagada",
    }:

        return "🗑️"

    if acao == "npc_derrotado":

        return "💀"

    return "📝"


# ============================================================
# FORMATAR REGISTRO
# ============================================================

def formatar_registro(
    registro
):

    nome = nome_ficha_historico(
        registro
    )

    emoji = emoji_acao(
        registro
    )

    descricao = registro.get(
        "descricao"
    )

    campo = registro.get(
        "campo"
    )

    anterior = registro.get(
        "valor_anterior"
    )

    novo = registro.get(
        "valor_novo"
    )

    usuario_id = registro.get(
        "usuario_id"
    )

    data = timestamp_discord(
        registro.get(
            "criado_em"
        )
    )

    acao = registro.get(
        "acao"
    )

    linhas = [
        f"{emoji} **{nome}**"
    ]

    # ========================================================
    # ROLAGEM
    # ========================================================

    if acao == "rolagem":

        if descricao:

            linhas.append(
                descricao
            )

    else:

        if descricao:

            linhas.append(
                str(
                    descricao
                )
            )

        elif campo:

            linhas.append(
                f"`{campo}` alterado."
            )

        if (
            anterior is not None
            or novo is not None
        ):

            linhas.append(
                (
                    f"**{anterior}**"
                    f" → "
                    f"**{novo}**"
                )
            )

    # ========================================================
    # USUÁRIO / DATA
    # ========================================================

    if usuario_id:

        linhas.append(
            f"👤 <@{usuario_id}> • {data}"
        )

    else:

        linhas.append(
            f"🕒 {data}"
        )

    return "\n".join(
        linhas
    )


# ============================================================
# CRIAR EMBED
# ============================================================

def criar_embed_historico(
    registros,
    pagina,
    filtro
):

    total = len(
        registros
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

    embed = discord.Embed(
        title="📜 HISTÓRICO DA MESA",
        color=discord.Color.dark_red()
    )

    embed.description = (
        f"🔎 Filtro: "
        f"**{FILTROS.get(filtro, 'Tudo')}**\n"
        f"📄 Página: "
        f"**{pagina + 1}/{total_paginas}**\n"
        f"📝 Registros: **{total}**"
    )

    if total == 0:

        embed.add_field(
            name="Nenhum registro",
            value=(
                "Não há alterações registradas "
                "para este filtro."
            ),
            inline=False
        )

        return embed

    inicio = (
        pagina
        * ITENS_POR_PAGINA
    )

    fim = (
        inicio
        + ITENS_POR_PAGINA
    )

    pagina_registros = registros[
        inicio:fim
    ]

    for registro in pagina_registros:

        embed.add_field(
            name="\u200b",
            value=formatar_registro(
                registro
            ),
            inline=False
        )

    embed.set_footer(
        text=(
            "Registros mais recentes primeiro"
        )
    )

    return embed


# ============================================================
# SELECT DE FILTRO
# ============================================================

class HistoricoFiltroSelect(
    discord.ui.Select
):

    def __init__(
        self,
        view_historico
    ):

        self.view_historico = (
            view_historico
        )

        options = [
            discord.SelectOption(
                label="Tudo",
                value="tudo",
                emoji="📜",
                default=(
                    view_historico.filtro
                    == "tudo"
                )
            ),
            discord.SelectOption(
                label="Jogadores",
                value="jogadores",
                emoji="👤",
                default=(
                    view_historico.filtro
                    == "jogadores"
                )
            ),
            discord.SelectOption(
                label="NPCs",
                value="npcs",
                emoji="👹",
                default=(
                    view_historico.filtro
                    == "npcs"
                )
            ),
            discord.SelectOption(
                label="HP",
                value="hp",
                emoji="❤️",
                default=(
                    view_historico.filtro
                    == "hp"
                )
            ),
            discord.SelectOption(
                label="Mana",
                value="mana",
                emoji="🔵",
                default=(
                    view_historico.filtro
                    == "mana"
                )
            ),
            discord.SelectOption(
                label="XP",
                value="xp",
                emoji="✨",
                default=(
                    view_historico.filtro
                    == "xp"
                )
            ),
            discord.SelectOption(
                label="Atributos",
                value="atributos",
                emoji="⚔️",
                default=(
                    view_historico.filtro
                    == "atributos"
                )
            ),
            discord.SelectOption(
                label="Perícias",
                value="pericias",
                emoji="📚",
                default=(
                    view_historico.filtro
                    == "pericias"
                )
            ),
            discord.SelectOption(
                label="Rolagens",
                value="rolagens",
                emoji="🎲",
                default=(
                    view_historico.filtro
                    == "rolagens"
                )
            ),
        ]

        super().__init__(
            placeholder=(
                "Filtrar histórico..."
            ),
            min_values=1,
            max_values=1,
            options=options
        )


    async def callback(
        self,
        interaction: discord.Interaction
    ):

        self.view_historico.filtro = (
            self.values[0]
        )

        self.view_historico.pagina = 0

        self.view_historico.recarregar()

        await self.view_historico.editar(
            interaction
        )


# ============================================================
# VIEW DO HISTÓRICO
# ============================================================

class HistoricoView(
    discord.ui.View
):

    def __init__(
        self,
        channel_id,
        usuario_id
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

        self.filtro = "tudo"
        self.pagina = 0

        self.todos_registros = []
        self.registros = []

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
                "❌ Somente quem abriu o histórico "
                "pode usar estes controles.",
                ephemeral=True
            )

            return False

        return True


    # ========================================================
    # TOTAL DE PÁGINAS
    # ========================================================

    def total_paginas(
        self
    ):

        if not self.registros:

            return 1

        return (
            len(self.registros)
            + ITENS_POR_PAGINA
            - 1
        ) // ITENS_POR_PAGINA


    # ========================================================
    # RECARREGAR
    # ========================================================

    def recarregar(
        self
    ):

        self.todos_registros = (
            carregar_historico(
                self.channel_id
            )
        )

        self.registros = (
            filtrar_historico(
                self.todos_registros,
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
    # RECONSTRUIR
    # ========================================================

    def reconstruir(
        self
    ):

        self.clear_items()

        self.add_item(
            HistoricoFiltroSelect(
                self
            )
        )

        anterior = discord.ui.Button(
            label="◀ Anterior",
            style=discord.ButtonStyle.secondary,
            disabled=(
                self.pagina <= 0
            )
        )

        proxima = discord.ui.Button(
            label="Próxima ▶",
            style=discord.ButtonStyle.secondary,
            disabled=(
                self.pagina
                >= self.total_paginas() - 1
            )
        )

        atualizar = discord.ui.Button(
            label="Atualizar",
            emoji="🔄",
            style=discord.ButtonStyle.primary
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
    # EDITAR
    # ========================================================

    async def editar(
        self,
        interaction
    ):

        await interaction.response.edit_message(
            embed=criar_embed_historico(
                self.registros,
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
# REGISTRAR COMANDO
# ============================================================

def registrar_comandos_historico(
    bot
):

    @bot.tree.command(
        name="historico",
        description="Mostra o histórico de alterações da mesa."
    )
    async def historico(
        interaction: discord.Interaction
    ):

        if not pode_ver_historico(
            interaction
        ):

            await interaction.response.send_message(
                "❌ Somente o Mestre ou um administrador "
                "pode consultar o histórico da mesa.",
                ephemeral=True
            )

            return

        view = HistoricoView(
            interaction.channel.id,
            interaction.user.id
        )

        await interaction.response.send_message(
            embed=criar_embed_historico(
                view.registros,
                view.pagina,
                view.filtro
            ),
            view=view,
            ephemeral=True
        )
