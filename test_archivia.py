"""
Test per verificare le correzioni apportate alla funzione archivia()
Verifica che le assunzioni fatte siano corrette
"""

import sys
import os

# Aggiungi la directory corrente al path per importare sheets
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
from sheets import (
    get_players, get_actions, worksheet, 
    jump_giocatri, ultimo_giocatore, jump_azione, ultima_azione,
    righe_bonus_malus, to_a1_range, get_azioni_results
)

def test_giocatori_consistency():
    """Verifica che l'ordine dei giocatori sia consistente"""
    print("=== TEST 1: Consistenza giocatori ===")
    
    # Ottieni giocatori tramite funzione
    giocatori_function = get_players()
    
    # Ottieni giocatori direttamente dal foglio
    ws_selezione = worksheet("SELEZIONE")
    header = ws_selezione.row_values(1)
    giocatori_direct = header[jump_giocatri:ultimo_giocatore]
    
    print(f"Giocatori da get_players(): {len(giocatori_function)}")
    print(f"Giocatori da foglio diretto: {len(giocatori_direct)}")
    
    if giocatori_function == giocatori_direct:
        print("✓ PASS: L'ordine dei giocatori è consistente")
        return True
    else:
        print("✗ FAIL: L'ordine dei giocatori NON è consistente")
        print("Differenze:")
        for i, (f, d) in enumerate(zip(giocatori_function, giocatori_direct)):
            if f != d:
                print(f"  Posizione {i}: get_players()='{f}', foglio='{d}'")
        return False

def test_azioni_consistency():
    """Verifica che il mapping delle azioni sia corretto"""
    print("\n=== TEST 2: Consistenza azioni ===")
    
    # Ottieni azioni tramite funzione
    azioni_function = get_actions(bonus_malus=True)
    
    # Ottieni azioni direttamente dal foglio
    ws_selezione = worksheet("SELEZIONE")
    values = ws_selezione.get_all_values()
    header = values[0]
    records = [
        dict(zip(header, row))
        for row in values[1:]
        if len(row) > 0
    ]
    azioni_direct = [r['AZIONE'] for r in records if r.get('CODICE') != '']
    
    print(f"Azioni da get_actions(): {len(azioni_function)}")
    print(f"Azioni da foglio diretto: {len(azioni_direct)}")
    
    if azioni_function == azioni_direct:
        print("✓ PASS: L'elenco delle azioni è consistente")
        return True
    else:
        print("✗ FAIL: L'elenco delle azioni NON è consistente")
        # Trova differenze
        set_func = set(azioni_function)
        set_direct = set(azioni_direct)
        
        only_in_func = set_func - set_direct
        only_in_direct = set_direct - set_func
        
        if only_in_func:
            print(f"  Solo in get_actions(): {only_in_func}")
        if only_in_direct:
            print(f"  Solo in foglio diretto: {only_in_direct}")
        return False

def test_storico_mapping():
    """Verifica che il mapping delle azioni nello storico sia corretto"""
    print("\n=== TEST 3: Mapping azioni nello storico ===")
    
    ws_selezione = worksheet("SELEZIONE")
    
    # Simula la lettura dei dati come nella funzione archivia
    rng = to_a1_range(0, ultima_azione + righe_bonus_malus, 0, ultimo_giocatore)
    data = ws_selezione.get(rng)
    
    df = pd.DataFrame(data[1:], columns=data[0])
    df = df.loc[df['CODICE'] != '']
    
    # Leggi i giocatori
    header = ws_selezione.row_values(1)
    giocatori = header[jump_giocatri:ultimo_giocatore]
    
    # Simula il vecchio metodo (buggato)
    azioni_old = get_actions(bonus_malus=True)
    df_long_old = []
    
    for a, (idx, row) in enumerate(df.iterrows()):
        for g, v in row.items():
            if v == 'SI' and g in giocatori:
               df_long_old.append({'Giocatore':g, 'Azione': azioni_old[a]}) 
    
    # Simula il nuovo metodo (corretto)
    df_long_new = []
    
    for idx, row in df.iterrows():
        for g, v in row.items():
            if v == 'SI' and g in giocatori:
               df_long_new.append({'Giocatore':g, 'Azione': row['AZIONE']}) 
    
    print(f"Selezioni trovate (vecchio metodo): {len(df_long_old)}")
    print(f"Selezioni trovate (nuovo metodo): {len(df_long_new)}")
    
    if df_long_old == df_long_new:
        print("✓ PASS: Entrambi i metodi producono lo stesso risultato")
        return True
    else:
        print("✗ FAIL: I metodi producono risultati diversi")
        
        # Trova differenze
        df_old = pd.DataFrame(df_long_old)
        df_new = pd.DataFrame(df_long_new)
        
        if not df_old.empty and not df_new.empty:
            print("\nDifferenze trovate:")
            merged = df_old.merge(df_new, on=['Giocatore'], suffixes=('_old', '_new'))
            diff = merged[merged['Azione_old'] != merged['Azione_new']]
            
            if not diff.empty:
                print(diff[['Giocatore', 'Azione_old', 'Azione_new']].head(10))
        
        return False

