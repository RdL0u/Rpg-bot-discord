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
# CONFIGURAÇÕES
# ============================================================

NPCS_POR_PAGINA = 25


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
# PERÍCIAS DIVIDIDAS EM 2 CAMPOS NO MESMO MODAL
# ============================================================

PERICIAS_PARTE_1 = ORDEM_PERICIAS[:12]
PERICIAS_PARTE_2 = ORDEM_PERICIAS[12:]


# ============================================================
# FUNÇÕES AUXILIARES — NPCS
# ============================================================

def buscar_npcs_canal(channel_id):

    cursor.execute("""
        SELECT id, nome
        FROM fichas
        WHERE channel_id = ?
        AND tipo = 'npc'
        ORDER BY nome COLLATE NOCASE, id
    """, (
        channel_id,
    ))

    return cursor.fetchall()


def buscar_npc_completo(
    channel_id,
    npc_id
):

    cursor.execute("""
        SELECT *
        FROM fichas
        WHERE channel_id = ?
        AND tipo = 'npc'
        AND id = ?
        LIMIT 1
    """, (
        channel_id,
        npc_id
    ))

    return cursor.fetchone()


def nome_visual_npc(
    npc_id,
    nome
):

    return f"{nome} #{npc_id}"


def total_paginas(lista):

    if not lista:
        return 1

    return (
        len(lista)
        + NPCS_POR_PAGINA
        - 1
    ) // NPCS_POR_PAGINA


def obter_pagina(
    lista,
    pagina
):

    inicio = (
        pagina
        * NPCS_POR_PAGINA
    )

    fim = (
        inicio
        + NPCS_POR_PAGINA
    )

    return lista[
        inicio:fim
    ]


# ============================================================
# MONTAR TEXTO DOS ATRIBUTOS
# ============================================================

def montar_texto_atributos(
    sessao
):

    linhas = []

    for chave in ATRIBUTOS:

        nome = NOMES_ATRIBUTOS[
            chave
        ]

        valor = sessao.atributos.get(
            chave,
            0
        )

        linhas.append(
            f"{nome}: {valor}"
        )

    return "\n".join(
        linhas
    )


# ============================================================
# MONTAR TEXTO DAS PERÍCIAS
# ============================================================

def montar_texto_pericias(
    sessao,
    chaves
):

    linhas = []

    for chave in chaves:

        emoji, nome = PERICIAS[
            chave
        ]

        valor = sessao.pericias.get(
            chave,
            0
        )

        linhas.append(
            f"{nome}: {valor}"
        )

    return "\n".join(
        linhas
    )


# ============================================================
# INTERPRETAR CAMPO MULTILINHA
# ============================================================

def interpretar_lista_valores(
    texto,
    chaves
):

    linhas = [
        linha.strip()
        for linha in texto.splitlines()
        if linha.strip()
    ]

    if len(linhas) != len(chaves):
        return None

    resultado = {}

    for chave, linha in zip(
        chaves,
        linhas
    ):

        if ":" in linha:

            valor_texto = linha.rsplit(
                ":",
                1
            )[1].strip()

        else:

            valor_texto = linha.strip()

        try:

            valor = int(
                valor_texto
            )

        except ValueError:

            return None

        if valor < 0:
            return None

        resultado[
            chave
        ] = valor

    return resultado


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

class ViewSessao(
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
                "❌ Somente quem iniciou esta ação "
                "pode usar estes controles.",
                ephemeral=True
            )

            return False

        return True


# ============================================================
# VIEW BASE PARA AÇÕES DE UM USUÁRIO
# ============================================================

