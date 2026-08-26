import discord

from database import (
    obter_mestre,
)


# ============================================================
# UTILIDADES
# ============================================================

def tem_guild(
    interaction: discord.Interaction
):

    return (
        interaction.guild is not None
    )


def tem_canal(
    interaction: discord.Interaction
):

    return (
        interaction.channel is not None
    )


# ============================================================
# ADMINISTRADOR GLOBAL
# ============================================================

def eh_admin(
    interaction: discord.Interaction
):

    if not tem_guild(
        interaction
    ):

        return False

    # ========================================================
    # DONO DO SERVIDOR
    # ========================================================

    if (
        interaction.guild.owner_id
        == interaction.user.id
    ):

        return True

    # ========================================================
    # PERMISSÃO ADMINISTRADOR
    # ========================================================

    try:

        return bool(
            interaction.user
            .guild_permissions
            .administrator
        )

    except AttributeError:

        return False


# ============================================================
# GERENCIAR CANAL
# ============================================================

def pode_gerenciar_canal(
    interaction: discord.Interaction
):

    if not tem_guild(
        interaction
    ):

        return False

    if not tem_canal(
        interaction
    ):

        return False

    # ========================================================
    # DONO DO SERVIDOR
    # ========================================================

    if (
        interaction.guild.owner_id
        == interaction.user.id
    ):

        return True

    # ========================================================
    # ADMINISTRADOR GLOBAL
    # ========================================================

    if eh_admin(
        interaction
    ):

        return True

    # ========================================================
    # PERMISSÃO INFORMADA PELA INTERAÇÃO
    #
    # Esta é a principal verificação para permissões
    # específicas daquele canal.
    # ========================================================

    try:

        permissoes_interacao = (
            interaction.permissions
        )

        if (
            permissoes_interacao
            is not None
            and
            permissoes_interacao.manage_channels
        ):

            return True

    except (
        AttributeError,
        TypeError
    ):

        pass

    # ========================================================
    # PERMISSÕES CALCULADAS DIRETAMENTE PELO CANAL
    #
    # Serve como segunda verificação.
    # ========================================================

    try:

        permissoes_canal = (
            interaction.channel
            .permissions_for(
                interaction.user
            )
        )

        if (
            permissoes_canal.manage_channels
        ):

            return True

    except (
        AttributeError,
        TypeError
    ):

        pass

    return False


# ============================================================
# MESTRE
# ============================================================

def eh_mestre(
    interaction: discord.Interaction
):

    if not tem_canal(
        interaction
    ):

        return False

    mestre_id = obter_mestre(
        interaction.channel.id
    )

    return (
        mestre_id
        == interaction.user.id
    )


# ============================================================
# ADMIN OU MESTRE
# ============================================================

def eh_admin_ou_mestre(
    interaction: discord.Interaction
):

    return (
        eh_admin(
            interaction
        )
        or
        eh_mestre(
            interaction
        )
    )


# ============================================================
# DONO DA FICHA
# ============================================================

def eh_dono_ficha(
    interaction: discord.Interaction,
    ficha
):

    if ficha is None:

        return False

    if (
        ficha.get("tipo")
        != "jogador"
    ):

        return False

    return (
        ficha.get("dono_id")
        == interaction.user.id
    )


# ============================================================
# MESTRE RESPONSÁVEL PELO NPC
# ============================================================

def eh_mestre_do_npc(
    interaction: discord.Interaction,
    ficha
):

    if ficha is None:

        return False

    if (
        ficha.get("tipo")
        != "npc"
    ):

        return False

    if eh_mestre(
        interaction
    ):

        return True

    return (
        ficha.get("mestre_id")
        == interaction.user.id
    )


# ============================================================
# ALTERAR FICHA
# ============================================================

def pode_alterar_ficha(
    interaction: discord.Interaction,
    ficha
):

    if ficha is None:

        return False

    if eh_admin(
        interaction
    ):

        return True

    tipo = ficha.get(
        "tipo"
    )

    if tipo == "jogador":

        if eh_dono_ficha(
            interaction,
            ficha
        ):

            return True

        if eh_mestre(
            interaction
        ):

            return True

        return False

    if tipo == "npc":

        return eh_mestre_do_npc(
            interaction,
            ficha
        )

    return False


# ============================================================
# ALTERAR PRÓPRIA FICHA
# ============================================================

def pode_alterar_propria_ficha(
    interaction: discord.Interaction,
    ficha
):

    if ficha is None:

        return False

    if eh_admin(
        interaction
    ):

        return True

    return eh_dono_ficha(
        interaction,
        ficha
    )


# ============================================================
# GERENCIAR MESA
# ============================================================

def pode_gerenciar_mesa(
    interaction: discord.Interaction
):

    return eh_admin_ou_mestre(
        interaction
    )


# ============================================================
# DEFINIR MESTRE
#
# DONO DO SERVIDOR
# OU ADMINISTRADOR
# OU GERENCIAR CANAL
# ============================================================

def pode_definir_mestre(
    interaction: discord.Interaction
):

    return pode_gerenciar_canal(
        interaction
    )


# ============================================================
# PASSAR MESTRE
# ============================================================

def pode_passar_mestre(
    interaction: discord.Interaction
):

    return eh_admin_ou_mestre(
        interaction
    )


# ============================================================
# GERENCIAR NPCS
# ============================================================

def pode_gerenciar_npcs(
    interaction: discord.Interaction
):

    return eh_admin_ou_mestre(
        interaction
    )


# ============================================================
# CRIAR NPC
# ============================================================

def pode_criar_npc(
    interaction: discord.Interaction
):

    return pode_gerenciar_npcs(
        interaction
    )


# ============================================================
# APAGAR NPC
# ============================================================

def pode_apagar_npc(
    interaction: discord.Interaction
):

    return pode_gerenciar_npcs(
        interaction
    )


# ============================================================
# VISUALIZAR NPCS
# ============================================================

def pode_visualizar_npcs(
    interaction: discord.Interaction
):

    return pode_gerenciar_npcs(
        interaction
    )


# ============================================================
# ALTERAR XP
# ============================================================

def pode_alterar_xp(
    interaction: discord.Interaction,
    ficha
):

    return pode_alterar_ficha(
        interaction,
        ficha
    )


# ============================================================
# ALTERAR ATRIBUTOS
# ============================================================

def pode_alterar_atributos(
    interaction: discord.Interaction,
    ficha
):

    return pode_alterar_ficha(
        interaction,
        ficha
    )


# ============================================================
# ALTERAR PERÍCIAS
# ============================================================

def pode_alterar_pericias(
    interaction: discord.Interaction,
    ficha
):

    return pode_alterar_ficha(
        interaction,
        ficha
    )


# ============================================================
# ALTERAR RECURSOS
# HP / MANA
# ============================================================

def pode_alterar_recursos(
    interaction: discord.Interaction,
    ficha
):

    return pode_alterar_ficha(
        interaction,
        ficha
    )


# ============================================================
# CONSULTAR HISTÓRICO
# ============================================================

def pode_ver_historico(
    interaction: discord.Interaction
):

    return eh_admin_ou_mestre(
        interaction
    )


# ============================================================
# USAR PAINEL
# ============================================================

def pode_usar_painel(
    interaction: discord.Interaction
):

    return True


# ============================================================
# BACKUPS
# ============================================================

def pode_criar_backup(
    interaction: discord.Interaction
):

    return eh_admin(
        interaction
    )


def pode_visualizar_backups(
    interaction: discord.Interaction
):

    return eh_admin(
        interaction
    )
