"""
AI ROUTER - Roteador Inteligente conectado ao CRUD
"""

import os
import asyncio
from enum import Enum
from loguru import logger
from dotenv import load_dotenv
from google import genai
from app.core.database import SessionLocal
from app.services.gemini_service import (
    criar_tarefa, listar_tarefas, listar_pendentes,
    marcar_concluida, deletar_tarefa, editar_tarefa,
    listar_condominios
)

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# ============================================================
# TIPOS DE COMPLEXIDADE
# ============================================================

class Complexidade(Enum):
    SIMPLES   = "simples"
    MEDIA     = "media"
    COMPLEXA  = "complexa"
    AUTOMACAO = "automacao"


# ============================================================
# PALAVRAS-CHAVE
# ============================================================

PALAVRAS_CRIAR = [
    "adiciona", "adicionar", "cria", "criar",
    "nova tarefa", "novo boleto", "cadastra",
    "coloca", "insere", "anota",
]

PALAVRAS_LISTAR = [
    "listar", "mostrar", "ver", "quais", "lista",
    "tenho hoje", "pendentes", "atrasadas",
    "do mes", "do dia",
]

PALAVRAS_CONCLUIR = [
    "marca", "marcar", "concluir", "conclui",
    "feito", "pago", "paguei", "finaliza",
    "done", "ok", "pronto",
]

PALAVRAS_ANALISAR = [
    "analisar", "analisa", "resumir", "resume",
    "sugerir", "sugere", "priorizar", "prioriza",
    "relatorio", "historico",
]

PALAVRAS_AUTOMACAO = [
    "baixar", "baixa", "download",
    "acessar", "acessa", "logar",
    "portal", "site da light", "site do banco",
    "automaticamente",
]


# ============================================================
# CLASSIFICADOR
# ============================================================

def classificar_intencao(mensagem: str) -> str:
    """Classifica a intenção da mensagem"""
    msg = mensagem.lower()

    for p in PALAVRAS_AUTOMACAO:
        if p in msg:
            return "automacao"
    for p in PALAVRAS_CRIAR:
        if p in msg:
            return "criar"
    for p in PALAVRAS_CONCLUIR:
        if p in msg:
            return "concluir"
    for p in PALAVRAS_LISTAR:
        if p in msg:
            return "listar"
    for p in PALAVRAS_ANALISAR:
        if p in msg:
            return "analisar"

    return "conversa"


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """Voce e um assistente da Comprimoveis, empresa de administracao de condominios no RJ.
Ajuda Vanessa com tarefas, pagamentos e calendario.

Condominios: Village Mananciais, Colina Verde, Village Tucanos, Itaipu, Samira,
Nascente Rio Grande, Anchieta, Village Ipadu, Sylvania, Village Pedras, Primavera

Responda SEMPRE em portugues do Brasil. Seja objetivo e amigavel.
"""


# ============================================================
# EXTRATORES (Gemini extrai dados da mensagem)
# ============================================================

async def extrair_dados_tarefa(mensagem: str) -> dict:
    """Usa Gemini para extrair dados estruturados da mensagem"""
    from datetime import datetime
    hoje = datetime.now()

    prompt = f"""Extraia os dados desta mensagem e retorne APENAS um JSON valido, sem explicacoes.

Mensagem: "{mensagem}"

Retorne exatamente neste formato:
{{
    "titulo": "titulo da tarefa",
    "condominio": "nome do condominio ou null",
    "dia": numero do dia ou null,
    "mes": {hoje.month},
    "ano": {hoje.year},
    "urgente": false,
    "categoria": "pagamento ou geral"
}}

Exemplos:
- "boleto Light" -> categoria: "pagamento"
- "reuniao sindico" -> categoria: "geral"
- "URGENTE" ou "urgente" -> urgente: true
"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    try:
        import json
        texto = response.text.strip()
        texto = texto.replace("```json", "").replace("```", "").strip()
        dados = json.loads(texto)

        # Garante que mes e ano nunca vêm null
        if not dados.get("mes"):
            dados["mes"] = hoje.month
        if not dados.get("ano"):
            dados["ano"] = hoje.year

        return dados
    except Exception as e:
        logger.error(f"Erro ao extrair dados: {e}")
        return {
            "titulo": mensagem,
            "condominio": None,
            "dia": None,
            "mes": hoje.month,
            "ano": hoje.year,
            "urgente": False,
            "categoria": "geral"
        }


async def extrair_id_tarefa(mensagem: str, tarefas: list) -> int:
    """Usa Gemini para identificar qual tarefa o usuário quer concluir"""
    if not tarefas:
        return None

    lista = "\n".join([f"ID {t['id']}: {t['titulo']} - {t['condominio']}" for t in tarefas])

    prompt = f"""O usuario disse: "{mensagem}"

Tarefas disponíveis:
{lista}

