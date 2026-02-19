"""
AI ROUTER v2.1 - Roteador Inteligente com Prompts Dinâmicos e Contexto
FIX: Client Gemini com inicialização lazy para evitar api_key=None no import
"""

import os
import json
import asyncio
import unicodedata
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


# ============================================================
# CLIENTE GEMINI — INICIALIZAÇÃO LAZY (FIX DO BUG)
# ============================================================
# PROBLEMA: client = genai.Client(api_key=os.getenv(...)) no nível do módulo
# cria o client no momento do `import`, antes do .env estar carregado.
# Se GEMINI_API_KEY for None nesse momento, o SDK usa ADC (Application Default
# Credentials) que pode estar vencido → erro "API key expired".
#
# SOLUÇÃO: inicializar o client apenas quando a API for chamada de fato,
# garantindo que load_dotenv() já rodou.

_client_cache: genai.Client | None = None


def _get_client() -> genai.Client:
    """
    Retorna o cliente Gemini (singleton por processo).
    Cria o client na primeira chamada — lazy — evitando o problema de
    módulo importado antes do .env estar disponível.
    """
    global _client_cache

    if _client_cache is not None:
        return _client_cache

    # Garante que .env está carregado (idempotente — sem efeito se já estiver)
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY não encontrada. "
            "Verifique se o arquivo .env existe e contém GEMINI_API_KEY=..."
        )

    # Log parcial da chave para confirmar qual está sendo usada
    logger.info(f"Inicializando cliente Gemini (key: ...{api_key[-6:]})")

    _client_cache = genai.Client(api_key=api_key)
    return _client_cache


# ============================================================
# PALAVRAS-CHAVE — INTENÇÕES
# ============================================================

PALAVRAS_CONDOMINIOS = [
    "condominios", "condominio",
    "quais condominios", "lista condominios",
    "que condominios", "quais sao", 
    "condominios temos", "condominios tem",
    "condominios ativos", "condominios cadastrados",
    "quais prédios", "que prédios",  # adiciona variações
]

