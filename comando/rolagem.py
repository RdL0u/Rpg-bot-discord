import discord

from database import (
    buscar_ficha_jogador,
    registrar_historico,
)

from fichas import (
    transformar_ficha,
)

from config import (
    ATRIBUTOS,
    PERICIAS,
    ORDEM_PERICIAS,
)

from rolagens import (
    realizar_rolagem,
    formatar_rolagem,
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
# SESSÃO DA ROLAGEM
# ============================================================

class SessaoRolagem:

    def __init__(
        self,
        channel_id,
        usuario_id
    ):

        self.channel_id = channel_id
        self.usuario_id = usuario_id

        self.atributo = None
        self.pericia = None


# ============================================================
# TEXTO DO PAINEL
# ============================================================

def criar_texto_painel(
    sessao
):

    if sessao.atributo is None:

        atributo_texto = (
            "❔ Não selecionado"
        )

    else:

        emoji, _ = ATRIBUTOS[
            sessao.atributo
        ]

        atributo_texto = (
            f"{emoji} "
            f"{NOMES_ATRIBUTOS[sessao.atributo]}"
        )

    if sessao.pericia is None:

        pericia_texto = (
            "❔ Não selecionada"
        )

    else:

        emoji, nome = PERICIAS[
            sessao.pericia
        ]

        pericia_texto = (
            f"{emoji} {nome}"
        )

    return (
        "🎲 **NOVA ROLAGEM**\n\n"
        f"⚔️ Atributo:\n"
        f"{atributo_texto}\n\n"
        f"📚 Perícia:\n"
        f"{pericia_texto}\n\n"
        "Selecione um atributo e uma perícia "
        "e depois pressione **🎲 Rolar**."
    )


# ============================================================
# SELECT DE ATRIBUTO
# ============================================================

class AtributoSelect(
    discord.ui.Select
):

    def __init__(
        self,
        view_rolagem
    ):

        self.view_rolagem = (
            view_rolagem
        )

        opcoes = []

        for chave, (
            emoji,
            abreviacao
        ) in ATRIBUTOS.items():

            opcoes.append(
                discord.SelectOption(
                    label=NOMES_ATRIBUTOS[
                        chave
                    ],
                    value=chave,
                    emoji=emoji,
                    description=(
                        f"Atributo {abreviacao}"
                    )
                )
            )

        super().__init__(
            placeholder=(
                "Escolha um atributo..."
            ),
            min_values=1,
            max_values=1,
            options=opcoes,
            row=0
        )


    async def callback(
        self,
        interaction: discord.Interaction
    ):

        self.view_rolagem.sessao.atributo = (
            self.values[0]
        )

        self.view_rolagem.atualizar_botao()

        await interaction.response.edit_message(
            content=criar_texto_painel(
                self.view_rolagem.sessao
            ),
            view=self.view_rolagem
        )


# ============================================================
# SELECT DE PERÍCIA
# ============================================================

class PericiaSelect(
    discord.ui.Select
):

    def __init__(
        self,
        view_rolagem
    ):

        self.view_rolagem = (
            view_rolagem
        )

        opcoes = []

        for chave in ORDEM_PERICIAS:

            emoji, nome = PERICIAS[
                chave
            ]

            opcoes.append(
                discord.SelectOption(
                    label=nome[:100],
                    value=chave,
                    emoji=emoji
                )
            )

        super().__init__(
            placeholder=(
                "Escolha uma perícia..."
            ),
            min_values=1,
            max_values=1,
            options=opcoes,
            row=1
        )


    async def callback(
        self,
        interaction: discord.Interaction
    ):

        self.view_rolagem.sessao.pericia = (
            self.values[0]
        )

        self.view_rolagem.atualizar_botao()

        await interaction.response.edit_message(
            content=criar_texto_painel(
                self.view_rolagem.sessao
            ),
            view=self.view_rolagem
        )


# ============================================================
# VIEW DA ROLAGEM
# ============================================================

class RolagemView(
    discord.ui.View
):

    def __init__(
        self,
        sessao
    ):

        super().__init__(
            timeout=300
        )

        self.sessao = sessao

        self.add_item(
            AtributoSelect(
                self
            )
        )

        self.add_item(
            PericiaSelect(
                self
            )
        )

        self.atualizar_botao()


    # ========================================================
    # SOMENTE QUEM ABRIU PODE USAR
    # ========================================================

    async def interaction_check(
        self,
        interaction: discord.Interaction
    ):

        if (
            interaction.user.id
            != self.sessao.usuario_id
        ):

            await interaction.response.send_message(
                "❌ Somente quem iniciou esta rolagem "
                "pode usar estes controles.",
                ephemeral=True
            )

            return False

        return True


    # ========================================================
    # HABILITAR / DESABILITAR ROLAR
    # ========================================================

    def atualizar_botao(
        self
    ):

        self.rolar_button.disabled = (
            self.sessao.atributo is None
            or
            self.sessao.pericia is None
        )


    # ========================================================
    # BOTÃO ROLAR
    # ========================================================

    @discord.ui.button(
        label="Rolar",
        emoji="🎲",
        style=discord.ButtonStyle.success,
        row=2,
        disabled=True
    )
    async def rolar_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        # ====================================================
        # GARANTIR QUE AS OPÇÕES EXISTEM
        # ====================================================

        if (
            self.sessao.atributo is None
            or
            self.sessao.pericia is None
        ):

            await interaction.response.send_message(
                "❌ Escolha um atributo e uma perícia.",
                ephemeral=True
            )

            return

        # ====================================================
        # BUSCAR FICHA ATUALIZADA
        # ====================================================

        dados = buscar_ficha_jogador(
            interaction.channel.id,
            interaction.user.id
        )

        if dados is None:

            await interaction.response.edit_message(
                content=(
                    "❌ Você não possui uma ficha "
                    "neste canal."
                ),
                view=None
            )

            self.stop()

            return

        ficha = transformar_ficha(
            dados
        )

        # ====================================================
        # ATRIBUTO
        # ====================================================

        chave_atributo = (
            self.sessao.atributo
        )

        emoji_atributo, _ = (
            ATRIBUTOS[
                chave_atributo
            ]
        )

        nome_atributo = (
            NOMES_ATRIBUTOS[
                chave_atributo
            ]
        )

        valor_atributo = int(
            ficha.get(
                chave_atributo,
                0
            )
            or 0
        )

        # ====================================================
        # PERÍCIA
        # ====================================================

        chave_pericia = (
            self.sessao.pericia
        )

        emoji_pericia, nome_pericia = (
            PERICIAS[
                chave_pericia
            ]
        )

        valor_pericia = int(
            ficha.get(
                chave_pericia,
                0
            )
            or 0
        )

        # ====================================================
        # REALIZAR ROLAGEM
        # ====================================================

        dados_rolagem = realizar_rolagem(
            valor_atributo,
            valor_pericia
        )

        texto_resultado = formatar_rolagem(
            nome_jogador=(
                interaction.user.display_name
            ),
            nome_atributo=nome_atributo,
            emoji_atributo=emoji_atributo,
            nome_pericia=nome_pericia,
            emoji_pericia=emoji_pericia,
            dados_rolagem=dados_rolagem
        )

        # ====================================================
        # DADOS DA ROLAGEM
        # ====================================================

        dado_1 = dados_rolagem[
            "dado_1"
        ]

        dado_2 = dados_rolagem[
            "dado_2"
        ]

        modificador = dados_rolagem[
            "modificador"
        ]

        resultado = dados_rolagem[
            "resultado"
        ]

        # ====================================================
        # REGISTRAR NO HISTÓRICO
        # ====================================================

        descricao_historico = (
            f"{emoji_atributo} {nome_atributo}: "
            f"{valor_atributo}\n"
            f"{emoji_pericia} {nome_pericia}: "
            f"{valor_pericia}\n"
            f"🎲 Dados: {dado_1} + {dado_2}\n"
            f"➕ Modificador: {modificador}\n"
            f"🏁 Resultado: {resultado}"
        )

        registrar_historico(
            interaction.channel.id,
            ficha["id"],
            ficha["nome"],
            "jogador",
            interaction.user.id,
            "rolagem",
            campo="rolagem",
            valor_anterior=None,
            valor_novo=str(
                resultado
            ),
            descricao=descricao_historico
        )

        # ====================================================
        # FECHAR PAINEL PRIVADO
        # ====================================================

        await interaction.response.edit_message(
            content=(
                "✅ Rolagem realizada!\n\n"
                "🎲 O resultado foi publicado "
                "no canal."
            ),
            view=None
        )

        # ====================================================
        # PUBLICAR RESULTADO
        # ====================================================

        if interaction.channel is not None:

            await interaction.channel.send(
                texto_resultado
            )

        self.stop()


# ============================================================
# REGISTRAR COMANDO
# ============================================================

def registrar_comandos_rolagem(
    bot
):

    @bot.tree.command(
        name="rolar",
        description=(
            "Realiza uma rolagem de 2d10 "
            "usando atributo e perícia."
        )
    )
    async def rolar(
        interaction: discord.Interaction
    ):

        # ====================================================
        # PRECISA ESTAR EM UM CANAL
        # ====================================================

        if interaction.channel is None:

            await interaction.response.send_message(
                "❌ Este comando precisa ser usado "
                "dentro de uma mesa.",
                ephemeral=True
            )

            return

        # ====================================================
        # VERIFICAR FICHA
        # ====================================================

        dados = buscar_ficha_jogador(
            interaction.channel.id,
            interaction.user.id
        )

        if dados is None:

            await interaction.response.send_message(
                "❌ Você precisa possuir uma ficha "
                "neste canal para realizar uma rolagem.",
                ephemeral=True
            )

            return

        # ====================================================
        # CRIAR SESSÃO
        # ====================================================

        sessao = SessaoRolagem(
            interaction.channel.id,
            interaction.user.id
        )

        view = RolagemView(
            sessao
        )

        # ====================================================
        # ABRIR PAINEL PRIVADO
        # ====================================================

        await interaction.response.send_message(
            criar_texto_painel(
                sessao
            ),
            view=view,
            ephemeral=True
        )
