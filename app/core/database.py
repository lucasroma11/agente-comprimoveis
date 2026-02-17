"""
DATABASE - Configuração do Banco de Dados
SQLite para beta, PostgreSQL para produção
"""

import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String,
    Boolean, DateTime, Text, ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

# ============================================================
# CONFIGURAÇÃO DO BANCO
# ============================================================

# SQLite para beta (arquivo local)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./agente_comprimoveis.db"
)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Necessário para SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ============================================================
# TABELAS
# ============================================================

class Condominio(Base):
    __tablename__ = "condominios"

    id        = Column(Integer, primary_key=True, index=True)
    nome      = Column(String(100), nullable=False)
    tipo      = Column(String(50), default="residencial")
    ativo     = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.now)

    # Relacionamento com tarefas
    tarefas = relationship("Tarefa", back_populates="condominio")

    def __repr__(self):
        return f"<Condominio {self.nome}>"


class Tarefa(Base):
    __tablename__ = "tarefas"

    id             = Column(Integer, primary_key=True, index=True)
    titulo         = Column(String(200), nullable=False)
    descricao      = Column(Text, nullable=True)
    condominio_id  = Column(Integer, ForeignKey("condominios.id"), nullable=True)
    dia_vencimento = Column(Integer, nullable=True)
    mes            = Column(Integer, nullable=False)
    ano            = Column(Integer, nullable=False)
    status         = Column(String(20), default="pendente")
    urgente        = Column(Boolean, default=False)
    categoria      = Column(String(50), default="geral")
    criado_em      = Column(DateTime, default=datetime.now)
    atualizado_em  = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relacionamento com condomínio
    condominio = relationship("Condominio", back_populates="tarefas")

    # Relacionamento com histórico
    historico = relationship("Historico", back_populates="tarefa")

    def __repr__(self):
        return f"<Tarefa {self.titulo}>"


class Historico(Base):
    __tablename__ = "historico"

    id         = Column(Integer, primary_key=True, index=True)
    tarefa_id  = Column(Integer, ForeignKey("tarefas.id"))
    acao       = Column(String(50))
    observacao = Column(Text, nullable=True)
    criado_em  = Column(DateTime, default=datetime.now)

    # Relacionamento com tarefa
    tarefa = relationship("Tarefa", back_populates="historico")


# ============================================================
# FUNÇÕES UTILITÁRIAS
# ============================================================

def criar_tabelas():
    """Cria todas as tabelas no banco de dados"""
    Base.metadata.create_all(bind=engine)
    logger.info("Tabelas criadas com sucesso!")


def get_db():
    """Retorna uma sessão do banco de dados"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def popular_condominios():
    """Popula os condomínios da Comprimóveis no banco"""
    db = SessionLocal()

    condominios_comprimoveis = [
        "Village Mananciais",
        "Colina Verde",
        "Village Tucanos",
        "Itaipu",
        "Samira",
        "Nascente Rio Grande",
        "Anchieta",
        "Village Ipadu",
        "Sylvania",
        "Village Pedras",
        "Primavera",
    ]

    try:
        # Verifica se já existem condomínios
        existentes = db.query(Condominio).count()
        if existentes > 0:
            logger.info(f"{existentes} condomínios já cadastrados!")
            return

        # Adiciona os condomínios
        for nome in condominios_comprimoveis:
            cond = Condominio(nome=nome)
            db.add(cond)

        db.commit()
        logger.info(f"{len(condominios_comprimoveis)} condomínios cadastrados!")

    except Exception as e:
        logger.error(f"Erro ao popular condomínios: {e}")
        db.rollback()
    finally:
        db.close()


# ============================================================
# INICIALIZAÇÃO
# ============================================================

if __name__ == "__main__":
    print("\nINICIALIZANDO BANCO DE DADOS\n")
    print("=" * 40)

    # Cria as tabelas
    criar_tabelas()

    # Popula os condomínios
    popular_condominios()

    # Verifica o resultado
    db = SessionLocal()
    total = db.query(Condominio).count()
    print(f"\nCondominios cadastrados: {total}")

    condominios = db.query(Condominio).all()
    for c in condominios:
        print(f"  - {c.nome}")

    db.close()
    print("\nBanco pronto!")