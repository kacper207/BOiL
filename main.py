import tkinter as tk
from tkinter import ttk, messagebox, font
import copy

BIG_M = 10**9


def solve_transport_full(supply, demand, cost_orig, blocked):
    m, n = len(supply), len(demand)
    cost = [[(-BIG_M if (i, j) in blocked else cost_orig[i][j]) for j in range(n)] for i in range(m)]
    supply_rem, demand_rem = list(supply), list(demand)
    allocation = [[0]*n for _ in range(m)]
    done_rows, done_cols = [False]*m, [False]*n
    iterations, step = [], 0

    while True:
        best_val, bi, bj = -float('inf'), -1, -1
        for i in range(m):
            if done_rows[i]: continue
            for j in range(n):
                if done_cols[j]: continue
                if cost[i][j] > best_val:
                    best_val, bi, bj = cost[i][j], i, j
        if bi == -1: break

        qty = min(supply_rem[bi], demand_rem[bj])
        allocation[bi][bj] += qty
        supply_rem[bi] -= qty
        demand_rem[bj] -= qty
        step += 1
        iterations.append({"step": step, "i": bi, "j": bj, "cost": cost[bi][bj],
                            "qty": qty, "supply_rem": list(supply_rem),
                            "demand_rem": list(demand_rem),
                            "allocation": copy.deepcopy(allocation)})
        if supply_rem[bi] == 0: done_rows[bi] = True
        if demand_rem[bj] == 0: done_cols[bj] = True
        if all(done_rows) or all(done_cols): break

    return allocation, iterations, cost


def compute_dual(allocation, cost, m, n, blocked):
    alpha, beta = [None]*m, [None]*n
    alpha[0] = 0
    changed = True
    while changed:
        changed = False
        for i in range(m):
            for j in range(n):
                if allocation[i][j] > 0 and (i, j) not in blocked:
                    if alpha[i] is not None and beta[j] is None:
                        beta[j] = cost[i][j] - alpha[i]; changed = True
                    elif beta[j] is not None and alpha[i] is None:
                        alpha[i] = cost[i][j] - beta[j]; changed = True
    return [a or 0 for a in alpha], [b or 0 for b in beta]


def compute_delta(allocation, cost, alpha, beta, m, n, blocked):
    return [[None if (allocation[i][j] > 0 or (i,j) in blocked)
             else cost[i][j] - alpha[i] - beta[j]
             for j in range(n)] for i in range(m)]


def find_loop(allocation, pi, pj, m, n, blocked):
    basis = {(i,j) for i in range(m) for j in range(n)
             if allocation[i][j] > 0 and (i,j) not in blocked}
    basis.add((pi, pj))

    def dfs(path, direction):
        ci, cj = path[-1]
        if len(path) > 3 and ci == pi and cj == pj:
            return path
        nxt = [(ni,nj) for ni,nj in basis if (ni,nj) not in path[1:]
               and (ni == ci if direction == 'row' else nj == cj)
               and (nj != cj if direction == 'row' else ni != ci)]
        for cell in nxt:
            r = dfs(path + [cell], 'col' if direction == 'row' else 'row')
            if r: return r
        return None

    return dfs([(pi, pj)], 'row') or dfs([(pi, pj)], 'col')


def optimize_allocation(allocation, cost_orig, blocked, m, n):
    opt_iters = []
    cost = [[(-BIG_M if (i,j) in blocked else cost_orig[i][j]) for j in range(n)] for i in range(m)]

    for _ in range(100):
        alpha, beta = compute_dual(allocation, cost, m, n, blocked)
        delta = compute_delta(allocation, cost, alpha, beta, m, n, blocked)
        bi, bj, best = -1, -1, 0
        for i in range(m):
            for j in range(n):
                if delta[i][j] is not None and delta[i][j] > best:
                    best, bi, bj = delta[i][j], i, j

        opt_iters.append({"alpha": list(alpha), "beta": list(beta),
                          "delta": copy.deepcopy(delta),
                          "allocation": copy.deepcopy(allocation),
                          "pivot": (bi, bj) if bi != -1 else None,
                          "optimal": bi == -1})
        if bi == -1: break

        loop = find_loop(allocation, bi, bj, m, n, blocked)
        if not loop: break
        theta = min(allocation[i][j] for i,j in loop[1::2])
        for k, (i,j) in enumerate(loop):
            allocation[i][j] += theta if k%2==0 else -theta

    return allocation, opt_iters


def total_profit(allocation, cost):
    return sum(allocation[i][j]*cost[i][j]
               for i in range(len(allocation)) for j in range(len(allocation[0])))


C = {
    "bg":        "#0f1117",
    "panel":     "#161b22",
    "head":      "#263238",
    "cell":      "#1c2733",
    "fg":        "#e0f2f1",
    "acc":       "#00e5ff",
    "green":     "#a5d6a7",
    "green_bg":  "#0d3b2e",
    "red":       "#ef9a9a",
    "red_bg":    "#3b1010",
    "purple":    "#ce93d8",
    "yellow":    "#ffcc80",
    "blue":      "#90caf9",
    "muted":     "#546e7a",
    "white":     "#ffffff",
}

