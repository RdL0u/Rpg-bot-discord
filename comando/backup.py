import discord

from backup import (
    criar_backup,
    listar_backups,
)

from comando.permissoes import (
    pode_criar_backup,
    pode_visualizar_backups,
)


# ============================================================
# FORMATAR TAMANHO
# ============================================================

def formatar_tamanho(
    tamanho
):

    tamanho = float(
        tamanho
    )

    unidades = [
        "B",
        "KB",
        "MB",
        "GB",
    ]

    indice = 0

    while (
        tamanho >= 1024
        and indice
        < len(unidades) - 1
    ):

        tamanho /= 1024

        indice += 1

    if indice == 0:

        return (
            f"{int(tamanho)} "
            f"{unidades[indice]}"
        )

    return (
        f"{tamanho:.2f} "
        f"{unidades[indice]}"
    )


# ============================================================
# EXTRAIR INFORMAÇÕES DO BACKUP
# ============================================================

def obter_info_backup(
    backup
):

    if hasattr(
        backup,
        "name"
    ):

        nome = backup.name

    else:

        nome = str(
            backup
        )

    tamanho = None

    try:

        if hasattr(
            backup,
            "stat"
        ):

            tamanho = (
                backup.stat().st_size
            )

    except Exception:

        tamanho = None

    return (
        nome,
        tamanho
    )


# ============================================================
# REGISTRAR COMANDOS
# ============================================================

def registrar_comandos_backup(
    bot
):

    # ========================================================
    # CRIAR BACKUP
    # ========================================================

    @bot.tree.command(
        name="backup",
        description="Cria um backup manual do banco de dados."
    )
    async def backup(
        interaction: discord.Interaction
    ):

        if not pode_criar_backup(
            interaction
        ):

            await interaction.response.send_message(
                "❌ Somente administradores "
                "podem criar backups.",
                ephemeral=True
            )

            return

        await interaction.response.defer(
            ephemeral=True
        )

        try:

            caminho = criar_backup()

        except Exception as erro:

            await interaction.followup.send(
                (
                    "❌ Não foi possível criar "
                    "o backup.\n\n"
                    f"`{erro}`"
                ),
                ephemeral=True
            )

            return

        nome = getattr(
            caminho,
            "name",
            str(caminho)
        )

        tamanho = None

        try:

            tamanho = (
                caminho.stat().st_size
            )

        except Exception:

            pass

        mensagem = (
            "✅ **Backup criado com sucesso!**\n\n"
            f"💾 Arquivo: `{nome}`"
        )

        if tamanho is not None:

            mensagem += (
                "\n"
                f"📦 Tamanho: "
                f"**{formatar_tamanho(tamanho)}**"
            )

        mensagem += (
            "\n\n"
            "🔒 O backup permanece armazenado "
            "localmente no servidor do bot."
        )

        await interaction.followup.send(
            mensagem,
            ephemeral=True
        )


    # ========================================================
    # LISTAR BACKUPS
    # ========================================================

    @bot.tree.command(
        name="backups",
        description="Lista os backups disponíveis."
    )
    async def backups(
        interaction: discord.Interaction
    ):

        if not pode_visualizar_backups(
            interaction
        ):

            await interaction.response.send_message(
                "❌ Somente administradores "
                "podem visualizar os backups.",
                ephemeral=True
            )

            return

        try:

            lista = listar_backups()

        except Exception as erro:

            await interaction.response.send_message(
                (
                    "❌ Não foi possível listar "
                    "os backups.\n\n"
                    f"`{erro}`"
                ),
                ephemeral=True
            )

            return

        if not lista:

            await interaction.response.send_message(
                "💾 Nenhum backup foi encontrado.",
                ephemeral=True
            )

            return

        # Exibir somente os 10 mais recentes
        lista = lista[:10]

        linhas = []

        for indice, item in enumerate(
            lista,
            start=1
        ):

            nome, tamanho = (
                obter_info_backup(
                    item
                )
            )

            if tamanho is not None:

                linhas.append(
                    (
                        f"**{indice}.** `{nome}`\n"
                        f"└ 📦 "
                        f"{formatar_tamanho(tamanho)}"
                    )
                )

            else:

                linhas.append(
                    (
                        f"**{indice}.** "
                        f"`{nome}`"
                    )
                )

        embed = discord.Embed(
            title="💾 BACKUPS DO BOT",
            description="\n\n".join(
                linhas
            ),
            color=discord.Color.dark_red()
        )

        embed.set_footer(
            text=(
                "Exibindo até os "
                "10 backups mais recentes"
            )
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )
