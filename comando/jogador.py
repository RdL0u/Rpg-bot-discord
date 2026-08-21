 import discord

from discord import app_commands

from database import (
    db,
    cursor,
    garantir_mesa,
    obter_mestre,
    buscar_ficha_jogador,
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
    PERICIAS
)


# ============================================================
# PERMISSÕES
# ============================================================

def eh_admin(interaction):

    if interaction.guild is None:
        return False

    return interaction.user.guild_permissions.administrator


def eh_mestre(interaction):

    if interaction.channel is None:
        return False

    return (
        obter_mestre(
            interaction.channel.id
        )
        == interaction.user.id
    )


# ============================================================
# BUSCAR FICHA PELO ID NO CANAL
# ============================================================

def buscar_ficha_por_id(
    channel_id,
    ficha_id
):

    cursor.execute("""
        SELECT *
        FROM fichas
        WHERE id = ?
        AND channel_id = ?
        LIMIT 1
    """, (
        ficha_id,
        channel_id
    ))

    return cursor.fetchone()


# ============================================================
# MODAL — APLICAR DANO
# ============================================================

class DanoModal(
    discord.ui.Modal
):

    def __init__(
        self,
        ficha_id,
        autor_id
    ):

        super().__init__(
            title="Aplicar dano"
        )

        self.ficha_id = ficha_id
        self.autor_id = autor_id

        self.valor = discord.ui.TextInput(
            label="Quantidade de dano",
            placeholder="Digite o valor do dano",
            required=True,
            max_length=10
        )

        self.add_item(
            self.valor
        )


    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        # ====================================================
        # SOMENTE QUEM INICIOU PODE CONTINUAR
        # ====================================================

        if (
            interaction.user.id
            != self.autor_id
        ):

            await interaction.response.send_message(
                "❌ Somente quem iniciou a ação "
                "pode aplicar o dano.",
                ephemeral=True
            )

            return

        # ====================================================
        # VALIDAR VALOR
        # ====================================================

        try:

            valor = int(
                self.valor.value
            )

        except ValueError:

            await interaction.response.send_message(
                "❌ O dano precisa ser um número inteiro.",
                ephemeral=True
            )

            return

        if valor <= 0:

            await interaction.response.send_message(
                "❌ O dano precisa ser maior que 0.",
                ephemeral=True
            )

            return

        # ====================================================
        # BUSCAR FICHA NOVAMENTE
        # ====================================================

        dados = buscar_ficha_por_id(
            interaction.channel.id,
            self.ficha_id
        )

        if dados is None:

            await interaction.response.send_message(
                "❌ Essa ficha não existe mais.",
                ephemeral=True
            )

            return

        f = transformar_ficha(
            dados
        )

        # ====================================================
        # CALCULAR DANO
        # ====================================================

        hp_anterior = f[
            "hp_atual"
        ]

        novo_hp = max(
            0,
            hp_anterior - valor
        )

        dano_real = (
            hp_anterior - novo_hp
        )

        # ====================================================
        # NPC DERROTADO
        # ====================================================

        if (
            f["tipo"] == "npc"
            and novo_hp <= 0
        ):

            cursor.execute("""
                DELETE FROM fichas
                WHERE id = ?
                AND channel_id = ?
                AND tipo = 'npc'
            """, (
                f["id"],
                interaction.channel.id
            ))

            db.commit()

            await interaction.response.send_message(
                f"💀 **NPC DERROTADO**\n\n"
                f"**{f['nome']} #{f['id']}** recebeu "
                f"**{dano_real} de dano**.\n\n"
                f"❤️ **HP**\n"
                f"**{hp_anterior}/{f['hp_max']}** "
                f"→ "
                f"**0/{f['hp_max']}**\n"
                f"💀 **DERROTADO**\n\n"
                f"🗑️ NPC removido da mesa."
            )

            return

        # ====================================================
        # ATUALIZAR HP
        # ====================================================

        cursor.execute("""
            UPDATE fichas
            SET hp_atual = ?
            WHERE id = ?
            AND channel_id = ?
        """, (
            novo_hp,
            f["id"],
            interaction.channel.id
        ))

        db.commit()

        estado = estado_hp(
            novo_hp,
            f["hp_max"]
        )

        # ====================================================
        # NOME VISUAL
        # ====================================================

        if f["tipo"] == "npc":

            nome_visual = (
                f"{f['nome']} #{f['id']}"
            )

        else:

            nome_visual = f[
                "nome"
            ]

        # ====================================================
        # RESPOSTA
        # ====================================================

        await interaction.response.send_message(
            f"💥 **DANO**\n\n"
            f"**{nome_visual}** recebeu "
            f"**{dano_real} de dano**.\n\n"
            f"❤️ **HP**\n"
            f"**{hp_anterior}/{f['hp_max']}** "
            f"→ "
            f"**{novo_hp}/{f['hp_max']}**\n"
            f"{estado}"
        )


