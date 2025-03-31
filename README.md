# Implementacja algorytmu Tabu Search dla problemu RPQ
## Wprowadzenie
Problem RPQ to jednomaszynowy problem szeregowania zadań, w którym każde zadanie $j$ ma trzy parametry:
- $R_j$ – czas przygotowania (release time), od którego zadanie jest dostępne do przetwarzania,
- $P_j$ – czas przetwarzania (processing time) na maszynie,
- $Q_j$ – czas dostarczenia (czas „po przetworzeniu” potrzebny do ukończenia zadania).

Zadania muszą być wykonane sekwencyjnie na jednej maszynie (nie mogą się nakładać). Maszyna może rozpocząć zadanie dopiero, gdy nadejdzie czas $R_j$ tego zadania oraz gdy zakończy przetwarzanie poprzedniego. Po przetworzeniu przez czas $P_j$ zadanie uzyskuje czas zakończenia równy momentowi zakończenia przetwarzania plus $Q_j$ (czyli $C_j = \text{finish}j + Q_j$). Celem optymalizacji jest minimalizacja maksymalnego czasu zakończenia wszystkich zadań, czyli minimalizacja $C{\max} = \max_j C_j$. Intuicyjnie $C_{\max}$ oznacza moment, w którym ukończone (dostarczone) zostanie ostatnie zadanie w harmonogramie. 
Ponieważ problem RPQ (minimalizacji $C_{\max}$ przy ograniczeniach $R_j$, $Q_j$) jest złożony obliczeniowo (NP-trudny dla wielu zadań), zastosujemy podejście metaheurystyczne – algorytm przeszukiwania z zabronieniami (Tabu Search) – aby znaleźć bliskie optymalnym rozwiązania w rozsądnym czasie. Tabu Search to algorytm poprawy iteracyjnej, który eksploruje sąsiedztwo bieżącego rozwiązania w poszukiwaniu lepszego rozkładu zadań, a dzięki mechanizmowi pamięci (liście tabu) unika powtarzania niedawnych ruchów i utykania w pułapkach lokalnych minimów

## Działanie algorytmu Tabu Search w problemie RPQ
Algorytm Tabu Search (TS) inicjalizuje się pewnym rozwiązaniem (harmonogramem zadań), a następnie iteracyjnie ulepsza je, przeszukując przestrzeń możliwych permutacji zadań. W kontekście problemu RPQ ogólne kroki algorytmu wyglądają następująco:
1. Inicjalizacja: Wygeneruj rozwiązanie początkowe (np. posortuj zadania rosnąco według czasów $R_j$ lub użyj rozwiązania losowego). Oblicz wartość funkcji celu ($C_{\max}$) dla tego rozwiązania. Ustaw to rozwiązanie jako bieżące oraz jako najlepsze znalezione do tej pory. Zainicjuj pustą listę tabu.
2. Generowanie sąsiadów: Wygeneruj zbiór rozwiązań sąsiednich względem bieżącego – w tym przypadku przez niewielką zmianę kolejności zadań (np. zamianę miejscami dwóch zadań w sekwencji).
3. Wybór najlepszego sąsiada: Dla każdego sąsiedniego rozwiązania oblicz wartość $C_{\max}$. Wybierz rozwiązanie najlepsze (o najmniejszym $C_{\max}$) spośród sąsiadów dopuszczalnych, tzn. takich, które nie są zabronione przez listę tabu (chyba że naruszając tabu poprawiłoby dotychczas najlepsze rozwiązanie – tzw. kryterium aspiracji pozwalające pominąć tabu).
4. Aktualizacja stanu: Ustaw wybranego najlepszego sąsiada jako nowe bieżące rozwiązanie. Jeśli jest lepsze niż dotychczas najlepsze znane, zaktualizuj najlepsze rozwiązanie. Dodaj wykonany ruch (zmianę w kolejności zadań prowadzącą do tego sąsiada) do listy tabu i usuń z listy tabu najdawniejszy wpis, jeśli lista tabu przekracza ustaloną wielkość (tzw. okres tabu lub tabu tenure).
5. Kontynuacja/Stop: Powtarzaj kroki 2–4 aż do spełnienia kryterium stopu (np. ustalona maksymalna liczba iteracji lub brak poprawy rozwiązania przez dłuższy czas). Zwróć najlepsze znalezione rozwiązanie jako wynik algorytmu.

