import random
from collections import deque
from concurrent.futures import ThreadPoolExecutor

def wczytaj_zadania(plik="zadania.txt"):
    zadania = []
    with open(plik, "r") as f:
        for linia in f:
            czesci = linia.strip().split()
            if len(czesci) == 4:
                ident, R, P, Q = map(int, czesci)
                zadania.append({"id": ident, "R": R, "P": P, "Q": Q})
    return zadania

zadania = wczytaj_zadania()

# Konwersja listy zadań do słownika dla wygodniejszego dostępu po id zadania
tasks_map = {task["id"]: task for task in zadania}

# Funkcja obliczająca Cmax dla danego porządku zadań (sekwencji) 
def oblicz_cmax(sekwencja, zadania):
    czas = 0
    cmax = 0
    for zad_id in sekwencja:
        # Ustalenie czasu startu (zadanie nie może rozpocząć przed czasem dostępności R)
        start = max(czas, zadania[zad_id]["R"])
        finish = start + zadania[zad_id]["P"]
        czas = finish  # maszyna kończy przetwarzanie zadania 'zad_id' o czasie finish
        # Czas ukończenia zadania (z uwzględnieniem dostarczenia Q)
        completion = finish + zadania[zad_id]["Q"]
        if completion > cmax:
            cmax = completion
    return cmax


# Funkcja generująca wszystkie sąsiedztwa
def generuj_sasiadów(sekwencja):
    n = len(sekwencja)
    sąsiedzi = []
    for i in range(n):
        for j in range(i + 1, n):
            sasiad = sekwencja[:]
            sasiad[i], sasiad[j] = sasiad[j], sasiad[i]  # zamiana miejscami dwóch zadań
            sąsiedzi.append(sasiad)
    return sąsiedzi

# Funkcja realizująca algorytm Tabu Search z równoległym przetwarzaniem
def tabu_search(zadania, max_iter=1000, tabu_tenure=5, max_no_improvement=50):
    # Rozwiązanie początkowe: zadania posortowane rosnąco po czasie dostępności R
    aktualna_sekwencja = sorted(zadania.keys(), key=lambda x: zadania[x]["R"])
    aktualna_wartosc = oblicz_cmax(aktualna_sekwencja, zadania)
    najlepsza_sekwencja = aktualna_sekwencja[:]
    najlepsza_wartosc = aktualna_wartosc
    
    # Inicjalizacja listy tabu (deque) oraz zbioru dla szybkiej kontroli ruchów tabu
    lista_tabu = deque()
    zbior_tabu = set()
    
    no_improvement = 0  # Licznik iteracji bez poprawy
    
    # Główna pętla iteracyjna Tabu Search
    for it in range(max_iter):
        najlepszy_sasiad = None
        najlepszy_sasiad_wart = float("inf")
        najlepszy_ruch = None
        
        # Generowanie wszystkich możliwych sąsiadów równolegle
        with ThreadPoolExecutor() as executor:
            # Tworzymy wszystkie sąsiedztwa
            sąsiedzi = generuj_sasiadów(aktualna_sekwencja)
            wyniki = list(executor.map(lambda s: oblicz_cmax(s, zadania), sąsiedzi))
        
        for idx, wartosc in enumerate(wyniki):
            sasiad = sąsiedzi[idx]
            
            # Użyjemy tylko poprawnego generowania ruchów przez zamianę dwóch zadań
            for i in range(len(sasiad)):
                for j in range(i + 1, len(sasiad)):
                    # Zamiana miejscami dwóch elementów w sekwencji
                    ruch = tuple(sorted((sasiad[i], sasiad[j])))

                    # Sprawdzamy warunek tabu: jeśli ruch jest zabroniony i nie poprawia najlepszego wyniku, pomijamy go
                    if ruch in zbior_tabu and wartosc >= najlepsza_wartosc:
                        continue  # ruch tabu (brak aspiracji)
                    # Jeśli ruch nie jest tabu *lub* jest aspiracyjny (daje lepszy wynik niż dotychczasowy najlepszy)
                    if wartosc < najlepszy_sasiad_wart:
                        najlepszy_sasiad_wart = wartosc
                        najlepszy_sasiad = sasiad
                        najlepszy_ruch = ruch
        
        # Jeśli nie znaleziono żadnego sąsiada (może się zdarzyć przy zbyt restrykcyjnej liście tabu) – przerwij
        if najlepszy_sasiad is None:
            break
        
        # Przejdź do najlepszego znalezionego sąsiada
        aktualna_sekwencja = najlepszy_sasiad
        aktualna_wartosc = najlepszy_sasiad_wart
        
        # Dodaj wykonany ruch do listy tabu i usuń najstarszy ruch jeśli przekroczono rozmiar tabu_tenure
        lista_tabu.append(najlepszy_ruch)
        zbior_tabu.add(najlepszy_ruch)
        if len(lista_tabu) > tabu_tenure:
            najstarszy = lista_tabu.popleft()
            zbior_tabu.discard(najstarszy)
        
        # Aktualizacja najlepszego globalnie rozwiązania
        if aktualna_wartosc < najlepsza_wartosc:
            najlepsza_wartosc = aktualna_wartosc
            najlepsza_sekwencja = aktualna_sekwencja[:]
            no_improvement = 0  # Resetujemy licznik, gdy poprawa została znaleziona
        else:
            no_improvement += 1

        # Jeśli przez 50 iteracji nie znaleziono żadnej poprawy, przechodzimy do następnego rozwiązania
        if no_improvement >= max_no_improvement:
            print(f"Brak poprawy przez {max_no_improvement} iteracji. Zatrzymywanie algorytmu.")
            break

    # Zwróć najlepsze znalezione rozwiązanie oraz jego Cmax
    return najlepsza_sekwencja, najlepsza_wartosc

# Uruchomienie algorytmu dla przykładowych danych
pocz_sekw = sorted(tasks_map.keys(), key=lambda x: tasks_map[x]["R"])
print("Rozwiazanie poczatkowe:", pocz_sekw, "Cmax =", oblicz_cmax(pocz_sekw, tasks_map))
najlepsza_sekw, najlepszy_wynik = tabu_search(tasks_map, max_iter=1000, tabu_tenure=10, max_no_improvement=50)
print("Najlepsza znaleziona sekwencja:", najlepsza_sekw, "Cmax =", najlepszy_wynik)
