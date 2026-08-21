import discord

from database import obter_mestre


# ============================================================
# VERIFICAR ADMINISTRADOR
# ============================================================

def eh_admin(interaction: discord.Interaction):

    if interaction.guild is None:
        return False

    return interaction.user.guild_permissions.administrator


# ============================================================
# VERIFICAR MESTRE
# ============================================================

def eh_mestre(interaction: discord.Interaction):

    if interaction.channel is None:
        return False

    return (
        obter_mestre(
            interaction.channel.id
        )
        == interaction.user.id
    )