PALAVRAS_CRIAR = [
    "adiciona", "adicionar", "adicione",
    "cria", "criar", "crie",
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
# NORMALIZADOR DE TEXTO (remove acentos para comparação)
# ============================================================

def _sem_acento(texto: str) -> str:
    """
    Converte texto para minúsculas e remove acentos.
    'Condomínios' → 'condominios'   'prédio' → 'predio'
    Necessário porque as listas de palavras não têm acentos,
    mas os usuários digitam texto acentuado.
    """
    return (
        unicodedata.normalize("NFKD", texto)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )


# ============================================================
# CLASSIFICADOR DE INTENÇÃO
# ============================================================

def classificar_intencao(mensagem: str) -> str:
    """Classifica a intenção da mensagem.
    PRIORIDADE: Se menciona condomínios → sempre retorna 'condominios'.
    Usa normalização unicode para ignorar acentos na comparação.
    """
    msg = _sem_acento(mensagem)   # "Condomínios" → "condominios"

    # AUTOMAÇÃO
    for p in PALAVRAS_AUTOMACAO:
        if p in msg:
            return "automacao"

    # CONDOMÍNIOS — verificação explícita e direta (sem acentos)
    palavras_cond = ["condominio", "condominios", "predio", "predios"]
    for palavra in palavras_cond:
        if palavra in msg:
            return "condominios"   # retorna IMEDIATAMENTE

    # CRIAR
    for p in PALAVRAS_CRIAR:
        if p in msg:
            return "criar"

    # CONCLUIR
    for p in PALAVRAS_CONCLUIR:
        if p in msg:
            return "concluir"

    # ANALISAR
    for p in PALAVRAS_ANALISAR:
        if p in msg:
            return "analisar"

    # LISTAR (só chega aqui se NÃO mencionou condomínios)
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
    nomes_condominios = (
        ", ".join([c["nome"] for c in condominios])
        if condominios else "nenhum cadastrado"
    )

    status_pendentes = ""
    if n_pendentes > 0:
        urgencia = (
            f" ({n_urgentes} URGENTE{'S' if n_urgentes > 1 else ''})"
            if n_urgentes > 0 else ""
        )
        status_pendentes = f"\nPendencias este mes: {n_pendentes} tarefa(s){urgencia}."

    contexto_historico = ""
    if historico:
        pares = []
        for item in historico[-6:]:
            role = "Vanessa" if item.get("role") == "user" else "Assistente"
            pares.append(f"{role}: {item.get('content', '')}")
        if pares:
            contexto_historico = "\n\nContexto da conversa:\n" + "\n".join(pares)

    return (
        f"Voce e o assistente da Comprimoveis, empresa de administracao de condominios no RJ.\n"
        f"Voce ajuda Vanessa com tarefas, pagamentos e calendario de vencimentos.\n\n"
        f"Condominios ativos no sistema: {nomes_condominios}{status_pendentes}{contexto_historico}\n\n"
        f"Regras:\n"
        f"- Responda SEMPRE em portugues do Brasil\n"
        f"- Seja objetivo, amigavel e use emojis quando adequado\n"
        f"- Ao listar tarefas, use o formato: [ID] Dia XX - Titulo (Condominio)\n"
        f"- Nunca invente dados — use apenas o que o sistema fornece\n"
        f"- Se nao souber algo, diga isso e oriente Vanessa"
    )


# ============================================================
# EXTRATORES COM IA
# ============================================================

async def extrair_dados_tarefa(mensagem: str, condominios_validos: list = None) -> dict:
    """Usa Gemini para extrair dados estruturados de uma mensagem de criação de tarefa."""
    hoje = datetime.now()

    lista_condominios = ""
    if condominios_validos:
        nomes = [c["nome"] for c in condominios_validos]
        lista_condominios = f"\nCondominios validos: {', '.join(nomes)}"

    prompt = (
        f'Extraia os dados desta mensagem e retorne APENAS um JSON valido, sem explicacoes.\n\n'
        f'Mensagem: "{mensagem}"\n'
        f'{lista_condominios}\n\n'
        f'Retorne exatamente neste formato:\n'
        f'{{\n'
        f'    "titulo": "titulo resumido da tarefa",\n'
        f'    "condominio": "nome exato do condominio ou null",\n'
        f'    "dia": numero do dia ou null,\n'
        f'    "mes": {hoje.month},\n'
        f'    "ano": {hoje.year},\n'
        f'    "urgente": false,\n'
        f'    "categoria": "pagamento ou geral"\n'
        f'}}\n\n'
        f'Regras:\n'
        f'- "boleto", "conta", "fatura", "pagar" -> categoria: "pagamento"\n'
        f'- "reuniao", "vistoria", "ligar", "enviar" -> categoria: "geral"\n'
        f'- "URGENTE" ou "urgente" na mensagem -> urgente: true\n'
        f'- Se o condominio nao estiver na lista valida, retorne null\n'
        f'- O titulo deve ser curto e descritivo (ex: "Boleto Light", "Reuniao sindico")'
    )

    client = _get_client()
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    try:
        texto = response.text.strip()
        texto = texto.replace("```json", "").replace("```", "").strip()
        dados = json.loads(texto)

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

    prompt = (
        f'Vanessa disse: "{mensagem}"\n'
        f'{contexto}\n\n'
        f'Tarefas pendentes disponiveis:\n'
        f'{lista}\n\n'
        f'Qual o ID da tarefa que Vanessa quer marcar como concluida?\n'
        f'Analise o contexto da conversa para entender a qual tarefa ela se refere.\n'
        f'Retorne APENAS o numero do ID, sem explicacoes.\n'
        f'Se nao for possivel identificar com certeza, retorne: null'
    )

    client = _get_client()
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
    logger.info(f"Mensagem: '{mensagem[:60]}' -> intencao: {intencao}")

    db = SessionLocal()

    try:
        # Carrega dados do banco uma única vez
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
            logger.info("Acao: LISTAR condominios")
            if not condominios:
                resposta = "Nenhum condominio cadastrado no sistema ainda."
            else:
                linhas = [f"Condominios ativos ({len(condominios)}):"]
                for i, c in enumerate(condominios, 1):
                    linhas.append(f"  {i}. {c['nome']}")
                resposta = "\n".join(linhas)

            return {"resposta": resposta, "acao": "condominios", "dados": condominios}

        # ── CRIAR TAREFA ──
        elif intencao == "criar":
            logger.info("Acao: CRIAR tarefa")
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
                cond = f" - {dados.get('condominio')}" if dados.get("condominio") else ""
                dia = f" para o dia {dados.get('dia')}" if dados.get("dia") else ""
                urgente_txt = " URGENTE!" if dados.get("urgente") else ""
                resposta = f"Tarefa criada!{urgente_txt}\n'{resultado['titulo']}'{cond}{dia}"
            else:
                resposta = "Nao consegui criar a tarefa. Pode tentar de novo com mais detalhes?"

            return {"resposta": resposta, "acao": "criar", "dados": resultado}

        # ── LISTAR TAREFAS ──
        elif intencao == "listar":
            logger.info("Acao: LISTAR tarefas pendentes")

            if not tarefas_mes:
                resposta = "Nenhuma tarefa pendente este mes!"
            else:
                lista_txt = "\n".join([
                    f"[{t['id']}] "
                    + (f"Dia {t['dia']} - " if t.get('dia') else "")
                    + f"{t['titulo']} ({t['condominio']})"
                    + (" URGENTE!" if t.get("urgente") else "")
                    for t in tarefas_mes
                ])

                prompt_listar = (
                    f"{system_prompt}\n\n"
                    f'Vanessa perguntou: "{mensagem}"\n\n'
                    f"Tarefas pendentes deste mes:\n{lista_txt}\n\n"
                    f"Responda de forma clara e organizada. Se a pergunta for especifica "
                    f"(ex: 'tarefas de pagamento'), filtre apenas as relevantes. "
                    f"Caso contrario, liste todas."
                )

                client = _get_client()
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt_listar
                )
                resposta = response.text

            return {"resposta": resposta, "acao": "listar", "dados": tarefas_mes}

        # ── CONCLUIR TAREFA ──
        elif intencao == "concluir":
            logger.info("Acao: CONCLUIR tarefa")
            tarefa_id = await extrair_id_tarefa(mensagem, tarefas_mes, historico=historico)

            if tarefa_id:
                resultado = marcar_concluida(db, tarefa_id)
                if resultado["sucesso"]:
                    resposta = f"'{resultado['titulo']}' marcada como concluida!"
                else:
                    resposta = "Nao encontrei essa tarefa. Qual o numero ou nome dela?"
            else:
                resposta = "Qual tarefa voce quer marcar como concluida?\nMe diz o numero [ID] ou o nome!"

            return {"resposta": resposta, "acao": "concluir"}

        # ── ANALISAR ──
        elif intencao == "analisar":
            logger.info("Acao: ANALISAR pendencias")

            if not tarefas_mes:
                return {"resposta": "Nenhuma pendencia este mes! Tudo em dia.", "acao": "analisar"}

            lista_txt = "\n".join([
                f"- {t['titulo']} ({t['condominio']})"
                + (f" - Dia {t['dia']}" if t.get('dia') else "")
                + (" URGENTE!" if t.get("urgente") else "")
                for t in tarefas_mes
            ])

            prompt_analise = (
                f"{system_prompt}\n\n"
                f"Vanessa tem estas pendencias este mes:\n{lista_txt}\n\n"
                f'Solicitacao: "{mensagem}"\n\n'
                f"Analise as pendencias e sugira prioridades de forma objetiva. "
                f"Agrupe por condominio quando fizer sentido. Destaque as urgentes primeiro."
            )

            client = _get_client()
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt_analise
            )

            return {"resposta": response.text, "acao": "analisar"}

        # ── AUTOMAÇÃO ──
        elif intencao == "automacao":
            return {
                "resposta": "Automacao em desenvolvimento!\nEm breve o agente fara isso sozinho.",
                "acao": "automacao"
            }

        # ── CONVERSA GERAL ──
        else:
            logger.info("Acao: CONVERSA geral")
            prompt_conversa = (
                f"{system_prompt}\n\n"
                f"Vanessa: {mensagem}\n\n"
                f"Responda de forma util e objetiva. Se a pergunta for sobre tarefas, "
                f"pagamentos ou condominios, use as informacoes do sistema acima."
            )

            client = _get_client()
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt_conversa
            )

            return {"resposta": response.text, "acao": "conversa"}

    except EnvironmentError as e:
        # Erro de configuração — chave ausente
        logger.error(f"Erro de configuracao: {e}")
        return {
            "resposta": f"Erro de configuracao: {str(e)}",
            "acao": "erro"
        }
    except Exception as e:
        # Qualquer outro erro — loga com detalhes para debugging
        logger.error(f"Erro no processador [{type(e).__name__}]: {e}")
        return {
            "resposta": f"Erro ao processar. Tente novamente em instantes.",
            "acao": "erro"
        }
    finally:
        db.close()


