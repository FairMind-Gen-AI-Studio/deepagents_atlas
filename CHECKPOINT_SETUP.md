# LangGraph Checkpoint Configuration Guide

## Il Problema Risolto

Senza configurazione di checkpoint, LangGraph **non persiste lo stato** tra un messaggio utente e l'altro. Questo causava:

❌ Router classifica intent correttamente
❌ Agent esegue e propaga `active_agent`
❌ **Ma lo stato viene perso tra i messaggi!**
❌ Prossimo messaggio: `active_agent=None` → re-routing errato

Con checkpoint configurato:

✅ Router classifica intent correttamente
✅ Agent esegue e propaga `active_agent`
✅ **Checkpoint salva lo stato!**
✅ Prossimo messaggio: `active_agent` caricato → session continuity

## Configurazione Corrente (Memory Store)

**File:** `langgraph.json`

```json
{
  "dependencies": [...],
  "graphs": {
    "router": "./router_graph.py:agent"
  },
  "env": ".env",
  "store": {
    "type": "memory"
  }
}
```

### Caratteristiche Memory Store

**Vantaggi:**
- ✅ Setup zero - nessuna configurazione aggiuntiva
- ✅ Veloce - tutto in RAM
- ✅ Perfetto per development e testing
- ✅ Nessuna dipendenza esterna

**Limitazioni:**
- ❌ Stato perso al restart del server
- ❌ Non scalabile per produzione
- ❌ Non adatto per conversazioni long-running

**Quando Usare:**
- Development locale
- Testing della session continuity
- Debug rapido
- Proof of concept

### Come Avviare il Server

**Metodo 1: Script Clean Start (Raccomandato)**
```bash
./scripts/clean_start.sh
```
Lo script automaticamente:
- Pulisce checkpoint esistenti
- Avvia il server con le opzioni corrette
- Include `--allow-blocking` per MCP tools

**Metodo 2: Avvio Manuale**
```bash
langgraph dev --no-browser --allow-blocking
```

**⚠️ IMPORTANTE: Flag `--allow-blocking`**

Il flag `--allow-blocking` è **necessario** perché:
- `langchain_mcp_adapters` usa HTTP sincrono (non può essere convertito ad async)
- MCP tools vengono inizializzati **una volta per utente** al primo request
- Dopo il primo request, i tools vengono cachati nello stato (no blocking)
- Senza questo flag, LangGraph mostrerà warning ad ogni primo request

**Cosa aspettarsi:**
```
✅ Primo request di un utente:
   🔧 MCP tools cache miss - initializing with user credentials
   ✅ MCP tools initialized: 42 tools available

✅ Request successivi dello stesso utente:
   ♻️ MCP tools cache hit - reusing 42 cached tools
```

## Upgrade a SQLite (Produzione Light)

Per persistenza su disco senza dipendenze esterne:

```json
{
  "dependencies": [...],
  "graphs": {
    "router": "./router_graph.py:agent"
  },
  "env": ".env",
  "store": {
    "type": "sqlite",
    "path": "./data/checkpoints.db"
  }
}
```

### Preparazione

1. **Crea la directory per i checkpoint:**
   ```bash
   mkdir -p data
   ```

2. **Aggiungi al .gitignore:**
   ```bash
   echo "data/checkpoints.db*" >> .gitignore
   ```

3. **Aggiorna langgraph.json** con la configurazione sopra

4. **Riavvia il server:**
   ```bash
   langgraph dev
   ```

### Caratteristiche SQLite Store

**Vantaggi:**
- ✅ Persistenza su disco - sopravvive ai restart
- ✅ Nessuna dipendenza esterna (SQLite embedded)
- ✅ Buone performance per scale medie
- ✅ File-based - facile da backuppare

**Limitazioni:**
- ⚠️ Non distribuito - single server only
- ⚠️ Performance limitate per alta concorrenza
- ⚠️ File può crescere nel tempo

**Quando Usare:**
- Deployment single-server
- MVP e progetti pilota
- < 1000 conversazioni attive
- Applicazioni interne

## Upgrade a PostgreSQL (Produzione Enterprise)

Per alta disponibilità e scalabilità:

```json
{
  "dependencies": [...],
  "graphs": {
    "router": "./router_graph.py:agent"
  },
  "env": ".env",
  "store": {
    "type": "postgres",
    "uri": "${POSTGRES_URI}"
  }
}
```

### Preparazione

1. **Setup PostgreSQL:**
   ```bash
   # Docker Compose per development
   docker run -d \
     --name langgraph-postgres \
     -e POSTGRES_PASSWORD=password \
     -e POSTGRES_DB=langgraph \
     -p 5432:5432 \
     postgres:15
   ```

2. **Aggiungi URI al .env:**
   ```bash
   POSTGRES_URI=postgresql://postgres:password@localhost:5432/langgraph
   ```

3. **Aggiorna langgraph.json** con la configurazione sopra

4. **Riavvia il server:**
   ```bash
   langgraph dev
   ```

