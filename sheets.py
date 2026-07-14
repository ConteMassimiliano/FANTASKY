
jump_giocatri = 7
ultimo_giocatore = 35

n_prove = 4

jump_azione = 2
ultima_azione = 46

righe_bonus_malus = 12
colonne_verifica = 4

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
from gspread.utils import rowcol_to_a1

import time
TTL = 120  # 2 minuti
_CACHE = { # per azioni e giocatori
    "timestamp": 0,
    "values": None
}

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

SPREADSHEET_ID = "1wBLC0cbGhEYTvrnwIW529O-ysqDB-svKTYYRftNXi_c"

def client():
    # creds = Credentials.from_service_account_file(
    #     "secrets/google-service-account.json",
    #     scopes=SCOPES
    # )
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES,
    )
    return gspread.authorize(creds)


def worksheet(name):
    return client().open_by_key(SPREADSHEET_ID).worksheet(name)




def _get_sheet_values():
    global _CACHE

    now = time.time()

    # usa cache se valida
    if _CACHE["values"] is not None and (now - _CACHE["timestamp"] < TTL):
        return _CACHE["values"]

    # una sola richiesta al foglio
    ws = worksheet("SELEZIONE")
    values = ws.get_all_values()

    _CACHE["values"] = values
    _CACHE["timestamp"] = now

    return values


def get_players():
    values = _get_sheet_values()
    header = values[0]  # se serve in futuro

    return values[0][jump_giocatri:ultimo_giocatore]

def get_prove():
    values = _get_sheet_values()
    header = values[0]  # se serve in futuro

    return values[0][jump_giocatri - n_prove:jump_giocatri]


def get_actions(bonus_malus=False):
    values = _get_sheet_values()
    header = values[0]

    # costruzione "tipo get_all_records" ma senza seconda chiamata
    headers = header
    records = [
        dict(zip(headers, row))
        for row in values[1:]
        if len(row) > 0
    ]

    if bonus_malus:
        excluded = ('')
    else:
        excluded = ('', 'B', 'M')

    return [r['AZIONE'] for r in records if r.get('CODICE') not in excluded]
    
def get_actions_no_last5(giocatore):

    azioni = get_actions()

    ws_storico = worksheet("STORICO")
    all_records = ws_storico.get_all_records()

    last_week = max([r['Settimana'] for r in all_records] + [0])
    df = pd.DataFrame(all_records).query(f'Settimana == {last_week}')

    last5 = set(df.query(f'Giocatore == {giocatore}'))

    return set(azioni) - last5

def get_azioni_results():

    all_records = _get_sheet_values()

    header = all_records[0]
    all_records = [
        dict(zip(header, row))
        for row in all_records[1:]
        if len(row) > 0
    ]

    return pd.DataFrame([{
            'Azione':r['AZIONE'],
            'Punteggio':r['PNT'],
            'Verificato venerdì':r['SKYLINE'],
            'Verificato lunedì':r['BIG lunedì'],
            'Verificato mercoledì':r['BIG mercoledì'],
            'Verificato bonus/malus':r['SPECIALE CONCERTI']
        } for r in all_records if r['CODICE'] != ''])



def get_classifica():
    ws = worksheet("CLASSIFICA")
    df = pd.DataFrame(ws.get_all_records())[['PARTECIPANTI', 'CLASSIFICA']].rename(
        columns={
            'PARTECIPANTI': 'Giocatore',
            'CLASSIFICA': 'Punteggio'
        }
    )
    df.index = df.index+1
    df.index.name = 'Posizione'
    return df

def save_prove(prova, azioni):
    ws = worksheet("SELEZIONE")

    prove = get_prove()

    col_map = {g: i + 1 + jump_giocatri - n_prove for i, g in enumerate(prove)}
    c = col_map.get(prova)

    if not c:
        raise ValueError(f"Prova non trovata: {prova}")

    row_values = ws.col_values(2)[jump_azione-1:ultima_azione]
    row_map = {a: i + jump_azione for i, a in enumerate(row_values)}

    updates = []

    # set delle azioni selezionate
    for a in azioni:
        r = row_map.get(a)
        if r:
            updates.append((r, c, "SI"))

    cell_list = ws.range(
        min(row_map.values()),
        c,
        max(row_map.values()),
        c
    )

    # mappa veloce row -> value
    value_map = {r: v for r, v in row_map.items()}
    for a in azioni:
        r = row_map.get(a)
        if r:
            value_map[r] = "SI"

    for cell in cell_list:
        if cell.row in value_map:
            cell.value = value_map[cell.row]

    ws.update_cells(cell_list)

