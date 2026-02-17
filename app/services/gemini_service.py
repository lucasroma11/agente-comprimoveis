"""
GEMINI SERVICE - Operacoes no Banco de Dados
Funcoes que o agente executa quando recebe comandos
"""

from datetime import datetime
from sqlalchemy.orm import Session
from loguru import logger
from app.core.database import Tarefa, Condominio, Historico, SessionLocal


# ============================================================
# FUNCOES DE CONDOMINIO
# ============================================================

def listar_condominios(db: Session) -> list:
    """Lista todos os condomínios ativos"""
    condominios = db.query(Condominio).filter(
        Condominio.ativo == True
    ).all()
    return [{"id": c.id, "nome": c.nome} for c in condominios]


def buscar_condominio(db: Session, nome: str):
    """Busca condomínio pelo nome (busca parcial)"""
    condominio = db.query(Condominio).filter(
        Condominio.nome.ilike(f"%{nome}%"),
        Condominio.ativo == True
    ).first()
    return condominio


# ============================================================
# FUNCOES DE TAREFA
# ============================================================

def criar_tarefa(
    db: Session,
    titulo: str,
    mes: int,
    ano: int,
    condominio_nome: str = None,
    dia_vencimento: int = None,
    descricao: str = None,
    urgente: bool = False,
    categoria: str = "geral"
) -> dict:
    """Cria uma nova tarefa no banco"""
    try:
        condominio_id = None

        # Busca o condomínio se foi informado
        if condominio_nome:
            cond = buscar_condominio(db, condominio_nome)
            if cond:
                condominio_id = cond.id
            else:
                logger.warning(f"Condominio nao encontrado: {condominio_nome}")

        # Cria a tarefa
        tarefa = Tarefa(
            titulo=titulo,
            descricao=descricao,
            condominio_id=condominio_id,
            dia_vencimento=dia_vencimento,
            mes=mes,
            ano=ano,
            status="pendente",
            urgente=urgente,
            categoria=categoria
        )

        db.add(tarefa)
        db.commit()
        db.refresh(tarefa)

        logger.info(f"Tarefa criada: {titulo}")
        return {"sucesso": True, "id": tarefa.id, "titulo": titulo}

    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao criar tarefa: {e}")
        return {"sucesso": False, "erro": str(e)}


def listar_tarefas(
    db: Session,
    mes: int = None,
    ano: int = None,
    status: str = None,
    condominio_nome: str = None
) -> list:
    """Lista tarefas com filtros opcionais"""
    query = db.query(Tarefa)

    if mes:
        query = query.filter(Tarefa.mes == mes)
    if ano:
        query = query.filter(Tarefa.ano == ano)
    if status:
        query = query.filter(Tarefa.status == status)
    if condominio_nome:
        cond = buscar_condominio(db, condominio_nome)
        if cond:
            query = query.filter(Tarefa.condominio_id == cond.id)

    tarefas = query.order_by(Tarefa.dia_vencimento).all()

    resultado = []
    for t in tarefas:
        resultado.append({
            "id": t.id,
            "titulo": t.titulo,
            "condominio": t.condominio.nome if t.condominio else "Geral",
            "dia": t.dia_vencimento,
            "status": t.status,
            "urgente": t.urgente,
            "categoria": t.categoria
        })

    return resultado


def listar_tarefas_hoje(db: Session) -> list:
    """Lista tarefas do dia atual"""
    hoje = datetime.now()
    return listar_tarefas(
        db,
        mes=hoje.month,
        ano=hoje.year
    )


def listar_pendentes(db: Session, mes: int = None, ano: int = None) -> list:
    """Lista só as tarefas pendentes"""
    hoje = datetime.now()
    return listar_tarefas(
        db,
        mes=mes or hoje.month,
        ano=ano or hoje.year,
        status="pendente"
    )


