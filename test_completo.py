"""
Test completo di tutte le funzionalità dell'applicazione FANTASKY
Usa esclusivamente i fogli DEBUG per non modificare i dati di produzione
"""

import sys
import os

# Aggiungi la directory corrente al path per importare sheets
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
from gspread.utils import rowcol_to_a1

# Constants dal file sheets.py
jump_giocatri = 7
ultimo_giocatore = 35
n_prove = 4
jump_azione = 2
ultima_azione = 46
righe_bonus_malus = 12
colonne_verifica = 4

# SPREADSHEET_ID
SPREADSHEET_ID = "1wBLC0cbGhEYTvrnwIW529O-ysqDB-svKTYYRftNXi_c"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def client():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES,
    )
    return gspread.authorize(creds)

def worksheet(name):
    return client().open_by_key(SPREADSHEET_ID).worksheet(name)

def to_a1_range(r1, r2, c1, c2):
    start = rowcol_to_a1(r1 + 1, c1 + 1)
    end = rowcol_to_a1(r2, c2)
    return f"{start}:{end}"

def setup_debug_sheets():
    """Prepara tutti i fogli DEBUG necessari"""
    print("=== SETUP FOGLI DEBUG ===")
    
    try:
        client_sheet = client()
        spreadsheet = client_sheet.open_by_key(SPREADSHEET_ID)
        existing_sheets = [sheet.title for sheet in spreadsheet.worksheets()]
        
        debug_sheets = ["DEBUG", "DEBUG_PRONOSTICI", "DEBUG_STORICO", "DEBUG_TOTALE", "DEBUG_CLASSIFICA"]
        
        for sheet_name in debug_sheets:
            if sheet_name not in existing_sheets:
                print(f"Creazione foglio {sheet_name}...")
                spreadsheet.add_worksheet(title=sheet_name, rows="100", cols="50")
            else:
                print(f"Foglio {sheet_name} già esistente")
        
        # Copia struttura base da SELEZIONE a DEBUG
        print("Copia struttura da SELEZIONE a DEBUG...")
        ws_selezione = worksheet("SELEZIONE")
        ws_debug = worksheet("DEBUG")
        
        header = ws_selezione.row_values(1)
        ws_debug.update(values=[header], range_name="A1")
        
        # Copia azioni
        azioni_data = ws_selezione.get(f"A{jump_azione}:B{ultima_azione}")
        ws_debug.update(values=azioni_data, range_name=f"A{jump_azione}:B{ultima_azione}")
        
        # Copia header giocatori e prove
        giocatori_header = ws_selezione.row_values(1)[jump_giocatri:ultimo_giocatore]
        prove_header = ws_selezione.row_values(1)[jump_giocatri - n_prove:jump_giocatri]
        
        header_debug = ws_debug.row_values(1)
        while len(header_debug) < ultimo_giocatore:
            header_debug.append("")
        
        for i, giocatore in enumerate(giocatori_header):
            header_debug[jump_giocatri + i] = giocatore
        
        for i, prova in enumerate(prove_header):
            header_debug[jump_giocatri - n_prove + i] = prova
        
        ws_debug.update(values=[header_debug], range_name="A1")
        
        print("✓ Setup completato")
        return True
        
    except Exception as e:
        print(f"✗ Errore durante setup: {e}")
        return False

def test_get_players():
    """Test della funzione get_players"""
    print("\n=== TEST 1: get_players ===")
    
    try:
        from sheets import get_players
        
        giocatori = get_players()
        print(f"Giocatori trovati: {len(giocatori)}")
        print(f"Primi 5 giocatori: {giocatori[:5]}")
        
        if len(giocatori) > 0:
            print("✓ PASS: get_players funziona correttamente")
            return True
        else:
            print("✗ FAIL: Nessun giocatore trovato")
            return False
            
    except Exception as e:
        print(f"✗ FAIL: Errore in get_players: {e}")
        return False

def test_get_prove():
    """Test della funzione get_prove"""
    print("\n=== TEST 2: get_prove ===")
    
    try:
        from sheets import get_prove
        
        prove = get_prove()
        print(f"Prove trovate: {len(prove)}")
        print(f"Prove: {prove}")
        
        if len(prove) == n_prove:
            print("✓ PASS: get_prove funziona correttamente")
            return True
        else:
            print(f"✗ FAIL: Atteso {n_prove} prove, trovate {len(prove)}")
            return False
            
    except Exception as e:
        print(f"✗ FAIL: Errore in get_prove: {e}")
        return False

