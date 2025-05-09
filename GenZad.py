import random

def generuj_zadania(n, R_max=10, P_max=10, Q_max=10, plik="zadania.txt"):
    with open(plik, "w") as f:
        for i in range(1, n + 1):
            R = random.randint(0, R_max)
            P = random.randint(1, P_max)
            Q = random.randint(1, Q_max)
            f.write(f"{i} {R} {P} {Q}\n")
    print(f"Wygenerowano {n} zadan i zapisano do pliku '{plik}'.")


generuj_zadania(160)  # generuje x zadań
