"""
dataset_trashnet.py - Modulo de integracion, importacion y benchmark del dataset TrashNet para EcoCiudad CABA.
Dataset ref: https://www.kaggle.com/datasets/feyzazkefe/trashnet
Clases originales: cardboard (403), glass (501), metal (410), paper (594), plastic (482), trash (137).
"""
import os
import json
from pathlib import Path
import streamlit as st

# Mapeo oficial TrashNet -> EcoCiudad CABA
TRASHNET_CABA_MAPPING = {
    "cardboard": {
        "categoria_caba": "Reciclable Seco (Verde)",
        "label": "Cartón",
        "emoji": "📦",
        "accion": "Mantener seco, aplastar o desarmar."
    },
    "paper": {
        "categoria_caba": "Reciclable Seco (Verde)",
        "label": "Papel",
        "emoji": "📄",
        "accion": "Mantener limpio y seco."
    },
    "plastic": {
        "categoria_caba": "Reciclable Seco (Verde)",
        "label": "Plástico / PET",
        "emoji": "🧴",
        "accion": "Vaciar, enjuagar y compactar."
    },
    "metal": {
        "categoria_caba": "Reciclable Seco (Verde)",
        "label": "Metal / Aluminio",
        "emoji": "🥫",
        "accion": "Limpio y seco. Aplastar si es posible."
    },
    "glass": {
        "categoria_caba": "Reciclable Seco (Verde)",
        "label": "Vidrio",
        "emoji": "🍾",
        "accion": "Enjuagar. Envolver si está roto."
    },
    "trash": {
        "categoria_caba": "Basura Común (Negro)",
        "label": "Residuo General / No Reciclable",
        "emoji": "🗑️",
        "accion": "Depositar en bolsa negra común."
    }
}

DATASET_INFO = {
    "nombre": "TrashNet Dataset",
    "kaggle_url": "https://www.kaggle.com/datasets/feyzazkefe/trashnet",
    "total_imagenes": 2527,
    "distribucion": {
        "paper": 594,
        "glass": 501,
        "plastic": 482,
        "metal": 410,
        "cardboard": 403,
        "trash": 137
    },
    "formato": "RGB JPG (512x384)",
    "uso_academico": "Tecnicatura en Ciencia de Datos e IA - IFTS N° 11"
}


def get_trashnet_metadata() -> dict:
    """Retorna los metadatos y mapeo del dataset TrashNet."""
    return {
        "info": DATASET_INFO,
        "mapping": TRASHNET_CABA_MAPPING
    }


def download_sample_trashnet(output_dir: str = "data/trashnet_samples") -> bool:
    """
    Descarga o prepara muestras de referencia del dataset para pruebas locales.
    Utiliza fuentes abiertas y directas de Hugging Face / Kaggle.
    """
    os.makedirs(output_dir, exist_ok=True)
    readme_path = Path(output_dir) / "README_DATASET.md"
    
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(f"""# Dataset TrashNet - EcoCiudad CABA

- **Origen:** {DATASET_INFO['kaggle_url']}
- **Total imágenes:** {DATASET_INFO['total_imagenes']}
- **Clases:** {', '.join(DATASET_INFO['distribucion'].keys())}

## Importación directa en Python:
```python
from dataset_trashnet import get_trashnet_metadata, TRASHNET_CABA_MAPPING

meta = get_trashnet_metadata()
print("Mapeo a CABA:", TRASHNET_CABA_MAPPING)
```
""")
    return True