### Caratteristiche PostgreSQL Store

**Vantaggi:**
- ✅ Alta disponibilità e replicazione
- ✅ Scalabile orizzontalmente
- ✅ Ottimo per alta concorrenza
- ✅ Backup e recovery enterprise-grade
- ✅ Supporto transazionale completo

**Limitazioni:**
- ⚠️ Richiede PostgreSQL server esterno
- ⚠️ Setup più complesso
- ⚠️ Costi di infrastruttura

**Quando Usare:**
- Produzione multi-server
- Alta concorrenza (> 1000 utenti)
- Deployment distribuiti
- Requisiti enterprise (HA, backup, compliance)

## Tabella Comparativa

| Feature | Memory | SQLite | PostgreSQL |
|---------|--------|--------|------------|
| **Setup** | Zero | Facile | Medio |
| **Persistenza** | No | Sì (locale) | Sì (distribuita) |
| **Performance** | Massime | Buone | Ottime |
| **Scalabilità** | Bassa | Media | Alta |
| **Costo** | $0 | $0 | $-$$ |
| **Uso Raccomandato** | Dev/Test | MVP/Small | Production |

## Verifica Post-Configurazione

Dopo aver aggiunto checkpoint e riavviato il server, verifica che funzioni:

### 1. Check Server Logs

Cerca questi pattern nei log:

**Prima Run (Nuovo Messaggio):**
```
🔍 DEBUG: router_node INPUT active_agent = None
🔀 ROUTER DECISION
Routed to: DOCGEN
🔍 DEBUG: router_node OUTPUT active_agent = docgen
```

**Seconda Run (Continuazione):**
```
🔍 DEBUG: router_node INPUT active_agent = docgen  ← ✅ Caricato!
🔗 CONTINUING ACTIVE SESSION
Active agent: DOCGEN
```

### 2. Check State Keys

Nel log della seconda run, verifica che `active_agent` sia nelle chiavi:

```
🔍 DEBUG: router_node INPUT state keys = ['messages', 'todos', 'files', 'active_agent']
                                                                         ↑ PRESENTE!
```

### 3. Test Conversation Flow

1. Inizia DocGen: "document this code"
2. Rispondi alle domande: "A) architettura B) sviluppatori..."
3. **Verifica:** DocGen continua (non switch ad Atlas)

### 4. Check LangSmith

In LangSmith, dovresti vedere:
- Checkpoint creation events
- Checkpoint load events
- `active_agent` presente in tutti i node outputs

### 5. Check Checkpoint Storage

**Memory:**
Nessun file da verificare - tutto in RAM.

**SQLite:**
```bash
ls -lh data/checkpoints.db
# Dovresti vedere il file crescere con l'uso
```

**PostgreSQL:**
```bash
psql $POSTGRES_URI -c "SELECT COUNT(*) FROM checkpoints;"
# Dovresti vedere record crescere
```

## Troubleshooting

### Problema: active_agent Ancora None in Seconda Run

**Diagnosi:**
```
🔍 DEBUG: router_node INPUT active_agent = None  ← Ancora None!
🔍 DEBUG: router_node INPUT state keys = ['messages', 'todos', 'files']  ← Manca!
```

**Possibili Cause:**

1. **Server non riavviato dopo modifica langgraph.json**
   ```bash
   # Soluzione: Riavvia
   # Ctrl+C per fermare, poi:
   langgraph dev
   ```

2. **Thread ID diversi tra messaggi**
   ```bash
   # Check nei log se vedi:
   thread_id=abc123  # Prima run
   thread_id=xyz789  # Seconda run ← DIVERSO!

   # Soluzione: Assicurati che UI passi stesso thread_id
   ```

3. **Configurazione non valida**
   ```bash
   # Verifica syntax JSON:
   cat langgraph.json | python -m json.tool

   # Deve stampare JSON valido senza errori
   ```

4. **Store type non supportato**
   ```bash
   # Check error logs:
   grep -i "store" langgraph_server.log

   # Se vedi errori, verifica che il type sia valido
   ```

### Problema: SQLite File Non Creato

**Diagnosi:**
```bash
ls -la data/checkpoints.db
# ls: data/checkpoints.db: No such file or directory
```

**Possibili Cause:**

1. **Directory non esiste**
   ```bash
   mkdir -p data
   langgraph dev  # Riavvia
   ```

2. **Permessi insufficienti**
   ```bash
   chmod 755 data
   langgraph dev  # Riavvia
   ```

3. **Path relativo errato**
   ```json
   // Verifica che path sia relativo a project root:
   "path": "./data/checkpoints.db"  ✅
   "path": "data/checkpoints.db"    ✅
   "path": "/tmp/checkpoints.db"    ✅
   ```

### Problema: PostgreSQL Connection Refused

**Diagnosi:**
```
Error: could not connect to postgres
Connection refused on localhost:5432
```

**Possibili Cause:**

1. **PostgreSQL non in running**
   ```bash
   # Check se container è up:
   docker ps | grep postgres

   # Se non c'è, start:
   docker start langgraph-postgres
   ```