# ============================================================
# SELECT — ESCOLHER ALVO DO DANO
# ============================================================

class DanoAlvoSelect(
    discord.ui.Select
):

    def __init__(
        self,
        interaction
    ):

        self.autor_id = (
            interaction.user.id
        )

        cursor.execute("""
            SELECT
                id,
                nome,
                tipo
            FROM fichas
            WHERE channel_id = ?
            ORDER BY
                tipo,
                nome COLLATE NOCASE,
                id
            LIMIT 25
        """, (
            interaction.channel.id,
        ))

        resultados = cursor.fetchall()

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

                descricao = (
                    f"NPC • ID {ficha_id}"
                )

            else:

                label = nome

                emoji = "👤"

                descricao = "Jogador"

            opcoes.append(
                discord.SelectOption(
                    label=label[:100],
                    value=str(
                        ficha_id
                    ),
                    emoji=emoji,
                    description=descricao[:100]
                )
            )

        super().__init__(
            placeholder="Escolha quem receberá o dano...",
            min_values=1,
            max_values=1,
            options=opcoes
        )


    async def callback(
        self,
        interaction: discord.Interaction
    ):

        if (
            interaction.user.id
            != self.autor_id
        ):

            await interaction.response.send_message(
                "❌ Somente quem iniciou a ação "
                "pode escolher o alvo.",
                ephemeral=True
            )

            return

        ficha_id = int(
            self.values[0]
        )

        dados = buscar_ficha_por_id(
            interaction.channel.id,
            ficha_id
        )

        if dados is None:

            await interaction.response.send_message(
                "❌ Essa ficha não existe mais.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            DanoModal(
                ficha_id,
                self.autor_id
            )
        )


# ============================================================
# VIEW — ESCOLHER ALVO DO DANO
# ============================================================

class DanoAlvoView(
    discord.ui.View
):

    def __init__(
        self,
        interaction
    ):

        super().__init__(
            timeout=120
        )

        self.add_item(
            DanoAlvoSelect(
                interaction
            )
        )


# ============================================================
# REGISTRAR COMANDOS DE JOGADOR
# ============================================================

