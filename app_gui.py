import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox

from core.esals import compute_esals_detailed
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
    "dd": "DD (factor direccional): fracción del tránsito en la dirección de diseño.",
    "dl": "DL (factor de carril): fracción del tránsito direccional que usa carril de diseño.",
    "growth": "Crecimiento anual del tránsito utilizado para el factor B en ESALs.",
    "rel": "Confiabilidad (R): probabilidad de que el pavimento cumpla su desempeño durante el periodo de diseño.",
    "so": "Desviación estándar combinada (So) del modelo AASHTO 93.",
    "pi": "Índice de serviciabilidad inicial (Pi).",
    "pt": "Índice de serviciabilidad terminal (Pt).",
    "mr": "Módulo resiliente de subrasante (Mr), en MPa.",
    "a1": "Coeficiente estructural de la carpeta asfáltica.",
    "a2": "Coeficiente estructural de la base.",
    "a3": "Coeficiente estructural de la subbase.",
    "m2": "Coeficiente de drenaje para la base.",
    "m3": "Coeficiente de drenaje para la subbase.",
    "sn1": "Número estructural objetivo para la capa 1.",
    "sn2": "Número estructural objetivo acumulado hasta la capa 2.",
    "sn3": "Número estructural objetivo acumulado total (estructura completa).",
    "width": "Ancho de corona del camino para el cálculo volumétrico por kilómetro.",
    "cost_d1": "Costo unitario de carpeta asfáltica en $/m³.",
    "cost_d2": "Costo unitario de base en $/m³.",
    "cost_d3": "Costo unitario de subbase en $/m³.",
}

IMAGE_SOURCES_DIR = Path(__file__).parent / "sources" / "images"
UI_IMAGE_PATHS = {
    "logo_school": IMAGE_SOURCES_DIR / "logo_school.png",
    "logo_lab": IMAGE_SOURCES_DIR / "logo_lab.png",
    "traffic_banner": IMAGE_SOURCES_DIR / "traffic_types.png",
    "help_aadt": IMAGE_SOURCES_DIR / "help_aadt.png",
    "help_dd": IMAGE_SOURCES_DIR / "help_dd.png",
    "help_dl": IMAGE_SOURCES_DIR / "help_dl.png",
    "help_growth": IMAGE_SOURCES_DIR / "help_growth.png",
    "help_rel": IMAGE_SOURCES_DIR / "help_rel.png",
    "help_so": IMAGE_SOURCES_DIR / "help_so.png",
    "help_pi": IMAGE_SOURCES_DIR / "help_pi.png",
    "help_pt": IMAGE_SOURCES_DIR / "help_pt.png",
    "help_mr": IMAGE_SOURCES_DIR / "help_mr.png",
    "help_a1": IMAGE_SOURCES_DIR / "help_a1.png",
    "help_a2": IMAGE_SOURCES_DIR / "help_a2.png",
    "help_a3": IMAGE_SOURCES_DIR / "help_a3.png",
    "help_m2": IMAGE_SOURCES_DIR / "help_m2.png",
    "help_m3": IMAGE_SOURCES_DIR / "help_m3.png",
    "help_sn1": IMAGE_SOURCES_DIR / "help_sn1.png",
    "help_sn2": IMAGE_SOURCES_DIR / "help_sn2.png",
    "help_sn3": IMAGE_SOURCES_DIR / "help_sn3.png",
    "help_width": IMAGE_SOURCES_DIR / "help_width.png",
    "help_cost_d1": IMAGE_SOURCES_DIR / "help_cost_d1.png",
    "help_cost_d2": IMAGE_SOURCES_DIR / "help_cost_d2.png",
    "help_cost_d3": IMAGE_SOURCES_DIR / "help_cost_d3.png",
}

HELP_IMAGE_KEYS = {
    "aadt": "help_aadt",
    "dd": "help_dd",
    "dl": "help_dl",
    "growth": "help_growth",
    "rel": "help_rel",
    "so": "help_so",
    "pi": "help_pi",
    "pt": "help_pt",
    "mr": "help_mr",
    "a1": "help_a1",
    "a2": "help_a2",
    "a3": "help_a3",
    "m2": "help_m2",
    "m3": "help_m3",
    "sn1": "help_sn1",
    "sn2": "help_sn2",
    "sn3": "help_sn3",
    "width": "help_width",
    "cost_d1": "help_cost_d1",
    "cost_d2": "help_cost_d2",
    "cost_d3": "help_cost_d3",
}