Powyższy schemat ilustruje, jak Tabu Search przeszukuje przestrzeń permutacji zadań. Dzięki liście tabu algorytm nie cofnie się natychmiast do niedawno odwiedzonego rozwiązania (nawet jeśli w danym kroku wydawałoby się ono najlepsze), co zapobiega cyklicznemu oscylowaniu wokół tego samego układu​.

Kryterium aspiracji natomiast umożliwia złamanie zakazu tabu dla ruchu, który prowadzi do rozwiązania lepszego niż jakiekolwiek dotąd napotkane – dzięki temu nie blokujemy drogi do globalnego optimum przez zbyt restrykcyjne tabu. W kolejnych sekcjach omówiono szczegóły implementacyjne: sposób reprezentacji rozwiązań i listy tabu, metodę generowania sąsiedztwa, obliczanie funkcji celu oraz utrzymanie najlepszego rozwiązania w trakcie iteracji.

## Reprezentacja rozwiązań i struktura danych
Rozwiązanie (harmonogram) będziemy reprezentować jako permutację identyfikatorów zadań. Przykładowo, rozwiązanie $[2,,1,,3,,4]$ oznacza, że jako pierwsze wykonywane jest zadanie 2, następnie 1, potem 3 i 4. Taka lista definiuje jednoznacznie harmonogram na maszynie jednozadaniowej.

Do przechowywania parametrów zadań ($R$, $P$, $Q$) użyjemy prostej struktury danych, np. listy słowników lub krotek. W implementacji poniżej wykorzystano listę słowników Python, gdzie każdy słownik ma klucze "id", "R", "P", "Q". Dodatkowo, dla wygody obliczeń, przekształcamy tę listę na słownik (tasks_map), którego kluczem jest id zadania, a wartością – słownik z jego parametrami. Dzięki temu łatwo odwoływać się do danych zadania poprzez jego identyfikator.

Lista tabu będzie przechowywać ograniczoną pamięć ostatnio wykonanych ruchów (modyfikacji rozwiązania). W kontekście permutacji zadań jako ruch naturalnie definiujemy zamianę miejsc dwóch zadań. Taki ruch można zapisać jako parę identyfikatorów zadań (lub ich pozycji) zamienionych ze sobą. Aby uprościć sprawdzanie ruchów niezależnie od kolejności pary, można zapisywać je w uporządkowanej formie, np. (min(id_i, id_j), max(id_i, id_j)).

Implementacyjnie wygodna jest struktura FIFO, np. kolejka (collections.deque), do której dodajemy każdy wykonany ruch. Jeśli długość kolejki przekracza ustalony tabu tenure (liczbę iteracji, przez jakie ruch ma pozostać zabroniony), usuwamy najstarszy ruch (z końca kolejki). Dodatkowo użyjemy struktury set (zbioru) do szybkiego sprawdzania, czy dany ruch jest obecnie na liście tabu. W ten sposób lista tabu będzie zawierać ostatnie $k$ wykonanych ruchów (gdzie $k$ to przyjęty parametr, np. 5 czy 10), które nie powinny być ponownie wykonane w kolejnym kroku (chyba że zadziała kryterium aspiracji).

## Funkcja oceny: obliczanie $C_{\max}$
Aby porównać rozwiązania, potrzebujemy funkcji oceny obliczającej $C_{\max}$ dla danej permutacji zadań. Dla ustalonej kolejności zadań symulujemy harmonogram i wyznaczamy czasy zakończenia:
- Utrzymujemy bieżący czas maszyny czas (początkowo 0).
- Iterujemy przez zadania w permutacji. Dla każdego zadania $j$ w kolejności:
  - Wyznaczamy czas rozpoczęcia jako $\text{start}_j = \max(\text{czas}, R_j)$ (maszyna czeka do końca poprzedniego zadania lub dostępności bieżącego, w zależności co nastąpi później).
  - Obliczamy czas zakończenia przetwarzania: $\text{finish}_j = \text{start}_j + P_j$. Następnie aktualizujemy czas = \text{finish}_j (maszyna będzie wolna od tego czasu).
  - Obliczamy pełny czas ukończenia zadania (z dostarczeniem): $C_j = \text{finish}_j + Q_j$.
- Po przetworzeniu wszystkich zadań obliczamy $C_{\max} = \max_j C_j$.

