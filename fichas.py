import discord

from database import cursor, db

from config import (
    ATRIBUTOS,
    PERICIAS,
    ORDEM_PERICIAS
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
    """, (ficha_id,))

    return cursor.fetchone()


# ============================================================
# TRANSFORMAR FICHA
# ============================================================

def transformar_ficha(dados):

    if dados is None:
        return None

    # IMPORTANTE:
    # Esta ordem deve continuar exatamente igual à tabela fichas.

    colunas = [
        "id",
        "channel_id",
        "dono_id",
        "mestre_id",
        "tipo",
        "nome",

        "hp_atual",
        "hp_max",

        "mana_atual",
        "mana_max",

        "xp",

        "forca",
        "destreza",
        "vigor",
        "inteligencia",
        "carisma",
        "raciocinio",

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

        "aleatorio"
    ]

    ficha = {}

    for indice, coluna in enumerate(colunas):

        if indice < len(dados):
            ficha[coluna] = dados[indice]

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
    """, (ficha_id,))

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
# FORMATAR PERÍCIAS
# ============================================================

def formatar_pericias(ficha):

    linhas = []

    for chave in ORDEM_PERICIAS:

        emoji, nome = PERICIAS[chave]

        # Remove aspas triplas caso tenham sido inseridas
        # acidentalmente no nome.
        nome = nome.replace("'''", "").strip()

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

def criar_pagina_status(ficha, jogador=None):

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
    # ATRIBUTOS
    #
    # A ordem é declarada manualmente de propósito.
    # Assim For/Des, Vig/Int e Car/Rac nunca são trocados.
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

def criar_pagina_pericias(ficha, jogador=None):

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

    texto_pericias = "\n".join(
        linhas
    )

    # ========================================================
    # PERÍCIAS EM UMA COLUNA
    # ========================================================

    embed.add_field(
        name="📚 PERÍCIAS",
        value=texto_pericias or "Nenhuma",
        inline=False
    )

    # ========================================================
    # RODAPÉ
    # ========================================================

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
# VERIFICAR SE PODE ALTERAR FICHA
# ============================================================

def pode_alterar_ficha(
    interaction,
    ficha
):

    if ficha is None:
        return False

    # ========================================================
    # ADMINISTRADOR
    # ========================================================

    if (
        interaction.guild
        and interaction.user.guild_permissions.administrator
    ):
        return True

    # ========================================================
    # DONO DA FICHA
    # ========================================================

    if (
        ficha.get("dono_id")
        == interaction.user.id
    ):
        return True

    # ========================================================
    # MESTRE
    # ========================================================

    mestre_id = ficha.get(
        "mestre_id"
    )

    if (
        mestre_id is not None
        and mestre_id
        == interaction.user.id
    ):
        return True

    return False


# ============================================================
# MENU DE EDIÇÃO — ETAPA 1.2
# ============================================================

class MenuEdicao(discord.ui.Select):

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
                description="Editar atributos da ficha.",
                emoji="📊",
                value="atributos"
            ),
            discord.SelectOption(
                label="Perícias",
                description="Editar perícias da ficha.",
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
                description="Editar experiência.",
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

        # Confere novamente a permissão.
        if not pode_alterar_ficha(
            interaction,
            self.ficha
        ):

            await interaction.response.send_message(
                "❌ Você não tem permissão para editar esta ficha.",
                ephemeral=True
            )

            return

        escolha = self.values[0]

        nomes = {
            "atributos": "📊 Atributos",
            "pericias": "📚 Perícias",
            "recursos": "❤️ HP / Mana",
            "xp": "✨ XP"
        }

        nome_escolhido = nomes.get(
            escolha,
            "Opção"
        )

        await interaction.response.send_message(
            f"✏️ Você selecionou **{nome_escolhido}**.\n\n"
            "Essa opção será ligada ao editor "
            "nas próximas etapas.",
            ephemeral=True
        )


# ============================================================
# VIEW DO MENU DE EDIÇÃO
# ============================================================

class MenuEdicaoView(discord.ui.View):

    def __init__(
        self,
        ficha,
        jogador=None
    ):

        super().__init__(
            timeout=120
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

class FichaView(discord.ui.View):

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