2. **URI errata**
   ```bash
   # Verifica .env:
   cat .env | grep POSTGRES_URI

   # Deve essere:
   POSTGRES_URI=postgresql://user:pass@host:port/db
   ```

3. **Database non esiste**
   ```bash
   # Crea database:
   psql postgresql://postgres:password@localhost:5432/postgres \
     -c "CREATE DATABASE langgraph;"
   ```

## Performance Tuning

### Memory Store

Nessun tuning necessario - tutto automatico.

### SQLite Store

**Opzioni avanzate:**

```json
{
  "store": {
    "type": "sqlite",
    "path": "./data/checkpoints.db",
    "pragmas": {
      "journal_mode": "WAL",
      "synchronous": "NORMAL",
      "cache_size": -64000
    }
  }
}
```

**Cosa fanno:**
- `journal_mode=WAL`: Write-Ahead Logging - migliori performance in scrittura
- `synchronous=NORMAL`: Balance tra safety e speed
- `cache_size=-64000`: Cache di 64MB (valore in KB negativo)

### PostgreSQL Store

**Connection pooling:**

```json
{
  "store": {
    "type": "postgres",
    "uri": "${POSTGRES_URI}",
    "pool_size": 20,
    "max_overflow": 10
  }
}
```

**Ottimizzazioni database:**

```sql
-- Crea indici per query veloci
CREATE INDEX idx_thread_id ON checkpoints(thread_id);
CREATE INDEX idx_timestamp ON checkpoints(created_at);

-- Vacuum periodico (PostgreSQL auto-vacuum dovrebbe bastare)
VACUUM ANALYZE checkpoints;
```

## Backup e Recovery

### SQLite

**Backup:**
```bash
# Backup semplice (file copy)
cp data/checkpoints.db data/checkpoints.db.backup

# Backup con timestamp
cp data/checkpoints.db "data/checkpoints.$(date +%Y%m%d_%H%M%S).db"

# Backup automatico (cron)
0 2 * * * cp /path/to/data/checkpoints.db /path/to/backups/checkpoints.$(date +\%Y\%m\%d).db
```

**Recovery:**
```bash
# Restore da backup
cp data/checkpoints.db.backup data/checkpoints.db
langgraph dev  # Riavvia
```

### PostgreSQL

**Backup:**
```bash
# Dump completo
pg_dump $POSTGRES_URI > checkpoints_backup.sql

# Dump solo tabella checkpoints
pg_dump $POSTGRES_URI -t checkpoints > checkpoints_table.sql

# Backup automatico
0 2 * * * pg_dump $POSTGRES_URI | gzip > /path/to/backups/checkpoints_$(date +\%Y\%m\%d).sql.gz
```

**Recovery:**
```bash
# Restore da dump
psql $POSTGRES_URI < checkpoints_backup.sql
```

## Migration Path

### Da Memory a SQLite

1. **Aggiungi SQLite config** in langgraph.json
2. **Riavvia server**
3. **Nota:** Conversazioni in-memory vengono perse (previsto)

### Da SQLite a PostgreSQL

1. **Setup PostgreSQL** (vedi sopra)
2. **Esporta da SQLite:**
   ```bash
   sqlite3 data/checkpoints.db .dump > checkpoints.sql
   ```
3. **Importa in PostgreSQL:**
   ```bash
   psql $POSTGRES_URI < checkpoints.sql
   ```
4. **Aggiorna langgraph.json** con Postgres config
5. **Riavvia server**

## Best Practices

### Development

- ✅ Usa **memory store** per rapid iteration
- ✅ Testa con **SQLite** prima di production
- ✅ Commit langgraph.json changes
- ❌ Non commitare file di checkpoint

### Staging/Production

- ✅ Usa **SQLite** per MVP e low-traffic
- ✅ Usa **PostgreSQL** per production e high-traffic
- ✅ Setup backup automatici
- ✅ Monitor checkpoint storage size
- ✅ Implementa cleanup vecchi checkpoint (se necessario)

### Security

- ✅ **SQLite:** Proteggi file con permessi appropriati (600)
- ✅ **PostgreSQL:** Usa SSL per connessioni remote
- ✅ **Passwords:** Mai hardcode in config, sempre .env
- ✅ **Backup:** Encrypt backup se contengono dati sensibili

## Conclusione

Il checkpoint storage è **essenziale** per session continuity. Senza di esso:
- ❌ Lo stato viene perso tra messaggi
- ❌ `active_agent` non persiste
- ❌ Session continuity non funziona

Con checkpoint configurato:
- ✅ Lo stato persiste tra messaggi
- ✅ `active_agent` sopravvive
- ✅ Session continuity funziona perfettamente

**Setup minimo richiesto:** Aggiungi `"store": {"type": "memory"}` a langgraph.json e riavvia.

**Prossimi step:** Vedi [FINAL_FIX_SUMMARY.md](FINAL_FIX_SUMMARY.md) per test completo del fix.
