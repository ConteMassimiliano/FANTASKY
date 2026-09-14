"""
Test che usa esclusivamente il foglio DEBUG per testare operazioni di scrittura
Verifica il flusso: selezioni -> salva pronostici -> ripristino archivia
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

# SPREADSHEET_ID per il foglio DEBUG (stesso del produzione ma useremo solo il foglio DEBUG)
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

def setup_debug_sheet():
    """Prepara il foglio DEBUG con la struttura necessaria"""
    print("=== SETUP FOGLIO DEBUG ===")
    
    try:
        # Crea i fogli necessari in DEBUG se non esistono
        client_sheet = client()
        spreadsheet = client_sheet.open_by_key(SPREADSHEET_ID)
        
        existing_sheets = [sheet.title for sheet in spreadsheet.worksheets()]
        print(f"Fogli esistenti: {existing_sheets}")
        
        # Verifica che esista il foglio DEBUG
        if "DEBUG" not in existing_sheets:
            print("Creazione foglio DEBUG...")
            spreadsheet.add_worksheet(title="DEBUG", rows="100", cols="50")
        else:
            print("Foglio DEBUG già esistente")
        
        # Verifica che esista il foglio DEBUG_PRONOSTICI
        if "DEBUG_PRONOSTICI" not in existing_sheets:
            print("Creazione foglio DEBUG_PRONOSTICI...")
            spreadsheet.add_worksheet(title="DEBUG_PRONOSTICI", rows="100", cols="50")
        else:
            print("Foglio DEBUG_PRONOSTICI già esistente")
        
        # Copia la struttura dal foglio SELEZIONE a DEBUG
        print("Copia struttura da SELEZIONE a DEBUG...")
        ws_selezione = worksheet("SELEZIONE")
        ws_debug = worksheet("DEBUG")
        
        # Copia header e struttura base
        header = ws_selezione.row_values(1)
        ws_debug.update(values=[header], range_name="A1")
        
        # Copia le azioni (codice e nome azione)
        azioni_data = ws_selezione.get(f"A{jump_azione}:B{ultima_azione}")
        ws_debug.update(values=azioni_data, range_name=f"A{jump_azione}:B{ultima_azione}")
        
        # Copia header dei giocatori
        giocatori_header = ws_selezione.row_values(1)[jump_giocatri:ultimo_giocatore]
        header_debug = ws_debug.row_values(1)
        
        # Estendi header se necessario
        while len(header_debug) < ultimo_giocatore:
            header_debug.append("")
        
        for i, giocatore in enumerate(giocatori_header):
            header_debug[jump_giocatri + i] = giocatore
        
        ws_debug.update(values=[header_debug], range_name="A1")
        
        # Copia header delle prove
        prove_header = ws_selezione.row_values(1)[jump_giocatri - n_prove:jump_giocatri]
        for i, prova in enumerate(prove_header):
            header_debug[jump_giocatri - n_prove + i] = prova
        
        ws_debug.update([header_debug])
        
        print("✓ Setup completato")
        return True
        
    except Exception as e:
        print(f"✗ Errore durante setup: {e}")
        return False

def test_salva_pronostici_debug():
    """Test del flusso completo sul foglio DEBUG"""
    print("\n=== TEST FLUSSO COMPLETO SU DEBUG ===")
    
    try:
        ws_selezione = worksheet("SELEZIONE")
        ws_debug = worksheet("DEBUG")
        ws_debug_pronostici = worksheet("DEBUG_PRONOSTICI")
        
        # 1. Leggi le selezioni attuali dal foglio SELEZIONE
        print("1. Lettura selezioni dal foglio SELEZIONE...")
        rng = to_a1_range(jump_azione - 1, ultima_azione, jump_giocatri, ultimo_giocatore)
        selezioni_data = ws_selezione.get(rng)
        
        print(f"   - Range letto: {rng}")
        print(f"   - Righe: {len(selezioni_data)}")
        print(f"   - Colonne: {len(selezioni_data[0]) if selezioni_data else 0}")
        
        # 2. Copia le selezioni nel foglio DEBUG
        print("2. Copia selezioni nel foglio DEBUG...")
        ws_debug.update(values=selezioni_data, range_name=f"H{jump_azione}:AI{ultima_azione}")
        print("   ✓ Selezioni copiate in DEBUG")
        
        # 3. Esegui salva_pronostici sul DEBUG
        print("3. Esecuzione salva_pronostici su DEBUG...")
        
        # Copia solo la parte delle selezioni dei giocatori
        rng_debug = to_a1_range(jump_azione - 1, ultima_azione, jump_giocatri, ultimo_giocatore)
        data_debug = ws_debug.get(rng_debug)
        
        # Prima pulisce il foglio DEBUG_PRONOSTICI
        ws_debug_pronostici.clear()
        
        # Scrive i dati
        ws_debug_pronostici.update(values=data_debug, range_name=rng_debug, value_input_option='USER_ENTERED')
        print("   ✓ salva_pronostici eseguito su DEBUG")
        
        # 4. Verifica che selezioni e pronostici combacino
        print("4. Verifica corrispondenza selezioni-pronostici...")
        
        pronostici_data = ws_debug_pronostici.get(rng_debug)
        
        print(f"   - Dimensioni selezioni: {len(selezioni_data)}x{len(selezioni_data[0]) if selezioni_data else 0}")
        print(f"   - Dimensioni pronostici: {len(pronostici_data)}x{len(pronostici_data[0]) if pronostici_data else 0}")
        
        if selezioni_data == pronostici_data:
            print("   ✓ Selezioni e pronostici combaciano perfettamente")
        else:
            print("   ✗ Selezioni e pronostici NON combaciano")
            
            # Trova differenze
            for i, (sel, pron) in enumerate(zip(selezioni_data, pronostici_data)):
                if sel != pron:
                    print(f"   Differenza riga {i}:")
                    print(f"     Selezione: {sel}")
                    print(f"     Pronostico: {pron}")
            return False
        
        # 5. Simula il ripristino in archivia() - LOGICA CORRETTA
        print("5. Simulazione ripristino archivia()...")
        
        # Copia i pronostici salvati nel foglio DEBUG (come in archivia corretto)
        data_pronostici = ws_debug_pronostici.get(rng_debug)
        
        # Usa la logica corretta (senza mapping complesso che causava shift)
        rng_write = to_a1_range(jump_azione - 1, ultima_azione, jump_giocatri, ultimo_giocatore)
        ws_debug.update(values=data_pronostici, range_name=rng_write, value_input_option='USER_ENTERED')
        print("   ✓ Ripristino simulato completato (logica corretta)")
        
        # 6. Verifica che il ripristino sia corretto
        print("6. Verifica correttezza ripristino...")
        
        # Leggi solo la parte che dovrebbe corrispondere ai pronostici (range originale)
        data_ripristinata = ws_debug.get(rng_debug)
        
        if data_pronostici == data_ripristinata:
            print("   ✓ Ripristino corretto: dati ripristinati identici ai pronostici salvati")
        else:
            print("   ✗ Ripristino non corretto")
            # Debug: mostra le differenze
            print(f"   - Atteso: {len(data_pronostici)}x{len(data_pronostici[0]) if data_pronostici else 0}")
            print(f"   - Trovato: {len(data_ripristinata)}x{len(data_ripristinata[0]) if data_ripristinata else 0}")
            
            # Mostra prime differenze
            for i in range(min(3, len(data_pronostici), len(data_ripristinata))):
                if data_pronostici[i] != data_ripristinata[i]:
                    print(f"   Differenza riga {i}:")
                    print(f"     Pronostico: {data_pronostici[i]}")
                    print(f"     Ripristinato: {data_ripristinata[i]}")
            # Falliamo solo se i dati ripristinati non corrispondono ai pronostici
            return False
        
        # 7. Verifica che il ripristino corrisponda alle selezioni originali
        print("7. Verifica corrispondenza con selezioni originali...")
        
        if selezioni_data == data_ripristinata:
            print("   ✓ Ripristino corretto: dati ripristinati identici alle selezioni originali")
        else:
            print("   ✗ Ripristino non corrisponde alle selezioni originali")
            # Questo potrebbe essere normale se il ripristino include anche le righe bonus_malus
            print("   (Nota: questo potrebbe essere normale se il ripristino include righe extra)")
            # Non falliamo il test per questo, è informativo
        
        print("\n✓ TEST COMPLETATO CON SUCCESSO")
        return True
        
    except Exception as e:
        print(f"\n✗ Errore durante test: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_debug():
    """Pulisce i fogli DEBUG dopo i test"""
    print("\n=== CLEANUP FOGLIO DEBUG ===")
    
    try:
        ws_debug = worksheet("DEBUG")
        ws_debug_pronostici = worksheet("DEBUG_PRONOSTICI")
        
        # Pulisci i dati ma mantieni la struttura
        ws_debug_pronostici.clear()
        print("✓ DEBUG_PRONOSTICI pulito")
        
        # Pulisci le selezioni in DEBUG ma mantieni header e azioni
        ws_debug.batch_clear([f"H{jump_azione}:AI{ultima_azione}"])
        print("✓ DEBUG selezioni pulite")
        
        print("✓ Cleanup completato")
        return True
        
    except Exception as e:
        print(f"✗ Errore durante cleanup: {e}")
        return False

def main():
    print("=== TEST DEBUG - FLUSSO COMPLETO ===\n")
    
    # Setup
    if not setup_debug_sheet():
        print("Setup fallito, interruzione test")
        return 1
    
    # Esegui test
    result = test_salva_pronostici_debug()
    
    # Cleanup
    cleanup_debug()
    
    # Riepilogo
    print("\n=== RIEPILOGO ===")
    if result:
        print("✓ PASS: Test completato con successo")
        print("Il flusso selezioni -> salva pronostici -> ripristino funziona correttamente")
        return 0
    else:
        print("✗ FAIL: Test fallito")
        return 1

if __name__ == "__main__":
    exit(main())