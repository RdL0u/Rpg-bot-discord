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
# CAMPOS
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
# NOME DO FILTRO
# ============================================================

def nome_filtro(filtro):

    nomes = {
        "tudo": "📋 Tudo",
        "jogadores": "👤 Jogadores",
        "npcs": "👹 NPCs",
        "hp": "❤️ HP",
        "mana": "🔵 Mana",
        "xp": "✨ XP",
        "atributos": "⚔️ Atributos",
        "pericias": "📚 Perícias",
    }

    return nomes.get(
        filtro,
        "📋 Tudo"
    )


# ============================================================
# ÍCONE DA AÇÃO
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

    if acao == "atributo":
        return "⚔️"

    if acao == "pericia":
        return "📚"

    if campo in CAMPOS_ATRIBUTOS:
        return "⚔️"

    if campo in CAMPOS_PERICIAS:
        return "📚"

    return "⚙️"


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
    }

    return nomes.get(
        acao,
        "ALTERAÇÃO"
    )


# ============================================================
# MONTAR SQL DO FILTRO
# ============================================================

def montar_consulta(
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

    # ========================================================
    # JOGADORES
    # ========================================================

    if filtro == "jogadores":

        sql += """
            AND ficha_tipo = 'jogador'
        """

    # ========================================================
    # NPCs
    # ========================================================

    elif filtro == "npcs":

        sql += """
            AND ficha_tipo = 'npc'
        """

    # ========================================================
    # HP
    # ========================================================

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

    # ========================================================
    # MANA
    # ========================================================

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

    # ========================================================
    # XP
    # ========================================================

    elif filtro == "xp":

        sql += """
            AND (
                campo = 'xp'
                OR acao = 'xp'
            )
        """

    # ========================================================
    # ATRIBUTOS
    # ========================================================

    elif filtro == "atributos":

        campos = sorted(
            CAMPOS_ATRIBUTOS
        )

        marcadores = ",".join(
            "?"
            for _ in campos
        )

        sql += f"""
            AND campo IN ({marcadores})
        """

        parametros.extend(
            campos
        )

    # ========================================================
    # PERÍCIAS
    # ========================================================

    elif filtro == "pericias":

        campos = sorted(
            CAMPOS_PERICIAS
        )

        marcadores = ",".join(
            "?"
            for _ in campos
        )

        sql += f"""
            AND campo IN ({marcadores})
        """

        parametros.extend(
            campos
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
        montar_consulta(
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

def calcular_total_paginas(
    quantidade
):

    if quantidade <= 0:
        return 1

    return math.ceil(
        quantidade
        / REGISTROS_POR_PAGINA
    )


# ============================================================
# HORÁRIO DO DISCORD
# ============================================================

def formatar_data_discord(
    criado_em
):

    if criado_em is None:
        return None

    try:

        texto = str(
            criado_em
        )

        # SQLite CURRENT_TIMESTAMP:
        # YYYY-MM-DD HH:MM:SS
        data = datetime.strptime(
            texto,
            "%Y-%m-%d %H:%M:%S"
        )

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
            criado_em
        )


# ============================================================
# NOME VISUAL DA FICHA
# ============================================================

def nome_visual_ficha(
    ficha_id,
    ficha_nome,
    ficha_tipo
):

    if (
        ficha_tipo == "npc"
        and ficha_id is not None
    ):

        return (
            f"{ficha_nome} #{ficha_id}"
        )

    return ficha_nome


# ============================================================
# FORMATAR UM REGISTRO
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

    nome_visual = (
        nome_visual_ficha(
            ficha_id,
            ficha_nome,
            ficha_tipo
        )
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

    # ========================================================
    # VALORES
    # ========================================================

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

    # ========================================================
    # DESCRIÇÃO
    # ========================================================

    if descricao:

        linhas.append(
            descricao
        )

    # ========================================================
    # USUÁRIO
    # ========================================================

    if usuario_id is not None:

        linhas.append(
            f"👤 Alterado por <@{usuario_id}>"
        )

    # ========================================================
    # HORÁRIO
    # ========================================================

    horario = formatar_data_discord(
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

    quantidade = len(
        registros
    )

    total_paginas = (
        calcular_total_paginas(
            quantidade
        )
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

    embed.add_field(
        name="🔎 Filtro",
        value=nome_filtro(
            filtro
        ),
        inline=False
    )

    if not registros_pagina:

        embed.description = (
            "📭 Nenhuma alteração encontrada."
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
            f"Página {pagina + 1}/{total_paginas} "
            f"• {quantidade} registro(s)"
        )
    )

    return (
        embed,
        total_paginas,
        pagina
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

        self.total_paginas = 1

        self.atualizar_estado()


    # ========================================================
    # ATUALIZAR TOTAL
    # ========================================================

    def atualizar_estado(
        self
    ):

        registros = (
            buscar_historico_filtrado(
                self.channel_id,
                self.filtro
            )
        )

        self.total_paginas = (
            calcular_total_paginas(
                len(registros)
            )
        )

        self.pagina = max(
            0,
            min(
                self.pagina,
                self.total_paginas - 1
            )
        )

        self.anterior.disabled = (
            self.pagina <= 0
        )

        self.proxima.disabled = (
            self.pagina
            >= self.total_paginas - 1
        )


    # ========================================================
    # SOMENTE AUTOR
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
                "❌ Somente quem abriu o histórico "
                "pode usar estes botões.",
                ephemeral=True
            )

            return False

        return True


    # ========================================================
    # ATUALIZAR MENSAGEM
    # ========================================================

    async def atualizar_mensagem(
        self,
        interaction
    ):

        self.atualizar_estado()

        embed, total, pagina = (
            criar_embed_historico(
                self.channel_id,
                self.filtro,
                self.pagina
            )
        )

        self.total_paginas = total
        self.pagina = pagina

        self.atualizar_estado()

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )


    # ========================================================
    # ANTERIOR
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

        await self.atualizar_mensagem(
            interaction
        )


    # ========================================================
    # PRÓXIMA
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

        await self.atualizar_mensagem(
            interaction
        )


# ============================================================
# REGISTRAR COMANDOS
# ============================================================

def registrar_comandos_historico(
    bot
):

    @bot.tree.command(
        name="historico",
        description="Mostra o histórico de alterações da mesa."
    )
    @app_commands.describe(
        filtro="Escolha quais alterações deseja visualizar"
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
                name="⚔️ Atributos",
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
                "📭 Ainda não existem registros "
                "para esse filtro.",
                ephemeral=True
            )

            return

        embed, total, pagina = (
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
