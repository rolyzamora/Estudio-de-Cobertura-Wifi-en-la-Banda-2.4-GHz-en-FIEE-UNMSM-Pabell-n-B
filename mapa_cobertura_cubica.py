# 0. IMPORTACIONES
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from scipy.ndimage import label, center_of_mass
import matplotlib.patches as patches

# 1. ARCHIVOS DE ENTRADA
# Cada CSV debe tener las columnas: x, y, piso, rssi
ARCHIVOS = {
    'Bitel':        'datos_rssi_bitel.csv',
    'Alumnos FIEE': 'datos_rssi_alumnosunmsm.csv',
}

# 2. CONFIGURACIÓN
UMBRAL_ZONA_MUERTA = -75   # dBm — ajusta según tu criterio

# Rango de la escala de colores (RSSI). Antes estaba fijo en -95/-35, lo cual
# "aplastaba" la paleta cuando había algún dato atípico muy fuerte (ej. -37 dBm),
# dejando casi todo el mapa en tonos verde-amarillo y el rojo casi invisible.
# Si RANGO_AUTOMATICO = True, cada red/piso usa el rango real de sus propios datos
# (percentil 1-99 para evitar que un outlier siga distorsionando la escala).
# Si RANGO_AUTOMATICO = False, se usa el rango fijo definido en VMIN_FIJO/VMAX_FIJO.
RANGO_AUTOMATICO = False
VMIN_FIJO = -95
VMAX_FIJO = -55   # antes era -35; ajustado a un valor de señal "buena" realista


def leer_csv(path):
    """Lee y valida un CSV de mediciones RSSI."""
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"❌ No se encontró el archivo '{path}'.\n"
            f"   Asegúrate de que el CSV esté en la misma carpeta que este script, "
            f"o edita la variable ARCHIVOS con la ruta correcta.\n"
            f"   Consulta el README.md para más detalles."
        )
    columnas_requeridas = {'x', 'y', 'piso', 'rssi'}
    if not columnas_requeridas.issubset(df.columns):
        raise ValueError(f"El CSV '{path}' debe tener las columnas: {columnas_requeridas}. "
                         f"Encontradas: {set(df.columns)}")

    print(f"✅ CSV cargado: {path} -> {len(df)} filas, {df['piso'].nunique()} pisos")
    print(f"   Pisos encontrados: {sorted(df['piso'].unique())}")
    for p in sorted(df['piso'].unique()):
        sub = df[df['piso'] == p]
        print(f"   Piso {p}: {len(sub)} puntos | RSSI min={sub['rssi'].min()} dBm, max={sub['rssi'].max()} dBm")
    return df


