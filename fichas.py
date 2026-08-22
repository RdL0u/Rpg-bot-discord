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
# BUSCAR FICHA DE JOGADOR
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
# BUSCAR FICHA POR ID
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

    # ========================================================
    # IMPORTANTE
    #
    # O banco já passou por migrações.
    #
    # Por isso NÃO podemos assumir que a ordem física das
    # colunas seja igual à ordem lógica esperada pelo código.
    # ========================================================

    cursor.execute(
        "PRAGMA table_info(fichas)"
    )

    informacoes_colunas = (
        cursor.fetchall()
    )

    colunas_reais = [
        coluna[1]
        for coluna
        in informacoes_colunas
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
# REFLEXO DE COMBATE
# ============================================================

def calcular_rc(
    ficha
):

    return (
        ficha.get(
            "esquiva",
            0
        )
        + ficha.get(
            "destreza",
            0
        )
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
        atual
        / maximo
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
        atual
        / maximo
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

    if maximo <= 0:

        return "0/0"

    return (
        f"{atual}/{maximo}"
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

    # ========================================================
    # ADMIN
    # ========================================================

    if eh_admin(
        interaction
    ):

        return True

    tipo = ficha.get(
        "tipo"
    )

    # ========================================================
    # JOGADOR
    # ========================================================

    if tipo == "jogador":

        if (
            ficha.get(
                "dono_id"
            )
            == interaction.user.id
        ):

            return True

        if eh_mestre(
            interaction
        ):

            return True

        return False

    # ========================================================
    # NPC
    # ========================================================

    if tipo == "npc":

        if eh_mestre(
            interaction
        ):

            return True

        if (
            ficha.get(
                "mestre_id"
            )
            == interaction.user.id
        ):

            return True

        return False

    return False


# ============================================================
# RECARREGAR FICHA
# ============================================================

def recarregar_ficha(
    ficha_id
):

    dados = buscar_ficha(
        ficha_id
    )

    if dados is None:

        return None

    return transformar_ficha(
        dados
    )


# ============================================================
# FORMATAR ATRIBUTOS
# ============================================================

def formatar_atributos(
    ficha
):

    return (
        f"💪 For: **{ficha.get('forca', 0)}**"
        f"  🏹 Des: **{ficha.get('destreza', 0)}**\n"

        f"🛡️ Vig: **{ficha.get('vigor', 0)}**"
        f"  🧠 Int: **{ficha.get('inteligencia', 0)}**\n"

        f"🎭 Car: **{ficha.get('carisma', 0)}**"
        f"  💡 Rac: **{ficha.get('raciocinio', 0)}**"
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

    estado_atual_hp = (
        estado_hp(
            hp_atual,
            hp_max
        )
    )

    estado_atual_mana = (
        estado_mana(
            mana_atual,
            mana_max
        )
    )

    embed = discord.Embed(
        title=(
            f"📜 FICHA DE "
            f"{nome.upper()}"
        ),
        color=discord.Color.dark_red()
    )

    # ========================================================
    # STATUS
    # ========================================================

    embed.add_field(
        name="❤️ STATUS",
        value=(
            f"❤️ HP: **{hp_atual}/{hp_max}** "
            f"• {estado_atual_hp}\n"

            f"🔵 Mana: **{mana_atual}/{mana_max}** "
            f"• {estado_atual_mana}\n"

            f"✨ XP: **{xp}**    "
            f"⚡ RC: **{rc}**"
        ),
        inline=False
    )

    # ========================================================
    # ATRIBUTOS
    # ========================================================

    embed.add_field(
        name="⚔️ ATRIBUTOS",
        value=formatar_atributos(
            ficha
        ),
        inline=False
    )

    # ========================================================
    # RODAPÉ
    # ========================================================

    if jogador is not None:

        embed.set_footer(
            text=(
                f"Jogador: "
                f"{jogador.display_name}"
                f" • Página 1/2 "
                f"• Status e Atributos"
            )
        )

    else:

        embed.set_footer(
            text=(
                "Página 1/2 "
                "• Status e Atributos"
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

    # ========================================================
    # UMA COLUNA
    # ========================================================

    texto = "\n".join(
        linhas
    )

    embed.add_field(
        name="📚 PERÍCIAS",
        value=(
            texto
            if texto
            else "Nenhuma perícia."
        ),
        inline=False
    )

    # ========================================================
    # RODAPÉ
    # ========================================================

    if jogador is not None:

        embed.set_footer(
            text=(
                f"Jogador: "
                f"{jogador.display_name}"
                f" • Página 2/2 "
                f"• Perícias"
            )
        )

    else:

        embed.set_footer(
            text=(
                "Página 2/2 "
                "• Perícias"
            )
        )

    return embed


# ============================================================
# MODAL — EDITAR RECURSOS
# ============================================================

class EditarRecursosModal(
    discord.ui.Modal
):

    def __init__(
        self,
        ficha,
        view_ficha=None
    ):

        super().__init__(
            title="Editar recursos"
        )

        self.ficha = ficha
        self.view_ficha = view_ficha

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

        ficha_atual = (
            recarregar_ficha(
                self.ficha[
                    "id"
                ]
            )
        )

        if ficha_atual is None:

            await interaction.response.send_message(
                "❌ Essa ficha não existe mais.",
                ephemeral=True
            )

            return

        if not pode_alterar_ficha(
            interaction,
            ficha_atual
        ):

            await interaction.response.send_message(
                "❌ Você não pode alterar essa ficha.",
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
                "❌ O HP máximo precisa ser "
                "maior que 0.",
                ephemeral=True
            )

            return

        if (
            novo_hp_atual < 0
            or novo_hp_atual > novo_hp_max
        ):

            await interaction.response.send_message(
                "❌ O HP atual precisa estar "
                "entre 0 e o HP máximo.",
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

        if (
            nova_mana_atual < 0
            or nova_mana_atual
            > nova_mana_max
        ):

            await interaction.response.send_message(
                "❌ A Mana atual precisa estar "
                "entre 0 e a Mana máxima.",
                ephemeral=True
            )

            return

        antigo_hp_atual = (
            ficha_atual.get(
                "hp_atual",
                0
            )
        )

        antigo_hp_max = (
            ficha_atual.get(
                "hp_max",
                0
            )
        )

        antiga_mana_atual = (
            ficha_atual.get(
                "mana_atual",
                0
            )
        )

        antiga_mana_max = (
            ficha_atual.get(
                "mana_max",
                0
            )
        )

        cursor.execute("""
            UPDATE fichas
            SET hp_atual = ?,
                hp_max = ?,
                mana_atual = ?,
                mana_max = ?
            WHERE id = ?
        """, (
            novo_hp_atual,
            novo_hp_max,
            nova_mana_atual,
            nova_mana_max,
            ficha_atual["id"]
        ))

        db.commit()

        # ====================================================
        # HISTÓRICO
        # ====================================================

        mudancas = [
            (
                "hp_atual",
                antigo_hp_atual,
                novo_hp_atual
            ),
            (
                "hp_max",
                antigo_hp_max,
                novo_hp_max
            ),
            (
                "mana_atual",
                antiga_mana_atual,
                nova_mana_atual
            ),
            (
                "mana_max",
                antiga_mana_max,
                nova_mana_max
            ),
        ]

        for (
            campo,
            anterior,
            novo
        ) in mudancas:

            if anterior == novo:

                continue

            registrar_historico(
                interaction.channel.id,
                ficha_atual["id"],
                ficha_atual["nome"],
                ficha_atual["tipo"],
                interaction.user.id,
                "recursos",
                campo=campo,
                valor_anterior=anterior,
                valor_novo=novo,
                descricao=(
                    "⚙️ Alterado pelo "
                    "menu de edição da ficha."
                )
            )

        ficha_nova = (
            recarregar_ficha(
                ficha_atual[
                    "id"
                ]
            )
        )

        if (
            self.view_ficha
            is not None
            and ficha_nova
            is not None
        ):

            self.view_ficha.ficha = (
                ficha_nova
            )

        await interaction.response.send_message(
            f"✅ Recursos de "
            f"**{ficha_atual['nome']}** "
            f"atualizados.\n\n"

            f"❤️ HP: "
            f"**{novo_hp_atual}/{novo_hp_max}** "
            f"• "
            f"{estado_hp(novo_hp_atual, novo_hp_max)}\n"

            f"🔵 Mana: "
            f"**{nova_mana_atual}/{nova_mana_max}** "
            f"• "
            f"{estado_mana(nova_mana_atual, nova_mana_max)}",
            ephemeral=True
        )


# ============================================================
# MODAL — EDITAR XP
# ============================================================

class EditarXPModal(
    discord.ui.Modal
):

    def __init__(
        self,
        ficha,
        view_ficha=None
    ):

        super().__init__(
            title="Editar XP"
        )

        self.ficha = ficha
        self.view_ficha = view_ficha

        self.valor = (
            discord.ui.TextInput(
                label="XP atual",
                default=str(
                    ficha.get(
                        "xp",
                        0
                    )
                ),
                required=True,
                max_length=10
            )
        )

        self.add_item(
            self.valor
        )


    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        ficha_atual = (
            recarregar_ficha(
                self.ficha[
                    "id"
                ]
            )
        )

        if ficha_atual is None:

            await interaction.response.send_message(
                "❌ Essa ficha não existe mais.",
                ephemeral=True
            )

            return

        if not pode_alterar_ficha(
            interaction,
            ficha_atual
        ):

            await interaction.response.send_message(
                "❌ Você não pode alterar essa ficha.",
                ephemeral=True
            )

            return

        try:

            novo_xp = int(
                self.valor.value
            )

        except ValueError:

            await interaction.response.send_message(
                "❌ O XP precisa ser um "
                "número inteiro.",
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
            ficha_atual.get(
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
            ficha_atual["id"]
        ))

        db.commit()

        if xp_anterior != novo_xp:

            registrar_historico(
                interaction.channel.id,
                ficha_atual["id"],
                ficha_atual["nome"],
                ficha_atual["tipo"],
                interaction.user.id,
                "xp",
                campo="xp",
                valor_anterior=xp_anterior,
                valor_novo=novo_xp,
                descricao=(
                    "⚙️ XP alterado pelo "
                    "menu de edição da ficha."
                )
            )

        ficha_nova = (
            recarregar_ficha(
                ficha_atual[
                    "id"
                ]
            )
        )

        if (
            self.view_ficha
            is not None
            and ficha_nova
            is not None
        ):

            self.view_ficha.ficha = (
                ficha_nova
            )

        await interaction.response.send_message(
            f"✨ XP de "
            f"**{ficha_atual['nome']}** "
            f"alterado de "
            f"**{xp_anterior}** para "
            f"**{novo_xp}**.",
            ephemeral=True
        )


# ============================================================
# MODAL — EDITAR ATRIBUTO
# ============================================================

class EditarAtributoModal(
    discord.ui.Modal
):

    def __init__(
        self,
        ficha,
        atributo,
        view_ficha=None
    ):

        self.ficha = ficha
        self.atributo = atributo
        self.view_ficha = view_ficha

        emoji, nome = (
            ATRIBUTOS[
                atributo
            ]
        )

        super().__init__(
            title=f"Editar {nome}"
        )

        self.valor = (
            discord.ui.TextInput(
                label=nome,
                default=str(
                    ficha.get(
                        atributo,
                        0
                    )
                ),
                required=True,
                max_length=10
            )
        )

        self.add_item(
            self.valor
        )


    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        ficha_atual = (
            recarregar_ficha(
                self.ficha[
                    "id"
                ]
            )
        )

        if ficha_atual is None:

            await interaction.response.send_message(
                "❌ Essa ficha não existe mais.",
                ephemeral=True
            )

            return

        if not pode_alterar_ficha(
            interaction,
            ficha_atual
        ):

            await interaction.response.send_message(
                "❌ Você não pode alterar essa ficha.",
                ephemeral=True
            )

            return

        try:

            novo_valor = int(
                self.valor.value
            )

        except ValueError:

            await interaction.response.send_message(
                "❌ O valor precisa ser um "
                "número inteiro.",
                ephemeral=True
            )

            return

        if novo_valor < 0:

            await interaction.response.send_message(
                "❌ O valor não pode ser negativo.",
                ephemeral=True
            )

            return

        valor_anterior = (
            ficha_atual.get(
                self.atributo,
                0
            )
        )

        cursor.execute(
            f"""
            UPDATE fichas
            SET {self.atributo} = ?
            WHERE id = ?
            """,
            (
                novo_valor,
                ficha_atual["id"]
            )
        )

        db.commit()

        if (
            valor_anterior
            != novo_valor
        ):

            registrar_historico(
                interaction.channel.id,
                ficha_atual["id"],
                ficha_atual["nome"],
                ficha_atual["tipo"],
                interaction.user.id,
                "atributo",
                campo=self.atributo,
                valor_anterior=valor_anterior,
                valor_novo=novo_valor,
                descricao=(
                    "⚙️ Atributo alterado pelo "
                    "menu de edição da ficha."
                )
            )

        ficha_nova = (
            recarregar_ficha(
                ficha_atual[
                    "id"
                ]
            )
        )

        if (
            self.view_ficha
            is not None
            and ficha_nova
            is not None
        ):

            self.view_ficha.ficha = (
                ficha_nova
            )

        emoji, nome = (
            ATRIBUTOS[
                self.atributo
            ]
        )

        await interaction.response.send_message(
            f"{emoji} **{nome}** alterado de "
            f"**{valor_anterior}** para "
            f"**{novo_valor}**.",
            ephemeral=True
        )


# ============================================================
# MODAL — EDITAR PERÍCIA
# ============================================================

class EditarPericiaModal(
    discord.ui.Modal
):

    def __init__(
        self,
        ficha,
        pericia,
        view_ficha=None
    ):

        self.ficha = ficha
        self.pericia = pericia
        self.view_ficha = view_ficha

        emoji, nome = (
            PERICIAS[
                pericia
            ]
        )

        super().__init__(
            title=f"Editar {nome}"[:45]
        )

        self.valor = (
            discord.ui.TextInput(
                label=nome[:45],
                default=str(
                    ficha.get(
                        pericia,
                        0
                    )
                ),
                required=True,
                max_length=10
            )
        )

        self.add_item(
            self.valor
        )


    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        ficha_atual = (
            recarregar_ficha(
                self.ficha[
                    "id"
                ]
            )
        )

        if ficha_atual is None:

            await interaction.response.send_message(
                "❌ Essa ficha não existe mais.",
                ephemeral=True
            )

            return

        if not pode_alterar_ficha(
            interaction,
            ficha_atual
        ):

            await interaction.response.send_message(
                "❌ Você não pode alterar essa ficha.",
                ephemeral=True
            )

            return

        try:

            novo_valor = int(
                self.valor.value
            )

        except ValueError:

            await interaction.response.send_message(
                "❌ O valor precisa ser um "
                "número inteiro.",
                ephemeral=True
            )

            return

        if novo_valor < 0:

            await interaction.response.send_message(
                "❌ O valor não pode ser negativo.",
                ephemeral=True
            )

            return

        valor_anterior = (
            ficha_atual.get(
                self.pericia,
                0
            )
        )

        cursor.execute(
            f"""
            UPDATE fichas
            SET {self.pericia} = ?
            WHERE id = ?
            """,
            (
                novo_valor,
                ficha_atual["id"]
            )
        )

        db.commit()

        if (
            valor_anterior
            != novo_valor
        ):

            registrar_historico(
                interaction.channel.id,
                ficha_atual["id"],
                ficha_atual["nome"],
                ficha_atual["tipo"],
                interaction.user.id,
                "pericia",
                campo=self.pericia,
                valor_anterior=valor_anterior,
                valor_novo=novo_valor,
                descricao=(
                    "⚙️ Perícia alterada pelo "
                    "menu de edição da ficha."
                )
            )

        ficha_nova = (
            recarregar_ficha(
                ficha_atual[
                    "id"
                ]
            )
        )

        if (
            self.view_ficha
            is not None
            and ficha_nova
            is not None
        ):

            self.view_ficha.ficha = (
                ficha_nova
            )

        emoji, nome = (
            PERICIAS[
                self.pericia
            ]
        )

        await interaction.response.send_message(
            f"{emoji} **{nome}** alterada de "
            f"**{valor_anterior}** para "
            f"**{novo_valor}**.",
            ephemeral=True
        )


# ============================================================
# SELECT — ATRIBUTO
# ============================================================

class EditarAtributoSelect(
    discord.ui.Select
):

    def __init__(
        self,
        ficha,
        view_ficha=None
    ):

        self.ficha = ficha
        self.view_ficha = view_ficha

        opcoes = []

        for chave, (
            emoji,
            nome
        ) in ATRIBUTOS.items():

            opcoes.append(
                discord.SelectOption(
                    label=nome,
                    value=chave,
                    emoji=emoji,
                    description=(
                        f"Valor atual: "
                        f"{ficha.get(chave, 0)}"
                    )
                )
            )

        super().__init__(
            placeholder="Escolha o atributo...",
            min_values=1,
            max_values=1,
            options=opcoes
        )


    async def callback(
        self,
        interaction: discord.Interaction
    ):

        ficha_atual = (
            recarregar_ficha(
                self.ficha[
                    "id"
                ]
            )
        )

        if ficha_atual is None:

            await interaction.response.send_message(
                "❌ Essa ficha não existe mais.",
                ephemeral=True
            )

            return

        if not pode_alterar_ficha(
            interaction,
            ficha_atual
        ):

            await interaction.response.send_message(
                "❌ Você não pode alterar essa ficha.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            EditarAtributoModal(
                ficha_atual,
                self.values[0],
                self.view_ficha
            )
        )


# ============================================================
# VIEW — ATRIBUTOS
# ============================================================

class EditarAtributoView(
    discord.ui.View
):

    def __init__(
        self,
        ficha,
        view_ficha=None
    ):

        super().__init__(
            timeout=180
        )

        self.add_item(
            EditarAtributoSelect(
                ficha,
                view_ficha
            )
        )


# ============================================================
# SELECT — PERÍCIA
# ============================================================

class EditarPericiaSelect(
    discord.ui.Select
):

    def __init__(
        self,
        ficha,
        view_ficha=None
    ):

        self.ficha = ficha
        self.view_ficha = view_ficha

        opcoes = []

        for chave in ORDEM_PERICIAS:

            emoji, nome = (
                PERICIAS[
                    chave
                ]
            )

            opcoes.append(
                discord.SelectOption(
                    label=nome[:100],
                    value=chave,
                    emoji=emoji,
                    description=(
                        f"Valor atual: "
                        f"{ficha.get(chave, 0)}"
                    )[:100]
                )
            )

        super().__init__(
            placeholder="Escolha a perícia...",
            min_values=1,
            max_values=1,
            options=opcoes
        )


    async def callback(
        self,
        interaction: discord.Interaction
    ):

        ficha_atual = (
            recarregar_ficha(
                self.ficha[
                    "id"
                ]
            )
        )

        if ficha_atual is None:

            await interaction.response.send_message(
                "❌ Essa ficha não existe mais.",
                ephemeral=True
            )

            return

        if not pode_alterar_ficha(
            interaction,
            ficha_atual
        ):

            await interaction.response.send_message(
                "❌ Você não pode alterar essa ficha.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            EditarPericiaModal(
                ficha_atual,
                self.values[0],
                self.view_ficha
            )
        )


# ============================================================
# VIEW — PERÍCIAS
# ============================================================

class EditarPericiaView(
    discord.ui.View
):

    def __init__(
        self,
        ficha,
        view_ficha=None
    ):

        super().__init__(
            timeout=180
        )

        self.add_item(
            EditarPericiaSelect(
                ficha,
                view_ficha
            )
        )


# ============================================================
# SELECT — MENU PRINCIPAL DE EDIÇÃO
# ============================================================

class EditarFichaSelect(
    discord.ui.Select
):

    def __init__(
        self,
        ficha,
        view_ficha
    ):

        self.ficha = ficha
        self.view_ficha = view_ficha

        opcoes = [
            discord.SelectOption(
                label="Recursos",
                value="recursos",
                emoji="❤️",
                description=(
                    "Editar HP e Mana"
                )
            ),

            discord.SelectOption(
                label="XP",
                value="xp",
                emoji="✨",
                description=(
                    "Editar XP atual"
                )
            ),

            discord.SelectOption(
                label="Atributo",
                value="atributo",
                emoji="⚔️",
                description=(
                    "Editar um atributo"
                )
            ),

            discord.SelectOption(
                label="Perícia",
                value="pericia",
                emoji="📚",
                description=(
                    "Editar uma perícia"
                )
            ),
        ]

        super().__init__(
            placeholder="O que deseja editar?",
            min_values=1,
            max_values=1,
            options=opcoes
        )


    async def callback(
        self,
        interaction: discord.Interaction
    ):

        ficha_atual = (
            recarregar_ficha(
                self.ficha[
                    "id"
                ]
            )
        )

        if ficha_atual is None:

            await interaction.response.send_message(
                "❌ Essa ficha não existe mais.",
                ephemeral=True
            )

            return

        if not pode_alterar_ficha(
            interaction,
            ficha_atual
        ):

            await interaction.response.send_message(
                "❌ Você não pode alterar essa ficha.",
                ephemeral=True
            )

            return

        escolha = (
            self.values[0]
        )

        # ====================================================
        # RECURSOS
        # ====================================================

        if escolha == "recursos":

            await interaction.response.send_modal(
                EditarRecursosModal(
                    ficha_atual,
                    self.view_ficha
                )
            )

            return

        # ====================================================
        # XP
        # ====================================================

        if escolha == "xp":

            await interaction.response.send_modal(
                EditarXPModal(
                    ficha_atual,
                    self.view_ficha
                )
            )

            return

        # ====================================================
        # ATRIBUTO
        # ====================================================

        if escolha == "atributo":

            await interaction.response.send_message(
                "⚔️ **Escolha o atributo "
                "que deseja editar:**",
                view=EditarAtributoView(
                    ficha_atual,
                    self.view_ficha
                ),
                ephemeral=True
            )

            return

        # ====================================================
        # PERÍCIA
        # ====================================================

        if escolha == "pericia":

            await interaction.response.send_message(
                "📚 **Escolha a perícia "
                "que deseja editar:**",
                view=EditarPericiaView(
                    ficha_atual,
                    self.view_ficha
                ),
                ephemeral=True
            )

            return


# ============================================================
# VIEW — MENU PRINCIPAL DE EDIÇÃO
# ============================================================

class EditarFichaView(
    discord.ui.View
):

    def __init__(
        self,
        ficha,
        view_ficha
    ):

        super().__init__(
            timeout=180
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
    # ATUALIZAR DADOS DA FICHA
    # ========================================================

    def atualizar_ficha(
        self
    ):

        ficha_nova = (
            recarregar_ficha(
                self.ficha[
                    "id"
                ]
            )
        )

        if ficha_nova is not None:

            self.ficha = (
                ficha_nova
            )

        return ficha_nova


    # ========================================================
    # STATUS
    # ========================================================

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

        ficha_nova = (
            self.atualizar_ficha()
        )

        if ficha_nova is None:

            await interaction.response.send_message(
                "❌ Essa ficha não existe mais.",
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
        style=discord.ButtonStyle.secondary,
        row=0
    )
    async def pericias_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        ficha_nova = (
            self.atualizar_ficha()
        )

        if ficha_nova is None:

            await interaction.response.send_message(
                "❌ Essa ficha não existe mais.",
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
        label="✏️ Editar",
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def editar_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        ficha_nova = (
            self.atualizar_ficha()
        )

        if ficha_nova is None:

            await interaction.response.send_message(
                "❌ Essa ficha não existe mais.",
                ephemeral=True
            )

            return

        if not pode_alterar_ficha(
            interaction,
            self.ficha
        ):

            await interaction.response.send_message(
                "❌ Você não pode alterar essa ficha.",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            f"✏️ **Editar ficha de "
            f"{self.ficha['nome']}**\n\n"
            f"Escolha abaixo o que deseja alterar.",
            view=EditarFichaView(
                self.ficha,
                self
            ),
            ephemeral=True
        )
