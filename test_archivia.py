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
    righe_bonus_malus, to_a1_range, get_azioni_results, n_prove
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

def test_save_picks_mapping():
    """Verifica che il mapping giocatore->colonna in save_picks sia corretto"""
    print("\n=== TEST 6: Mapping save_picks ===")
    
    ws_selezione = worksheet("SELEZIONE")
    
    # Ottieni giocatori tramite funzione
    giocatori_function = get_players()
    
    # Ottieni giocatori direttamente dal foglio
    header = ws_selezione.row_values(1)
    giocatori_direct = header[jump_giocatri:ultimo_giocatore]
    
    # Verifica che il mapping colonna sia corretto
    col_map_function = {g: i + 1 + jump_giocatri for i, g in enumerate(giocatori_function)}
    col_map_direct = {g: i + 1 + jump_giocatri for i, g in enumerate(giocatori_direct)}
    
    print(f"Mapping da get_players(): {len(col_map_function)}")
    print(f"Mapping da foglio diretto: {len(col_map_direct)}")
    
    if col_map_function == col_map_direct:
        print("✓ PASS: Il mapping giocatore->colonna è consistente")
        return True
    else:
        print("✗ FAIL: Il mapping giocatore->colonna NON è consistente")
        return False

def test_save_prove_mapping():
    """Verifica che il mapping prova->colonna in save_prove sia corretto"""
    print("\n=== TEST 7: Mapping save_prove ===")
    
    ws_selezione = worksheet("SELEZIONE")
    
    # Ottieni prove direttamente dal foglio
    header = ws_selezione.row_values(1)
    prove_direct = header[jump_giocatri - n_prove:jump_giocatri]
    
    # Verifica che il mapping colonna sia corretto
    col_map = {g: i + 1 + jump_giocatri - n_prove for i, g in enumerate(prove_direct)}
    
    print(f"Prove trovate: {len(prove_direct)}")
    print(f"Mapping colonne: {col_map}")
    
    if len(col_map) == len(prove_direct):
        print("✓ PASS: Il mapping prova->colonna è corretto")
        return True
    else:
        print("✗ FAIL: Il mapping prova->colonna NON è corretto")
        return False

def test_salva_pronostici_structure():
    """Verifica la struttura dei dati per salva_pronostici"""
    print("\n=== TEST 8: Struttura salva_pronostici ===")
    
    ws_selezione = worksheet("SELEZIONE")
    ws_pronostici = worksheet("PRONOSTICI")
    
    # Verifica il range che dovrebbe essere copiato
    rng = to_a1_range(jump_azione - 1, ultima_azione, jump_giocatri, ultimo_giocatore)
    data = ws_selezione.get(rng)
    
    print(f"Range da copiare: {rng}")
    print(f"Righe lette: {len(data)}")
    print(f"Colonne per riga: {len(data[0]) if data else 0}")
    
    # Verifica che il range abbia senso
    expected_rows = ultima_azione - jump_azione + 1
    expected_cols = ultimo_giocatore - jump_giocatri  # Corretto: slice [jump_giocatri:ultimo_giocatore] ha ultimo_giocatore - jump_giocatri elementi
    
    if len(data) == expected_rows and (len(data[0]) if data else 0) == expected_cols:
        print("✓ PASS: Il range di copia ha le dimensioni corrette")
        return True
    else:
        print(f"✗ FAIL: Dimensioni non corrette. Atteso: {expected_rows}x{expected_cols}, Trovato: {len(data)}x{len(data[0]) if data else 0}")
        return False

def test_get_actions_no_last5():
    """Verifica che get_actions_no_last5 filtri correttamente"""
    print("\n=== TEST 9: Filtraggio get_actions_no_last5 ===")
    
    ws_storico = worksheet("STORICO")
    all_records = ws_storico.get_all_records()
    
    if not all_records:
        print("⚠ WARNING: Foglio STORICO vuoto, test saltato")
        return True
    
    last_week = max([r['Settimana'] for r in all_records] + [0])
    
    if last_week == 0:
        print("⚠ WARNING: Nessuna settimana trovata, test saltato")
        return True
    
    print(f"Ultima settimana: {last_week}")
    
    # Controlla che ci siano dati per l'ultima settimana
    df = pd.DataFrame(all_records).query(f'Settimana == {last_week}')
    
    if len(df) == 0:
        print("⚠ WARNING: Nessun dato per l'ultima settimana, test saltato")
        return True
    
    print(f"Record ultima settimana: {len(df)}")
    
    # Verifica che ogni giocatore abbia esattamente 5 selezioni (escludendo B e M)
    giocatori = df['Giocatore'].unique()
    
    issues = []
    for giocatore in giocatori:
        # Escludi le azioni B e M dal conteggio
        giocatore_df = df[df['Giocatore'] == giocatore]
        selezioni_senza_bm = giocatore_df[~giocatore_df['Azione'].isin(['B', 'M'])]
        selezioni = len(selezioni_senza_bm)
        
        if selezioni != 5:
            total_selezioni = len(giocatore_df)
            bm_count = total_selezioni - selezioni
            issues.append(f"{giocatore}: {selezioni} selezioni normali (atteso: 5), totali incl. B/M: {total_selezioni}")
    
    if not issues:
        print("✓ PASS: Tutti i giocatori hanno esattamente 5 selezioni (escluse B e M)")
        return True
    else:
        print("✗ FAIL: Alcuni giocatori non hanno 5 selezioni normali:")
        for issue in issues:
            print(f"  {issue}")
        return False