def registrar_comandos_jogador(bot):

    # ========================================================
    # CRIAR FICHA
    # ========================================================

    @bot.tree.command(
        name="criarficha",
        description="Cria sua ficha neste canal."
    )
    @app_commands.describe(
        nome="Nome do personagem",
        hp="HP inicial e máximo",
        mana="Mana inicial e máxima"
    )
    async def criarficha(
        interaction: discord.Interaction,
        nome: str,
        hp: int,
        mana: int
    ):

        garantir_mesa(
            interaction.channel.id
        )

        existente = buscar_ficha_jogador(
            interaction.channel.id,
            interaction.user.id
        )

        if existente:

            await interaction.response.send_message(
                "⚠️ Você já possui uma ficha neste canal.",
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

        nome = nome[:50]

        cursor.execute("""
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
                forca,
                destreza,
                vigor,
                inteligencia,
                carisma,
                raciocinio,
                aleatorio
            )
            VALUES (
                ?, ?, NULL, 'jogador', ?,
                ?, ?, ?, ?, 0,
                0, 0, 0, 0, 0, 0, 0
            )
        """, (
            interaction.channel.id,
            interaction.user.id,
            nome,
            hp,
            hp,
            mana,
            mana
        ))

        db.commit()

        estado_inicial_hp = estado_hp(
            hp,
            hp
        )

        estado_inicial_mana = estado_mana(
            mana,
            mana
        )

        await interaction.response.send_message(
            f"📜 Ficha de **{nome}** criada!\n\n"
            f"❤️ HP: **{hp}/{hp}** • "
            f"{estado_inicial_hp}\n"
            f"🔵 Mana: **{mana}/{mana}** • "
            f"{estado_inicial_mana}\n"
            f"✨ XP: **0**\n"
            f"⚡ RC: **5**"
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
    # VER FICHA DE OUTRO JOGADOR
    # ========================================================

    @bot.tree.command(
        name="verficha",
        description="Visualiza a ficha de outro jogador."
    )
    @app_commands.describe(
        jogador="Jogador cuja ficha você deseja visualizar"
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
    # ALTERAR ATRIBUTO
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
            )
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

        await interaction.response.send_message(
            f"⚔️ **{ATRIBUTOS[atributo.value][1]}** "
            f"alterado para **{valor}**!"
        )

    # ========================================================
    # ALTERAR PERÍCIA
    # ========================================================

    @bot.tree.command(
        name="pericia",
        description="Define ou altera uma perícia da sua ficha."
    )
    @app_commands.describe(
        pericia="Perícia",
        valor="Novo valor"
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
            )
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

        if valor < 0:

            await interaction.response.send_message(
                "❌ O valor não pode ser negativo.",
                ephemeral=True
            )

            return

        f = transformar_ficha(
            dados
        )

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

        await interaction.response.send_message(
            f"📚 **{PERICIAS[pericia.value][1]}** "
            f"alterada para **{valor}**!"
        )

    # ========================================================
    # ALTERAR HP E MANA
    # ========================================================

    @bot.tree.command(
        name="alterarficha",
        description="Altera HP e Mana máximos de um jogador."
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
                "❌ Esse jogador não possui uma ficha.",
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
                "❌ Você não pode alterar essa ficha.",
                ephemeral=True
            )

            return

        if (
            hp <= 0
            or mana < 0
        ):

            await interaction.response.send_message(
                "❌ Valores inválidos.",
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
            hp,
            hp,
            mana,
            mana,
            f["id"]
        ))

        db.commit()

        estado_atual_hp = estado_hp(
            hp,
            hp
        )

        estado_atual_mana = estado_mana(
            mana,
            mana
        )

        await interaction.response.send_message(
            f"⚙️ **FICHA ATUALIZADA**\n\n"
            f"**{f['nome']}**\n\n"
            f"❤️ **HP**\n"
            f"**{hp}/{hp}**\n"
            f"{estado_atual_hp}\n\n"
            f"🔵 **Mana**\n"
            f"**{mana}/{mana}**\n"
            f"{estado_atual_mana}"
        )

    # ========================================================
    # APAGAR FICHA
    # ========================================================

    @bot.tree.command(
        name="apagarficha",
        description="Apaga sua ficha."
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

        cursor.execute("""
            DELETE FROM fichas
            WHERE id = ?
        """, (
            f["id"],
        ))

        db.commit()

        await interaction.response.send_message(
            f"🗑️ A ficha **{f['nome']}** foi apagada."
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
            SELECT COUNT(*)
            FROM fichas
            WHERE channel_id = ?
        """, (
            interaction.channel.id,
        ))

        quantidade = cursor.fetchone()[0]

        if quantidade <= 0:

            await interaction.response.send_message(
                "❌ Não existem fichas neste canal.",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "💥 **Escolha quem receberá o dano:**",
            view=DanoAlvoView(
                interaction
            ),
            ephemeral=True
        )

    # ========================================================
    # CURA
    # ========================================================

    @bot.tree.command(
        name="cura",
        description="Cura um jogador."
    )
    @app_commands.describe(
        jogador="Jogador que receberá a cura",
        valor="Quantidade de cura"
    )
    async def cura(
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

        if valor <= 0:

            await interaction.response.send_message(
                "❌ A cura precisa ser maior que 0.",
                ephemeral=True
            )

            return

        f = transformar_ficha(
            dados
        )

        hp_anterior = f[
            "hp_atual"
        ]

        novo_hp = min(
            f["hp_max"],
            hp_anterior + valor
        )

        recuperado = (
            novo_hp - hp_anterior
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

        estado = estado_hp(
            novo_hp,
            f["hp_max"]
        )

        await interaction.response.send_message(
            f"💚 **CURA**\n\n"
            f"**{f['nome']}** recuperou "
            f"**{recuperado} de HP**.\n\n"
            f"❤️ **HP**\n"
            f"**{hp_anterior}/{f['hp_max']}** "
            f"→ "
            f"**{novo_hp}/{f['hp_max']}**\n"
            f"{estado}"
        )

    # ========================================================
    # GASTAR MANA
    # ========================================================

    @bot.tree.command(
        name="gastarmana",
        description="Gasta Mana da sua própria ficha."
    )
    @app_commands.describe(
        valor="Quantidade de Mana"
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
                "❌ Você não possui uma ficha.",
                ephemeral=True
            )

            return

        f = transformar_ficha(
            dados
        )

        if valor <= 0:

            await interaction.response.send_message(
                "❌ O valor precisa ser maior que 0.",
                ephemeral=True
            )

            return

        if valor > f["mana_atual"]:

            estado_atual = estado_mana(
                f["mana_atual"],
                f["mana_max"]
            )

            await interaction.response.send_message(
                f"❌ **MANA INSUFICIENTE**\n\n"
                f"🔵 **Mana**\n"
                f"**{f['mana_atual']}/{f['mana_max']}**\n"
                f"{estado_atual}",
                ephemeral=True
            )

            return

        mana_anterior = f[
            "mana_atual"
        ]

        nova_mana = (
            mana_anterior - valor
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

        estado = estado_mana(
            nova_mana,
            f["mana_max"]
        )

        await interaction.response.send_message(
            f"🔮 **MANA CONSUMIDA**\n\n"
            f"**{f['nome']}** gastou "
            f"**{valor} de Mana**.\n\n"
            f"🔵 **Mana**\n"
            f"**{mana_anterior}/{f['mana_max']}** "
            f"→ "
            f"**{nova_mana}/{f['mana_max']}**\n"
            f"{estado}"
        )

    # ========================================================
    # RECUPERAR MANA
    # ========================================================

    @bot.tree.command(
        name="recuperarmana",
        description="Recupera Mana de um jogador."
    )
    @app_commands.describe(
        jogador="Jogador que recuperará Mana",
        valor="Quantidade de Mana"
    )
    async def recuperarmana(
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

        if valor <= 0:

            await interaction.response.send_message(
                "❌ O valor precisa ser maior que 0.",
                ephemeral=True
            )

            return

        f = transformar_ficha(
            dados
        )

        mana_anterior = f[
            "mana_atual"
        ]

        nova_mana = min(
            f["mana_max"],
            mana_anterior + valor
        )

        recuperado = (
            nova_mana - mana_anterior
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

        estado = estado_mana(
            nova_mana,
            f["mana_max"]
        )

        await interaction.response.send_message(
            f"💧 **MANA RECUPERADA**\n\n"
            f"**{f['nome']}** recuperou "
            f"**{recuperado} de Mana**.\n\n"
            f"🔵 **Mana**\n"
            f"**{mana_anterior}/{f['mana_max']}** "
            f"→ "
            f"**{nova_mana}/{f['mana_max']}**\n"
            f"{estado}"
        )

    # ========================================================
    # XP
    # ========================================================

    @bot.tree.command(
        name="addxp",
        description="Adiciona XP a uma ficha."
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

        if (
            f["dono_id"]
            != interaction.user.id
            and not eh_admin(
                interaction
            )
            and not eh_mestre(
                interaction
            )
        ):

            await interaction.response.send_message(
                "❌ Você não pode alterar o XP dessa ficha.",
                ephemeral=True
            )

            return

        if valor <= 0:

            await interaction.response.send_message(
                "❌ O XP precisa ser maior que 0.",
                ephemeral=True
            )

            return

        cursor.execute("""
            UPDATE fichas
            SET xp = xp + ?
            WHERE id = ?
        """, (
            valor,
            f["id"]
        ))

        db.commit()

        cursor.execute("""
            SELECT xp
            FROM fichas
            WHERE id = ?
        """, (
            f["id"],
        ))

        resultado = cursor.fetchone()

        xp_atual = resultado[
            0
        ]

        await interaction.response.send_message(
            f"✨ **XP ADICIONADO**\n\n"
            f"**{f['nome']}** recebeu "
            f"**{valor} XP**.\n\n"
            f"✨ XP atual: **{xp_atual}**"
        )
