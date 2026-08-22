import discord

from database import (
    db,
    cursor,
    registrar_historico,
)

from config import (
    ATRIBUTOS,
    PERICIAS,
    ORDEM_PERICIAS,
)

from comando.permissoes import (
    pode_alterar_ficha,
)


# ============================================================
# NOMES COMPLETOS DOS ATRIBUTOS
# ============================================================

NOMES_ATRIBUTOS = {
    "forca": "Força",
    "destreza": "Destreza",
    "vigor": "Vigor",
    "inteligencia": "Inteligência",
    "carisma": "Carisma",
    "raciocinio": "Raciocínio",
}


# ============================================================
# GRUPOS DE ATRIBUTOS
# ============================================================

GRUPOS_ATRIBUTOS = [
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
# GRUPOS DE PERÍCIAS
# ============================================================

GRUPOS_PERICIAS = [
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
# BUSCAR FICHA PELO ID
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
#
# IMPORTANTE:
# NÃO usamos posições fixas da tabela.
#
# Isso evita erros caso colunas tenham sido adicionadas
# posteriormente através das migrações do SQLite.
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

            nome_coluna = (
                colunas_reais[
                    indice
                ]
            )

            ficha[
                nome_coluna
            ] = valor

    return ficha


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
    valor
):

    cursor.execute("""
        UPDATE fichas
        SET xp = xp + ?
        WHERE id = ?
    """, (
        valor,
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

    esquiva = ficha.get(
        "esquiva",
        0
    )

    destreza = ficha.get(
        "destreza",
        0
    )

    return (
        esquiva
        + destreza
        + 5
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
# ESTADO GENÉRICO
#
# Mantido por compatibilidade com versões anteriores.
# ============================================================

def estado_recurso(
    atual,
    maximo
):

    if (
        atual <= 0
        or maximo <= 0
    ):

        return "ZERADO"

    percentual = (
        atual / maximo
    ) * 100

    if percentual >= 70:

        return "BOM"

    if percentual >= 30:

        return "BAIXO"

    return "CRÍTICO"


# ============================================================
# PÁGINA 1
# STATUS + ATRIBUTOS
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

    # ========================================================
    # IDENTIFICAÇÃO
    # ========================================================

    if ficha.get(
        "tipo"
    ) == "npc":

        identificacao = (
            f"👹 NPC #{ficha.get('id', '?')}"
        )

    elif jogador is not None:

        identificacao = (
            f"Jogador: {jogador.mention}"
        )

    else:

        identificacao = (
            "👤 Jogador"
        )

    # ========================================================
    # STATUS
    # ========================================================

    status = (
        f"❤️ HP: **{hp_atual}/{hp_max}**\n"
        f"   {estado_hp(hp_atual, hp_max)}\n\n"
        f"🔵 Mana: **{mana_atual}/{mana_max}**\n"
        f"   {estado_mana(mana_atual, mana_max)}\n\n"
        f"✨ XP: **{xp}**\n"
        f"⚡ RC: **{rc}**"
    )

    # ========================================================
    # ATRIBUTOS
    # ========================================================

    atributos = (
        f"💪 For: **{ficha.get('forca', 0)}**  "
        f"🏹 Des: **{ficha.get('destreza', 0)}**\n"
        f"🛡️ Vig: **{ficha.get('vigor', 0)}**  "
        f"🧠 Int: **{ficha.get('inteligencia', 0)}**\n"
        f"🎭 Car: **{ficha.get('carisma', 0)}**  "
        f"💡 Rac: **{ficha.get('raciocinio', 0)}**"
    )

    embed.description = (
        f"{identificacao}\n\n"
        f"❤️ **STATUS**\n\n"
        f"{status}\n\n"
        f"⚔️ **ATRIBUTOS**\n\n"
        f"{atributos}"
    )

    embed.set_footer(
        text=(
            "Página 1/2 • "
            "Status e Atributos"
        )
    )

    return embed


# ============================================================
# PÁGINA 2
# PERÍCIAS
#
# UMA COLUNA
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
            f"📚 PERÍCIAS — "
            f"{nome}"
        ),
        color=discord.Color.dark_red()
    )

    linhas = []

    for chave in ORDEM_PERICIAS:

        emoji, nome_pericia = (
            PERICIAS[
                chave
            ]
        )

        valor = ficha.get(
            chave,
            0
        )

        linhas.append(
            f"{emoji} {nome_pericia}: "
            f"**{valor}**"
        )

    embed.description = (
        "\n".join(
            linhas
        )
    )

    embed.set_footer(
        text=(
            "Página 2/2 • Perícias"
        )
    )

    return embed


# ============================================================
# BUSCAR FICHA ATUALIZADA
# ============================================================

def obter_ficha_atualizada(
    ficha_id
):

    dados = buscar_ficha(
        ficha_id
    )

    return transformar_ficha(
        dados
    )


# ============================================================
# MODAL — RECURSOS
# ============================================================

class ModalEditarRecursos(
    discord.ui.Modal,
    title="Editar Recursos"
):

    def __init__(
        self,
        ficha
    ):

        super().__init__()

        self.ficha_id = (
            ficha["id"]
        )

        self.hp_atual = (
            discord.ui.TextInput(
                label="HP atual",
                default=str(
                    ficha.get(
                        "hp_atual",
                        0
                    )
                ),
                required=True,
                max_length=10
            )
        )

        self.hp_max = (
            discord.ui.TextInput(
                label="HP máximo",
                default=str(
                    ficha.get(
                        "hp_max",
                        0
                    )
                ),
                required=True,
                max_length=10
            )
        )

        self.mana_atual = (
            discord.ui.TextInput(
                label="Mana atual",
                default=str(
                    ficha.get(
                        "mana_atual",
                        0
                    )
                ),
                required=True,
                max_length=10
            )
        )

        self.mana_max = (
            discord.ui.TextInput(
                label="Mana máxima",
                default=str(
                    ficha.get(
                        "mana_max",
                        0
                    )
                ),
                required=True,
                max_length=10
            )
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

        ficha = (
            obter_ficha_atualizada(
                self.ficha_id
            )
        )

        if ficha is None:

            await interaction.response.send_message(
                "❌ Esta ficha não existe mais.",
                ephemeral=True
            )

            return

        if not pode_alterar_ficha(
            interaction,
            ficha
        ):

            await interaction.response.send_message(
                "❌ Você não possui permissão "
                "para editar esta ficha.",
                ephemeral=True
            )

            return

        try:

            novo_hp_atual = int(
                self.hp_atual.value
            )

            novo_hp_max = int(
                self.hp_max.value
            )

            nova_mana_atual = int(
                self.mana_atual.value
            )

            nova_mana_max = int(
                self.mana_max.value
            )

        except ValueError:

            await interaction.response.send_message(
                "❌ Todos os valores precisam "
                "ser números inteiros.",
                ephemeral=True
            )

            return

        if novo_hp_max <= 0:

            await interaction.response.send_message(
                "❌ O HP máximo precisa "
                "ser maior que 0.",
                ephemeral=True
            )

            return

        if novo_hp_atual < 0:

            await interaction.response.send_message(
                "❌ O HP atual não pode "
                "ser negativo.",
                ephemeral=True
            )

            return

        if novo_hp_atual > novo_hp_max:

            await interaction.response.send_message(
                "❌ O HP atual não pode "
                "ser maior que o HP máximo.",
                ephemeral=True
            )

            return

        if nova_mana_max < 0:

            await interaction.response.send_message(
                "❌ A Mana máxima não pode "
                "ser negativa.",
                ephemeral=True
            )

            return

        if nova_mana_atual < 0:

            await interaction.response.send_message(
                "❌ A Mana atual não pode "
                "ser negativa.",
                ephemeral=True
            )

            return

        if nova_mana_atual > nova_mana_max:

            await interaction.response.send_message(
                "❌ A Mana atual não pode "
                "ser maior que a Mana máxima.",
                ephemeral=True
            )

            return

        hp_anterior = (
            f"{ficha['hp_atual']}/"
            f"{ficha['hp_max']}"
        )

        hp_novo = (
            f"{novo_hp_atual}/"
            f"{novo_hp_max}"
        )

        mana_anterior = (
            f"{ficha['mana_atual']}/"
            f"{ficha['mana_max']}"
        )

        mana_nova = (
            f"{nova_mana_atual}/"
            f"{nova_mana_max}"
        )

        cursor.execute("""
            UPDATE fichas
            SET
                hp_atual = ?,
                hp_max = ?,
                mana_atual = ?,
                mana_max = ?
            WHERE id = ?
        """, (
            novo_hp_atual,
            novo_hp_max,
            nova_mana_atual,
            nova_mana_max,
            self.ficha_id
        ))

        db.commit()

        if hp_anterior != hp_novo:

            registrar_historico(
                ficha["channel_id"],
                ficha["id"],
                ficha["nome"],
                ficha["tipo"],
                interaction.user.id,
                "recursos",
                campo="hp",
                valor_anterior=hp_anterior,
                valor_novo=hp_novo,
                descricao=(
                    "❤️ HP alterado "
                    "pela edição da ficha."
                )
            )

        if (
            mana_anterior
            != mana_nova
        ):

            registrar_historico(
                ficha["channel_id"],
                ficha["id"],
                ficha["nome"],
                ficha["tipo"],
                interaction.user.id,
                "recursos",
                campo="mana",
                valor_anterior=mana_anterior,
                valor_novo=mana_nova,
                descricao=(
                    "🔵 Mana alterada "
                    "pela edição da ficha."
                )
            )

        await interaction.response.send_message(
            "✅ Recursos atualizados!\n\n"
            f"❤️ HP: **{novo_hp_atual}/{novo_hp_max}**\n"
            f"🔵 Mana: **{nova_mana_atual}/{nova_mana_max}**",
            ephemeral=True
        )


# ============================================================
# MODAL — XP
# ============================================================

class ModalEditarXP(
    discord.ui.Modal,
    title="Editar XP"
):

    def __init__(
        self,
        ficha
    ):

        super().__init__()

        self.ficha_id = (
            ficha["id"]
        )

        self.xp = (
            discord.ui.TextInput(
                label="XP atual",
                default=str(
                    ficha.get(
                        "xp",
                        0
                    )
                ),
                required=True,
                max_length=12
            )
        )

        self.add_item(
            self.xp
        )


    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        ficha = (
            obter_ficha_atualizada(
                self.ficha_id
            )
        )

        if ficha is None:

            await interaction.response.send_message(
                "❌ Esta ficha não existe mais.",
                ephemeral=True
            )

            return

        if not pode_alterar_ficha(
            interaction,
            ficha
        ):

            await interaction.response.send_message(
                "❌ Você não possui permissão "
                "para editar esta ficha.",
                ephemeral=True
            )

            return

        try:

            novo_xp = int(
                self.xp.value
            )

        except ValueError:

            await interaction.response.send_message(
                "❌ O XP precisa ser "
                "um número inteiro.",
                ephemeral=True
            )

            return

        if novo_xp < 0:

            await interaction.response.send_message(
                "❌ O XP não pode ser negativo.",
                ephemeral=True
            )

            return

        xp_anterior = (
            ficha.get(
                "xp",
                0
            )
        )

        cursor.execute("""
            UPDATE fichas
            SET xp = ?
            WHERE id = ?
        """, (
            novo_xp,
            self.ficha_id
        ))

        db.commit()

        if (
            xp_anterior
            != novo_xp
        ):

            registrar_historico(
                ficha["channel_id"],
                ficha["id"],
                ficha["nome"],
                ficha["tipo"],
                interaction.user.id,
                "xp",
                campo="xp",
                valor_anterior=xp_anterior,
                valor_novo=novo_xp,
                descricao=(
                    "✨ XP alterado "
                    "pela edição da ficha."
                )
            )

        await interaction.response.send_message(
            f"✅ XP atualizado para "
            f"**{novo_xp}**.",
            ephemeral=True
        )


# ============================================================
# MODAL — ATRIBUTOS
# ============================================================

class ModalEditarAtributos(
    discord.ui.Modal
):

    def __init__(
        self,
        ficha_id,
        grupo
    ):

        self.ficha_id = (
            ficha_id
        )

        self.grupo = grupo

        ficha = (
            obter_ficha_atualizada(
                ficha_id
            )
        )

        campos = (
            GRUPOS_ATRIBUTOS[
                grupo
            ]
        )

        super().__init__(
            title=(
                f"Editar Atributos "
                f"{grupo + 1}/"
                f"{len(GRUPOS_ATRIBUTOS)}"
            )
        )

        self.inputs = {}

        for chave in campos:

            campo = (
                discord.ui.TextInput(
                    label=NOMES_ATRIBUTOS[
                        chave
                    ],
                    default=str(
                        ficha.get(
                            chave,
                            0
                        )
                    ),
                    required=True,
                    max_length=7
                )
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

        ficha = (
            obter_ficha_atualizada(
                self.ficha_id
            )
        )

        if ficha is None:

            await interaction.response.send_message(
                "❌ Esta ficha não existe mais.",
                ephemeral=True
            )

            return

        if not pode_alterar_ficha(
            interaction,
            ficha
        ):

            await interaction.response.send_message(
                "❌ Você não possui permissão "
                "para editar esta ficha.",
                ephemeral=True
            )

            return

        valores = {}

        try:

            for chave, campo in (
                self.inputs.items()
            ):

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
                "❌ Todos os atributos precisam "
                "ser números inteiros maiores "
                "ou iguais a 0.",
                ephemeral=True
            )

            return

        alteracoes = []

        for chave, valor in (
            valores.items()
        ):

            anterior = ficha.get(
                chave,
                0
            )

            if anterior == valor:

                continue

            cursor.execute(
                f"""
                UPDATE fichas
                SET {chave} = ?
                WHERE id = ?
                """,
                (
                    valor,
                    self.ficha_id
                )
            )

            alteracoes.append(
                (
                    chave,
                    anterior,
                    valor
                )
            )

        db.commit()

        for (
            chave,
            anterior,
            novo
        ) in alteracoes:

            registrar_historico(
                ficha["channel_id"],
                ficha["id"],
                ficha["nome"],
                ficha["tipo"],
                interaction.user.id,
                "atributo",
                campo=chave,
                valor_anterior=anterior,
                valor_novo=novo,
                descricao=(
                    f"⚔️ "
                    f"{NOMES_ATRIBUTOS[chave]} "
                    f"alterado."
                )
            )

        proximo = (
            self.grupo + 1
        )

        if (
            proximo
            < len(
                GRUPOS_ATRIBUTOS
            )
        ):

            await interaction.response.send_message(
                "✅ Primeira parte dos "
                "atributos salva.\n\n"
                "Clique abaixo para continuar.",
                view=ViewContinuarEdicaoAtributos(
                    self.ficha_id,
                    proximo
                ),
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "✅ Todos os atributos "
            "foram atualizados.",
            ephemeral=True
        )


# ============================================================
# CONTINUAR EDIÇÃO DOS ATRIBUTOS
# ============================================================

class ViewContinuarEdicaoAtributos(
    discord.ui.View
):

    def __init__(
        self,
        ficha_id,
        grupo
    ):

        super().__init__(
            timeout=300
        )

        self.ficha_id = (
            ficha_id
        )

        self.grupo = grupo


    @discord.ui.button(
        label="➡️ Continuar atributos",
        style=discord.ButtonStyle.primary
    )
    async def continuar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        ficha = (
            obter_ficha_atualizada(
                self.ficha_id
            )
        )

        if ficha is None:

            await interaction.response.send_message(
                "❌ Esta ficha não existe mais.",
                ephemeral=True
            )

            return

        if not pode_alterar_ficha(
            interaction,
            ficha
        ):

            await interaction.response.send_message(
                "❌ Você não possui permissão "
                "para editar esta ficha.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            ModalEditarAtributos(
                self.ficha_id,
                self.grupo
            )
        )


# ============================================================
# MODAL — PERÍCIAS
# ============================================================

class ModalEditarPericias(
    discord.ui.Modal
):

    def __init__(
        self,
        ficha_id,
        grupo
    ):

        self.ficha_id = (
            ficha_id
        )

        self.grupo = grupo

        ficha = (
            obter_ficha_atualizada(
                ficha_id
            )
        )

        campos = (
            GRUPOS_PERICIAS[
                grupo
            ]
        )

        super().__init__(
            title=(
                f"Editar Perícias "
                f"{grupo + 1}/"
                f"{len(GRUPOS_PERICIAS)}"
            )
        )

        self.inputs = {}

        for chave in campos:

            emoji, nome = (
                PERICIAS[
                    chave
                ]
            )

            campo = (
                discord.ui.TextInput(
                    label=nome[:45],
                    default=str(
                        ficha.get(
                            chave,
                            0
                        )
                    ),
                    placeholder="0 a 5",
                    required=True,
                    max_length=1
                )
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

        ficha = (
            obter_ficha_atualizada(
                self.ficha_id
            )
        )

        if ficha is None:

            await interaction.response.send_message(
                "❌ Esta ficha não existe mais.",
                ephemeral=True
            )

            return

        if not pode_alterar_ficha(
            interaction,
            ficha
        ):

            await interaction.response.send_message(
                "❌ Você não possui permissão "
                "para editar esta ficha.",
                ephemeral=True
            )

            return

        valores = {}

        try:

            for chave, campo in (
                self.inputs.items()
            ):

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
                "❌ Todas as perícias precisam "
                "ser números inteiros entre "
                "**0 e 5**.",
                ephemeral=True
            )

            return

        alteracoes = []

        for chave, valor in (
            valores.items()
        ):

            anterior = ficha.get(
                chave,
                0
            )

            if anterior == valor:

                continue

            cursor.execute(
                f"""
                UPDATE fichas
                SET {chave} = ?
                WHERE id = ?
                """,
                (
                    valor,
                    self.ficha_id
                )
            )

            alteracoes.append(
                (
                    chave,
                    anterior,
                    valor
                )
            )

        db.commit()

        for (
            chave,
            anterior,
            novo
        ) in alteracoes:

            emoji, nome = (
                PERICIAS[
                    chave
                ]
            )

            registrar_historico(
                ficha["channel_id"],
                ficha["id"],
                ficha["nome"],
                ficha["tipo"],
                interaction.user.id,
                "pericia",
                campo=chave,
                valor_anterior=anterior,
                valor_novo=novo,
                descricao=(
                    f"{emoji} "
                    f"{nome} alterada."
                )
            )

        proximo = (
            self.grupo + 1
        )

        if (
            proximo
            < len(
                GRUPOS_PERICIAS
            )
        ):

            await interaction.response.send_message(
                f"✅ Perícias "
                f"{self.grupo + 1}/"
                f"{len(GRUPOS_PERICIAS)} "
                f"salvas.\n\n"
                f"Clique abaixo para continuar.",
                view=ViewContinuarEdicaoPericias(
                    self.ficha_id,
                    proximo
                ),
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "✅ Todas as perícias "
            "foram atualizadas.",
            ephemeral=True
        )


# ============================================================
# CONTINUAR EDIÇÃO DAS PERÍCIAS
# ============================================================

class ViewContinuarEdicaoPericias(
    discord.ui.View
):

    def __init__(
        self,
        ficha_id,
        grupo
    ):

        super().__init__(
            timeout=300
        )

        self.ficha_id = (
            ficha_id
        )

        self.grupo = grupo


    @discord.ui.button(
        label="➡️ Continuar perícias",
        style=discord.ButtonStyle.primary
    )
    async def continuar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        ficha = (
            obter_ficha_atualizada(
                self.ficha_id
            )
        )

        if ficha is None:

            await interaction.response.send_message(
                "❌ Esta ficha não existe mais.",
                ephemeral=True
            )

            return

        if not pode_alterar_ficha(
            interaction,
            ficha
        ):

            await interaction.response.send_message(
                "❌ Você não possui permissão "
                "para editar esta ficha.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            ModalEditarPericias(
                self.ficha_id,
                self.grupo
            )
        )


# ============================================================
# MENU DE EDIÇÃO
# ============================================================

class EditarFichaView(
    discord.ui.View
):

    def __init__(
        self,
        ficha_id,
        usuario_id
    ):

        super().__init__(
            timeout=300
        )

        self.ficha_id = (
            ficha_id
        )

        self.usuario_id = (
            usuario_id
        )


    async def interaction_check(
        self,
        interaction: discord.Interaction
    ):

        if (
            interaction.user.id
            != self.usuario_id
        ):

            await interaction.response.send_message(
                "❌ Somente quem abriu este "
                "menu pode utilizar "
                "estes botões.",
                ephemeral=True
            )

            return False

        ficha = (
            obter_ficha_atualizada(
                self.ficha_id
            )
        )

        if ficha is None:

            await interaction.response.send_message(
                "❌ Esta ficha não existe mais.",
                ephemeral=True
            )

            return False

        if not pode_alterar_ficha(
            interaction,
            ficha
        ):

            await interaction.response.send_message(
                "❌ Você não possui permissão "
                "para editar esta ficha.",
                ephemeral=True
            )

            return False

        return True


    # ========================================================
    # RECURSOS
    # ========================================================

    @discord.ui.button(
        label="Recursos",
        emoji="❤️",
        style=discord.ButtonStyle.primary
    )
    async def recursos(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        ficha = (
            obter_ficha_atualizada(
                self.ficha_id
            )
        )

        await interaction.response.send_modal(
            ModalEditarRecursos(
                ficha
            )
        )


    # ========================================================
    # XP
    # ========================================================

    @discord.ui.button(
        label="XP",
        emoji="✨",
        style=discord.ButtonStyle.secondary
    )
    async def xp(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        ficha = (
            obter_ficha_atualizada(
                self.ficha_id
            )
        )

        await interaction.response.send_modal(
            ModalEditarXP(
                ficha
            )
        )


    # ========================================================
    # ATRIBUTOS
    # ========================================================

    @discord.ui.button(
        label="Atributos",
        emoji="⚔️",
        style=discord.ButtonStyle.secondary
    )
    async def atributos(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.send_modal(
            ModalEditarAtributos(
                self.ficha_id,
                grupo=0
            )
        )


    # ========================================================
    # PERÍCIAS
    # ========================================================

    @discord.ui.button(
        label="Perícias",
        emoji="📚",
        style=discord.ButtonStyle.secondary
    )
    async def pericias(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.send_modal(
            ModalEditarPericias(
                self.ficha_id,
                grupo=0
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


    # ========================================================
    # ATUALIZAR FICHA DA VIEW
    # ========================================================

    def atualizar_ficha(
        self
    ):

        ficha_atualizada = (
            obter_ficha_atualizada(
                self.ficha["id"]
            )
        )

        if (
            ficha_atualizada
            is not None
        ):

            self.ficha = (
                ficha_atualizada
            )

        return ficha_atualizada


    # ========================================================
    # ATUALIZAR BOTÕES
    # ========================================================

    def atualizar_botoes(
        self
    ):

        self.status_button.disabled = (
            self.pagina == 1
        )

        self.pericias_button.disabled = (
            self.pagina == 2
        )


    # ========================================================
    # STATUS
    # ========================================================

    @discord.ui.button(
        label="◀ Status",
        style=discord.ButtonStyle.secondary
    )
    async def status_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        ficha = (
            self.atualizar_ficha()
        )

        if ficha is None:

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


    # ========================================================
    # PERÍCIAS
    # ========================================================

    @discord.ui.button(
        label="Perícias ▶",
        style=discord.ButtonStyle.secondary
    )
    async def pericias_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        ficha = (
            self.atualizar_ficha()
        )

        if ficha is None:

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


    # ========================================================
    # EDITAR
    # ========================================================

    @discord.ui.button(
        label="Editar",
        emoji="✏️",
        style=discord.ButtonStyle.success
    )
    async def editar_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        ficha = (
            self.atualizar_ficha()
        )

        if ficha is None:

            await interaction.response.send_message(
                "❌ Esta ficha não existe mais.",
                ephemeral=True
            )

            return

        if not pode_alterar_ficha(
            interaction,
            ficha
        ):

            await interaction.response.send_message(
                "❌ Você não possui permissão "
                "para editar esta ficha.",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "✏️ **Editar ficha**\n\n"
            "Escolha o grupo que deseja alterar:",
            view=EditarFichaView(
                ficha["id"],
                interaction.user.id
            ),
            ephemeral=True
        )
