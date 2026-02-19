import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from core.esals import calc_w18
from core.aashto93_flexible import solve_sn_required
from core.layers import recommend_thicknesses
from data_io.project_json import save_project, load_project


def fnum(x, nd=3):
    try:
        return f"{float(x):.{nd}f}"
    except Exception:
        return str(x)


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ASHTOO Flexible (AASHTO 93) - MVP")
        self.root.geometry("980x620")
        self.root.minsize(900, 560)

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
                "design_years": 20
            },
            "aashto": {
                "reliability_pct": 95.0,
                "so": 0.49,
                "pi": 4.2,
                "pt": 2.5,
                "mr_mpa": 70.0
            },
            "layers": {
                "a1": 0.44,
                "a2": 0.14,
                "a3": 0.11,
                "m2": 1.0,
                "m3": 1.0
            },
            "search": {
                "step_in": 0.5,
                "d1_fixed_cm": 10.0,
                "d2_min_cm": 10.0, "d2_max_cm": 40.0,
                "d3_min_cm": 10.0, "d3_max_cm": 50.0,
            },
            "results": {}
        }

    def _build_ui(self):
        # Top bar
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="ASHTOO Flexible (AASHTO 1993) — MVP", font=("Segoe UI", 14, "bold")).pack(side="left")

        btns = ttk.Frame(top)
        btns.pack(side="right")

        ttk.Button(btns, text="Nuevo", command=self.on_new).pack(side="left", padx=5)
        ttk.Button(btns, text="Abrir...", command=self.on_open).pack(side="left", padx=5)
        ttk.Button(btns, text="Guardar...", command=self.on_save).pack(side="left", padx=5)
        ttk.Button(btns, text="Calcular", command=self.on_calculate).pack(side="left", padx=5)

        # Notebook
        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_traffic = ttk.Frame(self.nb, padding=12)
        self.tab_aashto = ttk.Frame(self.nb, padding=12)
        self.tab_layers = ttk.Frame(self.nb, padding=12)
        self.tab_results = ttk.Frame(self.nb, padding=12)

        self.nb.add(self.tab_traffic, text="Tránsito / ESALs")
        self.nb.add(self.tab_aashto, text="Parámetros AASHTO")
        self.nb.add(self.tab_layers, text="Capas / Búsqueda")
        self.nb.add(self.tab_results, text="Resultados")

        self._build_tab_traffic()
        self._build_tab_aashto()
        self._build_tab_layers()
        self._build_tab_results()

        self._load_to_form()

    def _grid2(self, parent):
        parent.columnconfigure(0, weight=0)
        parent.columnconfigure(1, weight=1)
        parent.columnconfigure(2, weight=0)
        parent.columnconfigure(3, weight=1)

    def _entry_row(self, parent, r, label, var, unit="", col=0):
        ttk.Label(parent, text=label).grid(row=r, column=col, sticky="w", pady=4, padx=(0,8))
        e = ttk.Entry(parent, textvariable=var)
        e.grid(row=r, column=col+1, sticky="ew", pady=4)
        ttk.Label(parent, text=unit).grid(row=r, column=col+2, sticky="w", padx=(8,0))
        return e

    def _build_tab_traffic(self):
        frm = ttk.LabelFrame(self.tab_traffic, text="Datos de tránsito", padding=12)
        frm.pack(fill="x")
        self._grid2(frm)

        self.v_aadt = tk.StringVar()
        self.v_pct_trucks = tk.StringVar()
        self.v_dd = tk.StringVar()
        self.v_dl = tk.StringVar()
        self.v_tf = tk.StringVar()
        self.v_growth = tk.StringVar()
        self.v_years = tk.StringVar()

        self._entry_row(frm, 0, "TPDA total (AADT)", self.v_aadt, "veh/día", col=0)
        self._entry_row(frm, 1, "% pesados", self.v_pct_trucks, "%", col=0)
        self._entry_row(frm, 2, "DD (direccional)", self.v_dd, "-", col=0)
        self._entry_row(frm, 3, "DL (carril de diseño)", self.v_dl, "-", col=0)
        self._entry_row(frm, 4, "TF (Truck Factor)", self.v_tf, "ESAL/veh pesado", col=0)
        self._entry_row(frm, 5, "Crecimiento g", self.v_growth, "% anual", col=0)
        self._entry_row(frm, 6, "Periodo n", self.v_years, "años", col=0)

        tip = ttk.Label(self.tab_traffic, text="Tip: TF=1 es un arranque típico si no tienes espectro. Luego lo refinamos con clases vehiculares.",
                        foreground="#555")
        tip.pack(anchor="w", pady=(10,0))

    def _build_tab_aashto(self):
        frm = ttk.LabelFrame(self.tab_aashto, text="Parámetros AASHTO 1993 (Flexible)", padding=12)
        frm.pack(fill="x")
        self._grid2(frm)

        self.v_rel = tk.StringVar()
        self.v_so = tk.StringVar()
        self.v_pi = tk.StringVar()
        self.v_pt = tk.StringVar()
        self.v_mr = tk.StringVar()

        self._entry_row(frm, 0, "Confiabilidad R", self.v_rel, "%", col=0)
        self._entry_row(frm, 1, "So (desviación estándar)", self.v_so, "-", col=0)
        self._entry_row(frm, 2, "Pi (serviciabilidad inicial)", self.v_pi, "-", col=0)
        self._entry_row(frm, 3, "Pt (serviciabilidad terminal)", self.v_pt, "-", col=0)
        self._entry_row(frm, 4, "Mr subrasante", self.v_mr, "MPa", col=0)

        tip = ttk.Label(self.tab_aashto, text="Internamente se convierte Mr de MPa a psi para la ecuación AASHTO.",
                        foreground="#555")
        tip.pack(anchor="w", pady=(10,0))

    def _build_tab_layers(self):
        frm1 = ttk.LabelFrame(self.tab_layers, text="Coeficientes estructurales y drenaje", padding=12)
        frm1.pack(fill="x")
        self._grid2(frm1)

        self.v_a1 = tk.StringVar()
        self.v_a2 = tk.StringVar()
        self.v_a3 = tk.StringVar()
        self.v_m2 = tk.StringVar()
        self.v_m3 = tk.StringVar()

        self._entry_row(frm1, 0, "a1 (Carpeta/HMA)", self.v_a1, "-", col=0)
        self._entry_row(frm1, 1, "a2 (Base)", self.v_a2, "-", col=0)
        self._entry_row(frm1, 2, "a3 (Subbase)", self.v_a3, "-", col=0)
        self._entry_row(frm1, 3, "m2 (drenaje base)", self.v_m2, "-", col=0)
        self._entry_row(frm1, 4, "m3 (drenaje subbase)", self.v_m3, "-", col=0)

        frm2 = ttk.LabelFrame(self.tab_layers, text="Búsqueda de espesores (cm)", padding=12)
        frm2.pack(fill="x", pady=(12,0))
        self._grid2(frm2)

        self.v_step = tk.StringVar()
        self.v_d1 = tk.StringVar()
        self.v_d2min = tk.StringVar()
        self.v_d2max = tk.StringVar()
        self.v_d3min = tk.StringVar()
        self.v_d3max = tk.StringVar()

        self._entry_row(frm2, 0, "Paso de búsqueda", self.v_step, "in", col=0)
        self._entry_row(frm2, 1, "D1 fijo (Carpeta)", self.v_d1, "cm", col=0)
        self._entry_row(frm2, 2, "D2 min / max (Base)", self.v_d2min, "cm", col=0)
        ttk.Label(frm2, text="").grid(row=2, column=2)  # spacer
        e_d2max = ttk.Entry(frm2, textvariable=self.v_d2max)
        e_d2max.grid(row=2, column=3, sticky="ew", pady=4)
        ttk.Label(frm2, text="cm").grid(row=2, column=4, sticky="w", padx=(8,0))

        self._entry_row(frm2, 3, "D3 min / max (Subbase)", self.v_d3min, "cm", col=0)
        ttk.Label(frm2, text="").grid(row=3, column=2)
        e_d3max = ttk.Entry(frm2, textvariable=self.v_d3max)
        e_d3max.grid(row=3, column=3, sticky="ew", pady=4)
        ttk.Label(frm2, text="cm").grid(row=3, column=4, sticky="w", padx=(8,0))

        tip = ttk.Label(self.tab_layers, text="MVP: D1 es fijo y el programa encuentra el menor combo (D2,D3) que cumpla SN.",
                        foreground="#555")
        tip.pack(anchor="w", pady=(10,0))

    def _build_tab_results(self):
        self.txt = tk.Text(self.tab_results, height=24, wrap="word")
        self.txt.pack(fill="both", expand=True)
        self.txt.insert("1.0", "Aquí saldrán los resultados.\n")
        self.txt.configure(state="disabled")

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
        self.v_d1.set(str(s["d1_fixed_cm"]))
        self.v_d2min.set(str(s["d2_min_cm"]))
        self.v_d2max.set(str(s["d2_max_cm"]))
        self.v_d3min.set(str(s["d3_min_cm"]))
        self.v_d3max.set(str(s["d3_max_cm"]))

    def _read_form_to_data(self):
        try:
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
            s["d1_fixed_cm"] = float(self.v_d1.get())
            s["d2_min_cm"] = float(self.v_d2min.get())
            s["d2_max_cm"] = float(self.v_d2max.get())
            s["d3_min_cm"] = float(self.v_d3min.get())
            s["d3_max_cm"] = float(self.v_d3max.get())

        except Exception as e:
            raise ValueError(f"Error leyendo datos: {e}")

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
        try:
            self.data = load_project(path)
            self._load_to_form()
            self._write_results(f"Proyecto cargado:\n{path}\n")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_save(self):
        self._read_form_to_data()
        path = filedialog.asksaveasfilename(title="Guardar proyecto", defaultextension=".json",
                                            filetypes=[("Proyecto JSON", "*.json")])
        if not path:
            return
        try:
            save_project(self.data, path)
            self._write_results(f"Proyecto guardado:\n{path}\n")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_calculate(self):
        try:
            self._read_form_to_data()
            t = self.data["traffic"]
            a = self.data["aashto"]
            l = self.data["layers"]
            s = self.data["search"]

            w18 = calc_w18(
                aadt_total=t["aadt_total"],
                pct_trucks=t["pct_trucks"]/100.0,
                dd=t["dd"],
                dl=t["dl"],
                truck_factor=t["truck_factor"],
                growth_pct=t["growth_pct"],
                years=t["design_years"]
            )

            sn_req, zr = solve_sn_required(
                w18=w18,
                reliability_pct=a["reliability_pct"],
                so=a["so"],
                pi=a["pi"],
                pt=a["pt"],
                mr_mpa=a["mr_mpa"]
            )

            rec = recommend_thicknesses(
                sn_required=sn_req,
                a1=l["a1"], a2=l["a2"], a3=l["a3"],
                m2=l["m2"], m3=l["m3"],
                step_in=s["step_in"],
                d1_fixed_cm=s["d1_fixed_cm"],
                d2_min_cm=s["d2_min_cm"], d2_max_cm=s["d2_max_cm"],
                d3_min_cm=s["d3_min_cm"], d3_max_cm=s["d3_max_cm"],
            )

            self.data["results"] = {
                "W18": w18,
                "SN_required": sn_req,
                "Zr": zr,
                **rec
            }

            out = []
            out.append("RESULTADOS\n")
            out.append(f"W18 (ESALs acumulados): {w18:,.0f}\n")
            out.append(f"Zr (por R): {fnum(zr, 3)}\n")
            out.append(f"SN requerido: {fnum(sn_req, 3)}\n\n")

            if rec["status"] == "OK":
                out.append("ESPESORES RECOMENDADOS (cumplen SN)\n")
                out.append(f"D1 Carpeta: {fnum(rec['D1_cm'], 1)} cm\n")
                out.append(f"D2 Base:    {fnum(rec['D2_cm'], 1)} cm\n")
                out.append(f"D3 Subbase: {fnum(rec['D3_cm'], 1)} cm\n\n")
                out.append(f"SN provisto: {fnum(rec['SN_provided'], 3)}\n")
                out.append(f"Margen (provisto - requerido): {fnum(rec['SN_provided'] - sn_req, 3)}\n")
            else:
                out.append("NO SE ENCONTRÓ SOLUCIÓN con los límites actuales.\n")
                out.append("Sugerencia: aumenta máximos de D2/D3 o D1 fijo, o reduce paso.\n\n")
                out.append(f"Mejor intento SN provisto: {fnum(rec.get('SN_best', 0.0), 3)}\n")

            self._write_results("".join(out))
            self.nb.select(self.tab_results)

        except Exception as e:
            messagebox.showerror("Error de cálculo", str(e))

    def run(self):
        # Better default theme on Windows if available
        try:
            style = ttk.Style()
            if "vista" in style.theme_names():
                style.theme_use("vista")
        except Exception:
            pass
        self.root.mainloop()
