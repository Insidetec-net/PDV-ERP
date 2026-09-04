from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from config.settings import DB_CONFIG, save_local_config
from database.setup import check_mysql_available, _connect_without_db, _execute_sql_script, _read_sql_file

class SetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuração do Banco de Dados")
        self.setFixedSize(450, 480)
        self.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4;")
        self.setup_successful = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        title = QLabel("☁️ Conectar à Nuvem (MySQL)")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #89b4fa;")
        layout.addWidget(title)

        desc = QLabel("Insira as credenciais do seu banco de dados Hostinger:")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)
        
        layout.addSpacing(10)

        # Campos
        self.host_input = self._create_input("Host / IP do Servidor:", DB_CONFIG.get("host", "127.0.0.1"))
        layout.addWidget(self.host_input["label"])
        layout.addWidget(self.host_input["field"])

        self.port_input = self._create_input("Porta:", str(DB_CONFIG.get("port", 3306)))
        layout.addWidget(self.port_input["label"])
        layout.addWidget(self.port_input["field"])

        self.db_input = self._create_input("Nome do Banco:", "u836386780_meubazar")
        layout.addWidget(self.db_input["label"])
        layout.addWidget(self.db_input["field"])

        self.user_input = self._create_input("Usuário:", "u836386780_meubazar")
        layout.addWidget(self.user_input["label"])
        layout.addWidget(self.user_input["field"])

        self.pass_input = self._create_input("Senha:", "CQjTA~1#t", password=True)
        layout.addWidget(self.pass_input["label"])
        layout.addWidget(self.pass_input["field"])

        layout.addStretch()

        btn_layout = QHBoxLayout()
        self.connect_btn = QPushButton("Conectar e Criar Tabelas")
        self.connect_btn.setMinimumHeight(40)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #a6e3a1; color: #11111b; font-weight: bold; border-radius: 6px;
            }
            QPushButton:hover { background-color: #94e289; }
        """)
        self.connect_btn.clicked.connect(self._on_connect)
        btn_layout.addWidget(self.connect_btn)

        layout.addLayout(btn_layout)

    def _create_input(self, label_text, default_value, password=False):
        label = QLabel(label_text)
        label.setFont(QFont("Segoe UI", 10))
        field = QLineEdit(default_value)
        field.setMinimumHeight(35)
        field.setStyleSheet("background-color: #313244; border: 1px solid #45475a; border-radius: 4px; padding: 5px;")
        if password:
            field.setEchoMode(QLineEdit.EchoMode.Password)
        return {"label": label, "field": field}

    def _on_connect(self):
        host = self.host_input["field"].text().strip()
        port = int(self.port_input["field"].text().strip() or 3306)
        db = self.db_input["field"].text().strip()
        user = self.user_input["field"].text().strip()
        password = self.pass_input["field"].text().strip()

        self.connect_btn.setText("Conectando...")
        self.connect_btn.setEnabled(False)
        QApplication.processEvents()

        try:
            conn = _connect_without_db(host, port, user, password)
            cursor = conn.cursor()
            
            # Hostinger não permite CREATE DATABASE via script externo. Vamos direto pro USE.
            cursor.execute(f"USE `{db}`")
            
            # Rodar schema e seeds
            schema_sql = _read_sql_file("schema.sql")
            _execute_sql_script(conn, schema_sql)
            
            seeds_sql = _read_sql_file("seeds.sql")
            _execute_sql_script(conn, seeds_sql)
            
            conn.close()

            # Salvar credenciais no config.json
            new_config = {
                "host": host,
                "port": port,
                "user": user,
                "password": password,
                "database": db
            }
            save_local_config(db_config=new_config)

            QMessageBox.information(self, "Sucesso!", "Conexão com a nuvem estabelecida e tabelas criadas com sucesso!\n\nLogin padrão:\nUsuário: admin\nSenha: admin123")
            self.setup_successful = True
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Erro Técnico", f"A conexão falhou com o seguinte erro retornado pelo servidor:\n\n{e}\n\nVerifique se o IP ou a senha estão 100% corretos.")
            self.connect_btn.setText("Conectar e Criar Tabelas")
            self.connect_btn.setEnabled(True)
