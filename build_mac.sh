#!/bin/bash

echo "Limpando builds anteriores..."
rm -rf build/ dist/ SistemaMeuBazar.spec

echo "Iniciando compilação do Sistema Meu Bazar para macOS..."

python3 -m PyInstaller --name "SistemaMeuBazar" \
  --windowed \
  --add-data "ui/themes:ui/themes" \
  --add-data "assets:assets" \
  --hidden-import="PyQt6" \
  --hidden-import="PyQt6.QtWidgets" \
  --hidden-import="PyQt6.QtCore" \
  --hidden-import="PyQt6.QtGui" \
  --hidden-import="PyQt6.QtPrintSupport" \
  --hidden-import="mysql.connector" \
  --hidden-import="mysql.connector.locales.eng" \
  --hidden-import="mysql.connector.plugins.mysql_native_password" \
  --hidden-import="barcode" \
  --hidden-import="barcode.writer" \
  --hidden-import="requests" \
  --hidden-import="bcrypt" \
  --hidden-import="openpyxl" \
  main.py

echo "Compilação finalizada! O app está na pasta dist/."

echo "Criando imagem DMG..."
mkdir -p dist/dmg_content
cp -R "dist/SistemaMeuBazar.app" "dist/dmg_content/"
ln -s /Applications "dist/dmg_content/Applications"

hdiutil create -volname "Sistema Meu Bazar" -srcfolder "dist/dmg_content" -ov -format UDZO "SistemaMeuBazar.dmg"

rm -rf dist/dmg_content
echo "DMG criado com sucesso: SistemaMeuBazar.dmg"
