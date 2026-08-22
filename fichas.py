import discord

from database import (
    cursor,
    db,
    registrar_historico,
)

from config import (
    ATRIBUTOS,
    PERICIAS,
    ORDEM_PERICIAS,
)

from comando.permissoes import (
    eh_admin,
    eh_mestre,
)


# ============================================================
# GRUPOS DE ATRIBUTOS PARA EDIÇÃO
# ============================================================

GRUPOS_ATRIBUTOS_EDICAO = [
    [
        "forca",
        "destreza",
        "vigor",
    ],
    [
        "inteligencia",
        "carisma",
        "raciocinio",
    ],
]


# ============================================================
# GRUPOS DE PERÍCIAS PARA EDIÇÃO
# ============================================================

GRUPOS_PERICIAS_EDICAO = [
    ORDEM_PERICIAS[0:5],
    ORDEM_PERICIAS[5:10],
    ORDEM_PERICIAS[10:15],
    ORDEM_PERICIAS[15:20],
    ORDEM_PERICIAS[20:23],
]


# ============================================================
# BUSCAR FICHA DO JOGADOR
# ============================================================

def buscar_ficha_jogador(
    channel_id,
    user_id
):

    cursor.execute("""
        SELECT *
        FROM fichas
        WHERE channel_id = ?
        AND dono_id = ?
        AND tipo = 'jogador'
        LIMIT 1
    """, (
        channel_id,
        user_id
    ))

    return cursor.fetchone()


# ============================================================
# BUSCAR FICHA
# ============================================================

def buscar_ficha(
    ficha_id
):

    cursor.execute("""
        SELECT *
        FROM fichas
        WHERE id = ?
        LIMIT 1
    """, (
        ficha_id,
    ))

    return cursor.fetchone()


# ============================================================
# TRANSFORMAR FICHA
# ============================================================

def transformar_ficha(
    dados
):

    if dados is None:
        return None

    cursor.execute(
        "PRAGMA table_info(fichas)"
    )

    informacoes_colunas = (
        cursor.fetchall()
    )

    colunas_reais = [
        coluna[1]
        for coluna in informacoes_colunas
    ]

    ficha = {}

    for indice, valor in enumerate(
        dados
    ):

        if indice < len(
            colunas_reais
        ):

            ficha[
                colunas_reais[indice]
            ] = valor

    return ficha


# ============================================================
# RECARREGAR FICHA
# ============================================================

def recarregar_ficha(
    ficha_id
):

    dados = buscar_ficha(
        ficha_id
    )

    return transformar_ficha(
        dados
    )


# ============================================================
# ATUALIZAR HP
# ============================================================

def atualizar_hp(
    ficha_id,
    novo_hp
):

    cursor.execute("""
        UPDATE fichas
        SET hp_atual = ?
        WHERE id = ?
    """, (
        novo_hp,
        ficha_id
    ))

    db.commit()


# ============================================================
# ATUALIZAR MANA
# ============================================================

def atualizar_mana(
    ficha_id,
    nova_mana
):

    cursor.execute("""
        UPDATE fichas
        SET mana_atual = ?
        WHERE id = ?
    """, (
        nova_mana,
        ficha_id
    ))

    db.commit()


# ============================================================
# ADICIONAR XP
# ============================================================

def adicionar_xp(
    ficha_id,
    quantidade
):

    cursor.execute("""
        UPDATE fichas
        SET xp = xp + ?
        WHERE id = ?
    """, (
        quantidade,
        ficha_id
    ))

    db.commit()


# ============================================================
# DELETAR FICHA
# ============================================================

def deletar_ficha(
    ficha_id
):

    cursor.execute("""
        DELETE FROM fichas
        WHERE id = ?
    """, (
        ficha_id,
    ))

    db.commit()


# ============================================================
# CALCULAR RC
# ============================================================

def calcular_rc(
    ficha
):

    return (
        ficha.get(
            "esquiva",
            0
        )
        +
        ficha.get(
            "destreza",
            0
        )
        +
        5
    )


