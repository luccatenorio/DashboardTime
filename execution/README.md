# Scripts de Sincronização Meta → Supabase

## Arquivos

- **`sync_meta_metrics.py`** - Script principal de sincronização
- **`test_sync.py`** - Script de teste para validar configurações
- **`schedule_sync.ps1`** - Script PowerShell para criar tarefa agendada
- **`run_sync.bat`** - Script batch para execução manual

## Pré-requisitos

1. **Python 3.8+** instalado e no PATH
2. **Dependências instaladas:**
   ```bash
   pip install -r ../requirements.txt
   ```

## Configuração

As variáveis de ambiente já estão configuradas no arquivo `.env`:
- `META_ACCESS_TOKEN` - Token de acesso do Meta
- `SUPABASE_URL` - URL do projeto Supabase
- `SUPABASE_KEY` - Chave de API do Supabase

## Uso

### 1. Testar Configurações

Antes de executar a sincronização completa, teste as configurações:

```bash
python test_sync.py
```

Este script valida:
- ✅ Variáveis de ambiente carregadas
- ✅ Conexão com Supabase
- ✅ Token do Meta válido

### 2. Executar Sincronização Manual

Para executar a sincronização uma vez:

```bash
python sync_meta_metrics.py
```

Ou use o script batch:

```bash
run_sync.bat
```

### 3. Configurar Automação (Executar a cada 1 hora)

**Opção A: Usando PowerShell (Recomendado)**

Execute como Administrador:

```powershell
cd execution
.\schedule_sync.ps1
```

**Opção B: Manual via Task Scheduler**

1. Abra o "Agendador de Tarefas" do Windows
2. Criar Tarefa Básica
3. Nome: `SyncMetaMetricsToSupabase`
4. Trigger: Repetir a cada 1 hora
5. Ação: Iniciar programa
   - Programa: `python` (ou caminho completo)
   - Argumentos: `"C:\caminho\completo\execution\sync_meta_metrics.py"`
   - Diretório inicial: `C:\caminho\completo\execution`

## O que o Script Faz

1. **Busca clientes ativos** da tabela `clients` no Supabase
2. **Para cada cliente:**
   - Busca todas as campanhas da conta Meta (`conta_anuncio`)
   - Para cada campanha, busca insights históricos (desde 2020)
   - Processa métricas diárias:
     - Investimento (spend)
     - Impressões
     - Alcance
     - Cliques no link
     - Conversões (actions)
3. **Insere/atualiza** dados na tabela `dashboard_campaign_metrics`
4. **Registra logs** na tabela `logs` para auditoria

## Estrutura de Dados

### Tabela `dashboard_campaign_metrics`

- `client_id` - UUID do cliente
- `campaign_id` - ID da campanha no Meta
- `campaign_name` - Nome da campanha
- `data_referencia` - Data das métricas (YYYY-MM-DD)
- `investimento` - Valor investido (R$)
- `impressoes` - Número de impressões
- `cliques_link` - Cliques no link
- `alcance` - Alcance
- `resultado_valor` - Valor total das conversões
- `resultado_nome` - Tipos de conversão (ex: "lead,onsite_conversion")

### Upsert

Os dados são inseridos/atualizados usando chave única:
- `client_id + campaign_id + data_referencia`

Isso evita duplicatas e permite atualizações.

## Tratamento de Erros

- **Rate Limits:** O script aguarda automaticamente e tenta novamente
- **Contas inválidas:** Loga erro e continua com próximo cliente
- **Campanhas sem dados:** Pula e continua
- **Erros de conexão:** Registra em logs e continua

## Logs

Todos os eventos são registrados na tabela `logs`:
- Sucessos e erros
- Número de campanhas processadas
- Detalhes de erros específicos

Para verificar logs:

```sql
SELECT * FROM logs 
WHERE tipo = 'sync_meta_metrics' 
ORDER BY created_at DESC 
LIMIT 50;
```

## Performance

- **Primeira execução:** Pode levar várias horas dependendo do volume histórico
- **Execuções subsequentes:** Mais rápidas (apenas novos dados)
- **Rate Limits:** Script implementa delay de 100ms entre requisições

## Troubleshooting

### Erro: "Python não encontrado"
- Instale Python e adicione ao PATH
- Ou ajuste `$pythonPath` no script `schedule_sync.ps1`

### Erro: "Token inválido"
- Verifique se o token no `.env` está correto
- Tokens do Meta podem expirar - gere um novo se necessário

### Erro: "Erro ao conectar no Supabase"
- Verifique `SUPABASE_URL` e `SUPABASE_KEY` no `.env`
- Confirme que as credenciais estão corretas

### Tarefa agendada não executa
- Verifique se está configurada para executar mesmo sem login
- Verifique permissões (pode precisar executar como Administrador)
- Verifique logs do Windows Event Viewer
