"""
AI ROUTER v2 - Roteador Inteligente com Prompts Dinâmicos e Contexto
"""

import os
import json
import asyncio
from datetime import datetime
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
# PALAVRAS-CHAVE — INTENÇÕES
# ============================================================

PALAVRAS_CONDOMINIOS = [
    "condominios", "condominio", "quais condominios", "lista condominios",
    "que condominios", "quais sao", "condominios temos", "condominios tem",
    "condominios ativos", "condominios cadastrados",
]

PALAVRAS_CRIAR = [
    "adiciona", "adicionar", "cria", "criar",
    "nova tarefa", "novo boleto", "cadastra",
    "coloca", "insere", "anota",
]

PALAVRAS_LISTAR = [
    "listar", "mostrar", "ver", "quais", "lista",
    "tenho hoje", "pendentes", "atrasadas",
    "do mes", "do dia", "minhas tarefas", "meus boletos",
]

PALAVRAS_CONCLUIR = [
    "marca", "marcar", "concluir", "conclui",
    "feito", "pago", "paguei", "finaliza",
    "done", "ok", "pronto", "marcar como", "concluido",
]

PALAVRAS_ANALISAR = [
    "analisar", "analisa", "resumir", "resume",
    "sugerir", "sugere", "priorizar", "prioriza",
    "relatorio", "historico", "prioridade", "mais urgente",
]

PALAVRAS_AUTOMACAO = [
    "baixar", "baixa", "download",
    "acessar", "acessa", "logar",
    "portal", "site da light", "site do banco",
    "automaticamente",
]


# ============================================================
# CLASSIFICADOR DE INTENÇÃO
# ============================================================

def classificar_intencao(mensagem: str) -> str:
    """Classifica a intenção da mensagem.
    Ordem importa: condominios ANTES de listar para evitar falso-positivo em 'quais'.
    """
    msg = mensagem.lower()

    for p in PALAVRAS_AUTOMACAO:
        if p in msg:
            return "automacao"
    for p in PALAVRAS_CONDOMINIOS:
        if p in msg:
            return "condominios"
    for p in PALAVRAS_CRIAR:
        if p in msg:
            return "criar"
    for p in PALAVRAS_CONCLUIR:
        if p in msg:
            return "concluir"
    for p in PALAVRAS_ANALISAR:
        if p in msg:
            return "analisar"
    for p in PALAVRAS_LISTAR:
        if p in msg:
            return "listar"

    return "conversa"


# ============================================================
# CONSTRUTOR DE PROMPT DINÂMICO
# ============================================================

def construir_prompt_sistema(
    condominios: list,
    n_pendentes: int = 0,
    n_urgentes: int = 0,
    historico: list = None
) -> str:
    """Monta o system prompt com dados reais do banco em tempo real."""
    nomes_condominios = ", ".join([c["nome"] for c in condominios]) if condominios else "nenhum cadastrado"

    status_pendentes = ""
    if n_pendentes > 0:
        urgencia = f" ({n_urgentes} URGENTE{'S' if n_urgentes > 1 else ''})" if n_urgentes > 0 else ""
        status_pendentes = f"\nPendências este mês: {n_pendentes} tarefa(s){urgencia}."

    contexto_historico = ""
    if historico:
        pares = []
        for item in historico[-6:]:  # últimas 6 mensagens
            role = "Vanessa" if item.get("role") == "user" else "Assistente"
            pares.append(f"{role}: {item.get('content', '')}")
        if pares:
            contexto_historico = "\n\nContexto da conversa:\n" + "\n".join(pares)

    prompt = f"""Você é o assistente da Comprimóveis, empresa de administração de condomínios no RJ.
Você ajuda Vanessa com tarefas, pagamentos e calendário de vencimentos.

Condomínios ativos no sistema: {nomes_condominios}{status_pendentes}{contexto_historico}

Regras:
- Responda SEMPRE em português do Brasil
- Seja objetivo, amigável e use emojis quando adequado
- Ao listar tarefas, use o formato: [ID] Dia XX - Título (Condomínio)
- Nunca invente dados — use apenas o que o sistema fornece
- Se não souber algo, diga isso e oriente Vanessa"""

    return prompt


# ============================================================
# EXTRATORES COM IA
# ============================================================