# ============================================================
# ESTADO DO HP
# ============================================================

def estado_hp(
    atual,
    maximo
):

    if (
        maximo <= 0
        or atual <= 0
    ):

        return "⚫ INCAPACITADO"

    percentual = (
        atual / maximo
    ) * 100

    if percentual < 30:
        return "🔴 CRÍTICO"

    if percentual <= 40:
        return "🟡 FERIDO"

    return "🟢 ESTÁVEL"


# ============================================================
# ESTADO DA MANA
# ============================================================

def estado_mana(
    atual,
    maximo
):

    if (
        maximo <= 0
        or atual <= 0
    ):

        return "⚫ ESGOTADA"

    percentual = (
        atual / maximo
    ) * 100

    if percentual < 30:
        return "🔴 CRÍTICA"

    if percentual <= 40:
        return "🟡 BAIXA"

    return "🟢 PLENA"


# ============================================================
# COMPATIBILIDADE
# ============================================================

def estado_recurso(
    atual,
    maximo
):

    return (
        atual,
        maximo
    )


# ============================================================
# PERMISSÃO PARA ALTERAR FICHA
# ============================================================

def pode_alterar_ficha(
    interaction,
    ficha
):

    if ficha is None:
        return False

    if eh_admin(
        interaction
    ):
        return True

    if (
        ficha.get("tipo")
        == "jogador"
    ):

        if (
            ficha.get("dono_id")
            == interaction.user.id
        ):
            return True

        if eh_mestre(
            interaction
        ):
            return True

        return False

    if (
        ficha.get("tipo")
        == "npc"
    ):

        if eh_mestre(
            interaction
        ):
            return True

        if (
            ficha.get("mestre_id")
            == interaction.user.id
        ):
            return True

        return False

    return False


# ============================================================
# FORMATAR ATRIBUTOS
# ============================================================

def formatar_atributos(
    ficha
):

    return (
        f"💪 For: **{ficha.get('forca', 0)}**"
        f"  "
        f"🏹 Des: **{ficha.get('destreza', 0)}**\n"
        f"🛡️ Vig: **{ficha.get('vigor', 0)}**"
        f"  "
        f"🧠 Int: **{ficha.get('inteligencia', 0)}**\n"
        f"🎭 Car: **{ficha.get('carisma', 0)}**"
        f"  "
        f"💡 Rac: **{ficha.get('raciocinio', 0)}**"
    )


# ============================================================
# FORMATAR PERÍCIAS
# ============================================================

def formatar_pericias(
    ficha
):

    linhas = []

    for chave in ORDEM_PERICIAS:

        emoji, nome = (
            PERICIAS[
                chave
            ]
        )

        valor = ficha.get(
            chave,
            0
        )

        linhas.append(
            f"{emoji} {nome}: **{valor}**"
        )

    return linhas


# ============================================================
# PÁGINA DE STATUS
# ============================================================

def criar_pagina_status(
    ficha,
    jogador=None
):

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

    xp = ficha.get(
        "xp",
        0
    )

    rc = calcular_rc(
        ficha
    )

    embed = discord.Embed(
        title=(
            f"📜 FICHA DE "
            f"{nome.upper()}"
        ),
        color=discord.Color.dark_red()
    )

    status = (
        f"❤️ HP: **{hp_atual}/{hp_max}**"
        f" • {estado_hp(hp_atual, hp_max)}\n"
        f"🔵 Mana: **{mana_atual}/{mana_max}**"
        f" • {estado_mana(mana_atual, mana_max)}\n"
        f"✨ XP: **{xp}**"
        f"  "
        f"⚡ RC: **{rc}**"
    )

    embed.add_field(
        name="❤️ STATUS",
        value=status,
        inline=False
    )

    embed.add_field(
        name="⚔️ ATRIBUTOS",
        value=formatar_atributos(
            ficha
        ),
        inline=False
    )

    if jogador is not None:

        embed.set_footer(
            text=(
                f"Jogador: "
                f"{jogador.display_name}"
                f" • Página 1/2"
                f" • Status e Atributos"
            )
        )

    else:

        embed.set_footer(
            text=(
                "Página 1/2"
                " • Status e Atributos"
            )
        )

    return embed