def save_picks(giocatore, azioni):
    ws = worksheet("SELEZIONE")

    # =========================
    # 1. LETTURA HEADER (1 chiamata)
    # =========================
    giocatori = get_players()

    col_map = {g: i + 1 + jump_giocatri for i, g in enumerate(giocatori)}
    c = col_map.get(giocatore)

    if not c:
        raise ValueError(f"Giocatore non trovato: {giocatore}")

    # =========================
    # 2. LETTURA AZIONI (1 chiamata)
    # =========================
    row_values = ws.col_values(2)[jump_azione-1:ultima_azione]
    row_map = {a: i + jump_azione for i, a in enumerate(row_values)}

    # =========================
    # 3. PREPARA TUTTI I VALORI IN MEMORIA
    # =========================
    # Evitiamo update_cell (N chiamate)
    updates = []

    # reset tutte le righe
    for azione, r in row_map.items():
        updates.append((r, c, "NO"))

    # set delle azioni selezionate
    for a in azioni:
        r = row_map.get(a)
        if r:
            updates.append((r, c, "SI"))

    # =========================
    # 4. ESEGUI UPDATE IN BATCH
    # =========================
    # gspread non ha batch update_cell diretto → usiamo update con range
    cell_list = ws.range(
        min(row_map.values()),
        c,
        max(row_map.values()),
        c
    )

    # mappa veloce row -> value
    value_map = {r: "NO" for r in row_map.values()}
    for a in azioni:
        r = row_map.get(a)
        if r:
            value_map[r] = "SI"

    for cell in cell_list:
        if cell.row in value_map:
            cell.value = value_map[cell.row]

    ws.update_cells(cell_list)

def to_a1_range(r1, r2, c1, c2):
    start = rowcol_to_a1(r1 + 1, c1 + 1)
    end = rowcol_to_a1(r2, c2)
    return f"{start}:{end}"

def archivia():
    ws_storico = worksheet("STORICO")
    ws_selezione = worksheet("SELEZIONE")
    ws_totale = worksheet("TOTALE")

    azioni = get_actions(bonus_malus=True)
    giocatori = get_players()
    

    last_week = max([r['Settimana'] for r in ws_storico.get_all_records()] + [0])
    


    ############################# STORICO #############################
    rng = to_a1_range(0, ultima_azione + righe_bonus_malus, 0, ultimo_giocatore)
    data = ws_selezione.get(rng)

    df = pd.DataFrame(data[1:], columns=data[0])
    df = df.loc[df['CODICE'] != '']

    df_long = []

    for a, (idx, row) in enumerate(df.iterrows()):
        for g, v in row.items():
            if v == 'SI' and g in giocatori:
               df_long.append({'Giocatore':g, 'Azione': azioni[a]}) 

    df_long = pd.DataFrame(df_long)

    df_long['Settimana'] = last_week + 1

    res_azioni = get_azioni_results()

    df_long = df_long.merge(res_azioni, on='Azione')

    ws_storico.append_rows([(r['Giocatore'], r['Azione'], r['Settimana'], r['Punteggio'], r['Verificato venerdì'], r['Verificato lunedì'], r['Verificato mercoledì'], r['Verificato bonus/malus']) for idx, r in df_long.iterrows()],
                           value_input_option='USER_ENTERED')
    ##########################################################
    
    ############################# PUNTEGGI #############################
    rng = to_a1_range(ultima_azione + righe_bonus_malus,ultima_azione + righe_bonus_malus+1, jump_giocatri, ultimo_giocatore)
    punteggi = ws_selezione.get(rng)

    cell_list = ws_totale.range(3, 2 + last_week, 3 + len(giocatori) - 1,  2 + last_week)

    for i, cell in enumerate(cell_list):
        cell.value = punteggi[0][i]

    ws_totale.update_cells(cell_list, value_input_option='USER_ENTERED')
    ##########################################################

    ############################# RESET SELEZIONI #############################
    cell_list = ws_selezione.range(jump_azione, jump_giocatri - colonne_verifica + 1, ultima_azione , ultimo_giocatore)

    for cell in cell_list:
        cell.value = 'NO'

    ws_selezione.update_cells(cell_list)

    cell_list = ws_selezione.range(ultima_azione, jump_giocatri - colonne_verifica + 1, ultima_azione + righe_bonus_malus, jump_giocatri)

    for cell in cell_list:
        cell.value = 'NO'

    ws_selezione.update_cells(cell_list)
    ##########################################################

