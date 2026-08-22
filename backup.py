import sqlite3

from datetime import datetime
from pathlib import Path


# ============================================================
# CONFIGURAÇÃO
# ============================================================

PASTA_PROJETO = Path(
    __file__
).resolve().parent

ARQUIVO_BANCO = (
    PASTA_PROJETO
    / "rpg_fichas.db"
)

PASTA_BACKUPS = (
    PASTA_PROJETO
    / "backups"
)

MAX_BACKUPS = 20


# ============================================================
# GARANTIR PASTA DE BACKUPS
# ============================================================

def garantir_pasta_backups():

    PASTA_BACKUPS.mkdir(
        parents=True,
        exist_ok=True
    )


# ============================================================
# GERAR NOME DO BACKUP
# ============================================================

def gerar_nome_backup():

    momento = datetime.now()

    return (
        "rpg_fichas_"
        + momento.strftime(
            "%Y-%m-%d_%H-%M-%S"
        )
        + ".db"
    )


# ============================================================
# VERIFICAR INTEGRIDADE
# ============================================================

def verificar_integridade(
    caminho_banco
):

    conexao = None

    try:

        conexao = sqlite3.connect(
            str(caminho_banco)
        )

        cursor = conexao.cursor()

        cursor.execute(
            "PRAGMA integrity_check"
        )

        resultado = cursor.fetchone()

        return (
            resultado is not None
            and resultado[0] == "ok"
        )

    except sqlite3.Error:

        return False

    finally:

        if conexao is not None:

            conexao.close()


# ============================================================
# CRIAR BACKUP
# ============================================================

def criar_backup():

    garantir_pasta_backups()

    if not ARQUIVO_BANCO.exists():

        raise FileNotFoundError(
            "O banco rpg_fichas.db "
            "não foi encontrado."
        )

    nome_backup = (
        gerar_nome_backup()
    )

    caminho_backup = (
        PASTA_BACKUPS
        / nome_backup
    )

    origem = None
    destino = None

    try:

        # ====================================================
        # ABRIR O BANCO ORIGINAL
        # ====================================================

        origem = sqlite3.connect(
            str(ARQUIVO_BANCO)
        )

        # ====================================================
        # CRIAR O BANCO DE BACKUP
        # ====================================================

        destino = sqlite3.connect(
            str(caminho_backup)
        )

        # ====================================================
        # BACKUP NATIVO DO SQLITE
        # ====================================================

        origem.backup(
            destino
        )

        destino.commit()

    except Exception:

        if caminho_backup.exists():

            try:

                caminho_backup.unlink()

            except OSError:

                pass

        raise

    finally:

        if destino is not None:

            destino.close()

        if origem is not None:

            origem.close()

    # ========================================================
    # VERIFICAR INTEGRIDADE DO BACKUP
    # ========================================================

    if not verificar_integridade(
        caminho_backup
    ):

        try:

            caminho_backup.unlink()

        except OSError:

            pass

        raise RuntimeError(
            "O backup foi criado, "
            "mas falhou na verificação "
            "de integridade."
        )

    # ========================================================
    # LIMPAR BACKUPS ANTIGOS
    # ========================================================

    limpar_backups_antigos()

    return caminho_backup


# ============================================================
# LISTAR BACKUPS
# ============================================================

def listar_backups():

    garantir_pasta_backups()

    backups = list(
        PASTA_BACKUPS.glob(
            "rpg_fichas_*.db"
        )
    )

    backups.sort(
        key=lambda arquivo: (
            arquivo.stat().st_mtime
        ),
        reverse=True
    )

    return backups


# ============================================================
# CONTAR BACKUPS
# ============================================================

def contar_backups():

    return len(
        listar_backups()
    )


# ============================================================
# OBTER BACKUP MAIS RECENTE
# ============================================================

def obter_backup_mais_recente():

    backups = listar_backups()

    if not backups:

        return None

    return backups[0]


# ============================================================
# LIMPAR BACKUPS ANTIGOS
# ============================================================

def limpar_backups_antigos(
    max_backups=MAX_BACKUPS
):

    backups = listar_backups()

    if len(backups) <= max_backups:

        return []

    removidos = []

    for backup in backups[
        max_backups:
    ]:

        try:

            backup.unlink()

            removidos.append(
                backup
            )

        except OSError:

            pass

    return removidos


# ============================================================
# TAMANHO DO BACKUP
# ============================================================

def obter_tamanho_backup(
    caminho_backup
):

    caminho_backup = Path(
        caminho_backup
    )

    if not caminho_backup.exists():

        return 0

    return caminho_backup.stat().st_size


# ============================================================
# FORMATAR TAMANHO
# ============================================================

def formatar_tamanho(
    tamanho_bytes
):

    tamanho = float(
        tamanho_bytes
    )

    unidades = [
        "B",
        "KB",
        "MB",
        "GB",
    ]

    for unidade in unidades:

        if tamanho < 1024:

            return (
                f"{tamanho:.2f} "
                f"{unidade}"
            )

        tamanho /= 1024

    return (
        f"{tamanho:.2f} TB"
    )


# ============================================================
# INFORMAÇÕES DO BACKUP
# ============================================================

def obter_info_backup(
    caminho_backup
):

    caminho_backup = Path(
        caminho_backup
    )

    if not caminho_backup.exists():

        return None

    estatisticas = (
        caminho_backup.stat()
    )

    criado_em = datetime.fromtimestamp(
        estatisticas.st_mtime
    )

    tamanho = (
        estatisticas.st_size
    )

    return {
        "nome": caminho_backup.name,
        "caminho": caminho_backup,
        "criado_em": criado_em,
        "tamanho": tamanho,
        "tamanho_formatado": (
            formatar_tamanho(
                tamanho
            )
        ),
        "integro": verificar_integridade(
            caminho_backup
        ),
    }


# ============================================================
# LISTAR INFORMAÇÕES DOS BACKUPS
# ============================================================

def listar_info_backups():

    resultado = []

    for backup in listar_backups():

        info = obter_info_backup(
            backup
        )

        if info is not None:

            resultado.append(
                info
            )

    return resultado