VALIDATION_FIELDS = [
    ("aadt_min", "TPDA mínimo", "Límite inferior aceptado para TPDA total."),
    ("aadt_max", "TPDA máximo", "Límite superior aceptado para TPDA total."),
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
        self.root.title("Calculadora de Espesores de Pavimento Flexible por el método AASHTO")
        self.root.geometry("1240x820")
        self.root.minsize(1100, 720)
        self.data = self.default_data()
        self._ui_images = {}
        self._build_ui()

    def default_data(self):
        return {
            "project": {"name": "Proyecto 01"},
            "traffic": {
                "aadt_total": 10000.0,
                "pct_trucks": 100.0,
                "dd": 0.50,
                "dl": 0.90,
                "growth_pct": 3.0,
                "design_years": 20,
                "class_input_mode": "share_pct",
                "truck_classes": [
                    {"name": "A", "share_pct": 25.0, "count": 2500.0, "ealf": 0.05, "enabled": True},
                    {"name": "B", "share_pct": 15.0, "count": 1500.0, "ealf": 0.20, "enabled": True},
                    {"name": "C2", "share_pct": 8.0, "count": 800.0, "ealf": 0.30, "enabled": True},
                    {"name": "C3", "share_pct": 8.0, "count": 800.0, "ealf": 0.50, "enabled": True},
                    {"name": "C2-R2", "share_pct": 8.0, "count": 800.0, "ealf": 0.80, "enabled": True},
                    {"name": "C3-R2", "share_pct": 8.0, "count": 800.0, "ealf": 1.00, "enabled": True},
                    {"name": "C2-R3", "share_pct": 8.0, "count": 800.0, "ealf": 1.10, "enabled": True},
                    {"name": "C3-R3", "share_pct": 6.0, "count": 600.0, "ealf": 1.30, "enabled": True},
                    {"name": "T2-S1", "share_pct": 5.0, "count": 500.0, "ealf": 1.40, "enabled": True},
                    {"name": "T2-S2", "share_pct": 4.0, "count": 400.0, "ealf": 1.60, "enabled": True},
                    {"name": "T2-S3", "share_pct": 3.0, "count": 300.0, "ealf": 1.90, "enabled": True},
                    {"name": "T3-S2", "share_pct": 1.5, "count": 150.0, "ealf": 2.10, "enabled": True},
                    {"name": "T3-S3", "share_pct": 0.5, "count": 50.0, "ealf": 2.40, "enabled": True},
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
                "dd_min": 0.3, "dd_max": 0.7,
                "dl_min": 0.5, "dl_max": 1.0,
                "growth_min": -2.0, "growth_max": 10.0,
                "mr_min": 20.0, "mr_max": 300.0,
                "r_min": 50.0, "r_max": 99.9,
            },
            "minimums_table": {k: v.copy() for k, v in DEFAULT_MINIMUMS_TABLE_IN.items()},
            "prelim_costs": {"width_m": 12.0, "cost_d1": 3200.0, "cost_d2": 900.0, "cost_d3": 700.0},
            "results": {},
        }

    def _build_ui(self):
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))

        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")
        top.columnconfigure(0, weight=1)
        top.columnconfigure(1, weight=3)
        top.columnconfigure(2, weight=1)

        logo_wrap = ttk.Frame(top)
        logo_wrap.grid(row=0, column=0, sticky="w")
        school_logo = self._load_ui_image("logo_school", subsample=2)
        if school_logo:
            ttk.Label(logo_wrap, image=school_logo).pack(side="left", padx=(0, 6))
        else:
            ttk.Label(logo_wrap, text="[Logo Escolar]", foreground="#666").pack(side="left", padx=(0, 6))

        lab_logo = self._load_ui_image("logo_lab", subsample=2)
        if lab_logo:
            ttk.Label(logo_wrap, image=lab_logo).pack(side="left", padx=(0, 8))
        else:
            ttk.Label(logo_wrap, text="[Logo Laboratorio]", foreground="#666").pack(side="left", padx=(0, 8))

        ttk.Label(
            top,
            text="Calculadora de Espesores de Pavimento Flexible por el método AASHTO",
            style="Title.TLabel",
            anchor="center",
            justify="center",
        ).grid(row=0, column=1, sticky="ew")

        actions = ttk.Frame(top)
        actions.grid(row=0, column=2, sticky="e")
        ttk.Button(actions, text="Calcular", command=self.on_calculate).pack(side="left", padx=(0, 8))
        actions_btn = ttk.Menubutton(actions, text="Acciones")
        actions_btn.pack(side="left")
        actions_menu = tk.Menu(actions_btn, tearoff=False)
        for txt, cmd in [
            ("Nuevo", self.on_new),
            ("Abrir", self.on_open),
            ("Guardar", self.on_save),
            ("Opciones", self.on_options),
            ("PDF", self.on_export_pdf),
        ]:
            actions_menu.add_command(label=txt, command=cmd)
        actions_btn["menu"] = actions_menu

        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill="both", expand=True, padx=10, pady=8)

        self.tab_traffic = ttk.Frame(self.nb, padding=12)
        self.tab_aashto = ttk.Frame(self.nb, padding=12)
        self.tab_layers = ttk.Frame(self.nb, padding=12)
        self.tab_results = ttk.Frame(self.nb, padding=12)
        self.tab_calc_esals = ttk.Frame(self.nb, padding=12)
        self.tab_calc_thickness = ttk.Frame(self.nb, padding=12)
        self.tab_costs = ttk.Frame(self.nb, padding=12)
        self.tab_section = ttk.Frame(self.nb, padding=12)
        self.tab_legal = ttk.Frame(self.nb, padding=12)

        self.nb.add(self.tab_traffic, text="Tránsito / ESALs")
        self.nb.add(self.tab_calc_esals, text="Cálculos ESALs")
        self.nb.add(self.tab_aashto, text="Parámetros AASHTO")
        self.nb.add(self.tab_layers, text="Capas / Espesores")
        self.nb.add(self.tab_calc_thickness, text="Cálculos Espesores")
        self.nb.add(self.tab_results, text="Resultados")
        self.nb.add(self.tab_costs, text="Costos preliminares")
        self.nb.add(self.tab_section, text="Sección de Pavimento")
        self.nb.add(self.tab_legal, text="Legal")

        self._build_tab_traffic()
        self._build_tab_calc_esals()
        self._build_tab_aashto()
        self._build_tab_layers()
        self._build_tab_calc_thickness()
        self._build_tab_results()
        self._build_tab_costs()
        self._build_tab_section()
        self._build_tab_legal()
        self._load_to_form()

    def _load_ui_image(self, key: str, subsample: int = 1):
        path = UI_IMAGE_PATHS.get(key)
        if not path or not path.exists():
            return None
        try:
            img = tk.PhotoImage(file=str(path))
            if subsample and subsample > 1:
                img = img.subsample(subsample, subsample)
            self._ui_images[key] = img
            return img
        except Exception:
            return None

    def _bind_mousewheel(self, scrollable):
        def on_wheel(event):
            if getattr(event, "num", None) == 4:
                step = -1
            elif getattr(event, "num", None) == 5:
                step = 1
            else:
                delta = getattr(event, "delta", 0)
                step = -1 if delta > 0 else 1
            try:
                scrollable.yview_scroll(step, "units")
            except Exception:
                return

        def bind_all(_):
            self.root.bind_all("<MouseWheel>", on_wheel)
            self.root.bind_all("<Button-4>", on_wheel)
            self.root.bind_all("<Button-5>", on_wheel)

        def unbind_all(_):
            self.root.unbind_all("<MouseWheel>")
            self.root.unbind_all("<Button-4>")
            self.root.unbind_all("<Button-5>")

        scrollable.bind("<Enter>", bind_all)
        scrollable.bind("<Leave>", unbind_all)

    def _entry_with_help(self, parent, row, label, key, unit="", col=0):
        ttk.Label(parent, text=label).grid(row=row, column=col, sticky="w", pady=3)
        v = tk.StringVar()
        ttk.Entry(parent, textvariable=v).grid(row=row, column=col + 1, sticky="ew", pady=3)
        ttk.Label(parent, text=unit).grid(row=row, column=col + 2, sticky="w", padx=(6, 2))
        ttk.Button(parent, text="?", width=3, command=lambda k=key: self.show_help(k)).grid(row=row, column=col + 3)
        return v

    def _build_tab_traffic(self):
        holder = ttk.Frame(self.tab_traffic)
        holder.pack(fill="both", expand=True)
        tab_canvas = tk.Canvas(holder, highlightthickness=0)
        tab_scroll = ttk.Scrollbar(holder, orient="vertical", command=tab_canvas.yview)
        content = ttk.Frame(tab_canvas)
        content.bind("<Configure>", lambda e: tab_canvas.configure(scrollregion=tab_canvas.bbox("all")))
        content_window = tab_canvas.create_window((0, 0), window=content, anchor="nw")
        tab_canvas.bind("<Configure>", lambda e: tab_canvas.itemconfigure(content_window, width=e.width))
        tab_canvas.configure(yscrollcommand=tab_scroll.set)
        tab_canvas.pack(side="left", fill="both", expand=True)
        tab_scroll.pack(side="right", fill="y")
        self._bind_mousewheel(tab_canvas)

        frm = ttk.LabelFrame(content, text="Datos de tránsito", padding=12)
        frm.pack(fill="x")
        for c in range(8):
            frm.columnconfigure(c, weight=1 if c in (1, 5) else 0)
        self.v_aadt = self._entry_with_help(frm, 0, "TPDA total", "aadt", "veh/día")
        self.e_aadt = frm.grid_slaves(row=0, column=1)[0]
        self.v_dd = self._entry_with_help(frm, 1, "DD", "dd")
        self.v_dl = self._entry_with_help(frm, 2, "DL", "dl")
        ttk.Label(frm, text="Crecimiento anual").grid(row=3, column=0, sticky="w", pady=3)
        self.v_growth = tk.StringVar(value="0.00")
        ttk.Label(frm, textvariable=self.v_growth, foreground="#0b5394", font=("Segoe UI", 10, "bold")).grid(row=3, column=1, sticky="w", pady=3)
        ttk.Label(frm, text="%").grid(row=3, column=2, sticky="w", padx=(6, 2))
        ttk.Button(frm, text="?", width=3, command=lambda: self.show_help("growth")).grid(row=3, column=3, sticky="w")
        ttk.Button(frm, text="Definir crecimiento", command=self.on_growth_dialog).grid(row=3, column=4, sticky="w")

        ttk.Label(frm, text="Años de diseño").grid(row=5, column=0, sticky="w")
        self.v_years = tk.StringVar()
        ttk.Entry(frm, textvariable=self.v_years).grid(row=5, column=1, sticky="ew")

        self.v_class_input_mode = tk.StringVar(value="share_pct")
        ttk.Radiobutton(frm, text="Entrada por % participación", variable=self.v_class_input_mode, value="share_pct", command=self._update_traffic_mode_ui).grid(row=7, column=0, columnspan=2, sticky="w")
        ttk.Radiobutton(frm, text="Entrada por tránsito (veh/día)", variable=self.v_class_input_mode, value="count", command=self._update_traffic_mode_ui).grid(row=7, column=2, columnspan=2, sticky="w")

        cls = ttk.LabelFrame(content, text="Clasificación vehicular (activar/desactivar por tipo)", padding=10)
        cls.pack(fill="both", expand=True, pady=(10, 0))
        grid_holder = ttk.Frame(cls)
        grid_holder.pack(fill="both", expand=True)
        self.traffic_table_canvas = tk.Canvas(grid_holder, highlightthickness=0)
        sc = ttk.Scrollbar(grid_holder, orient="vertical", command=self.traffic_table_canvas.yview)
        table = ttk.Frame(self.traffic_table_canvas)
        table.bind("<Configure>", lambda e: self.traffic_table_canvas.configure(scrollregion=self.traffic_table_canvas.bbox("all")))
        table_window = self.traffic_table_canvas.create_window((0, 0), window=table, anchor="nw")
        self.traffic_table_canvas.bind("<Configure>", lambda e: self.traffic_table_canvas.itemconfigure(table_window, width=e.width))
        self.traffic_table_canvas.configure(yscrollcommand=sc.set)
        self.traffic_table_canvas.pack(side="left", fill="both", expand=True)
        sc.pack(side="right", fill="y")
        self._bind_mousewheel(self.traffic_table_canvas)

        traffic_img = self._load_ui_image("traffic_banner", subsample=2)
        if traffic_img:
            ttk.Label(content, image=traffic_img).pack(anchor="e", pady=(6, 0))
        else:
            ttk.Label(content, text="[Imagen tipos de vehículos: sources/images/traffic_types.png]", foreground="#666").pack(anchor="e", pady=(6, 0))

        headers = ["Usar", "Nomenclatura", "Participación %", "Tránsito (veh/día)", "EALF"]
        for c in range(5):
            table.columnconfigure(c, weight=1)
        for i, h in enumerate(headers):
            ttk.Label(table, text=h).grid(row=0, column=i, sticky="w")

        self.class_rows = []
        self.share_entries = []
        self.count_entries = []
        for i in range(13):
            en = tk.BooleanVar(value=True)
            name_v = tk.StringVar()
            share_v = tk.StringVar()
            count_v = tk.StringVar()
            ealf_v = tk.StringVar()
            ttk.Checkbutton(table, variable=en).grid(row=i + 1, column=0, sticky="w")
            ttk.Entry(table, textvariable=name_v, width=12).grid(row=i + 1, column=1, sticky="ew", padx=2, pady=2)
            e_share = ttk.Entry(table, textvariable=share_v, width=10)
            e_share.grid(row=i + 1, column=2, sticky="ew", padx=2, pady=2)
            e_count = ttk.Entry(table, textvariable=count_v, width=12)
            e_count.grid(row=i + 1, column=3, sticky="ew", padx=2, pady=2)
            ttk.Entry(table, textvariable=ealf_v, width=10).grid(row=i + 1, column=4, sticky="ew", padx=2, pady=2)
            self.class_rows.append((en, name_v, share_v, count_v, ealf_v))
            self.share_entries.append(e_share)
            self.count_entries.append(e_count)
            count_v.trace_add("write", self._auto_update_aadt_from_counts)
            en.trace_add("write", self._auto_update_aadt_from_counts)

        actions = ttk.Frame(content)
        actions.pack(fill="x", pady=(8, 0))
        ttk.Button(actions, text="Calcular ESALs", command=self.on_calculate_esals).pack(side="left")

        self.v_esal_warn = tk.StringVar(value="")
        ttk.Label(actions, textvariable=self.v_esal_warn, foreground="#b00020", font=("Segoe UI", 10, "bold")).pack(side="left", padx=12)

        box = ttk.LabelFrame(content, text="Ejes equivalentes acumulados W18", padding=10)
        box.pack(fill="x", pady=(10, 0))
        self.v_w18_traffic = tk.StringVar(value="0")
        ttk.Label(box, textvariable=self.v_w18_traffic, foreground="#0b5394", font=("Segoe UI", 22, "bold")).pack(anchor="center")

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

        def er(r, t, v, key, u=""):
            ttk.Label(frm, text=t).grid(row=r, column=0, sticky="w", pady=3)
            ttk.Entry(frm, textvariable=v).grid(row=r, column=1, sticky="ew", pady=3)
            ttk.Label(frm, text=u).grid(row=r, column=2, sticky="w")
            ttk.Button(frm, text="?", width=3, command=lambda k=key: self.show_help(k)).grid(row=r, column=3, sticky="w")

        er(0, "a1", self.v_a1, "a1")
        er(1, "a2", self.v_a2, "a2")
        er(2, "a3", self.v_a3, "a3")
        er(3, "m2", self.v_m2, "m2")
        er(4, "m3", self.v_m3, "m3")
        er(5, "SN1 objetivo", self.v_sn1, "sn1")
        er(6, "SN2 objetivo", self.v_sn2, "sn2")
        er(7, "SN3 objetivo", self.v_sn3, "sn3")

        ttk.Label(self.tab_layers, text="SN1, SN2 y SN3 objetivo son ingresados por el usuario para el método secuencial.", foreground="#444").pack(anchor="w", pady=(8, 0))

    def _build_tab_calc_esals(self):
        body = ttk.Frame(self.tab_calc_esals)
        body.pack(fill="both", expand=True)
        self.txt_calc_esals = tk.Text(body, height=30, wrap="word")
        sc = ttk.Scrollbar(body, orient="vertical", command=self.txt_calc_esals.yview)
        self.txt_calc_esals.configure(yscrollcommand=sc.set)
        self.txt_calc_esals.pack(side="left", fill="both", expand=True)
        sc.pack(side="right", fill="y")
        self._bind_mousewheel(self.txt_calc_esals)
        self.txt_calc_esals.configure(state="disabled")

    def _build_tab_calc_thickness(self):
        body = ttk.Frame(self.tab_calc_thickness)
        body.pack(fill="both", expand=True)
        self.txt_calc_thickness = tk.Text(body, height=30, wrap="word")
        sc = ttk.Scrollbar(body, orient="vertical", command=self.txt_calc_thickness.yview)
        self.txt_calc_thickness.configure(yscrollcommand=sc.set)
        self.txt_calc_thickness.pack(side="left", fill="both", expand=True)
        sc.pack(side="right", fill="y")
        self._bind_mousewheel(self.txt_calc_thickness)
        self.txt_calc_thickness.configure(state="disabled")

    def _build_tab_results(self):
        body = ttk.Frame(self.tab_results)
        body.pack(fill="both", expand=True)
        self.txt = tk.Text(body, height=24, wrap="word")
        sc = ttk.Scrollbar(body, orient="vertical", command=self.txt.yview)
        self.txt.configure(yscrollcommand=sc.set)
        self.txt.pack(side="left", fill="both", expand=True)
        sc.pack(side="right", fill="y")
        self._bind_mousewheel(self.txt)
        self.txt.configure(state="disabled")

    def _build_tab_costs(self):
        frm = ttk.LabelFrame(self.tab_costs, text="Parámetros de costo por m³", padding=12)
        frm.pack(fill="x")
        for c in range(4):
            frm.columnconfigure(c, weight=1 if c == 1 else 0)

        self.v_width = tk.StringVar()
        self.v_cost_d1 = tk.StringVar()
        self.v_cost_d2 = tk.StringVar()
        self.v_cost_d3 = tk.StringVar()

        def row(r, lbl, var, unit, key):
            ttk.Label(frm, text=lbl).grid(row=r, column=0, sticky="w", pady=3)
            ttk.Entry(frm, textvariable=var).grid(row=r, column=1, sticky="ew", pady=3)
            ttk.Label(frm, text=unit).grid(row=r, column=2, sticky="w")
            ttk.Button(frm, text="?", width=3, command=lambda k=key: self.show_help(k)).grid(row=r, column=3, sticky="w")

        row(0, "Ancho de corona", self.v_width, "m", "width")
        row(1, "Costo carpeta", self.v_cost_d1, "$/m³", "cost_d1")
        row(2, "Costo base", self.v_cost_d2, "$/m³", "cost_d2")
        row(3, "Costo subbase", self.v_cost_d3, "$/m³", "cost_d3")

        btnf = ttk.Frame(self.tab_costs)
        btnf.pack(fill="x", pady=(8,0))
        ttk.Button(btnf, text="Calcular costos", command=self.on_calculate_costs).pack(side="left")

        body = ttk.Frame(self.tab_costs)
        body.pack(fill="both", expand=True, pady=(10, 0))
        self.txt_cost = tk.Text(body, height=16, wrap="word")
        sc = ttk.Scrollbar(body, orient="vertical", command=self.txt_cost.yview)
        self.txt_cost.configure(yscrollcommand=sc.set)
        self.txt_cost.pack(side="left", fill="both", expand=True)
        sc.pack(side="right", fill="y")
        self._bind_mousewheel(self.txt_cost)
        self.txt_cost.configure(state="disabled")

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

    def _build_tab_legal(self):
        body = ttk.Frame(self.tab_legal)
        body.pack(fill="both", expand=True)
        txt = tk.Text(body, height=22, wrap="word")
        sc = ttk.Scrollbar(body, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sc.set)
        txt.pack(side="left", fill="both", expand=True)
        sc.pack(side="right", fill="y")
        self._bind_mousewheel(txt)

        legal = []
        legal.append("AVISO LEGAL Y ACADÉMICO\n\n")
        legal.append("El presente software ha sido desarrollado exclusivamente con fines educativos, académicos y de apoyo técnico dentro de las actividades del Laboratorio de Pavimentos de la Escuela Superior de Ingeniería y Arquitectura (ESIA), Unidad Zacatenco, del Instituto Politécnico Nacional.\n\n")
        legal.append("Su desarrollo contó con el apoyo de herramientas de Inteligencia Artificial (IA) como medio auxiliar de programación y estructuración. No obstante, los resultados generados por el sistema constituyen únicamente estimaciones basadas en los datos proporcionados por el usuario y en los modelos implementados.\n\n")
        legal.append("El uso de esta herramienta es responsabilidad total del usuario. En ningún caso el desarrollador, el Laboratorio de Pavimentos, la ESIA, el Instituto Politécnico Nacional, ni el Ing. José Santos Arriaga Soto serán responsables por errores de cálculo, interpretaciones incorrectas, decisiones de diseño, fallas en obra o cualquier daño directo o indirecto derivado del uso del software.\n\n")
        legal.append("Antes de su aplicación en proyectos reales, obra civil o toma de decisiones técnicas, el usuario deberá verificar, validar y, en su caso, recalcular los resultados conforme a la normativa vigente aplicable (SICT, AASHTO, ASTM u otras que correspondan).\n\n")
        legal.append("El software se proporciona “tal cual” (AS IS), sin garantías explícitas ni implícitas de exactitud, integridad, comerciabilidad o idoneidad para un propósito particular.\n\n")
        legal.append("El uso de este programa implica la aceptación plena de los términos aquí establecidos.\n")

        txt.insert("1.0", "".join(legal))
        txt.configure(state="disabled")

    def _load_to_form(self):
        t = self.data["traffic"]; a = self.data["aashto"]; l = self.data["layers"]
        self.v_aadt.set(str(t["aadt_total"])); self.v_dd.set(str(t["dd"])); self.v_dl.set(str(t["dl"]))
        self.v_growth.set(f"{float(t['growth_pct']):.4f}"); self.v_years.set(str(t["design_years"])); self.v_class_input_mode.set(t.get("class_input_mode", "share_pct"))
        for idx, row in enumerate(t.get("truck_classes", [])):
            if idx < len(self.class_rows):
                en, n, s_v, c_v, e = self.class_rows[idx]
                en.set(bool(row.get("enabled", True))); n.set(str(row.get("name", ""))); s_v.set(str(row.get("share_pct", ""))); c_v.set(str(row.get("count", ""))); e.set(f"{float(row.get('ealf',0.0)):.4f}")
        self.v_rel.set(str(a["reliability_pct"])); self.v_so.set(str(a["so"])); self.v_pi.set(str(a["pi"])); self.v_pt.set(str(a["pt"])); self.v_mr.set(str(a["mr_mpa"]))
        self.v_a1.set(str(l["a1"])); self.v_a2.set(str(l["a2"])); self.v_a3.set(str(l["a3"])); self.v_m2.set(str(l["m2"])); self.v_m3.set(str(l["m3"])); self.v_sn1.set(str(l["sn1_target"])); self.v_sn2.set(str(l["sn2_target"])); self.v_sn3.set(str(l["sn3_target"]))
        c = self.data["prelim_costs"]
        self.v_width.set(str(c.get("width_m", 12.0))); self.v_cost_d1.set(str(c.get("cost_d1", 0.0))); self.v_cost_d2.set(str(c.get("cost_d2", 0.0))); self.v_cost_d3.set(str(c.get("cost_d3", 0.0))
)
        self._update_traffic_mode_ui()

    def _read_form_to_data(self):
        t = self.data["traffic"]; a = self.data["aashto"]; l = self.data["layers"]
        t["aadt_total"] = float(self.v_aadt.get()); t["pct_trucks"] = 100.0; t["dd"] = float(self.v_dd.get()); t["dl"] = float(self.v_dl.get())
        t["growth_pct"] = float(self.v_growth.get()); t["design_years"] = int(float(self.v_years.get())); t["class_input_mode"] = self.v_class_input_mode.get()
        classes = []
        for en, n, s_v, c_v, e in self.class_rows:
            if n.get().strip() or s_v.get().strip() or c_v.get().strip() or e.get().strip():
                classes.append({"enabled": bool(en.get()), "name": n.get().strip() or "Clase", "share_pct": float(s_v.get() or 0), "count": float(c_v.get() or 0), "ealf": float(e.get() or 0)})
        t["truck_classes"] = classes
        if t.get("class_input_mode") == "count":
            t["aadt_total"] = sum(r["count"] for r in classes if r["enabled"])
            self.v_aadt.set(str(t["aadt_total"]))
        a["reliability_pct"] = float(self.v_rel.get()); a["so"] = float(self.v_so.get()); a["pi"] = float(self.v_pi.get()); a["pt"] = float(self.v_pt.get()); a["mr_mpa"] = float(self.v_mr.get())
        l["a1"] = float(self.v_a1.get()); l["a2"] = float(self.v_a2.get()); l["a3"] = float(self.v_a3.get()); l["m2"] = float(self.v_m2.get()); l["m3"] = float(self.v_m3.get())
        l["sn1_target"] = float(self.v_sn1.get()); l["sn2_target"] = float(self.v_sn2.get()); l["sn3_target"] = float(self.v_sn3.get())
        c = self.data["prelim_costs"]
        c["width_m"] = float(self.v_width.get()); c["cost_d1"] = float(self.v_cost_d1.get()); c["cost_d2"] = float(self.v_cost_d2.get()); c["cost_d3"] = float(self.v_cost_d3.get())
        self._validate_ranges()


    def _auto_update_aadt_from_counts(self, *_):
        if getattr(self, "v_class_input_mode", None) is None:
            return

        total = 0.0
        is_count = self.v_class_input_mode.get() == "count"
        for en, _, _, c_v, e_v in self.class_rows:
            if not en.get():
                c_v.set("0")
                e_v.set("0")
                continue
            if is_count:
                try:
                    total += float(c_v.get() or 0)
                except Exception:
                    pass

        if is_count:
            self.v_aadt.set(f"{total:.2f}")

    def _update_traffic_mode_ui(self):
        mode = self.v_class_input_mode.get()
        is_count = mode == "count"
        self.e_aadt.configure(state="readonly" if is_count else "normal")
        for e in self.share_entries:
            e.configure(state="disabled" if is_count else "normal")
        for e in self.count_entries:
            e.configure(state="normal" if is_count else "disabled")
        self._auto_update_aadt_from_counts()

    def _validate_ranges(self):
        t = self.data["traffic"]; a = self.data["aashto"]; v = self.data["validation"]
        if t["growth_pct"] < 0:
            raise ValueError("La tasa de crecimiento debe ser >= 0")

        checks = [
            ("TPDA", t["aadt_total"], v["aadt_min"], v["aadt_max"], "Ajusta TPDA o cambia rango en Opciones."),
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
        txt = HELP_TEXTS.get(key, "Ayuda no disponible.")
        img_key = HELP_IMAGE_KEYS.get(key)
        if not img_key:
            messagebox.showinfo("Ayuda", txt)
            return

        win = tk.Toplevel(self.root)
        win.title(f"Ayuda: {key}")
        win.geometry("760x520")
        win.transient(self.root)

        frm = ttk.Frame(win, padding=10)
        frm.pack(fill="both", expand=True)
        ttk.Label(frm, text=txt, wraplength=720, justify="left").pack(anchor="w", pady=(0, 8))

        img = self._load_ui_image(img_key, subsample=1)
        if img:
            lbl = ttk.Label(frm, image=img)
            lbl.pack(anchor="center", fill="both", expand=True)
        else:
            ph = f"No se encontró la imagen de ayuda. Colócala en: {UI_IMAGE_PATHS.get(img_key)}"
            ttk.Label(frm, text=ph, foreground="#666", wraplength=720, justify="left").pack(anchor="w")


    def on_growth_dialog(self):
        win = tk.Toplevel(self.root)
        win.title("Definir crecimiento")
        win.geometry("620x320")
        win.transient(self.root)
        win.grab_set()

        ttk.Label(
            win,
            text=(
                "Si tienes el factor de crecimiento ingrésalo manualmente. "
                "Si no, calcula con TA (tránsito año actual), TP (tránsito año previo) y N (años entre aforos)."
            ),
            wraplength=580,
            justify="left",
        ).pack(anchor="w", padx=12, pady=(12, 8))

        mode = tk.StringVar(value="manual")
        frm = ttk.Frame(win, padding=12)
        frm.pack(fill="both", expand=True)

        manual_pct = tk.StringVar(value=self.v_growth.get() or "0")
        ta_v = tk.StringVar(value="")
        tp_v = tk.StringVar(value="")
        n_v = tk.StringVar(value="")
        calc_result = tk.StringVar(value="")

        ttk.Radiobutton(frm, text="Ingresar porcentaje manual", variable=mode, value="manual").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, textvariable=manual_pct, width=12).grid(row=0, column=1, sticky="w", padx=(8, 4))
        ttk.Label(frm, text="%").grid(row=0, column=2, sticky="w")

        ttk.Radiobutton(frm, text="Calcular con aforos", variable=mode, value="formula").grid(row=1, column=0, sticky="w", pady=(12, 4))
        ttk.Label(frm, text="TA").grid(row=2, column=0, sticky="w")
        ttk.Entry(frm, textvariable=ta_v, width=16).grid(row=2, column=1, sticky="w")
        ttk.Label(frm, text="TP").grid(row=3, column=0, sticky="w")
        ttk.Entry(frm, textvariable=tp_v, width=16).grid(row=3, column=1, sticky="w")
        ttk.Label(frm, text="N").grid(row=4, column=0, sticky="w")
        ttk.Entry(frm, textvariable=n_v, width=16).grid(row=4, column=1, sticky="w")
        ttk.Label(frm, text="r=(TA/TP)^(1/N) y crecimiento(%)=(r-1)*100", foreground="#444").grid(row=5, column=0, columnspan=3, sticky="w", pady=(4, 0))
        ttk.Label(frm, textvariable=calc_result, foreground="#0b5394").grid(row=6, column=0, columnspan=3, sticky="w", pady=(4, 0))

        def apply_growth_value():
            try:
                if mode.get() == "manual":
                    g = float(manual_pct.get())
                else:
                    ta = float(ta_v.get())
                    tp = float(tp_v.get())
                    n = float(n_v.get())
                    if ta <= 0 or tp <= 0 or n <= 0:
                        raise ValueError("TA, TP y N deben ser > 0")
                    r = (ta / tp) ** (1.0 / n)
                    g = (r - 1.0) * 100.0
                    calc_result.set(f"r = {r:.6f} | crecimiento = {g:.4f}%")
                self.v_growth.set(f"{g:.4f}")
                win.destroy()
            except Exception as e:
                messagebox.showerror("Crecimiento", f"No se pudo guardar el crecimiento\n{e}")

        btns = ttk.Frame(win, padding=12)
        btns.pack(fill="x")
        ttk.Button(btns, text="Guardar", command=apply_growth_value).pack(side="right")
        ttk.Button(btns, text="Cancelar", command=win.destroy).pack(side="right", padx=8)

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
        self._bind_mousewheel(canvas)

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
        self._write_text(self.txt_calc_esals, "")
        self._write_text(self.txt_calc_thickness, "")

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

    def _compute_traffic_load(self):
        t = self.data["traffic"]
        mode = t.get("class_input_mode", "share_pct")
        result = compute_esals_detailed(
            vehicle_classes=t.get("truck_classes", []),
            mode=mode,
            tpda_total=t["aadt_total"],
            dd=t["dd"],
            dl=t["dl"],
            growth_pct=t["growth_pct"],
            years=t["design_years"],
        )
        return result["W18"], result



    def _format_esal_breakdown(self, esal_detail: dict) -> str:
        lines = []
        lines.append("DESGLOSE COMPLETO DE CÁLCULO ESAL\n\n")
        lines.append("1) Parámetros globales\n")
        lines.append(f"- Factor B: {esal_detail.get('B', 0):.6f}\n")
        lines.append(f"- ΣESAL: {esal_detail.get('sum_esal', 0):,.4f}\n")
        lines.append(f"- W18: {esal_detail.get('W18', 0):,.4f}\n")
        if esal_detail.get("mode") == "share_pct":
            lines.append(f"- Suma participación: {esal_detail.get('total_share_pct', 0):.4f}%\n")
        lines.append("\n2) Cálculo por tipo\n")
        lines.append("Tipo            ADT_i          EALF            ESAL_i\n")
        lines.append("-" * 62 + "\n")
        for r in esal_detail.get("rows", []):
            lines.append(f"{r['name']:<12}{r['ADT_i']:>12,.4f}{r['ealf']:>14,.4f}{r['ESAL_i']:>24,.4f}\n")
        lines.append("\n3) Fórmulas usadas\n")
        lines.append("- ADT_i (modo %): TPDA * (%Participación_i/100).\n")
        lines.append("- ADT_i (modo tránsito): Tránsito_i capturado.\n")
        lines.append("- ESAL_i = ADT_i * EALF_i * 365 * B.\n")
        lines.append("- ΣESAL = suma de ESAL_i.\n")
        lines.append("- W18 = ΣESAL * DD * DL.\n")
        return "".join(lines)

    def on_calculate_esals(self):
        try:
            self._read_form_to_data()
            w18, esal_detail = self._compute_traffic_load()
            self.data.setdefault("results", {})["W18"] = w18
            self.data["results"]["ESAL_detail"] = esal_detail
            self.v_w18_traffic.set(f"{w18:,.0f}")
            self._write_text(self.txt_calc_esals, self._format_esal_breakdown(esal_detail))
            self.v_esal_warn.set("⚠ Solo se han calculado ESALs. Ejecuta 'Calcular' para actualizar espesores.")
            self.nb.select(self.tab_calc_esals)
            messagebox.showwarning("ESALs", "Solo se calculó tránsito/ESALs. Ejecuta 'Calcular' para actualizar espesores y costos.")
        except Exception as e:
            messagebox.showerror("ESALs", f"No se pudo calcular ESALs:\n{e}")

    def _compute_costs(self, calc: dict, mins: dict):
        cst = self.data["prelim_costs"]
        width = cst["width_m"]
        v1 = (calc["D1_in"] * 0.0254) * width * 1000
        v2 = (calc["D2_in"] * 0.0254) * width * 1000
        v3 = (calc["D3_in"] * 0.0254) * width * 1000
        calc_cost = v1*cst["cost_d1"] + v2*cst["cost_d2"] + v3*cst["cost_d3"]
        m1 = (mins["D1_in"] * 0.0254) * width * 1000
        m2 = (mins["D2_in"] * 0.0254) * width * 1000
        m3 = (mins["D3_in"] * 0.0254) * width * 1000
        min_cost = m1*cst["cost_d1"] + m2*cst["cost_d2"] + m3*cst["cost_d3"]
        return {
            "width_m": width,
            "calculated": {"vol_d1": v1, "vol_d2": v2, "vol_d3": v3, "cost_d1": v1*cst["cost_d1"], "cost_d2": v2*cst["cost_d2"], "cost_d3": v3*cst["cost_d3"], "total": calc_cost},
            "minimums": {"vol_d1": m1, "vol_d2": m2, "vol_d3": m3, "cost_d1": m1*cst["cost_d1"], "cost_d2": m2*cst["cost_d2"], "cost_d3": m3*cst["cost_d3"], "total": min_cost},
        }

    def on_calculate_costs(self):
        try:
            self._read_form_to_data()
            rs = self.data.get("results", {})
            calc = rs.get("calculated")
            mins = rs.get("with_minimums")
            if not calc or not mins:
                messagebox.showwarning("Costos", "Primero ejecuta 'Calcular' para obtener espesores.")
                return
            costs = self._compute_costs(calc, mins)
            self.data["results"]["costs"] = costs
            self._write_text(self.txt_cost, self._build_costs_text(costs))
            self.nb.select(self.tab_costs)
        except Exception as e:
            messagebox.showerror("Costos", f"No se pudo calcular costos:\n{e}")

    def on_calculate(self):
        try:
            self._read_form_to_data()
            t = self.data["traffic"]; a = self.data["aashto"]; l = self.data["layers"]
            w18, esal_detail = self._compute_traffic_load()
            sn3_aashto, zr = solve_sn_required(w18=w18, reliability_pct=a["reliability_pct"], so=a["so"], pi=a["pi"], pt=a["pt"], mr_mpa=a["mr_mpa"])
            sn3_target = l["sn3_target"]

            calc = design_thicknesses_sequential(
                sn1_target=l["sn1_target"], sn2_target=l["sn2_target"], sn3_target=sn3_target,
                a1=l["a1"], a2=l["a2"], a3=l["a3"], m2=l["m2"], m3=l["m3"],
            )
            mins = apply_minimums_sequential(calc, w18, l["a1"], l["a2"], l["a3"], l["m2"], l["m3"], sn3_target, self.data.get("minimums_table"))

            costs = self._compute_costs(calc, mins)

            self.data["results"] = {"W18": w18, "SN3_target": sn3_target, "SN3_aashto": sn3_aashto, "Zr": zr, "ESAL_detail": esal_detail, "calculated": calc, "with_minimums": mins, "costs": costs}
            self.v_w18_traffic.set(f"{w18:,.0f}")
            self.v_esal_warn.set("")

            out = []
            out.append("RESULTADOS FINALES DE ESPESORES\n\n")
            out.append("A) Espesores calculados (sin mínimos)\n")
            out.append(f"- D1: {fnum(calc['D1_in'],2)} in | {fnum(calc['D1_cm'],2)} cm\n")
            out.append(f"- D2: {fnum(calc['D2_in'],2)} in | {fnum(calc['D2_cm'],2)} cm\n")
            out.append(f"- D3: {fnum(calc['D3_in'],2)} in | {fnum(calc['D3_cm'],2)} cm\n")
            out.append(f"- SN total corregido: {fnum(calc['SN_sum'],3)}\n\n")
            out.append("B) Espesores con mínimos sugeridos\n")
            out.append(f"- D1: {fnum(mins['D1_in'],2)} in | {fnum(mins['D1_cm'],2)} cm\n")
            out.append(f"- D2: {fnum(mins['D2_in'],2)} in | {fnum(mins['D2_cm'],2)} cm\n")
            out.append(f"- D3: {fnum(mins['D3_in'],2)} in | {fnum(mins['D3_cm'],2)} cm\n")
            out.append(f"- SN total corregido: {fnum(mins['SN_sum'],3)}\n")
            out.append(f"- Rango de mínimos aplicado: {mins['minimum_table']['range_label']}\n")
            self._write_text(self.txt, "".join(out))
            self._write_text(self.txt_calc_esals, self._format_esal_breakdown(esal_detail))
            self._write_text(self.txt_calc_thickness, self._build_calculos_text(calc, mins, l, sn3_target))
            self._draw_sections(calc, mins)
            self._write_text(self.txt_cost, self._build_costs_text(costs))
            self.nb.select(self.tab_results)

        except Exception as e:
            messagebox.showerror("Error de cálculo", f"No se puede calcular:\n{e}\n\nPosibles soluciones:\n- Revisa rangos en Opciones\n- Verifica SN1 <= SN2 <= SN3\n- Revisa coeficientes a y m")

    def _build_calculos_text(self, calc, mins, l, sn3):
        lines = []
        lines.append("DESGLOSE DE CÁLCULOS\n\n")
        lines.append("A) ESPESORES CALCULADOS\n")
        lines.append(f"D1 = SN1/A1 = {calc['SN1_target']:,.3f}/{l['a1']:,.3f} = {calc['D1_raw_in']:,.3f} in\n")
        lines.append(f"D1 redondeado (0.5 más cercana) = {calc['D1_in']:,.2f} in\n")
        lines.append(f"SN1* = D1red*A1 = {calc['D1_in']:,.2f}*{l['a1']:,.3f} = {calc['SN1_star']:,.3f}\n\n")
        lines.append(f"D2 = (SN2-SN1*)/(A2*M2) = ({calc['SN2_target']:,.3f}-{calc['SN1_star']:,.3f})/({l['a2']:,.3f}*{l['m2']:,.3f}) = {calc['D2_raw_in']:,.3f} in\n")
        lines.append(f"D2 redondeado (0.5 hacia arriba) = {calc['D2_in']:,.2f} in\n")
        lines.append(f"SN2* = D2red*A2*M2 = {calc['D2_in']:,.2f}*{l['a2']:,.3f}*{l['m2']:,.3f} = {calc['SN2_star']:,.3f}\n\n")
        lines.append(f"D3 = (SN3-(SN1*+SN2*))/(A3*M3) = ({sn3:,.3f}-({calc['SN1_star']:,.3f}+{calc['SN2_star']:,.3f}))/({l['a3']:,.3f}*{l['m3']:,.3f}) = {calc['D3_raw_in']:,.3f} in\n")
        lines.append(f"D3 redondeado (0.5 hacia arriba) = {calc['D3_in']:,.2f} in\n")
        lines.append(f"SN3* = D3red*A3*M3 = {calc['D3_in']:,.2f}*{l['a3']:,.3f}*{l['m3']:,.3f} = {calc['SN3_star']:,.3f}\n")
        lines.append(f"Comprobación suma: SN1*+SN2*+SN3* = {calc['SN_sum']:,.3f}\n")
        lines.append("\n")
        lines.append(f"Criterio estructural (>=SN3): {calc['SN_sum']:,.3f} >= {sn3:,.3f} -> {calc['criterion_meets_or_exceeds']}\n\n")

        lines.append("B) AJUSTE CON MÍNIMOS\n")
        lines.append(f"Tabla 7-2 aplicada: {mins['minimum_table']['range_label']}\n")
        lines.append(f"D1 ajustado = D1_min(opciones) = {mins['minimum_table']['D1_min_in']:,.2f} in -> {mins['D1_in']:,.2f} in\n")
        lines.append(f"D2 ajustado = D2_min(opciones) = {mins['minimum_table']['D2_min_in']:,.2f} in -> {mins['D2_in']:,.2f} in\n")
        lines.append(f"SN1*min = D1_adj*A1 = {mins['SN1_star']:,.3f}\n")
        lines.append(f"SN2*min = D2_adj*A2*M2 = {mins['SN2_star']:,.3f}\n")
        lines.append(f"D3_min = (SN3-(SN1*min+SN2*min))/(A3*M3) = {mins['D3_raw_in']:,.3f} in\n")
        lines.append(f"D3 redondeado (0.5 hacia arriba) = {mins['D3_in']:,.2f} in\n")
        lines.append(f"SN3*min = {mins['SN3_star']:,.3f}\n")
        lines.append(f"Comprobación suma mínima: {mins['SN_sum']:,.3f}\n")
        return "".join(lines)


    def _build_costs_text(self, costs: dict) -> str:
        c = self.data["prelim_costs"]
        lines = []
        lines.append("COSTOS PRELIMINARES POR KILÓMETRO\n\n")
        lines.append(f"Ancho de corona: {costs['width_m']:,.2f} m\n")
        lines.append(f"Costo carpeta: {c['cost_d1']:,.2f} $/m³ | base: {c['cost_d2']:,.2f} $/m³ | subbase: {c['cost_d3']:,.2f} $/m³\n\n")

        lines.append("1) Solución calculada\n")
        lines.append(f"- Carpeta: Vol {costs['calculated']['vol_d1']:,.2f} m³/km | Costo {costs['calculated']['cost_d1']:,.2f} $/km\n")
        lines.append(f"- Base: Vol {costs['calculated']['vol_d2']:,.2f} m³/km | Costo {costs['calculated']['cost_d2']:,.2f} $/km\n")
        lines.append(f"- Subbase: Vol {costs['calculated']['vol_d3']:,.2f} m³/km | Costo {costs['calculated']['cost_d3']:,.2f} $/km\n")
        lines.append(f"- Costo total: {costs['calculated']['total']:,.2f} $/km\n\n")

        lines.append("2) Solución con mínimos\n")
        lines.append(f"- Carpeta: Vol {costs['minimums']['vol_d1']:,.2f} m³/km | Costo {costs['minimums']['cost_d1']:,.2f} $/km\n")
        lines.append(f"- Base: Vol {costs['minimums']['vol_d2']:,.2f} m³/km | Costo {costs['minimums']['cost_d2']:,.2f} $/km\n")
        lines.append(f"- Subbase: Vol {costs['minimums']['vol_d3']:,.2f} m³/km | Costo {costs['minimums']['cost_d3']:,.2f} $/km\n")
        lines.append(f"- Costo total: {costs['minimums']['total']:,.2f} $/km\n")
        return "".join(lines)

    def _draw_one_section(self, canvas, d1, d2, d3, sn1, sn2, sn3, mr_mpa):
        canvas.delete("all")
        total = max(d1 + d2 + d3, 0.1)
        scale = 420 / total
        x1, x2, y = 70, 430, 40
        layers = [
            ("Carpeta", d1, sn1, "#474fa8"),
            ("Base", d2, sn2, "#d1b06e"),
            ("Subbase", d3, sn3, "#a0b370"),
        ]
        for name, thk, sn_star, color in layers:
            h = thk * scale
            canvas.create_rectangle(x1, y, x2, y + h, fill=color, outline="black")
            canvas.create_text(
                (x1 + x2) / 2,
                y + h / 2,
                text=f"{name}: {thk:.2f} in / {thk*2.54:.1f} cm | SN*: {sn_star:.3f}",
                fill="white",
            )
            y += h
        canvas.create_rectangle(x1, y, x2, y + 70, fill="#9c7d5f", outline="black")
        canvas.create_text((x1 + x2) / 2, y + 35, text=f"Subrasante | Mr: {mr_mpa:.1f} MPa", fill="white")

    def _draw_sections(self, calc, mins):
        mr = self.data.get("aashto", {}).get("mr_mpa", 0.0)
        self._draw_one_section(self.canvas_calc, calc["D1_in"], calc["D2_in"], calc["D3_in"], calc["SN1_star"], calc["SN2_star"], calc["SN3_star"], mr)
        self._draw_one_section(self.canvas_min, mins["D1_in"], mins["D2_in"], mins["D3_in"], mins["SN1_star"], mins["SN2_star"], mins["SN3_star"], mr)

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
            t = self.data["traffic"]
            a = self.data["aashto"]
            l = self.data["layers"]
            calc = rs["calculated"]
            mins = rs["with_minimums"]
            costs = rs.get("costs", {})

            c = canvas.Canvas(path, pagesize=letter)
            page_w, page_h = letter
            y = page_h - 36

            c.setFont("Helvetica-Bold", 13)
            c.drawString(36, y, "Reporte - Calculadora de Espesores por método AASHTO")
            y -= 22
            c.setFont("Helvetica", 9)

            data_lines = [
                f"Proyecto: {self.data.get('project', {}).get('name', 'N/A')}",
                f"TPDA: {t['aadt_total']:.2f} | DD: {t['dd']:.3f} | DL: {t['dl']:.3f}",
                f"Crecimiento: {t['growth_pct']:.4f}% | Años: {t['design_years']}",
                f"R: {a['reliability_pct']:.2f} | So: {a['so']:.3f} | Pi: {a['pi']:.3f} | Pt: {a['pt']:.3f} | Mr(MPa): {a['mr_mpa']:.3f}",
                f"a1:{l['a1']:,.3f} a2:{l['a2']:,.3f} a3:{l['a3']:,.3f} m2:{l['m2']:,.3f} m3:{l['m3']:,.3f}",
                f"SN1:{l['sn1_target']:.3f} SN2:{l['sn2_target']:.3f} SN3_obj:{l['sn3_target']:.3f} SN3_ref:{rs['SN3_aashto']:.3f}",
                f"W18: {rs['W18']:,.0f}",
                f"Costo calculada: {costs.get('calculated', {}).get('total', 0.0):.2f} $/km",
                f"Costo mínimos: {costs.get('minimums', {}).get('total', 0.0):.2f} $/km",
            ]
            for ln in data_lines:
                c.drawString(36, y, ln)
                y -= 13

            y -= 8
            c.setFont("Helvetica-Bold", 10)
            c.drawString(36, y, "Desglose de cálculos")
            y -= 14
            c.setFont("Helvetica", 8)
            for ln in self._build_calculos_text(calc, mins, l, l['sn3_target']).splitlines():
                if y < 80:
                    c.showPage()
                    y = page_h - 36
                    c.setFont("Helvetica", 8)
                c.drawString(36, y, ln[:140])
                y -= 10

            def draw_section_pdf(x, y_top, d1, d2, d3, title):
                c.setFont("Helvetica-Bold", 9)
                c.drawString(x, y_top + 8, title)
                total = max(d1 + d2 + d3, 0.1)
                scale = 120 / total
                w = 160
                y = y_top - 2
                for name, thk, color in [("Carpeta", d1, (0.28, 0.31, 0.66)), ("Base", d2, (0.82, 0.69, 0.43)), ("Subbase", d3, (0.63, 0.70, 0.44))]:
                    h = thk * scale
                    r,g,b = color
                    c.setFillColorRGB(r,g,b)
                    c.rect(x, y - h, w, h, fill=1, stroke=1)
                    c.setFillColorRGB(1,1,1)
                    c.drawString(x + 4, y - h/2, f"{name}: {thk:.2f} in")
                    y -= h
                c.setFillColorRGB(0.61,0.49,0.37)
                c.rect(x, y - 25, w, 25, fill=1, stroke=1)
                c.setFillColorRGB(1,1,1)
                c.drawString(x + 4, y - 14, "Subrasante")
                c.setFillColorRGB(0,0,0)

            if y < 220:
                c.showPage()
                y = page_h - 36
            y -= 20
            draw_section_pdf(36, y, calc['D1_in'], calc['D2_in'], calc['D3_in'], "Sección calculada")
            draw_section_pdf(240, y, mins['D1_in'], mins['D2_in'], mins['D3_in'], "Sección con mínimos")

            c.save()
            messagebox.showinfo("PDF", f"Reporte exportado:\n{path}")
        except Exception as e:
            messagebox.showerror("PDF", f"No se pudo generar PDF (requiere reportlab):\n{e}")

    def run(self):
        self.root.mainloop()
