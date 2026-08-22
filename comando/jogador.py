import discord

from discord import app_commands

from database import (
    db,
    cursor,
    garantir_mesa,
    obter_mestre,
    buscar_ficha_jogador,
    registrar_historico,
)

from fichas import (
    transformar_ficha,
    criar_pagina_status,
    FichaView,
    pode_alterar_ficha,
    estado_hp,
    estado_mana,
)

from config import (
    ATRIBUTOS,
    PERICIAS,
    ORDEM_PERICIAS,
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

GRUPOS_ATRIBUTOS_JOGADOR = [
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

GRUPOS_PERICIAS_JOGADOR = [
    ORDEM_PERICIAS[0:5],
    ORDEM_PERICIAS[5:10],
    ORDEM_PERICIAS[10:15],
    ORDEM_PERICIAS[15:20],
    ORDEM_PERICIAS[20:23],
]


# ============================================================
# ADMIN
# ============================================================

def eh_admin(
    interaction
):

    if interaction.guild is None:
        return False

    return (
        interaction.user
        .guild_permissions
        .administrator
    )


# ============================================================
# MESTRE
# ============================================================

def eh_mestre(
    interaction
):

    if interaction.channel is None:
        return False

    return (
        obter_mestre(
            interaction.channel.id
        )
        == interaction.user.id
    )


# ============================================================
# BUSCAR FICHA PELO ID E CANAL
# ============================================================

def buscar_ficha_por_id(
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

    return cursor.fetchone()


# ============================================================
# SESSÃO DE CRIAÇÃO DO JOGADOR
# ============================================================

class SessaoCriacaoJogador:

    def __init__(
        self,
        channel_id,
        usuario_id
    ):

        self.channel_id = channel_id
        self.usuario_id = usuario_id

        self.nome = None
        self.hp = None
        self.mana = None

        self.atributos = {}
        self.pericias = {}


# ============================================================
# VIEW BASE DA CRIAÇÃO
# ============================================================

class ViewSessaoJogador(
    discord.ui.View
):

    def __init__(
        self,
        sessao,
        timeout=300
    ):

        super().__init__(
            timeout=timeout
        )

        self.sessao = sessao


    async def interaction_check(
        self,
        interaction: discord.Interaction
    ):

        if (
            interaction.user.id
            != self.sessao.usuario_id
        ):

            await interaction.response.send_message(
                "❌ Somente o jogador que iniciou "
                "a criação da ficha pode usar "
                "estes controles.",
                ephemeral=True
            )

            return False

        return True


# ============================================================
# FINALIZAR CRIAÇÃO DA FICHA
# ============================================================

async def finalizar_criacao_jogador(
    interaction,
    sessao
):

    # ========================================================
    # VERIFICAR SE JÁ EXISTE FICHA
    # ========================================================

    existente = buscar_ficha_jogador(
        sessao.channel_id,
        sessao.usuario_id
    )

    if existente is not None:

        await interaction.response.send_message(
            "❌ Você já possui uma ficha neste canal.",
            ephemeral=True
        )

        return

    # ========================================================
    # VALIDAR DADOS BÁSICOS
    # ========================================================

    if not sessao.nome:

        await interaction.response.send_message(
            "❌ O personagem está sem nome.",
            ephemeral=True
        )

        return

    if (
        sessao.hp is None
        or sessao.hp <= 0
    ):

        await interaction.response.send_message(
            "❌ O HP da ficha é inválido.",
            ephemeral=True
        )

        return

    if (
        sessao.mana is None
        or sessao.mana < 0
    ):

        await interaction.response.send_message(
            "❌ A Mana da ficha é inválida.",
            ephemeral=True
        )

        return

    # ========================================================
    # VALIDAR ATRIBUTOS
    # ========================================================

    for chave in ATRIBUTOS:

        if chave not in sessao.atributos:

            await interaction.response.send_message(
                f"❌ O atributo `{chave}` "
                f"não foi preenchido.",
                ephemeral=True
            )

            return

        valor = sessao.atributos[
            chave
        ]

        if valor < 0:

            await interaction.response.send_message(
                f"❌ O atributo `{chave}` "
                f"não pode ser negativo.",
                ephemeral=True
            )

            return

    # ========================================================
    # VALIDAR PERÍCIAS
    # ========================================================

    for chave in ORDEM_PERICIAS:

        if chave not in sessao.pericias:

            await interaction.response.send_message(
                f"❌ A perícia `{chave}` "
                f"não foi preenchida.",
                ephemeral=True
            )

            return

        valor = sessao.pericias[
            chave
        ]

        if (
            valor < 0
            or valor > 5
        ):

            await interaction.response.send_message(
                f"❌ A perícia `{chave}` "
                f"precisa estar entre 0 e 5.",
                ephemeral=True
            )

            return

    # ========================================================
    # PREPARAR COLUNAS
    # ========================================================

    colunas = (
        list(
            ATRIBUTOS.keys()
        )
        +
        ORDEM_PERICIAS
    )

    valores = (
        [
            sessao.atributos[
                chave
            ]
            for chave in ATRIBUTOS
        ]
        +
        [
            sessao.pericias[
                chave
            ]
            for chave in ORDEM_PERICIAS
        ]
    )

    placeholders = ", ".join(
        ["?"] * len(valores)
    )

    nome = sessao.nome[:50]

    # ========================================================
    # INSERIR FICHA
    # ========================================================

    cursor.execute(
        f"""
        INSERT INTO fichas (
            channel_id,
            dono_id,
            mestre_id,
            tipo,
            nome,

            hp_atual,
            hp_max,

            mana_atual,
            mana_max,

            xp,

            {", ".join(colunas)},

            aleatorio
        )
        VALUES (
            ?, ?, NULL, 'jogador', ?,

            ?, ?,

            ?, ?,

            0,

            {placeholders},

            0
        )
        """,
        [
            sessao.channel_id,
            sessao.usuario_id,
            nome,

            sessao.hp,
            sessao.hp,

            sessao.mana,
            sessao.mana
        ]
        + valores
    )

    db.commit()

    ficha_id = (
        cursor.lastrowid
    )

    # ========================================================
    # CALCULAR RC
    # ========================================================

    rc = (
        sessao.pericias[
            "esquiva"
        ]
        +
        sessao.atributos[
            "destreza"
        ]
        +
        5
    )

    # ========================================================
    # MENSAGEM FINAL
    # ========================================================

    await interaction.response.send_message(
        f"📜 Ficha de **{nome}** "
        f"criada com sucesso!\n\n"
        f"❤️ HP: **{sessao.hp}/{sessao.hp}**\n"
        f"🔵 Mana: **{sessao.mana}/{sessao.mana}**\n"
        f"✨ XP: **0**\n"
        f"⚡ RC: **{rc}**\n\n"
        f"⚔️ **6 atributos preenchidos**\n"
        f"📚 **23 perícias preenchidas**\n\n"
        f"🆔 Ficha: **#{ficha_id}**",
        ephemeral=True
    )


# ============================================================
# MODAL DOS DADOS BÁSICOS
# ============================================================

class ModalDadosJogador(
    discord.ui.Modal,
    title="Criar ficha"
):

    def __init__(
        self,
        sessao
    ):

        super().__init__()

        self.sessao = sessao

        self.nome = discord.ui.TextInput(
            label="Nome do personagem",
            placeholder="Ex.: Arthur",
            required=True,
            max_length=50
        )

        self.hp = discord.ui.TextInput(
            label="HP máximo",
            placeholder="Ex.: 20",
            required=True,
            max_length=7
        )

        self.mana = discord.ui.TextInput(
            label="Mana máxima",
            placeholder="Ex.: 10",
            required=True,
            max_length=7
        )

        self.add_item(
            self.nome
        )

        self.add_item(
            self.hp
        )

        self.add_item(
            self.mana
        )


    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        if (
            interaction.user.id
            != self.sessao.usuario_id
        ):

            await interaction.response.send_message(
                "❌ Você não pode preencher "
                "este formulário.",
                ephemeral=True
            )

            return

        try:

            hp = int(
                self.hp.value
            )

            mana = int(
                self.mana.value
            )

        except ValueError:

            await interaction.response.send_message(
                "❌ HP e Mana precisam ser "
                "números inteiros.",
                ephemeral=True
            )

            return

        if hp <= 0:

            await interaction.response.send_message(
                "❌ O HP precisa ser maior que 0.",
                ephemeral=True
            )

            return

        if mana < 0:

            await interaction.response.send_message(
                "❌ A Mana não pode ser negativa.",
                ephemeral=True
            )

            return

        nome = (
            self.nome.value
            .strip()
        )

        if not nome:

            await interaction.response.send_message(
                "❌ Informe um nome válido.",
                ephemeral=True
            )

            return

        self.sessao.nome = (
            nome[:50]
        )

        self.sessao.hp = hp
        self.sessao.mana = mana

        await interaction.response.send_message(
            f"✅ Dados básicos salvos.\n\n"
            f"👤 **{self.sessao.nome}**\n"
            f"❤️ HP: **{hp}**\n"
            f"🔵 Mana: **{mana}**\n\n"
            f"⚔️ Agora vamos preencher "
            f"os **atributos**.",
            view=ViewIniciarAtributosJogador(
                self.sessao
            ),
            ephemeral=True
        )


# ============================================================
# INICIAR ATRIBUTOS
# ============================================================

class ViewIniciarAtributosJogador(
    ViewSessaoJogador
):

    @discord.ui.button(
        label="⚔️ Preencher atributos",
        style=discord.ButtonStyle.primary
    )
    async def continuar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.send_modal(
            ModalAtributosJogador(
                self.sessao,
                grupo=0
            )
        )


# ============================================================
# MODAL DE ATRIBUTOS
# ============================================================

class ModalAtributosJogador(
    discord.ui.Modal
):

    def __init__(
        self,
        sessao,
        grupo
    ):

        self.sessao = sessao
        self.grupo = grupo

        campos = (
            GRUPOS_ATRIBUTOS_JOGADOR[
                grupo
            ]
        )

        super().__init__(
            title=(
                f"Atributos "
                f"{grupo + 1}/"
                f"{len(GRUPOS_ATRIBUTOS_JOGADOR)}"
            )
        )

        self.inputs = {}

        for chave in campos:

            campo = discord.ui.TextInput(
                label=NOMES_ATRIBUTOS[
                    chave
                ],
                placeholder="Valor",
                default=str(
                    sessao.atributos.get(
                        chave,
                        0
                    )
                ),
                required=True,
                max_length=5
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

        if (
            interaction.user.id
            != self.sessao.usuario_id
        ):

            await interaction.response.send_message(
                "❌ Você não pode preencher "
                "este formulário.",
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

        self.sessao.atributos.update(
            valores
        )

        proximo = (
            self.grupo + 1
        )

        if (
            proximo
            < len(
                GRUPOS_ATRIBUTOS_JOGADOR
            )
        ):

            await interaction.response.send_message(
                f"✅ Atributos "
                f"{self.grupo + 1}/"
                f"{len(GRUPOS_ATRIBUTOS_JOGADOR)} "
                f"salvos.\n\n"
                f"Clique abaixo para continuar.",
                view=ViewContinuarAtributosJogador(
                    self.sessao,
                    proximo
                ),
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "✅ Todos os atributos foram salvos.\n\n"
            "📚 Agora vamos preencher "
            "as **perícias**.",
            view=ViewIniciarPericiasJogador(
                self.sessao
            ),
            ephemeral=True
        )


# ============================================================
# CONTINUAR ATRIBUTOS
# ============================================================

class ViewContinuarAtributosJogador(
    ViewSessaoJogador
):

    def __init__(
        self,
        sessao,
        grupo
    ):

        super().__init__(
            sessao
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

        await interaction.response.send_modal(
            ModalAtributosJogador(
                self.sessao,
                self.grupo
            )
        )


# ============================================================
# INICIAR PERÍCIAS
# ============================================================

class ViewIniciarPericiasJogador(
    ViewSessaoJogador
):

    @discord.ui.button(
        label="📚 Preencher perícias",
        style=discord.ButtonStyle.primary
    )
    async def continuar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.send_modal(
            ModalPericiasJogador(
                self.sessao,
                grupo=0
            )
        )


# ============================================================
# MODAL DE PERÍCIAS
# ============================================================

class ModalPericiasJogador(
    discord.ui.Modal
):

    def __init__(
        self,
        sessao,
        grupo
    ):

        self.sessao = sessao
        self.grupo = grupo

        campos = (
            GRUPOS_PERICIAS_JOGADOR[
                grupo
            ]
        )

        super().__init__(
            title=(
                f"Perícias "
                f"{grupo + 1}/"
                f"{len(GRUPOS_PERICIAS_JOGADOR)}"
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
                    sessao.pericias.get(
                        chave,
                        0
                    )
                ),
                required=True,
                max_length=1
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

        if (
            interaction.user.id
            != self.sessao.usuario_id
        ):

            await interaction.response.send_message(
                "❌ Você não pode preencher "
                "este formulário.",
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

        self.sessao.pericias.update(
            valores
        )

        proximo = (
            self.grupo + 1
        )

        if (
            proximo
            < len(
                GRUPOS_PERICIAS_JOGADOR
            )
        ):

            await interaction.response.send_message(
                f"✅ Perícias "
                f"{self.grupo + 1}/"
                f"{len(GRUPOS_PERICIAS_JOGADOR)} "
                f"salvas.\n\n"
                f"Clique abaixo para continuar.",
                view=ViewContinuarPericiasJogador(
                    self.sessao,
                    proximo
                ),
                ephemeral=True
            )

            return

        await finalizar_criacao_jogador(
            interaction,
            self.sessao
        )


# ============================================================
# CONTINUAR PERÍCIAS
# ============================================================

class ViewContinuarPericiasJogador(
    ViewSessaoJogador
):

    def __init__(
        self,
        sessao,
        grupo
    ):

        super().__init__(
            sessao
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

        await interaction.response.send_modal(
            ModalPericiasJogador(
                self.sessao,
                self.grupo
            )
        )


# ============================================================
# REGISTRAR COMANDOS
# ============================================================

def registrar_comandos_jogador(
    bot
):

    # ========================================================
    # CRIAR FICHA
    # ========================================================

    @bot.tree.command(
        name="criarficha",
        description="Inicia a criação guiada da sua ficha."
    )
    async def criarficha(
        interaction: discord.Interaction
    ):

        garantir_mesa(
            interaction.channel.id
        )

        existente = buscar_ficha_jogador(
            interaction.channel.id,
            interaction.user.id
        )

        if existente is not None:

            await interaction.response.send_message(
                "❌ Você já possui uma ficha neste canal.",
                ephemeral=True
            )

            return

        sessao = SessaoCriacaoJogador(
            interaction.channel.id,
            interaction.user.id
        )

        await interaction.response.send_modal(
            ModalDadosJogador(
                sessao
            )
        )


    # ========================================================
    # MOSTRAR PRÓPRIA FICHA
    # ========================================================

    @bot.tree.command(
        name="ficha",
        description="Mostra sua ficha neste canal."
    )
    async def ficha(
        interaction: discord.Interaction
    ):

        dados = buscar_ficha_jogador(
            interaction.channel.id,
            interaction.user.id
        )

        if dados is None:

            await interaction.response.send_message(
                "❌ Você não possui uma ficha neste canal.",
                ephemeral=True
            )

            return

        f = transformar_ficha(
            dados
        )

        await interaction.response.send_message(
            embed=criar_pagina_status(
                f,
                interaction.user
            ),
            view=FichaView(
                f,
                interaction.user
            ),
            ephemeral=True
        )


    # ========================================================
    # VER FICHA
    # ========================================================

    @bot.tree.command(
        name="verficha",
        description="Visualiza a ficha de outro jogador."
    )
    @app_commands.describe(
        jogador="Jogador cuja ficha deseja visualizar"
    )
    async def verficha(
        interaction: discord.Interaction,
        jogador: discord.Member
    ):

        dados = buscar_ficha_jogador(
            interaction.channel.id,
            jogador.id
        )

        if dados is None:

            await interaction.response.send_message(
                f"❌ **{jogador.display_name}** "
                f"não possui uma ficha.",
                ephemeral=True
            )

            return

        f = transformar_ficha(
            dados
        )

        await interaction.response.send_message(
            embed=criar_pagina_status(
                f,
                jogador
            ),
            view=FichaView(
                f,
                jogador
            )
        )


    # ========================================================
    # ATRIBUTO
    # ========================================================

    @bot.tree.command(
        name="atributo",
        description="Define ou altera um atributo da sua ficha."
    )
    @app_commands.describe(
        atributo="Atributo",
        valor="Novo valor"
    )
    @app_commands.choices(
        atributo=[
            app_commands.Choice(
                name="Força",
                value="forca"
            ),
            app_commands.Choice(
                name="Destreza",
                value="destreza"
            ),
            app_commands.Choice(
                name="Vigor",
                value="vigor"
            ),
            app_commands.Choice(
                name="Inteligência",
                value="inteligencia"
            ),
            app_commands.Choice(
                name="Carisma",
                value="carisma"
            ),
            app_commands.Choice(
                name="Raciocínio",
                value="raciocinio"
            ),
        ]
    )
    async def atributo(
        interaction: discord.Interaction,
        atributo: app_commands.Choice[str],
        valor: int
    ):

        dados = buscar_ficha_jogador(
            interaction.channel.id,
            interaction.user.id
        )

        if dados is None:

            await interaction.response.send_message(
                "❌ Você não possui uma ficha.",
                ephemeral=True
            )

            return

        if valor < 0:

            await interaction.response.send_message(
                "❌ O valor não pode ser negativo.",
                ephemeral=True
            )

            return

        f = transformar_ficha(
            dados
        )

        valor_anterior = f[
            atributo.value
        ]

        cursor.execute(
            f"""
            UPDATE fichas
            SET {atributo.value} = ?
            WHERE id = ?
            """,
            (
                valor,
                f["id"]
            )
        )

        db.commit()

        if valor_anterior != valor:

            registrar_historico(
                f["channel_id"],
                f["id"],
                f["nome"],
                f["tipo"],
                interaction.user.id,
                "atributo",
                campo=atributo.value,
                valor_anterior=valor_anterior,
                valor_novo=valor,
                descricao=(
                    "⚔️ Atributo alterado."
                )
            )

        emoji, nome = ATRIBUTOS[
            atributo.value
        ]

        await interaction.response.send_message(
            f"{emoji} **{nome}** "
            f"alterado para **{valor}**!"
        )


    # ========================================================
    # PERÍCIA
    # ========================================================

    @bot.tree.command(
        name="pericia",
        description="Define ou altera uma perícia da sua ficha."
    )
    @app_commands.describe(
        pericia="Perícia",
        valor="Novo valor entre 0 e 5"
    )
    @app_commands.choices(
        pericia=[
            app_commands.Choice(
                name="Acadêmicos",
                value="academicos"
            ),
            app_commands.Choice(
                name="Idiomas",
                value="idiomas"
            ),
            app_commands.Choice(
                name="Ofícios",
                value="oficios"
            ),
            app_commands.Choice(
                name="Armas Brancas",
                value="armas_brancas"
            ),
            app_commands.Choice(
                name="Intimidação",
                value="intimidacao"
            ),
            app_commands.Choice(
                name="Ocultismo",
                value="ocultismo"
            ),
            app_commands.Choice(
                name="Briga",
                value="briga"
            ),
            app_commands.Choice(
                name="Investigação",
                value="investigacao"
            ),
            app_commands.Choice(
                name="Persuasão",
                value="persuasao"
            ),
            app_commands.Choice(
                name="Ciências",
                value="ciencias"
            ),
            app_commands.Choice(
                name="Lábia",
                value="labia"
            ),
            app_commands.Choice(
                name="Prontidão",
                value="prontidao"
            ),
            app_commands.Choice(
                name="Conhecimentos Gerais",
                value="conhecimentos_gerais"
            ),
            app_commands.Choice(
                name="Liderança",
                value="lideranca"
            ),
            app_commands.Choice(
                name="Sobrevivência",
                value="sobrevivencia"
            ),
            app_commands.Choice(
                name="Condução",
                value="conducao"
            ),
            app_commands.Choice(
                name="Manha",
                value="manha"
            ),
            app_commands.Choice(
                name="Tecnologia",
                value="tecnologia"
            ),
            app_commands.Choice(
                name="Esportes",
                value="esportes"
            ),
            app_commands.Choice(
                name="Medicina",
                value="medicina"
            ),
            app_commands.Choice(
                name="Mira",
                value="mira"
            ),
            app_commands.Choice(
                name="Esquiva",
                value="esquiva"
            ),
            app_commands.Choice(
                name="Furtividade",
                value="furtividade"
            ),
        ]
    )
    async def pericia(
        interaction: discord.Interaction,
        pericia: app_commands.Choice[str],
        valor: int
    ):

        dados = buscar_ficha_jogador(
            interaction.channel.id,
            interaction.user.id
        )

        if dados is None:

            await interaction.response.send_message(
                "❌ Você não possui uma ficha.",
                ephemeral=True
            )

            return

        if (
            valor < 0
            or valor > 5
        ):

            await interaction.response.send_message(
                "❌ O valor da perícia precisa "
                "estar entre **0 e 5**.",
                ephemeral=True
            )

            return

        f = transformar_ficha(
            dados
        )

        valor_anterior = f[
            pericia.value
        ]

        cursor.execute(
            f"""
            UPDATE fichas
            SET {pericia.value} = ?
            WHERE id = ?
            """,
            (
                valor,
                f["id"]
            )
        )

        db.commit()

        if valor_anterior != valor:

            registrar_historico(
                f["channel_id"],
                f["id"],
                f["nome"],
                f["tipo"],
                interaction.user.id,
                "pericia",
                campo=pericia.value,
                valor_anterior=valor_anterior,
                valor_novo=valor,
                descricao=(
                    "📚 Perícia alterada."
                )
            )

        emoji, nome = PERICIAS[
            pericia.value
        ]

        await interaction.response.send_message(
            f"{emoji} **{nome}** "
            f"alterada para **{valor}**!"
        )


    # ========================================================
    # ALTERAR FICHA
    # ========================================================

    @bot.tree.command(
        name="alterarficha",
        description="Altera HP e Mana máximos de uma ficha."
    )
    @app_commands.describe(
        jogador="Jogador",
        hp="Novo HP máximo",
        mana="Nova Mana máxima"
    )
    async def alterarficha(
        interaction: discord.Interaction,
        jogador: discord.Member,
        hp: int,
        mana: int
    ):

        dados = buscar_ficha_jogador(
            interaction.channel.id,
            jogador.id
        )

        if dados is None:

            await interaction.response.send_message(
                "❌ Ficha não encontrada.",
                ephemeral=True
            )

            return

        f = transformar_ficha(
            dados
        )

        if not pode_alterar_ficha(
            interaction,
            f
        ):

            await interaction.response.send_message(
                "❌ Você não possui permissão "
                "para alterar esta ficha.",
                ephemeral=True
            )

            return

        if hp <= 0:

            await interaction.response.send_message(
                "❌ O HP precisa ser maior que 0.",
                ephemeral=True
            )

            return

        if mana < 0:

            await interaction.response.send_message(
                "❌ A Mana não pode ser negativa.",
                ephemeral=True
            )

            return

        hp_anterior = (
            f"{f['hp_atual']}/{f['hp_max']}"
        )

        mana_anterior = (
            f"{f['mana_atual']}/{f['mana_max']}"
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
            hp,
            hp,
            mana,
            mana,
            f["id"]
        ))

        db.commit()

        novo_hp = (
            f"{hp}/{hp}"
        )

        nova_mana = (
            f"{mana}/{mana}"
        )

        if hp_anterior != novo_hp:

            registrar_historico(
                f["channel_id"],
                f["id"],
                f["nome"],
                f["tipo"],
                interaction.user.id,
                "recursos",
                campo="hp",
                valor_anterior=hp_anterior,
                valor_novo=novo_hp,
                descricao=(
                    "❤️ HP alterado."
                )
            )

        if mana_anterior != nova_mana:

            registrar_historico(
                f["channel_id"],
                f["id"],
                f["nome"],
                f["tipo"],
                interaction.user.id,
                "recursos",
                campo="mana",
                valor_anterior=mana_anterior,
                valor_novo=nova_mana,
                descricao=(
                    "🔵 Mana alterada."
                )
            )

        await interaction.response.send_message(
            f"✅ Ficha de **{f['nome']}** atualizada.\n\n"
            f"❤️ HP: **{hp}/{hp}**\n"
            f"🔵 Mana: **{mana}/{mana}**"
        )


    # ========================================================
# APAGAR PRÓPRIA FICHA
# ========================================================

@bot.tree.command(
    name="apagarficha",
    description="Apaga sua própria ficha."
)
async def apagarficha(
    interaction: discord.Interaction
):

    dados = buscar_ficha_jogador(
        interaction.channel.id,
        interaction.user.id
    )

    if dados is None:

        await interaction.response.send_message(
            "❌ Você não possui uma ficha.",
            ephemeral=True
        )

        return

    f = transformar_ficha(
        dados
    )

    # ====================================================
    # VIEW DE CONFIRMAÇÃO
    # ====================================================

    class ConfirmarApagarFichaView(
        discord.ui.View
    ):

        def __init__(self):

            super().__init__(
                timeout=120
            )

        async def interaction_check(
            self,
            nova_interaction: discord.Interaction
        ):

            if (
                nova_interaction.user.id
                != interaction.user.id
            ):

                await nova_interaction.response.send_message(
                    "❌ Somente quem iniciou esta ação "
                    "pode usar estes botões.",
                    ephemeral=True
                )

                return False

            return True

        # ================================================
        # CONFIRMAR
        # ================================================

        @discord.ui.button(
            label="Sim, apagar",
            emoji="🗑️",
            style=discord.ButtonStyle.danger
        )
        async def confirmar(
            self,
            nova_interaction: discord.Interaction,
            button: discord.ui.Button
        ):

            dados_atualizados = (
                buscar_ficha_jogador(
                    interaction.channel.id,
                    interaction.user.id
                )
            )

            if dados_atualizados is None:

                await nova_interaction.response.edit_message(
                    content=(
                        "❌ A ficha não existe mais."
                    ),
                    view=None
                )

                return

            ficha_atual = transformar_ficha(
                dados_atualizados
            )

            cursor.execute("""
                DELETE FROM fichas
                WHERE id = ?
            """, (
                ficha_atual["id"],
            ))

            db.commit()

            registrar_historico(
                ficha_atual["channel_id"],
                ficha_atual["id"],
                ficha_atual["nome"],
                ficha_atual["tipo"],
                nova_interaction.user.id,
                "ficha_apagada",
                campo=None,
                valor_anterior=None,
                valor_novo=None,
                descricao=(
                    "🗑️ Ficha de jogador apagada."
                )
            )

            await nova_interaction.response.edit_message(
                content=(
                    f"🗑️ Ficha "
                    f"**{ficha_atual['nome']}** "
                    f"apagada com sucesso."
                ),
                view=None
            )

        # ================================================
        # CANCELAR
        # ================================================

        @discord.ui.button(
            label="Cancelar",
            emoji="❌",
            style=discord.ButtonStyle.secondary
        )
        async def cancelar(
            self,
            nova_interaction: discord.Interaction,
            button: discord.ui.Button
        ):

            await nova_interaction.response.edit_message(
                content=(
                    "❎ Exclusão cancelada. "
                    "Sua ficha não foi apagada."
                ),
                view=None
            )

    # ====================================================
    # PEDIR CONFIRMAÇÃO
    # ====================================================

    await interaction.response.send_message(
        (
            "⚠️ **Tem certeza que deseja apagar sua ficha?**\n\n"
            f"📜 Personagem: **{f['nome']}**\n\n"
            "Essa ação removerá a ficha da mesa."
        ),
        view=ConfirmarApagarFichaView(),
        ephemeral=True
    )


    # ========================================================
    # SELETOR DE ALVO
    # ========================================================

    class AlvoSelect(
        discord.ui.Select
    ):

        def __init__(
            self,
            interaction_original,
            acao
        ):

            self.interaction_original = (
                interaction_original
            )

            self.acao = acao

            cursor.execute("""
                SELECT id, nome, tipo
                FROM fichas
                WHERE channel_id = ?
                ORDER BY tipo, nome
                LIMIT 25
            """, (
                interaction_original.channel.id,
            ))

            resultados = (
                cursor.fetchall()
            )

            opcoes = []

            for (
                ficha_id,
                nome,
                tipo
            ) in resultados:

                if tipo == "npc":

                    label = (
                        f"{nome} #{ficha_id}"
                    )

                    emoji = "👹"

                else:

                    label = nome
                    emoji = "👤"

                opcoes.append(
                    discord.SelectOption(
                        label=label[:100],
                        value=str(
                            ficha_id
                        ),
                        emoji=emoji
                    )
                )

            super().__init__(
                placeholder="Escolha a ficha...",
                min_values=1,
                max_values=1,
                options=opcoes
            )


        async def callback(
            self,
            interaction: discord.Interaction
        ):

            ficha_id = int(
                self.values[0]
            )

            dados = buscar_ficha_por_id(
                interaction.channel.id,
                ficha_id
            )

            if dados is None:

                await interaction.response.send_message(
                    "❌ A ficha não existe mais.",
                    ephemeral=True
                )

                return

            f = transformar_ficha(
                dados
            )

            await interaction.response.send_modal(
                ValorAcaoModal(
                    f,
                    self.acao
                )
            )


    # ========================================================
    # VIEW DO ALVO
    # ========================================================

    class AlvoView(
        discord.ui.View
    ):

        def __init__(
            self,
            interaction_original,
            acao
        ):

            super().__init__(
                timeout=300
            )

            self.add_item(
                AlvoSelect(
                    interaction_original,
                    acao
                )
            )


    # ========================================================
    # MODAL DE VALOR
    # ========================================================

    class ValorAcaoModal(
        discord.ui.Modal
    ):

        def __init__(
            self,
            ficha,
            acao
        ):

            self.ficha = ficha
            self.acao = acao

            titulo = {
                "dano": "Aplicar dano",
                "cura": "Aplicar cura",
                "recuperarmana": "Recuperar Mana",
            }.get(
                acao,
                "Alterar recurso"
            )

            super().__init__(
                title=titulo
            )

            self.valor = (
                discord.ui.TextInput(
                    label="Valor",
                    placeholder="Digite um número",
                    required=True
                )
            )

            self.add_item(
                self.valor
            )


        async def on_submit(
            self,
            interaction: discord.Interaction
        ):

            try:

                valor = int(
                    self.valor.value
                )

            except ValueError:

                await interaction.response.send_message(
                    "❌ Informe um número inteiro.",
                    ephemeral=True
                )

                return

            if valor <= 0:

                await interaction.response.send_message(
                    "❌ O valor precisa ser maior que 0.",
                    ephemeral=True
                )

                return

            dados = buscar_ficha_por_id(
                interaction.channel.id,
                self.ficha["id"]
            )

            if dados is None:

                await interaction.response.send_message(
                    "❌ Esta ficha não existe mais.",
                    ephemeral=True
                )

                return

            f = transformar_ficha(
                dados
            )

            # =================================================
            # DANO
            # =================================================

            if self.acao == "dano":

                hp_anterior = (
                    f["hp_atual"]
                )

                novo_hp = max(
                    0,
                    hp_anterior - valor
                )

                if (
                    f["tipo"] == "npc"
                    and novo_hp <= 0
                ):

                    registrar_historico(
                        f["channel_id"],
                        f["id"],
                        f["nome"],
                        f["tipo"],
                        interaction.user.id,
                        "npc_derrotado",
                        campo="hp",
                        valor_anterior=hp_anterior,
                        valor_novo=0,
                        descricao=(
                            f"💥 {valor} de dano recebido. "
                            f"🗑️ NPC derrotado e removido da mesa."
                        )
                    )

                    cursor.execute("""
                        DELETE FROM fichas
                        WHERE id = ?
                    """, (
                        f["id"],
                    ))

                    db.commit()

                    await interaction.response.send_message(
                        f"💀 NPC **{f['nome']} #{f['id']}** "
                        f"foi derrotado!\n"
                        f"🗑️ O NPC foi removido da mesa."
                    )

                    return

                cursor.execute("""
                    UPDATE fichas
                    SET hp_atual = ?
                    WHERE id = ?
                """, (
                    novo_hp,
                    f["id"]
                ))

                db.commit()

                registrar_historico(
                    f["channel_id"],
                    f["id"],
                    f["nome"],
                    f["tipo"],
                    interaction.user.id,
                    "dano",
                    campo="hp",
                    valor_anterior=hp_anterior,
                    valor_novo=novo_hp,
                    descricao=(
                        f"💥 {valor} de dano recebido."
                    )
                )

                await interaction.response.send_message(
                    f"💥 **{f['nome']}** recebeu "
                    f"**{valor} de dano**!\n"
                    f"❤️ HP: **{novo_hp}/{f['hp_max']}** "
                    f"• {estado_hp(novo_hp, f['hp_max'])}"
                )

                return

            # =================================================
            # CURA
            # =================================================

            if self.acao == "cura":

                hp_anterior = (
                    f["hp_atual"]
                )

                novo_hp = min(
                    f["hp_max"],
                    hp_anterior + valor
                )

                recuperado = (
                    novo_hp
                    - hp_anterior
                )

                cursor.execute("""
                    UPDATE fichas
                    SET hp_atual = ?
                    WHERE id = ?
                """, (
                    novo_hp,
                    f["id"]
                ))

                db.commit()

                if (
                    novo_hp
                    != hp_anterior
                ):

                    registrar_historico(
                        f["channel_id"],
                        f["id"],
                        f["nome"],
                        f["tipo"],
                        interaction.user.id,
                        "cura",
                        campo="hp",
                        valor_anterior=hp_anterior,
                        valor_novo=novo_hp,
                        descricao=(
                            f"💚 {recuperado} de HP recuperado."
                        )
                    )

                await interaction.response.send_message(
                    f"💚 **{f['nome']}** recuperou "
                    f"**{recuperado} de HP**!\n"
                    f"❤️ HP: **{novo_hp}/{f['hp_max']}** "
                    f"• {estado_hp(novo_hp, f['hp_max'])}"
                )

                return

            # =================================================
            # RECUPERAR MANA
            # =================================================

            if (
                self.acao
                == "recuperarmana"
            ):

                mana_anterior = (
                    f["mana_atual"]
                )

                nova_mana = min(
                    f["mana_max"],
                    mana_anterior + valor
                )

                recuperado = (
                    nova_mana
                    - mana_anterior
                )

                cursor.execute("""
                    UPDATE fichas
                    SET mana_atual = ?
                    WHERE id = ?
                """, (
                    nova_mana,
                    f["id"]
                ))

                db.commit()

                if (
                    nova_mana
                    != mana_anterior
                ):

                    registrar_historico(
                        f["channel_id"],
                        f["id"],
                        f["nome"],
                        f["tipo"],
                        interaction.user.id,
                        "mana_recuperada",
                        campo="mana",
                        valor_anterior=mana_anterior,
                        valor_novo=nova_mana,
                        descricao=(
                            f"💧 {recuperado} "
                            f"de Mana recuperada."
                        )
                    )

                await interaction.response.send_message(
                    f"💧 **{f['nome']}** recuperou "
                    f"**{recuperado} de Mana**!\n"
                    f"🔵 Mana: **{nova_mana}/{f['mana_max']}** "
                    f"• {estado_mana(nova_mana, f['mana_max'])}"
                )


    # ========================================================
    # DANO
    # ========================================================

    @bot.tree.command(
        name="dano",
        description="Escolhe uma ficha para receber dano."
    )
    async def dano(
        interaction: discord.Interaction
    ):

        cursor.execute("""
            SELECT id
            FROM fichas
            WHERE channel_id = ?
            LIMIT 25
        """, (
            interaction.channel.id,
        ))

        if not cursor.fetchall():

            await interaction.response.send_message(
                "❌ Não existem fichas neste canal.",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "💥 **Escolha quem receberá o dano:**",
            view=AlvoView(
                interaction,
                "dano"
            ),
            ephemeral=True
        )


    # ========================================================
    # CURA
    # ========================================================

    @bot.tree.command(
        name="cura",
        description="Escolhe uma ficha para receber cura."
    )
    async def cura(
        interaction: discord.Interaction
    ):

        cursor.execute("""
            SELECT id
            FROM fichas
            WHERE channel_id = ?
            LIMIT 25
        """, (
            interaction.channel.id,
        ))

        if not cursor.fetchall():

            await interaction.response.send_message(
                "❌ Não existem fichas neste canal.",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "💚 **Escolha quem receberá a cura:**",
            view=AlvoView(
                interaction,
                "cura"
            ),
            ephemeral=True
        )


    # ========================================================
    # RECUPERAR MANA
    # ========================================================

    @bot.tree.command(
        name="recuperarmana",
        description="Escolhe uma ficha para recuperar Mana."
    )
    async def recuperarmana(
        interaction: discord.Interaction
    ):

        cursor.execute("""
            SELECT id
            FROM fichas
            WHERE channel_id = ?
            LIMIT 25
        """, (
            interaction.channel.id,
        ))

        if not cursor.fetchall():

            await interaction.response.send_message(
                "❌ Não existem fichas neste canal.",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "💧 **Escolha quem recuperará Mana:**",
            view=AlvoView(
                interaction,
                "recuperarmana"
            ),
            ephemeral=True
        )


    # ========================================================
    # GASTAR MANA
    # ========================================================

    @bot.tree.command(
        name="gastarmana",
        description="Gasta Mana da sua própria ficha."
    )
    @app_commands.describe(
        valor="Quantidade de Mana gasta"
    )
    async def gastarmana(
        interaction: discord.Interaction,
        valor: int
    ):

        dados = buscar_ficha_jogador(
            interaction.channel.id,
            interaction.user.id
        )

        if dados is None:

            await interaction.response.send_message(
                "❌ Você não possui uma ficha neste canal.",
                ephemeral=True
            )

            return

        if valor <= 0:

            await interaction.response.send_message(
                "❌ O valor precisa ser maior que 0.",
                ephemeral=True
            )

            return

        f = transformar_ficha(
            dados
        )

        if valor > f[
            "mana_atual"
        ]:

            await interaction.response.send_message(
                "❌ Você não possui Mana suficiente.",
                ephemeral=True
            )

            return

        mana_anterior = (
            f["mana_atual"]
        )

        nova_mana = (
            mana_anterior
            - valor
        )

        cursor.execute("""
            UPDATE fichas
            SET mana_atual = ?
            WHERE id = ?
        """, (
            nova_mana,
            f["id"]
        ))

        db.commit()

        registrar_historico(
            f["channel_id"],
            f["id"],
            f["nome"],
            f["tipo"],
            interaction.user.id,
            "mana_gasta",
            campo="mana",
            valor_anterior=mana_anterior,
            valor_novo=nova_mana,
            descricao=(
                f"🔮 {valor} de Mana consumida."
            )
        )

        await interaction.response.send_message(
            f"🔮 **{f['nome']}** gastou "
            f"**{valor} de Mana**!\n"
            f"🔵 Mana: **{nova_mana}/{f['mana_max']}** "
            f"• {estado_mana(nova_mana, f['mana_max'])}"
        )


    # ========================================================
    # ADICIONAR XP
    # ========================================================

    @bot.tree.command(
        name="addxp",
        description="Adiciona XP à ficha de um jogador."
    )
    @app_commands.describe(
        jogador="Jogador que receberá XP",
        valor="Quantidade de XP"
    )
    async def addxp(
        interaction: discord.Interaction,
        jogador: discord.Member,
        valor: int
    ):

        dados = buscar_ficha_jogador(
            interaction.channel.id,
            jogador.id
        )

        if dados is None:

            await interaction.response.send_message(
                "❌ Ficha não encontrada.",
                ephemeral=True
            )

            return

        f = transformar_ficha(
            dados
        )

        if not pode_alterar_ficha(
            interaction,
            f
        ):

            await interaction.response.send_message(
                "❌ Você não possui permissão "
                "para alterar esta ficha.",
                ephemeral=True
            )

            return

        if valor <= 0:

            await interaction.response.send_message(
                "❌ O XP adicionado precisa "
                "ser maior que 0.",
                ephemeral=True
            )

            return

        xp_anterior = (
            f["xp"]
        )

        novo_xp = (
            xp_anterior
            + valor
        )

        cursor.execute("""
            UPDATE fichas
            SET xp = ?
            WHERE id = ?
        """, (
            novo_xp,
            f["id"]
        ))

        db.commit()

        registrar_historico(
            f["channel_id"],
            f["id"],
            f["nome"],
            f["tipo"],
            interaction.user.id,
            "xp",
            campo="xp",
            valor_anterior=xp_anterior,
            valor_novo=novo_xp,
            descricao=(
                f"✨ {valor} XP adicionado."
            )
        )

        await interaction.response.send_message(
            f"✨ **{f['nome']}** recebeu "
            f"**{valor} XP**!\n"
            f"✨ XP atual: **{novo_xp}**"
        )
