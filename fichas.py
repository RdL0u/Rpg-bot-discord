import discord

from database import cursor, db

from config import (
    ATRIBUTOS,
    PERICIAS,
    ORDEM_PERICIAS
)

from comando.permissoes import (
    eh_admin,
    eh_mestre
)


# ============================================================
# BUSCAR FICHA DO JOGADOR
# ============================================================

def buscar_ficha_jogador(channel_id, user_id):

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

def buscar_ficha(ficha_id):

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

def transformar_ficha(dados):

    if dados is None:
        return None

    # Busca a ordem REAL das colunas da tabela no SQLite.
    # Isso evita valores trocados mesmo que tenham ocorrido
    # migrações com ALTER TABLE no passado.
    cursor.execute(
        "PRAGMA table_info(fichas)"
    )

    informacoes_colunas = cursor.fetchall()

    colunas_reais = [
        coluna[1]
        for coluna in informacoes_colunas
    ]

    ficha = {}

    for indice, valor in enumerate(dados):

        if indice < len(colunas_reais):

            nome_coluna = colunas_reais[
                indice
            ]

            ficha[
                nome_coluna
            ] = valor

    return ficha

# ============================================================
# ATUALIZAR HP
# ============================================================

def atualizar_hp(ficha_id, novo_hp):

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

def atualizar_mana(ficha_id, nova_mana):

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
# ATUALIZAR XP
# ============================================================

def adicionar_xp(ficha_id, valor):

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

def deletar_ficha(ficha_id):

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

def calcular_rc(ficha):

    return (
        ficha.get("esquiva", 0)
        + ficha.get("destreza", 0)
        + 5
    )


# ============================================================
# ESTADO DE RECURSO
# ============================================================

def estado_recurso(atual, maximo):

    if maximo <= 0:
        return "0/0"

    return f"{atual}/{maximo}"


# ============================================================
# PERMISSÃO DE EDIÇÃO
# ============================================================

def pode_alterar_ficha(
    interaction,
    ficha
):

    if ficha is None:
        return False

    # ADMINISTRADOR
    if eh_admin(interaction):
        return True

    tipo = ficha.get(
        "tipo"
    )

    # JOGADOR PODE EDITAR A PRÓPRIA FICHA
    if tipo == "jogador":

        if (
            ficha.get("dono_id")
            == interaction.user.id
        ):
            return True

        # MESTRE DA MESA
        if eh_mestre(interaction):
            return True

        return False

    # NPC — MESTRE OU ADMIN
    if tipo == "npc":

        if eh_mestre(interaction):
            return True

        if (
            ficha.get("mestre_id")
            == interaction.user.id
        ):
            return True

        return False

    return False


# ============================================================
# FORMATAR PERÍCIAS
# ============================================================

def formatar_pericias(ficha):

    linhas = []

    for chave in ORDEM_PERICIAS:

        emoji, nome = PERICIAS[chave]

        # Limpeza preventiva
        nome = nome.replace(
            "'''",
            ""
        ).strip()

        valor = ficha.get(
            chave,
            0
        )

        linhas.append(
            f"{emoji} {nome}: **{valor}**"
        )

    return linhas


