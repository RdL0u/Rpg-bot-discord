import discord
import random

from discord import app_commands

from database import (
    db,
    cursor
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


# ============================================================
# FUNÇÕES AUXILIARES DO MESTRE
# ============================================================

def garantir_mesa(channel_id):

    cursor.execute("""
        INSERT OR IGNORE INTO mesas (
            channel_id,
            mestre_id
        )
        VALUES (?, NULL)
    """, (
        channel_id,
    ))

    db.commit()


def obter_mestre(channel_id):

    cursor.execute("""
        SELECT mestre_id
        FROM mesas
        WHERE channel_id = ?
    """, (
        channel_id,
    ))

    resultado = cursor.fetchone()

    if resultado:
        return resultado[0]

    return None


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
                "❌ Somente o Mestre atual ou um administrador pode fazer isso.",
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
        description="Cria um NPC."
    )
    @app_commands.describe(
        aleatorio="NPC aleatório ou personalizado",
        nome="Nome do NPC",
        hp="HP do NPC",
        mana="Mana do NPC"
    )
    @app_commands.choices(
        aleatorio=[
            app_commands.Choice(
                name="Sim",
                value="sim"
            ),
            app_commands.Choice(
                name="Não",
                value="nao"
            )
        ]
    )
    async def criarnpc(
        interaction: discord.Interaction,
        aleatorio: app_commands.Choice[str],
        nome: str = None,
        hp: int = None,
        mana: int = None
    ):

        garantir_mesa(
            interaction.channel.id
        )

        if (
            not eh_mestre(interaction)
            and not eh_admin(interaction)
        ):

            await interaction.response.send_message(
                "❌ Somente o Mestre pode criar NPCs.",
                ephemeral=True
            )

            return

        # ====================================================
        # NPC ALEATÓRIO
        # ====================================================

        if aleatorio.value == "sim":

            nomes = [
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

            nome = random.choice(
                nomes
            )

            hp = random.randint(
                20,
                150
            )

            mana = random.randint(
                0,
                100
            )

            atributos = {}

            for chave in ATRIBUTOS:

                atributos[chave] = random.randint(
                    0,
                    5
                )

            pericias = {}

            for chave in PERICIAS:

                pericias[chave] = random.randint(
                    0,
                    5
                )

            aleatorio_valor = 1

        # ====================================================
        # NPC PERSONALIZADO
        # ====================================================

        else:

            if not nome:

                await interaction.response.send_message(
                    "❌ Informe o nome do NPC.",
                    ephemeral=True
                )

                return

            if hp is None:

                await interaction.response.send_message(
                    "❌ Informe o HP do NPC.",
                    ephemeral=True
                )

                return

            if mana is None:

                await interaction.response.send_message(
                    "❌ Informe a Mana do NPC.",
                    ephemeral=True
                )

                return

            if hp <= 0 or mana < 0:

                await interaction.response.send_message(
                    "❌ Valores inválidos.",
                    ephemeral=True
                )

                return

            atributos = {
                chave: 0
                for chave in ATRIBUTOS
            }

            pericias = {
                chave: 0
                for chave in PERICIAS
            }

            aleatorio_valor = 0

        nome = nome[:50]

        mestre_id = obter_mestre(
            interaction.channel.id
        )

        if mestre_id is None:

            mestre_id = interaction.user.id

            cursor.execute("""
                UPDATE mesas
                SET mestre_id = ?
                WHERE channel_id = ?
            """, (
                mestre_id,
                interaction.channel.id
            ))

        colunas = (
            list(ATRIBUTOS.keys())
            + ORDEM_PERICIAS
        )

        valores = (
            [
                atributos[chave]
                for chave in ATRIBUTOS
            ]
            +
            [
                pericias[chave]
                for chave in ORDEM_PERICIAS
            ]
        )

        placeholders = ", ".join(
            ["?"] * len(valores)
        )

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
                ?, ?, ?, ?, 0,
                {placeholders},
                ?
            )
            """,
            [
                interaction.channel.id,
                mestre_id,
                nome,
                hp,
                hp,
                mana,
                mana
            ]
            + valores
            + [
                aleatorio_valor
            ]
        )

        db.commit()

        rc = (
            pericias["esquiva"]
            + atributos["destreza"]
            + 5
        )

        await interaction.response.send_message(
            f"👹 NPC **{nome}** criado!\n\n"
            f"❤️ HP: **{hp}/{hp}**\n"
            f"🔵 Mana: **{mana}/{mana}**\n"
            f"⚡ RC: **{rc}**\n\n"
            f"🎲 Atributos e perícias "
            f"{'foram gerados aleatoriamente' if aleatorio_valor else 'começaram em 0'}."
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
            f"{len(resultados)} encontrados**"
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
                )
            )


    # ========================================================
    # APAGAR NPC
    # ========================================================

    @bot.tree.command(
        name="apagarnpc",
        description="Apaga um NPC."
    )
    @app_commands.describe(
        nome="Nome exato do NPC"
    )
    async def apagarnpc(
        interaction: discord.Interaction,
        nome: str
    ):

        if (
            not eh_mestre(interaction)
            and not eh_admin(interaction)
        ):

            await interaction.response.send_message(
                "❌ Somente o Mestre pode apagar NPCs.",
                ephemeral=True
            )

            return

        cursor.execute("""
            SELECT id
            FROM fichas
            WHERE channel_id = ?
            AND tipo = 'npc'
            AND nome = ?
            LIMIT 1
        """, (
            interaction.channel.id,
            nome
        ))

        resultado = cursor.fetchone()

        if resultado is None:

            await interaction.response.send_message(
                "❌ NPC não encontrado.",
                ephemeral=True
            )

            return

        cursor.execute(
            "DELETE FROM fichas WHERE id = ?",
            (
                resultado[0],
            )
        )

        db.commit()

        await interaction.response.send_message(
            f"🗑️ NPC **{nome}** apagado."
        )
