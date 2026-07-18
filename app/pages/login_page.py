"""Login and user setup pages."""

from nicegui import ui, app

from app.database.db import get_session_direct as get_session
from app.services.auth_service import (
    authenticate,
    create_user,
    get_user_count,
    change_password,
    is_auth_enabled,
)


def render_login():
    """Render the login page."""
    # If no users exist, show setup instead
    session = get_session()
    if get_user_count(session) == 0:
        session.close()
        render_setup()
        return
    session.close()

    ui.add_css("""
        .login-container { 
            display: flex; justify-content: center; align-items: center; 
            min-height: 100vh; background: #1a1a2e; 
        }
        .login-card { width: 400px; padding: 40px; }
    """)

    with ui.column().classes("login-container"):
        with ui.card().classes("login-card"):
            with ui.column().classes("items-center w-full gap-4"):
                ui.icon("lan").classes("text-5xl text-primary")
                ui.label("Home Lab Manager").classes("text-2xl font-bold")
                ui.label("Sign in to continue").classes("text-gray-500 text-sm")

                username_input = ui.input("Username").classes("w-full").props(
                    'outlined dense'
                )
                password_input = ui.input("Password", password=True, password_toggle_button=True).classes(
                    "w-full"
                ).props('outlined dense')

                error_label = ui.label("").classes("text-red text-sm")

                def do_login():
                    session = get_session()
                    user = authenticate(session, username_input.value, password_input.value)
                    session.close()

                    if user:
                        app.storage.user["authenticated"] = True
                        app.storage.user["username"] = user.username
                        app.storage.user["role"] = user.role
                        app.storage.user["user_id"] = user.id
                        ui.navigate.to("/")
                    else:
                        error_label.text = "Invalid username or password"
                        password_input.value = ""

                password_input.on("keydown.enter", lambda: do_login())

                ui.button("Sign In", on_click=do_login).classes("w-full").props(
                    "color=primary size=lg"
                )


def render_setup():
    """Render the initial setup page (create first admin user)."""
    ui.add_css("""
        .login-container { 
            display: flex; justify-content: center; align-items: center; 
            min-height: 100vh; background: #1a1a2e; 
        }
        .login-card { width: 400px; padding: 40px; }
    """)

    with ui.column().classes("login-container"):
        with ui.card().classes("login-card"):
            with ui.column().classes("items-center w-full gap-4"):
                ui.icon("lan").classes("text-5xl text-primary")
                ui.label("Home Lab Manager").classes("text-2xl font-bold")
                ui.label("Create your admin account").classes("text-gray-500 text-sm")
                ui.label(
                    "This is a one-time setup. You'll use these credentials to log in."
                ).classes("text-xs text-gray-400 text-center")

                setup_username = ui.input("Username", value="admin").classes("w-full").props(
                    'outlined dense'
                )
                setup_password = ui.input("Password", password=True, password_toggle_button=True).classes(
                    "w-full"
                ).props('outlined dense')
                setup_confirm = ui.input("Confirm Password", password=True).classes(
                    "w-full"
                ).props('outlined dense')

                error_label = ui.label("").classes("text-red text-sm")

                def do_setup():
                    if not setup_username.value or not setup_password.value:
                        error_label.text = "Username and password are required"
                        return
                    if len(setup_password.value) < 4:
                        error_label.text = "Password must be at least 4 characters"
                        return
                    if setup_password.value != setup_confirm.value:
                        error_label.text = "Passwords don't match"
                        return

                    session = get_session()
                    create_user(session, setup_username.value, setup_password.value, role="admin")
                    session.close()

                    # Auto-login
                    app.storage.user["authenticated"] = True
                    app.storage.user["username"] = setup_username.value.strip().lower()
                    app.storage.user["role"] = "admin"
                    ui.notify("Admin account created!", type="positive")
                    ui.navigate.to("/")

                ui.button("Create Account", on_click=do_setup).classes("w-full").props(
                    "color=primary size=lg"
                )


def render_change_password():
    """Render password change form (used in settings)."""
    with ui.card().classes("w-full mt-4"):
        ui.label("Change Password").classes("text-lg font-semibold mb-2")

        current_pw = ui.input("Current Password", password=True, password_toggle_button=True).classes("w-full")
        new_pw = ui.input("New Password", password=True, password_toggle_button=True).classes("w-full")
        confirm_pw = ui.input("Confirm New Password", password=True).classes("w-full")

        def do_change():
            if not current_pw.value or not new_pw.value:
                ui.notify("All fields required", type="warning")
                return
            if new_pw.value != confirm_pw.value:
                ui.notify("New passwords don't match", type="warning")
                return
            if len(new_pw.value) < 4:
                ui.notify("Password must be at least 4 characters", type="warning")
                return

            session = get_session()
            user = authenticate(session, app.storage.user.get("username", ""), current_pw.value)
            if not user:
                ui.notify("Current password is incorrect", type="negative")
                session.close()
                return

            change_password(session, user.id, new_pw.value)
            session.close()
            ui.notify("Password changed!", type="positive")
            current_pw.value = ""
            new_pw.value = ""
            confirm_pw.value = ""

        ui.button("Change Password", on_click=do_change).props("color=primary size=sm").classes("mt-2")
