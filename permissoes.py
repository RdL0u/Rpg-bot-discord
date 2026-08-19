from database import cursor


# ============================================================
# ADMINISTRADOR
# ============================================================

def eh_admin(interaction):

    if interaction.guild is None:
        return False

    return interaction.user.guild_permissions.administrator


# ============================================================
# OBTER MESTRE
# ============================================================

def obter_mestre(channel_id):

    cursor.execute("""
        SELECT mestre_id
        FROM mesas
        WHERE channel_id = ?
    """, (channel_id,))

    resultado = cursor.fetchone()

    if resultado:
        return resultado[0]

    return None


# ============================================================
# VERIFICAR MESTRE
# ============================================================

def eh_mestre(interaction):

    return (
        obter_mestre(interaction.channel.id)
        == interaction.user.id
    )


# ============================================================
# VERIFICAR PERMISSÃO SOBRE UMA FICHA
# ============================================================

def pode_alterar_ficha(interaction, ficha):

    if eh_admin(interaction):
        return True

    if ficha["tipo"] == "jogador":

        return (
            ficha["dono_id"]
            == interaction.user.id
            or eh_mestre(interaction)
        )

    if ficha["tipo"] == "npc":

        return (
            ficha["mestre_id"]
            == interaction.user.id
        )

    return False
