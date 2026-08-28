"""
app.py - EcoCiudad CABA - Scanner de Residuos con IA y Red de Puntos Verdes
Tecnicatura en Ciencia de Datos e IA - IFTS N° 11
"""
import base64
from pathlib import Path

import av
import cv2
import pandas as pd
import numpy as np
import streamlit as st
import pydeck as pdk
from PIL import Image
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration

from utils_vision import load_model, run_inference
from feedback_store import load_feedback, add_correction, get_total_corrections
from puntos_verdes_data import PUNTOS_VERDES_LIST, CENTROS_VERDES_LIST, CATEGORIAS_OFICIALES_GCBA

# Umbral de alta confianza: si supera esto, no se molesta al usuario con consultas
HIGH_CONF_THRESHOLD = 0.60

# ─── Configuración de Página ────────────────────────────────────────────────
st.set_page_config(
    page_title="EcoCiudad CABA | Scanner IA & Puntos Verdes",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)


def get_logo_base64() -> str:
    """Carga y codifica en Base64 el archivo logo2.png para renderizado HTML."""
    candidates = [
        Path("logo2.png"),
        Path(__file__).parent / "logo2.png",
        Path(__file__).parent.parent / "logo2.png",
        Path("d:/Backup/2025/Terciario/IA & Datos/4to Cuatri/Proyecto Integrador/logo2.png"),
    ]
    for p in candidates:
        if p.exists():
            try:
                encoded = base64.b64encode(p.read_bytes()).decode("utf-8")
                return f"data:image/png;base64,{encoded}"
            except Exception:
                pass
    return ""


LOGO_B64 = get_logo_base64()

# ─── Estado de Feedback / Memoria ───────────────────────────────────────────
if "feedback_store" not in st.session_state:
    st.session_state.feedback_store = load_feedback()

fb_store = st.session_state.feedback_store
total_feedbacks = get_total_corrections(fb_store)

# ─── CSS Estilos: Stitch & Tailwind Design System ────────────────────────────
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet">

<style>
/* ─── Variables y Reset Global Stitch ─── */
:root {
    --color-bg: #F8FAFC;
    --color-surface: #FFFFFF;
    --color-primary: #012D1D;
    --color-primary-container: #1B4332;
    --color-secondary: #116C4A;
    --color-secondary-container: #A1F4C8;
    --color-on-secondary-container: #1B724F;
    --color-tertiary: #19273A;
    --color-tertiary-container: #2F3D51;
    --color-outline-variant: #C1C8C2;
    --color-outline: #717973;
    --color-on-surface: #191C1E;
    --color-on-surface-variant: #414844;
    --color-goal-green: #40916C;
    --color-surface-variant: #E0E3E5;
    --color-surface-low: #F2F4F6;
}

html, body, [class*="css"], .stApp {
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    background-color: var(--color-bg) !important;
    color: var(--color-on-surface) !important;
}

/* ─── Material Symbols ─── */
.material-symbols-outlined {
    font-family: 'Material Symbols Outlined' !important;
    font-weight: normal;
    font-style: normal;
    font-size: 24px;
    line-height: 1;
    letter-spacing: normal;
    text-transform: none;
    display: inline-block;
    white-space: nowrap;
    word-wrap: normal;
    direction: ltr;
    vertical-align: middle;
}

/* ─── Top Navbar Banner ─── */
.ecoscan-navbar {
    display: flex;
    align-items: center;
    justify-content: center;
    background: #FFFFFF;
    border: 1px solid var(--color-outline-variant);
    border-radius: 16px;
    padding: 0.75rem 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}
.ecoscan-navbar-banner {
    max-height: 75px;
    width: auto;
    max-width: 100%;
    object-fit: contain;
}
.ecoscan-navbar-right {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}
.live-status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #F2F4F6;
    border: 1px solid var(--color-outline-variant);
    padding: 5px 12px;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--color-on-surface);
}
.live-dot-pulse {
    width: 8px;
    height: 8px;
    background-color: #116C4A;
    border-radius: 50%;
    box-shadow: 0 0 0 rgba(17, 108, 74, 0.4);
    animation: pulse-green 2s infinite;
}
@keyframes pulse-green {
    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(17, 108, 74, 0.7); }
    70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(17, 108, 74, 0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(17, 108, 74, 0); }
}

