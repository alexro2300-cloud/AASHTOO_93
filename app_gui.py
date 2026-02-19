import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from core.esals import calc_w18, calc_truck_factor_detailed
from core.aashto93_flexible import solve_sn_required
from core.layers import design_thicknesses_sequential, apply_minimums_sequential, DEFAULT_MINIMUMS_TABLE_IN
from data_io.project_json import save_project, load_project


def fnum(x, nd=3):
    try:
        return f"{float(x):.{nd}f}"
    except Exception:
        return str(x)


HELP_TEXTS = {
    "aadt": "TPDA (AADT): Tránsito Promedio Diario Anual total de vehículos.",
    "pct_trucks": "% Pesados: proporción de vehículos pesados respecto al TPDA total.",
    "dd": "DD (factor direccional): fracción del tránsito en la dirección de diseño.",
    "dl": "DL (factor de carril): fracción del tránsito direccional que usa carril de diseño.",
    "tf": "TF manual: ESAL por vehículo pesado promedio.",
    "ap": "Ap: factor de ajuste adicional para cada clase vehicular. Si no aplica, usar 1.0.",
}

VALIDATION_FIELDS = [
    ("aadt_min", "TPDA mínimo", "Límite inferior aceptado para TPDA total."),
    ("aadt_max", "TPDA máximo", "Límite superior aceptado para TPDA total."),
    ("pct_trucks_min", "% pesados mínimo", "Límite inferior del porcentaje de pesados."),
    ("pct_trucks_max", "% pesados máximo", "Límite superior del porcentaje de pesados."),
    ("dd_min", "DD mínimo", "Límite inferior del factor direccional DD."),
    ("dd_max", "DD máximo", "Límite superior del factor direccional DD."),
    ("dl_min", "DL mínimo", "Límite inferior del factor de carril DL."),
    ("dl_max", "DL máximo", "Límite superior del factor de carril DL."),
    ("growth_min", "Crecimiento mínimo (%)", "Límite inferior de crecimiento anual."),
    ("growth_max", "Crecimiento máximo (%)", "Límite superior de crecimiento anual."),
    ("mr_min", "Mr mínimo (MPa)", "Límite inferior para Mr."),
    ("mr_max", "Mr máximo (MPa)", "Límite superior para Mr."),
    ("r_min", "R mínima (%)", "Límite inferior de confiabilidad."),
    ("r_max", "R máxima (%)", "Límite superior de confiabilidad."),
]


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AASHTO 1993 Flexible - Diseñador de Pavimentos")
        self.root.geometry("1240x820")
        self.root.minsize(1100, 720)
        self.data = self.default_data()
        self._build_ui()

    def default_data(self):
        return {
            "project": {"name": "Proyecto 01"},
            "traffic": {
                "aadt_total": 10000.0,
                "pct_trucks": 15.0,
                "dd": 0.50,
                "dl": 0.90,
                "truck_factor": 1.00,
                "growth_pct": 3.0,
                "design_years": 20,
                "use_detailed_tf": True,
                "truck_classes": [
                    {"name": "C2", "share_pct": 10.0, "ealf": 0.30, "ap": 1.0, "enabled": True},
                    {"name": "C3", "share_pct": 10.0, "ealf": 0.50, "ap": 1.0, "enabled": True},
                    {"name": "C2-R2", "share_pct": 10.0, "ealf": 0.80, "ap": 1.0, "enabled": True},
                    {"name": "C3-R2", "share_pct": 10.0, "ealf": 1.00, "ap": 1.0, "enabled": True},
                    {"name": "C2-R3", "share_pct": 10.0, "ealf": 1.10, "ap": 1.0, "enabled": True},
                    {"name": "C3-R3", "share_pct": 10.0, "ealf": 1.30, "ap": 1.0, "enabled": True},
                    {"name": "T2-S1", "share_pct": 10.0, "ealf": 1.40, "ap": 1.0, "enabled": True},
                    {"name": "T2-S2", "share_pct": 10.0, "ealf": 1.60, "ap": 1.0, "enabled": True},
                    {"name": "T2-S3", "share_pct": 10.0, "ealf": 1.90, "ap": 1.0, "enabled": True},
                    {"name": "T3-S2", "share_pct": 5.0, "ealf": 2.10, "ap": 1.0, "enabled": True},
                    {"name": "T3-S3", "share_pct": 5.0, "ealf": 2.40, "ap": 1.0, "enabled": True},
                ],
            },
            "aashto": {"reliability_pct": 95.0, "so": 0.49, "pi": 4.2, "pt": 2.5, "mr_mpa": 70.0},
            "layers": {
                "a1": 0.44, "a2": 0.14, "a3": 0.11, "m2": 1.0, "m3": 1.0,
                "sn1_target": 1.8,
                "sn2_target": 3.2,
                "sn3_target": 4.5,
            },
            "validation": {
                "aadt_min": 100.0, "aadt_max": 200000.0,
                "pct_trucks_min": 0.0, "pct_trucks_max": 60.0,
                "dd_min": 0.3, "dd_max": 0.7,
                "dl_min": 0.5, "dl_max": 1.0,
                "growth_min": -2.0, "growth_max": 10.0,
                "mr_min": 20.0, "mr_max": 300.0,
                "r_min": 50.0, "r_max": 99.9,
            },
            "minimums_table": {k: v.copy() for k, v in DEFAULT_MINIMUMS_TABLE_IN.items()},
            "results": {},
        }

    def _build_ui(self):
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))

        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text="AASHTO 1993 Flexible Pavement Designer", style="Title.TLabel").pack(side="left")

        btns = ttk.Frame(top)
        btns.pack(side="right")
        for txt, cmd in [("Nuevo", self.on_new), ("Abrir", self.on_open), ("Guardar", self.on_save), ("Opciones", self.on_options), ("Calcular", self.on_calculate), ("PDF", self.on_export_pdf)]:
            ttk.Button(btns, text=txt, command=cmd).pack(side="left", padx=4)

        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill="both", expand=True, padx=10, pady=8)

        self.tab_traffic = ttk.Frame(self.nb, padding=12)
        self.tab_aashto = ttk.Frame(self.nb, padding=12)
        self.tab_layers = ttk.Frame(self.nb, padding=12)
        self.tab_results = ttk.Frame(self.nb, padding=12)
        self.tab_calculos = ttk.Frame(self.nb, padding=12)
        self.tab_section = ttk.Frame(self.nb, padding=12)

        self.nb.add(self.tab_traffic, text="Tránsito / ESALs")
        self.nb.add(self.tab_aashto, text="Parámetros AASHTO")
        self.nb.add(self.tab_layers, text="Capas / Espesores")
        self.nb.add(self.tab_results, text="Resultados")
        self.nb.add(self.tab_calculos, text="Cálculos")
        self.nb.add(self.tab_section, text="Sección de Pavimento")

        self._build_tab_traffic()
        self._build_tab_aashto()
        self._build_tab_layers()
        self._build_tab_results()
        self._build_tab_calculos()
        self._build_tab_section()
        self._load_to_form()

    def _entry_with_help(self, parent, row, label, key, unit="", col=0):
        ttk.Label(parent, text=label).grid(row=row, column=col, sticky="w", pady=3)
        v = tk.StringVar()
        ttk.Entry(parent, textvariable=v).grid(row=row, column=col + 1, sticky="ew", pady=3)
        ttk.Label(parent, text=unit).grid(row=row, column=col + 2, sticky="w", padx=(6, 2))
        ttk.Button(parent, text="?", width=3, command=lambda k=key: self.show_help(k)).grid(row=row, column=col + 3)
        return v

    def _build_tab_traffic(self):
        frm = ttk.LabelFrame(self.tab_traffic, text="Datos de tránsito", padding=12)
        frm.pack(fill="x")
        for c in range(8):
            frm.columnconfigure(c, weight=1 if c in (1, 5) else 0)
        self.v_aadt = self._entry_with_help(frm, 0, "TPDA total", "aadt", "veh/día")
        self.v_pct_trucks = self._entry_with_help(frm, 1, "% pesados", "pct_trucks", "%")
        self.v_dd = self._entry_with_help(frm, 2, "DD", "dd")
        self.v_dl = self._entry_with_help(frm, 3, "DL", "dl")
        self.v_tf = self._entry_with_help(frm, 4, "TF manual", "tf", "ESAL/veh pesado")
        self.v_growth = self._entry_with_help(frm, 5, "Crecimiento", "growth", "%")

        ttk.Label(frm, text="Años de diseño").grid(row=6, column=0, sticky="w")
        self.v_years = tk.StringVar()
        ttk.Entry(frm, textvariable=self.v_years).grid(row=6, column=1, sticky="ew")

        self.v_use_detailed = tk.BooleanVar()
        ttk.Checkbutton(frm, text="Usar TF detallado por tipo de vehículo", variable=self.v_use_detailed).grid(row=7, column=0, columnspan=4, sticky="w")

        cls = ttk.LabelFrame(self.tab_traffic, text="Clasificación vehicular (activar/desactivar por tipo)", padding=10)
        cls.pack(fill="both", expand=True, pady=(10, 0))
        headers = ["Usar", "Nomenclatura", "Participación %", "EALF", "Ap"]
        for i, h in enumerate(headers):
            ttk.Label(cls, text=h).grid(row=0, column=i, sticky="w")

        self.class_rows = []
        for i in range(11):
            en = tk.BooleanVar(value=True)
            name_v = tk.StringVar()
            share_v = tk.StringVar()
            ealf_v = tk.StringVar()
            ap_v = tk.StringVar(value="1.0")
            ttk.Checkbutton(cls, variable=en).grid(row=i + 1, column=0, sticky="w")
            ttk.Entry(cls, textvariable=name_v, width=12).grid(row=i + 1, column=1, sticky="ew", padx=2, pady=2)
            ttk.Entry(cls, textvariable=share_v, width=10).grid(row=i + 1, column=2, sticky="ew", padx=2, pady=2)
            ttk.Entry(cls, textvariable=ealf_v, width=10).grid(row=i + 1, column=3, sticky="ew", padx=2, pady=2)
            ttk.Entry(cls, textvariable=ap_v, width=8).grid(row=i + 1, column=4, sticky="ew", padx=2, pady=2)
            self.class_rows.append((en, name_v, share_v, ealf_v, ap_v))

    def _build_tab_aashto(self):
        frm = ttk.LabelFrame(self.tab_aashto, text="Parámetros de diseño", padding=12)
        frm.pack(fill="x")
        for c in range(8):
            frm.columnconfigure(c, weight=1 if c in (1, 5) else 0)
        self.v_rel = self._entry_with_help(frm, 0, "Confiabilidad R", "rel", "%")
        self.v_so = self._entry_with_help(frm, 1, "So", "so")
        self.v_pi = self._entry_with_help(frm, 2, "Pi", "pi")
        self.v_pt = self._entry_with_help(frm, 3, "Pt", "pt")
        self.v_mr = self._entry_with_help(frm, 4, "Mr", "mr", "MPa")

    def _build_tab_layers(self):
        frm = ttk.LabelFrame(self.tab_layers, text="Coeficientes y SN por nivel", padding=12)
        frm.pack(fill="x")
        for c in range(8):
            frm.columnconfigure(c, weight=1 if c in (1, 5) else 0)
        self.v_a1 = tk.StringVar(); self.v_a2 = tk.StringVar(); self.v_a3 = tk.StringVar(); self.v_m2 = tk.StringVar(); self.v_m3 = tk.StringVar()
        self.v_sn1 = tk.StringVar(); self.v_sn2 = tk.StringVar(); self.v_sn3 = tk.StringVar()

        def er(r, t, v, u=""):
            ttk.Label(frm, text=t).grid(row=r, column=0, sticky="w", pady=3)
            ttk.Entry(frm, textvariable=v).grid(row=r, column=1, sticky="ew", pady=3)
            ttk.Label(frm, text=u).grid(row=r, column=2, sticky="w")

        er(0, "a1", self.v_a1)
        er(1, "a2", self.v_a2)
        er(2, "a3", self.v_a3)
        er(3, "m2", self.v_m2)
        er(4, "m3", self.v_m3)
        er(5, "SN1 objetivo", self.v_sn1)
        er(6, "SN2 objetivo", self.v_sn2)
        er(7, "SN3 objetivo", self.v_sn3)

        ttk.Label(self.tab_layers, text="SN1, SN2 y SN3 objetivo son ingresados por el usuario para el método secuencial.", foreground="#444").pack(anchor="w", pady=(8, 0))

    def _build_tab_results(self):
        self.txt = tk.Text(self.tab_results, height=30, wrap="word")
        self.txt.pack(fill="both", expand=True)
        self.txt.configure(state="disabled")

    def _build_tab_calculos(self):
        self.txt_calc = tk.Text(self.tab_calculos, height=30, wrap="word")
        self.txt_calc.pack(fill="both", expand=True)
        self.txt_calc.configure(state="disabled")

    def _build_tab_section(self):
        holder = ttk.Frame(self.tab_section)
        holder.pack(fill="both", expand=True)
        holder.columnconfigure(0, weight=1)
        holder.columnconfigure(1, weight=1)
        ttk.Label(holder, text="Espesores calculados").grid(row=0, column=0)
        ttk.Label(holder, text="Espesores con mínimos sugeridos").grid(row=0, column=1)
        self.canvas_calc = tk.Canvas(holder, width=500, height=520, bg="white")
        self.canvas_min = tk.Canvas(holder, width=500, height=520, bg="white")
        self.canvas_calc.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
        self.canvas_min.grid(row=1, column=1, sticky="nsew", padx=6, pady=6)

    def _load_to_form(self):
        t = self.data["traffic"]; a = self.data["aashto"]; l = self.data["layers"]
        self.v_aadt.set(str(t["aadt_total"])); self.v_pct_trucks.set(str(t["pct_trucks"])); self.v_dd.set(str(t["dd"])); self.v_dl.set(str(t["dl"]))
        self.v_tf.set(str(t["truck_factor"])); self.v_growth.set(str(t["growth_pct"])); self.v_years.set(str(t["design_years"])); self.v_use_detailed.set(bool(t.get("use_detailed_tf", False)))
        for idx, row in enumerate(t.get("truck_classes", [])):
            if idx < len(self.class_rows):
                en, n, s_v, e, ap = self.class_rows[idx]
                en.set(bool(row.get("enabled", True))); n.set(str(row.get("name", ""))); s_v.set(str(row.get("share_pct", ""))); e.set(str(row.get("ealf", ""))); ap.set(str(row.get("ap", 1.0)))
        self.v_rel.set(str(a["reliability_pct"])); self.v_so.set(str(a["so"])); self.v_pi.set(str(a["pi"])); self.v_pt.set(str(a["pt"])); self.v_mr.set(str(a["mr_mpa"]))
        self.v_a1.set(str(l["a1"])); self.v_a2.set(str(l["a2"])); self.v_a3.set(str(l["a3"])); self.v_m2.set(str(l["m2"])); self.v_m3.set(str(l["m3"])); self.v_sn1.set(str(l["sn1_target"])); self.v_sn2.set(str(l["sn2_target"])); self.v_sn3.set(str(l["sn3_target"]))

    def _read_form_to_data(self):
        t = self.data["traffic"]; a = self.data["aashto"]; l = self.data["layers"]
        t["aadt_total"] = float(self.v_aadt.get()); t["pct_trucks"] = float(self.v_pct_trucks.get()); t["dd"] = float(self.v_dd.get()); t["dl"] = float(self.v_dl.get())
        t["truck_factor"] = float(self.v_tf.get()); t["growth_pct"] = float(self.v_growth.get()); t["design_years"] = int(float(self.v_years.get())); t["use_detailed_tf"] = bool(self.v_use_detailed.get())
        classes = []
        for en, n, s_v, e, ap in self.class_rows:
            if n.get().strip() or s_v.get().strip() or e.get().strip():
                classes.append({"enabled": bool(en.get()), "name": n.get().strip() or "Clase", "share_pct": float(s_v.get() or 0), "ealf": float(e.get() or 0), "ap": float(ap.get() or 1)})
        t["truck_classes"] = classes
        a["reliability_pct"] = float(self.v_rel.get()); a["so"] = float(self.v_so.get()); a["pi"] = float(self.v_pi.get()); a["pt"] = float(self.v_pt.get()); a["mr_mpa"] = float(self.v_mr.get())
        l["a1"] = float(self.v_a1.get()); l["a2"] = float(self.v_a2.get()); l["a3"] = float(self.v_a3.get()); l["m2"] = float(self.v_m2.get()); l["m3"] = float(self.v_m3.get())
        l["sn1_target"] = float(self.v_sn1.get()); l["sn2_target"] = float(self.v_sn2.get()); l["sn3_target"] = float(self.v_sn3.get())
        self._validate_ranges()

    def _validate_ranges(self):
        t = self.data["traffic"]; a = self.data["aashto"]; v = self.data["validation"]
        checks = [
            ("TPDA", t["aadt_total"], v["aadt_min"], v["aadt_max"], "Ajusta TPDA o cambia rango en Opciones."),
            ("% pesados", t["pct_trucks"], v["pct_trucks_min"], v["pct_trucks_max"], "Verifica clasificación vehicular."),
            ("DD", t["dd"], v["dd_min"], v["dd_max"], "Revisa factor direccional."),
            ("DL", t["dl"], v["dl_min"], v["dl_max"], "Revisa factor de carril."),
            ("Crecimiento", t["growth_pct"], v["growth_min"], v["growth_max"], "Revisa tasa histórica."),
            ("Mr", a["mr_mpa"], v["mr_min"], v["mr_max"], "Verifica ensayo y unidades MPa."),
            ("R", a["reliability_pct"], v["r_min"], v["r_max"], "Revisa confiabilidad objetivo."),
        ]
        for name, val, low, high, hint in checks:
            if not (low <= val <= high):
                raise ValueError(f"No se puede calcular: {name}={val} fuera de [{low}, {high}]. Sugerencia: {hint}")

    def show_help(self, key):
        messagebox.showinfo("Ayuda", HELP_TEXTS.get(key, "Ayuda no disponible."))

    def on_options(self):
        win = tk.Toplevel(self.root)
        win.title("Opciones")
        win.geometry("920x700")

        canvas = tk.Canvas(win)
        sc = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
        container = ttk.Frame(canvas, padding=12)
        container.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=container, anchor="nw")
        canvas.configure(yscrollcommand=sc.set)
        canvas.pack(side="left", fill="both", expand=True)
        sc.pack(side="right", fill="y")

        ttk.Label(container, text="Rangos de validación", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))
        ttk.Label(container, text="Parámetro", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w")
        ttk.Label(container, text="Descripción", font=("Segoe UI", 10, "bold")).grid(row=1, column=1, sticky="w")
        ttk.Label(container, text="Valor", font=("Segoe UI", 10, "bold")).grid(row=1, column=2, sticky="w")

        vars_map = {}
        row = 2
        for key, label, desc in VALIDATION_FIELDS:
            ttk.Label(container, text=label).grid(row=row, column=0, sticky="w")
            ttk.Label(container, text=desc, foreground="#444").grid(row=row, column=1, sticky="w")
            sv = tk.StringVar(value=str(self.data["validation"].get(key, "")))
            ttk.Entry(container, textvariable=sv, width=16).grid(row=row, column=2, sticky="ew")
            vars_map[key] = sv
            row += 1

        row += 1
        ttk.Separator(container, orient="horizontal").grid(row=row, column=0, columnspan=3, sticky="ew", pady=8)
        row += 1
        ttk.Label(container, text="Espesores mínimos por rango (pulgadas)", font=("Segoe UI", 11, "bold")).grid(row=row, column=0, columnspan=3, sticky="w")
        row += 1
        ttk.Label(container, text="Rango W18", font=("Segoe UI", 10, "bold")).grid(row=row, column=0, sticky="w")
        ttk.Label(container, text="D1 mínima (in)", font=("Segoe UI", 10, "bold")).grid(row=row, column=1, sticky="w")
        ttk.Label(container, text="D2 mínima (in)", font=("Segoe UI", 10, "bold")).grid(row=row, column=2, sticky="w")
        row += 1

        min_vars = {}
        minimums_table = self.data.get("minimums_table", {k: v.copy() for k, v in DEFAULT_MINIMUMS_TABLE_IN.items()})
        order = ["lt_50000", "50k_150k", "150k_500k", "500k_2m", "2m_7m", "gt_7m"]
        for key in order:
            r = minimums_table.get(key, DEFAULT_MINIMUMS_TABLE_IN[key])
            ttk.Label(container, text=r.get("label", key)).grid(row=row, column=0, sticky="w", pady=2)
            d1v = tk.StringVar(value=str(r.get("D1_min_in", 0.0)))
            d2v = tk.StringVar(value=str(r.get("D2_min_in", 0.0)))
            ttk.Entry(container, textvariable=d1v, width=16).grid(row=row, column=1, sticky="ew", pady=2)
            ttk.Entry(container, textvariable=d2v, width=16).grid(row=row, column=2, sticky="ew", pady=2)
            min_vars[key] = (d1v, d2v)
            row += 1

        container.columnconfigure(1, weight=1)

        def save_options():
            for k, sv in vars_map.items():
                self.data["validation"][k] = float(sv.get())

            if "minimums_table" not in self.data:
                self.data["minimums_table"] = {k: v.copy() for k, v in DEFAULT_MINIMUMS_TABLE_IN.items()}
            for key, (d1v, d2v) in min_vars.items():
                self.data["minimums_table"][key]["D1_min_in"] = float(d1v.get())
                self.data["minimums_table"][key]["D2_min_in"] = float(d2v.get())

            win.destroy()
            messagebox.showinfo("Opciones", "Rangos y mínimos actualizados.")

        ttk.Button(container, text="Guardar", command=save_options).grid(row=row + 1, column=2, sticky="e", pady=10)

    def _write_text(self, widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def on_new(self):
        self.data = self.default_data()
        self._load_to_form()
        self._write_text(self.txt, "Proyecto reiniciado.\n")
        self._write_text(self.txt_calc, "")

    def on_open(self):
        path = filedialog.askopenfilename(title="Abrir proyecto", filetypes=[("Proyecto JSON", "*.json")])
        if not path:
            return
        loaded = load_project(path)
        base = self.default_data()
        for k, v in loaded.items():
            if isinstance(v, dict) and isinstance(base.get(k), dict):
                base[k].update(v)
            else:
                base[k] = v
        self.data = base
        self._load_to_form()

    def on_save(self):
        self._read_form_to_data()
        path = filedialog.asksaveasfilename(title="Guardar proyecto", defaultextension=".json", filetypes=[("Proyecto JSON", "*.json")])
        if not path:
            return
        save_project(self.data, path)

    def _compute_tf(self):
        t = self.data["traffic"]
        if t.get("use_detailed_tf"):
            return calc_truck_factor_detailed(t.get("truck_classes", []))
        return t["truck_factor"], None

    def on_calculate(self):
        try:
            self._read_form_to_data()
            t = self.data["traffic"]; a = self.data["aashto"]; l = self.data["layers"]
            tf, tf_breakdown = self._compute_tf()

            w18 = calc_w18(aadt_total=t["aadt_total"], pct_trucks=t["pct_trucks"] / 100.0, dd=t["dd"], dl=t["dl"], truck_factor=tf, growth_pct=t["growth_pct"], years=t["design_years"])
            sn3_aashto, zr = solve_sn_required(w18=w18, reliability_pct=a["reliability_pct"], so=a["so"], pi=a["pi"], pt=a["pt"], mr_mpa=a["mr_mpa"])
            sn3_target = l["sn3_target"]

            calc = design_thicknesses_sequential(
                sn1_target=l["sn1_target"], sn2_target=l["sn2_target"], sn3_target=sn3_target,
                a1=l["a1"], a2=l["a2"], a3=l["a3"], m2=l["m2"], m3=l["m3"],
            )
            mins = apply_minimums_sequential(calc, w18, l["a1"], l["a2"], l["a3"], l["m2"], l["m3"], sn3_target, self.data.get("minimums_table"))

            self.data["results"] = {"W18": w18, "SN3_target": sn3_target, "SN3_aashto": sn3_aashto, "Zr": zr, "TF_used": tf, "TF_breakdown": tf_breakdown, "calculated": calc, "with_minimums": mins}

            out = []
            out.append("RESULTADOS AASHTO 1993\n\n")
            out.append(f"W18 acumulado: {w18:,.0f}\n")
            out.append(f"SN3 objetivo (usuario): {fnum(sn3_target,3)}\n")
            out.append(f"SN3 estimado por AASHTO (referencia): {fnum(sn3_aashto,3)}\n")
            out.append(f"SN1 objetivo: {fnum(l['sn1_target'],3)} | SN2 objetivo: {fnum(l['sn2_target'],3)}\n\n")
            out.append("1) Espesores calculados (SIN mínimos)\n")
            out.append(f"- D1: {fnum(calc['D1_in'],2)} in | {fnum(calc['D1_cm'],2)} cm\n")
            out.append(f"- D2: {fnum(calc['D2_in'],2)} in | {fnum(calc['D2_cm'],2)} cm\n")
            out.append(f"- D3: {fnum(calc['D3_in'],2)} in | {fnum(calc['D3_cm'],2)} cm\n")
            out.append(f"SN corregidos sumados: {fnum(calc['SN_sum'],3)}\n\n")
            out.append("2) Espesores ajustados con mínimos sugeridos\n")
            out.append(f"Rango tabla: {mins['minimum_table']['range_label']}\n")
            out.append(f"- D1: {fnum(mins['D1_in'],2)} in | {fnum(mins['D1_cm'],2)} cm\n")
            out.append(f"- D2: {fnum(mins['D2_in'],2)} in | {fnum(mins['D2_cm'],2)} cm\n")
            out.append(f"- D3: {fnum(mins['D3_in'],2)} in | {fnum(mins['D3_cm'],2)} cm\n")
            out.append(f"SN corregidos sumados: {fnum(mins['SN_sum'],3)}\n")
            out.append("Observación: En ajuste con mínimos se toman SIEMPRE D1 y D2 de la tabla/configuración de Opciones.\n")

            calc_txt = self._build_calculos_text(calc, mins, l, sn3_target)
            self._write_text(self.txt, "".join(out))
            self._write_text(self.txt_calc, calc_txt)
            self._draw_sections(calc, mins)
            self.nb.select(self.tab_results)

        except Exception as e:
            messagebox.showerror("Error de cálculo", f"No se puede calcular:\n{e}\n\nPosibles soluciones:\n- Revisa rangos en Opciones\n- Verifica SN1 <= SN2 <= SN3\n- Revisa coeficientes a y m")

    def _build_calculos_text(self, calc, mins, l, sn3):
        lines = []
        lines.append("DESGLOSE DE CÁLCULOS\n\n")
        lines.append("A) ESPESORES CALCULADOS\n")
        lines.append(f"D1 = SN1/A1 = {calc['SN1_target']:.3f}/{l['a1']:.3f} = {calc['D1_raw_in']:.3f} in\n")
        lines.append(f"D1 redondeado (0.5 más cercana) = {calc['D1_in']:.2f} in\n")
        lines.append(f"SN1* = D1red*A1 = {calc['D1_in']:.2f}*{l['a1']:.3f} = {calc['SN1_star']:.3f}\n\n")
        lines.append(f"D2 = (SN2-SN1*)/(A2*M2) = ({calc['SN2_target']:.3f}-{calc['SN1_star']:.3f})/({l['a2']:.3f}*{l['m2']:.3f}) = {calc['D2_raw_in']:.3f} in\n")
        lines.append(f"D2 redondeado (0.5 hacia arriba) = {calc['D2_in']:.2f} in\n")
        lines.append(f"SN2* = D2red*A2*M2 = {calc['D2_in']:.2f}*{l['a2']:.3f}*{l['m2']:.3f} = {calc['SN2_star']:.3f}\n\n")
        lines.append(f"D3 = (SN3-(SN1*+SN2*))/(A3*M3) = ({sn3:.3f}-({calc['SN1_star']:.3f}+{calc['SN2_star']:.3f}))/({l['a3']:.3f}*{l['m3']:.3f}) = {calc['D3_raw_in']:.3f} in\n")
        lines.append(f"D3 redondeado (0.5 hacia arriba) = {calc['D3_in']:.2f} in\n")
        lines.append(f"SN3* = D3red*A3*M3 = {calc['D3_in']:.2f}*{l['a3']:.3f}*{l['m3']:.3f} = {calc['SN3_star']:.3f}\n")
        lines.append(f"Comprobación suma: SN1*+SN2*+SN3* = {calc['SN_sum']:.3f}\n")
        lines.append(f"Criterio solicitado (<SN3): {calc['SN_sum']:.3f} < {sn3:.3f} -> {calc['criterion_user_lt_sn3']}\n")
        lines.append(f"Criterio estructural (>=SN3): {calc['SN_sum']:.3f} >= {sn3:.3f} -> {calc['criterion_meets_or_exceeds']}\n\n")

        lines.append("B) AJUSTE CON MÍNIMOS\n")
        lines.append(f"Tabla 7-2 aplicada: {mins['minimum_table']['range_label']}\n")
        lines.append(f"D1 ajustado = D1_min(opciones) = {mins['minimum_table']['D1_min_in']:.2f} in -> {mins['D1_in']:.2f} in\n")
        lines.append(f"D2 ajustado = D2_min(opciones) = {mins['minimum_table']['D2_min_in']:.2f} in -> {mins['D2_in']:.2f} in\n")
        lines.append(f"SN1*min = D1_adj*A1 = {mins['SN1_star']:.3f}\n")
        lines.append(f"SN2*min = D2_adj*A2*M2 = {mins['SN2_star']:.3f}\n")
        lines.append(f"D3_min = (SN3-(SN1*min+SN2*min))/(A3*M3) = {mins['D3_raw_in']:.3f} in\n")
        lines.append(f"D3 redondeado (0.5 hacia arriba) = {mins['D3_in']:.2f} in\n")
        lines.append(f"SN3*min = {mins['SN3_star']:.3f}\n")
        lines.append(f"Comprobación suma mínima: {mins['SN_sum']:.3f}\n")
        return "".join(lines)

    def _draw_one_section(self, canvas, d1, d2, d3):
        canvas.delete("all")
        total = max(d1 + d2 + d3, 0.1)
        scale = 420 / total
        x1, x2, y = 70, 430, 40
        for name, thk, color in [("Carpeta", d1, "#474fa8"), ("Base", d2, "#d1b06e"), ("Subbase", d3, "#a0b370")]:
            h = thk * scale
            canvas.create_rectangle(x1, y, x2, y + h, fill=color, outline="black")
            canvas.create_text((x1 + x2) / 2, y + h / 2, text=f"{name}: {thk:.2f} in / {thk*2.54:.1f} cm", fill="white")
            y += h
        canvas.create_rectangle(x1, y, x2, y + 70, fill="#9c7d5f", outline="black")
        canvas.create_text((x1 + x2) / 2, y + 35, text="Subrasante", fill="white")

    def _draw_sections(self, calc, mins):
        self._draw_one_section(self.canvas_calc, calc["D1_in"], calc["D2_in"], calc["D3_in"])
        self._draw_one_section(self.canvas_min, mins["D1_in"], mins["D2_in"], mins["D3_in"])

    def on_export_pdf(self):
        if not self.data.get("results"):
            messagebox.showwarning("PDF", "Primero calcula para generar reporte.")
            return
        path = filedialog.asksaveasfilename(title="Exportar reporte", defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if not path:
            return
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            rs = self.data["results"]
            c = canvas.Canvas(path, pagesize=letter)
            y = 760
            c.setFont("Helvetica-Bold", 13)
            c.drawString(40, y, "Reporte de Diseño - AASHTO 1993 Flexible")
            y -= 30
            c.setFont("Helvetica", 10)
            for ln in [
                f"W18: {rs['W18']:,.0f}",
                f"SN3 objetivo (usuario): {rs['SN3_target']:.3f}",
                f"SN3 estimado AASHTO (referencia): {rs['SN3_aashto']:.3f}",
                f"D calculados (in): {rs['calculated']['D1_in']:.2f}, {rs['calculated']['D2_in']:.2f}, {rs['calculated']['D3_in']:.2f}",
                f"D con mínimos (in): {rs['with_minimums']['D1_in']:.2f}, {rs['with_minimums']['D2_in']:.2f}, {rs['with_minimums']['D3_in']:.2f}",
            ]:
                c.drawString(40, y, ln)
                y -= 16
            c.save()
            messagebox.showinfo("PDF", f"Reporte exportado:\n{path}")
        except Exception as e:
            messagebox.showerror("PDF", f"No se pudo generar PDF (requiere reportlab):\n{e}")

    def run(self):
        self.root.mainloop()
