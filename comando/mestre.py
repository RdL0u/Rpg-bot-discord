import discord
import random

from discord import app_commands

from database import (
    db,
    cursor,
    garantir_mesa,
    obter_mestre,
    registrar_historico
)

from fichas import (
    transformar_ficha,
    criar_pagina_status,
    FichaView
)

from config import (
    ATRIBUTOS,
    PERICIAS,
    ORDEM_PERICIAS
)

from comando.permissoes import (
    pode_definir_mestre,
    pode_passar_mestre,
    pode_criar_npc,
    pode_visualizar_npcs,
    pode_apagar_npc
)


# ============================================================
# NOMES ALEATÓRIOS DE NPC
# ============================================================

NOMES_NPCS = [
    "Goblin",
    "Orc",
    "Esqueleto",
    "Bandido",
    "Lobo",
    "Zumbi",
    "Slime",
    "Aranha Gigante",
    "Cultista",
    "Guardião",
    "Golem",
    "Morcego Gigante",
    "Troll",
    "Ladrão",
    "Cavaleiro Sombrio"
]


# ============================================================
# NOMES COMPLETOS DOS ATRIBUTOS
# ============================================================

NOMES_ATRIBUTOS = {
    "forca": "Força",
    "destreza": "Destreza",
    "vigor": "Vigor",
    "inteligencia": "Inteligência",
    "carisma": "Carisma",
    "raciocinio": "Raciocínio"
}


# ============================================================
# GRUPOS DOS ATRIBUTOS
# ============================================================

GRUPOS_ATRIBUTOS = [
    [
        "forca",
        "destreza",
        "vigor"
    ],
    [
        "inteligencia",
        "carisma",
        "raciocinio"
    ]
]


# ============================================================
# GRUPOS DAS PERÍCIAS
# ============================================================

GRUPOS_PERICIAS = [
    ORDEM_PERICIAS[0:5],
    ORDEM_PERICIAS[5:10],
    ORDEM_PERICIAS[10:15],
    ORDEM_PERICIAS[15:20],
    ORDEM_PERICIAS[20:23]
]


# ============================================================
# GERAR PERÍCIAS ALEATÓRIAS DO NPC
# ============================================================

def gerar_pericias_aleatorias_npc():

    pericias = {
        chave: 0
        for chave in ORDEM_PERICIAS
    }

    pontos_restantes = 30

    while pontos_restantes > 0:

        disponiveis = [
            chave
            for chave in ORDEM_PERICIAS
            if pericias[chave] < 5
        ]

        escolhida = random.choice(
            disponiveis
        )

        pericias[
            escolhida
        ] += 1

        pontos_restantes -= 1

    return pericias


# ============================================================
# SESSÃO DE CRIAÇÃO DE NPC
# ============================================================

class SessaoCriacaoNPC:

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

        self.dados_basicos_aleatorios = False
        self.atributos_aleatorios = False
        self.pericias_aleatorias = False


# ============================================================
# VIEW BASE DA CRIAÇÃO
# ============================================================

class ViewSessao(discord.ui.View):

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
                "❌ Somente quem iniciou a criação "
                "pode usar estes controles.",
                ephemeral=True
            )

            return False

        return True


# ============================================================
# FINALIZAR CRIAÇÃO DO NPC
# ============================================================