/* ── Hero Scan Card ── */
.bento-hero-card {
    background: var(--color-surface);
    border: 1px solid var(--color-outline-variant);
    border-radius: 16px;
    padding: 2rem 1.5rem;
    text-align: center;
    box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    position: relative;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 240px;
}
.bento-hero-glow {
    position: absolute;
    inset: 0;
    opacity: 0.06;
    background: radial-gradient(ellipse at center, #012D1D 0%, transparent 70%);
    pointer-events: none;
}
.hero-camera-icon-btn {
    width: 68px;
    height: 68px;
    background-color: var(--color-primary);
    color: #FFFFFF;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 1rem;
    box-shadow: 0 8px 18px rgba(1, 45, 29, 0.25);
    transition: transform 0.2s ease, background-color 0.2s ease;
}
.hero-camera-icon-btn:hover {
    background-color: var(--color-primary-container);
    transform: scale(1.04);
}
.hero-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--color-on-surface);
    margin: 0 0 0.4rem;
    letter-spacing: -0.02em;
}
.hero-subtitle {
    font-size: 0.92rem;
    color: var(--color-on-surface-variant);
    max-width: 460px;
    margin: 0 auto 1rem;
    line-height: 1.45;
}
.hero-badges-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
}
.hero-badge-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 6px 14px;
    border: 1px solid var(--color-outline-variant);
    background: #FFFFFF;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--color-primary);
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}

/* ── Bento Side Column & Mini Cards ── */
.bento-side-col {
    display: flex;
    flex-direction: column;
    gap: 16px;
    justify-content: space-between;
}
.bento-mini-card {
    background: var(--color-surface);
    border: 1px solid var(--color-outline-variant);
    border-radius: 16px;
    padding: 1.25rem 1.4rem;
    box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 100%;
}
.bento-card-title {
    font-size: 0.72rem;
    font-weight: 700;
    color: var(--color-on-surface-variant);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.5rem;
}
.bento-goal-numbers {
    display: flex;
    align-items: baseline;
    gap: 6px;
    margin-bottom: 0.6rem;
}
.bento-goal-current {
    font-size: 1.85rem;
    font-weight: 700;
    color: var(--color-primary);
    line-height: 1;
}
.bento-goal-target {
    font-size: 0.9rem;
    color: var(--color-on-surface-variant);
}
.bento-progress-track {
    width: 100%;
    background-color: var(--color-surface-variant);
    height: 8px;
    border-radius: 9999px;
    overflow: hidden;
    margin-bottom: 0.35rem;
}
.bento-progress-bar {
    background-color: var(--color-goal-green);
    height: 100%;
    border-radius: 9999px;
    transition: width 0.4s ease;
}
.bento-progress-footer {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--color-on-surface-variant);
    text-align: right;
}

/* ── Nearby Green Points List ── */
.nearby-center-item {
    background: var(--color-surface);
    border: 1px solid var(--color-outline-variant);
    border-radius: 12px;
    padding: 0.9rem 1.1rem;
    margin-bottom: 0.65rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    transition: all 0.15s ease;
}
.nearby-center-item:hover {
    background-color: var(--color-surface-low);
    border-color: var(--color-secondary);
    transform: translateY(-1px);
}
.nearby-item-left {
    display: flex;
    align-items: center;
    gap: 12px;
}
.nearby-item-icon {
    width: 42px;
    height: 42px;
    background-color: var(--color-surface-variant);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--color-on-surface-variant);
    flex-shrink: 0;
}
.nearby-center-item:hover .nearby-item-icon {
    background-color: var(--color-primary-container);
    color: #FFFFFF;
}
.nearby-item-name {
    font-size: 0.9rem;
    font-weight: 700;
    color: var(--color-on-surface);
}
.nearby-item-meta {
    font-size: 0.78rem;
    color: var(--color-on-surface-variant);
}