async def extrair_dados_tarefa(mensagem: str, condominios_validos: list = None) -> dict:
    """Usa Gemini para extrair dados estruturados de uma mensagem de criação de tarefa."""
    hoje = datetime.now()

    lista_condominios = ""
    if condominios_validos:
        nomes = [c["nome"] for c in condominios_validos]
        lista_condominios = f"\nCondomínios válidos: {', '.join(nomes)}"

    prompt = f"""Extraia os dados desta mensagem e retorne APENAS um JSON válido, sem explicações.

Mensagem: "{mensagem}"
{lista_condominios}

Retorne exatamente neste formato:
{{
    "titulo": "título resumido da tarefa",
    "condominio": "nome exato do condomínio ou null",
    "dia": número do dia ou null,
    "mes": {hoje.month},
    "ano": {hoje.year},
    "urgente": false,
    "categoria": "pagamento ou geral"
}}

Regras:
- "boleto", "conta", "fatura", "pagar" → categoria: "pagamento"
- "reunião", "vistoria", "ligar", "enviar" → categoria: "geral"
- "URGENTE" ou "urgente" na mensagem → urgente: true
- Se o condomínio não estiver na lista válida, retorne null
- O título deve ser curto e descritivo (ex: "Boleto Light", "Reunião síndico")"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    try:
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
        logger.error(f"Erro ao extrair dados da tarefa: {e}")
        return {
            "titulo": mensagem,
            "condominio": None,
            "dia": None,
            "mes": hoje.month,
            "ano": hoje.year,
            "urgente": False,
            "categoria": "geral"
        }


async def extrair_id_tarefa(mensagem: str, tarefas: list, historico: list = None) -> int:
    """Usa Gemini para identificar qual tarefa o usuário quer concluir,
    considerando o contexto da conversa."""
    if not tarefas:
        return None

    lista = "\n".join([
        f"ID {t['id']}: {t['titulo']} - {t['condominio']}"
        + (f" (Dia {t['dia']})" if t.get('dia') else "")
        for t in tarefas
    ])

    contexto = ""
    if historico:
        ultimas = historico[-4:]
        pares = []
        for item in ultimas:
            role = "Vanessa" if item.get("role") == "user" else "Assistente"
            pares.append(f"{role}: {item.get('content', '')}")
        if pares:
            contexto = "\nContexto recente:\n" + "\n".join(pares)

    prompt = f"""Vanessa disse: "{mensagem}"
{contexto}

Tarefas pendentes disponíveis:
{lista}

Qual o ID da tarefa que Vanessa quer marcar como concluída?
Analise o contexto da conversa para entender a qual tarefa ela se refere.
Retorne APENAS o número do ID, sem explicações.
Se não for possível identificar com certeza, retorne: null"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    try:
        texto = response.text.strip()
        if texto.lower() == "null" or not texto.isdigit():
            return None
        return int(texto)
    except Exception:
        return None


# ============================================================
# PROCESSADOR PRINCIPAL
# ============================================================

