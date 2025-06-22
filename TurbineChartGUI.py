import tkinter as tk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.path import Path
import matplotlib.patches as patches
import numpy as np
from matplotlib.ticker import ScalarFormatter

def define_envelopes():
    envelopes = {
        'Pelton': [
            (0.02, 120), (0.02, 1000), (3.5, 1000), (9.8, 350),
            (4.8, 60), (0.038, 60)
        ],
        'Francis': [
            (0.2, 12), (0.2, 36), (1.2, 350),
            (9.8, 350), (40, 85), (25, 20), (1.6, 7), (0.32, 7)
        ],
        'Kaplan': [
            (1.2, 2), (0.5, 4.5), (0.5, 7), (1.8, 30),
            (5.9, 48), (35.0, 48), (100.0, 18), (100.0, 2.9), (75.0, 2)
        ],
    }
    return envelopes

def plot_envelopes(ax, envelopes):
    colors = {
        'Pelton':   '#2ca02c',
        'Francis':  '#1f77b4',
        'Kaplan':   '#ff7f0e',
    }
    paths = {}
    for name, pts in envelopes.items():
        poly = pts + [pts[0]]
        path = Path(poly)
        patch = patches.PathPatch(path, facecolor=colors[name], alpha=0.25, label=name)
        ax.add_patch(patch)
        ax.plot(*zip(*poly), color=colors[name], lw=1.5)
        paths[name] = path
    return paths

def plot_power_curves(ax):
    rho = 998
    g = 9.81
    efficiencies = {'Pelton': 0.915, 'Francis': 0.945, 'Kaplan': 0.94}
    avg_eff = sum(efficiencies.values()) / len(efficiencies)
    kW_values = [10, 50, 100, 500, 1000, 5000, 10000, 25000]
    Q_vals = np.logspace(np.log10(0.01), np.log10(1000), 1000)
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()
    for P in kW_values:
        H_vals = (P * 1000) / (rho * g * Q_vals * avg_eff)
        valid = (H_vals >= y_min) & (H_vals <= y_max) & (Q_vals >= x_min) & (Q_vals <= x_max)
        if np.any(valid):
            ax.plot(Q_vals[valid], H_vals[valid], 'k--', linewidth=0.8, alpha=0.7)

def calculate_power(Q, H, turbine=None):
    rho = 998
    g = 9.81
    eff = {'Pelton': 0.915, 'Francis': 0.945, 'Kaplan': 0.94}.get(turbine, 0.88)
    return (rho * g * Q * H * eff) / 1000

def create_plot(Q, H):
    envelopes = define_envelopes()
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlim(0.1, 100); ax.set_ylim(3, 1000)
    ax.set_xlabel('Flow rate Q (m³/s)'); ax.set_ylabel('Net head H (m)')
    ax.grid(True, which='major', linestyle='--', alpha=0.6)
    ax.grid(True, which='minor', linestyle=':', alpha=0.3)
    fmt = ScalarFormatter(); fmt.set_scientific(False); fmt.set_powerlimits((-3, 4))
    ax.xaxis.set_major_formatter(fmt); ax.yaxis.set_major_formatter(fmt)
    paths = plot_envelopes(ax, envelopes)
    plot_power_curves(ax)
    ax.plot(Q, H, 'ko', markersize=8, label=f'Point ({Q:.2f}, {H:.2f})')
    ax.plot([Q,Q], [ax.get_ylim()[0], H], color='gray', linestyle=':', linewidth=1.5)
    ax.plot([ax.get_xlim()[0],Q], [H, H], color='gray', linestyle=':', linewidth=1.5)
    suitable = [t for t, p in paths.items() if p.contains_point((Q, H))]
    if suitable:
        pows = {t: calculate_power(Q, H, t) for t in suitable}
        ann = "\n".join([f"{t}: {p:.2f} kW" for t, p in pows.items()])
        ax.annotate(ann, (Q, H), textcoords="offset points", xytext=(10,10),
                    ha='left', va='bottom', fontsize=9,
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", lw=0.5, alpha=0.8))
        ax.set_title("Turbine(s): " + ", ".join(suitable), pad=15)
    else:
        pow0 = calculate_power(Q, H)
        ax.annotate(f"Approx. Power: {pow0:.2f} kW", (Q, H), textcoords="offset points", xytext=(10,10),
                    ha='left', va='bottom', fontsize=9,
                    bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="black", lw=0.5, alpha=0.8))
        ax.set_title("Turbine(s): None", pad=15)
    ax.legend(loc='upper right')
    plt.tight_layout(); plt.show()

def on_plot():
    try:
        Q = float(q_entry.get())
        H = float(h_entry.get())
    except ValueError:
        messagebox.showerror("Geçersiz giriş", "Lütfen sayısal değerler giriniz.")
        return
    create_plot(Q, H)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Turbine Selection Chart")
    tk.Label(root, text="Flow rate Q (m³/s):").grid(row=0, column=0, padx=5, pady=5)
    q_entry = tk.Entry(root); q_entry.grid(row=0, column=1, padx=5, pady=5)
    tk.Label(root, text="Net head H (m):").grid(row=1, column=0, padx=5, pady=5)
    h_entry = tk.Entry(root); h_entry.grid(row=1, column=1, padx=5, pady=5)
    tk.Button(root, text="Plot", command=on_plot).grid(row=2, column=0, columnspan=2, pady=10)
    root.mainloop()