/* ── Tarjetas de Detección ── */
.det-card {
    background: #FFFFFF;
    border: 1px solid var(--color-outline-variant);
    border-left: 5px solid #116C4A;
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.det-card.special {
    border-left-color: #BA1A1A;
    background: #FFF8F7;
}
.det-card.glass {
    border-left-color: #1E88E5;
}
.det-card.paper {
    border-left-color: #F59E0B;
}
.det-card.metal {
    border-left-color: #64748B;
}

/* ── Badges ── */
.ecoscan-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 12px;
    font-size: 0.82rem;
    font-weight: 700;
    border-radius: 9999px;
    background: var(--color-secondary-container);
    color: var(--color-on-secondary-container);
}
.ecoscan-badge-special {
    background: #FFDAD6;
    color: #93000A;
}

/* ── Feedback Box ── */
.fb-container-stitch {
    background: #FFFFFF;
    border: 1.5px dashed var(--color-outline-variant);
    border-radius: 14px;
    padding: 1.1rem 1.4rem;
    margin-top: 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.03);
}

/* ── Streamlit UI Elements Customization (Stitch Theme) ── */
[data-testid="stSidebar"] {
    background-color: #F2F4F6 !important;
    border-right: 1px solid var(--color-outline-variant) !important;
}
[data-testid="stTab"] {
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    color: var(--color-on-surface-variant) !important;
    padding: 0.6rem 1rem !important;
}
[data-testid="stTab"][aria-selected="true"] {
    border-bottom: 3px solid var(--color-secondary) !important;
    color: var(--color-primary) !important;
    font-weight: 700 !important;
}
[data-testid="stButton"] button {
    border-radius: 9999px !important;
    font-size: 0.86rem !important;
    font-weight: 600 !important;
    padding: 0.45rem 1.25rem !important;
    border: 1px solid var(--color-outline-variant) !important;
    background: #FFFFFF !important;
    color: var(--color-primary) !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
}
[data-testid="stButton"] button:hover {
    background: var(--color-secondary-container) !important;
    border-color: var(--color-secondary) !important;
    color: var(--color-on-secondary-container) !important;
    transform: translateY(-1px) !important;
}
[data-testid="stExpander"] {
    background: #FFFFFF !important;
    border: 1px solid var(--color-outline-variant) !important;
    border-radius: 12px !important;
    margin-bottom: 0.6rem !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03) !important;
}
[data-testid="stMetricValue"] {
    color: var(--color-primary) !important;
    font-weight: 700 !important;
}
[data-testid="stMetricLabel"] {
    color: var(--color-on-surface-variant) !important;
    font-weight: 600 !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

</style>
""", unsafe_allow_html=True)

# ─── Banner Principal Superior ──────────────────────────────────────────────
if LOGO_B64:
    banner_html = f'<img src="{LOGO_B64}" class="ecoscan-navbar-banner" alt="EcoCiudad Banner">'
else:
    banner_html = '<div style="font-size: 1.7rem; font-weight: 700; color: #012D1D; display: flex; align-items: center; gap: 8px;"><span class="material-symbols-outlined" style="font-size: 32px; color: #116C4A;">recycling</span> EcoCiudad Scanner</div>'

st.markdown(f"""
<header class="ecoscan-navbar">
  {banner_html}
</header>
""", unsafe_allow_html=True)

# ─── Variables y Configuración ──────────────────────────────────────────────
model_choice = "waste_specialized"
CONF_THRESH = 0.20
FILTER_PEOPLE = True

# ─── Carga del Modelo ────────────────────────────────────────────────────────
model = load_model(model_choice)

# ─── Bento Grid Header (EcoCiudad Dashboard) ────────────────────────────────────
daily_current = 124 + total_feedbacks
daily_target = 200
progress_pct = min(100, int((daily_current / daily_target) * 100))

bento_col1, bento_col2 = st.columns([1.8, 1], gap="medium")

with bento_col1:
    st.markdown(f"""
<div class="bento-hero-card">
  <div class="bento-hero-glow"></div>
  <div class="hero-camera-icon-btn">
    <span class="material-symbols-outlined" style="font-size: 34px;">photo_camera</span>
  </div>
  <h2 class="hero-title">Identificador Inteligente de Residuos</h2>
  <p class="hero-subtitle">Utilizá visión computacional para clasificar tus materiales y consultar su disposición correcta en la Ciudad.</p>
  <div class="hero-badges-row">
    <span class="hero-badge-pill"><span class="material-symbols-outlined" style="font-size:16px;">videocam</span> Live </span>
    <span class="hero-badge-pill"><span class="material-symbols-outlined" style="font-size:16px;">upload_file</span> Foto / Archivo</span>
    <span class="hero-badge-pill"><span class="material-symbols-outlined" style="font-size:16px;">psychology</span> Auto-Entrenamiento</span>
  </div>
</div>
""", unsafe_allow_html=True)

with bento_col2:
    st.markdown(f"""
<div class="bento-side-col">
  <div class="bento-mini-card">
    <div>
      <div class="bento-card-title">Meta Diaria de Clasificación</div>
      <div class="bento-goal-numbers">
        <span class="bento-goal-current">{daily_current}</span>
        <span class="bento-goal-target">/ {daily_target} residuos</span>
      </div>
    </div>
    <div>
      <div class="bento-progress-track">
        <div class="bento-progress-bar" style="width: {progress_pct}%;"></div>
      </div>
      <div class="bento-progress-footer">{progress_pct}% completado</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── Tabs Principales ────────────────────────────────────────────────────────
tab_live, tab_photo, tab_pv = st.tabs([
    "📷 Cámara",
    "🖼 Foto / Archivo",
    "📍 Puntos y Centros Verdes"
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Cámara en Vivo
# ═══════════════════════════════════════════════════════════════════════════════
with tab_live:
    st.info("📱 Mostrá el objeto en el centro de la cámara. El sistema detecta automáticamente si está sostenido por tu mano y optimiza el foco.")

    RTC_CONFIG = RTCConfiguration({"iceServers": [
        {"urls": ["stun:stun.l.google.com:19302"]},
        {"urls": ["stun:stun1.l.google.com:19302"]},
    ]})

    def video_frame_callback(frame: av.VideoFrame) -> av.VideoFrame:
        img_bgr = frame.to_ndarray(format="bgr24")
        annotated, _ = run_inference(
            model,
            img_bgr,
            conf_threshold=CONF_THRESH,
            filter_people=FILTER_PEOPLE,
            feedback_store=fb_store,
        )
        return av.VideoFrame.from_ndarray(annotated, format="bgr24")

    webrtc_streamer(
        key=f"stream-{model_choice}",
        mode=WebRtcMode.SENDRECV,
        rtc_configuration=RTC_CONFIG,
        video_frame_callback=video_frame_callback,
        media_stream_constraints={"video": {"facingMode": {"ideal": "environment"}}, "audio": False},
        async_processing=True,
    )
    st.caption("💡 Si un objeto es ambiguo o querés corregir el material para que aprenda, usá la Pestaña 2 (Foto / Archivo).")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Foto / Archivo
# ═══════════════════════════════════════════════════════════════════════════════
with tab_photo:
    col_in, col_out = st.columns([1, 1], gap="large")

    with col_in:
        st.subheader("📥 Captura o Carga de Imagen")
        source = st.radio(
            "Método:", ["📸 Cámara del dispositivo", "📂 Subir imagen"],
            horizontal=True, label_visibility="collapsed",
        )
        img_pil = None
        if "Cámara" in source or "Camara" in source:
            cam_shot = st.camera_input("Capturar foto del residuo")
            if cam_shot:
                img_pil = Image.open(cam_shot).convert("RGB")
        else:
            uploaded = st.file_uploader("Subir foto de residuo", type=["jpg", "jpeg", "png", "webp", "bmp"])
            if uploaded:
                img_pil = Image.open(uploaded).convert("RGB")

    with col_out:
        st.subheader("🔍 Diagnóstico y Separación")

        if img_pil is None:
            st.markdown("""
<div class="bento-hero-card" style="min-height: 200px; padding: 1.5rem;">
  <div class="hero-camera-icon-btn" style="width: 52px; height: 52px; margin-bottom: 0.5rem;">
    <span class="material-symbols-outlined" style="font-size: 26px;">photo_camera</span>
  </div>
  <h3 class="hero-title" style="font-size: 1.2rem;">Identificá tu residuo</h3>
  <p class="hero-desc" style="font-size: 0.85rem; margin-bottom: 0;">Tomá una foto o subí una imagen del material.<br>La IA detectará y clasificará el tipo de residuo automáticamente.</p>
</div>
""", unsafe_allow_html=True)
        else:
            frame_bgr = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
            annotated_bgr, detections = run_inference(
                model,
                frame_bgr,
                conf_threshold=CONF_THRESH,
                filter_people=FILTER_PEOPLE,
                feedback_store=fb_store,
            )
            annotated_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)
            st.image(annotated_rgb, use_container_width=True)

            if not detections:
                st.warning("No se detectó ningún residuo claro con el umbral actual. Probá centrando el objeto o bajando el 'Umbral de confianza'.")
            else:
                top_det = detections[0]
                top_conf = top_det["confianza"]
                is_held = top_det["is_held_in_center"]
                has_special = top_det.get("es_especial", False)

                m1, m2 = st.columns(2)
                m1.metric("Objetos detectados", len(detections))
                m2.metric("Confianza principal", f"{top_conf:.0%}")

                if top_conf < 0.35:
                    st.warning("⚠️ Baja confianza en la detección. El resultado puede no ser exacto — revisá la imagen o corregí con los botones de abajo.")

                st.markdown("### 📋 Recomendación de Separación")
                det = top_det
                tipo = det["tipo"]
                label = det["label"]
                es_esp = det.get("es_especial", False)
                card_cls = "det-card special" if es_esp else "det-card"
                if not es_esp:
                    if "Vidrio" in label:
                        card_cls += " glass"
                    elif "Carton" in label or "Papel" in label:
                        card_cls += " paper"
                    elif "Metal" in label or "Lata" in label:
                        card_cls += " metal"
                    elif "CD" in label or "Disco" in label:
                        card_cls += " glass"

                held_tag = " · 🖐️ En mano (Centro)" if det["is_held_in_center"] else ""
                boost_tag = " ✦ Auto-aprendido" if det.get("boost_applied") else ""
                badge_class = "ecoscan-badge ecoscan-badge-special" if es_esp else "ecoscan-badge"

                st.markdown(f"""
<div class="{card_cls}">
  <div style="display:flex; justify-content:space-between; align-items:center;">
    <span style="font-size:1.15rem; font-weight:700; color:#012D1D;">{det['emoji']} {det['label']}</span>
    <div>
      <span class="{badge_class}">{det['confianza']:.0%}{boost_tag}</span>
    </div>
  </div>
  <div style="margin-top:0.5rem; font-size:0.92rem; line-height:1.5;">
    <b>Destino:</b> {det['tipo']}{held_tag}<br>
    <b>¿Qué hacer?:</b> {det['accion']}
  </div>
</div>
""", unsafe_allow_html=True)

                # ── Opcionalidad de Puntos Verdes según el tipo de residuo ──
                st.divider()
                if has_special:
                    st.error("🔴 **RESIDUO ESPECIAL:** Este material **NO debe tirarse en el contenedor verde ni negro**. Requiere Punto Verde o Punto Verde Móvil.")
                    st.info("👉 Consultá la pestaña **'📍 Puntos y Centros Verdes'** para ver el mapa y horarios del punto más cercano a tu Comuna.")
                else:
                    st.success("🟢 **Disposición en Origen:** Podés depositar este material directamente en el **Contenedor Verde** de tu cuadra (limpio y seco).")
                    with st.expander("📍 ¿Querés llevarlo a un Punto Verde o Centro de Cooperativa? (Opcional)"):
                        st.markdown("""
Si no tenés contenedor verde cerca o preferís entregarlo en mano:
- **Puntos Verdes:** Miércoles a Domingos de 11 a 14:30 h y de 15 a 19 h.
- **Centros Verdes:** Plantas de cooperativas de recuperadores urbanos.
- Consulta el mapa completo en la pestaña **'📍 Puntos y Centros Verdes'**.
""")

                # ── Auto-entrenamiento / Corrección ──
                if top_conf < HIGH_CONF_THRESHOLD:
                    st.markdown("""
<div class="fb-container-stitch">
  <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
    <span class="material-symbols-outlined" style="color:#116C4A; font-size:20px;">psychology</span>
    <b style="color:#012D1D; font-size:0.95rem;">Auto-Entrenamiento: ¿Qué material es en realidad?</b>
  </div>
  <span style="font-size:0.86rem; color:#414844;">
    Seleccioná el material correcto con 1 click. El sistema aprenderá a reconocerlo con mayor peso cuando esté sostenido en el centro.
  </span>
</div>
""", unsafe_allow_html=True)

                    quick_materials = [
                        ("cd",        "💿 CD / DVD"),
                        ("plastic",   "🧴 Plástico"),
                        ("cardboard", "📦 Cartón"),
                        ("metal",     "🥫 Metal / Lata"),
                        ("glass",     "🍾 Vidrio"),
                        ("paper",     "📄 Papel"),
                        ("e-waste",   "🔋 RAEE"),
                        ("toner",     "🖨️ Tóner"),
                    ]

                    st.write("")
                    cols_btn = st.columns(4)
                    for idx, (mat_key, mat_label) in enumerate(quick_materials):
                        col_target = cols_btn[idx % 4]
                        if col_target.button(mat_label, key=f"btn_fb_{mat_key}", use_container_width=True):
                            new_store = add_correction(
                                predicted_cls=top_det["clase"],
                                correct_cls=mat_key,
                                is_held_in_center=is_held,
                                store=st.session_state.feedback_store
                            )
                            st.session_state.feedback_store = new_store
                            st.success(f"🧠 ¡Aprendizaje registrado! Se reforzó el peso para '{mat_label}' en objetos sostenidos en el centro.")
                            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Puntos y Centros Verdes
# ═══════════════════════════════════════════════════════════════════════════════
with tab_pv:
    st.subheader("📍 Red de Puntos Verdes y Centros Verdes de CABA")
    st.markdown("""
Visualizá las **32 plazas con Puntos Verdes** y las **14 plantas de Centros Verdes** gestionadas por Cooperativas de Recuperadores Urbanos en la Ciudad de Buenos Aires.
""")

    COMUNAS_BARRIOS = {
        1: "1 (Constitución, Montserrat, Puerto Madero, Retiro, San Nicolás, San Telmo)",
        2: "2 (Recoleta)",
        3: "3 (Balvanera, San Cristóbal)",
        4: "4 (Barracas, La Boca, Nueva Pompeya, Parque Patricios)",
        5: "5 (Almagro, Boedo)",
        6: "6 (Caballito)",
        7: "7 (Flores, Parque Chacabuco)",
        8: "8 (Villa Lugano, Villa Riachuelo, Villa Soldati)",
        9: "9 (Liniers, Mataderos, Parque Avellaneda)",
        10: "10 (Floresta, Monte Castro, Vélez Sarsfield, Versalles, Villa Luro, Villa Real)",
        11: "11 (Villa del Parque, Villa Devoto, Villa General Mitre, Villa Santa Rita)",
        12: "12 (Coghlan, Saavedra, Villa Pueyrredón, Villa Urquiza)",
        13: "13 (Belgrano, Colegiales, Núñez)",
        14: "14 (Palermo)",
        15: "15 (Agronomía, Chacarita, La Paternal, Parque Chas, Villa Crespo, Villa Ortúzar)",
    }

    # Coordenadas aproximadas de centroide por comuna
    COMUNA_CENTROIDES = {
        1: (-34.6037, -58.3750), 2: (-34.5910, -58.3980), 3: (-34.6150, -58.4030),
        4: (-34.6430, -58.3950), 5: (-34.6140, -58.4180), 6: (-34.6178, -58.4345),
        7: (-34.6310, -58.4520), 8: (-34.6680, -58.4580), 9: (-34.6530, -58.4950),
        10: (-34.6260, -58.5000), 11: (-34.6020, -58.5030), 12: (-34.5610, -58.4940),
        13: (-34.5530, -58.4620), 14: (-34.5820, -58.4240), 15: (-34.5840, -58.4580),
    }

    col_f1, col_f2 = st.columns([1.2, 1])
    with col_f1:
        comunas_disponibles = ["Todas"] + list(range(1, 16))
        filtro_comuna = st.selectbox(
            "Tu Comuna / Barrio de referencia:",
            comunas_disponibles,
            format_func=lambda c: "CABA (Todas las Comunas)" if c == "Todas" else COMUNAS_BARRIOS.get(c, str(c)),
            key="filtro_comuna_pv"
        )
    with col_f2:
        tipo_capa = st.radio(
            "Capa en mapa:",
            ["📍 Puntos Verdes (32)", "🏭 Centros Verdes (14)", "🌐 Todos (46)"],
            horizontal=True
        )

    df_pv = pd.DataFrame(PUNTOS_VERDES_LIST)
    df_cv = pd.DataFrame(CENTROS_VERDES_LIST)

    if "Puntos Verdes" in tipo_capa:
        df_display = df_pv.copy()
    elif "Centros Verdes" in tipo_capa:
        df_display = df_cv.copy()
    else:
        df_display = pd.concat([df_pv, df_cv], ignore_index=True)

    # Coordenada de referencia para cálculo según Comuna seleccionada
    if filtro_comuna != "Todas" and int(filtro_comuna) in COMUNA_CENTROIDES:
        ref_lat, ref_lon = COMUNA_CENTROIDES[int(filtro_comuna)]
        df_filtrado_mapa = df_display[df_display["comuna"] == int(filtro_comuna)]
        if df_filtrado_mapa.empty:
            df_filtrado_mapa = df_display.copy()
    else:
        ref_lat, ref_lon = -34.6037, -58.3816
        df_filtrado_mapa = df_display.copy()

    # ── Sección Puntos Verdes Cercanos (Dinámica con datos reales CABA) ──
    st.markdown("### 📍 Puntos Verdes más cercanos a tu ubicación")
    
    todos_puntos = PUNTOS_VERDES_LIST + CENTROS_VERDES_LIST
    
    def calc_dist(pt):
        dlat = np.radians(pt["lat"] - ref_lat)
        dlon = np.radians(pt["lon"] - ref_lon)
        a = np.sin(dlat / 2)**2 + np.cos(np.radians(ref_lat)) * np.cos(np.radians(pt["lat"])) * np.sin(dlon / 2)**2
        return 6371.0 * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    
    puntos_con_dist = []
    for p in todos_puntos:
        p_copy = dict(p)
        p_copy["dist_km"] = calc_dist(p)
        puntos_con_dist.append(p_copy)
    
    puntos_con_dist.sort(key=lambda x: x["dist_km"])
    top3_cercanos = puntos_con_dist[:3]
    
    cards_html = ""
    for p in top3_cercanos:
        is_cv = "Centro Verde" in p.get("tipo", "")
        is_esp = "Especial" in p.get("tipo", "")
        
        if is_cv:
            icon_name = "factory"
            tag_color = "#19273A"
        elif is_esp:
            icon_name = "battery_charging_full"
            tag_color = "#BA1A1A"
        else:
            icon_name = "recycling"
            tag_color = "#116C4A"
            
        cards_html += f"""<div class="nearby-center-item"><div class="nearby-item-left"><div class="nearby-item-icon" style="color: {tag_color};"><span class="material-symbols-outlined">{icon_name}</span></div><div><div class="nearby-item-name">{p['nombre']}</div><div class="nearby-item-meta">{p.get('tipo', 'Punto Verde')} • {p.get('direccion', '')} • Comuna {p['comuna']} • <b>{p['dist_km']:.1f} km</b></div></div></div><span class="material-symbols-outlined" style="color: #717973; font-size: 20px;">chevron_right</span></div>"""
    
    st.markdown(f'<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; margin-bottom: 1.25rem;">{cards_html}</div>', unsafe_allow_html=True)

    st.markdown("#### 🗺️ Ubicaciones Geolocalizadas (Pasá el cursor o tocá un punto)")
    
    # Colores pydeck: Verde para Punto Verde, Rojo para Especial, Azul para Centro Verde
    def get_color_pdk(row):
        t = str(row.get("tipo", ""))
        if "Especial" in t:
            return [229, 57, 53, 220]
        elif "Centro Verde" in t:
            return [25, 39, 58, 220]
        else:
            return [17, 108, 74, 220]

    df_map_render = df_filtrado_mapa.copy()
    df_map_render["color"] = df_map_render.apply(get_color_pdk, axis=1)

    layer_points = pdk.Layer(
        "ScatterplotLayer",
        data=df_map_render,
        get_position=["lon", "lat"],
        get_color="color",
        get_radius=220,
        pickable=True,
        auto_highlight=True,
    )

    view_state = pdk.ViewState(
        latitude=float(df_map_render["lat"].mean()) if not df_map_render.empty else -34.6037,
        longitude=float(df_map_render["lon"].mean()) if not df_map_render.empty else -58.3816,
        zoom=12 if filtro_comuna != "Todas" else 11.2,
        pitch=0,
    )

    st.pydeck_chart(
        pdk.Deck(
            layers=[layer_points],
            initial_view_state=view_state,
            tooltip={
                "html": "<div style='font-family: sans-serif; font-size: 13px; line-height: 1.4;'>"
                        "<b style='font-size: 14px; color: #A1F4C8;'>{nombre}</b><br/>"
                        "📍 <b>Dirección:</b> {direccion}<br/>"
                        "🏷️ <b>Tipo:</b> {tipo}<br/>"
                        "🕒 <b>Horario:</b> {horario}<br/>"
                        "📌 <b>Comuna:</b> {comuna}<br/>"
                        "🟢 <b>Estado:</b> {estado}</div>",
                "style": {
                    "backgroundColor": "#012D1D",
                    "color": "#FFFFFF",
                    "borderRadius": "10px",
                    "padding": "10px 14px",
                    "boxShadow": "0 4px 12px rgba(0,0,0,0.2)"
                }
            },
            map_style="light"
        )
    )

    st.markdown(f"#### 📋 Detalle ({len(df_filtrado_mapa)} ubicaciones)")
    for _, row in df_filtrado_mapa.iterrows():
        tipo = row.get("tipo", "Punto Verde")
        admin = f" · Admin: {row['administra']}" if "administra" in row and pd.notnull(row["administra"]) else ""
        estado_badge = "🟢 " + str(row.get("estado", "Operativo")) if "Abierto" in str(row.get("estado", "")) or "Operativo" in str(row.get("estado", "")) else "🔴 " + str(row.get("estado", ""))

        with st.expander(f"{tipo}: {row['nombre']} — Comuna {row['comuna']}{admin} ({estado_badge})"):
            st.markdown(f"""
- **Dirección:** `{row['direccion']}`
- **Barrio / Comuna:** `{row.get('barrio', '')}` (Comuna {row['comuna']})
- **Horario:** `{row.get('horario', 'Consultar')}`
- **Estado:** `{row.get('estado', 'Operativo')}`
""")

    st.divider()
    st.markdown("### 📚 Guía Oficial GCBA: Residuos Especiales")
    for cat_id, cat_info in CATEGORIAS_OFICIALES_GCBA.items():
        with st.expander(f"{cat_info['titulo']}"):
            st.markdown(f"""
- **Materiales recibidos:** {cat_info['items']}
- **Condición de entrega:** {cat_info['condicion']}
- **Destino obligatorio Punto Verde:** `{'Sí (No tirar a tachos de calle)' if cat_info['obligatorio_punto_verde'] else 'Opcional'}`
""")



# ─── Footer ──────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<p style='text-align:center; color:#717973; font-size:0.82rem; margin:1rem 0;'>"
    "EcoCiudad CABA · Tecnicatura en Ciencia de Datos e IA · IFTS N° 11 · 2026"
    "</p>",
    unsafe_allow_html=True,
)