# 3. FUNCIÓN: MAPA POR PISO EN 4 CUADRANTES
def generar_mapa_cuadrantes(df_piso, piso_num, ax, nombre_red):
    x    = df_piso['x'].values
    y    = df_piso['y'].values
    rssi = df_piso['rssi'].values

    # Rango fijo de -35 a 35 metros
    RANGO = 35

    # Malla fina interpolada en los 4 cuadrantes
    xi = np.linspace(-RANGO, RANGO, 200)
    yi = np.linspace(-RANGO, RANGO, 200)
    xi_grid, yi_grid = np.meshgrid(xi, yi)

    puntos  = np.array(list(zip(x, y)))
    zi_grid = griddata(puntos, rssi, (xi_grid, yi_grid),
                       method='cubic', fill_value=rssi.min())

    # Rango de la escala de colores para este piso/red
    if RANGO_AUTOMATICO:
        VMIN_ESCALA = float(np.percentile(rssi, 1))
        VMAX_ESCALA = float(np.percentile(rssi, 99))
    else:
        VMIN_ESCALA = VMIN_FIJO
        VMAX_ESCALA = VMAX_FIJO

    # Detección de zonas muertas
    mascara_muerta = zi_grid < UMBRAL_ZONA_MUERTA
    labeled, num_features = label(mascara_muerta)

    #  Mapa de calor 
    contour = ax.contourf(xi_grid, yi_grid, zi_grid, levels=50,
                          cmap='RdYlGn_r', vmin=VMIN_ESCALA, vmax=VMAX_ESCALA, alpha=0.92)

    # Línea de umbral zona muerta
    ax.contour(xi_grid, yi_grid, zi_grid, levels=[UMBRAL_ZONA_MUERTA],
               colors=['red'], linewidths=1.5, linestyles='--', alpha=0.8)

    # Ejes cruzados
    ax.axhline(0, color='white', linewidth=0.8, alpha=0.5, linestyle=':')
    ax.axvline(0, color='white', linewidth=0.8, alpha=0.5, linestyle=':')

    # Puntos de medición coloreados por RSSI
    ax.scatter(x, y, c=rssi, cmap='RdYlGn_r', vmin=VMIN_ESCALA, vmax=VMAX_ESCALA,
               s=60, edgecolors='white', linewidth=1.2, zorder=5)

    # Anotaciones de RSSI en cada punto
    for xi_pt, yi_pt, r in zip(x, y, rssi):
        offset_x = 0.4 if xi_pt >= 0 else -0.4
        ha = 'left' if xi_pt >= 0 else 'right'
        ax.text(xi_pt + offset_x, yi_pt, f'{r:.0f}', fontsize=6.5,
                color='white', ha=ha, va='center',
                bbox=dict(boxstyle='round,pad=0.15', fc='black', alpha=0.35, lw=0))

    # Router en el origen
    ax.scatter(0, 0, c='gold', s=280, marker='*', edgecolors='black',
               linewidth=1.0, zorder=10, label='Router')
    ax.text(0.3, 0.6, 'Router\n(0,0)', fontsize=8, color='gold',
            fontweight='bold', va='bottom')

    # Etiquetas de dirección
    ax.text( RANGO - 0.5,  0.3, '+X', fontsize=9, color='white', fontweight='bold')
    ax.text(-RANGO + 0.1,  0.3, '−X', fontsize=9, color='white', fontweight='bold')
    ax.text( 0.3,  RANGO - 0.5, '+Y', fontsize=9, color='white', fontweight='bold')
    ax.text( 0.3, -RANGO + 0.3, '−Y', fontsize=9, color='white', fontweight='bold')

    # Etiquetas de distancia sobre los ejes
    for d in np.unique(np.abs(x[x != 0])):
        if abs(d) <= RANGO:  # Solo mostrar si está dentro del rango
            ax.text( d, -0.9, f'{d:.0f}m', fontsize=6, color='lightgray', ha='center')
            ax.text(-d, -0.9, f'{d:.0f}m', fontsize=6, color='lightgray', ha='center')
    for d in np.unique(np.abs(y[y != 0])):
        if abs(d) <= RANGO:  # Solo mostrar si está dentro del rango
            ax.text(0.3,  d, f'{d:.0f}m', fontsize=6, color='lightgray', va='center')
            ax.text(0.3, -d, f'{d:.0f}m', fontsize=6, color='lightgray', va='center')

    # Zona muerta — círculo en centro de masa
    if num_features > 0:
        cy_px, cx_px = center_of_mass(mascara_muerta)
        real_cx = xi[0] + cx_px * (xi[-1] - xi[0]) / mascara_muerta.shape[1]
        real_cy = yi[0] + cy_px * (yi[-1] - yi[0]) / mascara_muerta.shape[0]
        area_px = np.sum(mascara_muerta)
        radio   = np.sqrt(area_px / np.pi) * (xi[-1] - xi[0]) / mascara_muerta.shape[1]
        radio   = min(radio, RANGO * 0.4)

        circ = patches.Circle((real_cx, real_cy), radius=radio,
                               color='red', alpha=0.18, zorder=3)
        ax.add_patch(circ)
        ax.text(real_cx, real_cy, f'Zona muerta\n< {UMBRAL_ZONA_MUERTA} dBm',
                ha='center', va='center', color='red', fontsize=7.5, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.2', fc='black', alpha=0.4, lw=0))

    # Título con estadísticas
    rssi_medio  = rssi.mean()
    pct_muerta  = np.sum(mascara_muerta) / mascara_muerta.size * 100
    ax.set_title(
        f'{nombre_red} — Piso {piso_num}\n'
        f'RSSI medio: {rssi_medio:.1f} dBm  |  Zona muerta: {pct_muerta:.1f}%',
        fontsize=9.5, color='white', pad=8)
    ax.set_xlabel('X (metros)', fontsize=9, color='lightgray')
    ax.set_ylabel('Y (metros)', fontsize=9, color='lightgray')
    ax.tick_params(colors='lightgray', labelsize=8)
    ax.set_xlim(-RANGO, RANGO)
    ax.set_ylim(-RANGO, RANGO)
    ax.set_aspect('equal')
    ax.grid(alpha=0.15, linestyle='--', color='white')
    for spine in ax.spines.values():
        spine.set_edgecolor('#444')

    return contour


def procesar_red(nombre_red, csv_path):
    """Genera la figura de cobertura (interpolación cúbica) para una red Wi-Fi completa."""
    print(f"\n{'='*60}\nProcesando red: {nombre_red}\n{'='*60}")
    df = leer_csv(csv_path)

    # 4. FIGURA: UN SUBPLOT POR PISO
    pisos    = sorted(df['piso'].unique())
    n_pisos  = len(pisos)
    ancho    = 7 * n_pisos

    fig, axes = plt.subplots(1, n_pisos, figsize=(ancho, 7))
    fig.patch.set_facecolor('#1a1a2e')

    if n_pisos == 1:
        axes = [axes]

    contour_last = None
    for ax, piso in zip(axes, pisos):
        ax.set_facecolor('#0f0f1a')
        df_piso      = df[df['piso'] == piso]
        contour_last = generar_mapa_cuadrantes(df_piso, piso, ax, nombre_red)

    # Colorbar global
    cbar_ax = fig.add_axes([0.92, 0.12, 0.015, 0.76])
    cbar    = fig.colorbar(contour_last, cax=cbar_ax)
    cbar.set_label('RSSI (dBm)', color='lightgray', fontsize=10)
    cbar.ax.yaxis.set_tick_params(color='lightgray')
    cbar.set_ticks([-95, -90, -85, -80, -75, -70, -65, -60, -55])
    cbar.ax.set_yticklabels(
        ['-95', '-90', '-85', '-80', '-75\n(límite)', '-70', '-65', '-60', '-55'],
        color='lightgray', fontsize=7.5)

    fig.suptitle(f'Mapa de Cobertura Wi-Fi — 4 Cuadrantes por Piso — Red: {nombre_red}',
                 fontsize=14, color='white', y=1.01, fontweight='bold')

    ruta_salida = f"mapa_rssi_{nombre_red.lower().replace(' ', '_')}.png"
    plt.tight_layout(rect=[0, 0, 0.91, 1])
    plt.savefig(ruta_salida, dpi=200, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    print(f"\n✅ Imagen guardada en: {ruta_salida}")
    plt.close(fig)
    return ruta_salida


# 5. EJECUCIÓN PRINCIPAL: procesa ambas redes
if __name__ == '__main__':
    resultados = {}
    for nombre_red, csv_path in ARCHIVOS.items():
        resultados[nombre_red] = procesar_red(nombre_red, csv_path)

    print(f"\n{'='*60}\nResumen de archivos generados:\n{'='*60}")
    for red, ruta in resultados.items():
        print(f"  {red}: {ruta}")