def test_edge_cases():
    """Verifica casi edge"""
    print("\n=== TEST 10: Casi edge ===")
    
    ws_selezione = worksheet("SELEZIONE")
    ws_storico = worksheet("STORICO")
    
    issues = []
    
    # Test 1: Verifica che non ci siano colonne vuote tra i giocatori
    header = ws_selezione.row_values(1)
    giocatori = header[jump_giocatri:ultimo_giocatore]
    
    empty_positions = [i for i, g in enumerate(giocatori) if not g or g.strip() == '']
    if empty_positions:
        issues.append(f"Posizioni vuote tra i giocatori: {empty_positions}")
    
    # Test 2: Verifica che non ci siano duplicati nei giocatori
    if len(giocatori) != len(set(giocatori)):
        duplicates = [g for g in set(giocatori) if giocatori.count(g) > 1]
        issues.append(f"Giocatori duplicati: {duplicates}")
    
    # Test 3: Verifica che il foglio STORICO non sia vuoto
    storico_records = ws_storico.get_all_records()
    if not storico_records:
        issues.append("Foglio STORICO vuoto")
    
    # Test 4: Verifica che non ci siano codici duplicati nelle azioni (esclusi B e M che sono normali)
    values = ws_selezione.get_all_values()
    header = values[0]
    records = [
        dict(zip(header, row))
        for row in values[1:]
        if len(row) > 0
    ]
    codici = [r['CODICE'] for r in records if r.get('CODICE')]
    
    # Escludi B e M dal controllo duplicati (sono azioni speciali)
    codici_senza_bm = [c for c in codici if c not in ['B', 'M']]
    
    if len(codici_senza_bm) != len(set(codici_senza_bm)):
        duplicates = [c for c in set(codici_senza_bm) if codici_senza_bm.count(c) > 1]
        issues.append(f"Codici azione duplicati (esclusi B/M): {duplicates}")
    
    if not issues:
        print("✓ PASS: Nessun caso edge problematico trovato")
        return True
    else:
        print("✗ FAIL: Trovati casi edge problematici:")
        for issue in issues:
            print(f"  {issue}")
        return False

def test_data_integrity():
    """Verifica l'integrità dei dati tra i fogli"""
    print("\n=== TEST 11: Integrità dati tra fogli ===")
    
    ws_selezione = worksheet("SELEZIONE")
    ws_pronostici = worksheet("PRONOSTICI")
    ws_storico = worksheet("STORICO")
    
    issues = []
    
    # Test 1: Verifica che il foglio PRONOSTICI abbia la stessa struttura dei giocatori
    header_selezione = ws_selezione.row_values(1)
    giocatori_selezione = header_selezione[jump_giocatri:ultimo_giocatore]
    
    try:
        header_pronostici = ws_pronostici.row_values(1)
        if len(header_pronostici) > 0:
            # Se il foglio pronostici ha dati, verifica la struttura
            pronostici_data = ws_pronostici.get_all_values()
            if pronostici_data and len(pronostici_data) > 0:
                expected_cols = len(giocatori_selezione)
                actual_cols = len(pronostici_data[0]) if pronostici_data[0] else 0
                
                if actual_cols != expected_cols:
                    issues.append(f"PRONOSTICI: colonne {actual_cols} != attese {expected_cols}")
    except Exception as e:
        issues.append(f"Errore lettura PRONOSTICI: {e}")
    
    # Test 2: Verifica che le azioni nello STORICO esistano nel foglio SELEZIONE
    storico_records = ws_storico.get_all_records()
    if storico_records:
        storico_azioni = set(r['Azione'] for r in storico_records)
        
        values = ws_selezione.get_all_values()
        header = values[0]
        records = [
            dict(zip(header, row))
            for row in values[1:]
            if len(row) > 0
        ]
        selezione_azioni = set(r['AZIONE'] for r in records if r.get('CODICE'))
        
        missing_in_selezione = storico_azioni - selezione_azioni
        if missing_in_selezione:
            issues.append(f"Azioni in STORICO non in SELEZIONE: {missing_in_selezione}")
    
    if not issues:
        print("✓ PASS: Integrità dati verificata")
        return True
    else:
        print("✗ FAIL: Problemi di integrità dati:")
        for issue in issues:
            print(f"  {issue}")
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
    results.append(("Mapping save_picks", test_save_picks_mapping()))
    results.append(("Mapping save_prove", test_save_prove_mapping()))
    results.append(("Struttura salva_pronostici", test_salva_pronostici_structure()))
    results.append(("Filtraggio get_actions_no_last5", test_get_actions_no_last5()))
    results.append(("Casi edge", test_edge_cases()))
    results.append(("Integrità dati", test_data_integrity()))
    
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