# ============================================================
# TESTE DO CLASSIFICADOR (rode antes de commitar)
# ============================================================

def _testar_classificacao():
    """Testa todos os cenários do classificador sem chamar a API."""
    testes = [
        # Condomínios COM acento (bug original)
        ("Quais condomínios atendemos?",     "condominios"),
        ("Lista os condomínios",             "condominios"),
        ("Mostre os prédios",                "condominios"),
        # Condomínios SEM acento
        ("Quais condominios atendemos?",     "condominios"),
        ("Lista os condominios",             "condominios"),
        ("Mostre os predios",                "condominios"),
        # Listar tarefas (NÃO deve ir para condominios)
        ("Quais tarefas tenho?",             "listar"),
        ("Liste pendentes",                  "listar"),
        ("Mostrar tarefas do mes",           "listar"),
        # Criar
        ("Adicione boleto Light",            "criar"),
        ("Adiciona reuniao sindico",         "criar"),
        # Concluir
        ("Marca como concluído",             "concluir"),
        ("Marcar como pago",                 "concluir"),
        # Analisar
        ("Analisa minhas pendencias",        "analisar"),
        ("Prioriza as urgentes",             "analisar"),
        # Conversa
        ("Olá, tudo bem?",                   "conversa"),
    ]

    print("\nTESTANDO CLASSIFICACAO DE INTENCAO:\n")
    todos_passaram = True
    for mensagem, esperado in testes:
        resultado = classificar_intencao(mensagem)
        ok = resultado == esperado
        status = "OK" if ok else "FALHOU"
        print(f"  [{status}] '{mensagem}' -> {resultado} (esperado: {esperado})")
        if not ok:
            todos_passaram = False

    print()
    if todos_passaram:
        print("TODOS OS TESTES PASSARAM!")
    else:
        print("ALGUNS TESTES FALHARAM - CORRIJA ANTES DE COMMITAR")

    return todos_passaram


# ============================================================
# TESTE LOCAL
# ============================================================

if __name__ == "__main__":
    _testar_classificacao()
    print()

if __name__ == "__main__":
    testes = [
        "Olá, tudo bem?",
        "Quais condominios atendemos?",
        "Adicione boleto Light Village Mananciais 450 dia 19",
        "Quais tarefas tenho pendentes?",
        "Analisa minhas pendencias e sugere prioridades",
    ]

    print("\nTESTANDO AGENTE v2.1 — LAZY CLIENT + PROMPTS DINAMICOS\n")
    print("=" * 55)

    async def rodar():
        historico = []
        for msg in testes:
            print(f"\nVanessa: '{msg}'")
            resultado = await processar_mensagem(msg, historico=historico)
            print(f"Agente: {resultado['resposta']}")
            print(f"Acao: {resultado['acao']}")
            print("-" * 55)
            historico.append({"role": "user", "content": msg})
            historico.append({"role": "assistant", "content": resultado["resposta"]})

    asyncio.run(rodar())
