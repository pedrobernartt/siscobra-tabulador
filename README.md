# Tabulador Siscobra

Ferramenta interna da **Solug Cobranças** para auto-tabulação de ocorrências no Siscobra via IA (**Google Gemini** com camada gratuita, **OpenAI/GPT** ou **Claude**). O operador cola a conversa do WhatsApp e recebe os três campos prontos: **Situação Atual**, **Complemento** e **Descritivo**.

---

## Requisitos

- Python 3.9+
- Uma chave de API de **um** destes provedores:
  - **Google Gemini** — possui **camada gratuita**: https://aistudio.google.com/apikey *(recomendado)*
  - **OpenAI (GPT)** — https://platform.openai.com/api-keys
  - **Anthropic (Claude)** — https://console.anthropic.com/settings/keys

---

## Instalação e execução local

```bash
# 1. Clone ou copie a pasta do projeto
cd siscobra-tabulador

# 2. Crie e ative um ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate           # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Rode a aplicação
streamlit run app.py
```

A interface abre automaticamente em `http://localhost:8501`.

---

## Configuração do provedor de IA

A forma mais simples é pela própria interface:

1. Rode o app e abra a aba **⚙️ Configurações**.
2. Escolha o **Provedor** (o Gemini é gratuito e já vem selecionado).
3. Cole a **Chave de API** e, se quiser, ajuste o **Modelo**.
4. Clique em **Salvar configurações**.

A chave fica salva **localmente** em `config.json` (ignorado pelo Git — nunca é compartilhada).

> Para a chave gratuita do Gemini, acesse https://aistudio.google.com/apikey — basta uma conta Google.

**Alternativa por `.env`** (fallback): copie `.env.example` para `.env` e preencha `PROVIDER`, `MODEL_NAME` e a chave do provedor escolhido.

---

## Rodando os testes

```bash
# Na raiz do projeto (siscobra-tabulador/)
python -m pytest tests/ -v
```

---

## Estrutura do projeto

```
siscobra-tabulador/
├── .env.example          # Template de configuração (fallback)
├── README.md
├── requirements.txt
├── app.py                # Interface Streamlit
├── config.json           # Provedor + modelo + chaves (criado ao salvar; ignorado pelo Git)
├── tabulacoes.db         # Banco SQLite (criado automaticamente)
├── tabulador/
│   ├── __init__.py
│   ├── taxonomia.py      # Fonte da verdade: Situação/Complemento + validação
│   ├── parser.py         # Parser do export do WhatsApp / timeline do Kommo
│   ├── prompt.py         # System prompt dinâmico + few-shot
│   ├── llm.py            # Wrapper multi-provedor (Gemini / OpenAI / Claude)
│   ├── config.py         # Provedor, modelo, chaves e operadores
│   └── db.py             # Log SQLite
└── tests/
    └── test_taxonomia.py
```

---

## Como usar

1. Abra a interface (`streamlit run app.py`)
2. *(Na primeira vez)* configure o provedor de IA e cole a chave na aba **⚙️ Configurações**
3. Cole o export do WhatsApp (ou Kommo / resumo) no campo da esquerda
4. Clique em **Tabular**
5. Confira os campos gerados na coluna direita
6. Edite o descritivo se necessário
7. Clique em **Aprovar** ou **Salvar com edição**
8. Copie os valores para o Siscobra

O histórico completo fica na aba **Histórico**.

---

## Taxonomia suportada

| Situação Atual | Complementos disponíveis |
|----------------|--------------------------|
| Contato (26) | Proposta, Sem interesse, Sem sucesso, Terceiros |
| Acordo (2) | Acordo com uso de Alvará CJ, Acordo extrajudicial à vista CJ, Acordo extrajudicial Parcelado CJ, Acordo judicial à vista CJ, Acordo judicial parcelado CJ |
| Contato com terceiros (6) | Desconhece a pessoa/cobrança, Inquilino, Novo proprietário, Representante legal (Advogado), Recado |
| Dúvidas gerais (3) | Dúvidas de preenchimento link Quita+, Encargos (juros/mora/HO), Solicitação CND, Cliente adimplente |
| Recusa acordo (9) | Alega pagamento, Discorda do valor cobrado, Não informou o motivo, Sem previsão de pagamento |

O sistema **nunca** sugere uma combinação fora desta lista (validado em `taxonomia.py`).

---

## Custo por provedor

| Provedor / modelo | Custo por tabulação |
|-------------------|---------------------|
| **Gemini 2.5 Flash** | **Grátis** dentro da camada gratuita do Google AI Studio |
| Gemini 2.5 Flash-Lite | **Grátis** (cota diária maior, um pouco menos preciso) |
| Gemini 3.5 Flash | **Grátis** com limites mais restritos (modelo mais inteligente) |
| GPT-4o mini | ~US$ 0,001–0,002 |
| Claude Sonnet 4.5 | ~US$ 0,010–0,015 |

Para uso interno de baixo volume, o **Gemini gratuito** costuma ser suficiente. Os limites da camada gratuita (requisições por minuto/dia) são definidos pelo Google e variam por modelo — o Flash-Lite costuma ter a maior cota diária. O modelo pode ser trocado a qualquer momento na aba **Configurações** ou pela variável `MODEL_NAME`.

> Existe também o `PROMPT-UNIVERSAL.md` / `PROMPT-CURTO.md` (na pasta acima): o mesmo trabalho em forma de prompt para colar em qualquer chat de IA, sem rodar o app.

---

## Roadmap (próximas versões)

- **Integração direta com Siscobra:** extensão de browser ou API para preencher os 3 campos com 1 clique.
- **Webhook WhatsApp Business:** receber conversas automaticamente da plataforma, sem copiar/colar.
- **Dashboard de métricas:** % aprovado vs editado, complementos mais frequentes, operadores que mais editam.
