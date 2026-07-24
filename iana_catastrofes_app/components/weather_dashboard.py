import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone

try:
    from chatbot_emergencia_app.app.weather_service import get_extended_weather_report, COQUIMBO_COMMUNES_COORDS, CHILE_TZ
except ModuleNotFoundError:
    try:
        from iana_catastrofes_app.app.weather_service import get_extended_weather_report, COQUIMBO_COMMUNES_COORDS, CHILE_TZ
    except ModuleNotFoundError:
        from app.weather_service import get_extended_weather_report, COQUIMBO_COMMUNES_COORDS, CHILE_TZ


def render_weather_monitoring_tab(default_commune: str = "Coquimbo"):
    st.markdown("### Centro de Monitoreo Climático Regional - Región de Coquimbo")
    st.caption("Integración en tiempo real con la Dirección Meteorológica de Chile (DMC) y OpenWeather One Call API")

    communes_list = sorted(list(COQUIMBO_COMMUNES_COORDS.keys()))
    default_idx = communes_list.index(default_commune) if default_commune in communes_list else 0

    col_comm, col_info = st.columns([1.5, 2.5])
    with col_comm:
        selected_commune = st.selectbox(
            "Seleccionar Comuna de Coquimbo",
            options=communes_list,
            index=default_idx,
            key="weather_commune_selector"
        )

    weather = get_extended_weather_report(selected_commune)
    cur = weather.get("current", {})
    sum_4d = weather.get("summary_4days", {})
    alerts = weather.get("alerts", [])
    timeline = weather.get("hourly_timeline", [])
    isotherm = weather.get("isotherm_0_m", 2100)

    if alerts:
        for alert in alerts:
            sev = str(alert.get("severity", "")).upper()
            border_color = "#FF4B4B" if "ALT" in sev or "CRIT" in sev else "#FFA726"
            bg_color = "rgba(255, 75, 75, 0.12)" if "ALT" in sev or "CRIT" in sev else "rgba(255, 167, 38, 0.12)"
            st.markdown(f"""
                <div style="background-color: {bg_color}; border-left: 5px solid {border_color}; border-radius: 8px; padding: 12px 18px; margin-bottom: 14px;">
                    <div style="font-weight: 800; color: {border_color}; font-size: 1.05rem;"> {alert.get('source', 'ALERTA OFICIAL')}: {alert.get('event', 'Alerta Meteorológica')}</div>
                    <div style="color: var(--text-primary); font-size: 0.95rem; margin-top: 4px;">{alert.get('description', '')}</div>
                    <div style="color: #888; font-size: 0.8rem; margin-top: 4px;">Vigencia: {alert.get('start_time', 'N/A')} al {alert.get('end_time', 'N/A')}</div>
                </div>
            """, unsafe_allow_html=True)

    today_rain = sum_4d.get('day_0_today_rain_mm', 0.0)
    day1_rain = sum_4d.get('day_plus_1_rain_mm', 0.0)
    day2_rain = sum_4d.get('day_plus_2_rain_mm', 0.0)
    past_rain = sum_4d.get('day_minus_1_rain_mm', 0.0)

    f_timeline = [t for t in timeline if t.get("is_future")]
    day0_items = f_timeline[:24]
    day1_items = f_timeline[24:48]
    day2_items = f_timeline[48:72]

    def get_day_stats(items, default_temp, default_wind):
        if not items:
            return default_temp, default_wind
        temps = [x["temp_c"] for x in items]
        winds = [x["wind_kmh"] for x in items]
        avg_t = round(sum(temps) / len(temps), 1)
        max_w = round(max(winds), 1)
        return f"{min(temps):.1f}°C - {max(temps):.1f}°C (Prom: {avg_t}°C)", max_w

    t0_str, w0_val = get_day_stats(day0_items, f"{cur.get('temp_c', 0)}°C", cur.get('wind_kmh', 0))
    t1_str, w1_val = get_day_stats(day1_items, "14.0°C", 18.0)
    t2_str, w2_val = get_day_stats(day2_items, "15.5°C", 14.0)

    now_dt = datetime.now(CHILE_TZ)
    date_d0 = now_dt.strftime("%d/%m/%Y")
    date_d1 = (now_dt + timedelta(days=1)).strftime("%d/%m/%Y")
    date_d2 = (now_dt + timedelta(days=2)).strftime("%d/%m/%Y")

    st.markdown(f"""
        <div style="background-color: var(--card-bg, #0F1F2E); border: 1px solid var(--border-subtle, #1D344B); border-radius: 10px; padding: 1.2rem; margin-bottom: 1.5rem; color: #FFFFFF;">
            <div style="font-weight: 800; font-size: 1.15rem; color: #FFFFFF; margin-bottom: 0.8rem; display: flex; justify-content: space-between; align-items: center;">
                <span>Pronóstico por Días - Comuna de {selected_commune}</span>
                <span style="font-size: 0.85rem; background-color: rgba(50, 197, 255, 0.12); color: var(--azul-cielo, #32C5FF); padding: 4px 12px; border-radius: 12px; border: 1px solid var(--azul-cielo, #32C5FF); font-weight: 600;">
                    Isoterma 0°C: {isotherm} m.s.n.m. | Ayer (-24h): {past_rain} mm
                </span>
            </div>
            <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 0.95rem; color: #FFFFFF;">
                <thead>
                    <tr style="border-bottom: 2px solid var(--border-subtle, #1D344B); color: #32C5FF; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 0.5px; font-weight: bold;">
                        <th style="padding: 10px 14px; color: #32C5FF;">Fecha / Día</th>
                        <th style="padding: 10px 14px; color: #32C5FF;">Temperatura (°C)</th>
                        <th style="padding: 10px 14px; color: #32C5FF;">Viento Máx. Esperado</th>
                        <th style="padding: 10px 14px; color: #32C5FF;">Precipitación Esperada</th>
                        <th style="padding: 10px 14px; color: #32C5FF;">Estado Proyectado</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom: 1px solid var(--border-subtle, #1D344B); background-color: rgba(50, 197, 255, 0.1);">
                        <td style="padding: 12px 14px; font-weight: bold; color: #FFFFFF;">{date_d0} (Hoy)</td>
                        <td style="padding: 12px 14px; color: #E2E8F0;">{t0_str}</td>
                        <td style="padding: 12px 14px; color: #E2E8F0; font-weight: 600;">{w0_val} km/h</td>
                        <td style="padding: 12px 14px; color: #32C5FF; font-weight: bold;">{today_rain:.1f} mm</td>
                        <td style="padding: 12px 14px; color: #E2E8F0; font-weight: 600;">{cur.get('condition', 'Temporal Activo')}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid var(--border-subtle, #1D344B);">
                        <td style="padding: 12px 14px; font-weight: bold; color: #FFFFFF;">{date_d1}</td>
                        <td style="padding: 12px 14px; color: #E2E8F0;">{t1_str}</td>
                        <td style="padding: 12px 14px; color: #E2E8F0;">{w1_val} km/h</td>
                        <td style="padding: 12px 14px; color: #32C5FF; font-weight: bold;">{day1_rain:.1f} mm</td>
                        <td style="padding: 12px 14px; color: #E2E8F0;">Precipitación / Chubascos</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px 14px; font-weight: bold; color: #FFFFFF;">{date_d2}</td>
                        <td style="padding: 12px 14px; color: #E2E8F0;">{t2_str}</td>
                        <td style="padding: 12px 14px; color: #E2E8F0;">{w2_val} km/h</td>
                        <td style="padding: 12px 14px; color: #32C5FF; font-weight: bold;">{day2_rain:.1f} mm</td>
                        <td style="padding: 12px 14px; color: #E2E8F0;">Declinando / Parcial</td>
                    </tr>
                </tbody>
            </table>
        </div>
    """, unsafe_allow_html=True)


    st.markdown("---")

    st.markdown(f"#### Línea de Tiempo Meteorológica (-12h a +36h) - Comuna de {selected_commune}")
    
    if timeline:
        now_ts = datetime.now(timezone.utc).timestamp()
        start_ts = now_ts - (12 * 3600)
        end_ts = now_ts + (36 * 3600)

        filtered_timeline = [t for t in timeline if start_ts <= t.get("dt", 0) <= end_ts]
        if not filtered_timeline:
            filtered_timeline = timeline[:48]
        
        df_time = pd.DataFrame(filtered_timeline)
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Bar(
                x=df_time["datetime_str"],
                y=df_time["rain_mm"],
                name="Lluvia (mm/h)",
                marker_color="#29B6F6",
                opacity=0.85
            ),
            secondary_y=False
        )

        fig.add_trace(
            go.Scatter(
                x=df_time["datetime_str"],
                y=df_time["wind_kmh"],
                name="Viento (km/h)",
                line=dict(color="#FF7043", width=2.5, dash="solid")
            ),
            secondary_y=True
        )

        fig.add_trace(
            go.Scatter(
                x=df_time["datetime_str"],
                y=df_time["temp_c"],
                name="Temperatura (°C)",
                line=dict(color="#FFCA28", width=1.8, dash="dot")
            ),
            secondary_y=True
        )

        fig.update_layout(
            title=dict(
                text=f"Evolución del Temporal (-12 Horas a +36 Horas) en {selected_commune}",
                font=dict(color="#E2E8F0", size=14)
            ),
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="top", y=-0.35, xanchor="center", x=0.5, font=dict(color="#E2E8F0")),
            margin=dict(t=50, b=80, l=10, r=10),
            height=400,
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E2E8F0")
        )

        fig.update_xaxes(title_text="Fecha / Hora", showgrid=False, color="#E2E8F0")
        fig.update_yaxes(title_text="Precipitación (mm/h)", secondary_y=False, showgrid=True, gridcolor="#1D344B", color="#E2E8F0")
        fig.update_yaxes(title_text="Viento (km/h) / Temp (°C)", secondary_y=True, showgrid=False, color="#E2E8F0")


        st.plotly_chart(fig, width="stretch")

