#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tabu Search 1|rj,qj|Cmax
 • Wykres 1 – ewolucja globalnego Cmax (najlepszy dotąd).
 • Wykres 2 – Cmax aktualnego rozwiązania w każdej iteracji.
 • Dodatkowy wykres porównawczy heurystyk R↑, (R+Q)↑, Q↓, NEHRPQ.
Autor: ChatGPT (o3), 2025
"""

import matplotlib.pyplot as plt
from collections import deque
from concurrent.futures import ThreadPoolExecutor


# ───────────────────────── 1. Wczytanie danych ────────────────────────────────
def wczytaj_zadania(plik="zadania.txt"):
    """Plik: id  r  p  q (spacje)."""
    zadania, mapa = [], {}
    with open(plik, "r", encoding="utf-8") as f:
        for w in f:
            if not w.strip():
                continue
            i, r, p, q = map(int, w.split())
            z = {"id": i, "R": r, "P": p, "Q": q}
            zadania.append(z)
            mapa[i] = z
    if not zadania:
        raise ValueError("Plik zadania.txt jest pusty!")
    return zadania, mapa


lista_zadan, tasks_map = wczytaj_zadania()
ids = list(tasks_map.keys())


# ───────────────────────── 2. Funkcje pomocnicze ──────────────────────────────
def oblicz_cmax(sekw, zmap):
    t, cmax = 0, 0
    for z_id in sekw:
        z = zmap[z_id]
        start = max(t, z["R"])
        finish = start + z["P"]
        t = finish
        cmax = max(cmax, finish + z["Q"])
    return cmax


def generuj_sasiadow(sekw):
    n = len(sekw)
    for i in range(n):
        for j in range(i + 1, n):
            s = sekw[:]
            s[i], s[j] = s[j], s[i]
            yield s, tuple(sorted((sekw[i], sekw[j])))


# ───────────────────────── 3. Tabu Search ─────────────────────────────────────
def tabu_search(zmap, max_iter=1000, tabu_tenure=10, max_no_impr=100):
    """
    Zwraca:
        • najlepszą sekwencję i jej Cmax,
        • hist_curr – Cmax bieżący po każdej iteracji,
        • hist_best – najlepszy Cmax po każdej iteracji.
    """
    curr_seq = sorted(zmap.keys(), key=lambda i: zmap[i]["R"])
    curr_val = oblicz_cmax(curr_seq, zmap)
    best_seq, best_val = curr_seq[:], curr_val

    hist_curr = [curr_val]
    hist_best = [best_val]

    lista_tabu, zbior_tabu = deque(), set()
    no_impr = 0

    for _ in range(1, max_iter + 1):
        best_nei, best_nei_val, best_move = None, float("inf"), None

        sasiedzi, ruchy = zip(*list(generuj_sasiadow(curr_seq)))
        with ThreadPoolExecutor() as exe:
            wartosci = list(exe.map(lambda s: oblicz_cmax(s, zmap), sasiedzi))

        for sasiad, ruch, val in zip(sasiedzi, ruchy, wartosci):
            ruch = tuple(sorted(ruch))
            if ruch in zbior_tabu and val >= best_val:
                continue
            if val < best_nei_val:
                best_nei, best_nei_val, best_move = sasiad, val, ruch

        if best_nei is None:
            break  # wszystkie ruchy tabu bez aspiracji

        curr_seq, curr_val = best_nei, best_nei_val

        # aktualizacja tabu-listy
        lista_tabu.append(best_move)
        zbior_tabu.add(best_move)
        if len(lista_tabu) > tabu_tenure:
            zbior_tabu.discard(lista_tabu.popleft())

        # aktualizacja najlepszego globalnie
        if curr_val < best_val:
            best_seq, best_val, no_impr = curr_seq[:], curr_val, 0
        else:
            no_impr += 1

        hist_curr.append(curr_val)
        hist_best.append(best_val)

        if no_impr >= max_no_impr:
            break

    return best_seq, best_val, hist_curr, hist_best


# ─────────────────────── 4. Heurystyki porównawcze ─────────────────────────---
def heurystyki(zmap):
    idx = list(zmap)

    seq_R  = sorted(idx, key=lambda i: zmap[i]["R"])
    seq_RQ = sorted(idx, key=lambda i: zmap[i]["R"] + zmap[i]["Q"])
    seq_Q  = sorted(idx, key=lambda i: zmap[i]["Q"], reverse=True)

    def neh_rpq():
        seq_p = sorted(idx, key=lambda i: zmap[i]["P"], reverse=True)
        seq = []
        for j in seq_p:
            best, best_seq = float("inf"), None
            for pos in range(len(seq) + 1):
                tmp = seq[:]
                tmp.insert(pos, j)
                v = oblicz_cmax(tmp, zmap)
                if v < best:
                    best, best_seq = v, tmp
            seq = best_seq
        return seq

    seq_NEH = neh_rpq()

    return [
        ("R↑",      oblicz_cmax(seq_R,  zmap)),
        ("(R+Q)↑",  oblicz_cmax(seq_RQ, zmap)),
        ("Q↓",      oblicz_cmax(seq_Q,  zmap)),
        ("NEHRPQ",  oblicz_cmax(seq_NEH, zmap)),
    ]


# ───────────────────────────── 5. Wykresy ─────────────────────────────────────
def wykres_globalny(hist_best):
    """Globalny (najlepszy dotąd) Cmax w funkcji iteracji."""
    plt.figure(figsize=(8, 4.5))
    plt.plot(range(len(hist_best)), hist_best, '-o', mfc='white', ms=4)
    plt.xlabel("Iteracja")
    plt.ylabel("Najlepszy C_max")
    plt.title("Ewolucja globalnego C_max (Tabu Search)")
    plt.grid(True, linestyle=":", linewidth=0.6)
    plt.tight_layout()
    plt.savefig("global_cmax.png", dpi=300)
    plt.show()


def wykres_lokalny(hist_curr):
    """Cmax bieżącego rozwiązania w kolejnych iteracjach."""
    plt.figure(figsize=(8, 4.5))
    plt.plot(range(len(hist_curr)), hist_curr, '-s', mfc='white', ms=4,
             color='tab:orange')
    plt.xlabel("Iteracja")
    plt.ylabel("C_max bieżący")
    plt.title("C_max aktualnego rozwiązania w każdej iteracji")
    plt.grid(True, linestyle=":", linewidth=0.6)
    plt.tight_layout()
    plt.savefig("lokalne_cmax.png", dpi=300)
    plt.show()


def wykres_porownania(c_tabu, heur):
    metody = ["Tabu Search"] + [h[0] for h in heur]
    wart   = [c_tabu]        + [h[1] for h in heur]
    plt.figure(figsize=(8, 4.5))
    bars = plt.bar(metody, wart)
    plt.ylabel("C_max")
    plt.title("Porównanie C_max metod")
    plt.grid(axis="y", linestyle=":", linewidth=0.6)
    for b in bars:
        y = b.get_height()
        plt.text(b.get_x() + b.get_width()/2, y + 0.5, f"{y:.0f}",
                 ha="center", va="bottom")
    plt.tight_layout()
    plt.savefig("porownanie_cmax.png", dpi=300)
    plt.show()


# ─────────────────────────── 6. Uruchomienie ─────────────────────────────────
if __name__ == "__main__":
    print(f"█ Problem 1|rj,qj|Cmax – liczba zadań: {len(tasks_map)}")

    start_seq = sorted(ids, key=lambda i: tasks_map[i]["R"])
    print("  ▸ Sekwencja startowa:", start_seq,
          "C_max =", oblicz_cmax(start_seq, tasks_map))

    best_seq, best_c, hist_curr, hist_best = tabu_search(
        tasks_map, max_iter=1000, tabu_tenure=10, max_no_impr=100
    )
    print("  ▸ Najlepsza sekwencja TS:", best_seq,
          "C_max =", best_c)

    heur = heurystyki(tasks_map)
    for nazwa, c in heur:
        print(f"  ▸ {nazwa:<7} C_max = {c}")

    # Rysowanie wykresów
    wykres_globalny(hist_best)
    wykres_lokalny(hist_curr)
    wykres_porownania(best_c, heur)
