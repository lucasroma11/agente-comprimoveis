# Agente Comprimóveis — Changelog

---

## v2.1 — Fevereiro 2026

### Melhorias Implementadas nesta sessão

---

### 1. Migração SDK Gemini (`requirements.txt`)

| Antes | Depois |
|-------|--------|
| `google-generativeai==0.8.6` (deprecated) | `google-genai==1.63.0` (SDK oficial atual) |

**Impacto:** Elimina avisos de deprecação e garante compatibilidade com a API Gemini mais recente.

---

### 2. Design Premium (`app/main.py`)

Aplicado glassmorphism completo inspirado no `calendario_bpo_comprimoveis.py`.

| Antes | Depois |
|-------|--------|
| Interface padrão Streamlit sem customização | Glassmorphism com `backdrop-filter: blur()` |
| Sem identidade visual | Cores oficiais: `#1a2942` (azul) + `#ff6b35` (laranja) |
| Cards simples | Cards com gradiente, sombra e animações |
| Sem animações | `slideDown`, `shimmer`, `scaleIn`, `urgentPulse`, `msgIn` |
| Fonte padrão | Poppins (corpo) + Space Mono (números) |
| Chat sem estilo | Bolhas de chat com animação de entrada |

---

### 3. Botão "Marcar como Concluída" (`app/main.py`)

| Antes | Depois |
|-------|--------|
| Sem ação nos cards de tarefa | Botão ✅ por card (`st.columns([5, 1])`) |
| Precisava digitar no chat para concluir | 1 clique elimina a pendência |
| Sem feedback visual | `st.toast()` confirma a conclusão |
| `processar_mensagem(msg)` sem histórico | `processar_mensagem(msg, historico=historico[-10:])` |

**Trecho adicionado em `main.py`:**
```python
c_card, c_btn = st.columns([5, 1])
with c_btn:
    if st.button("✅", key=f"concluir_{t['id']}", help=f"Concluir '{t['titulo']}'"):
        res = marcar_concluida(db_c, t['id'])
        st.toast(f"✅ '{res['titulo']}' concluída!", icon="✅")
        st.rerun()
```

---

### 4. AI Router v2 — Prompts Dinâmicos (`app/services/ai_router.py`)

#### 4.1 Novo intent: `condominios`

| Antes | Depois |
|-------|--------|
| `"quais condomínios"` → rota `listar` (mostrava tarefas!) | `"quais condomínios"` → rota `condominios` (lista do banco) |
| Nome dos condomínios hardcoded no SYSTEM_PROMPT | Busca em tempo real com `listar_condominios(db)` |

**Bug corrigido:** `PALAVRAS_CONDOMINIOS` é checado **antes** de `PALAVRAS_LISTAR` no classificador, evitando que `"quais"` dispare falso-positivo.

#### 4.2 `construir_prompt_sistema()` — prompt dinâmico

| Antes | Depois |
|-------|--------|
| `SYSTEM_PROMPT` estático (string constante) | `construir_prompt_sistema(condominios, n_pendentes, n_urgentes, historico)` |
| Condomínios hardcoded (podiam estar desatualizados) | Lista real buscada do banco a cada requisição |
| Sem informação de pendências no contexto | Inclui: "Pendências este mês: 5 tarefa(s) (2 URGENTES)" |
| Sem histórico no prompt | Injeta últimas 6 mensagens da conversa no contexto |

#### 4.3 `extrair_dados_tarefa()` — com condomínios válidos

| Antes | Depois |
|-------|--------|
| Sem referência a condomínios no prompt de extração | Passa lista de nomes válidos: "Condomínios válidos: Village Mananciais, ..." |
| Podia gerar nomes inexistentes | Retorna `null` para condomínio não cadastrado |
| Título podia ser a mensagem inteira | Título curto e descritivo (ex: "Boleto Light") |
| Sem exemplos claros de categorias | Regras explícitas: `"boleto/fatura"` → `pagamento`, `"reunião"` → `geral` |

#### 4.4 `extrair_id_tarefa()` — com contexto

| Antes | Depois |
|-------|--------|
| `extrair_id_tarefa(mensagem, tarefas)` | `extrair_id_tarefa(mensagem, tarefas, historico=historico)` |
| Sem contexto → falha em "marca o último" | Últimas 4 mensagens injetadas → identifica por contexto |
| Retornava `None` para texto não-numérico | Trata explicitamente `"null"` e strings não-numéricas |

#### 4.5 Respostas enriquecidas com emojis e formatação

| Antes | Depois |
|-------|--------|
| `"Tarefa criada! 'Boleto Light' - Village Mananciais dia 15"` | `"✅ Tarefa criada!\n📌 'Boleto Light' — Village Mananciais para o dia 15"` |
| `"Nenhuma tarefa pendente este mes!"` | `"🎉 Nenhuma tarefa pendente este mês!"` |
| `"Automacao em desenvolvimento!"` | `"🤖 Automação em desenvolvimento!\nEm breve o agente fará isso sozinho."` |
| `"Qual tarefa voce quer marcar..."` | `"❓ Qual tarefa você quer marcar como concluída?\nMe diz o número [ID] ou o nome!"` |

#### 4.6 `processar_mensagem()` — carrega DB uma única vez

| Antes | Depois |
|-------|--------|
| Cada ação consultava o banco separadamente | `condominios` e `tarefas_mes` carregados 1× por chamada |
| `historico` aceito mas nunca usado | `historico` passado para `construir_prompt_sistema()`, `extrair_id_tarefa()` |
| Intenção `conversa` usava SYSTEM_PROMPT vazio | Usa `system_prompt` dinâmico com dados reais do banco |

---

### 5. Infraestrutura AWS (`setup-systemd-aws.txt`)

Arquivo criado com instruções completas para rodar o Streamlit como serviço systemd 24/7 na EC2.

| Item | Detalhe |
|------|---------|
| Arquivo de serviço | `/etc/systemd/system/agente-comprimoveis.service` |
| Auto-restart | `Restart=always` + `RestartSec=3` |
| Variáveis de ambiente | `EnvironmentFile=/home/ubuntu/agente-comprimoveis/.env` |
| Endpoint | `http://54.242.191.173:8501` |

---

### Cenários de Teste Recomendados

Para validar no site AWS após deploy (`git pull && sudo systemctl restart agente-comprimoveis`):

#### Testes de NLU (novos comportamentos)
1. **"Quais condomínios temos?"** → deve listar do banco, NÃO mostrar tarefas
2. **"boleto Igua Village Tucanos 450 dia 19"** → deve criar tarefa completa em 1 mensagem
3. **"Adiciona reunião com síndico Colina Verde URGENTE dia 20"** → urgente=true, categoria=geral
4. **"Olá, como você pode me ajudar?"** → deve mencionar os condomínios reais do banco

#### Testes de contexto (multi-turn)
5. `"Liste minhas tarefas"` → ver lista → `"Marca a primeira como paga"` → deve identificar por contexto
6. `"Quais tarefas de pagamento tenho?"` → deve filtrar apenas categoria=pagamento

#### Testes de conclusão (novo botão ✅)
7. Clicar ✅ em qualquer card → toast de confirmação + card some
8. Digitar `"marca o boleto da Light como pago"` → deve funcionar via chat também

#### Testes de regressão
9. `"Adiciona boleto da Light dia 15 Village Mananciais"` → criação normal
10. `"Analisa minhas pendências"` → análise com Gemini contextualizado

---

*Gerado automaticamente pelo Agente de desenvolvimento — Fevereiro 2026*
