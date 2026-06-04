"""
Instala o Portfolio DCA Monitor como atalho clicavel no sistema.

Windows : cria atalho na Area de Trabalho com icone — pode fixar na barra de tarefas
Linux   : cria entrada no menu de aplicativos — pode fixar no dock/painel

Uso (a partir da raiz do projeto ou da pasta config/):
    python config/install.py
"""
import sys
import subprocess
from pathlib import Path

# install.py fica em config/, entao a raiz do projeto eh o parent
BASE_DIR  = Path(__file__).parent.parent.resolve()
MAIN_PYW  = BASE_DIR / "main.pyw"
ICON_FILE = BASE_DIR / "img" / "favicon.ico"

APP_NAME = "Portfolio DCA Monitor"


def install_windows() -> None:
    pythonw = Path(sys.executable).parent / "pythonw.exe"
    if not pythonw.exists():
        pythonw = Path(sys.executable)

    desktop  = Path.home() / "Desktop"
    shortcut = desktop / f"{APP_NAME}.lnk"

    ps = f"""
$sh = New-Object -ComObject WScript.Shell
$lnk = $sh.CreateShortcut('{shortcut}')
$lnk.TargetPath       = '{pythonw}'
$lnk.Arguments        = '"{MAIN_PYW}"'
$lnk.IconLocation     = '{ICON_FILE}'
$lnk.WorkingDirectory = '{BASE_DIR}'
$lnk.Description      = '{APP_NAME} — Monitor de Portfolio DCA de Criptomoedas'
$lnk.Save()
"""
    result = subprocess.run(["powershell", "-Command", ps], capture_output=True)
    if result.returncode == 0:
        print(f"Atalho criado em: {shortcut}")
        print()
        print("Para fixar na barra de tarefas:")
        print("  Clique direito no atalho da area de trabalho -> Fixar na barra de tarefas")
    else:
        print("Erro ao criar atalho:")
        print(result.stderr.decode())


def install_linux() -> None:
    apps_dir = Path.home() / ".local" / "share" / "applications"
    apps_dir.mkdir(parents=True, exist_ok=True)

    python       = sys.executable
    desktop_file = apps_dir / "dca-portfolio-monitor.desktop"

    desktop_file.write_text(
        f"[Desktop Entry]\n"
        f"Name={APP_NAME}\n"
        f"Comment=Monitor de Portfolio DCA de Criptomoedas\n"
        f"Exec={python} \"{MAIN_PYW}\"\n"
        f"Icon={ICON_FILE}\n"
        f"Terminal=false\n"
        f"Type=Application\n"
        f"Categories=Finance;Utility;\n"
        f"StartupWMClass=main\n",
        encoding="utf-8",
    )
    desktop_file.chmod(0o755)
    subprocess.run(["update-desktop-database", str(apps_dir)], capture_output=True)

    print(f"Entrada criada em: {desktop_file}")
    print()
    print("Para fixar no dock/painel:")
    print("  Procure 'Portfolio DCA Monitor' no menu de aplicativos e arraste para o dock")
    print("  Ou clique direito -> Adicionar aos favoritos (GNOME/KDE)")


def main() -> None:
    if not MAIN_PYW.exists():
        print(f"Erro: nao encontrei {MAIN_PYW}")
        print("Execute este script a partir da raiz do projeto ou da pasta config/")
        sys.exit(1)

    if sys.platform == "win32":
        install_windows()
    elif sys.platform.startswith("linux"):
        install_linux()
    else:
        print(f"Sistema nao suportado: {sys.platform}")
        print("Plataformas suportadas: Windows e Linux")


if __name__ == "__main__":
    main()
