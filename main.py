from __future__ import annotations

from auth import AuthWindow
from dashboard import MainApp


def launch_auth():
    app = AuthWindow(on_success=launch_main)
    app.mainloop()


def launch_main(user):
    app = MainApp(user=user, on_logout=launch_auth)

    def safe_close():
        try:
            app.quit()
            app.destroy()
        except:
            pass

    app.protocol("WM_DELETE_WINDOW", safe_close)
    app.mainloop()


if __name__ == "__main__":
    launch_auth()