# ============================================================
# CRIAR PÁGINA DE STATUS
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
        title=f"📜 FICHA DE {nome.upper()}",
        color=discord.Color.dark_red()
    )

    # ========================================================
    # STATUS
    # ========================================================

    embed.add_field(
        name="❤️ STATUS",
        value=(
            f"❤️ HP: **{hp_atual}/{hp_max}**    "
            f"🔵 Mana: **{mana_atual}/{mana_max}**\n"
            f"✨ XP: **{xp}**    "
            f"⚡ RC: **{rc}**"
        ),
        inline=False
    )

    # ========================================================
    # ATRIBUTOS — 2 COLUNAS
    # ========================================================

    atributos = (
        f"💪 For: **{ficha.get('forca', 0)}**"
        f"  🏹 Des: **{ficha.get('destreza', 0)}**\n"

        f"🛡️ Vig: **{ficha.get('vigor', 0)}**"
        f"  🧠 Int: **{ficha.get('inteligencia', 0)}**\n"

        f"🎭 Car: **{ficha.get('carisma', 0)}**"
        f"  💡 Rac: **{ficha.get('raciocinio', 0)}**"
    )

    embed.add_field(
        name="📊 ATRIBUTOS",
        value=atributos,
        inline=False
    )

    # ========================================================
    # RODAPÉ
    # ========================================================

    if jogador is not None:

        embed.set_footer(
            text=(
                f"Jogador: {jogador.display_name}"
                " • Página 1/2 • Status e Atributos"
            )
        )

    else:

        embed.set_footer(
            text="Página 1/2 • Status e Atributos"
        )

    return embed


# ============================================================
# CRIAR PÁGINA DE PERÍCIAS
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
        title=f"📜 FICHA DE {nome.upper()}",
        color=discord.Color.dark_red()
    )

    linhas = formatar_pericias(
        ficha
    )

    embed.add_field(
        name="📚 PERÍCIAS",
        value=(
            "\n".join(linhas)
            if linhas
            else "Nenhuma"
        ),
        inline=False
    )

    if jogador is not None:

        embed.set_footer(
            text=(
                f"Jogador: {jogador.display_name}"
                " • Página 2/2 • Perícias"
            )
        )

    else:

        embed.set_footer(
            text="Página 2/2 • Perícias"
        )

    return embed


# ============================================================
# MODAL — EDITAR ATRIBUTO
# ============================================================

class ModalEditarAtributo(
    discord.ui.Modal
):

    def __init__(
        self,
        ficha,
        atributo
    ):

        emoji, nome = ATRIBUTOS[
            atributo
        ]

        super().__init__(
            title=f"Editar {nome}"
        )

        self.ficha = ficha
        self.atributo = atributo
        self.emoji = emoji
        self.nome = nome

        self.valor = discord.ui.TextInput(
            label="Novo valor",
            default=str(
                ficha.get(
                    atributo,
                    0
                )
            ),
            placeholder="Digite um número inteiro",
            required=True,
            max_length=5
        )

        self.add_item(
            self.valor
        )


    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        if not pode_alterar_ficha(
            interaction,
            self.ficha
        ):

            await interaction.response.send_message(
                "❌ Você não pode editar esta ficha.",
                ephemeral=True
            )
            return

        try:
            novo_valor = int(
                self.valor.value
            )

        except ValueError:

            await interaction.response.send_message(
                "❌ Informe um número inteiro.",
                ephemeral=True
            )
            return

        if novo_valor < 0:

            await interaction.response.send_message(
                "❌ O valor não pode ser negativo.",
                ephemeral=True
            )
            return

        if (
            self.atributo
            not in ATRIBUTOS
        ):

            await interaction.response.send_message(
                "❌ Atributo inválido.",
                ephemeral=True
            )
            return

        anterior = self.ficha.get(
            self.atributo,
            0
        )

        cursor.execute(
            f"""
            UPDATE fichas
            SET {self.atributo} = ?
            WHERE id = ?
            """,
            (
                novo_valor,
                self.ficha["id"]
            )
        )

        db.commit()

        self.ficha[
            self.atributo
        ] = novo_valor

        await interaction.response.send_message(
            f"{self.emoji} **{self.nome}** atualizado.\n"
            f"**{anterior} → {novo_valor}**",
            ephemeral=True
        )


# ============================================================
# MENU — ATRIBUTOS
# ============================================================