# ============================================================
# PÁGINA DE PERÍCIAS
# ============================================================

def criar_pagina_pericias(
    ficha,
    jogador=None
):

    nome = ficha.get(
        "nome",
        "Sem nome"
    )

    embed = discord.Embed(
        title=(
            f"📜 FICHA DE "
            f"{nome.upper()}"
        ),
        color=discord.Color.dark_red()
    )

    linhas = formatar_pericias(
        ficha
    )

    embed.add_field(
        name="📚 PERÍCIAS",
        value="\n".join(
            linhas
        ),
        inline=False
    )

    if jogador is not None:

        embed.set_footer(
            text=(
                f"Jogador: "
                f"{jogador.display_name}"
                f" • Página 2/2"
                f" • Perícias"
            )
        )

    else:

        embed.set_footer(
            text=(
                "Página 2/2"
                " • Perícias"
            )
        )

    return embed


# ============================================================
# ATUALIZAR VIEW
# ============================================================

def atualizar_view_ficha(
    view_ficha,
    ficha_id
):

    if view_ficha is None:
        return None

    ficha_atualizada = (
        recarregar_ficha(
            ficha_id
        )
    )

    if ficha_atualizada:

        view_ficha.ficha = (
            ficha_atualizada
        )

    return ficha_atualizada


# ============================================================
# MODAL RECURSOS
# ============================================================

