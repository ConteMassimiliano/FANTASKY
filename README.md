
# FantaSkyline Streamlit

## Setup

```bash
pip install -r requirements.txt
```

Crea un Service Account Google Cloud e scarica il JSON.

Salvalo come:

```text
secrets/google-service-account.json
```

Condividi il Google Sheet con l'email del Service Account.

## Avvio

```bash
streamlit run Home.py
```

## Fogli richiesti

### GIOCATORI
| nome |
|------|
| Marco |

### AZIONI
| id | descrizione | settimana |
|----|------------|------------|

### GIOCATE
| settimana | giocatore | azione_id |
|------------|------------|------------|

### CLASSIFICA
libero, gestito da formule Google Sheets
