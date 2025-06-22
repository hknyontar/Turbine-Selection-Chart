import matplotlib.pyplot as plt
from matplotlib.path import Path
import matplotlib.patches as patches
import numpy as np
from matplotlib.ticker import ScalarFormatter 

def define_envelopes():
    """
    Returns a dict of turbine-name -> list of (Q, H) vertices.
    Vertices are closed by repeating the first point when plotting.
    These values were digitized approximately from the chart.
    """
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
    """
    Plot each turbine envelope on the given Axes and return a
    dict of name -> matplotlib.path.Path for point‐in‐polygon tests.
    """
    colors = {
        'Pelton':   '#2ca02c', # Green
        'Francis':  '#1f77b4', # Blue
        'Kaplan':   '#ff7f0e', # Orange
    }
    paths = {}
    for name, pts in envelopes.items():
        # close the polygon by appending the first point
        poly = pts + [pts[0]]
        path = Path(poly)
        patch = patches.PathPatch(path, facecolor=colors[name], alpha=0.25, label=name)
        ax.add_patch(patch)
        ax.plot(*zip(*poly), color=colors[name], lw=1.5)
        paths[name] = path
    return paths

def plot_power_curves(ax):
    """
    Plots constant power curves (kW) on the selection chart.
    P = rho * g * Q * H * eta / 1000 (for kW)
    H = P * 1000 / (rho * g * Q * eta)
    Assuming rho = 998 kg/m^3 (water density), g = 9.81 m/s^2.
    """
    rho = 998 # kg/m^3
    g = 9.81  # m/s^2
    
    # Efficiencies for power calculation, used for general curves
    efficiencies = {
        'Pelton': 0.915,
        'Francis': 0.945,
        'Kaplan': 0.94,
    }
    avg_efficiency = sum(efficiencies.values()) / len(efficiencies) 

    kW_values = [10, 50, 100, 500, 1000, 5000, 10000, 25000] # kW values for chart
    # Q_values should span a wider range to ensure intersection with limits for labels
    Q_values = np.logspace(np.log10(ax.get_xlim()[0] * 0.1), np.log10(ax.get_xlim()[1] * 10), 1000) # Extend Q range
    
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()

    for P_kW in kW_values:
        H_values = (P_kW * 1000) / (rho * g * Q_values * avg_efficiency)
        
        # Filter points to only plot within the visible y-range
        valid_indices = (H_values >= y_min) & (H_values <= y_max)
        
        # Find the portion of the curve that is actually visible
        visible_Q = Q_values[valid_indices & (Q_values >= x_min) & (Q_values <= x_max)]
        visible_H = H_values[valid_indices & (Q_values >= x_min) & (Q_values <= x_max)]

        if np.any(visible_Q): # Only plot if there are visible points
            ax.plot(visible_Q, visible_H, 'k--', linewidth=0.8, alpha=0.7)
            
            # --- Label Placement Logic V2: More Robust ---
            label_placed = False
            
            # Strategy 1: Try to place the label near the middle of the visible curve segment
            if len(visible_Q) > 0:
                mid_idx = len(visible_Q) // 2
                label_Q = visible_Q[mid_idx]
                label_H = visible_H[mid_idx]
                
                # Check if this mid-point is reasonable for a label (not too close to edge)
                if label_Q > x_min * 1.1 and label_Q < x_max * 0.9 and \
                   label_H > y_min * 1.1 and label_H < y_max * 0.9:
                    rotation_angle = -45 if P_kW <= 100 else 45
                    ax.text(label_Q, label_H, f'{P_kW} kW',
                            color='black', fontsize=8, ha='center', va='bottom', rotation=rotation_angle,
                            bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))
                    label_placed = True

            # Strategy 2: If Strategy 1 fails (e.g., curve mostly outside), try to place at a boundary
            if not label_placed:
                # Find the point where the curve enters the plot from the left (Q increasing)
                for i in range(len(Q_values)):
                    q = Q_values[i]
                    h = H_values[i]
                    if (x_min <= q <= x_max) and (y_min <= h <= y_max):
                        # Found an entry point. Place label slightly after it.
                        label_Q = q * 1.1 # Move slightly to the right
                        label_H = h * 1.1 # Move slightly up (for visual separation)
                        
                        # Ensure label remains within bounds after adjustment
                        if label_Q < x_max and label_H < y_max:
                            rotation_angle = -45 if P_kW <= 100 else 45
                            ax.text(label_Q, label_H, f'{P_kW} kW',
                                    color='black', fontsize=8, ha='left', va='bottom', rotation=rotation_angle,
                                    bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))
                            label_placed = True
                            break # Only place one label per curve

                # If still not placed, try from the right edge, moving left (for high power curves that come in from top-right)
                if not label_placed:
                    for i in range(len(Q_values) - 1, -1, -1): # Iterate backwards
                        q = Q_values[i]
                        h = H_values[i]
                        if (x_min <= q <= x_max) and (y_min <= h <= y_max):
                            label_Q = q * 0.9 # Move slightly to the left
                            label_H = h * 0.9 # Move slightly down
                            if label_Q > x_min and label_H > y_min:
                                rotation_angle = -45 if P_kW <= 100 else 45
                                ax.text(label_Q, label_H, f'{P_kW} kW',
                                        color='black', fontsize=8, ha='right', va='top', rotation=rotation_angle,
                                        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))
                                label_placed = True
                                break