def test_merge_with_risultati():
    """Verifica che il merge con i risultati delle azioni funzioni correttamente"""
    print("\n=== TEST 4: Merge con risultati azioni ===")
    
    ws_selezione = worksheet("SELEZIONE")
    
    # Simula la lettura dei dati
    rng = to_a1_range(0, ultima_azione + righe_bonus_malus, 0, ultimo_giocatore)
    data = ws_selezione.get(rng)
    
    df = pd.DataFrame(data[1:], columns=data[0])
    df = df.loc[df['CODICE'] != '']
    
    # Leggi i giocatori
    header = ws_selezione.row_values(1)
    giocatori = header[jump_giocatri:ultimo_giocatore]
    
    # Usa il metodo corretto
    df_long = []
    
    for idx, row in df.iterrows():
        for g, v in row.items():
            if v == 'SI' and g in giocatori:
               df_long.append({'Giocatore':g, 'Azione': row['AZIONE']}) 
    
    if not df_long:
        print("⚠ WARNING: Nessuna selezione trovata nel foglio")
        return True
    
    df_long = pd.DataFrame(df_long)
    
    # Ottieni i risultati delle azioni
    res_azioni = get_azioni_results()
    
    print(f"Selezioni: {len(df_long)}")
    print(f"Risultati azioni disponibili: {len(res_azioni)}")
    
    # Esegui il merge
    df_merged = df_long.merge(res_azioni, on='Azione')
    
    print(f"Selezioni dopo merge: {len(df_merged)}")
    
    if len(df_merged) == len(df_long):
        print("✓ PASS: Tutte le selezioni hanno corrispondenza nei risultati")
        return True
    else:
        print("✗ FAIL: Alcune selezioni non hanno corrispondenza nei risultati")
        
        # Trova azioni senza corrispondenza
        azioni_selezioni = set(df_long['Azione'])
        azioni_risultati = set(res_azioni['Azione'])
        missing = azioni_selezioni - azioni_risultati
        
        if missing:
            print(f"  Azioni senza risultato: {missing}")
        
        return False

def test_punteggi_mapping():
    """Verifica che il mapping dei punteggi sia corretto"""
    print("\n=== TEST 5: Mapping punteggi ===")
    
    ws_selezione = worksheet("SELEZIONE")
    ws_totale = worksheet("TOTALE")
    
    # Leggi i giocatori direttamente dal foglio SELEZIONE
    header = ws_selezione.row_values(1)
    giocatori = header[jump_giocatri:ultimo_giocatore]
    
    # Leggi i punteggi dal foglio SELEZIONE
    rng = to_a1_range(ultima_azione + righe_bonus_malus, ultima_azione + righe_bonus_malus+1, jump_giocatri, ultimo_giocatore)
    punteggi = ws_selezione.get(rng)
    
    print(f"Giocatori: {len(giocatori)}")
    print(f"Punteggi letti: {len(punteggi[0]) if punteggi else 0}")
    
    if len(giocatori) == len(punteggi[0]):
        print("✓ PASS: Il numero di giocatori corrisponde al numero di punteggi")
        
        # Mostra mappatura
        print("\nMappatura Giocatore -> Punteggio:")
        for i, (giocatore, punteggio) in enumerate(zip(giocatori, punteggi[0])):
            print(f"  {i+1}. {giocatore}: {punteggio}")
        
        return True
    else:
        print("✗ FAIL: Il numero di giocatori NON corrisponde al numero di punteggi")
        return False

def main():
    print("=== TEST CORREZIONI ARCHIVIA ===\n")
    
    results = []
    
    # Esegui tutti i test
    results.append(("Consistenza giocatori", test_giocatori_consistency()))
    results.append(("Consistenza azioni", test_azioni_consistency()))
    results.append(("Mapping azioni storico", test_storico_mapping()))
    results.append(("Merge con risultati", test_merge_with_risultati()))
    results.append(("Mapping punteggi", test_punteggi_mapping()))
    
    # Riepilogo
    print("\n=== RIEPILOGO ===")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotale: {passed}/{total} test passati")
    
    if passed == total:
        print("\n🎉 Tutti i test sono passati! Le correzioni sembrano corrette.")
        return 0
    else:
        print(f"\n⚠ {total - passed} test sono falliti. Controlla i problemi sopra.")
        return 1

if __name__ == "__main__":
    exit(main())