class EditarRecursosModal(
    discord.ui.Modal,
    title="Editar recursos"
):

    def __init__(
        self,
        ficha,
        view_ficha=None
    ):

        super().__init__()

        self.ficha = ficha
        self.view_ficha = view_ficha

        self.hp_atual = discord.ui.TextInput(
            label="HP atual",
            default=str(
                ficha.get(
                    "hp_atual",
                    0
                )
            ),
            required=True
        )

        self.hp_max = discord.ui.TextInput(
            label="HP máximo",
            default=str(
                ficha.get(
                    "hp_max",
                    0
                )
            ),
            required=True
        )

        self.mana_atual = discord.ui.TextInput(
            label="Mana atual",
            default=str(
                ficha.get(
                    "mana_atual",
                    0
                )
            ),
            required=True
        )

        self.mana_max = discord.ui.TextInput(
            label="Mana máxima",
            default=str(
                ficha.get(
                    "mana_max",
                    0
                )
            ),
            required=True
        )

        self.add_item(
            self.hp_atual
        )

        self.add_item(
            self.hp_max
        )

        self.add_item(
            self.mana_atual
        )

        self.add_item(
            self.mana_max
        )


    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        ficha_atual = recarregar_ficha(
            self.ficha["id"]
        )

        if ficha_atual is None:

            await interaction.response.send_message(
                "❌ Esta ficha não existe mais.",
                ephemeral=True
            )

            return

        if not pode_alterar_ficha(
            interaction,
            ficha_atual
        ):

            await interaction.response.send_message(
                "❌ Você não possui permissão para alterar esta ficha.",
                ephemeral=True
            )

            return

        try:

            hp_atual = int(
                self.hp_atual.value
            )

            hp_max = int(
                self.hp_max.value
            )

            mana_atual = int(
                self.mana_atual.value
            )

            mana_max = int(
                self.mana_max.value
            )

        except ValueError:

            await interaction.response.send_message(
                "❌ HP e Mana precisam ser números inteiros.",
                ephemeral=True
            )

            return

        if hp_max <= 0:

            await interaction.response.send_message(
                "❌ O HP máximo precisa ser maior que 0.",
                ephemeral=True
            )

            return

        if (
            hp_atual < 0
            or hp_atual > hp_max
        ):

            await interaction.response.send_message(
                "❌ O HP atual precisa estar entre 0 e o HP máximo.",
                ephemeral=True
            )

            return

        if mana_max < 0:

            await interaction.response.send_message(
                "❌ A Mana máxima não pode ser negativa.",
                ephemeral=True
            )

            return

        if (
            mana_atual < 0
            or mana_atual > mana_max
        ):

            await interaction.response.send_message(
                "❌ A Mana atual precisa estar entre 0 e a Mana máxima.",
                ephemeral=True
            )

            return

        anteriores = {
            "hp_atual": ficha_atual["hp_atual"],
            "hp_max": ficha_atual["hp_max"],
            "mana_atual": ficha_atual["mana_atual"],
            "mana_max": ficha_atual["mana_max"],
        }

        novos = {
            "hp_atual": hp_atual,
            "hp_max": hp_max,
            "mana_atual": mana_atual,
            "mana_max": mana_max,
        }

        cursor.execute("""
            UPDATE fichas
            SET
                hp_atual = ?,
                hp_max = ?,
                mana_atual = ?,
                mana_max = ?
            WHERE id = ?
        """, (
            hp_atual,
            hp_max,
            mana_atual,
            mana_max,
            ficha_atual["id"]
        ))

        db.commit()

        for campo, valor_novo in novos.items():

            valor_anterior = anteriores[
                campo
            ]

            if (
                valor_anterior
                == valor_novo
            ):
                continue

            registrar_historico(
                ficha_atual["channel_id"],
                ficha_atual["id"],
                ficha_atual["nome"],
                ficha_atual["tipo"],
                interaction.user.id,
                "recursos",
                campo=campo,
                valor_anterior=valor_anterior,
                valor_novo=valor_novo,
                descricao=(
                    "⚙️ Alterado pelo menu "
                    "de edição da ficha."
                )
            )

        ficha_nova = atualizar_view_ficha(
            self.view_ficha,
            ficha_atual["id"]
        )

        if ficha_nova is None:

            ficha_nova = recarregar_ficha(
                ficha_atual["id"]
            )

        await interaction.response.send_message(
            "✅ **Recursos atualizados.**\n\n"
            f"❤️ HP: **{ficha_nova['hp_atual']}/{ficha_nova['hp_max']}** "
            f"• {estado_hp(ficha_nova['hp_atual'], ficha_nova['hp_max'])}\n"
            f"🔵 Mana: **{ficha_nova['mana_atual']}/{ficha_nova['mana_max']}** "
            f"• {estado_mana(ficha_nova['mana_atual'], ficha_nova['mana_max'])}",
            ephemeral=True
        )


# ============================================================
# MODAL XP
# ============================================================

class EditarXPModal(
    discord.ui.Modal,
    title="Editar XP"
):

    def __init__(
        self,
        ficha,
        view_ficha=None
    ):

        super().__init__()

        self.ficha = ficha
        self.view_ficha = view_ficha

        self.xp = discord.ui.TextInput(
            label="XP atual",
            default=str(
                ficha.get(
                    "xp",
                    0
                )
            ),
            required=True
        )

        self.add_item(
            self.xp
        )


    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        ficha_atual = recarregar_ficha(
            self.ficha["id"]
        )

        if ficha_atual is None:

            await interaction.response.send_message(
                "❌ Esta ficha não existe mais.",
                ephemeral=True
            )

            return

        if not pode_alterar_ficha(
            interaction,
            ficha_atual
        ):

            await interaction.response.send_message(
                "❌ Você não possui permissão para alterar esta ficha.",
                ephemeral=True
            )

            return

        try:

            novo_xp = int(
                self.xp.value
            )

        except ValueError:

            await interaction.response.send_message(
                "❌ O XP precisa ser um número inteiro.",
                ephemeral=True
            )

            return

        if novo_xp < 0:

            await interaction.response.send_message(
                "❌ O XP não pode ser negativo.",
                ephemeral=True
            )

            return

        xp_anterior = ficha_atual["xp"]

        cursor.execute("""
            UPDATE fichas
            SET xp = ?
            WHERE id = ?
        """, (
            novo_xp,
            ficha_atual["id"]
        ))

        db.commit()

        if xp_anterior != novo_xp:

            registrar_historico(
                ficha_atual["channel_id"],
                ficha_atual["id"],
                ficha_atual["nome"],
                ficha_atual["tipo"],
                interaction.user.id,
                "xp",
                campo="xp",
                valor_anterior=xp_anterior,
                valor_novo=novo_xp,
                descricao=(
                    "✨ Alterado pelo menu "
                    "de edição da ficha."
                )
            )

        atualizar_view_ficha(
            self.view_ficha,
            ficha_atual["id"]
        )

        await interaction.response.send_message(
            f"✅ XP atualizado para **{novo_xp}**.",
            ephemeral=True
        )


