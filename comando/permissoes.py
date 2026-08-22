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
# ADMINISTRADOR
# ============================================================

def eh_admin(
    interaction: discord.Interaction
):

    if not tem_guild(
        interaction
    ):

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

    # Mestre atual do canal
    if eh_mestre(
        interaction
    ):

        return True

    # Compatibilidade com NPCs que já possuem
    # mestre_id gravado diretamente na ficha
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

    # Administrador sempre pode alterar
    if eh_admin(
        interaction
    ):

        return True

    tipo = ficha.get(
        "tipo"
    )

    # ========================================================
    # FICHA DE JOGADOR
    # ========================================================

    if tipo == "jogador":

        # O próprio jogador
        if eh_dono_ficha(
            interaction,
            ficha
        ):

            return True

        # Mestre atual da mesa
        if eh_mestre(
            interaction
        ):

            return True

        return False

    # ========================================================
    # NPC
    # ========================================================

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
# ============================================================

def pode_definir_mestre(
    interaction: discord.Interaction
):

    # Mantém a regra atual:
    # somente administradores.
    return eh_admin(
        interaction
    )


# ============================================================
# PASSAR MESTRE
# ============================================================

def pode_passar_mestre(
    interaction: discord.Interaction
):

    # Mantém a regra atual:
    # Mestre atual ou administrador.
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

    # Por enquanto mantém exatamente a mesma
    # regra geral de alteração da ficha.
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

    # Mantemos inicialmente Mestre ou Admin.
    return eh_admin_ou_mestre(
        interaction
    )


# ============================================================
# USAR PAINEL
# ============================================================

def pode_usar_painel(
    interaction: discord.Interaction
):

    # O painel continua acessível.
    # As ações dentro dele continuam sendo
    # controladas pelas permissões específicas.
    return True


# ============================================================
# BACKUPS
# ============================================================

def pode_criar_backup(
    interaction: discord.Interaction
):

    # Backup continua exclusivo para administrador.
    return eh_admin(
        interaction
    )


def pode_visualizar_backups(
    interaction: discord.Interaction
):

    # Listagem de backups continua exclusiva
    # para administrador.
    return eh_admin(
        interaction
    )