Warto zauważyć, że maszyna nie musi czekać na ukończenie dostarczenia $Q_j$ danego zadania, aby rozpocząć następne – $Q_j$ wpływa tylko na metrykę celu $C_{\max}$, ale nie blokuje maszyny (zadanie "dostarcza się" równolegle do wykonywania kolejnych, co jest istotą problemu RPQ). Dlatego w powyższej procedurze czas jest zwiększany tylko o $P_j$, natomiast $Q_j$ wpływa na wartość $C_j$, która może wyznaczać $C_{\max}$ nawet jeśli maszyna w tym czasie obsługuje już następne zadania. 

Tę logikę zaimplementujemy w funkcji oblicz_cmax(sekwencja, zadania) zwracającej wartość $C_{\max}$ dla zadanej permutacji sekwencja.

## Generowanie sąsiedztwa (rozwiązań sąsiednich)
Najprostszą i najczęściej stosowaną strategią generowania sąsiedztwa w problemach harmonogramowania (gdzie rozwiązanie jest permutacją) jest zamiana dwóch zadań miejscami (tzw. ruch typu swap). Sąsiedzi bieżącego rozwiązania to więc wszystkie permutacje, które można otrzymać poprzez pojedynczą zamianę pozycji dwóch zadań w obecnej sekwencji.

Jeśli mamy $n$ zadań, liczba takich sąsiadów wynosi $\binom{n}{2} = \frac{n(n-1)}{2}$ (każdą parę pozycji możemy zamienić). Dla umiarkowanych $n$ (dziesiątki, setki) jest to akceptowalne; dla bardzo dużych $n$ można losowo podpróbkować sąsiedztwo, ale w naszym przypadku przeglądamy pełne sąsiedztwo dla większej skuteczności algorytmu.

W implementacji generujemy sąsiadów za pomocą zagnieżdżonych pętli: wybieramy indeksy i < j i tworzymy kopię bieżącej sekwencji z zamienionymi elementami na pozycjach i oraz j. Dla każdego takiego sąsiada obliczamy $C_{\max}$. Następnie wybierzemy spośród nich rozwiązanie o najlepszej wartości celu (najmniejsze $C_{\max}$), respektując ograniczenia listy tabu.

## Mechanizm aktualizacji najlepszego rozwiązania i listy tabu
Przy wyborze najlepszego ruchu musimy uwzględnić listę tabu. Każdy potencjalny ruch (zamiana dwóch zadań) sprawdzany jest pod kątem obecności na liście tabu. Jeśli ruch znajduje się na liście tabu, oznacza to, że niedawno był wykonywany i nie powinien być ponownie wykonany zbyt szybko, aby algorytm nie cofał się do poprzednich rozwiązań. Taki ruch pomijamy chyba że prowadzi on do rozwiązania lepszego niż dotychczasowe globalnie najlepsze – w takim przypadku zadziała kryterium aspiracji i możemy ten ruch wykonać mimo tabu (ponieważ daje nowy najlepszy wynik).

Po wyłonieniu najlepszego dozwolonego sąsiada (najmniejsze $C_{\max}$ spośród nie-tabu lub aspiracyjnych), algorytm aktualizuje bieżące rozwiązanie do tego wybranego sąsiada. Następnie następuje aktualizacja pamięci i wyników:
- Do listy tabu dodajemy ruch (parę zadań), który został wykonany (zamienionych w tej iteracji). Będzie on zabroniony przez następne ustalone $T$ iteracji (parametr tabu_tenure). W praktyce dodajemy ten ruch do kolejki lista_tabu. Jeśli liczba ruchów w kolejce przekracza $T$, usuwamy najstarszy (czyli ten, który wystarczająco długo już pozostawał tabu).
- Sprawdzamy, czy nowe bieżące rozwiązanie nie jest najlepszym z dotąd znalezionych. Jeśli tak, zapisujemy je jako nowe najlepsze rozwiązanie (oraz jego wartość $C_{\max}$). Dzięki temu po zakończeniu algorytmu będziemy mieli zachowane rozwiązanie globalnie najlepsze napotkane w trakcie poszukiwań, a nie tylko ostatnie.