# ============================================================
# MODAL ATRIBUTOS EM LOTE
# ============================================================

class EditarAtributosModal(
    discord.ui.Modal
):

    def __init__(
        self,
        ficha,
        grupo,
        view_ficha=None
    ):

        self.ficha = ficha
        self.grupo = grupo
        self.view_ficha = view_ficha

        campos = GRUPOS_ATRIBUTOS_EDICAO[
            grupo
        ]

        super().__init__(
            title=(
                f"Editar atributos "
                f"{grupo + 1}/"
                f"{len(GRUPOS_ATRIBUTOS_EDICAO)}"
            )
        )

        self.inputs = {}

        for chave in campos:

            emoji, nome = ATRIBUTOS[
                chave
            ]

            campo = discord.ui.TextInput(
                label=nome,
                default=str(
                    ficha.get(
                        chave,
                        0
                    )
                ),
                required=True
            )

            self.inputs[
                chave
            ] = campo

            self.add_item(
                campo
            )


    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        ficha_atual = recarregar_ficha(
            self.ficha["id"]
        )

        if ficha_atual is None:

            await interaction.response.send_message(
                "❌ Esta ficha não existe mais.",
                ephemeral=True
            )

            return

        if not pode_alterar_ficha(
            interaction,
            ficha_atual
        ):

            await interaction.response.send_message(
                "❌ Você não possui permissão para alterar esta ficha.",
                ephemeral=True
            )

            return

        valores = {}

        try:

            for chave, campo in self.inputs.items():

                valor = int(
                    campo.value
                )

                if valor < 0:
                    raise ValueError

                valores[
                    chave
                ] = valor

        except ValueError:

            await interaction.response.send_message(
                "❌ Todos os atributos precisam ser "
                "números inteiros maiores ou iguais a 0.",
                ephemeral=True
            )

            return

        alteracoes = []

        for chave, valor_novo in valores.items():

            valor_anterior = ficha_atual.get(
                chave,
                0
            )

            if valor_anterior == valor_novo:
                continue

            cursor.execute(
                f"""
                UPDATE fichas
                SET {chave} = ?
                WHERE id = ?
                """,
                (
                    valor_novo,
                    ficha_atual["id"]
                )
            )

            alteracoes.append(
                (
                    chave,
                    valor_anterior,
                    valor_novo
                )
            )

        db.commit()

        for (
            chave,
            valor_anterior,
            valor_novo
        ) in alteracoes:

            registrar_historico(
                ficha_atual["channel_id"],
                ficha_atual["id"],
                ficha_atual["nome"],
                ficha_atual["tipo"],
                interaction.user.id,
                "atributo",
                campo=chave,
                valor_anterior=valor_anterior,
                valor_novo=valor_novo,
                descricao=(
                    "⚔️ Alterado pelo formulário "
                    "de atributos da ficha."
                )
            )

        ficha_nova = atualizar_view_ficha(
            self.view_ficha,
            ficha_atual["id"]
        )

        if ficha_nova is None:

            ficha_nova = recarregar_ficha(
                ficha_atual["id"]
            )

        proximo = self.grupo + 1

        if (
            proximo
            < len(
                GRUPOS_ATRIBUTOS_EDICAO
            )
        ):

            await interaction.response.send_message(
                f"✅ Atributos "
                f"{self.grupo + 1}/"
                f"{len(GRUPOS_ATRIBUTOS_EDICAO)} "
                f"salvos.\n\n"
                f"Clique abaixo para continuar.",
                view=ViewContinuarEdicaoAtributos(
                    ficha_nova,
                    proximo,
                    self.view_ficha
                ),
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "✅ Todos os atributos foram atualizados.",
            ephemeral=True
        )


