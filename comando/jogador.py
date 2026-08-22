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
)


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
        description="Cria sua ficha neste canal."
    )
    @app_commands.describe(
        nome="Nome do personagem",
        hp="HP máximo",
        mana="Mana máxima"
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

        if existente is not None:

            await interaction.response.send_message(
                "❌ Você já possui uma ficha neste canal.",
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

        nome = nome.strip()[:50]

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

                academicos,
                idiomas,
                oficios,
                armas_brancas,
                intimidacao,
                ocultismo,
                briga,
                investigacao,
                persuasao,
                ciencias,
                labia,
                prontidao,
                conhecimentos_gerais,
                lideranca,
                sobrevivencia,
                conducao,
                manha,
                tecnologia,
                esportes,
                medicina,
                mira,
                esquiva,
                furtividade,

                aleatorio
            )
            VALUES (
                ?, ?, NULL, 'jogador', ?,

                ?, ?,

                ?, ?,

                0,

                0, 0, 0, 0, 0, 0,

                0, 0, 0, 0, 0,
                0, 0, 0, 0, 0,
                0, 0, 0, 0, 0,
                0, 0, 0, 0, 0,
                0, 0, 0,

                0
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

        await interaction.response.send_message(
            f"📜 Ficha de **{nome}** criada!\n\n"
            f"❤️ HP: **{hp}/{hp}**\n"
            f"🔵 Mana: **{mana}/{mana}**\n"
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
    # LIMITE GLOBAL: 0 A 5
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

        novo_hp = f"{hp}/{hp}"
        nova_mana = f"{mana}/{mana}"

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

        cursor.execute("""
            DELETE FROM fichas
            WHERE id = ?
        """, (
            f["id"],
        ))

        db.commit()

        await interaction.response.send_message(
            f"🗑️ Ficha **{f['nome']}** apagada.",
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
    # MODAL DE VALOR DA AÇÃO
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

                hp_anterior = f[
                    "hp_atual"
                ]

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

                hp_anterior = f[
                    "hp_atual"
                ]

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

                if novo_hp != hp_anterior:

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

            if self.acao == "recuperarmana":

                mana_anterior = f[
                    "mana_atual"
                ]

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

                if nova_mana != mana_anterior:

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
                            f"💧 {recuperado} de Mana recuperada."
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

        if valor > f["mana_atual"]:

            await interaction.response.send_message(
                "❌ Você não possui Mana suficiente.",
                ephemeral=True
            )

            return

        mana_anterior = f[
            "mana_atual"
        ]

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
                "❌ O XP adicionado precisa ser maior que 0.",
                ephemeral=True
            )

            return

        xp_anterior = f[
            "xp"
        ]

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