async def finalizar_criacao_npc(
    interaction,
    sessao
):

    mestre_id = obter_mestre(
        sessao.channel_id
    )

    if mestre_id is None:

        mestre_id = sessao.usuario_id

        garantir_mesa(
            sessao.channel_id
        )

        cursor.execute("""
            UPDATE mesas
            SET mestre_id = ?
            WHERE channel_id = ?
        """, (
            mestre_id,
            sessao.channel_id
        ))

        db.commit()

    nome = (
        sessao.nome
        or "NPC"
    )

    nome = nome[:50]

    # ========================================================
    # COLUNAS
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
            sessao.atributos.get(
                chave,
                0
            )
            for chave in ATRIBUTOS
        ]
        +
        [
            sessao.pericias.get(
                chave,
                0
            )
            for chave in ORDEM_PERICIAS
        ]
    )

    placeholders = ", ".join(
        ["?"] * len(valores)
    )

    # ========================================================
    # SALVAR
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
            ?, NULL, ?, 'npc', ?,

            ?, ?,

            ?, ?,

            0,

            {placeholders},

            ?
        )
        """,
        [
            sessao.channel_id,
            mestre_id,
            nome,

            sessao.hp,
            sessao.hp,

            sessao.mana,
            sessao.mana
        ]
        + valores
        + [
            int(
                sessao.dados_basicos_aleatorios
                or sessao.atributos_aleatorios
                or sessao.pericias_aleatorias
            )
        ]
    )

    db.commit()

    npc_id = cursor.lastrowid

    rc = (
        sessao.pericias.get(
            "esquiva",
            0
        )
        +
        sessao.atributos.get(
            "destreza",
            0
        )
        +
        5
    )

    modos = []

    modos.append(
        "🎲 Dados básicos aleatórios"
        if sessao.dados_basicos_aleatorios
        else
        "✏️ Dados básicos personalizados"
    )

    modos.append(
        "🎲 Atributos aleatórios"
        if sessao.atributos_aleatorios
        else
        "✏️ Atributos personalizados"
    )

    modos.append(
        "🎲 Perícias aleatórias"
        if sessao.pericias_aleatorias
        else
        "✏️ Perícias personalizadas"
    )

    resumo_modos = "\n".join(
        modos
    )

    await interaction.response.send_message(
        f"👹 NPC **{nome} #{npc_id}** criado!\n\n"
        f"❤️ HP: **{sessao.hp}/{sessao.hp}**\n"
        f"🔵 Mana: **{sessao.mana}/{sessao.mana}**\n"
        f"✨ XP: **0**\n"
        f"⚡ RC: **{rc}**\n\n"
        f"{resumo_modos}",
        ephemeral=True
    )


# ============================================================
# DADOS BÁSICOS ALEATÓRIOS?
# ============================================================

class ViewDadosBasicos(ViewSessao):

    @discord.ui.button(
        label="🎲 Sim, aleatórios",
        style=discord.ButtonStyle.success
    )
    async def aleatorios(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        self.sessao.nome = random.choice(
            NOMES_NPCS
        )

        self.sessao.hp = random.randint(
            20,
            150
        )

        self.sessao.mana = random.randint(
            0,
            100
        )

        self.sessao.dados_basicos_aleatorios = True

        await interaction.response.send_message(
            f"🎲 Dados gerados:\n\n"
            f"👹 Nome: **{self.sessao.nome}**\n"
            f"❤️ HP: **{self.sessao.hp}**\n"
            f"🔵 Mana: **{self.sessao.mana}**\n\n"
            f"⚔️ Os **atributos** serão aleatórios?",
            view=ViewEscolherAtributos(
                self.sessao
            ),
            ephemeral=True
        )


    @discord.ui.button(
        label="✏️ Não, preencher",
        style=discord.ButtonStyle.primary
    )
    async def personalizados(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.send_modal(
            ModalDadosBasicos(
                self.sessao
            )
        )


# ============================================================
# MODAL DADOS BÁSICOS
# ============================================================

class ModalDadosBasicos(
    discord.ui.Modal,
    title="Dados do NPC"
):

    def __init__(
        self,
        sessao
    ):

        super().__init__()

        self.sessao = sessao

        self.nome = discord.ui.TextInput(
            label="Nome",
            placeholder="Nome do NPC",
            required=True,
            max_length=50
        )

        self.hp = discord.ui.TextInput(
            label="HP máximo",
            placeholder="Ex.: 40",
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
                "❌ Você não pode preencher este formulário.",
                ephemeral=True
            )

            return

        nome = self.nome.value.strip()

        if not nome:

            await interaction.response.send_message(
                "❌ Informe um nome válido.",
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
                "❌ HP e Mana precisam ser números inteiros.",
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

        self.sessao.nome = nome[:50]
        self.sessao.hp = hp
        self.sessao.mana = mana

        self.sessao.dados_basicos_aleatorios = False

        await interaction.response.send_message(
            "✅ Dados básicos salvos.\n\n"
            "⚔️ Os **atributos** serão aleatórios?",
            view=ViewEscolherAtributos(
                self.sessao
            ),
            ephemeral=True
        )


# ============================================================
# ATRIBUTOS ALEATÓRIOS?
# ============================================================

class ViewEscolherAtributos(ViewSessao):

    @discord.ui.button(
        label="🎲 Sim, aleatórios",
        style=discord.ButtonStyle.success
    )
    async def aleatorios(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        for chave in ATRIBUTOS:

            self.sessao.atributos[
                chave
            ] = random.randint(
                0,
                5
            )

        self.sessao.atributos_aleatorios = True

        await interaction.response.send_message(
            "🎲 Atributos gerados com sucesso.\n\n"
            "📚 As **perícias** serão aleatórias?",
            view=ViewEscolherPericias(
                self.sessao
            ),
            ephemeral=True
        )


    @discord.ui.button(
        label="✏️ Não, preencher",
        style=discord.ButtonStyle.primary
    )
    async def personalizados(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.send_modal(
            ModalAtributos(
                self.sessao,
                grupo=0
            )
        )


# ============================================================
# MODAL ATRIBUTOS
# ============================================================

class ModalAtributos(discord.ui.Modal):

    def __init__(
        self,
        sessao,
        grupo
    ):

        self.sessao = sessao
        self.grupo = grupo

        campos = GRUPOS_ATRIBUTOS[
            grupo
        ]

        super().__init__(
            title=(
                f"Atributos "
                f"{grupo + 1}/{len(GRUPOS_ATRIBUTOS)}"
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

        self.sessao.atributos.update(
            valores
        )

        self.sessao.atributos_aleatorios = False

        proximo = (
            self.grupo + 1
        )

        if (
            proximo
            < len(GRUPOS_ATRIBUTOS)
        ):

            await interaction.response.send_message(
                "✅ Parte dos atributos salva.\n\n"
                "Clique abaixo para continuar.",
                view=ViewContinuarAtributos(
                    self.sessao,
                    proximo
                ),
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "✅ Todos os atributos foram salvos.\n\n"
            "📚 As **perícias** serão aleatórias?",
            view=ViewEscolherPericias(
                self.sessao
            ),
            ephemeral=True
        )


# ============================================================
# CONTINUAR ATRIBUTOS
# ============================================================

class ViewContinuarAtributos(ViewSessao):

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
            ModalAtributos(
                self.sessao,
                self.grupo
            )
        )


# ============================================================
# PERÍCIAS ALEATÓRIAS?
# ============================================================

class ViewEscolherPericias(ViewSessao):

    @discord.ui.button(
        label="🎲 Sim, aleatórias",
        style=discord.ButtonStyle.success
    )
    async def aleatorias(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        self.sessao.pericias = (
            gerar_pericias_aleatorias_npc()
        )

        self.sessao.pericias_aleatorias = True

        await finalizar_criacao_npc(
            interaction,
            self.sessao
        )


    @discord.ui.button(
        label="✏️ Não, preencher",
        style=discord.ButtonStyle.primary
    )
    async def personalizadas(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.send_modal(
            ModalPericias(
                self.sessao,
                grupo=0
            )
        )


# ============================================================
# MODAL PERÍCIAS
# ============================================================

class ModalPericias(discord.ui.Modal):

    def __init__(
        self,
        sessao,
        grupo
    ):

        self.sessao = sessao
        self.grupo = grupo

        campos = GRUPOS_PERICIAS[
            grupo
        ]

        super().__init__(
            title=(
                f"Perícias "
                f"{grupo + 1}/{len(GRUPOS_PERICIAS)}"
            )
        )

        self.inputs = {}

        for chave in campos:

            emoji, nome = PERICIAS[
                chave
            ]

            campo = discord.ui.TextInput(
                label=nome[:45],
                placeholder="Valor",
                default=str(
                    sessao.pericias.get(
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

        valores = {}

        try:

            for chave, campo in self.inputs.items():

                valor = int(
                    campo.value
                )

                if valor < 0 or valor > 5:
                    raise ValueError

                valores[
                    chave
                ] = valor

        except ValueError:

            await interaction.response.send_message(
                "❌ Todas as perícias precisam ser "
                "números inteiros entre 0 e 5.",
                ephemeral=True
            )

            return

        self.sessao.pericias.update(
            valores
        )

        self.sessao.pericias_aleatorias = False

        proximo = (
            self.grupo + 1
        )

        if (
            proximo
            < len(GRUPOS_PERICIAS)
        ):

            await interaction.response.send_message(
                "✅ Parte das perícias salva.\n\n"
                "Clique abaixo para continuar.",
                view=ViewContinuarPericias(
                    self.sessao,
                    proximo
                ),
                ephemeral=True
            )

            return

        await finalizar_criacao_npc(
            interaction,
            self.sessao
        )


# ============================================================
# CONTINUAR PERÍCIAS
# ============================================================

class ViewContinuarPericias(ViewSessao):

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
            ModalPericias(
                self.sessao,
                self.grupo
            )
        )


# ============================================================
# REGISTRAR COMANDOS DO MESTRE
# ============================================================

def registrar_comandos_mestre(bot):

    # ========================================================
    # DEFINIR MESTRE
    # ========================================================

    @bot.tree.command(
        name="definirmestre",
        description="Define o Mestre deste canal."
    )
    @app_commands.describe(
        jogador="Jogador que será o Mestre"
    )
    async def definirmestre(
        interaction: discord.Interaction,
        jogador: discord.Member
    ):

        if not pode_definir_mestre(
            interaction
        ):

            await interaction.response.send_message(
                "❌ Somente administradores podem definir o Mestre.",
                ephemeral=True
            )

            return

        garantir_mesa(
            interaction.channel.id
        )

        cursor.execute("""
            UPDATE mesas
            SET mestre_id = ?
            WHERE channel_id = ?
        """, (
            jogador.id,
            interaction.channel.id
        ))

        cursor.execute("""
            UPDATE fichas
            SET mestre_id = ?
            WHERE channel_id = ?
            AND tipo = 'npc'
        """, (
            jogador.id,
            interaction.channel.id
        ))

        db.commit()

        await interaction.response.send_message(
            f"👑 **{jogador.display_name}** "
            f"agora é o Mestre deste canal!"
        )


    # ========================================================
    # PASSAR MESTRE
    # ========================================================

    @bot.tree.command(
        name="passarmestre",
        description="Passa o cargo de Mestre para outro jogador."
    )
    @app_commands.describe(
        jogador="Jogador que será o novo Mestre"
    )
    async def passarmestre(
        interaction: discord.Interaction,
        jogador: discord.Member
    ):

        if not pode_passar_mestre(
            interaction
        ):

            await interaction.response.send_message(
                "❌ Somente o Mestre atual ou um administrador "
                "pode fazer isso.",
                ephemeral=True
            )

            return

        garantir_mesa(
            interaction.channel.id
        )

        cursor.execute("""
            UPDATE mesas
            SET mestre_id = ?
            WHERE channel_id = ?
        """, (
            jogador.id,
            interaction.channel.id
        ))

        cursor.execute("""
            UPDATE fichas
            SET mestre_id = ?
            WHERE channel_id = ?
            AND tipo = 'npc'
        """, (
            jogador.id,
            interaction.channel.id
        ))

        db.commit()

        await interaction.response.send_message(
            f"👑 Novo Mestre: {jogador.mention}\n"
            f"👹 Os NPCs foram transferidos para ele."
        )


    # ========================================================
    # MOSTRAR MESTRE
    # ========================================================

    @bot.tree.command(
        name="mestre",
        description="Mostra o Mestre deste canal."
    )
    async def mestre(
        interaction: discord.Interaction
    ):

        mestre_id = obter_mestre(
            interaction.channel.id
        )

        if mestre_id is None:

            await interaction.response.send_message(
                "👑 Este canal ainda não possui um Mestre."
            )

            return

        membro = interaction.guild.get_member(
            mestre_id
        )

        if membro:

            await interaction.response.send_message(
                f"👑 Mestre deste canal: "
                f"**{membro.display_name}**"
            )

        else:

            await interaction.response.send_message(
                f"👑 Mestre: <@{mestre_id}>"
            )


    # ========================================================
    # CRIAR NPC
    # ========================================================

    @bot.tree.command(
        name="criarnpc",
        description="Inicia a criação guiada de um NPC."
    )
    async def criarnpc(
        interaction: discord.Interaction
    ):

        garantir_mesa(
            interaction.channel.id
        )

        if not pode_criar_npc(
            interaction
        ):

            await interaction.response.send_message(
                "❌ Somente o Mestre ou um administrador "
                "pode criar NPCs.",
                ephemeral=True
            )

            return

        sessao = SessaoCriacaoNPC(
            interaction.channel.id,
            interaction.user.id
        )

        await interaction.response.send_message(
            "👹 **Criação de NPC**\n\n"
            "🎲 O **nome, HP e Mana** serão aleatórios?",
            view=ViewDadosBasicos(
                sessao
            ),
            ephemeral=True
        )


    # ========================================================
    # LISTAR NPCS
    # ========================================================

    @bot.tree.command(
        name="npcs",
        description="Mostra os NPCs da mesa."
    )
    async def npcs(
        interaction: discord.Interaction
    ):

        if not pode_visualizar_npcs(
            interaction
        ):

            await interaction.response.send_message(
                "❌ Somente o Mestre pode visualizar os NPCs.",
                ephemeral=True
            )

            return

        cursor.execute("""
            SELECT *
            FROM fichas
            WHERE channel_id = ?
            AND tipo = 'npc'
            ORDER BY nome
        """, (
            interaction.channel.id,
        ))

        resultados = cursor.fetchall()

        if not resultados:

            await interaction.response.send_message(
                "👹 Não existem NPCs neste canal.",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            f"👹 **NPCs da mesa — "
            f"{len(resultados)} encontrados**",
            ephemeral=True
        )

        for dados in resultados:

            f = transformar_ficha(
                dados
            )

            await interaction.followup.send(
                embed=criar_pagina_status(
                    f
                ),
                view=FichaView(
                    f
                ),
                ephemeral=True
            )


    # ========================================================
    # APAGAR NPC
    # ========================================================

    @bot.tree.command(
        name="apagarnpc",
        description="Apaga um ou vários NPCs da mesa."
    )
    async def apagarnpc(
        interaction: discord.Interaction
    ):

        if not pode_apagar_npc(
            interaction
        ):

            await interaction.response.send_message(
                "❌ Somente o Mestre ou um administrador "
                "pode apagar NPCs.",
                ephemeral=True
            )

            return

        # ====================================================
        # BUSCAR NPCS
        # ====================================================

        cursor.execute("""
            SELECT id, nome
            FROM fichas
            WHERE channel_id = ?
            AND tipo = 'npc'
            ORDER BY nome
        """, (
            interaction.channel.id,
        ))

        npcs_encontrados = cursor.fetchall()

        if not npcs_encontrados:

            await interaction.response.send_message(
                "👹 Não existem NPCs neste canal.",
                ephemeral=True
            )

            return

        # ====================================================
        # SELETOR DE NPC
        # ====================================================

        class SelectNPC(
            discord.ui.Select
        ):

            def __init__(
                self,
                multiplo
            ):

                self.multiplo = multiplo

                opcoes = []

                for npc_id, nome in npcs_encontrados[:25]:

                    opcoes.append(
                        discord.SelectOption(
                            label=(
                                f"{nome} #{npc_id}"
                            )[:100],
                            value=str(
                                npc_id
                            ),
                            emoji="👹"
                        )
                    )

                if multiplo:

                    maximo = len(
                        opcoes
                    )

                else:

                    maximo = 1

                super().__init__(
                    placeholder=(
                        "Selecione os NPCs..."
                        if multiplo
                        else
                        "Selecione um NPC..."
                    ),
                    min_values=1,
                    max_values=maximo,
                    options=opcoes
                )


            async def callback(
                self,
                nova_interaction: discord.Interaction
            ):

                if (
                    nova_interaction.user.id
                    != interaction.user.id
                ):

                    await nova_interaction.response.send_message(
                        "❌ Você não pode usar este menu.",
                        ephemeral=True
                    )

                    return

                ids = [
                    int(
                        valor
                    )
                    for valor in self.values
                ]

                placeholders = ", ".join(
                    ["?"] * len(ids)
                )

                cursor.execute(
                    f"""
                    SELECT id, nome
                    FROM fichas
                    WHERE channel_id = ?
                    AND tipo = 'npc'
                    AND id IN ({placeholders})
                    """,
                    [
                        interaction.channel.id
                    ] + ids
                )

                selecionados = (
                    cursor.fetchall()
                )

                if not selecionados:

                    await nova_interaction.response.edit_message(
                        content=(
                            "❌ Os NPCs selecionados "
                            "não existem mais."
                        ),
                        view=None
                    )

                    return

                texto_nomes = "\n".join(
                    (
                        f"• 👹 **{nome} #{npc_id}**"
                    )
                    for npc_id, nome
                    in selecionados
                )

                await nova_interaction.response.edit_message(
                    content=(
                        "⚠️ **Confirmar exclusão?**\n\n"
                        f"{texto_nomes}\n\n"
                        "Esta ação não poderá ser desfeita."
                    ),
                    view=ViewConfirmarSelecionados(
                        ids
                    )
                )


        # ====================================================
        # VIEW DE SELEÇÃO
        # ====================================================

        class ViewSelecionarNPC(
            discord.ui.View
        ):

            def __init__(
                self,
                multiplo
            ):

                super().__init__(
                    timeout=300
                )

                self.add_item(
                    SelectNPC(
                        multiplo
                    )
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
                        "pode usar este menu.",
                        ephemeral=True
                    )

                    return False

                return True


        # ====================================================
        # CONFIRMAR NPCS SELECIONADOS
        # ====================================================

        class ViewConfirmarSelecionados(
            discord.ui.View
        ):

            def __init__(
                self,
                ids
            ):

                super().__init__(
                    timeout=300
                )

                self.ids = ids


            async def interaction_check(
                self,
                nova_interaction: discord.Interaction
            ):

                if (
                    nova_interaction.user.id
                    != interaction.user.id
                ):

                    await nova_interaction.response.send_message(
                        "❌ Você não pode confirmar esta ação.",
                        ephemeral=True
                    )

                    return False

                return True


            @discord.ui.button(
                label="Confirmar exclusão",
                emoji="🗑️",
                style=discord.ButtonStyle.danger
            )
            async def confirmar(
                self,
                nova_interaction: discord.Interaction,
                button: discord.ui.Button
            ):

                placeholders = ", ".join(
                    ["?"] * len(
                        self.ids
                    )
                )

                cursor.execute(
                    f"""
                    SELECT id, nome
                    FROM fichas
                    WHERE channel_id = ?
                    AND tipo = 'npc'
                    AND id IN ({placeholders})
                    """,
                    [
                        interaction.channel.id
                    ] + self.ids
                )

                encontrados = (
                    cursor.fetchall()
                )

                if not encontrados:

                    await nova_interaction.response.edit_message(
                        content=(
                            "❌ Os NPCs selecionados "
                            "não existem mais."
                        ),
                        view=None
                    )

                    self.stop()

                    return

                ids_validos = [
                    npc_id
                    for npc_id, nome
                    in encontrados
                ]

                placeholders_validos = ", ".join(
                    ["?"] * len(
                        ids_validos
                    )
                )

                # ============================================
                # HISTÓRICO
                # ============================================

                for npc_id, nome in encontrados:

                    registrar_historico(
                        interaction.channel.id,
                        npc_id,
                        nome,
                        "npc",
                        nova_interaction.user.id,
                        "npc_apagado",
                        campo=None,
                        valor_anterior=None,
                        valor_novo=None,
                        descricao=(
                            "🗑️ NPC apagado manualmente."
                        )
                    )

                # ============================================
                # APAGAR
                # ============================================

                cursor.execute(
                    f"""
                    DELETE FROM fichas
                    WHERE channel_id = ?
                    AND tipo = 'npc'
                    AND id IN ({placeholders_validos})
                    """,
                    [
                        interaction.channel.id
                    ] + ids_validos
                )

                db.commit()

                if len(
                    encontrados
                ) == 1:

                    npc_id, nome = (
                        encontrados[0]
                    )

                    mensagem = (
                        f"🗑️ NPC "
                        f"**{nome} #{npc_id}** "
                        f"apagado com sucesso."
                    )

                else:

                    lista = "\n".join(
                        (
                            f"• {nome} #{npc_id}"
                        )
                        for npc_id, nome
                        in encontrados
                    )

                    mensagem = (
                        f"🗑️ **{len(encontrados)} NPCs "
                        f"apagados com sucesso:**\n\n"
                        f"{lista}"
                    )

                await nova_interaction.response.edit_message(
                    content=mensagem,
                    view=None
                )

                self.stop()


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
                        "Nenhum NPC foi apagado."
                    ),
                    view=None
                )

                self.stop()


        # ====================================================
        # CONFIRMAR EXCLUSÃO DE TODOS
        # ====================================================

        class ViewConfirmarTodos(
            discord.ui.View
        ):

            def __init__(
                self
            ):

                super().__init__(
                    timeout=300
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
                        "❌ Você não pode confirmar esta ação.",
                        ephemeral=True
                    )

                    return False

                return True


            @discord.ui.button(
                label="Sim, apagar todos",
                emoji="🗑️",
                style=discord.ButtonStyle.danger
            )
            async def confirmar(
                self,
                nova_interaction: discord.Interaction,
                button: discord.ui.Button
            ):

                cursor.execute("""
                    SELECT id, nome
                    FROM fichas
                    WHERE channel_id = ?
                    AND tipo = 'npc'
                    ORDER BY nome
                """, (
                    interaction.channel.id,
                ))

                encontrados = (
                    cursor.fetchall()
                )

                quantidade = len(
                    encontrados
                )

                if quantidade == 0:

                    await nova_interaction.response.edit_message(
                        content=(
                            "👹 Não existem mais NPCs "
                            "para apagar."
                        ),
                        view=None
                    )

                    self.stop()

                    return

                # ============================================
                # HISTÓRICO
                # ============================================

                for npc_id, nome in encontrados:

                    registrar_historico(
                        interaction.channel.id,
                        npc_id,
                        nome,
                        "npc",
                        nova_interaction.user.id,
                        "npc_apagado",
                        campo=None,
                        valor_anterior=None,
                        valor_novo=None,
                        descricao=(
                            "🗑️ NPC apagado manualmente "
                            "na exclusão em massa."
                        )
                    )

                cursor.execute("""
                    DELETE FROM fichas
                    WHERE channel_id = ?
                    AND tipo = 'npc'
                """, (
                    interaction.channel.id,
                ))

                db.commit()

                await nova_interaction.response.edit_message(
                    content=(
                        f"🗑️ **{quantidade} NPC(s)** "
                        f"foram apagados da mesa."
                    ),
                    view=None
                )

                self.stop()


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
                        "Nenhum NPC foi apagado."
                    ),
                    view=None
                )

                self.stop()


        # ====================================================
        # MENU INICIAL
        # ====================================================

        class ViewModoExclusao(
            discord.ui.View
        ):

            def __init__(
                self
            ):

                super().__init__(
                    timeout=300
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


            @discord.ui.button(
                label="Um NPC",
                emoji="👹",
                style=discord.ButtonStyle.primary
            )
            async def um_npc(
                self,
                nova_interaction: discord.Interaction,
                button: discord.ui.Button
            ):

                await nova_interaction.response.edit_message(
                    content=(
                        "👹 **Qual NPC deseja apagar?**"
                    ),
                    view=ViewSelecionarNPC(
                        multiplo=False
                    )
                )


            @discord.ui.button(
                label="Vários NPCs",
                emoji="👥",
                style=discord.ButtonStyle.secondary
            )
            async def varios_npcs(
                self,
                nova_interaction: discord.Interaction,
                button: discord.ui.Button
            ):

                await nova_interaction.response.edit_message(
                    content=(
                        "👹 **Selecione os NPCs "
                        "que deseja apagar:**"
                    ),
                    view=ViewSelecionarNPC(
                        multiplo=True
                    )
                )


            @discord.ui.button(
                label="Todos",
                emoji="⚠️",
                style=discord.ButtonStyle.danger
            )
            async def todos(
                self,
                nova_interaction: discord.Interaction,
                button: discord.ui.Button
            ):

                cursor.execute("""
                    SELECT COUNT(*)
                    FROM fichas
                    WHERE channel_id = ?
                    AND tipo = 'npc'
                """, (
                    interaction.channel.id,
                ))

                quantidade_atual = (
                    cursor.fetchone()[0]
                )

                if quantidade_atual == 0:

                    await nova_interaction.response.edit_message(
                        content=(
                            "👹 Não existem mais NPCs "
                            "nesta mesa."
                        ),
                        view=None
                    )

                    self.stop()

                    return

                await nova_interaction.response.edit_message(
                    content=(
                        "⚠️ **ATENÇÃO**\n\n"
                        f"Você está prestes a apagar "
                        f"**{quantidade_atual} NPC(s)** "
                        f"desta mesa.\n\n"
                        "Esta ação não poderá ser desfeita.\n\n"
                        "Deseja continuar?"
                    ),
                    view=ViewConfirmarTodos()
                )


        # ====================================================
        # MOSTRAR MENU
        # ====================================================

        await interaction.response.send_message(
            "🗑️ **Gerenciamento de exclusão de NPCs**\n\n"
            f"Existem **{len(npcs_encontrados)} NPC(s)** "
            f"nesta mesa.\n\n"
            "O que deseja apagar?",
            view=ViewModoExclusao(),
            ephemeral=True
        )
