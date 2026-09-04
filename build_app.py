import PyInstaller.__main__
import os
import shutil

# Limpar builds antigos se existirem
if os.path.exists('build'):
    shutil.rmtree('build')
if os.path.exists('dist'):
    shutil.rmtree('dist')

print("Iniciando build do Sistema Meu Bazar para macOS...")

PyInstaller.__main__.run([
    'main.py',
    '--name=SistemaMeuBazar',
    '--windowed', # Para não abrir terminal de fundo (app nativo)
    '--add-data=ui/themes:ui/themes', # Incluindo a pasta de temas (onde tem o dark_theme.qss)
    '--hidden-import=mysql.connector.locales.eng.client_error',
    '--hidden-import=mysql.connector.plugins.mysql_native_password',
    # '--icon=app.icns', # Ícone (se houver, ignorado se não achar)
    '--clean'
])

print("\n✅ Build finalizado! O arquivo .app está dentro da pasta 'dist/SistemaMeuBazar.app'")
