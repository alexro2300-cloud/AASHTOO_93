import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from core.esals import calc_w18, calc_truck_factor_detailed
from core.aashto93_flexible import solve_sn_required
from core.layers import recommend_thicknesses, apply_minimums, sn_provided
from data_io.project_json import save_project, load_project


def fnum(x, nd=3):
    try:
        return f"{float(x):.{nd}f}"
    except Exception:
        return str(x)


def cm_pair(inches: float):
    cm = inches * 2.54
    return cm, round(cm)


HELP_TEXTS = {
    "aadt": "TPDA (AADT): Tránsito Promedio Diario Anual total de vehículos.",
    "pct_trucks": "% Pesados: proporción de vehículos pesados respecto al TPDA total.",
    "dd": "DD (factor direccional): fracción del tránsito que circula en la dirección de diseño.",
    "dl": "DL (factor de carril): fracción del tránsito direccional que usa el carril de diseño.",
    "tf": "TF manual: ESAL por vehículo pesado promedio.",
    "ap": "Ap (factor de presencia/participación de clase): ajuste adicional por clase (si no aplica, usar 1.0).",
    "growth": "Crecimiento anual del tránsito pesado en porcentaje.",
    "rel": "R (%): confiabilidad del diseño AASHTO.",
    "so": "So: desviación estándar global del modelo AASHTO.",
    "pi": "Pi: serviciabilidad inicial.",
    "pt": "Pt: serviciabilidad terminal.",
    "mr": "Mr: módulo resiliente de subrasante en MPa.",
    "a1": "a1: coeficiente estructural de carpeta asfáltica.",
    "a2": "a2: coeficiente estructural de base.",
    "a3": "a3: coeficiente estructural de subbase.",
    "m2": "m2: coeficiente de drenaje de base.",
    "m3": "m3: coeficiente de drenaje de subbase.",
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
        self.root.geometry("1220x800")
        self.root.minsize(1080, 700)

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
            "layers": {"a1": 0.44, "a2": 0.14, "a3": 0.11, "m2": 1.0, "m3": 1.0},
            "search": {
                "step_in": 0.5,
                "d1_fixed_in": 4.0,
                "d2_min_in": 4.0,
                "d2_max_in": 16.0,
                "d3_min_in": 4.0,
                "d3_max_in": 20.0,
            },
            "validation": {
                "aadt_min": 100.0,
                "aadt_max": 200000.0,
                "pct_trucks_min": 0.0,
                "pct_trucks_max": 60.0,
                "dd_min": 0.3,
                "dd_max": 0.7,
                "dl_min": 0.5,
                "dl_max": 1.0,
                "growth_min": -2.0,
                "growth_max": 10.0,
                "mr_min": 20.0,
                "mr_max": 300.0,
                "r_min": 50.0,
                "r_max": 99.9,
            },
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
        for txt, cmd in [
            ("Nuevo", self.on_new), ("Abrir", self.on_open), ("Guardar", self.on_save),
            ("Opciones", self.on_options), ("Calcular", self.on_calculate), ("PDF", self.on_export_pdf)
        ]:
            ttk.Button(btns, text=txt, command=cmd).pack(side="left", padx=4)

        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill="both", expand=True, padx=10, pady=8)

        self.tab_traffic = ttk.Frame(self.nb, padding=12)
        self.tab_aashto = ttk.Frame(self.nb, padding=12)
        self.tab_layers = ttk.Frame(self.nb, padding=12)
        self.tab_results = ttk.Frame(self.nb, padding=12)
        self.tab_section = ttk.Frame(self.nb, padding=12)

        self.nb.add(self.tab_traffic, text="Tránsito / ESALs")
        self.nb.add(self.tab_aashto, text="Parámetros AASHTO")
        self.nb.add(self.tab_layers, text="Capas / Búsqueda")
        self.nb.add(self.tab_results, text="Resultados")
        self.nb.add(self.tab_section, text="Sección de Pavimento")

        self._build_tab_traffic()
        self._build_tab_aashto()
        self._build_tab_layers()
        self._build_tab_results()
        self._build_tab_section()

        self._load_to_form()

    def _entry_with_help(self, parent, row, label, key, unit="", col=0):
        ttk.Label(parent, text=label).grid(row=row, column=col, sticky="w", pady=3, padx=(0, 6))
        v = tk.StringVar()
        ttk.Entry(parent, textvariable=v).grid(row=row, column=col + 1, sticky="ew", pady=3)
        ttk.Label(parent, text=unit).grid(row=row, column=col + 2, sticky="w", padx=(6, 2))
        ttk.Button(parent, text="?", width=3, command=lambda k=key: self.show_help(k)).grid(row=row, column=col + 3, padx=(2, 0))
        return v

    def _build_tab_traffic(self):
        frm = ttk.LabelFrame(self.tab_traffic, text="Datos de tránsito", padding=12)
        frm.pack(fill="x")
        for c in range(8):
            frm.columnconfigure(c, weight=1 if c in (1, 5) else 0)

        self.v_aadt = self._entry_with_help(frm, 0, "TPDA total", "aadt", "veh/día")
        self.v_pct_trucks = self._entry_with_help(frm, 1, "% pesados", "pct_trucks", "%")
        self.v_dd = self._entry_with_help(frm, 2, "DD", "dd", "-")
        self.v_dl = self._entry_with_help(frm, 3, "DL", "dl", "-")
        self.v_tf = self._entry_with_help(frm, 4, "TF manual", "tf", "ESAL/veh pesado")
        self.v_growth = self._entry_with_help(frm, 5, "Crecimiento", "growth", "%")

        ttk.Label(frm, text="Años de diseño").grid(row=6, column=0, sticky="w")
        self.v_years = tk.StringVar()
        ttk.Entry(frm, textvariable=self.v_years).grid(row=6, column=1, sticky="ew")

        self.v_use_detailed = tk.BooleanVar()
        ttk.Checkbutton(frm, text="Usar TF detallado por tipo de vehículo", variable=self.v_use_detailed).grid(row=7, column=0, columnspan=4, sticky="w", pady=(8, 4))

        tip = ttk.Label(
            self.tab_traffic,
            text="Ap = factor de ajuste por clase. Si no deseas ajuste adicional, usa Ap=1.0.",
            foreground="#444"
        )
        tip.pack(anchor="w", pady=(6, 0))

        cls = ttk.LabelFrame(self.tab_traffic, text="Clasificación vehicular (activa/desactiva con checkbox)", padding=10)
        cls.pack(fill="both", expand=True, pady=(10, 0))
        headers = ["Usar", "Nomenclatura", "Participación %", "EALF", "Ap", "?"]
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
            ttk.Button(cls, text="?", width=3, command=lambda: self.show_help("ap")).grid(row=i + 1, column=5)
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
        frm1 = ttk.LabelFrame(self.tab_layers, text="Coeficientes estructurales", padding=12)
        frm1.pack(fill="x")
        for c in range(8):
            frm1.columnconfigure(c, weight=1 if c in (1, 5) else 0)
        self.v_a1 = self._entry_with_help(frm1, 0, "a1", "a1")
        self.v_a2 = self._entry_with_help(frm1, 1, "a2", "a2")
        self.v_a3 = self._entry_with_help(frm1, 2, "a3", "a3")
        self.v_m2 = self._entry_with_help(frm1, 3, "m2", "m2")
        self.v_m3 = self._entry_with_help(frm1, 4, "m3", "m3")

        frm2 = ttk.LabelFrame(self.tab_layers, text="Búsqueda de espesores (pulgadas)", padding=12)
        frm2.pack(fill="x", pady=(10, 0))
        for c in range(5):
            frm2.columnconfigure(c, weight=1 if c in (1, 3) else 0)
        self.v_step = tk.StringVar()
        self.v_d1 = tk.StringVar()
        self.v_d2min = tk.StringVar()
        self.v_d2max = tk.StringVar()
        self.v_d3min = tk.StringVar()
        self.v_d3max = tk.StringVar()

        ttk.Label(frm2, text="Paso").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm2, textvariable=self.v_step).grid(row=0, column=1, sticky="ew")
        ttk.Label(frm2, text="in").grid(row=0, column=2, sticky="w")

        ttk.Label(frm2, text="D1 fijo").grid(row=1, column=0, sticky="w", pady=3)
        ttk.Entry(frm2, textvariable=self.v_d1).grid(row=1, column=1, sticky="ew", pady=3)
        ttk.Label(frm2, text="in").grid(row=1, column=2, sticky="w", pady=3)

        ttk.Label(frm2, text="D2 min / max").grid(row=2, column=0, sticky="w", pady=3)
        ttk.Entry(frm2, textvariable=self.v_d2min).grid(row=2, column=1, sticky="ew", pady=3)
        ttk.Entry(frm2, textvariable=self.v_d2max).grid(row=2, column=3, sticky="ew", pady=3)

        ttk.Label(frm2, text="D3 min / max").grid(row=3, column=0, sticky="w", pady=3)
        ttk.Entry(frm2, textvariable=self.v_d3min).grid(row=3, column=1, sticky="ew", pady=3)
        ttk.Entry(frm2, textvariable=self.v_d3max).grid(row=3, column=3, sticky="ew", pady=3)

    def _build_tab_results(self):
        self.txt = tk.Text(self.tab_results, height=30, wrap="word")
        self.txt.pack(fill="both", expand=True)
        self.txt.insert("1.0", "Aquí saldrán los resultados.\n")
        self.txt.configure(state="disabled")

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
        t = self.data["traffic"]
        a = self.data["aashto"]
        l = self.data["layers"]
        s = self.data["search"]

        self.v_aadt.set(str(t["aadt_total"]))
        self.v_pct_trucks.set(str(t["pct_trucks"]))
        self.v_dd.set(str(t["dd"]))
        self.v_dl.set(str(t["dl"]))
        self.v_tf.set(str(t["truck_factor"]))
        self.v_growth.set(str(t["growth_pct"]))
        self.v_years.set(str(t["design_years"]))
        self.v_use_detailed.set(bool(t.get("use_detailed_tf", False)))

        for idx, row in enumerate(t.get("truck_classes", [])):
            if idx < len(self.class_rows):
                en, n, s_v, e, ap = self.class_rows[idx]
                en.set(bool(row.get("enabled", True)))
                n.set(str(row.get("name", "")))
                s_v.set(str(row.get("share_pct", "")))
                e.set(str(row.get("ealf", "")))
                ap.set(str(row.get("ap", 1.0)))

        self.v_rel.set(str(a["reliability_pct"]))
        self.v_so.set(str(a["so"]))
        self.v_pi.set(str(a["pi"]))
        self.v_pt.set(str(a["pt"]))
        self.v_mr.set(str(a["mr_mpa"]))

        self.v_a1.set(str(l["a1"]))
        self.v_a2.set(str(l["a2"]))
        self.v_a3.set(str(l["a3"]))
        self.v_m2.set(str(l["m2"]))
        self.v_m3.set(str(l["m3"]))

        self.v_step.set(str(s["step_in"]))
        self.v_d1.set(str(s["d1_fixed_in"]))
        self.v_d2min.set(str(s["d2_min_in"]))
        self.v_d2max.set(str(s["d2_max_in"]))
        self.v_d3min.set(str(s["d3_min_in"]))
        self.v_d3max.set(str(s["d3_max_in"]))

    def _read_form_to_data(self):
        t = self.data["traffic"]
        a = self.data["aashto"]
        l = self.data["layers"]
        s = self.data["search"]

        t["aadt_total"] = float(self.v_aadt.get())
        t["pct_trucks"] = float(self.v_pct_trucks.get())
        t["dd"] = float(self.v_dd.get())
        t["dl"] = float(self.v_dl.get())
        t["truck_factor"] = float(self.v_tf.get())
        t["growth_pct"] = float(self.v_growth.get())
        t["design_years"] = int(float(self.v_years.get()))
        t["use_detailed_tf"] = bool(self.v_use_detailed.get())

        classes = []
        for en, n, s_v, e, ap in self.class_rows:
            if n.get().strip() or s_v.get().strip() or e.get().strip():
                classes.append({
                    "enabled": bool(en.get()),
                    "name": n.get().strip() or "Clase",
                    "share_pct": float(s_v.get() or 0),
                    "ealf": float(e.get() or 0),
                    "ap": float(ap.get() or 1),
                })
        t["truck_classes"] = classes

        a["reliability_pct"] = float(self.v_rel.get())
        a["so"] = float(self.v_so.get())
        a["pi"] = float(self.v_pi.get())
        a["pt"] = float(self.v_pt.get())
        a["mr_mpa"] = float(self.v_mr.get())

        l["a1"] = float(self.v_a1.get())
        l["a2"] = float(self.v_a2.get())
        l["a3"] = float(self.v_a3.get())
        l["m2"] = float(self.v_m2.get())
        l["m3"] = float(self.v_m3.get())

        s["step_in"] = float(self.v_step.get())
        s["d1_fixed_in"] = float(self.v_d1.get())
        s["d2_min_in"] = float(self.v_d2min.get())
        s["d2_max_in"] = float(self.v_d2max.get())
        s["d3_min_in"] = float(self.v_d3min.get())
        s["d3_max_in"] = float(self.v_d3max.get())

        self._validate_ranges()

    def _validate_ranges(self):
        t = self.data["traffic"]
        a = self.data["aashto"]
        v = self.data["validation"]

        checks = [
            ("TPDA", t["aadt_total"], v["aadt_min"], v["aadt_max"], "Ajusta TPDA en Tránsito o cambia rango en Opciones."),
            ("% pesados", t["pct_trucks"], v["pct_trucks_min"], v["pct_trucks_max"], "Verifica clasificación vehicular o corrige rango."),
            ("DD", t["dd"], v["dd_min"], v["dd_max"], "DD típico 0.5-0.6 en muchas vías bidireccionales."),
            ("DL", t["dl"], v["dl_min"], v["dl_max"], "En carril de diseño suele estar entre 0.7 y 1.0."),
            ("Crecimiento", t["growth_pct"], v["growth_min"], v["growth_max"], "Revisa tasa histórica de crecimiento."),
            ("Mr", a["mr_mpa"], v["mr_min"], v["mr_max"], "Revisa ensayo de subrasante y unidades (MPa)."),
            ("R", a["reliability_pct"], v["r_min"], v["r_max"], "Usa confiabilidad acorde al tipo de camino."),
        ]
        for name, val, low, high, hint in checks:
            if not (low <= val <= high):
                raise ValueError(
                    f"No se puede calcular: {name}={val} está fuera del rango [{low}, {high}].\n"
                    f"Sugerencia: {hint}"
                )

    def show_help(self, key):
        messagebox.showinfo("Ayuda", HELP_TEXTS.get(key, "Ayuda no disponible."))

    def on_options(self):
        win = tk.Toplevel(self.root)
        win.title("Opciones de validación")
        win.geometry("760x520")
        frame = ttk.Frame(win, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Parámetro", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(frame, text="Descripción", font=("Segoe UI", 10, "bold")).grid(row=0, column=1, sticky="w")
        ttk.Label(frame, text="Valor", font=("Segoe UI", 10, "bold")).grid(row=0, column=2, sticky="w")

        vars_map = {}
        row = 1
        for key, label, desc in VALIDATION_FIELDS:
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=2)
            ttk.Label(frame, text=desc, foreground="#444").grid(row=row, column=1, sticky="w", pady=2)
            sv = tk.StringVar(value=str(self.data["validation"].get(key, "")))
            ttk.Entry(frame, textvariable=sv, width=16).grid(row=row, column=2, sticky="ew", pady=2)
            vars_map[key] = sv
            row += 1
        frame.columnconfigure(1, weight=1)

        def save_options():
            for k, sv in vars_map.items():
                self.data["validation"][k] = float(sv.get())
            win.destroy()
            messagebox.showinfo("Opciones", "Rangos de validación actualizados.")

        ttk.Button(frame, text="Guardar", command=save_options).grid(row=row + 1, column=2, sticky="e", pady=10)

    def _write_results(self, text):
        self.txt.configure(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.insert("1.0", text)
        self.txt.configure(state="disabled")

    def on_new(self):
        self.data = self.default_data()
        self._load_to_form()
        self._write_results("Proyecto reiniciado.\n")

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
        self._write_results(f"Proyecto cargado:\n{path}\n")

    def on_save(self):
        self._read_form_to_data()
        path = filedialog.asksaveasfilename(title="Guardar proyecto", defaultextension=".json", filetypes=[("Proyecto JSON", "*.json")])
        if not path:
            return
        save_project(self.data, path)
        self._write_results(f"Proyecto guardado:\n{path}\n")

    def _compute_tf(self):
        t = self.data["traffic"]
        if t.get("use_detailed_tf"):
            return calc_truck_factor_detailed(t.get("truck_classes", []))
        return t["truck_factor"], None

    def on_calculate(self):
        try:
            self._read_form_to_data()
            t = self.data["traffic"]
            a = self.data["aashto"]
            l = self.data["layers"]
            s = self.data["search"]

            tf, tf_breakdown = self._compute_tf()
            w18 = calc_w18(
                aadt_total=t["aadt_total"],
                pct_trucks=t["pct_trucks"] / 100.0,
                dd=t["dd"],
                dl=t["dl"],
                truck_factor=tf,
                growth_pct=t["growth_pct"],
                years=t["design_years"],
            )
            sn_req, zr = solve_sn_required(w18=w18, reliability_pct=a["reliability_pct"], so=a["so"], pi=a["pi"], pt=a["pt"], mr_mpa=a["mr_mpa"])

            rec_calc = recommend_thicknesses(
                sn_required=sn_req,
                a1=l["a1"], a2=l["a2"], a3=l["a3"],
                m2=l["m2"], m3=l["m3"],
                step_in=s["step_in"],
                d1_fixed_in=s["d1_fixed_in"],
                d2_min_in=s["d2_min_in"], d2_max_in=s["d2_max_in"],
                d3_min_in=s["d3_min_in"], d3_max_in=s["d3_max_in"],
            )

            if rec_calc["status"] != "OK":
                best_sn = rec_calc.get("SN_best", 0.0)
                deficit = max(0.0, sn_req - best_sn)
                msg = (
                    "No se puede calcular una combinación válida con tus límites actuales.\n\n"
                    f"SN requerido: {sn_req:.3f}\n"
                    f"Mejor SN encontrado con tus máximos: {best_sn:.3f}\n"
                    f"Déficit aproximado: {deficit:.3f}\n\n"
                    "Posibles soluciones:\n"
                    "- Aumenta D2_max y/o D3_max\n"
                    "- Incrementa D1 fijo\n"
                    "- Reduce el paso de búsqueda\n"
                    "- Revisa Mr, R, So y parámetros de tránsito"
                )
                self._write_results(msg)
                self.nb.select(self.tab_results)
                return

            rec_min = apply_minimums(rec_calc, w18)
            sn_min = sn_provided(l["a1"], l["a2"], l["a3"], l["m2"], l["m3"], rec_min["D1_in"], rec_min["D2_in"], rec_min["D3_in"])

            self.data["results"] = {
                "W18": w18,
                "SN_required": sn_req,
                "Zr": zr,
                "TF_used": tf,
                "TF_breakdown": tf_breakdown,
                "calculated": rec_calc,
                "with_minimums": {**rec_min, "SN_provided": sn_min},
            }

            out = []
            out.append("RESULTADOS AASHTO 1993\n\n")
            out.append(f"W18 acumulado: {w18:,.0f}\n")
            out.append(f"TF usado: {fnum(tf, 3)}\n")
            out.append("Nota Ap: factor de ajuste por clase (multiplica a EALF por su participación).\n")
            out.append(f"Zr: {fnum(zr, 3)}\n")
            out.append(f"SN requerido: {fnum(sn_req, 3)}\n\n")

            out.append("1) Espesores calculados (SIN mínimos)\n")
            for k in ("D1_in", "D2_in", "D3_in"):
                cm, cm_round = cm_pair(rec_calc[k])
                out.append(f"- {k}: {fnum(rec_calc[k], 2)} in = {fnum(cm, 2)} cm (redondeado {cm_round} cm)\n")
            out.append(f"SN provisto calculado: {fnum(rec_calc['SN_provided'], 3)}\n\n")

            out.append("2) Espesores ajustados con mínimos sugeridos (Tabla 7-2)\n")
            mins = rec_min["minimum_table"]
            out.append(f"Rango de tabla aplicado: {mins['range_label']}\n")
            for k in ("D1_in", "D2_in", "D3_in"):
                cm, cm_round = cm_pair(rec_min[k])
                out.append(f"- {k}: {fnum(rec_min[k], 2)} in = {fnum(cm, 2)} cm (redondeado {cm_round} cm)\n")
            out.append(f"SN provisto con mínimos: {fnum(sn_min, 3)}\n")
            out.append(
                "Observación: "
                + ("Los mínimos SÍ modificaron la solución calculada." if rec_min["minimums_govern"] else "Los mínimos NO modificaron la solución calculada.")
                + "\n"
            )

            if rec_min["minimums_govern"]:
                messagebox.showwarning("Aviso de mínimos", "La solución final fue ajustada por espesores mínimos sugeridos (Tabla 7-2).")

            self._write_results("".join(out))
            self._draw_sections(rec_calc, rec_min)
            self.nb.select(self.tab_results)

        except Exception as e:
            messagebox.showerror("Error de cálculo", f"No se puede calcular:\n{e}\n\nSugerencia: revisa entradas y rangos en Opciones.")

    def _draw_one_section(self, canvas, d1, d2, d3):
        canvas.delete("all")
        h = 420
        total = max(d1 + d2 + d3, 0.1)
        scale = h / total
        x1, x2 = 70, 430
        y = 40
        layers = [("Carpeta", d1, "#474fa8"), ("Base", d2, "#d1b06e"), ("Subbase", d3, "#a0b370")]
        for name, thk, color in layers:
            lh = thk * scale
            canvas.create_rectangle(x1, y, x2, y + lh, fill=color, outline="black")
            canvas.create_text((x1 + x2) / 2, y + lh / 2, text=f"{name}: {thk:.2f} in / {thk*2.54:.1f} cm", fill="white")
            y += lh
        canvas.create_rectangle(x1, y, x2, y + 70, fill="#9c7d5f", outline="black")
        canvas.create_text((x1 + x2) / 2, y + 35, text="Subrasante", fill="white")

    def _draw_sections(self, rec_calc, rec_min):
        self._draw_one_section(self.canvas_calc, rec_calc["D1_in"], rec_calc["D2_in"], rec_calc["D3_in"])
        self._draw_one_section(self.canvas_min, rec_min["D1_in"], rec_min["D2_in"], rec_min["D3_in"])

    def on_export_pdf(self):
        if not self.data.get("results"):
            messagebox.showwarning("PDF", "Primero calcula para generar el reporte.")
            return
        path = filedialog.asksaveasfilename(title="Exportar reporte", defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if not path:
            return
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            c = canvas.Canvas(path, pagesize=letter)
            y = 760
            c.setFont("Helvetica-Bold", 13)
            c.drawString(40, y, "Reporte de Diseño - AASHTO 1993 Flexible")
            y -= 28
            c.setFont("Helvetica", 10)
            lines = [
                "Ecuaciones usadas:",
                "W18 = 365*AADT*%pesados*DD*DL*TF*factor_crecimiento",
                "log10(W18)=Zr*So+9.36log10(SN+1)-0.20+[log10(ΔPSI/2.7)]/(0.40+1094/(SN+1)^5.19)+2.32log10(Mr)-8.07",
                "SN = a1*D1 + a2*m2*D2 + a3*m3*D3",
                "TF detallado = Σ(participación_i * EALF_i * Ap_i)",
                "",
            ]
            rs = self.data["results"]
            lines.extend([
                f"W18: {rs['W18']:,.0f}",
                f"SN requerido: {rs['SN_required']:.3f}",
                f"SN provisto calculado: {rs['calculated']['SN_provided']:.3f}",
                f"SN provisto con mínimos: {rs['with_minimums']['SN_provided']:.3f}",
            ])
            for ln in lines:
                c.drawString(40, y, ln)
                y -= 16
            c.save()
            messagebox.showinfo("PDF", f"Reporte exportado:\n{path}")
        except Exception as e:
            messagebox.showerror("PDF", f"No se pudo generar PDF (requiere reportlab):\n{e}")

    def run(self):
        self.root.mainloop()