def render_compact_weather_widget(commune_name: str):
    """Renderiza un widget compacto para ser integrado dentro del tablero de una emergencia específica."""
    weather = get_extended_weather_report(commune_name)
    cur = weather.get("current", {})
    sum_4d = weather.get("summary_4days", {})
    alerts = weather.get("alerts", [])
    isotherm = weather.get("isotherm_0_m", 2100)

    st.markdown(f"""
        <div style="background-color: var(--card-bg); border: 1px solid var(--card-border); border-radius: 10px; padding: 1rem; margin-bottom: 1rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <div style="font-weight: bold; color: var(--blue-title); font-size: 1.1rem;">
                    Clima Terreno en {commune_name} (OpenWeather & DMC)
                </div>
                <div style="background-color: rgba(41, 182, 246, 0.2); color: #29B6F6; font-size: 0.8rem; padding: 3px 10px; border-radius: 12px; font-weight: bold;">
                    Isoterma 0°C: {isotherm} m.s.n.m.
                </div>
            </div>
            <div style="display: flex; gap: 15px; flex-wrap: wrap; margin-top: 8px;">
                <div style="flex: 1; min-width: 130px; background-color: rgba(255,255,255,0.03); padding: 8px; border-radius: 6px;">
                    <span style="color: #aaa; font-size: 0.75rem;">ESTADO ACTUAL</span><br/>
                    <strong style="color: var(--text-primary); font-size: 1.05rem;">{cur.get('temp_c', 0)}°C</strong> | {cur.get('condition', 'Normal')}<br/>
                    <span style="color: #29B6F6; font-size: 0.85rem;">{cur.get('rain_last_hour_mm', 0)} mm/h | {cur.get('wind_kmh', 0)} km/h</span>
                </div>
                <div style="flex: 1; min-width: 130px; background-color: rgba(255,255,255,0.03); padding: 8px; border-radius: 6px;">
                    <span style="color: #aaa; font-size: 0.75rem;">AYER (-24h)</span><br/>
                    <strong style="color: #29B6F6; font-size: 1.05rem;">{sum_4d.get('day_minus_1_rain_mm', 0)} mm</strong> acumulados
                </div>
                <div style="flex: 1; min-width: 130px; background-color: rgba(255,255,255,0.03); padding: 8px; border-radius: 6px;">
                    <span style="color: #aaa; font-size: 0.75rem;">PRÓXIMOS 3 DÍAS</span><br/>
                    <strong style="color: #FFA726; font-size: 1.05rem;">{sum_4d.get('day_0_today_rain_mm', 0) + sum_4d.get('day_plus_1_rain_mm', 0) + sum_4d.get('day_plus_2_rain_mm', 0):.1f} mm</strong> proyectados
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if alerts:
        top_alert = alerts[0]
        st.warning(f" **Alerta Oficial DMC / SENAPRED en {commune_name}:** {top_alert.get('event')} - {top_alert.get('description')}")