# ============================================================
# CONTINUAR ATRIBUTOS
# ============================================================

class ViewContinuarEdicaoAtributos(
    discord.ui.View
):

    def __init__(
        self,
        ficha,
        grupo,
        view_ficha=None
    ):

        super().__init__(
            timeout=300
        )

        self.ficha = ficha
        self.grupo = grupo
        self.view_ficha = view_ficha


    @discord.ui.button(
        label="➡️ Continuar atributos",
        style=discord.ButtonStyle.primary
    )
    async def continuar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        ficha_atual = recarregar_ficha(
            self.ficha["id"]
        )

        if ficha_atual is None:

            await interaction.response.send_message(
                "❌ Esta ficha não existe mais.",
                ephemeral=True
            )

            return

        if not pode_alterar_ficha(
            interaction,
            ficha_atual
        ):

            await interaction.response.send_message(
                "❌ Você não possui permissão para alterar esta ficha.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            EditarAtributosModal(
                ficha_atual,
                self.grupo,
                self.view_ficha
            )
        )


# ============================================================
# MODAL PERÍCIAS EM LOTE
# TODAS AS FICHAS: 0 A 5
# ============================================================

class EditarPericiasModal(
    discord.ui.Modal
):

    def __init__(
        self,
        ficha,
        grupo,
        view_ficha=None
    ):

        self.ficha = ficha
        self.grupo = grupo
        self.view_ficha = view_ficha

        campos = GRUPOS_PERICIAS_EDICAO[
            grupo
        ]

        super().__init__(
            title=(
                f"Editar perícias "
                f"{grupo + 1}/"
                f"{len(GRUPOS_PERICIAS_EDICAO)}"
            )
        )

        self.inputs = {}

        for chave in campos:

            emoji, nome = PERICIAS[
                chave
            ]

            campo = discord.ui.TextInput(
                label=nome[:45],
                placeholder="Valor de 0 a 5",
                default=str(
                    ficha.get(
                        chave,
                        0
                    )
                ),
                required=True
            )

            self.inputs[
                chave
            ] = campo

            self.add_item(
                campo
            )


    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        ficha_atual = recarregar_ficha(
            self.ficha["id"]
        )

        if ficha_atual is None:

            await interaction.response.send_message(
                "❌ Esta ficha não existe mais.",
                ephemeral=True
            )

            return

        if not pode_alterar_ficha(
            interaction,
            ficha_atual
        ):

            await interaction.response.send_message(
                "❌ Você não possui permissão para alterar esta ficha.",
                ephemeral=True
            )

            return

        valores = {}

        try:

            for chave, campo in self.inputs.items():

                valor = int(
                    campo.value
                )

                if (
                    valor < 0
                    or valor > 5
                ):

                    raise ValueError

                valores[
                    chave
                ] = valor

        except ValueError:

            await interaction.response.send_message(
                "❌ Todas as perícias precisam ser "
                "números inteiros entre **0 e 5**.",
                ephemeral=True
            )

            return

        alteracoes = []

        for chave, valor_novo in valores.items():

            valor_anterior = ficha_atual.get(
                chave,
                0
            )

            if valor_anterior == valor_novo:
                continue

            cursor.execute(
                f"""
                UPDATE fichas
                SET {chave} = ?
                WHERE id = ?
                """,
                (
                    valor_novo,
                    ficha_atual["id"]
                )
            )

            alteracoes.append(
                (
                    chave,
                    valor_anterior,
                    valor_novo
                )
            )

        db.commit()

        for (
            chave,
            valor_anterior,
            valor_novo
        ) in alteracoes:

            registrar_historico(
                ficha_atual["channel_id"],
                ficha_atual["id"],
                ficha_atual["nome"],
                ficha_atual["tipo"],
                interaction.user.id,
                "pericia",
                campo=chave,
                valor_anterior=valor_anterior,
                valor_novo=valor_novo,
                descricao=(
                    "📚 Alterada pelo formulário "
                    "de perícias da ficha."
                )
            )

        ficha_nova = atualizar_view_ficha(
            self.view_ficha,
            ficha_atual["id"]
        )

        if ficha_nova is None:

            ficha_nova = recarregar_ficha(
                ficha_atual["id"]
            )

        proximo = self.grupo + 1

        if (
            proximo
            < len(
                GRUPOS_PERICIAS_EDICAO
            )
        ):

            await interaction.response.send_message(
                f"✅ Perícias "
                f"{self.grupo + 1}/"
                f"{len(GRUPOS_PERICIAS_EDICAO)} "
                f"salvas.\n\n"
                f"Clique abaixo para continuar.",
                view=ViewContinuarEdicaoPericias(
                    ficha_nova,
                    proximo,
                    self.view_ficha
                ),
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "✅ Todas as perícias foram atualizadas.",
            ephemeral=True
        )


