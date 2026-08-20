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
)

from config import ATRIBUTOS, PERICIAS


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
        obter_mestre(interaction.channel.id)
        == interaction.user.id
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

        f = transformar_ficha(dados)

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
                f"❌ **{jogador.display_name}** não possui uma ficha.",
                ephemeral=True
            )

            return

        f = transformar_ficha(dados)

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

        f = transformar_ficha(dados)

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
            app_commands.Choice(name="Acadêmicos", value="academicos"),
            app_commands.Choice(name="Idiomas", value="idiomas"),
            app_commands.Choice(name="Ofícios", value="oficios"),
            app_commands.Choice(name="Armas Brancas", value="armas_brancas"),
            app_commands.Choice(name="Intimidação", value="intimidacao"),
            app_commands.Choice(name="Ocultismo", value="ocultismo"),
            app_commands.Choice(name="Briga", value="briga"),
            app_commands.Choice(name="Investigação", value="investigacao"),
            app_commands.Choice(name="Persuasão", value="persuasao"),
            app_commands.Choice(name="Ciências", value="ciencias"),
            app_commands.Choice(name="Lábia", value="labia"),
            app_commands.Choice(name="Prontidão", value="prontidao"),
            app_commands.Choice(name="Conhecimentos Gerais", value="conhecimentos_gerais"),
            app_commands.Choice(name="Liderança", value="lideranca"),
            app_commands.Choice(name="Sobrevivência", value="sobrevivencia"),
            app_commands.Choice(name="Condução", value="conducao"),
            app_commands.Choice(name="Manha", value="manha"),
            app_commands.Choice(name="Tecnologia", value="tecnologia"),
            app_commands.Choice(name="Esportes", value="esportes"),
            app_commands.Choice(name="Medicina", value="medicina"),
            app_commands.Choice(name="Mira", value="mira"),
            app_commands.Choice(name="Esquiva", value="esquiva"),
            app_commands.Choice(name="Furtividade", value="furtividade")
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

        f = transformar_ficha(dados)

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

        f = transformar_ficha(dados)

        if not pode_alterar_ficha(
            interaction,
            f
        ):

            await interaction.response.send_message(
                "❌ Você não pode alterar essa ficha.",
                ephemeral=True
            )

            return

        if hp <= 0 or mana < 0:

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

        await interaction.response.send_message(
            f"⚙️ Ficha de **{f['nome']}** atualizada!\n\n"
            f"❤️ HP: **{hp}/{hp}**\n"
            f"🔵 Mana: **{mana}/{mana}**"
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

        f = transformar_ficha(dados)

        cursor.execute(
            "DELETE FROM fichas WHERE id = ?",
            (f["id"],)
        )

        db.commit()

        await interaction.response.send_message(
            f"🗑️ A ficha **{f['nome']}** foi apagada."
        )

    # ========================================================
    # DANO
    # ========================================================

    @bot.tree.command(
        name="dano",
        description="Aplica dano a um jogador."
    )
    @app_commands.describe(
        jogador="Jogador que receberá o dano",
        valor="Quantidade de dano"
    )
    async def dano(
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
                "❌ O dano precisa ser maior que 0.",
                ephemeral=True
            )

            return

        f = transformar_ficha(dados)

        novo_hp = max(
            0,
            f["hp_atual"] - valor
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

        await interaction.response.send_message(
            f"💥 **{f['nome']}** recebeu **{valor} de dano**!\n"
            f"❤️ HP: **{novo_hp}/{f['hp_max']}**"
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

        f = transformar_ficha(dados)

        novo_hp = min(
            f["hp_max"],
            f["hp_atual"] + valor
        )

        recuperado = novo_hp - f["hp_atual"]

        cursor.execute("""
            UPDATE fichas
            SET hp_atual = ?
            WHERE id = ?
        """, (
            novo_hp,
            f["id"]
        ))

        db.commit()

        await interaction.response.send_message(
            f"💚 **{f['nome']}** recuperou "
            f"**{recuperado} de HP**!\n"
            f"❤️ HP: **{novo_hp}/{f['hp_max']}**"
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

        f = transformar_ficha(dados)

        if valor <= 0:

            await interaction.response.send_message(
                "❌ O valor precisa ser maior que 0.",
                ephemeral=True
            )

            return

        if valor > f["mana_atual"]:

            await interaction.response.send_message(
                "❌ Mana insuficiente.",
                ephemeral=True
            )

            return

        nova_mana = (
            f["mana_atual"] - valor
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

        await interaction.response.send_message(
            f"🔮 **{f['nome']}** gastou "
            f"**{valor} de Mana**!\n"
            f"🔵 Mana: **{nova_mana}/{f['mana_max']}**"
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

        f = transformar_ficha(dados)

        nova_mana = min(
            f["mana_max"],
            f["mana_atual"] + valor
        )

        recuperado = (
            nova_mana - f["mana_atual"]
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

        await interaction.response.send_message(
            f"💧 **{f['nome']}** recuperou "
            f"**{recuperado} de Mana**!\n"
            f"🔵 Mana: **{nova_mana}/{f['mana_max']}**"
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

        f = transformar_ficha(dados)

        if (
            f["dono_id"] != interaction.user.id
            and not eh_admin(interaction)
            and not eh_mestre(interaction)
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

        cursor.execute(
            "SELECT xp FROM fichas WHERE id = ?",
            (f["id"],)
        )

        resultado = cursor.fetchone()

        xp_atual = resultado[0]

        await interaction.response.send_message(
            f"✨ **{f['nome']}** recebeu "
            f"**{valor} XP**!\n"
            f"✨ XP atual: **{xp_atual}**"
        )
