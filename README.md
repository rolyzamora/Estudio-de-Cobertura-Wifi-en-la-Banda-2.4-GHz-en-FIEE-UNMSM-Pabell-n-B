# Mapa de Cobertura Wi-Fi (Interpolación Cúbica)

Genera mapas de calor de cobertura Wi-Fi por piso, a partir de mediciones de
señal (RSSI) tomadas en distintos puntos de un edificio. El script interpola
los datos con **scipy (interpolación cúbica)** y detecta automáticamente
zonas muertas (señal por debajo de un umbral configurable).

## 📷 ¿Qué genera?

Por cada red Wi-Fi definida, se produce una imagen `.png` con un mapa de
calor por piso, mostrando:
- Intensidad de señal (RSSI) interpolada en toda el área
- Puntos de medición reales con su valor RSSI
- Zonas muertas resaltadas en rojo
- Ubicación del router (origen 0,0)

## 🚀 Cómo ejecutarlo

### 1. Clona el repositorio
```bash
git clone https://github.com/TU_USUARIO/TU_REPO.git
cd TU_REPO
```

### 2. Crea un entorno virtual (recomendado)
```bash
python -m venv venv
source venv/bin/activate      # En Windows: venv\Scripts\activate
```

### 3. Instala las dependencias
```bash
pip install -r requirements.txt
```

### 4. Ejecuta el script
```bash
python mapa_cobertura_cubica.py
```

Esto generará imágenes como `mapa_rssi_bitel.png` y
`mapa_rssi_alumnos_fiee.png` en la misma carpeta.

> El repositorio incluye archivos CSV de ejemplo (`datos_rssi_bitel.csv` y
> `datos_rssi_alumnosunmsm.csv`) para que puedas probar el script sin
> necesidad de tus propios datos.

## 📊 Formato del archivo CSV

Cada archivo de mediciones debe tener estas columnas:

| Columna | Descripción                                  |
|---------|-----------------------------------------------|
| `x`     | Coordenada X en metros, relativa al router (0,0) |
| `y`     | Coordenada Y en metros, relativa al router (0,0) |
| `piso`  | Número de piso donde se tomó la medición      |
| `rssi`  | Intensidad de señal en dBm (valor negativo)   |

Ejemplo:
```csv
x,y,piso,rssi
0,3,1,-45
5,5,1,-58
-5,5,1,-60
```

## ⚙️ Configuración

Puedes ajustar estos parámetros al inicio del script `mapa_cobertura_cubica.py`:

- `ARCHIVOS`: diccionario `{nombre_red: ruta_csv}` — agrega o quita redes aquí.
- `UMBRAL_ZONA_MUERTA`: valor en dBm bajo el cual se considera "zona muerta" (por defecto `-75`).
- `RANGO_AUTOMATICO`: si es `True`, la escala de colores se ajusta automáticamente a los datos de cada red/piso; si es `False`, usa un rango fijo (`VMIN_FIJO`, `VMAX_FIJO`).

## 📦 Dependencias

- pandas
- numpy
- matplotlib
- scipy

Todas listadas en `requirements.txt`.

## 🖥️ Ejecutarlo sin instalar nada (opcional)

Si prefieres no instalar Python localmente, puedes usar **GitHub Codespaces**:
1. En la página del repo, haz clic en **Code → Codespaces → Create codespace**.
2. Una vez cargado el entorno, ejecuta en la terminal:
   ```bash
   pip install -r requirements.txt
   python mapa_cobertura_cubica.py
   ```

## 📄 Licencia

Este proyecto se distribuye bajo la licencia MIT (ver archivo `LICENSE`).