# ============================================================
# CONTINUAR PERÍCIAS
# ============================================================

class ViewContinuarEdicaoPericias(
    discord.ui.View
):

    def __init__(
        self,
        ficha,
        grupo,
        view_ficha=None
    ):

        super().__init__(
            timeout=300
        )

        self.ficha = ficha
        self.grupo = grupo
        self.view_ficha = view_ficha


    @discord.ui.button(
        label="➡️ Continuar perícias",
        style=discord.ButtonStyle.primary
    )
    async def continuar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        ficha_atual = recarregar_ficha(
            self.ficha["id"]
        )

        if ficha_atual is None:

            await interaction.response.send_message(
                "❌ Esta ficha não existe mais.",
                ephemeral=True
            )

            return

        if not pode_alterar_ficha(
            interaction,
            ficha_atual
        ):

            await interaction.response.send_message(
                "❌ Você não possui permissão para alterar esta ficha.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            EditarPericiasModal(
                ficha_atual,
                self.grupo,
                self.view_ficha
            )
        )


# ============================================================
# MENU DE EDIÇÃO
# ============================================================

class EditarFichaSelect(
    discord.ui.Select
):

    def __init__(
        self,
        ficha,
        view_ficha=None
    ):

        self.ficha = ficha
        self.view_ficha = view_ficha

        super().__init__(
            placeholder="O que deseja editar?",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Recursos",
                    value="recursos",
                    emoji="❤️",
                    description="Editar HP e Mana"
                ),
                discord.SelectOption(
                    label="XP",
                    value="xp",
                    emoji="✨",
                    description="Editar XP"
                ),
                discord.SelectOption(
                    label="Atributos",
                    value="atributos",
                    emoji="⚔️",
                    description="Editar todos os atributos"
                ),
                discord.SelectOption(
                    label="Perícias",
                    value="pericias",
                    emoji="📚",
                    description="Editar todas as perícias"
                ),
            ]
        )


    async def callback(
        self,
        interaction: discord.Interaction
    ):

        ficha_atual = recarregar_ficha(
            self.ficha["id"]
        )

        if ficha_atual is None:

            await interaction.response.send_message(
                "❌ Esta ficha não existe mais.",
                ephemeral=True
            )

            return

        if not pode_alterar_ficha(
            interaction,
            ficha_atual
        ):

            await interaction.response.send_message(
                "❌ Você não possui permissão para alterar esta ficha.",
                ephemeral=True
            )

            return

        escolha = self.values[0]

        if escolha == "recursos":

            await interaction.response.send_modal(
                EditarRecursosModal(
                    ficha_atual,
                    self.view_ficha
                )
            )

            return

        if escolha == "xp":

            await interaction.response.send_modal(
                EditarXPModal(
                    ficha_atual,
                    self.view_ficha
                )
            )

            return

        if escolha == "atributos":

            await interaction.response.send_modal(
                EditarAtributosModal(
                    ficha_atual,
                    0,
                    self.view_ficha
                )
            )

            return

        if escolha == "pericias":

            await interaction.response.send_modal(
                EditarPericiasModal(
                    ficha_atual,
                    0,
                    self.view_ficha
                )
            )


