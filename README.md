# Tabulador Siscobra

Ferramenta interna da **Solug Cobranças** para auto-tabulação de ocorrências no Siscobra via IA (Claude). O operador cola a conversa do WhatsApp e recebe os três campos prontos: **Situação Atual**, **Complemento** e **Descritivo**.

---

## Requisitos

- Python 3.11+
- Chave de API da Anthropic (`ANTHROPIC_API_KEY`)

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

# 4. Configure as variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env e adicione sua ANTHROPIC_API_KEY

# 5. Rode a aplicação
streamlit run app.py
```

A interface abre automaticamente em `http://localhost:8501`.

---

## Configuração da API Key

No arquivo `.env`:

```env
ANTHROPIC_API_KEY=sk-ant-sua-chave-aqui
MODEL_NAME=claude-sonnet-4-5
```

Para reduzir custo após validação, troque `MODEL_NAME` para `claude-haiku-4-5-20251001`.

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
├── .env.example          # Template de configuração
├── README.md
├── requirements.txt
├── app.py                # Interface Streamlit
├── tabulacoes.db         # Banco SQLite (criado automaticamente)
├── tabulador/
│   ├── __init__.py
│   ├── taxonomia.py      # Fonte da verdade: Situação/Complemento + validação
│   ├── parser.py         # Parser do export do WhatsApp
│   ├── prompt.py         # System prompt dinâmico + few-shot
│   ├── llm.py            # Wrapper Anthropic (caching, retry, custo)
│   └── db.py             # Log SQLite
└── tests/
    └── test_taxonomia.py
```

---

## Como usar

1. Abra a interface (`streamlit run app.py`)
2. Cole o export do WhatsApp no campo da esquerda
3. Selecione o modelo (Sonnet = mais preciso, Haiku = mais barato)
4. Clique em **Tabular**
5. Confira os campos gerados na coluna direita
6. Edite o descritivo se necessário
7. Clique em **Aprovar e usar** ou **Salvar com edição**
8. Copie os valores para o Siscobra

O histórico completo fica na aba **Histórico**.

---

## Taxonomia suportada

| Situação Atual | Complementos disponíveis |
|----------------|--------------------------|
| Contato (26) | Proposta, Sem interesse, Sem sucesso, Terceiros |
| Contato com terceiros (6) | Desconhece a pessoa/cobrança, Inquilino, Novo proprietário, Representante legal (Advogado), Recado |
| Dúvidas gerais (3) | Dúvidas de preenchimento link Quita+, Encargos (juros/mora/HO), Solicitação CND, Cliente adimplente |
| Recusa acordo (9) | Alega pagamento, Discorda do valor cobrado, Não informou o motivo, Sem previsão de pagamento |

O sistema **nunca** sugere uma combinação fora desta lista.

---

## Custo estimado

| Modelo | Por tabulação (estimado) |
|--------|--------------------------|
| Sonnet 4.5 | US$ 0,010–0,015 (1ª chamada) / ~US$ 0,001 (com cache) |
| Haiku 4.5 | US$ 0,002–0,004 (1ª chamada) / ~US$ 0,0002 (com cache) |

O prompt caching da Anthropic reduz o custo em ~90% após a primeira chamada de cada sessão.

---

## Roadmap (próximas versões)

- **Integração direta com Siscobra:** extensão de browser ou API para preencher os 3 campos com 1 clique.
- **Webhook WhatsApp Business:** receber conversas automaticamente da plataforma, sem copiar/colar.
- **Fine-tuning do prompt:** usar o log de tabulações editadas pelos operadores para refinar a IA após 1-2 semanas de uso.
- **Dashboard de métricas:** % aprovado vs editado, complementos mais frequentes, operadores que mais editam (sinal de retreinamento necessário).