def marcar_concluida(db: Session, tarefa_id: int, observacao: str = None) -> dict:
    """Marca uma tarefa como concluída"""
    try:
        tarefa = db.query(Tarefa).filter(Tarefa.id == tarefa_id).first()

        if not tarefa:
            return {"sucesso": False, "erro": "Tarefa nao encontrada"}

        tarefa.status = "concluida"
        tarefa.atualizado_em = datetime.now()

        # Registra no histórico
        hist = Historico(
            tarefa_id=tarefa_id,
            acao="concluida",
            observacao=observacao
        )
        db.add(hist)
        db.commit()

        logger.info(f"Tarefa {tarefa_id} concluida!")
        return {"sucesso": True, "titulo": tarefa.titulo}

    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao concluir tarefa: {e}")
        return {"sucesso": False, "erro": str(e)}


def editar_tarefa(
    db: Session,
    tarefa_id: int,
    titulo: str = None,
    dia_vencimento: int = None,
    urgente: bool = None,
    descricao: str = None
) -> dict:
    """Edita uma tarefa existente"""
    try:
        tarefa = db.query(Tarefa).filter(Tarefa.id == tarefa_id).first()

        if not tarefa:
            return {"sucesso": False, "erro": "Tarefa nao encontrada"}

        if titulo:
            tarefa.titulo = titulo
        if dia_vencimento:
            tarefa.dia_vencimento = dia_vencimento
        if urgente is not None:
            tarefa.urgente = urgente
        if descricao:
            tarefa.descricao = descricao

        tarefa.atualizado_em = datetime.now()
        db.commit()

        logger.info(f"Tarefa {tarefa_id} editada!")
        return {"sucesso": True, "titulo": tarefa.titulo}

    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao editar tarefa: {e}")
        return {"sucesso": False, "erro": str(e)}


def deletar_tarefa(db: Session, tarefa_id: int) -> dict:
    """Remove uma tarefa do banco"""
    try:
        tarefa = db.query(Tarefa).filter(Tarefa.id == tarefa_id).first()

        if not tarefa:
            return {"sucesso": False, "erro": "Tarefa nao encontrada"}

        titulo = tarefa.titulo
        db.delete(tarefa)
        db.commit()

        logger.info(f"Tarefa deletada: {titulo}")
        return {"sucesso": True, "titulo": titulo}

    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao deletar tarefa: {e}")
        return {"sucesso": False, "erro": str(e)}


# ============================================================
# TESTE RAPIDO
# ============================================================

if __name__ == "__main__":
    db = SessionLocal()

    print("\nTESTANDO CRUD DE TAREFAS\n")
    print("=" * 40)

    # Teste 1: Listar condomínios
    print("\n1. Condominios cadastrados:")
    conds = listar_condominios(db)
    for c in conds:
        print(f"   - {c['nome']}")

    # Teste 2: Criar tarefa
    print("\n2. Criando tarefa de teste...")
    resultado = criar_tarefa(
        db=db,
        titulo="Pagar boleto Light",
        mes=2,
        ano=2026,
        condominio_nome="Village Mananciais",
        dia_vencimento=15,
        categoria="pagamento"
    )
    print(f"   Resultado: {resultado}")

    # Teste 3: Listar tarefas
    print("\n3. Tarefas do mes:")
    tarefas = listar_tarefas(db, mes=2, ano=2026)
    for t in tarefas:
        print(f"   - [{t['id']}] {t['titulo']} | {t['condominio']} | Dia {t['dia']}")

    # Teste 4: Marcar como concluída
    if tarefas:
        print(f"\n4. Marcando tarefa {tarefas[0]['id']} como concluida...")
        res = marcar_concluida(db, tarefas[0]['id'])
        print(f"   Resultado: {res}")

    # Teste 5: Listar pendentes
    print("\n5. Tarefas pendentes:")
    pendentes = listar_pendentes(db, mes=2, ano=2026)
    print(f"   Total: {len(pendentes)}")

    db.close()
    print("\nCRUD funcionando!")