async def processar_mensagem(mensagem: str, historico: list = None) -> dict:
    """
    Processa mensagem da Vanessa e executa a ação correta.
    Usa dados dinâmicos do banco e passa contexto para todos os calls Gemini.
    """
    hoje = datetime.now()

    if historico is None:
        historico = []

    intencao = classificar_intencao(mensagem)
    logger.info(f"Mensagem: '{mensagem[:60]}' → intenção: {intencao}")

    db = SessionLocal()

    try:
        # Carrega dados do banco uma única vez para usar em todo o processamento
        condominios = listar_condominios(db)
        tarefas_mes = listar_pendentes(db, mes=hoje.month, ano=hoje.year)
        n_pendentes = len(tarefas_mes)
        n_urgentes = sum(1 for t in tarefas_mes if t.get("urgente"))

        # Monta prompt dinâmico com dados reais
        system_prompt = construir_prompt_sistema(
            condominios=condominios,
            n_pendentes=n_pendentes,
            n_urgentes=n_urgentes,
            historico=historico
        )

        # ── LISTAR CONDOMÍNIOS ──
        if intencao == "condominios":
            logger.info("Ação: LISTAR condomínios")
            if not condominios:
                resposta = "Nenhum condomínio cadastrado no sistema ainda."
            else:
                linhas = [f"🏢 Condomínios ativos ({len(condominios)}):"]
                for i, c in enumerate(condominios, 1):
                    linhas.append(f"  {i}. {c['nome']}")
                resposta = "\n".join(linhas)

            return {
                "resposta": resposta,
                "acao": "condominios",
                "dados": condominios
            }

        # ── CRIAR TAREFA ──
        elif intencao == "criar":
            logger.info("Ação: CRIAR tarefa")
            dados = await extrair_dados_tarefa(mensagem, condominios_validos=condominios)

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
                cond = f" — {dados.get('condominio')}" if dados.get("condominio") else ""
                dia = f" para o dia {dados.get('dia')}" if dados.get("dia") else ""
                urgente_txt = " ⚠️ URGENTE" if dados.get("urgente") else ""
                resposta = f"✅ Tarefa criada!{urgente_txt}\n📌 '{resultado['titulo']}'{cond}{dia}"
            else:
                resposta = "❌ Não consegui criar a tarefa. Pode tentar de novo com mais detalhes?"

            return {
                "resposta": resposta,
                "acao": "criar",
                "dados": resultado
            }

        # ── LISTAR TAREFAS ──
        elif intencao == "listar":
            logger.info("Ação: LISTAR tarefas pendentes")

            if not tarefas_mes:
                resposta = "🎉 Nenhuma tarefa pendente este mês!"
            else:
                # Usa Gemini para responder de forma contextual
                lista_txt = "\n".join([
                    f"[{t['id']}] "
                    + (f"Dia {t['dia']} - " if t.get('dia') else "")
                    + f"{t['titulo']} ({t['condominio']})"
                    + (" ⚠️ URGENTE" if t.get("urgente") else "")
                    for t in tarefas_mes
                ])

                prompt_listar = f"""{system_prompt}

Vanessa perguntou: "{mensagem}"

Tarefas pendentes deste mês:
{lista_txt}

Responda de forma clara e organizada. Se a pergunta for específica (ex: "tarefas de pagamento"),
filtre apenas as relevantes. Caso contrário, liste todas."""

                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt_listar
                )
                resposta = response.text

            return {
                "resposta": resposta,
                "acao": "listar",
                "dados": tarefas_mes
            }

        # ── CONCLUIR TAREFA ──
        elif intencao == "concluir":
            logger.info("Ação: CONCLUIR tarefa")
            tarefa_id = await extrair_id_tarefa(mensagem, tarefas_mes, historico=historico)

            if tarefa_id:
                resultado = marcar_concluida(db, tarefa_id)
                if resultado["sucesso"]:
                    resposta = f"✅ '{resultado['titulo']}' marcada como concluída!"
                else:
                    resposta = "⚠️ Não encontrei essa tarefa. Qual o número ou nome dela?"
            else:
                resposta = "❓ Qual tarefa você quer marcar como concluída?\nMe diz o número [ID] ou o nome!"

            return {
                "resposta": resposta,
                "acao": "concluir"
            }

        # ── ANALISAR ──
        elif intencao == "analisar":
            logger.info("Ação: ANALISAR pendências")

            if not tarefas_mes:
                return {
                    "resposta": "🎉 Nenhuma pendência este mês! Tudo em dia.",
                    "acao": "analisar"
                }

            lista_txt = "\n".join([
                f"- {t['titulo']} ({t['condominio']})"
                + (f" - Dia {t['dia']}" if t.get('dia') else "")
                + (" ⚠️ URGENTE" if t.get("urgente") else "")
                for t in tarefas_mes
            ])

            prompt_analise = f"""{system_prompt}

Vanessa tem estas pendências este mês:
{lista_txt}

Solicitação: "{mensagem}"

Analise as pendências e sugira prioridades de forma objetiva.
Agrupe por condomínio quando fizer sentido. Destaque as urgentes primeiro."""

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt_analise
            )

            return {
                "resposta": response.text,
                "acao": "analisar"
            }

        # ── AUTOMAÇÃO ──
        elif intencao == "automacao":
            return {
                "resposta": "🤖 Automação em desenvolvimento!\nEm breve o agente fará isso sozinho.",
                "acao": "automacao"
            }

        # ── CONVERSA GERAL ──
        else:
            logger.info("Ação: CONVERSA geral")
            prompt_conversa = f"""{system_prompt}

Vanessa: {mensagem}

Responda de forma útil e objetiva. Se a pergunta for sobre tarefas, pagamentos ou condomínios,
use as informações do sistema acima."""

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt_conversa
            )

            return {
                "resposta": response.text,
                "acao": "conversa"
            }

    except Exception as e:
        logger.error(f"Erro no processador: {e}")
        return {
            "resposta": "❌ Erro ao processar. Tente novamente em instantes.",
            "acao": "erro"
        }
    finally:
        db.close()


# ============================================================
# TESTE LOCAL
# ============================================================

if __name__ == "__main__":
    testes = [
        "Quais condomínios temos?",
        "Quais tarefas tenho pendentes?",
        "Adiciona boleto da Light dia 15 Village Mananciais",
        "Adiciona reunião com síndico Colina Verde URGENTE dia 20",
        "boleto Igua Village Tucanos 450 dia 19",
        "Marca como pago o boleto da Light",
        "Analisa minhas pendências e sugere prioridades",
        "Olá, tudo bem?",
    ]

    print("\nTESTANDO AGENTE v2 — PROMPTS DINÂMICOS\n")
    print("=" * 55)

    async def rodar():
        historico = []
        for msg in testes:
            print(f"\n👤 Vanessa: '{msg}'")
            resultado = await processar_mensagem(msg, historico=historico)
            print(f"🤖 Agente: {resultado['resposta']}")
            print(f"   Ação: {resultado['acao']}")
            print("-" * 55)

            # Simula acúmulo de histórico
            historico.append({"role": "user", "content": msg})
            historico.append({"role": "assistant", "content": resultado["resposta"]})

    asyncio.run(rodar())