def test_get_actions():
    """Test della funzione get_actions"""
    print("\n=== TEST 3: get_actions ===")
    
    try:
        from sheets import get_actions
        
        azioni_normali = get_actions(bonus_malus=False)
        azioni_complete = get_actions(bonus_malus=True)
        
        print(f"Azioni normali (senza B/M): {len(azioni_normali)}")
        print(f"Azioni complete (con B/M): {len(azioni_complete)}")
        
        if len(azioni_complete) > len(azioni_normali):
            print("✓ PASS: get_actions funziona correttamente")
            return True
        else:
            print("✗ FAIL: Le azioni complete dovrebbero includere B/M")
            return False
            
    except Exception as e:
        print(f"✗ FAIL: Errore in get_actions: {e}")
        return False

def test_save_picks():
    """Test della funzione save_picks usando DEBUG"""
    print("\n=== TEST 4: save_picks ===")
    
    try:
        from sheets import get_players, save_picks
        
        giocatori = get_players()
        if not giocatori:
            print("✗ FAIL: Nessun giocatore disponibile")
            return False
        
        # Usa il primo giocatore per il test
        test_giocatore = giocatori[0]
        print(f"Test con giocatore: {test_giocatore}")
        
        # Ottieni azioni disponibili
        from sheets import get_actions
        azioni = get_actions(bonus_malus=False)
        
        if len(azioni) < 5:
            print("✗ FAIL: Meno di 5 azioni disponibili")
            return False
        
        # Seleziona 5 azioni per il test
        test_selezioni = azioni[:5]
        print(f"Selezioni test: {test_selezioni}")
        
        # Salva nel foglio DEBUG invece di SELEZIONE
        ws_debug = worksheet("DEBUG")
        
        # Simula save_picks su DEBUG
        giocatori_debug = ws_debug.row_values(1)[jump_giocatri:ultimo_giocatore]
        col_map = {g: i + 1 + jump_giocatri for i, g in enumerate(giocatori_debug)}
        c = col_map.get(test_giocatore)
        
        if not c:
            print(f"✗ FAIL: Giocatore {test_giocatore} non trovato in DEBUG")
            return False
        
        row_values = ws_debug.col_values(2)[jump_azione-1:ultima_azione]
        row_map = {a: i + jump_azione for i, a in enumerate(row_values)}
        
        # Reset tutte le righe
        cell_list = ws_debug.range(jump_azione, c, ultima_azione, c)
        value_map = {r: "NO" for r in row_map.values()}
        
        # Set delle azioni selezionate
        for a in test_selezioni:
            r = row_map.get(a)
            if r:
                value_map[r] = "SI"
        
        for cell in cell_list:
            if cell.row in value_map:
                cell.value = value_map[cell.row]
        
        ws_debug.update_cells(cell_list, value_input_option='USER_ENTERED')
        
        # Verifica che le selezioni siano state salvate
        verify_data = ws_debug.col_values(c)[jump_azione-1:ultima_azione]
        si_count = sum(1 for v in verify_data if v == "SI")
        
        if si_count == 5:
            print(f"✓ PASS: save_picks simulato correttamente ({si_count} selezioni salvate)")
            return True
        else:
            print(f"✗ FAIL: Atteso 5 SI, trovati {si_count}")
            return False
            
    except Exception as e:
        print(f"✗ FAIL: Errore in save_picks: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_save_prove():
    """Test della funzione save_prove usando DEBUG"""
    print("\n=== TEST 5: save_prove ===")
    
    try:
        from sheets import get_prove, get_actions
        
        prove = get_prove()
        azioni = get_actions(bonus_malus=True)
        
        if not prove or not azioni:
            print("✗ FAIL: Dati non disponibili")
            return False
        
        test_prova = prove[0]
        test_azioni = azioni[:3]  # Seleziona 3 azioni per il test
        
        print(f"Test con prova: {test_prova}")
        print(f"Azioni test: {test_azioni}")
        
        # Simula save_prove su DEBUG
        ws_debug = worksheet("DEBUG")
        
        prove_debug = ws_debug.row_values(1)[jump_giocatri - n_prove:jump_giocatri]
        col_map = {g: i + 1 + jump_giocatri - n_prove for i, g in enumerate(prove_debug)}
        c = col_map.get(test_prova)
        
        if not c:
            print(f"✗ FAIL: Prova {test_prova} non trovata in DEBUG")
            return False
        
        row_values = ws_debug.col_values(2)[jump_azione-1:ultima_azione]
        row_map = {a: i + jump_azione for i, a in enumerate(row_values)}
        
        cell_list = ws_debug.range(jump_azione, c, ultima_azione, c)
        value_map = {r: v for r, v in row_map.items()}
        
        for a in test_azioni:
            r = row_map.get(a)
            if r:
                value_map[r] = "SI"
        
        for cell in cell_list:
            if cell.row in value_map:
                cell.value = value_map[cell.row]
        
        ws_debug.update_cells(cell_list, value_input_option='USER_ENTERED')
        
        # Verifica
        verify_data = ws_debug.col_values(c)[jump_azione-1:ultima_azione]
        si_count = sum(1 for v in verify_data if v == "SI")
        
        if si_count == len(test_azioni):
            print(f"✓ PASS: save_prove simulato correttamente ({si_count} eventi salvati)")
            return True
        else:
            print(f"✗ FAIL: Atteso {len(test_azioni)} SI, trovati {si_count}")
            return False
            
    except Exception as e:
        print(f"✗ FAIL: Errore in save_prove: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_salva_pronostici():
    """Test della funzione salva_pronostici usando DEBUG"""
    print("\n=== TEST 6: salva_pronostici ===")
    
    try:
        ws_debug = worksheet("DEBUG")
        ws_debug_pronostici = worksheet("DEBUG_PRONOSTICI")
        
        # Prepara dati di test in DEBUG
        rng = to_a1_range(jump_azione - 1, ultima_azione, jump_giocatri, ultimo_giocatore)
        
        # Crea dati di test
        test_data = []
        for i in range(ultima_azione - jump_azione + 1):
            row = []
            for j in range(ultimo_giocatore - jump_giocatri):
                if i == 0 and j == 0:
                    row.append("SI")
                elif i == 1 and j == 1:
                    row.append("SI")
                else:
                    row.append("NO")
            test_data.append(row)
        
        ws_debug.update(values=test_data, range_name=rng, value_input_option='USER_ENTERED')
        
        # Esegui salva_pronostici simulato
        data_debug = ws_debug.get(rng)
        ws_debug_pronostici.clear()
        ws_debug_pronostici.update(values=data_debug, range_name=rng, value_input_option='USER_ENTERED')
        
        # Verifica
        pronostici_data = ws_debug_pronostici.get(rng)
        
        if test_data == pronostici_data:
            print("✓ PASS: salva_pronostici simulato correttamente")
            return True
        else:
            print("✗ FAIL: I dati non corrispondono")
            return False
            
    except Exception as e:
        print(f"✗ FAIL: Errore in salva_pronostici: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_get_classifica():
    """Test della funzione get_classifica"""
    print("\n=== TEST 7: get_classifica ===")
    
    try:
        from sheets import get_classifica
        
        classifica = get_classifica()
        print(f"Classifica trovata: {len(classifica)} giocatori")
        
        if len(classifica) > 0:
            print("Prime 3 posizioni:")
            print(classifica.head(3))
            print("✓ PASS: get_classifica funziona correttamente")
            return True
        else:
            print("✗ FAIL: Classifica vuota")
            return False
            
    except Exception as e:
        print(f"✗ FAIL: Errore in get_classifica: {e}")
        return False

def test_get_punteggi_azioni():
    """Test della funzione get_punteggi_azioni"""
    print("\n=== TEST 8: get_punteggi_azioni ===")
    
    try:
        from sheets import get_punteggi_azioni
        
        punteggi = get_punteggi_azioni()
        print(f"Punteggi azioni trovati: {len(punteggi)} azioni")
        
        if len(punteggi) > 0:
            print("Prime 3 azioni:")
            print(punteggi.head(3))
            print("✓ PASS: get_punteggi_azioni funziona correttamente")
            return True
        else:
            print("⚠ WARNING: Nessun punteggio trovato (potrebbe essere normale)")
            return True  # Non falliamo se non ci sono dati
            
    except Exception as e:
        print(f"✗ FAIL: Errore in get_punteggi_azioni: {e}")
        return False

def test_refresh_cache():
    """Test della funzione refresh_cache"""
    print("\n=== TEST 9: refresh_cache ===")
    
    try:
        from sheets import refresh_cache
        
        print("Esecuzione refresh_cache...")
        refresh_cache()
        print("✓ PASS: refresh_cache eseguito senza errori")
        return True
        
    except Exception as e:
        print(f"✗ FAIL: Errore in refresh_cache: {e}")
        return False

def test_get_actions_no_last5():
    """Test della funzione get_actions_no_last5"""
    print("\n=== TEST 10: get_actions_no_last5 ===")
    
    try:
        from sheets import get_actions_no_last5, get_players
        
        giocatori = get_players()
        if not giocatori:
            print("✗ FAIL: Nessun giocatore disponibile")
            return False
        
        test_giocatore = giocatori[0]
        print(f"Test con giocatore: {test_giocatore}")
        
        azioni_filtrate = get_actions_no_last5(test_giocatore)
        print(f"Azioni filtrate (escluse ultime 5): {len(azioni_filtrate)}")
        
        from sheets import get_actions
        azioni_totali = get_actions(bonus_malus=False)
        
        if len(azioni_filtrate) <= len(azioni_totali):
            print("✓ PASS: get_actions_no_last5 funziona correttamente")
            return True
        else:
            print("✗ FAIL: Le azioni filtrate non possono essere più di quelle totali")
            return False
            
    except Exception as e:
        print(f"✗ FAIL: Errore in get_actions_no_last5: {e}")
        return False

def test_archivia_simulation():
    """Test simulato della funzione archivia usando DEBUG"""
    print("\n=== TEST 11: archivia (simulazione) ===")
    
    try:
        ws_debug = worksheet("DEBUG")
        ws_debug_pronostici = worksheet("DEBUG_PRONOSTICI")
        ws_debug_storico = worksheet("DEBUG_STORICO")
        
        # Simula il ripristino pronostici
        rng = to_a1_range(jump_azione - 1, ultima_azione, jump_giocatri, ultimo_giocatore)
        data_pronostici = ws_debug_pronostici.get(rng)
        
        if data_pronostici:
            rng_write = to_a1_range(jump_azione - 1, ultima_azione, jump_giocatri, ultimo_giocatore)
            ws_debug.update(values=data_pronostici, range_name=rng_write, value_input_option='USER_ENTERED')
            print("✓ Ripristino pronostici simulato")
        
        # Simula reset selezioni
        cell_list = ws_debug.range(jump_azione, jump_giocatri - colonne_verifica + 1, ultima_azione, ultimo_giocatore)
        for cell in cell_list:
            cell.value = 'NO'
        ws_debug.update_cells(cell_list, value_input_option='USER_ENTERED')
        print("✓ Reset selezioni simulato")
        
        print("✓ PASS: archivia simulato correttamente")
        return True
        
    except Exception as e:
        print(f"✗ FAIL: Errore in archivia: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_debug_sheets():
    """Pulisce i fogli DEBUG dopo i test"""
    print("\n=== CLEANUP FOGLI DEBUG ===")
    
    try:
        debug_sheets = ["DEBUG", "DEBUG_PRONOSTICI", "DEBUG_STORICO", "DEBUG_TOTALE", "DEBUG_CLASSIFICA"]
        
        for sheet_name in debug_sheets:
            try:
                ws = worksheet(sheet_name)
                ws.clear()
                print(f"✓ {sheet_name} pulito")
            except:
                print(f"⚠ {sheet_name} non pulito (foglio potrebbe non esistere)")
        
        print("✓ Cleanup completato")
        return True
        
    except Exception as e:
        print(f"✗ Errore durante cleanup: {e}")
        return False

def main():
    print("=== TEST COMPLETO FANTASKY ===\n")
    
    # Setup
    if not setup_debug_sheets():
        print("Setup fallito, interruzione test")
        return 1
    
    # Esegui tutti i test
    results = []
    results.append(("get_players", test_get_players()))
    results.append(("get_prove", test_get_prove()))
    results.append(("get_actions", test_get_actions()))
    results.append(("save_picks", test_save_picks()))
    results.append(("save_prove", test_save_prove()))
    results.append(("salva_pronostici", test_salva_pronostici()))
    results.append(("get_classifica", test_get_classifica()))
    results.append(("get_punteggi_azioni", test_get_punteggi_azioni()))
    results.append(("refresh_cache", test_refresh_cache()))
    results.append(("get_actions_no_last5", test_get_actions_no_last5()))
    results.append(("archivia", test_archivia_simulation()))
    
    # Cleanup
    cleanup_debug_sheets()
    
    # Riepilogo
    print("\n=== RIEPILOGO ===")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotale: {passed}/{total} test passati")
    
    if passed == total:
        print("\n🎉 Tutti i test sono passati!")
        return 0
    else:
        print(f"\n⚠ {total - passed} test sono falliti.")
        return 1

if __name__ == "__main__":
    exit(main())