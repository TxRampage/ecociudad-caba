# ♻️ EcoCiudad CABA — Scanner de Residuos con IA

**Proyecto Integrador · Tecnicatura en Ciencia de Datos e IA · IFTS N° 11**

Módulo integral de escaneo en tiempo real con Computer Vision, clasificación de residuos según la normativa de CABA, red geolocalizada de Puntos Verdes y auto-aprendizaje adaptativo.

---

## 🚀 Funcionalidades Principales

### 1. 📷 Scanner de Residuos por IA (Tiempo Real y Captura)
- **Modo Dual:**
  - **Pestaña 1 (Cámara en Vivo WebRTC):** Inferencia continua con bounding boxes y foco central.
  - **Pestaña 2 (Foto / Subida):** Análisis estático con desglose de confianza y recomendaciones de acción inmediata.
- **Foco Espacial + Mano en el Centro:** Detecta si el objeto está siendo sostenido por la mano en el centro de la toma visual para optimizar la detección del residuo e ignorar manos/fondos.
- **Auto-Entrenamiento en Caliente (`feedback_store.py`):**
  - Si la confianza es baja ($< 60\%$), permite al usuario confirmar el material con 1 solo clic.
  - El sistema auto-ajusta sus pesos y aprende a priorizar ese material en sucesivos escaneos de objetos similares.

### 2. 📍 Red Oficial de Puntos Verdes GCBA y Mapa Interactivo
- **Pestaña 3 (Puntos Verdes y Residuos Especiales):**
  - Mapa interactivo de CABA con las 32 ubicaciones de Puntos Verdes y Puntos Verdes Especiales.
  - Filtro por Comuna (1 a 15) y Tipo de Punto Verde.
  - Horarios oficiales:
    - **Puntos Verdes:** Miércoles a Domingos de 11:00 a 14:30 h y de 15:00 a 19:00 h.
    - **Puntos Verdes Especiales (Parque Centenario y Plaza Arenales):** Miércoles a Domingos de 11:00 a 19:00 h (Corrido).

### 3. ⚠️ Clasificación de Residuos Especiales (Scraping GCBA Oficial)
Mapeo diferenciado según normativa de la Ciudad:
- **🖨️ Cartuchos de Tinta y Tóneres:** Hasta 3 por persona (limpios, sin derrames). Obligatorio Punto Verde.
- **🔋 RAEE (Aparatos Eléctricos y Electrónicos):** Celulares, notebooks, tablets, cámaras, teclados, mouse (hasta 10 por persona). Obligatorio Punto Verde.
- **🍳 Aceite de Cocina Usado (AVU):** En botellas plásticas cerradas y frías (1L contamina 1000L de agua; se transforma en Biodiésel). Obligatorio Punto Verde.
- **🔋 Pilas:** AA, AAA, C, D, 9V, botón.
- **💡 Lámparas y Tubos Fluorescentes:** Hasta 5 por persona en su envoltorio/caja (contienen mercurio).
- **☕ Cápsulas de Café y Bolsas de Alimento:** Se recuperan para fabricar madera plástica.
- **🍂 Orgánicos para Compost:** Frutas, verduras, yerba, café, té, hojas secas (sin carnes ni huesos).

### 4. 📊 Integración del Dataset TrashNet (`dataset_trashnet.py`)
Módulo para importar y evaluar el dataset de referencia de investigación:
- **Dataset:** [TrashNet en Kaggle](https://www.kaggle.com/datasets/feyzazkefe/trashnet) (2.527 imágenes).
- **Clases:** `cardboard`, `glass`, `metal`, `paper`, `plastic`, `trash`.
- **Importación:**
  ```python
  from dataset_trashnet import get_trashnet_metadata, TRASHNET_CABA_MAPPING
  meta = get_trashnet_metadata()
  ```

---

## 🛠️ Estructura del Proyecto

```text
ecociudad-scanner/
├── .streamlit/
│   └── config.toml           # Tema verde/azul EcoCiudad
├── app.py                    # Interfaz Streamlit (3 Pestañas interactivas)
├── utils_vision.py           # Inferencia YOLO, análisis espacial de mano y CABA mapping
├── feedback_store.py         # Memoria de auto-entrenamiento y pesos adaptativos
├── puntos_verdes_data.py     # Catálogo geolocalizado de Puntos Verdes y Residuos Especiales
├── dataset_trashnet.py       # Módulo de integración del dataset TrashNet
├── requirements.txt          # Dependencias
└── README.md
```

---

## 💻 Ejecución

```bash
cd ecociudad-scanner
pip install -r requirements.txt
streamlit run app.py
```
Acceder en navegador a `http://localhost:8501`.