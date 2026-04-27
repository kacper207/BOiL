import tkinter as tk
from tkinter import ttk, messagebox, font
import copy

# LOGIKA ALGORYTMU


def solve_transport(supply, demand, cost, blocked):
    m = len(supply)
    n = len(demand)

    supply_rem = list(supply)
    demand_rem = list(demand)
    allocation = [[0]*n for _ in range(m)]
    iterations = []   # lista kroków

    # INF dla zablokowanych
    INF = float('inf')

    done_rows = [False]*m
    done_cols = [False]*n

    step = 0
    while True:
        #  maksimum wśród dostępnych cel
        best_val = -1
        best_i, best_j = -1, -1
        for i in range(m):
            if done_rows[i]:
                continue
            for j in range(n):
                if done_cols[j]:
                    continue
                if (i, j) in blocked:
                    continue
                if cost[i][j] > best_val:
                    best_val = cost[i][j]
                    best_i, best_j = i, j

        if best_i == -1:
            break  # nic już nie można przydzielić

        i, j = best_i, best_j
        qty = min(supply_rem[i], demand_rem[j])
        allocation[i][j] += qty
        supply_rem[i] -= qty
        demand_rem[j] -= qty

        step += 1
        iterations.append({
            "step": step,
            "i": i, "j": j,
            "cost": cost[i][j],
            "qty": qty,
            "supply_rem": list(supply_rem),
            "demand_rem": list(demand_rem),
            "allocation": copy.deepcopy(allocation),
        })

        if supply_rem[i] == 0:
            done_rows[i] = True
        if demand_rem[j] == 0:
            done_cols[j] = True

        if all(done_rows) or all(done_cols):
            break

    return allocation, iterations


def total_cost(allocation, cost):
    return sum(allocation[i][j]*cost[i][j]
               for i in range(len(allocation))
               for j in range(len(allocation[0])))

# GUI