BTN_STYLES = {
    "primary":   {"bg": "#00838f",  "fg": "white",    "hover": "#00acc1"},
    "secondary": {"bg": "#1e3a5f",  "fg": C["blue"],  "hover": "#1a4a7f"},
    "warn":      {"bg": "#4e342e",  "fg": C["yellow"], "hover": "#6d4c41"},
    "danger":    {"bg": "#263238",  "fg": "#90a4ae",  "hover": "#37474f"},
    "compute":   {"bg": "#1a3a1a",  "fg": C["green"], "hover": "#2a5a2a"},
}


class FlatButton(tk.Label):
    def __init__(self, parent, text, style, cmd, ft=None, padx=12, pady=5):
        s = BTN_STYLES[style]
        super().__init__(parent, text=text, font=ft,
                         bg=s["bg"], fg=s["fg"],
                         padx=padx, pady=pady,
                         cursor="hand2", relief="flat")
        self._bg, self._hover, self._cmd = s["bg"], s["hover"], cmd
        self.bind("<Enter>",    lambda e: self.configure(bg=self._hover))
        self.bind("<Leave>",    lambda e: self.configure(bg=self._bg))
        self.bind("<Button-1>", lambda e: self._cmd())


class TransportApp(tk.Tk):
    MAX = 10

    def __init__(self):
        super().__init__()
        self.title("Zagadnienie Posrednika - Metoda Max. Elementu Macierzy")
        self.configure(bg=C["bg"])
        self.geometry("1500x950")
        self.resizable(True, True)

        self.ft = {
            "title":  font.Font(family="Courier New", size=20, weight="bold"),
            "label":  font.Font(family="Courier New", size=14),
            "small":  font.Font(family="Courier New", size=12),
            "header": font.Font(family="Courier New", size=13, weight="bold"),
            "big":    font.Font(family="Courier New", size=18, weight="bold"),
        }
        self.m_var = tk.IntVar(value=2)
        self.n_var = tk.IntVar(value=3)
        self.blocked_cells = set()
        self._build_ui()


    def _lbl(self, parent, text, ft="small", fg=None, bg=None, **kw):
        return tk.Label(parent, text=text, font=self.ft[ft],
                        bg=bg or C["bg"], fg=fg or C["fg"], **kw)

    def _btn(self, parent, text, style, cmd, ft="small", padx=12, pady=5):
        return FlatButton(parent, text=text, style=style, cmd=cmd,
                          ft=self.ft[ft], padx=padx, pady=pady)

    def _entry(self, parent, var, width=8, bg=C["cell"], fg=C["fg"]):
        return tk.Entry(parent, textvariable=var, width=width,
                        bg=bg, fg=fg, insertbackground=fg,
                        relief="flat", font=self.ft["label"], justify="center")

    def _section(self, parent, title):
        f = tk.Frame(parent, bg=C["bg"])
        f.pack(fill="x", pady=(15,4), padx=4)
        self._lbl(f, title, ft="header", fg="#80cbc4", bg=C["bg"]).pack(anchor="w")
        tk.Frame(f, bg=C["head"], height=2).pack(fill="x", pady=2)
        return f

    def _table_header(self, parent, n, row=0, col_offset=1,
                      label_w=7, head_bg=None, head_fg="#80cbc4"):
        hbg = head_bg or C["head"]
        self._lbl(parent, "", bg=hbg, fg=C["fg"], width=5).grid(row=row, column=0)
        for j in range(n):
            self._lbl(parent, f"O{j+1}", bg=hbg, fg=head_fg,
                      ft="header", width=label_w).grid(row=row, column=j+col_offset, padx=1, pady=1)


    def _build_ui(self):
        hdr = tk.Frame(self, bg=C["bg"])
        hdr.pack(fill="x", padx=20, pady=(16,4))
        self._lbl(hdr, "ZAGADNIENIE  POSREDNIKA", ft="title", fg=C["acc"], bg=C["bg"]).pack(side="left")
        self._lbl(hdr, "metoda max. elementu macierzy", ft="label", fg=C["muted"], bg=C["bg"]).pack(side="left", padx=20)

        size_bar = tk.Frame(self, bg=C["panel"], pady=12)
        size_bar.pack(fill="x", padx=20, pady=8)
        for text, var in [("Dostawcy (m):", self.m_var), ("  Odbiorcy (n):", self.n_var)]:
            self._lbl(size_bar, text, ft="label", fg="#cfd8dc", bg=C["panel"]).pack(side="left", padx=8)
            ttk.Spinbox(size_bar, from_=1, to=self.MAX, textvariable=var, width=5,
                        font=self.ft["label"], command=self._rebuild_matrix).pack(side="left")
        self._btn(size_bar, "Zastosuj rozmiar", "secondary", self._rebuild_matrix, padx=10).pack(side="left", padx=14)

        main = tk.Frame(self, bg=C["bg"])
        main.pack(fill="both", expand=True, padx=20, pady=6)

        left_canvas = tk.Canvas(main, bg=C["bg"], highlightthickness=0, width=570)
        left_scroll = ttk.Scrollbar(main, orient="vertical", command=left_canvas.yview)
        left_canvas.configure(yscrollcommand=left_scroll.set)
        left_scroll.pack(side="left", fill="y")
        left_canvas.pack(side="left", fill="y", expand=False)
        self.left_inner = tk.Frame(left_canvas, bg=C["bg"])
        left_canvas.create_window((0,0), window=self.left_inner, anchor="nw")
        self.left_inner.bind("<Configure>",
            lambda e: left_canvas.configure(scrollregion=left_canvas.bbox("all")))

        right = tk.Frame(main, bg=C["bg"])
        right.pack(side="left", fill="both", expand=True, padx=(15,0))
        self.result_canvas = tk.Canvas(right, bg=C["bg"], highlightthickness=0)
        result_scroll = ttk.Scrollbar(right, orient="vertical", command=self.result_canvas.yview)
        self.result_canvas.configure(yscrollcommand=result_scroll.set)
        result_scroll.pack(side="right", fill="y")
        self.result_canvas.pack(side="left", fill="both", expand=True)
        self.result_inner = tk.Frame(self.result_canvas, bg=C["bg"])
        self.rc_win = self.result_canvas.create_window((0,0), window=self.result_inner, anchor="nw")
        self.result_inner.bind("<Configure>",
            lambda e: self.result_canvas.configure(scrollregion=self.result_canvas.bbox("all")))
        self.result_canvas.bind("<Configure>",
            lambda e: self.result_canvas.itemconfig(self.rc_win, width=e.width))

        left = self.left_inner
        self._lbl(left, "Dane wejsciowe", ft="header", fg="#80cbc4", bg=C["bg"]).pack(anchor="w")

        kz_f = tk.Frame(left, bg=C["panel"], padx=15, pady=10)
        kz_f.pack(fill="x", pady=(8,2))
        self._lbl(kz_f, "Jednostkowe koszty zakupu u dostawcow (Kz_i)",
                  ft="header", fg=C["yellow"], bg=C["panel"]).pack(anchor="w", pady=(0,6))
        self.kz_frame_inner = tk.Frame(kz_f, bg=C["panel"])
        self.kz_frame_inner.pack(anchor="w")

        cs_f = tk.Frame(left, bg=C["panel"], padx=15, pady=10)
        cs_f.pack(fill="x", pady=(2,2))
        self._lbl(cs_f, "Jednostkowe ceny sprzedazy u odbiorcow (Cs_j)",
                  ft="header", fg=C["purple"], bg=C["panel"]).pack(anchor="w", pady=(0,6))
        self.cs_frame_inner = tk.Frame(cs_f, bg=C["panel"])
        self.cs_frame_inner.pack(anchor="w")

        kt_lf = tk.Frame(left, bg=C["bg"])
        kt_lf.pack(fill="x", pady=(10,0))
        self._lbl(kt_lf, "Macierz kosztow transportu (Kt_ij)",
                  ft="header", fg="#80cbc4", bg=C["bg"]).pack(anchor="w")
        self._lbl(kt_lf, "(PPM lub dwuklik = zablokuj/odblokuj trase)",
                  fg=C["muted"], bg=C["bg"]).pack(anchor="w")
        self.transport_frame = tk.Frame(left, bg=C["panel"], padx=15, pady=15)
        self.transport_frame.pack(fill="x", pady=4)

        self._btn(left, "Oblicz zyski jednostkowe  Zij = Csj - Ktij - Kzi",
                  "compute", self._compute_unit_profits, pady=5).pack(anchor="w", pady=6)

        zij_lf = tk.Frame(left, bg=C["bg"])
        zij_lf.pack(fill="x")
        self._lbl(zij_lf, "Macierz zyskow jednostkowych (Zij)",
                  ft="header", fg="#80cbc4", bg=C["bg"]).pack(anchor="w")
        self._lbl(zij_lf, "(wypelnij recznie lub uzyj przycisku powyzej; PPM = zablokuj trase)",
                  fg=C["muted"], bg=C["bg"]).pack(anchor="w")
        self.matrix_frame = tk.Frame(left, bg=C["panel"], padx=15, pady=15)
        self.matrix_frame.pack(fill="x", pady=4)

        btn_f = tk.Frame(left, bg=C["bg"])
        btn_f.pack(fill="x", pady=10)
        self._btn(btn_f, "Zbilansuj (FD + FO)", "warn", self._add_fictitious,
                  padx=12, pady=6).pack(side="left", padx=4)
        self._btn(btn_f, "OBLICZ", "primary", self._solve,
                  ft="label", padx=16, pady=6).pack(side="left", padx=4)
        self._btn(btn_f, "Reset", "danger", self._reset,
                  padx=10, pady=4).pack(side="left", padx=4)

        self._lbl(left, "Zablokowane trasy:", fg=C["muted"], bg=C["bg"]).pack(anchor="w", pady=(12,0))
        self.blocked_label = self._lbl(left, "brak", fg=C["red"], bg=C["bg"])
        self.blocked_label.configure(wraplength=500, justify="left")
        self.blocked_label.pack(anchor="w")

        self._lbl(right, "Wyniki", ft="header", fg="#80cbc4", bg=C["bg"]).pack(anchor="w")
        self._rebuild_matrix()

    def _rebuild_matrix(self):
        for f in (self.matrix_frame, self.transport_frame,
                  self.kz_frame_inner, self.cs_frame_inner):
            for w in f.winfo_children(): w.destroy()
        self.blocked_cells.clear()
        self._update_blocked_label()

        m, n = self.m_var.get(), self.n_var.get()
        self.cost_vars      = [[tk.StringVar(value="0") for _ in range(n)] for _ in range(m)]
        self.transport_vars = [[tk.StringVar(value="0") for _ in range(n)] for _ in range(m)]
        self.supply_vars    = [tk.StringVar(value="0") for _ in range(m)]
        self.demand_vars    = [tk.StringVar(value="0") for _ in range(n)]
        self.kz_vars        = [tk.StringVar(value="0") for _ in range(m)]
        self.cs_vars        = [tk.StringVar(value="0") for _ in range(n)]
        self.cost_entries      = []
        self.transport_entries = []

        for i in range(m):
            self._lbl(self.kz_frame_inner, f"D{i+1}:", bg=C["panel"], fg=C["yellow"], width=4
                      ).grid(row=0, column=i*2, padx=(0,2))
            self._entry(self.kz_frame_inner, self.kz_vars[i], width=6,
                        bg="#2a2010", fg=C["yellow"]
                        ).grid(row=0, column=i*2+1, padx=(0,10), ipady=3)

        for j in range(n):
            self._lbl(self.cs_frame_inner, f"O{j+1}:", bg=C["panel"], fg=C["purple"], width=4
                      ).grid(row=0, column=j*2, padx=(0,2))
            self._entry(self.cs_frame_inner, self.cs_vars[j], width=6,
                        bg="#1a1230", fg=C["purple"]
                        ).grid(row=0, column=j*2+1, padx=(0,10), ipady=3)

        self._table_header(self.transport_frame, n)
        tr_entries = []
        for i in range(m):
            self._lbl(self.transport_frame, f"D{i+1}", bg=C["head"], fg="#80cbc4",
                      ft="header", width=5).grid(row=i+1, column=0, padx=2, pady=2)
            tr_row = []
            for j in range(n):
                e = self._entry(self.transport_frame, self.transport_vars[i][j],
                                bg="#1c2030", fg="#b0bcd4")
                e.grid(row=i+1, column=j+1, padx=2, pady=2, ipady=4)
                for seq in ("<Button-3>", "<Button-2>", "<Double-Button-1>"):
                    e.bind(seq, lambda ev, ii=i, jj=j: self._toggle_block(ii, jj))
                tr_row.append(e)
            tr_entries.append(tr_row)
        self.transport_entries = tr_entries

        self._table_header(self.matrix_frame, n)
        self._lbl(self.matrix_frame, "Podaz", bg=C["head"], fg=C["yellow"],
                  ft="header", width=9).grid(row=0, column=n+1, padx=2, pady=2)
        row_entries = []
        for i in range(m):
            self._lbl(self.matrix_frame, f"D{i+1}", bg=C["head"], fg="#80cbc4",
                      ft="header", width=5).grid(row=i+1, column=0, padx=2, pady=2)
            col_entries = []
            for j in range(n):
                e = self._entry(self.matrix_frame, self.cost_vars[i][j])
                e.grid(row=i+1, column=j+1, padx=2, pady=2, ipady=4)
                for seq in ("<Button-3>", "<Button-2>", "<Double-Button-1>"):
                    e.bind(seq, lambda ev, ii=i, jj=j: self._toggle_block(ii, jj))
                col_entries.append(e)
            row_entries.append(col_entries)
            self._entry(self.matrix_frame, self.supply_vars[i], width=9,
                        bg="#1a2a1a", fg=C["green"]
                        ).grid(row=i+1, column=n+1, padx=2, pady=2, ipady=4)
        self.cost_entries = row_entries

        self._lbl(self.matrix_frame, "Popyt", bg=C["head"], fg=C["yellow"],
                  ft="header", width=5).grid(row=m+1, column=0, padx=2, pady=2)
        for j in range(n):
            self._entry(self.matrix_frame, self.demand_vars[j],
                        bg="#1a1a2a", fg=C["purple"]
                        ).grid(row=m+1, column=j+1, padx=2, pady=2, ipady=4)

    def _toggle_block(self, i, j):
        if (i, j) in self.blocked_cells:
            self.blocked_cells.discard((i, j))
            if i < len(self.cost_entries):
                self.cost_entries[i][j].configure(bg=C["cell"], fg=C["fg"])
            if i < len(self.transport_entries):
                self.transport_entries[i][j].configure(bg="#1c2030", fg="#b0bcd4")
            if self.cost_vars[i][j].get() == "-M":
                self.cost_vars[i][j].set("0")
        else:
            self.blocked_cells.add((i, j))
            if i < len(self.cost_entries):
                self.cost_entries[i][j].configure(bg="#4a1010", fg=C["red"])
            if i < len(self.transport_entries):
                self.transport_entries[i][j].configure(bg="#4a1010", fg=C["red"])
            self.cost_vars[i][j].set("-M")
        self._update_blocked_label()

    def _update_blocked_label(self):
        self.blocked_label.configure(
            text="brak" if not self.blocked_cells
            else ", ".join(f"D{i+1}->O{j+1}" for i,j in sorted(self.blocked_cells)))

    def _safe_int(self, v, default=0):
        try: return int(v.strip() or default)
        except ValueError: return default

    def _get_kz_cs_kt(self, m, n):
        kz = [int(self.kz_vars[i].get()) for i in range(m)]
        cs = [int(self.cs_vars[j].get()) for j in range(n)]
        kt = [[int(self.transport_vars[i][j].get()) for j in range(n)] for i in range(m)]
        return kz, cs, kt

    def _compute_unit_profits(self):
        m, n = self.m_var.get(), self.n_var.get()
        try:
            kz, cs, kt = self._get_kz_cs_kt(m, n)
        except ValueError:
            messagebox.showerror("Blad", "Wartosci kosztow i cen musza byc liczbami calkowitymi.")
            return
        for i in range(m):
            for j in range(n):
                self.cost_vars[i][j].set(
                    "-M" if (i,j) in self.blocked_cells else str(cs[j]-kt[i][j]-kz[i]))
        messagebox.showinfo("Gotowe", "Zyski jednostkowe obliczone.\nZij = Csj - Ktij - Kzi")

    def _add_fictitious(self):
        m, n = self.m_var.get(), self.n_var.get()
        supply = [self._safe_int(self.supply_vars[i].get()) for i in range(m)]
        demand = [self._safe_int(self.demand_vars[j].get()) for j in range(n)]
        saved = {
            "costs":     [[self.cost_vars[i][j].get() for j in range(n)] for i in range(m)],
            "transport": [[self.transport_vars[i][j].get() for j in range(n)] for i in range(m)],
            "kz":        [self.kz_vars[i].get() for i in range(m)],
            "cs":        [self.cs_vars[j].get() for j in range(n)],
            "blocked":   list(self.blocked_cells),
        }
        self.m_var.set(m+1); self.n_var.set(n+1)
        self._rebuild_matrix()

        for i in range(m):
            self.supply_vars[i].set(str(supply[i]))
            self.kz_vars[i].set(saved["kz"][i])
            for j in range(n):
                self.cost_vars[i][j].set(saved["costs"][i][j])
                self.transport_vars[i][j].set(saved["transport"][i][j])
        for j in range(n):
            self.demand_vars[j].set(str(demand[j]))
            self.cs_vars[j].set(saved["cs"][j])

        self.demand_vars[n].set(str(sum(supply)))
        self.supply_vars[m].set(str(sum(demand)))
        self.kz_vars[m].set("0"); self.cs_vars[n].set("0")
        for i in range(m+1): self.cost_vars[i][n].set("0"); self.transport_vars[i][n].set("0")
        for j in range(n+1): self.cost_vars[m][j].set("0"); self.transport_vars[m][j].set("0")

        for (i,j) in saved["blocked"]:
            self.blocked_cells.add((i,j))
            self.cost_entries[i][j].configure(bg="#4a1010", fg=C["red"])
            self.transport_entries[i][j].configure(bg="#4a1010", fg=C["red"])
            self.cost_vars[i][j].set("-M")
        self._update_blocked_label()
        messagebox.showinfo("Zbilansowano",
            f"Dodano FD D{m+1} (podaz={sum(demand)}) i FO O{n+1} (popyt={sum(supply)}).")

    def _reset(self):
        self._rebuild_matrix()
        for w in self.result_inner.winfo_children(): w.destroy()

    def _solve(self):
        m, n = self.m_var.get(), self.n_var.get()
        try:
            cost = []
            for i in range(m):
                row = []
                for j in range(n):
                    v = self.cost_vars[i][j].get()
                    if v == "-M": self.blocked_cells.add((i,j)); row.append(0)
                    else: row.append(int(v))
                cost.append(row)
            supply = [int(self.supply_vars[i].get()) for i in range(m)]
            demand = [int(self.demand_vars[j].get()) for j in range(n)]
        except ValueError:
            messagebox.showerror("Blad", "Wartosci musza byc liczbami calkowitymi lub -M.")
            return

        try:
            kz, cs, kt = self._get_kz_cs_kt(m, n)
            has_kz_cs = True
        except ValueError:
            kz = [0]*m; cs = [0]*n; kt = [[0]*n for _ in range(m)]
            has_kz_cs = False

        if any(s < 0 for s in supply) or any(d < 0 for d in demand):
            messagebox.showerror("Blad", "Podaz i popyt musza byc nieujemne."); return
        if sum(supply) != sum(demand):
            messagebox.showwarning("Uwaga",
                f"Suma podazy ({sum(supply)}) != suma popytu ({sum(demand)}).\n"
                "Uzyj 'Zbilansuj' aby wyrownac.")

        allocation, iterations, _ = solve_transport_full(supply, demand, cost, self.blocked_cells)
        allocation, opt_iters = optimize_allocation(allocation, cost, self.blocked_cells, m, n)
        self._display_results(m, n, supply, demand, cost, allocation,
                              iterations, opt_iters, total_profit(allocation, cost),
                              kz, cs, kt, has_kz_cs)


    def _cell_label(self, parent, text, row, col, width=9, height=1,
                    bg=None, fg=None, ft="small"):
        tk.Label(parent, text=text, width=width, height=height,
                 bg=bg or C["cell"], fg=fg or C["fg"],
                 font=self.ft[ft], relief="flat", justify="center"
                 ).grid(row=row, column=col, padx=1, pady=1)

    def _draw_alloc_table(self, parent, m, n, alloc, highlight_ij=None,
                          supply_rem=None, demand_rem=None):
        self._table_header(parent, n, label_w=7)
        if supply_rem is not None:
            self._lbl(parent, "Poz.", bg=C["head"], fg=C["yellow"],
                      ft="small", width=7).grid(row=0, column=n+1, padx=1, pady=1)
        for i in range(m):
            self._lbl(parent, f"D{i+1}", bg=C["head"], fg="#80cbc4",
                      ft="small", width=5).grid(row=i+1, column=0, padx=1, pady=1)
            for j in range(n):
                val = alloc[i][j]
                blk = (i,j) in self.blocked_cells
                cur = highlight_ij == (i,j)
                bg = C["red_bg"] if blk else (C["green_bg"] if cur else C["cell"])
                fg = (C["red"] if blk
                      else ("#69f0ae" if (cur and val > 0) else
                            (C["green"] if val > 0 else "#37474f")))
                txt = "-M" if blk else (str(val) if val > 0 else "-")
                self._cell_label(parent, txt, i+1, j+1, width=7, bg=bg, fg=fg)
            if supply_rem is not None:
                self._lbl(parent, str(supply_rem[i]), bg=C["panel"],
                          fg=C["green"], ft="small").grid(row=i+1, column=n+1, padx=1, pady=1)

    def _display_results(self, m, n, supply, demand, cost, allocation,
                         iterations, opt_iters, tc, kz, cs, kt, has_kz_cs):
        for w in self.result_inner.winfo_children(): w.destroy()

        if has_kz_cs:
            self._section(self.result_inner, "Macierz zyskow jednostkowych (Zij = Csj - Ktij - Kzi)")
            frm = tk.Frame(self.result_inner, bg=C["panel"], padx=12, pady=12)
            frm.pack(fill="x", padx=4, pady=2)
            self._table_header(frm, n)
            self._lbl(frm, "Kzi", bg="#2a2010", fg=C["yellow"],
                      ft="header", width=8).grid(row=0, column=n+1, padx=1, pady=1)
            for i in range(m):
                self._lbl(frm, f"D{i+1}", bg=C["head"], fg="#80cbc4",
                          ft="header", width=5).grid(row=i+1, column=0)
                for j in range(n):
                    blk = (i,j) in self.blocked_cells
                    if blk:
                        txt, bg, fg = "-M", C["red_bg"], C["red"]
                    else:
                        v = cs[j]-kt[i][j]-kz[i]
                        txt = str(v)
                        bg = "#1a2a1a" if v>0 else ("#2a1a1a" if v<0 else C["cell"])
                        fg = C["green"] if v>0 else (C["red"] if v<0 else "#78909c")
                    self._cell_label(frm, txt, i+1, j+1, bg=bg, fg=fg)
                self._lbl(frm, str(kz[i]), bg="#2a2010", fg=C["yellow"],
                          ft="label").grid(row=i+1, column=n+1, padx=1, pady=1)
            self._lbl(frm, "Csj", bg="#1a1230", fg=C["purple"],
                      ft="header", width=5).grid(row=m+1, column=0, pady=4)
            for j in range(n):
                self._lbl(frm, str(cs[j]), bg="#1a1230", fg=C["purple"],
                          ft="label", width=9).grid(row=m+1, column=j+1, pady=4)

        self._section(self.result_inner, f"Wyznaczanie pierwszego planu ({len(iterations)} krokow)")
        for it in iterations:
            i, j = it["i"], it["j"]
            c_disp = "-M" if it["cost"] <= -BIG_M/2 else it["cost"]
            frm = tk.Frame(self.result_inner, bg=C["panel"], padx=10, pady=10)
            frm.pack(fill="x", padx=4, pady=4)
            self._lbl(frm, f"Krok {it['step']}:  D{i+1}->O{j+1}  (zysk={c_disp}, przydzial={it['qty']})",
                      ft="header", fg=C["acc"], bg=C["panel"]).pack(anchor="w")
            tbl = tk.Frame(frm, bg=C["panel"])
            tbl.pack(anchor="w", pady=(8,0))
            self._draw_alloc_table(tbl, m, n, it["allocation"],
                                   highlight_ij=(i,j), supply_rem=it["supply_rem"])
            rem = tk.Frame(frm, bg=C["panel"])
            rem.pack(anchor="w", pady=(8,0))
            self._lbl(rem, "Poz. popyt:", fg=C["yellow"], bg=C["panel"]).pack(side="left", padx=(0,10))
            for jj in range(n):
                self._lbl(rem, f" O{jj+1}:{it['demand_rem'][jj]}", fg=C["purple"],
                          bg=C["panel"]).pack(side="left", padx=4)

        self._section(self.result_inner, "Sprawdzenie optymalnosci (zmienne dualne i kryterialne)")
        for idx, oit in enumerate(opt_iters):
            alpha, beta, delta = oit["alpha"], oit["beta"], oit["delta"]
            alloc, pivot, is_opt = oit["allocation"], oit["pivot"], oit["optimal"]
            frm = tk.Frame(self.result_inner, bg=C["panel"], padx=10, pady=10)
            frm.pack(fill="x", padx=4, pady=4)
            label_txt = (f"Iteracja {idx+1}:  "
                         + ("Plan optymalny" if is_opt
                            else f"Wezel centralny: D{pivot[0]+1}->O{pivot[1]+1}"))
            self._lbl(frm, label_txt, ft="header",
                      fg="#69f0ae" if is_opt else C["acc"], bg=C["panel"]).pack(anchor="w")
            tbl = tk.Frame(frm, bg=C["panel"])
            tbl.pack(anchor="w", pady=(8,0))
            self._table_header(tbl, n)
            self._lbl(tbl, "ai", bg="#37474f", fg=C["white"],
                      ft="header", width=6).grid(row=0, column=n+1, padx=4)
            for i in range(m):
                self._lbl(tbl, f"D{i+1}", bg=C["head"], fg="#80cbc4",
                          ft="small", width=5).grid(row=i+1, column=0, padx=1, pady=1)
                for j in range(n):
                    val = alloc[i][j]
                    blk = (i,j) in self.blocked_cells
                    d_val = delta[i][j]
                    is_piv = pivot is not None and (i,j) == pivot
                    if blk:
                        txt, bg, fg = "-\n[-M]", C["red_bg"], C["red"]
                    elif val > 0:
                        txt, bg, fg = f"{val}\n[baz.]", C["green_bg"], "#69f0ae"
                    else:
                        d_str = f"{d_val:+}" if d_val is not None else "?"
                        txt = f"-\n[D={d_str}]"
                        bg = "#1e2a1e" if is_piv else C["cell"]
                        fg = "#ff8a65" if (d_val is not None and d_val > 0) else "#78909c"
                    self._cell_label(tbl, txt, i+1, j+1, height=2, bg=bg, fg=fg)
                self._lbl(tbl, str(alpha[i]), bg=C["head"], fg=C["white"],
                          ft="header", width=6).grid(row=i+1, column=n+1, padx=4)
            self._lbl(tbl, "bj", bg="#37474f", fg=C["white"],
                      ft="header", width=5).grid(row=m+1, column=0, pady=4)
            for j in range(n):
                self._lbl(tbl, str(beta[j]), bg=C["head"], fg=C["white"],
                          ft="header", width=9).grid(row=m+1, column=j+1, pady=4)
            if not is_opt and pivot:
                self._lbl(frm,
                    f"Delta D{pivot[0]+1}->O{pivot[1]+1} = {delta[pivot[0]][pivot[1]]:+} > 0"
                    "  ->  wyznaczam petle prostokatna i przesuwam przydzial",
                    fg=C["yellow"], bg=C["panel"]).pack(anchor="w", pady=(6,0))

        self._section(self.result_inner, "Koncowa macierz alokacji")
        alpha, beta = compute_dual(allocation, cost, m, n, self.blocked_cells)
        tbl_f = tk.Frame(self.result_inner, bg=C["panel"], padx=12, pady=12)
        tbl_f.pack(fill="x", padx=4, pady=2)
        self._table_header(tbl_f, n)
        for txt, col, fg in [("Podaz", n+1, C["yellow"]), ("ai", n+2, C["white"])]:
            self._lbl(tbl_f, txt, bg=C["head"], fg=fg, ft="header", width=8
                      ).grid(row=0, column=col, padx=1, pady=1)
        for i in range(m):
            self._lbl(tbl_f, f"D{i+1}", bg=C["head"], fg="#80cbc4",
                      ft="header", width=5).grid(row=i+1, column=0, padx=1, pady=1)
            for j in range(n):
                val = allocation[i][j]
                blk = (i,j) in self.blocked_cells
                bg = C["red_bg"] if blk else (C["green_bg"] if val>0 else C["cell"])
                fg = C["red"] if blk else ("#69f0ae" if val>0 else "#37474f")
                c_disp = "-M" if blk else cost[i][j]
                txt = f"{val}\n[c={c_disp}]" if val>0 else f"-\n[c={c_disp}]"
                self._cell_label(tbl_f, txt, i+1, j+1, height=2, bg=bg, fg=fg)
            self._lbl(tbl_f, str(supply[i]), bg=C["panel"], fg=C["green"],
                      ft="label", width=8).grid(row=i+1, column=n+1, padx=1, pady=1)
            self._lbl(tbl_f, str(alpha[i]), bg=C["head"], fg=C["white"],
                      ft="header", width=7).grid(row=i+1, column=n+2, padx=4)
        self._lbl(tbl_f, "Popyt", bg=C["head"], fg=C["yellow"],
                  ft="header", width=5).grid(row=m+1, column=0, padx=1, pady=1)
        for j in range(n):
            self._lbl(tbl_f, str(demand[j]), bg=C["panel"], fg=C["purple"],
                      ft="label", width=9).grid(row=m+1, column=j+1, padx=1, pady=1)
        self._lbl(tbl_f, "bj", bg="#37474f", fg=C["white"],
                  ft="header", width=5).grid(row=m+2, column=0, pady=4)
        for j in range(n):
            self._lbl(tbl_f, str(beta[j]), bg=C["head"], fg=C["white"],
                      ft="header", width=9).grid(row=m+2, column=j+1, pady=4)

        self._lbl(self.result_inner,
            "-M - nie bierzemy jej pod uwage (nieskonczona strata)\n\n"
            "Zj = ai + bj\nai = Zj - bj\nbj = Zj - ai\nDeltaj = Zj - ai - bj",
            fg="#b0bec5", bg=C["bg"]).pack(anchor="w", padx=4, pady=15)

        self._section(self.result_inner, "Wynik calkowity")
        cost_frame = tk.Frame(self.result_inner, bg="#0d2137", padx=16, pady=16)
        cost_frame.pack(fill="x", padx=4, pady=2)
        parts = [f"D{i+1}->O{j+1}: {allocation[i][j]}x{cost[i][j]}={allocation[i][j]*cost[i][j]}"
                 for i in range(m) for j in range(n)
                 if allocation[i][j] > 0 and (i,j) not in self.blocked_cells]
        self._lbl(cost_frame, "  +  ".join(parts), fg=C["blue"], bg="#0d2137",
                  ).configure(wraplength=800, justify="left")
        self._lbl(cost_frame, "  +  ".join(parts), fg=C["blue"], bg="#0d2137").pack(anchor="w", pady=(0,8))
        tk.Label(cost_frame, text=f"LACZNY ZYSK  Zc  =  {tc}",
                 font=self.ft["big"], bg="#0d2137", fg=C["acc"]).pack(anchor="w")

        if has_kz_cs:
            tk.Frame(cost_frame, bg="#1a3050", height=2).pack(fill="x", pady=10)
            kcz = sum(allocation[i][j]*kz[i] for i in range(m) for j in range(n)
                      if allocation[i][j]>0 and (i,j) not in self.blocked_cells)
            kct = sum(allocation[i][j]*kt[i][j] for i in range(m) for j in range(n)
                      if allocation[i][j]>0 and (i,j) not in self.blocked_cells)
            przychod = sum(allocation[i][j]*cs[j] for i in range(m) for j in range(n)
                           if allocation[i][j]>0 and (i,j) not in self.blocked_cells)
            for label, val, fg in [
                ("Calkowity koszt zakupu (Kcz):",       kcz,             C["yellow"]),
                ("Calkowite koszty transportu (Kct):",  kct,             "#b0bcd4"),
                ("Calkowity przychod ze sprzedazy:",    przychod,        C["purple"]),
                ("Zysk = Przychod - Kct - Kcz:",        przychod-kct-kcz, C["green"]),
            ]:
                row_f = tk.Frame(cost_frame, bg="#0d2137")
                row_f.pack(anchor="w", pady=1)
                tk.Label(row_f, text=label, width=42, font=self.ft["small"],
                         bg="#0d2137", fg="#90a4ae", anchor="w").pack(side="left")
                tk.Label(row_f, text=str(val), font=self.ft["header"],
                         bg="#0d2137", fg=fg).pack(side="left", padx=8)

        self.result_canvas.update_idletasks()
        self.result_canvas.configure(scrollregion=self.result_canvas.bbox("all"))


if __name__ == "__main__":
    TransportApp().mainloop()