Proces iteracyjny kontynuujemy, generując kolejne sąsiedztwa od nowego bieżącego rozwiązania, modyfikując listę tabu i aktualizując najlepsze znalezione rozwiązanie. Złożoność jednej iteracji wynosi ok. $O(n^2)$ (tyle potencjalnych sąsiadów oceniamy). W praktyce liczba iteracji i rozmiar listy tabu są dobierane doświadczalnie. Zbyt mała lista tabu może powodować szybkie powroty do poprzednich rozwiązań (cykle), a zbyt duża może ograniczyć przeszukiwanie okolicy bieżącego rozwiązania. Typowo przyjmuje się tabu_tenure rzędu od kilku do kilkudziesięciu ruchów, w zależności od rozmiaru problemu.

## Przykładowe dane testowe i działanie algorytmu
Rozważmy przykład z 4 zadaniami o następujących parametrach:

| Zadanie (ID) | $R$ (czas dostępności) | $P$ (czas przetwarzania) | $Q$ (czas dostarczenia) |
|--------------|------------------------|--------------------------|-------------------------|
| 1            | 0                      | 3                        | 3                       |
| 2            | 1                      | 2                        | 8                       |
| 3            | 2                      | 1                        | 4                       |
| 4            | 3                      | 4                        | 1                       |

Dla powyższego zestawu zadań rozwiązanie początkowe możemy wybrać według rosnących czasów przygotowania $R$. Daje to sekwencję $[1,,2,,3,,4]$. Obliczmy jej $C_{\max}$:
- Zadanie 1: start = max(0, R1=0) = 0; finish = 0 + P1=3 = 3; $C_1 = 3 + Q1=3 = 6$.
- Zadanie 2: start = max(3, R2=1) = 3; finish = 3 + P2=2 = 5; $C_2 = 5 + Q2=8 = 13$.
- Zadanie 3: start = max(5, R3=2) = 5; finish = 5 + P3=1 = 6; $C_3 = 6 + Q3=4 = 10$.
- Zadanie 4: start = max(6, R4=3) = 6; finish = 6 + P4=4 = 10; $C_4 = 10 + Q4=1 = 11$.

Dla sekwencji początkowej $[1,2,3,4]$ maksymalny czas zakończenia zadań wynosi $C_{\max} = \max(C_1, C_2, C_3, C_4) = \max(6, 13, 10, 11) = 13$. Czy można lepiej ułożyć kolejność? Zauważmy, że zadanie 2 ma dość duży czas dostarczenia $Q_2=8$. W harmonogramie na końcu (po zadaniu 1) jego dostarczenie wydłużyło cały $C_{\max}$ do 13. Intuicyjnie warto spróbować przestawić zadanie 2 wcześniej, aby czas jego dostarczenia mógł upłynąć, gdy inne zadania są w toku. Rzeczywiście, zamieniając kolejność zadań 1 i 2, otrzymujemy sekwencję $[2,,1,,3,,4]$. Dla niej:
- Zadanie 2 (pierwsze): start = max(0, R2=1) = 1; finish = 1 + P2=3; $C_2 = 3 + Q2 = 11$.
- Zadanie 1 (drugie): start = max(3, R1=0) = 3; finish = 3 + P1=6; $C_1 = 6 + Q1 = 9$.
- Zadanie 3: start = max(6, R3=2) = 6; finish = 6 + P3=7; $C_3 = 7 + Q3 = 11$.
- Zadanie 4: start = max(7, R4=3) = 7; finish = 7 + P4=11; $C_4 = 11 + Q4 = 12$. Teraz $C_{\max} = \max(11,9,11,12) = 12$. Jest lepiej niż 13. Okazuje się (sprawdzając wszystkie permutacje), że $[2,1,3,4]$ jest rozwiązaniem optymalnym z $C_{\max}=12$ dla tego zestawu danych.

Algorytm Tabu Search powinien odnaleźć tę lepszą sekwencję zaczynając od $[1,2,3,4]$. W kolejnych iteracjach będzie on próbował zamian zadań. Między innymi rozważy zamianę zadań 1 i 2, która (jak widzieliśmy) obniża $C_{\max}$ do 12 – taki ruch nie będzie zabroniony początkowo, więc zostanie wykonany. Następnie algorytm spróbuje dalszych zamian, ale prawdopodobnie nie znajdzie już lepszego wyniku niż 12 (inne zamiany pogorszą lub nie poprawią $C_{\max}$). Dzięki pamięci tabu nie będzie też od razu wracał do poprzedniej kolejności. W efekcie najlepsze rozwiązanie zapisane przez algorytm to właśnie $[2,1,3,4]$ o $C_{\max}=12$. Poniżej przedstawiono implementację, która ilustruje działanie algorytmu na tym przykładzie.
