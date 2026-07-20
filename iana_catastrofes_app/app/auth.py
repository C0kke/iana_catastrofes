import streamlit as st
from typing import Optional, Dict, Any

USERS_DB = {
    "Jefatura": {
        "username": "Jefatura",
        "password": "jefatura123@",
        "role": "read_only",
        "name": "Jefatura",
        "title": "Director de Operaciones & Catastro"
    },
    "usuario 1": {
        "username": "usuario 1",
        "password": "usuario123@",
        "role": "operator",
        "name": "Operador 1",
        "title": "Cuadrilla de Respuesta Rápida"
    },
    "usuario 2": {
        "username": "usuario 2",
        "password": "usuario123@",
        "role": "operator",
        "name": "Operador 2",
        "title": "Cuadrilla de Respuesta Rápida"
    }
}

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Valida las credenciales de usuario y retorna la información de perfil."""
    user = USERS_DB.get(username.strip())
    if user and user["password"] == password.strip():
        return user
    return None

def get_current_user() -> Optional[Dict[str, Any]]:
    """Obtiene el usuario autenticado en la sesión actual, manteniendo la persistencia ante recargas (F5)."""
    current = st.session_state.get("authenticated_user")
    if current:
        return current
    
    saved_user_key = st.query_params.get("session_user")
    if saved_user_key and saved_user_key in USERS_DB:
        user_obj = USERS_DB[saved_user_key]
        st.session_state["authenticated_user"] = user_obj
        return user_obj
        
    return None

def is_read_only() -> bool:
    """Retorna True si el usuario actual es Jefatura (solo lectura)."""
    user = get_current_user()
    if not user:
        return False
    return user.get("role") == "read_only"

def logout_user():
    """Cierra la sesión activa del usuario y limpia los parámetros de persistencia."""
    st.session_state.pop("authenticated_user", None)
    st.session_state.pop("active_project", None)
    st.session_state["show_new_project_dialog"] = False
    st.session_state["show_edit_project_dialog"] = False
    if "session_user" in st.query_params:
        try:
            del st.query_params["session_user"]
        except Exception:
            pass
    st.rerun()

def render_login_screen():
    """Renderiza la pantalla de inicio de sesión estilizada."""
    st.markdown("""
        <div style="max-width: 440px; margin: 4rem auto 2rem auto; background-color: var(--card-bg); border-radius: 12px; padding: 2.2rem; border: 1px solid var(--card-border); text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.1);">
            <h2 style="color: var(--blue-title); margin-top: 0; font-size: 1.8rem; font-weight: 800;">IANA - EMERGENCIA</h2>
            <p style="color: var(--text-primary); font-size: 0.95rem; margin-bottom: 1.5rem;">
                Sistema de Control y Monitoreo Municipal en Tiempo Real
            </p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form", clear_on_submit=False):
            username_input = st.selectbox(
                "Usuario / Perfil",
                options=["Jefatura", "usuario 1", "usuario 2"],
                help="Selecciona tu perfil asignado"
            )
            password_input = st.text_input("Contraseña", type="password", placeholder="Ingresa tu clave asignada")
            
            submit_btn = st.form_submit_button("Ingresar al Sistema", type="primary", use_container_width=True)

            if submit_btn:
                user = authenticate_user(username_input, password_input)
                if user:
                    st.session_state["authenticated_user"] = user
                    st.query_params["session_user"] = user["username"]
                    st.success(f"Bienvenido {user['name']}")
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas. Verifica la contraseña ingresada.")