class ViewUsuario(
    discord.ui.View
):

    def __init__(
        self,
        usuario_id,
        timeout=300
    ):

        super().__init__(
            timeout=timeout
        )

        self.usuario_id = usuario_id


    async def interaction_check(
        self,
        interaction: discord.Interaction
    ):

        if (
            interaction.user.id
            != self.usuario_id
        ):

            await interaction.response.send_message(
                "❌ Somente quem iniciou esta ação "
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

    npc_id = cursor.lastrowid

    # ========================================================
    # CALCULAR RC
    # ========================================================

    rc = (
        sessao.pericias[
            "esquiva"
        ]
        + sessao.atributos[
            "destreza"
        ]
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
        f"👹 NPC **{nome} #{npc_id}** criado com sucesso!\n\n"
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

class ViewDadosBasicos(
    ViewSessao
):

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
# MODAL — DADOS BÁSICOS
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

        nome = self.nome.value.strip()

        if not nome:

            await interaction.response.send_message(
                "❌ O NPC precisa ter um nome.",
                ephemeral=True
            )

            return

        self.sessao.nome = nome[:50]

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

class ViewEscolherAtributos(
    ViewSessao
):

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
            ModalAtributosCompacto(
                self.sessao
            )
        )


# ============================================================
# MODAL COMPACTO — ATRIBUTOS
# ============================================================

class ModalAtributosCompacto(
    discord.ui.Modal
):

    def __init__(
        self,
        sessao
    ):

        super().__init__(
            title="Atributos do NPC"
        )

        self.sessao = sessao

        self.valores = discord.ui.TextInput(
            label="Atributos",
            style=discord.TextStyle.paragraph,
            default=montar_texto_atributos(
                sessao
            ),
            placeholder=(
                "Força: 0\n"
                "Destreza: 0\n"
                "Vigor: 0\n"
                "Inteligência: 0\n"
                "Carisma: 0\n"
                "Raciocínio: 0"
            ),
            required=True,
            max_length=1000
        )

        self.add_item(
            self.valores
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

        valores = interpretar_lista_valores(
            self.valores.value,
            list(
                ATRIBUTOS.keys()
            )
        )

        if valores is None:

            await interaction.response.send_message(
                "❌ Não consegui interpretar os atributos.\n\n"
                "Mantenha as **6 linhas** e altere somente "
                "os números depois dos `:`.\n\n"
                "Exemplo:\n"
                "`Força: 3`\n"
                "`Destreza: 2`\n"
                "`Vigor: 4`",
                ephemeral=True
            )

            return

        self.sessao.atributos = valores

        self.sessao.atributos_aleatorios = False

        await interaction.response.send_message(
            "✅ Todos os atributos foram salvos.\n\n"
            "📚 As **perícias** serão aleatórias?",
            view=ViewEscolherPericias(
                self.sessao
            ),
            ephemeral=True
        )


# ============================================================
# PERÍCIAS ALEATÓRIAS?
# ============================================================

class ViewEscolherPericias(
    ViewSessao
):

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
            ModalPericiasCompacto(
                self.sessao
            )
        )


# ============================================================
# MODAL COMPACTO — PERÍCIAS
# ============================================================

class ModalPericiasCompacto(
    discord.ui.Modal
):

    def __init__(
        self,
        sessao
    ):

        super().__init__(
            title="Perícias do NPC"
        )

        self.sessao = sessao

        self.parte_1 = discord.ui.TextInput(
            label="Perícias — Parte 1",
            style=discord.TextStyle.paragraph,
            default=montar_texto_pericias(
                sessao,
                PERICIAS_PARTE_1
            ),
            required=True,
            max_length=2000
        )

        self.parte_2 = discord.ui.TextInput(
            label="Perícias — Parte 2",
            style=discord.TextStyle.paragraph,
            default=montar_texto_pericias(
                sessao,
                PERICIAS_PARTE_2
            ),
            required=True,
            max_length=2000
        )

        self.add_item(
            self.parte_1
        )

        self.add_item(
            self.parte_2
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

        valores_1 = interpretar_lista_valores(
            self.parte_1.value,
            PERICIAS_PARTE_1
        )

        valores_2 = interpretar_lista_valores(
            self.parte_2.value,
            PERICIAS_PARTE_2
        )

        if (
            valores_1 is None
            or valores_2 is None
        ):

            await interaction.response.send_message(
                "❌ Não consegui interpretar as perícias.\n\n"
                "Mantenha todas as linhas e altere somente "
                "os números depois dos `:`.\n\n"
                "Exemplo:\n"
                "`Acadêmicos: 2`\n"
                "`Idiomas: 0`\n"
                "`Ofícios: 3`",
                ephemeral=True
            )

            return

        self.sessao.pericias = {
            **valores_1,
            **valores_2
        }

        self.sessao.pericias_aleatorias = False

        await finalizar_criacao_npc(
            interaction,
            self.sessao
        )


# ============================================================
# SELECT — VISUALIZAR NPC
# ============================================================

class SelectVisualizarNPC(
    discord.ui.Select
):

    def __init__(
        self,
        view_pai
    ):

        self.view_pai = view_pai

        super().__init__(
            placeholder="👹 Escolha um NPC...",
            min_values=1,
            max_values=1,
            options=[],
            row=0
        )

        self.atualizar_opcoes()


    def atualizar_opcoes(
        self
    ):

        npcs_pagina = obter_pagina(
            self.view_pai.npcs,
            self.view_pai.pagina
        )

        self.options = []

        for npc_id, nome in npcs_pagina:

            self.options.append(
                discord.SelectOption(
                    label=nome_visual_npc(
                        npc_id,
                        nome
                    )[:100],
                    value=str(
                        npc_id
                    ),
                    emoji="👹",
                    description=(
                        f"ID do NPC: {npc_id}"
                    )
                )
            )

        self.placeholder = (
            f"👹 Escolha um NPC "
            f"• Página {self.view_pai.pagina + 1}/"
            f"{self.view_pai.paginas}"
        )


    async def callback(
        self,
        interaction: discord.Interaction
    ):

        npc_id = int(
            self.values[0]
        )

        dados = buscar_npc_completo(
            self.view_pai.channel_id,
            npc_id
        )

        if dados is None:

            await interaction.response.send_message(
                "❌ Este NPC não existe mais.",
                ephemeral=True
            )

            return

        ficha = transformar_ficha(
            dados
        )

        await interaction.response.send_message(
            content=(
                f"👹 **"
                f"{nome_visual_npc(npc_id, ficha['nome'])}"
                f"**"
            ),
            embed=criar_pagina_status(
                ficha
            ),
            view=FichaView(
                ficha
            ),
            ephemeral=True
        )


# ============================================================
# VIEW — LISTA PAGINADA DE NPCS
# ============================================================

class ViewListaNPCs(
    ViewUsuario
):

    def __init__(
        self,
        channel_id,
        usuario_id,
        npcs
    ):

        self.channel_id = channel_id

        self.npcs = npcs

        self.pagina = 0

        self.paginas = total_paginas(
            npcs
        )

        super().__init__(
            usuario_id,
            timeout=300
        )

        self.selector = SelectVisualizarNPC(
            self
        )

        self.add_item(
            self.selector
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

        self.selector.atualizar_opcoes()


    @discord.ui.button(
        label="◀ Anterior",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def anterior(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if self.pagina > 0:

            self.pagina -= 1

        self.atualizar_botoes()

        await interaction.response.edit_message(
            content=(
                f"👹 **NPCs da mesa**\n\n"
                f"Total: **{len(self.npcs)}**\n"
                f"Página **{self.pagina + 1}/{self.paginas}**\n\n"
                "Escolha um NPC para visualizar:"
            ),
            view=self
        )


    @discord.ui.button(
        label="Próxima ▶",
        style=discord.ButtonStyle.secondary,
        row=1
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

        self.atualizar_botoes()

        await interaction.response.edit_message(
            content=(
                f"👹 **NPCs da mesa**\n\n"
                f"Total: **{len(self.npcs)}**\n"
                f"Página **{self.pagina + 1}/{self.paginas}**\n\n"
                "Escolha um NPC para visualizar:"
            ),
            view=self
        )


# ============================================================
# SELECT — APAGAR UM NPC
# ============================================================

class SelectApagarUmNPC(
    discord.ui.Select
):

    def __init__(
        self,
        view_pai
    ):

        self.view_pai = view_pai

        super().__init__(
            placeholder="👹 Selecione o NPC...",
            min_values=1,
            max_values=1,
            options=[],
            row=0
        )

        self.atualizar_opcoes()


    def atualizar_opcoes(
        self
    ):

        pagina_npcs = obter_pagina(
            self.view_pai.npcs,
            self.view_pai.pagina
        )

        self.options = []

        for npc_id, nome in pagina_npcs:

            self.options.append(
                discord.SelectOption(
                    label=nome_visual_npc(
                        npc_id,
                        nome
                    )[:100],
                    value=str(
                        npc_id
                    ),
                    emoji="👹"
                )
            )

        self.placeholder = (
            f"👹 Selecione o NPC "
            f"• Página {self.view_pai.pagina + 1}/"
            f"{self.view_pai.paginas}"
        )


    async def callback(
        self,
        interaction: discord.Interaction
    ):

        npc_id = int(
            self.values[0]
        )

        cursor.execute("""
            SELECT id, nome
            FROM fichas
            WHERE channel_id = ?
            AND tipo = 'npc'
            AND id = ?
            LIMIT 1
        """, (
            self.view_pai.channel_id,
            npc_id
        ))

        resultado = cursor.fetchone()

        if resultado is None:

            await interaction.response.edit_message(
                content="❌ Este NPC não existe mais.",
                view=None
            )

            return

        npc_id, nome = resultado

        await interaction.response.edit_message(
            content=(
                "⚠️ **Confirmar exclusão?**\n\n"
                f"👹 **{nome_visual_npc(npc_id, nome)}**\n\n"
                "Esta ação não poderá ser desfeita."
            ),
            view=ViewConfirmarExclusaoNPCs(
                self.view_pai.channel_id,
                self.view_pai.usuario_id,
                [
                    npc_id
                ]
            )
        )


# ============================================================
# VIEW — APAGAR UM NPC
# ============================================================

class ViewApagarUmNPC(
    ViewUsuario
):

    def __init__(
        self,
        channel_id,
        usuario_id,
        npcs
    ):

        self.channel_id = channel_id

        self.npcs = npcs

        self.pagina = 0

        self.paginas = total_paginas(
            npcs
        )

        super().__init__(
            usuario_id,
            timeout=300
        )

        self.selector = SelectApagarUmNPC(
            self
        )

        self.add_item(
            self.selector
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

        self.selector.atualizar_opcoes()


    @discord.ui.button(
        label="◀ Anterior",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def anterior(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if self.pagina > 0:

            self.pagina -= 1

        self.atualizar_botoes()

        await interaction.response.edit_message(
            content=(
                "👹 **Qual NPC deseja apagar?**\n\n"
                f"Página **{self.pagina + 1}/{self.paginas}**"
            ),
            view=self
        )


    @discord.ui.button(
        label="Próxima ▶",
        style=discord.ButtonStyle.secondary,
        row=1
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

        self.atualizar_botoes()

        await interaction.response.edit_message(
            content=(
                "👹 **Qual NPC deseja apagar?**\n\n"
                f"Página **{self.pagina + 1}/{self.paginas}**"
            ),
            view=self
        )


# ============================================================
# SELECT — APAGAR VÁRIOS NPCS
# ============================================================

class SelectApagarVariosNPCs(
    discord.ui.Select
):

    def __init__(
        self,
        view_pai
    ):

        self.view_pai = view_pai

        super().__init__(
            placeholder="👥 Selecione os NPCs...",
            min_values=1,
            max_values=1,
            options=[],
            row=0
        )

        self.atualizar_opcoes()


    def atualizar_opcoes(
        self
    ):

        pagina_npcs = obter_pagina(
            self.view_pai.npcs,
            self.view_pai.pagina
        )

        self.options = []

        for npc_id, nome in pagina_npcs:

            self.options.append(
                discord.SelectOption(
                    label=nome_visual_npc(
                        npc_id,
                        nome
                    )[:100],
                    value=str(
                        npc_id
                    ),
                    emoji="👹",
                    default=(
                        npc_id
                        in self.view_pai.selecionados
                    )
                )
            )

        quantidade = len(
            self.options
        )

        self.max_values = max(
            1,
            quantidade
        )

        self.placeholder = (
            f"👥 Selecione NPCs "
            f"• Página {self.view_pai.pagina + 1}/"
            f"{self.view_pai.paginas}"
        )


    async def callback(
        self,
        interaction: discord.Interaction
    ):

        pagina_npcs = obter_pagina(
            self.view_pai.npcs,
            self.view_pai.pagina
        )

        ids_pagina = {
            npc_id
            for npc_id, nome in pagina_npcs
        }

        self.view_pai.selecionados.difference_update(
            ids_pagina
        )

        for valor in self.values:

            self.view_pai.selecionados.add(
                int(
                    valor
                )
            )

        self.view_pai.atualizar_botoes()

        await interaction.response.edit_message(
            content=(
                "👥 **Selecione os NPCs que deseja apagar**\n\n"
                f"Página **{self.view_pai.pagina + 1}/"
                f"{self.view_pai.paginas}**\n"
                f"Selecionados: **"
                f"{len(self.view_pai.selecionados)}**\n\n"
                "Você pode trocar de página sem perder "
                "os NPCs já selecionados."
            ),
            view=self.view_pai
        )


# ============================================================
# VIEW — APAGAR VÁRIOS NPCS
# ============================================================

class ViewApagarVariosNPCs(
    ViewUsuario
):

    def __init__(
        self,
        channel_id,
        usuario_id,
        npcs
    ):

        self.channel_id = channel_id

        self.npcs = npcs

        self.pagina = 0

        self.paginas = total_paginas(
            npcs
        )

        self.selecionados = set()

        super().__init__(
            usuario_id,
            timeout=300
        )

        self.selector = SelectApagarVariosNPCs(
            self
        )

        self.add_item(
            self.selector
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

        self.revisar.disabled = (
            len(
                self.selecionados
            )
            == 0
        )

        self.revisar.label = (
            f"Revisar ({len(self.selecionados)})"
        )

        self.selector.atualizar_opcoes()


    @discord.ui.button(
        label="◀ Anterior",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def anterior(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if self.pagina > 0:

            self.pagina -= 1

        self.atualizar_botoes()

        await interaction.response.edit_message(
            content=(
                "👥 **Selecione os NPCs que deseja apagar**\n\n"
                f"Página **{self.pagina + 1}/{self.paginas}**\n"
                f"Selecionados: **{len(self.selecionados)}**"
            ),
            view=self
        )


    @discord.ui.button(
        label="Próxima ▶",
        style=discord.ButtonStyle.secondary,
        row=1
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

        self.atualizar_botoes()

        await interaction.response.edit_message(
            content=(
                "👥 **Selecione os NPCs que deseja apagar**\n\n"
                f"Página **{self.pagina + 1}/{self.paginas}**\n"
                f"Selecionados: **{len(self.selecionados)}**"
            ),
            view=self
        )


    @discord.ui.button(
        label="Revisar (0)",
        emoji="✅",
        style=discord.ButtonStyle.danger,
        row=2
    )
    async def revisar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if not self.selecionados:

            await interaction.response.send_message(
                "❌ Nenhum NPC foi selecionado.",
                ephemeral=True
            )

            return

        ids = sorted(
            self.selecionados
        )

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
            ORDER BY nome COLLATE NOCASE, id
            """,
            [
                self.channel_id
            ] + ids
        )

        resultados = cursor.fetchall()

        if not resultados:

            await interaction.response.edit_message(
                content=(
                    "❌ Os NPCs selecionados "
                    "não existem mais."
                ),
                view=None
            )

            return

        linhas = [
            f"• 👹 **{nome_visual_npc(npc_id, nome)}**"
            for npc_id, nome in resultados
        ]

        limite_exibicao = 25

        exibidas = linhas[
            :limite_exibicao
        ]

        texto = "\n".join(
            exibidas
        )

        restantes = (
            len(linhas)
            - len(exibidas)
        )

        if restantes > 0:

            texto += (
                f"\n• ... e mais "
                f"**{restantes} NPC(s)**"
            )

        await interaction.response.edit_message(
            content=(
                "⚠️ **Confirmar exclusão dos NPCs?**\n\n"
                f"{texto}\n\n"
                f"Total selecionado: "
                f"**{len(resultados)}**\n\n"
                "Esta ação não poderá ser desfeita."
            ),
            view=ViewConfirmarExclusaoNPCs(
                self.channel_id,
                self.usuario_id,
                [
                    npc_id
                    for npc_id, nome
                    in resultados
                ]
            )
        )


    @discord.ui.button(
        label="Limpar seleção",
        emoji="🧹",
        style=discord.ButtonStyle.secondary,
        row=2
    )
    async def limpar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        self.selecionados.clear()

        self.atualizar_botoes()

        await interaction.response.edit_message(
            content=(
                "👥 **Selecione os NPCs que deseja apagar**\n\n"
                f"Página **{self.pagina + 1}/{self.paginas}**\n"
                "Selecionados: **0**"
            ),
            view=self
        )


# ============================================================
# CONFIRMAR EXCLUSÃO DOS NPCS SELECIONADOS
# ============================================================

class ViewConfirmarExclusaoNPCs(
    ViewUsuario
):

    def __init__(
        self,
        channel_id,
        usuario_id,
        ids
    ):

        self.channel_id = channel_id

        self.ids = list(
            dict.fromkeys(
                ids
            )
        )

        super().__init__(
            usuario_id,
            timeout=300
        )


    @discord.ui.button(
        label="Confirmar exclusão",
        emoji="🗑️",
        style=discord.ButtonStyle.danger
    )
    async def confirmar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if not self.ids:

            await interaction.response.edit_message(
                content="❌ Nenhum NPC selecionado.",
                view=None
            )

            return

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
            ORDER BY nome COLLATE NOCASE, id
            """,
            [
                self.channel_id
            ] + self.ids
        )

        encontrados = cursor.fetchall()

        if not encontrados:

            await interaction.response.edit_message(
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
                self.channel_id
            ] + ids_validos
        )

        db.commit()

        if len(encontrados) == 1:

            npc_id, nome = encontrados[
                0
            ]

            mensagem = (
                f"🗑️ NPC **"
                f"{nome_visual_npc(npc_id, nome)}** "
                f"apagado com sucesso."
            )

        else:

            mensagem = (
                f"🗑️ **{len(encontrados)} NPCs** "
                f"apagados com sucesso."
            )

        await interaction.response.edit_message(
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
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.edit_message(
            content=(
                "❎ Exclusão cancelada. "
                "Nenhum NPC foi apagado."
            ),
            view=None
        )


# ============================================================
# CONFIRMAR EXCLUSÃO DE TODOS OS NPCS
# ============================================================

class ViewConfirmarTodosNPCs(
    ViewUsuario
):

    def __init__(
        self,
        channel_id,
        usuario_id
    ):

        self.channel_id = channel_id

        super().__init__(
            usuario_id,
            timeout=300
        )


    @discord.ui.button(
        label="Sim, apagar todos",
        emoji="🗑️",
        style=discord.ButtonStyle.danger
    )
    async def confirmar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        cursor.execute("""
            SELECT COUNT(*)
            FROM fichas
            WHERE channel_id = ?
            AND tipo = 'npc'
        """, (
            self.channel_id,
        ))

        quantidade = cursor.fetchone()[
            0
        ]

        if quantidade == 0:

            await interaction.response.edit_message(
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
            self.channel_id,
        ))

        db.commit()

        await interaction.response.edit_message(
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
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.edit_message(
            content=(
                "❎ Exclusão cancelada. "
                "Nenhum NPC foi apagado."
            ),
            view=None
        )


# ============================================================
# MENU INICIAL DE EXCLUSÃO
# ============================================================

class ViewModoExclusao(
    ViewUsuario
):

    def __init__(
        self,
        channel_id,
        usuario_id,
        npcs
    ):

        self.channel_id = channel_id

        self.npcs = npcs

        super().__init__(
            usuario_id,
            timeout=300
        )


    @discord.ui.button(
        label="Um NPC",
        emoji="👹",
        style=discord.ButtonStyle.primary
    )
    async def um_npc(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        paginas = total_paginas(
            self.npcs
        )

        await interaction.response.edit_message(
            content=(
                "👹 **Qual NPC deseja apagar?**\n\n"
                f"Página **1/{paginas}**"
            ),
            view=ViewApagarUmNPC(
                self.channel_id,
                self.usuario_id,
                self.npcs
            )
        )


    @discord.ui.button(
        label="Vários NPCs",
        emoji="👥",
        style=discord.ButtonStyle.secondary
    )
    async def varios_npcs(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        paginas = total_paginas(
            self.npcs
        )

        await interaction.response.edit_message(
            content=(
                "👥 **Selecione os NPCs que deseja apagar**\n\n"
                f"Página **1/{paginas}**\n"
                "Selecionados: **0**\n\n"
                "Você pode selecionar NPCs "
                "e trocar de página."
            ),
            view=ViewApagarVariosNPCs(
                self.channel_id,
                self.usuario_id,
                self.npcs
            )
        )


    @discord.ui.button(
        label="Todos",
        emoji="⚠️",
        style=discord.ButtonStyle.danger
    )
    async def todos(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        cursor.execute("""
            SELECT COUNT(*)
            FROM fichas
            WHERE channel_id = ?
            AND tipo = 'npc'
        """, (
            self.channel_id,
        ))

        quantidade = cursor.fetchone()[
            0
        ]

        if quantidade == 0:

            await interaction.response.edit_message(
                content=(
                    "👹 Não existem mais NPCs "
                    "nesta mesa."
                ),
                view=None
            )

            return

        await interaction.response.edit_message(
            content=(
                "⚠️ **ATENÇÃO**\n\n"
                f"Você está prestes a apagar "
                f"**{quantidade} NPC(s)** desta mesa.\n\n"
                "Esta ação não poderá ser desfeita.\n\n"
                "Deseja continuar?"
            ),
            view=ViewConfirmarTodosNPCs(
                self.channel_id,
                self.usuario_id
            )
        )


# ============================================================
# REGISTRAR COMANDOS DO MESTRE
# ============================================================

def registrar_comandos_mestre(
    bot
):

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

        if not eh_admin(
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

        mestre_id = obter_mestre(
            interaction.channel.id
        )

        if (
            interaction.user.id
            != mestre_id
            and not eh_admin(
                interaction
            )
        ):

            await interaction.response.send_message(
                "❌ Somente o Mestre atual ou um administrador "
                "pode fazer isso.",
                ephemeral=True
            )

            return

        if (
            jogador.id
            == mestre_id
        ):

            await interaction.response.send_message(
                "❌ Este jogador já é o Mestre.",
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
            not eh_mestre(
                interaction
            )
            and not eh_admin(
                interaction
            )
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
    # LISTAR / VISUALIZAR NPCS
    # ========================================================

    @bot.tree.command(
        name="npcs",
        description="Mostra os NPCs da mesa."
    )
    async def npcs(
        interaction: discord.Interaction
    ):

        if (
            not eh_mestre(
                interaction
            )
            and not eh_admin(
                interaction
            )
        ):

            await interaction.response.send_message(
                "❌ Somente o Mestre ou um administrador "
                "pode visualizar os NPCs.",
                ephemeral=True
            )

            return

        resultados = buscar_npcs_canal(
            interaction.channel.id
        )

        if not resultados:

            await interaction.response.send_message(
                "👹 Não existem NPCs neste canal.",
                ephemeral=True
            )

            return

        paginas = total_paginas(
            resultados
        )

        await interaction.response.send_message(
            f"👹 **NPCs da mesa**\n\n"
            f"Total: **{len(resultados)}**\n"
            f"Página **1/{paginas}**\n\n"
            "Escolha um NPC para visualizar:",
            view=ViewListaNPCs(
                interaction.channel.id,
                interaction.user.id,
                resultados
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
            not eh_mestre(
                interaction
            )
            and not eh_admin(
                interaction
            )
        ):

            await interaction.response.send_message(
                "❌ Somente o Mestre ou um administrador "
                "pode apagar NPCs.",
                ephemeral=True
            )

            return

        resultados = buscar_npcs_canal(
            interaction.channel.id
        )

        if not resultados:

            await interaction.response.send_message(
                "👹 Não existem NPCs neste canal.",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "🗑️ **Gerenciamento de exclusão de NPCs**\n\n"
            f"Existem **{len(resultados)} NPC(s)** "
            f"nesta mesa.\n\n"
            "O que deseja apagar?",
            view=ViewModoExclusao(
                interaction.channel.id,
                interaction.user.id,
                resultados
            ),
            ephemeral=True
        )
