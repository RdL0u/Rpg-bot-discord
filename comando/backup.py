import discord

from discord import app_commands

from backup import (
    criar_backup,
    listar_info_backups,
)

from comando.permissoes import (
    eh_admin,
)


# ============================================================
# REGISTRAR COMANDOS DE BACKUP
# ============================================================

def registrar_comandos_backup(
    bot
):

    # ========================================================
    # CRIAR BACKUP MANUAL
    # ========================================================

    @bot.tree.command(
        name="backup",
        description="Cria um backup manual do banco de dados."
    )
    async def backup(
        interaction: discord.Interaction
    ):

        # ====================================================
        # APENAS ADMINISTRADORES
        # ====================================================

        if not eh_admin(
            interaction
        ):

            await interaction.response.send_message(
                "❌ Somente administradores podem "
                "criar backups manualmente.",
                ephemeral=True
            )

            return

        # ====================================================
        # DEFER
        # ====================================================

        await interaction.response.defer(
            ephemeral=True
        )

        try:

            caminho_backup = criar_backup()

        except Exception as erro:

            await interaction.followup.send(
                "❌ Não foi possível criar o backup.\n\n"
                f"Erro: `{erro}`",
                ephemeral=True
            )

            return

        tamanho = (
            caminho_backup.stat().st_size
        )

        # ====================================================
        # FORMATAR TAMANHO
        # ====================================================

        if tamanho < 1024:

            tamanho_formatado = (
                f"{tamanho} B"
            )

        elif tamanho < (
            1024 * 1024
        ):

            tamanho_formatado = (
                f"{tamanho / 1024:.2f} KB"
            )

        elif tamanho < (
            1024 * 1024 * 1024
        ):

            tamanho_formatado = (
                f"{tamanho / (1024 * 1024):.2f} MB"
            )

        else:

            tamanho_formatado = (
                f"{tamanho / (1024 * 1024 * 1024):.2f} GB"
            )

        await interaction.followup.send(
            "✅ **Backup criado com sucesso!**\n\n"
            f"📁 Arquivo: `{caminho_backup.name}`\n"
            f"💾 Tamanho: **{tamanho_formatado}**\n"
            f"🔒 Integridade: **OK**",
            ephemeral=True
        )


    # ========================================================
    # LISTAR BACKUPS
    # ========================================================

    @bot.tree.command(
        name="backups",
        description="Mostra os backups disponíveis."
    )
    async def backups(
        interaction: discord.Interaction
    ):

        # ====================================================
        # APENAS ADMINISTRADORES
        # ====================================================

        if not eh_admin(
            interaction
        ):

            await interaction.response.send_message(
                "❌ Somente administradores podem "
                "visualizar os backups.",
                ephemeral=True
            )

            return

        await interaction.response.defer(
            ephemeral=True
        )

        try:

            backups_disponiveis = (
                listar_info_backups()
            )

        except Exception as erro:

            await interaction.followup.send(
                "❌ Não foi possível listar os backups.\n\n"
                f"Erro: `{erro}`",
                ephemeral=True
            )

            return

        if not backups_disponiveis:

            await interaction.followup.send(
                "📦 Nenhum backup foi criado ainda.",
                ephemeral=True
            )

            return

        # ====================================================
        # EMBED
        # ====================================================

        embed = discord.Embed(
            title="💾 BACKUPS DO BOT",
            description=(
                f"Backups disponíveis: "
                f"**{len(backups_disponiveis)}**"
            ),
            color=discord.Color.blue()
        )

        # ====================================================
        # MOSTRAR OS 10 MAIS RECENTES
        # ====================================================

        for indice, info in enumerate(
            backups_disponiveis[:10],
            start=1
        ):

            criado_em = info[
                "criado_em"
            ]

            data_formatada = (
                criado_em.strftime(
                    "%d/%m/%Y às %H:%M:%S"
                )
            )

            integridade = (
                "✅ OK"
                if info["integro"]
                else "❌ FALHA"
            )

            embed.add_field(
                name=(
                    f"#{indice} — "
                    f"{info['nome']}"
                ),
                value=(
                    f"📅 {data_formatada}\n"
                    f"💾 {info['tamanho_formatado']}\n"
                    f"🔒 {integridade}"
                ),
                inline=False
            )

        if (
            len(backups_disponiveis)
            > 10
        ):

            restantes = (
                len(backups_disponiveis)
                - 10
            )

            embed.set_footer(
                text=(
                    f"Mostrando os 10 backups "
                    f"mais recentes • "
                    f"{restantes} não exibidos"
                )
            )

        else:

            embed.set_footer(
                text=(
                    "Backups ordenados "
                    "do mais recente para o mais antigo"
                )
            )

        await interaction.followup.send(
            embed=embed,
            ephemeral=True
        )
