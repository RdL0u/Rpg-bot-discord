import math
from datetime import datetime, timezone

import discord

from discord import app_commands

from database import cursor


# ============================================================
# CONFIGURAÇÃO
# ============================================================

REGISTROS_POR_PAGINA = 5


# ============================================================
# NOMES DOS CAMPOS
# ============================================================

NOMES_CAMPOS = {
    "hp": "HP",
    "hp_atual": "HP atual",
    "hp_max": "HP máximo",

    "mana": "Mana",
    "mana_atual": "Mana atual",
    "mana_max": "Mana máxima",

    "xp": "XP",

    "forca": "Força",
    "destreza": "Destreza",
    "vigor": "Vigor",
    "inteligencia": "Inteligência",
    "carisma": "Carisma",
    "raciocinio": "Raciocínio",

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
    "conhecimentos_gerais": "Conhecimentos Gerais",
    "lideranca": "Liderança",
    "sobrevivencia": "Sobrevivência",
    "conducao": "Condução",
    "manha": "Manha",
    "tecnologia": "Tecnologia",
    "esportes": "Esportes",
    "medicina": "Medicina",
    "mira": "Mira",
    "esquiva": "Esquiva",
    "furtividade": "Furtividade",
}


# ============================================================
# ATRIBUTOS E PERÍCIAS
# ============================================================

CAMPOS_ATRIBUTOS = {
    "forca",
    "destreza",
    "vigor",
    "inteligencia",
    "carisma",
    "raciocinio",
}


CAMPOS_PERICIAS = {
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
}


# ============================================================
# ÍCONES
# ============================================================

def icone_acao(
    acao,
    campo
):

    if acao == "dano":
        return "💥"

    if acao == "cura":
        return "💚"

    if acao == "npc_derrotado":
        return "💀"

    if acao == "mana_gasta":
        return "🔮"

    if acao == "mana_recuperada":
        return "💧"

    if acao == "xp":
        return "✨"

    if acao == "criacao":
        return "📜"

    if acao == "exclusao":
        return "🗑️"

    if campo in CAMPOS_ATRIBUTOS:
        return "📊"

    if campo in CAMPOS_PERICIAS:
        return "📚"

    return "✏️"


# ============================================================
# NOME DA AÇÃO
# ============================================================

def nome_acao(
    acao,
    campo
):

    nomes = {
        "dano": "DANO",
        "cura": "CURA",
        "npc_derrotado": "NPC DERROTADO",
        "mana_gasta": "MANA CONSUMIDA",
        "mana_recuperada": "MANA RECUPERADA",
        "xp": "XP ALTERADO",
        "atributo": "ATRIBUTO ALTERADO",
        "pericia": "PERÍCIA ALTERADA",
        "recursos": "RECURSO ALTERADO",
        "edicao": "FICHA EDITADA",
        "criacao": "FICHA CRIADA",
        "exclusao": "FICHA EXCLUÍDA",
    }

    return nomes.get(
        acao,
        "ALTERAÇÃO"
    )


# ============================================================
# FILTRO SQL
# ============================================================

def montar_filtro(
    channel_id,
    filtro
):

    sql = """
        SELECT
            id,
            ficha_id,
            ficha_nome,
            ficha_tipo,
            usuario_id,
            acao,
            campo,
            valor_anterior,
            valor_novo,
            descricao,
            criado_em
        FROM historico
        WHERE channel_id = ?
    """

    parametros = [
        channel_id
    ]

    if filtro == "jogadores":

        sql += """
            AND ficha_tipo = 'jogador'
        """

    elif filtro == "npcs":

        sql += """
            AND ficha_tipo = 'npc'
        """

    elif filtro == "hp":

        sql += """
            AND (
                campo = 'hp'
                OR campo = 'hp_atual'
                OR campo = 'hp_max'
                OR acao = 'dano'
                OR acao = 'cura'
                OR acao = 'npc_derrotado'
            )
        """

    elif filtro == "mana":

        sql += """
            AND (
                campo = 'mana'
                OR campo = 'mana_atual'
                OR campo = 'mana_max'
                OR acao = 'mana_gasta'
                OR acao = 'mana_recuperada'
            )
        """

    elif filtro == "xp":

        sql += """
            AND (
                campo = 'xp'
                OR acao = 'xp'
            )
        """

    elif filtro == "atributos":

        marcadores = ",".join(
            "?"
            for _ in CAMPOS_ATRIBUTOS
        )

        sql += f"""
            AND campo IN ({marcadores})
        """

        parametros.extend(
            sorted(
                CAMPOS_ATRIBUTOS
            )
        )

    elif filtro == "pericias":

        marcadores = ",".join(
            "?"
            for _ in CAMPOS_PERICIAS
        )

        sql += f"""
            AND campo IN ({marcadores})
        """

        parametros.extend(
            sorted(
                CAMPOS_PERICIAS
            )
        )

    return (
        sql,
        parametros
    )