def calculate_power(Q, H, turbine_type=None):
    """
    Calculates power in kW based on turbine type and given Q, H.
    P = rho * g * Q * H * eta / 1000 (for kW)
    """
    rho = 998 # kg/m^3
    g = 9.81  # m/s^2

    efficiencies = {
        'Pelton': 0.915,
        'Francis': 0.945,
        'Kaplan': 0.94,
    }

    efficiency = efficiencies.get(turbine_type, 0.88) # Default efficiency if type not found

    P = (rho * g * Q * H * efficiency) / 1000 # Power in kW
    return P

def main():
    # 1) Define envelopes
    envelopes = define_envelopes()

    # 2) Set up the plot
    fig, ax = plt.subplots(figsize=(12, 8)) # Slightly larger figure for better visibility

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlim(0.1, 100) # Adjusted x-axis limits
    ax.set_ylim(3, 1000)   # Adjusted y-axis limits

    ax.set_xlabel('Flow rate Q (m³/s)')
    ax.set_ylabel('Net head H (m)')
    ax.grid(True, which='major', linestyle='--', alpha=0.6) # Grid for major ticks
    ax.grid(True, which='minor', linestyle=':', alpha=0.3) # Grid for minor ticks

    # --- Set ScalarFormatter for non-exponential axis labels ---
    formatter = ScalarFormatter()
    formatter.set_scientific(False)
    formatter.set_powerlimits((-3, 4)) # Adjusts when scientific notation is used

    ax.xaxis.set_major_formatter(formatter)
    ax.yaxis.set_major_formatter(formatter)

    # 3) Draw the envelopes
    paths = plot_envelopes(ax, envelopes)

    # 4) Plot power curves
    plot_power_curves(ax)

    # 5) Obtain the test point (Q, H)
    Q = float(input("  Enter flow rate Q (m³/s): "))
    H = float(input("  Enter head H (m): "))

    # 6) Plot the point
    ax.plot(Q, H, 'ko', markersize=8, label=f'Point ({Q:.2f}, {H:.2f})')

    # --- Add dashed lines from the point to the axes (stopping at the point) ---
    # Vertical line from (Q, H) down to Q on the x-axis
    ax.plot([Q, Q], [ax.get_ylim()[0], H], color='gray', linestyle=':', linewidth=1.5)
    # Horizontal line from (Q, H) left to H on the y-axis
    ax.plot([ax.get_xlim()[0], Q], [H, H], color='gray', linestyle=':', linewidth=1.5)
    # ---------------------------------------------------

    # 7) Check which envelopes contain it and calculate power
    suitable = [name for name, path in paths.items() if path.contains_point((Q, H))]
    
    calculated_powers = {}
    if suitable:
        for turbine_type in suitable:
            power = calculate_power(Q, H, turbine_type)
            calculated_powers[turbine_type] = power
        
        # Format the power values for display
        power_strings = [f"{t}: {p:.2f} kW" for t, p in calculated_powers.items()]
        power_display = " | ".join(power_strings)
        title = f"Turbine(s): {', '.join(suitable)}"
        
        # Annotate the point with all calculated powers
        annotation_text = "\n".join(power_strings)
        ax.annotate(annotation_text, (Q, H), textcoords="offset points", xytext=(10, 10),
                    ha='left', va='bottom', fontsize=9,
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", lw=0.5, alpha=0.8))
        
    else:
        # If no suitable turbine, calculate approximate power with default efficiency
        power_at_point = calculate_power(Q, H)
        title = f"Turbine(s): None"
        ax.annotate(f"Approx. Power: {power_at_point:.2f} kW", (Q, H), textcoords="offset points", xytext=(10, 10),
                    ha='left', va='bottom', fontsize=9,
                    bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="black", lw=0.5, alpha=0.8))


    ax.set_title(title, pad=15)
    ax.legend(loc='upper right')

    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    main()