Qual o ID da tarefa que o usuario quer marcar como concluida?
Retorne APENAS o numero do ID, sem explicacoes."""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    try:
        tarefa_id = int(response.text.strip())
        return tarefa_id
    except:
        return None


# ============================================================
# PROCESSADOR PRINCIPAL
# ============================================================

async def processar_mensagem(mensagem: str, historico: list = None) -> dict:
    """
    Processa mensagem da Vanessa e executa a acao correta
    """
    from datetime import datetime
    hoje = datetime.now()

    if historico is None:
        historico = []

    intencao = classificar_intencao(mensagem)
    logger.info(f"Mensagem: '{mensagem[:50]}' -> {intencao}")

    db = SessionLocal()

    try:

        # ── CRIAR TAREFA ──
        if intencao == "criar":
            logger.info("Acao: CRIAR tarefa")
            dados = await extrair_dados_tarefa(mensagem)

            resultado = criar_tarefa(
                db=db,
                titulo=dados.get("titulo", mensagem),
                mes=dados.get("mes", hoje.month),
                ano=dados.get("ano", hoje.year),
                condominio_nome=dados.get("condominio"),
                dia_vencimento=dados.get("dia"),
                urgente=dados.get("urgente", False),
                categoria=dados.get("categoria", "geral")
            )

            if resultado["sucesso"]:
                cond = f" - {dados.get('condominio')}" if dados.get('condominio') else ""
                dia = f" para o dia {dados.get('dia')}" if dados.get('dia') else ""
                resposta = f"Tarefa criada! '{resultado['titulo']}'{cond}{dia}"
            else:
                resposta = "Nao consegui criar a tarefa. Pode repetir?"

            return {
                "resposta": resposta,
                "acao": "criar",
                "dados": resultado
            }

        # ── LISTAR TAREFAS ──
        elif intencao == "listar":
            logger.info("Acao: LISTAR tarefas")
            tarefas = listar_pendentes(db, mes=hoje.month, ano=hoje.year)

            if not tarefas:
                resposta = "Nenhuma tarefa pendente este mes!"
            else:
                linhas = [f"Voce tem {len(tarefas)} tarefa(s) pendente(s):\n"]
                for t in tarefas:
                    dia = f"Dia {t['dia']} - " if t['dia'] else ""
                    urgente = " URGENTE!" if t['urgente'] else ""
                    linhas.append(f"[{t['id']}] {dia}{t['titulo']} ({t['condominio']}){urgente}")
                resposta = "\n".join(linhas)

            return {
                "resposta": resposta,
                "acao": "listar",
                "dados": tarefas
            }

        # ── CONCLUIR TAREFA ──
        elif intencao == "concluir":
            logger.info("Acao: CONCLUIR tarefa")
            tarefas = listar_pendentes(db, mes=hoje.month, ano=hoje.year)
            tarefa_id = await extrair_id_tarefa(mensagem, tarefas)

            if tarefa_id:
                resultado = marcar_concluida(db, tarefa_id)
                if resultado["sucesso"]:
                    resposta = f"Tarefa '{resultado['titulo']}' marcada como concluida!"
                else:
                    resposta = "Nao encontrei essa tarefa. Qual o numero dela?"
            else:
                resposta = "Qual tarefa voce quer marcar como concluida? Me diz o numero ou o nome!"

            return {
                "resposta": resposta,
                "acao": "concluir"
            }

        # ── ANALISAR ──
        elif intencao == "analisar":
            logger.info("Acao: ANALISAR pendencias")
            tarefas = listar_pendentes(db, mes=hoje.month, ano=hoje.year)

            if not tarefas:
                return {
                    "resposta": "Nenhuma pendencia este mes!",
                    "acao": "analisar"
                }

            lista = "\n".join([
                f"- {t['titulo']} ({t['condominio']}) - Dia {t['dia']}"
                for t in tarefas
            ])

            prompt = f"""{SYSTEM_PROMPT}

Vanessa tem estas pendencias:
{lista}

{mensagem}

Analise e sugira prioridades de forma objetiva."""

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )

            return {
                "resposta": response.text,
                "acao": "analisar"
            }

        # ── AUTOMACAO ──
        elif intencao == "automacao":
            return {
                "resposta": "Automacao em desenvolvimento! Em breve o agente fara isso sozinho.",
                "acao": "automacao"
            }

        # ── CONVERSA GERAL ──
        else:
            logger.info("Acao: CONVERSA geral")
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"{SYSTEM_PROMPT}\n\nVanessa: {mensagem}"
            )
            return {
                "resposta": response.text,
                "acao": "conversa"
            }

    except Exception as e:
        logger.error(f"Erro: {e}")
        return {
            "resposta": "Erro ao processar. Tente novamente.",
            "acao": "erro"
        }
    finally:
        db.close()


# ============================================================
# TESTE
# ============================================================

if __name__ == "__main__":
    testes = [
        "Quais tarefas tenho pendentes?",
        "Adiciona boleto da Light dia 15 Village Mananciais",
        "Marca como pago o boleto da Light",
        "Analisa minhas pendencias",
        "Baixa o boleto da Igua automaticamente",
    ]

    print("\nTESTANDO AGENTE COMPLETO\n")
    print("=" * 50)

    async def rodar():
        for msg in testes:
            print(f"\nVanessa: '{msg}'")
            resultado = await processar_mensagem(msg)
            print(f"Agente: {resultado['resposta']}")
            print(f"Acao: {resultado['acao']}")
            print("-" * 50)

    asyncio.run(rodar())