# ============================================================
# BUSCAR HISTÓRICO
# ============================================================

def buscar_historico_filtrado(
    channel_id,
    filtro
):

    sql, parametros = (
        montar_filtro(
            channel_id,
            filtro
        )
    )

    sql += """
        ORDER BY id DESC
    """

    cursor.execute(
        sql,
        parametros
    )

    return cursor.fetchall()


# ============================================================
# TOTAL DE PÁGINAS
# ============================================================

def total_paginas(
    quantidade
):

    if quantidade <= 0:

        return 1

    return math.ceil(
        quantidade
        / REGISTROS_POR_PAGINA
    )


# ============================================================
# FORMATAR HORÁRIO
# ============================================================

def formatar_horario(
    valor
):

    if valor is None:

        return ""

    try:

        texto = str(
            valor
        )

        data = datetime.fromisoformat(
            texto
        )

        if data.tzinfo is None:

            data = data.replace(
                tzinfo=timezone.utc
            )

        timestamp = int(
            data.timestamp()
        )

        return (
            f"<t:{timestamp}:R>"
        )

    except Exception:

        return str(
            valor
        )


# ============================================================
# FORMATAR REGISTRO
# ============================================================

def formatar_registro(
    registro
):

    (
        historico_id,
        ficha_id,
        ficha_nome,
        ficha_tipo,
        usuario_id,
        acao,
        campo,
        valor_anterior,
        valor_novo,
        descricao,
        criado_em
    ) = registro

    emoji_tipo = (
        "👹"
        if ficha_tipo == "npc"
        else "👤"
    )

    if (
        ficha_tipo == "npc"
        and ficha_id is not None
    ):

        nome_visual = (
            f"{ficha_nome} #{ficha_id}"
        )

    else:

        nome_visual = (
            ficha_nome
        )

    icone = icone_acao(
        acao,
        campo
    )

    titulo = nome_acao(
        acao,
        campo
    )

    linhas = [
        f"{icone} **{titulo}**",
        f"{emoji_tipo} **{nome_visual}**",
    ]

    if campo:

        nome_campo = (
            NOMES_CAMPOS.get(
                campo,
                campo.replace(
                    "_",
                    " "
                ).title()
            )
        )

        if (
            valor_anterior is not None
            and valor_novo is not None
        ):

            linhas.append(
                f"**{nome_campo}:** "
                f"`{valor_anterior}` → `{valor_novo}`"
            )

        elif valor_novo is not None:

            linhas.append(
                f"**{nome_campo}:** "
                f"`{valor_novo}`"
            )

    if descricao:

        linhas.append(
            descricao
        )

    if usuario_id is not None:

        linhas.append(
            f"👤 Alterado por <@{usuario_id}>"
        )

    horario = formatar_horario(
        criado_em
    )

    if horario:

        linhas.append(
            f"🕒 {horario}"
        )

    return "\n".join(
        linhas
    )


# ============================================================
# CRIAR EMBED
# ============================================================

