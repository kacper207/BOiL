def metoda_maksymalnego_elementu(koszty, podaz, popyt):
    m = len(koszty)
    n = len(koszty[0])

    podaz = list(podaz)
    popyt = list(popyt)
    alokacja = [[0] * n for _ in range(m)]
    wiersze_wycz = [False] * m
    kolumny_wycz = [False] * n

    while True:
        max_koszt = -1
        max_i, max_j = -1, -1

        for i in range(m):
            if wiersze_wycz[i]:
                continue
            for j in range(n):
                if kolumny_wycz[j]:
                    continue
                if koszty[i][j] > max_koszt:
                    max_koszt = koszty[i][j]
                    max_i, max_j = i, j

        if max_i == -1:
            break

        przydz = min(podaz[max_i], popyt[max_j])
        alokacja[max_i][max_j] = przydz
        podaz[max_i] -= przydz
        popyt[max_j] -= przydz

        if podaz[max_i] == 0:
            wiersze_wycz[max_i] = True
        if popyt[max_j] == 0:
            kolumny_wycz[max_j] = True

    koszt_calkowity = sum(
        alokacja[i][j] * koszty[i][j]
        for i in range(m)
        for j in range(n)
    )

    return alokacja, koszt_calkowity


koszty = [
    [2, 3, 11],
    [1, 0,  6],
    [5, 8, 15],
]
podaz = [120, 80, 80]
popyt = [150, 70, 60]

alokacja, koszt = metoda_maksymalnego_elementu(koszty, podaz, popyt)

for wiersz in alokacja:
    print(wiersz)
print(koszt)