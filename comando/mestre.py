import discord
import random

from discord import app_commands

from database import (
    db,
    cursor,
    garantir_mesa,
    obter_mestre
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
    eh_admin,
    eh_mestre
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
                "do NPC pode usar estes controles.",
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

    # ========================================================
    # VALIDAR DADOS BÁSICOS
    # ========================================================

    if not sessao.nome:

        await interaction.response.send_message(
            "❌ O NPC está sem nome.",
            ephemeral=True
        )

        return

    if (
        sessao.hp is None
        or sessao.hp <= 0
    ):

        await interaction.response.send_message(
            "❌ O HP do NPC é inválido.",
            ephemeral=True
        )

        return

    if (
        sessao.mana is None
        or sessao.mana < 0
    ):

        await interaction.response.send_message(
            "❌ A Mana do NPC é inválida.",
            ephemeral=True
        )

        return

    # ========================================================
    # VALIDAR ATRIBUTOS
    # ========================================================

    for chave in ATRIBUTOS:

        if chave not in sessao.atributos:

            await interaction.response.send_message(
                f"❌ O atributo `{chave}` não foi preenchido.",
                ephemeral=True
            )

            return

    # ========================================================
    # VALIDAR PERÍCIAS
    # ========================================================

    for chave in ORDEM_PERICIAS:

        if chave not in sessao.pericias:

            await interaction.response.send_message(
                f"❌ A perícia `{chave}` não foi preenchida.",
                ephemeral=True
            )

            return

    # ========================================================
    # GARANTIR MESTRE
    # ========================================================

    garantir_mesa(
        sessao.channel_id
    )

    mestre_id = obter_mestre(
        sessao.channel_id
    )

    if mestre_id is None:

        mestre_id = sessao.usuario_id

        cursor.execute("""
            UPDATE mesas
            SET mestre_id = ?
            WHERE channel_id = ?
        """, (
            mestre_id,
            sessao.channel_id
        ))

        db.commit()

    # ========================================================
    # PREPARAR COLUNAS
    # ========================================================

    colunas = (
        list(ATRIBUTOS.keys())
        + ORDEM_PERICIAS
    )

    valores = (
        [
            sessao.atributos[chave]
            for chave in ATRIBUTOS
        ]
        +
        [
            sessao.pericias[chave]
            for chave in ORDEM_PERICIAS
        ]
    )

    placeholders = ", ".join(
        ["?"] * len(valores)
    )

    aleatorio_valor = int(
        sessao.dados_basicos_aleatorios
        or sessao.atributos_aleatorios
        or sessao.pericias_aleatorias
    )

    nome = sessao.nome[:50]

    # ========================================================
    # INSERIR NPC
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
            aleatorio_valor
        ]
    )

    db.commit()

    # ========================================================
    # CALCULAR RC
    # ========================================================

    rc = (
        sessao.pericias["esquiva"]
        + sessao.atributos["destreza"]
        + 5
    )

    # ========================================================
    # RESUMO
    # ========================================================

    dados_basicos_texto = (
        "🎲 Aleatórios"
        if sessao.dados_basicos_aleatorios
        else "✏️ Personalizados"
    )

    atributos_texto = (
        "🎲 Aleatórios"
        if sessao.atributos_aleatorios
        else "✏️ Personalizados"
    )

    pericias_texto = (
        "🎲 Aleatórias"
        if sessao.pericias_aleatorias
        else "✏️ Personalizadas"
    )

    await interaction.response.send_message(
        f"👹 NPC **{nome}** criado com sucesso!\n\n"
        f"❤️ HP: **{sessao.hp}/{sessao.hp}**\n"
        f"🔵 Mana: **{sessao.mana}/{sessao.mana}**\n"
        f"⚡ RC: **{rc}**\n\n"
        f"📋 Dados básicos: {dados_basicos_texto}\n"
        f"📊 Atributos: {atributos_texto}\n"
        f"📚 Perícias: {pericias_texto}",
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
            f"🎲 Dados básicos gerados:\n\n"
            f"👹 Nome: **{self.sessao.nome}**\n"
            f"❤️ HP: **{self.sessao.hp}**\n"
            f"🔵 Mana: **{self.sessao.mana}**\n\n"
            f"📊 Os **atributos** serão aleatórios?",
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
            label="Nome do NPC",
            placeholder="Ex.: Cavaleiro Negro",
            required=True,
            max_length=50
        )

        self.hp = discord.ui.TextInput(
            label="HP",
            placeholder="Ex.: 50",
            required=True,
            max_length=7
        )

        self.mana = discord.ui.TextInput(
            label="Mana",
            placeholder="Ex.: 20",
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

        self.sessao.nome = (
            self.nome.value.strip()[:50]
        )

        self.sessao.hp = hp
        self.sessao.mana = mana

        self.sessao.dados_basicos_aleatorios = False

        await interaction.response.send_message(
            "✅ Dados básicos salvos.\n\n"
            "📊 Os **atributos** serão aleatórios?",
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

        for chave in ORDEM_PERICIAS:

            self.sessao.pericias[
                chave
            ] = random.randint(
                0,
                5
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

                if valor < 0:
                    raise ValueError

                valores[
                    chave
                ] = valor

        except ValueError:

            await interaction.response.send_message(
                "❌ Todas as perícias precisam ser "
                "números inteiros maiores ou iguais a 0.",
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
                f"✅ Perícias "
                f"{self.grupo + 1}/{len(GRUPOS_PERICIAS)} "
                f"salvas.\n\n"
                f"Clique abaixo para continuar.",
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

        if not eh_admin(interaction):

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

        mestre_id = obter_mestre(
            interaction.channel.id
        )

        if (
            interaction.user.id != mestre_id
            and not eh_admin(interaction)
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

        if (
            not eh_mestre(interaction)
            and not eh_admin(interaction)
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

        if (
            not eh_mestre(interaction)
            and not eh_admin(interaction)
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

        if (
            not eh_mestre(interaction)
            and not eh_admin(interaction)
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
        # SELEÇÃO DE NPC
        # ====================================================

        class SelectNPC(discord.ui.Select):

            def __init__(
                self,
                multiplo
            ):

                self.multiplo = multiplo

                opcoes = []

                for npc_id, nome in npcs_encontrados[:25]:

                    opcoes.append(
                        discord.SelectOption(
                            label=nome[:100],
                            value=str(npc_id),
                            emoji="👹"
                        )
                    )

                if multiplo:
                    maximo = len(opcoes)
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
                    int(valor)
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

                selecionados = cursor.fetchall()

                if not selecionados:

                    await nova_interaction.response.edit_message(
                        content=(
                            "❌ Os NPCs selecionados "
                            "não existem mais."
                        ),
                        view=None
                    )

                    return

                nomes = [
                    nome
                    for npc_id, nome in selecionados
                ]

                texto_nomes = "\n".join(
                    f"• 👹 **{nome}**"
                    for nome in nomes
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

        class ViewSelecionarNPC(discord.ui.View):

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

        # ====================================================
        # CONFIRMAR SELECIONADOS
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
                nova_interaction
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
                    ["?"] * len(self.ids)
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

                encontrados = cursor.fetchall()

                if not encontrados:

                    await nova_interaction.response.edit_message(
                        content=(
                            "❌ Os NPCs selecionados "
                            "não existem mais."
                        ),
                        view=None
                    )

                    return

                ids_validos = [
                    npc_id
                    for npc_id, nome
                    in encontrados
                ]

                placeholders_validos = ", ".join(
                    ["?"] * len(ids_validos)
                )

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

                nomes = [
                    nome
                    for npc_id, nome
                    in encontrados
                ]

                if len(nomes) == 1:

                    mensagem = (
                        f"🗑️ NPC **{nomes[0]}** "
                        f"apagado com sucesso."
                    )

                else:

                    lista = "\n".join(
                        f"• {nome}"
                        for nome in nomes
                    )

                    mensagem = (
                        f"🗑️ **{len(nomes)} NPCs "
                        f"apagados com sucesso:**\n\n"
                        f"{lista}"
                    )

                await nova_interaction.response.edit_message(
                    content=mensagem,
                    view=None
                )


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

        # ====================================================
        # CONFIRMAR TODOS
        # ====================================================

        class ViewConfirmarTodos(
            discord.ui.View
        ):

            def __init__(self):

                super().__init__(
                    timeout=300
                )


            async def interaction_check(
                self,
                nova_interaction
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
                    SELECT COUNT(*)
                    FROM fichas
                    WHERE channel_id = ?
                    AND tipo = 'npc'
                """, (
                    interaction.channel.id,
                ))

                quantidade = cursor.fetchone()[0]

                if quantidade == 0:

                    await nova_interaction.response.edit_message(
                        content=(
                            "👹 Não existem mais NPCs "
                            "para apagar."
                        ),
                        view=None
                    )

                    return

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

        # ====================================================
        # MENU INICIAL DE EXCLUSÃO
        # ====================================================

        class ViewModoExclusao(discord.ui.View):

            def __init__(self):

                super().__init__(
                    timeout=300
                )


            async def interaction_check(
                self,
                nova_interaction
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

                await nova_interaction.response.edit_message(
                    content=(
                        "⚠️ **ATENÇÃO**\n\n"
                        f"Você está prestes a apagar "
                        f"**{len(npcs_encontrados)} NPC(s)** "
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