def criar_embed_historico(
    channel_id,
    filtro,
    pagina
):

    registros = (
        buscar_historico_filtrado(
            channel_id,
            filtro
        )
    )

    paginas = total_paginas(
        len(registros)
    )

    pagina = max(
        0,
        min(
            pagina,
            paginas - 1
        )
    )

    inicio = (
        pagina
        * REGISTROS_POR_PAGINA
    )

    fim = (
        inicio
        + REGISTROS_POR_PAGINA
    )

    registros_pagina = (
        registros[
            inicio:fim
        ]
    )

    embed = discord.Embed(
        title="📜 HISTÓRICO DA MESA",
        color=discord.Color.dark_red()
    )

    if not registros_pagina:

        embed.description = (
            "📭 Nenhuma alteração encontrada "
            "para este filtro."
        )

    else:

        blocos = []

        for registro in registros_pagina:

            blocos.append(
                formatar_registro(
                    registro
                )
            )

        embed.description = (
            "\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
        ).join(
            blocos
        )

    embed.set_footer(
        text=(
            f"Página {pagina + 1}/{paginas} "
            f"• {len(registros)} registro(s)"
        )
    )

    return (
        embed,
        paginas
    )


# ============================================================
# VIEW
# ============================================================

class HistoricoView(
    discord.ui.View
):

    def __init__(
        self,
        channel_id,
        autor_id,
        filtro
    ):

        super().__init__(
            timeout=300
        )

        self.channel_id = (
            channel_id
        )

        self.autor_id = (
            autor_id
        )

        self.filtro = (
            filtro
        )

        self.pagina = 0

        registros = (
            buscar_historico_filtrado(
                channel_id,
                filtro
            )
        )

        self.paginas = (
            total_paginas(
                len(registros)
            )
        )

        self.atualizar_botoes()


    def atualizar_botoes(
        self
    ):

        self.anterior.disabled = (
            self.pagina <= 0
        )

        self.proxima.disabled = (
            self.pagina
            >= self.paginas - 1
        )


    async def interaction_check(
        self,
        interaction: discord.Interaction
    ):

        if (
            interaction.user.id
            != self.autor_id
        ):

            await interaction.response.send_message(
                "❌ Somente quem abriu o histórico "
                "pode usar estes botões.",
                ephemeral=True
            )

            return False

        return True


    async def atualizar(
        self,
        interaction
    ):

        embed, paginas = (
            criar_embed_historico(
                self.channel_id,
                self.filtro,
                self.pagina
            )
        )

        self.paginas = (
            paginas
        )

        if (
            self.pagina
            >= self.paginas
        ):

            self.pagina = max(
                0,
                self.paginas - 1
            )

            embed, paginas = (
                criar_embed_historico(
                    self.channel_id,
                    self.filtro,
                    self.pagina
                )
            )

            self.paginas = paginas

        self.atualizar_botoes()

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )


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

        await self.atualizar(
            interaction
        )


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
            < self.paginas - 1
        ):

            self.pagina += 1

        await self.atualizar(
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
    @app_commands.describe(
        filtro="Filtra os tipos de alterações exibidas"
    )
    @app_commands.choices(
        filtro=[
            app_commands.Choice(
                name="📋 Tudo",
                value="tudo"
            ),
            app_commands.Choice(
                name="👤 Jogadores",
                value="jogadores"
            ),
            app_commands.Choice(
                name="👹 NPCs",
                value="npcs"
            ),
            app_commands.Choice(
                name="❤️ HP",
                value="hp"
            ),
            app_commands.Choice(
                name="🔵 Mana",
                value="mana"
            ),
            app_commands.Choice(
                name="✨ XP",
                value="xp"
            ),
            app_commands.Choice(
                name="📊 Atributos",
                value="atributos"
            ),
            app_commands.Choice(
                name="📚 Perícias",
                value="pericias"
            ),
        ]
    )
    async def historico(
        interaction: discord.Interaction,
        filtro: app_commands.Choice[str] = None
    ):

        if interaction.channel is None:

            await interaction.response.send_message(
                "❌ Este comando precisa ser usado "
                "em um canal da mesa.",
                ephemeral=True
            )

            return

        filtro_escolhido = (
            filtro.value
            if filtro is not None
            else "tudo"
        )

        registros = (
            buscar_historico_filtrado(
                interaction.channel.id,
                filtro_escolhido
            )
        )

        if not registros:

            await interaction.response.send_message(
                "📭 Nenhuma alteração registrada "
                "para esse filtro.",
                ephemeral=True
            )

            return

        embed, paginas = (
            criar_embed_historico(
                interaction.channel.id,
                filtro_escolhido,
                0
            )
        )

        view = HistoricoView(
            interaction.channel.id,
            interaction.user.id,
            filtro_escolhido
        )

        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True
        )