class TransportApp(tk.Tk):
    MAX = 10

    def __init__(self):
        super().__init__()
        self.title("Zagadnienie Pośrednika – Metoda Max. Elementu Macierzy")
        self.configure(bg="#0f1117")
        self.resizable(True, True)

        # Fonts
        self.ft_title  = font.Font(family="Courier New", size=15, weight="bold")
        self.ft_label  = font.Font(family="Courier New", size=10)
        self.ft_small  = font.Font(family="Courier New", size=9)
        self.ft_header = font.Font(family="Courier New", size=10, weight="bold")

        # Stan
        self.m_var = tk.IntVar(value=3)
        self.n_var = tk.IntVar(value=3)
        self.blocked_cells = set()

        self._build_ui()

    # budowanie interfejsu

    def _build_ui(self):
        # Nagłówek
        hdr = tk.Frame(self, bg="#0f1117")
        hdr.pack(fill="x", padx=20, pady=(16,4))
        tk.Label(hdr, text="ZAGADNIENIE  POŚREDNIKA",
                 font=self.ft_title, bg="#0f1117", fg="#00e5ff").pack(side="left")
        tk.Label(hdr, text="metoda max. elementu macierzy",
                 font=self.ft_small, bg="#0f1117", fg="#546e7a").pack(side="left", padx=12)

        # Pasek rozmiarów
        size_bar = tk.Frame(self, bg="#161b22", pady=8)
        size_bar.pack(fill="x", padx=20, pady=4)
        tk.Label(size_bar, text="Dostawcy (m):", font=self.ft_label,
                 bg="#161b22", fg="#cfd8dc").pack(side="left", padx=8)
        self.spin_m = ttk.Spinbox(size_bar, from_=2, to=self.MAX,
                                  textvariable=self.m_var, width=4,
                                  command=self._rebuild_matrix)
        self.spin_m.pack(side="left")
        tk.Label(size_bar, text="  Odbiorcy (n):", font=self.ft_label,
                 bg="#161b22", fg="#cfd8dc").pack(side="left", padx=8)
        self.spin_n = ttk.Spinbox(size_bar, from_=2, to=self.MAX,
                                  textvariable=self.n_var, width=4,
                                  command=self._rebuild_matrix)
        self.spin_n.pack(side="left")
        tk.Button(size_bar, text="Zastosuj rozmiar", font=self.ft_small,
                  bg="#1e3a5f", fg="#90caf9", relief="flat",
                  command=self._rebuild_matrix, padx=10).pack(side="left", padx=14)

        # Główny panel
        main = tk.Frame(self, bg="#0f1117")
        main.pack(fill="both", expand=True, padx=20, pady=6)

        left  = tk.Frame(main, bg="#0f1117")
        right = tk.Frame(main, bg="#0f1117")
        left.pack(side="left", fill="both", expand=False, padx=(0,10))
        right.pack(side="left", fill="both", expand=True)

        # dane wejściowe
        tk.Label(left, text="▸ Dane wejściowe", font=self.ft_header,
                 bg="#0f1117", fg="#80cbc4").pack(anchor="w")

        self.matrix_frame = tk.Frame(left, bg="#161b22", padx=10, pady=10)
        self.matrix_frame.pack(fill="x", pady=4)

        tk.Label(left, text="Kliknij komórkę kosztu PPM aby zablokować trasę",
                 font=self.ft_small, bg="#0f1117", fg="#546e7a").pack(anchor="w")

        # Przyciski
        btn_frame = tk.Frame(left, bg="#0f1117")
        btn_frame.pack(fill="x", pady=6)
        tk.Button(btn_frame, text="▶  OBLICZ", font=self.ft_label,
                  bg="#00838f", fg="white", relief="flat",
                  command=self._solve, padx=16, pady=6).pack(side="left", padx=4)
        tk.Button(btn_frame, text="↺  Reset", font=self.ft_small,
                  bg="#263238", fg="#90a4ae", relief="flat",
                  command=self._reset, padx=10).pack(side="left", padx=4)
        tk.Button(btn_frame, text="Przykład", font=self.ft_small,
                  bg="#1a237e", fg="#90caf9", relief="flat",
                  command=self._load_example, padx=10).pack(side="left", padx=4)

        # Zablokowane trasy
        tk.Label(left, text="Zablokowane trasy:", font=self.ft_small,
                 bg="#0f1117", fg="#546e7a").pack(anchor="w", pady=(6,0))
        self.blocked_label = tk.Label(left, text="brak",
                                      font=self.ft_small, bg="#0f1117", fg="#ef9a9a",
                                      wraplength=300, justify="left")
        self.blocked_label.pack(anchor="w")

        # wyniki
        tk.Label(right, text="▸ Wyniki", font=self.ft_header,
                 bg="#0f1117", fg="#80cbc4").pack(anchor="w")

        self.result_canvas = tk.Canvas(right, bg="#0f1117", highlightthickness=0)
        result_scroll = ttk.Scrollbar(right, orient="vertical",
                                      command=self.result_canvas.yview)
        self.result_canvas.configure(yscrollcommand=result_scroll.set)
        result_scroll.pack(side="right", fill="y")
        self.result_canvas.pack(side="left", fill="both", expand=True)
        self.result_inner = tk.Frame(self.result_canvas, bg="#0f1117")
        self.result_canvas_window = self.result_canvas.create_window(
            (0,0), window=self.result_inner, anchor="nw")
        self.result_inner.bind("<Configure>", self._on_result_configure)
        self.result_canvas.bind("<Configure>", self._on_canvas_configure)

        # zbuduj macierz po raz pierwszy
        self._rebuild_matrix()

    def _on_result_configure(self, event):
        self.result_canvas.configure(scrollregion=self.result_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.result_canvas.itemconfig(self.result_canvas_window, width=event.width)

    #  budowanie macierzy wejściowej

    def _rebuild_matrix(self):
        for w in self.matrix_frame.winfo_children():
            w.destroy()
        self.blocked_cells.clear()
        self._update_blocked_label()

        m = self.m_var.get()
        n = self.n_var.get()


        self.cost_vars   = [[tk.StringVar(value="0") for _ in range(n)] for _ in range(m)]
        self.supply_vars = [tk.StringVar(value="0") for _ in range(m)]
        self.demand_vars = [tk.StringVar(value="0") for _ in range(n)]
        self.cost_entries = []

        CLR_BG   = "#161b22"
        CLR_HEAD = "#263238"
        CLR_CELL = "#1c2733"
        CLR_FG   = "#e0f2f1"

        # Nagłówki kolumn
        tk.Label(self.matrix_frame, text="", width=4,
                 bg=CLR_HEAD, fg=CLR_FG, font=self.ft_small,
                 relief="flat").grid(row=0, column=0, padx=1, pady=1)
        for j in range(n):
            tk.Label(self.matrix_frame, text=f"O{j+1}", width=6,
                     bg=CLR_HEAD, fg="#80cbc4", font=self.ft_header,
                     relief="flat").grid(row=0, column=j+1, padx=1, pady=1)
        tk.Label(self.matrix_frame, text="Podaż", width=7,
                 bg=CLR_HEAD, fg="#ffcc80", font=self.ft_header,
                 relief="flat").grid(row=0, column=n+1, padx=1, pady=1)

        row_entries = []
        for i in range(m):
            tk.Label(self.matrix_frame, text=f"D{i+1}", width=4,
                     bg=CLR_HEAD, fg="#80cbc4", font=self.ft_header,
                     relief="flat").grid(row=i+1, column=0, padx=1, pady=1)
            col_entries = []
            for j in range(n):
                e = tk.Entry(self.matrix_frame, textvariable=self.cost_vars[i][j],
                             width=6, bg=CLR_CELL, fg=CLR_FG, insertbackground=CLR_FG,
                             relief="flat", font=self.ft_small, justify="center")
                e.grid(row=i+1, column=j+1, padx=1, pady=1)
                e.bind("<Button-3>", lambda ev, ii=i, jj=j: self._toggle_block(ii, jj))
                col_entries.append(e)
            row_entries.append(col_entries)

            # Podaż
            es = tk.Entry(self.matrix_frame, textvariable=self.supply_vars[i],
                          width=7, bg="#1a2a1a", fg="#a5d6a7", insertbackground="#a5d6a7",
                          relief="flat", font=self.ft_small, justify="center")
            es.grid(row=i+1, column=n+1, padx=1, pady=1)

        self.cost_entries = row_entries

        # Wiersz Popyt
        tk.Label(self.matrix_frame, text="Popyt", width=4,
                 bg=CLR_HEAD, fg="#ffcc80", font=self.ft_header,
                 relief="flat").grid(row=m+1, column=0, padx=1, pady=1)
        for j in range(n):
            ed = tk.Entry(self.matrix_frame, textvariable=self.demand_vars[j],
                          width=6, bg="#1a1a2a", fg="#ce93d8", insertbackground="#ce93d8",
                          relief="flat", font=self.ft_small, justify="center")
            ed.grid(row=m+1, column=j+1, padx=1, pady=1)

    #  blokowanie tras

    def _toggle_block(self, i, j):
        if (i, j) in self.blocked_cells:
            self.blocked_cells.discard((i, j))
            self.cost_entries[i][j].configure(bg="#1c2733", fg="#e0f2f1")
        else:
            self.blocked_cells.add((i, j))
            self.cost_entries[i][j].configure(bg="#4a1010", fg="#ef9a9a")
        self._update_blocked_label()

    def _update_blocked_label(self):
        if not self.blocked_cells:
            self.blocked_label.configure(text="brak")
        else:
            txt = ", ".join(f"D{i+1}→O{j+1}" for i,j in sorted(self.blocked_cells))
            self.blocked_label.configure(text=txt)

    #  akcje przycisków

    def _reset(self):
        self._rebuild_matrix()
        for w in self.result_inner.winfo_children():
            w.destroy()

    def _load_example(self):
        self.m_var.set(3)
        self.n_var.set(4)
        self._rebuild_matrix()

        costs = [
            [2, 3, 1, 5],
            [7, 3, 4, 6],
            [3, 5, 2, 4],
        ]
        supply = [120, 80, 80]
        demand = [150, 70, 100, 80]


        s = sum(supply); d = sum(demand)
        if s != d:
            messagebox.showwarning("Przykład", "Suma podaży ≠ suma popytu – przykład jest przybliżony.")

        for i in range(3):
            self.supply_vars[i].set(str(supply[i]))
            for j in range(4):
                self.cost_vars[i][j].set(str(costs[i][j]))
        for j in range(4):
            self.demand_vars[j].set(str(demand[j]))

    # obliczenia

    def _solve(self):
        m = self.m_var.get()
        n = self.n_var.get()
        try:
            cost   = [[int(self.cost_vars[i][j].get()) for j in range(n)] for i in range(m)]
            supply = [int(self.supply_vars[i].get()) for i in range(m)]
            demand = [int(self.demand_vars[j].get()) for j in range(n)]
        except ValueError:
            messagebox.showerror("Błąd", "Wszystkie wartości muszą być liczbami całkowitymi.")
            return

        if any(s < 0 for s in supply) or any(d < 0 for d in demand):
            messagebox.showerror("Błąd", "Podaż i popyt muszą być nieujemne.")
            return

        if sum(supply) != sum(demand):
            messagebox.showwarning("Uwaga",
                f"Suma podaży ({sum(supply)}) ≠ suma popytu ({sum(demand)}).\n"
                "Obliczenia mogą być niekompletne.")

        allocation, iterations = solve_transport(supply, demand, cost, self.blocked_cells)
        tc = total_cost(allocation, cost)

        self._display_results(m, n, supply, demand, cost, allocation, iterations, tc)

    #  wyświetlanie wyników

    def _display_results(self, m, n, supply, demand, cost, allocation, iterations, tc):
        for w in self.result_inner.winfo_children():
            w.destroy()

        CLR_BG   = "#0f1117"
        CLR_HEAD = "#1e3a5f"
        CLR_ITER = "#161b22"
        CLR_FG   = "#e0f2f1"
        CLR_ACC  = "#00e5ff"

        def section(parent, title):
            f = tk.Frame(parent, bg=CLR_BG)
            f.pack(fill="x", pady=(10,2), padx=4)
            tk.Label(f, text=title, font=self.ft_header,
                     bg=CLR_BG, fg="#80cbc4").pack(anchor="w")
            sep = tk.Frame(f, bg="#263238", height=1)
            sep.pack(fill="x")
            return f

        section(self.result_inner, f"► Iteracje ({len(iterations)} kroków)")

        for it in iterations:
            step = it["step"]
            i, j = it["i"], it["j"]
            qty  = it["qty"]
            c    = it["cost"]

            frm = tk.Frame(self.result_inner, bg=CLR_ITER,
                           relief="flat", bd=0, padx=8, pady=6)
            frm.pack(fill="x", padx=4, pady=2)

            title_str = (f"Krok {step}:  wybrano D{i+1}→O{j+1}  "
                         f"(koszt={c},  przydział={qty})")
            tk.Label(frm, text=title_str, font=self.ft_label,
                     bg=CLR_ITER, fg=CLR_ACC).pack(anchor="w")

            tbl = tk.Frame(frm, bg=CLR_ITER)
            tbl.pack(anchor="w", pady=(4,0))

            alloc = it["allocation"]
            # nagłówki kolumn
            tk.Label(tbl, text="", width=4, bg="#263238", fg=CLR_FG,
                     font=self.ft_small, relief="flat").grid(row=0, column=0)
            for jj in range(n):
                tk.Label(tbl, text=f"O{jj+1}", width=6,
                         bg="#263238", fg="#80cbc4",
                         font=self.ft_small, relief="flat").grid(row=0, column=jj+1)
            tk.Label(tbl, text="Poz.", width=6,
                     bg="#263238", fg="#ffcc80",
                     font=self.ft_small, relief="flat").grid(row=0, column=n+1)

            for ii in range(m):
                tk.Label(tbl, text=f"D{ii+1}", width=4,
                         bg="#263238", fg="#80cbc4",
                         font=self.ft_small, relief="flat").grid(row=ii+1, column=0)
                for jj in range(n):
                    val = alloc[ii][jj]
                    is_cur = (ii==i and jj==j)
                    bg = "#0d3b2e" if is_cur else "#1c2733"
                    fg = "#69f0ae" if (is_cur and val>0) else ("#a5d6a7" if val>0 else "#37474f")
                    tk.Label(tbl, text=str(val) if val>0 else "–",
                             width=6, bg=bg, fg=fg,
                             font=self.ft_small, relief="flat").grid(row=ii+1, column=jj+1)
                rem_s = it["supply_rem"][ii]
                tk.Label(tbl, text=str(rem_s), width=6,
                         bg=CLR_ITER, fg="#a5d6a7",
                         font=self.ft_small).grid(row=ii+1, column=n+1)

            # Pozostały popyt
            rem_row = tk.Frame(frm, bg=CLR_ITER)
            rem_row.pack(anchor="w")
            tk.Label(rem_row, text="Poz. popyt:", font=self.ft_small,
                     bg=CLR_ITER, fg="#ffcc80").pack(side="left")
            for jj in range(n):
                tk.Label(rem_row, text=f" O{jj+1}:{it['demand_rem'][jj]}",
                         font=self.ft_small, bg=CLR_ITER, fg="#ce93d8").pack(side="left")

        #  Końcowa macierz alokacji
        section(self.result_inner, "► Końcowa macierz alokacji")

        tbl_f = tk.Frame(self.result_inner, bg="#161b22", padx=8, pady=8)
        tbl_f.pack(fill="x", padx=4, pady=2)

        tk.Label(tbl_f, text="", width=4, bg="#263238", fg=CLR_FG,
                 font=self.ft_small, relief="flat").grid(row=0, column=0)
        for j in range(n):
            tk.Label(tbl_f, text=f"O{j+1}", width=8,
                     bg="#263238", fg="#80cbc4",
                     font=self.ft_header, relief="flat").grid(row=0, column=j+1)
        tk.Label(tbl_f, text="Podaż", width=7,
                 bg="#263238", fg="#ffcc80",
                 font=self.ft_header, relief="flat").grid(row=0, column=n+1)

        for i in range(m):
            tk.Label(tbl_f, text=f"D{i+1}", width=4,
                     bg="#263238", fg="#80cbc4",
                     font=self.ft_header, relief="flat").grid(row=i+1, column=0)
            for j in range(n):
                val = allocation[i][j]
                blk = (i,j) in self.blocked_cells
                bg  = "#3b1010" if blk else ("#0d3b2e" if val>0 else "#1c2733")
                fg  = "#ef9a9a" if blk else ("#69f0ae"  if val>0 else "#37474f")
                c   = cost[i][j]
                txt = f"{val}\n[c={c}]" if val>0 else f"–\n[c={c}]"
                tk.Label(tbl_f, text=txt, width=8,
                         bg=bg, fg=fg, font=self.ft_small,
                         relief="flat", justify="center").grid(row=i+1, column=j+1, padx=1, pady=1)
            tk.Label(tbl_f, text=str(supply[i]), width=7,
                     bg="#161b22", fg="#a5d6a7",
                     font=self.ft_small).grid(row=i+1, column=n+1)

        tk.Label(tbl_f, text="Popyt", width=4,
                 bg="#263238", fg="#ffcc80",
                 font=self.ft_header, relief="flat").grid(row=m+1, column=0)
        for j in range(n):
            tk.Label(tbl_f, text=str(demand[j]), width=8,
                     bg="#161b22", fg="#ce93d8",
                     font=self.ft_small).grid(row=m+1, column=j+1)

        #  Koszt całkowity
        section(self.result_inner, "► Koszt całkowity")
        cost_frame = tk.Frame(self.result_inner, bg="#0d2137", padx=12, pady=10)
        cost_frame.pack(fill="x", padx=4, pady=2)

        detail_parts = []
        for i in range(m):
            for j in range(n):
                if allocation[i][j] > 0:
                    detail_parts.append(
                        f"D{i+1}→O{j+1}: {allocation[i][j]}×{cost[i][j]}={allocation[i][j]*cost[i][j]}"
                    )
        tk.Label(cost_frame, text="  +  ".join(detail_parts),
                 font=self.ft_small, bg="#0d2137", fg="#90caf9",
                 wraplength=500, justify="left").pack(anchor="w")
        tk.Label(cost_frame,
                 text=f"ŁĄCZNY KOSZT  =  {tc}",
                 font=font.Font(family="Courier New", size=14, weight="bold"),
                 bg="#0d2137", fg="#00e5ff").pack(anchor="w", pady=(6,0))

        self.result_canvas.update_idletasks()
        self.result_canvas.configure(
            scrollregion=self.result_canvas.bbox("all"))


if __name__ == "__main__":
    app = TransportApp()
    app.geometry("1200x750")
    app.mainloop()