# ============================================================
# VIEW DO MENU DE EDIÇÃO
# ============================================================

class EditarFichaView(
    discord.ui.View
):

    def __init__(
        self,
        ficha,
        view_ficha=None
    ):

        super().__init__(
            timeout=300
        )

        self.add_item(
            EditarFichaSelect(
                ficha,
                view_ficha
            )
        )


# ============================================================
# VIEW PRINCIPAL DA FICHA
# ============================================================

class FichaView(
    discord.ui.View
):

    def __init__(
        self,
        ficha,
        jogador=None
    ):

        super().__init__(
            timeout=300
        )

        self.ficha = ficha
        self.jogador = jogador
        self.pagina = 1

        self.atualizar_botoes()


    def atualizar_ficha(
        self
    ):

        ficha_atualizada = recarregar_ficha(
            self.ficha["id"]
        )

        if ficha_atualizada:

            self.ficha = ficha_atualizada

        return ficha_atualizada


    def atualizar_botoes(
        self
    ):

        self.status_button.disabled = (
            self.pagina == 1
        )

        self.pericias_button.disabled = (
            self.pagina == 2
        )


    @discord.ui.button(
        label="◀ Status",
        style=discord.ButtonStyle.secondary,
        row=0
    )
    async def status_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if self.atualizar_ficha() is None:

            await interaction.response.send_message(
                "❌ Esta ficha não existe mais.",
                ephemeral=True
            )

            return

        self.pagina = 1
        self.atualizar_botoes()

        await interaction.response.edit_message(
            embed=criar_pagina_status(
                self.ficha,
                self.jogador
            ),
            view=self
        )


    @discord.ui.button(
        label="Perícias ▶",
        style=discord.ButtonStyle.secondary,
        row=0
    )
    async def pericias_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if self.atualizar_ficha() is None:

            await interaction.response.send_message(
                "❌ Esta ficha não existe mais.",
                ephemeral=True
            )

            return

        self.pagina = 2
        self.atualizar_botoes()

        await interaction.response.edit_message(
            embed=criar_pagina_pericias(
                self.ficha,
                self.jogador
            ),
            view=self
        )


    @discord.ui.button(
        label="✏️ Editar",
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def editar_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if self.atualizar_ficha() is None:

            await interaction.response.send_message(
                "❌ Esta ficha não existe mais.",
                ephemeral=True
            )

            return

        if not pode_alterar_ficha(
            interaction,
            self.ficha
        ):

            await interaction.response.send_message(
                "❌ Você não possui permissão para alterar esta ficha.",
                ephemeral=True
            )

            return

        tipo_visual = (
            "👹 NPC"
            if self.ficha.get("tipo") == "npc"
            else "👤 Jogador"
        )

        await interaction.response.send_message(
            f"✏️ **Editar ficha**\n\n"
            f"{tipo_visual}: "
            f"**{self.ficha.get('nome', 'Sem nome')}**\n\n"
            f"Escolha o tipo de informação "
            f"que deseja alterar:",
            view=EditarFichaView(
                self.ficha,
                self
            ),
            ephemeral=True
        )