class MenuAtributos(
    discord.ui.Select
):

    def __init__(
        self,
        ficha
    ):

        self.ficha = ficha

        opcoes = []

        nomes_completos = {
            "forca": "Força",
            "destreza": "Destreza",
            "vigor": "Vigor",
            "inteligencia": "Inteligência",
            "carisma": "Carisma",
            "raciocinio": "Raciocínio"
        }

        for chave in ATRIBUTOS:

            emoji, _ = ATRIBUTOS[
                chave
            ]

            opcoes.append(
                discord.SelectOption(
                    label=nomes_completos[
                        chave
                    ],
                    emoji=emoji,
                    value=chave,
                    description=(
                        f"Atual: "
                        f"{ficha.get(chave, 0)}"
                    )
                )
            )

        super().__init__(
            placeholder="📊 Escolha o atributo...",
            min_values=1,
            max_values=1,
            options=opcoes
        )


    async def callback(
        self,
        interaction: discord.Interaction
    ):

        if not pode_alterar_ficha(
            interaction,
            self.ficha
        ):
            await interaction.response.send_message(
                "❌ Você não pode editar esta ficha.",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(
            ModalEditarAtributo(
                self.ficha,
                self.values[0]
            )
        )


class MenuAtributosView(
    discord.ui.View
):

    def __init__(
        self,
        ficha
    ):

        super().__init__(
            timeout=180
        )

        self.add_item(
            MenuAtributos(
                ficha
            )
        )


# ============================================================
# MODAL — EDITAR PERÍCIA
# ============================================================

class ModalEditarPericia(
    discord.ui.Modal
):

    def __init__(
        self,
        ficha,
        pericia
    ):

        emoji, nome = PERICIAS[
            pericia
        ]

        super().__init__(
            title=f"Editar {nome}"[:45]
        )

        self.ficha = ficha
        self.pericia = pericia
        self.emoji = emoji
        self.nome = nome

        self.valor = discord.ui.TextInput(
            label="Novo valor",
            default=str(
                ficha.get(
                    pericia,
                    0
                )
            ),
            placeholder="Digite um número inteiro",
            required=True,
            max_length=5
        )

        self.add_item(
            self.valor
        )


    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        if not pode_alterar_ficha(
            interaction,
            self.ficha
        ):

            await interaction.response.send_message(
                "❌ Você não pode editar esta ficha.",
                ephemeral=True
            )
            return

        try:
            novo_valor = int(
                self.valor.value
            )

        except ValueError:

            await interaction.response.send_message(
                "❌ Informe um número inteiro.",
                ephemeral=True
            )
            return

        if novo_valor < 0:

            await interaction.response.send_message(
                "❌ O valor não pode ser negativo.",
                ephemeral=True
            )
            return

        if (
            self.pericia
            not in PERICIAS
        ):

            await interaction.response.send_message(
                "❌ Perícia inválida.",
                ephemeral=True
            )
            return

        anterior = self.ficha.get(
            self.pericia,
            0
        )

        cursor.execute(
            f"""
            UPDATE fichas
            SET {self.pericia} = ?
            WHERE id = ?
            """,
            (
                novo_valor,
                self.ficha["id"]
            )
        )

        db.commit()

        self.ficha[
            self.pericia
        ] = novo_valor

        await interaction.response.send_message(
            f"{self.emoji} **{self.nome}** atualizada.\n"
            f"**{anterior} → {novo_valor}**",
            ephemeral=True
        )


# ============================================================
# MENU — PERÍCIAS
# ============================================================

class MenuPericias(
    discord.ui.Select
):

    def __init__(
        self,
        ficha
    ):

        self.ficha = ficha

        opcoes = []

        for chave in ORDEM_PERICIAS:

            emoji, nome = PERICIAS[
                chave
            ]

            opcoes.append(
                discord.SelectOption(
                    label=nome[:100],
                    emoji=emoji,
                    value=chave,
                    description=(
                        f"Atual: "
                        f"{ficha.get(chave, 0)}"
                    )
                )
            )

        super().__init__(
            placeholder="📚 Escolha a perícia...",
            min_values=1,
            max_values=1,
            options=opcoes
        )


    async def callback(
        self,
        interaction: discord.Interaction
    ):

        if not pode_alterar_ficha(
            interaction,
            self.ficha
        ):

            await interaction.response.send_message(
                "❌ Você não pode editar esta ficha.",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(
            ModalEditarPericia(
                self.ficha,
                self.values[0]
            )
        )


class MenuPericiasView(
    discord.ui.View
):

    def __init__(
        self,
        ficha
    ):

        super().__init__(
            timeout=180
        )

        self.add_item(
            MenuPericias(
                ficha
            )
        )


# ============================================================
# MODAL — EDITAR HP / MANA
# ============================================================

class ModalEditarRecursos(
    discord.ui.Modal
):

    def __init__(
        self,
        ficha
    ):

        super().__init__(
            title="Editar HP e Mana"
        )

        self.ficha = ficha

        self.hp_atual = discord.ui.TextInput(
            label="HP atual",
            default=str(
                ficha.get(
                    "hp_atual",
                    0
                )
            ),
            required=True,
            max_length=7
        )

        self.hp_max = discord.ui.TextInput(
            label="HP máximo",
            default=str(
                ficha.get(
                    "hp_max",
                    0
                )
            ),
            required=True,
            max_length=7
        )

        self.mana_atual = discord.ui.TextInput(
            label="Mana atual",
            default=str(
                ficha.get(
                    "mana_atual",
                    0
                )
            ),
            required=True,
            max_length=7
        )

        self.mana_max = discord.ui.TextInput(
            label="Mana máxima",
            default=str(
                ficha.get(
                    "mana_max",
                    0
                )
            ),
            required=True,
            max_length=7
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

        if not pode_alterar_ficha(
            interaction,
            self.ficha
        ):

            await interaction.response.send_message(
                "❌ Você não pode editar esta ficha.",
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
                "❌ Todos os valores precisam ser números inteiros.",
                ephemeral=True
            )
            return

        if hp_max <= 0:

            await interaction.response.send_message(
                "❌ O HP máximo precisa ser maior que 0.",
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
            hp_atual < 0
            or hp_atual > hp_max
        ):

            await interaction.response.send_message(
                "❌ O HP atual precisa estar entre 0 e o HP máximo.",
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

        cursor.execute("""
            UPDATE fichas
            SET hp_atual = ?,
                hp_max = ?,
                mana_atual = ?,
                mana_max = ?
            WHERE id = ?
        """, (
            hp_atual,
            hp_max,
            mana_atual,
            mana_max,
            self.ficha["id"]
        ))

        db.commit()

        self.ficha[
            "hp_atual"
        ] = hp_atual

        self.ficha[
            "hp_max"
        ] = hp_max

        self.ficha[
            "mana_atual"
        ] = mana_atual

        self.ficha[
            "mana_max"
        ] = mana_max

        await interaction.response.send_message(
            "❤️🔵 **HP e Mana atualizados!**\n\n"
            f"❤️ HP: **{hp_atual}/{hp_max}**\n"
            f"🔵 Mana: **{mana_atual}/{mana_max}**",
            ephemeral=True
        )


# ============================================================
# MODAL — EDITAR XP
# ============================================================

class ModalEditarXP(
    discord.ui.Modal
):

    def __init__(
        self,
        ficha
    ):

        super().__init__(
            title="Editar XP"
        )

        self.ficha = ficha

        self.xp = discord.ui.TextInput(
            label="XP atual",
            default=str(
                ficha.get(
                    "xp",
                    0
                )
            ),
            placeholder="Digite o novo XP",
            required=True,
            max_length=10
        )

        self.add_item(
            self.xp
        )


    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        if not pode_alterar_ficha(
            interaction,
            self.ficha
        ):

            await interaction.response.send_message(
                "❌ Você não pode editar esta ficha.",
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

        anterior = self.ficha.get(
            "xp",
            0
        )

        cursor.execute("""
            UPDATE fichas
            SET xp = ?
            WHERE id = ?
        """, (
            novo_xp,
            self.ficha["id"]
        ))

        db.commit()

        self.ficha[
            "xp"
        ] = novo_xp

        await interaction.response.send_message(
            "✨ **XP atualizado!**\n"
            f"**{anterior} → {novo_xp}**",
            ephemeral=True
        )


# ============================================================
# MENU PRINCIPAL DE EDIÇÃO
# ============================================================

class MenuEdicao(
    discord.ui.Select
):

    def __init__(
        self,
        ficha,
        jogador=None
    ):

        self.ficha = ficha
        self.jogador = jogador

        opcoes = [
            discord.SelectOption(
                label="Atributos",
                description="Editar atributos.",
                emoji="📊",
                value="atributos"
            ),
            discord.SelectOption(
                label="Perícias",
                description="Editar perícias.",
                emoji="📚",
                value="pericias"
            ),
            discord.SelectOption(
                label="HP / Mana",
                description="Editar HP e Mana.",
                emoji="❤️",
                value="recursos"
            ),
            discord.SelectOption(
                label="XP",
                description="Editar XP.",
                emoji="✨",
                value="xp"
            )
        ]

        super().__init__(
            placeholder="✏️ Escolha o que deseja editar...",
            min_values=1,
            max_values=1,
            options=opcoes
        )


    async def callback(
        self,
        interaction: discord.Interaction
    ):

        if not pode_alterar_ficha(
            interaction,
            self.ficha
        ):

            await interaction.response.send_message(
                "❌ Você não pode editar esta ficha.",
                ephemeral=True
            )
            return

        escolha = self.values[0]

        # ====================================================
        # ATRIBUTOS
        # ====================================================

        if escolha == "atributos":

            await interaction.response.send_message(
                "📊 **Editar atributos**\n\n"
                "Escolha o atributo:",
                view=MenuAtributosView(
                    self.ficha
                ),
                ephemeral=True
            )

            return

        # ====================================================
        # PERÍCIAS
        # ====================================================

        if escolha == "pericias":

            await interaction.response.send_message(
                "📚 **Editar perícias**\n\n"
                "Escolha a perícia:",
                view=MenuPericiasView(
                    self.ficha
                ),
                ephemeral=True
            )

            return

        # ====================================================
        # HP / MANA
        # ====================================================

        if escolha == "recursos":

            await interaction.response.send_modal(
                ModalEditarRecursos(
                    self.ficha
                )
            )

            return

        # ====================================================
        # XP
        # ====================================================

        if escolha == "xp":

            await interaction.response.send_modal(
                ModalEditarXP(
                    self.ficha
                )
            )

            return


# ============================================================
# VIEW DO MENU DE EDIÇÃO
# ============================================================

class MenuEdicaoView(
    discord.ui.View
):

    def __init__(
        self,
        ficha,
        jogador=None
    ):

        super().__init__(
            timeout=180
        )

        self.add_item(
            MenuEdicao(
                ficha,
                jogador
            )
        )


# ============================================================
# VIEW DA FICHA
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

    def atualizar_botoes(self):

        self.status_button.disabled = (
            self.pagina == 1
        )

        self.pericias_button.disabled = (
            self.pagina == 2
        )


    # ========================================================
    # BOTÃO STATUS
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
    # BOTÃO PERÍCIAS
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
    # BOTÃO EDITAR
    # ========================================================

    @discord.ui.button(
        label="✏️ Editar",
        style=discord.ButtonStyle.primary,
        row=1
    )
    async def editar_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if not pode_alterar_ficha(
            interaction,
            self.ficha
        ):

            await interaction.response.send_message(
                "❌ Você não tem permissão para editar esta ficha.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "✏️ **Menu de edição**\n\n"
            "Escolha abaixo o que deseja editar:",
            view=MenuEdicaoView(
                self.ficha,
                self.jogador
            ),
            ephemeral=True
        )
