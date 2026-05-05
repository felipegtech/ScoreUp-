import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLineEdit, QPushButton, QLabel,
                               QScrollArea, QMessageBox, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator


class FilaNota(QWidget):
    """Widget personalizado que representa una fila con Actividad, Nota y Porcentaje"""

    def __init__(self, eliminar_callback):
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Validadores para aceptar solo números decimales
        validador = QDoubleValidator(0.0, 100.0, 2)
        validador.setNotation(QDoubleValidator.StandardNotation)

        # Campo para el nombre de la actividad
        self.input_actividad = QLineEdit()
        self.input_actividad.setPlaceholderText("Ej: Reporte técnico")

        # Campo para la nota
        self.input_nota = QLineEdit()
        self.input_nota.setPlaceholderText("Nota")
        self.input_nota.setFixedWidth(60)
        self.input_nota.setValidator(validador)

        # Campo para el porcentaje
        self.input_porcentaje = QLineEdit()
        self.input_porcentaje.setPlaceholderText("%")
        self.input_porcentaje.setFixedWidth(60)
        self.input_porcentaje.setValidator(validador)

        # Botón para eliminar la fila
        btn_eliminar = QPushButton("❌")
        btn_eliminar.setFixedWidth(30)
        btn_eliminar.setStyleSheet("color: red; border: none; font-weight: bold;")
        btn_eliminar.clicked.connect(lambda: eliminar_callback(self))

        layout.addWidget(QLabel("Actividad:"))
        layout.addWidget(self.input_actividad, stretch=1)
        layout.addWidget(QLabel("Nota:"))
        layout.addWidget(self.input_nota)
        layout.addWidget(QLabel("Peso (%):"))
        layout.addWidget(self.input_porcentaje)
        layout.addWidget(btn_eliminar)

        self.setLayout(layout)

    def obtener_datos(self):
        try:
            nota = float(self.input_nota.text().replace(',', '.')) if self.input_nota.text() else 0.0
            porcentaje = float(self.input_porcentaje.text().replace(',', '.')) if self.input_porcentaje.text() else 0.0
            return nota, porcentaje
        except ValueError:
            return 0.0, 0.0


class CalculadoraApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("¿Cuánto Necesito para el Final?")
        self.setMinimumSize(550, 500)

        self.filas = []

        # Widget principal y layout
        widget_central = QWidget()
        self.layout_principal = QVBoxLayout(widget_central)

        # --- SECCIÓN SUPERIOR: Materia y Meta ---
        header_layout = QHBoxLayout()

        # Nombre de la materia
        header_layout.addWidget(QLabel("Materia:"))
        self.input_materia = QLineEdit("Física II")
        self.input_materia.setPlaceholderText("Nombre de la materia")
        header_layout.addWidget(self.input_materia, stretch=1)

        # Espaciador
        header_layout.addSpacing(20)

        # Nota mínima
        header_layout.addWidget(QLabel("Nota para aprobar:"))
        self.input_meta = QLineEdit("3.0")
        self.input_meta.setFixedWidth(50)
        header_layout.addWidget(self.input_meta)

        self.layout_principal.addLayout(header_layout)

        # Línea separadora
        linea = QFrame()
        linea.setFrameShape(QFrame.HLine)
        linea.setFrameShadow(QFrame.Sunken)
        self.layout_principal.addWidget(linea)

        # --- SECCIÓN CENTRAL: Área con scroll para las notas ---
        self.area_scroll = QScrollArea()
        self.area_scroll.setWidgetResizable(True)
        self.widget_notas = QWidget()
        self.layout_notas = QVBoxLayout(self.widget_notas)
        self.layout_notas.setAlignment(Qt.AlignTop)
        self.area_scroll.setWidget(self.widget_notas)

        self.layout_principal.addWidget(self.area_scroll)

        # --- SECCIÓN INFERIOR: Botones y Resultados ---
        layout_botones = QHBoxLayout()
        btn_agregar = QPushButton("+ Agregar Actividad")
        btn_agregar.clicked.connect(self.agregar_fila)

        btn_calcular = QPushButton("Calcular")
        btn_calcular.setStyleSheet("background-color: #008CBA; color: white; font-weight: bold; padding: 8px;")
        btn_calcular.clicked.connect(self.calcular_resultado)

        layout_botones.addWidget(btn_agregar)
        layout_botones.addWidget(btn_calcular)
        self.layout_principal.addLayout(layout_botones)

        # Etiqueta de resultado
        self.label_resultado = QLabel("Ingresa tus notas y presiona Calcular.")
        self.label_resultado.setAlignment(Qt.AlignCenter)
        self.label_resultado.setWordWrap(True)
        self.label_resultado.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px; min-height: 40px;")
        self.layout_principal.addWidget(self.label_resultado)

        self.setCentralWidget(widget_central)

        # Agregar 3 filas por defecto al iniciar
        for _ in range(3):
            self.agregar_fila()

    def agregar_fila(self):
        fila = FilaNota(self.eliminar_fila)
        self.filas.append(fila)
        self.layout_notas.addWidget(fila)

    def eliminar_fila(self, fila):
        if len(self.filas) > 1:
            self.filas.remove(fila)
            self.layout_notas.removeWidget(fila)
            fila.deleteLater()
            self.calcular_resultado()  # Recalcular automáticamente al borrar
        else:
            QMessageBox.warning(self, "Aviso", "Debes tener al menos una actividad.")

    def calcular_resultado(self):
        try:
            meta = float(self.input_meta.text().replace(',', '.'))
        except ValueError:
            QMessageBox.critical(self, "Error", "La nota mínima debe ser un número.")
            return

        materia = self.input_materia.text().strip()
        nombre_materia = f" en {materia}" if materia else ""

        nota_acumulada = 0.0
        porcentaje_total = 0.0

        for fila in self.filas:
            nota, porcentaje = fila.obtener_datos()
            nota_acumulada += nota * (porcentaje / 100.0)
            porcentaje_total += porcentaje

        if porcentaje_total > 100.0:
            self.label_resultado.setText("¡Error! La suma de los porcentajes supera el 100%. Revisa los datos.")
            self.label_resultado.setStyleSheet("color: red; font-size: 14px; font-weight: bold;")
            return

        porcentaje_faltante = 100.0 - porcentaje_total

        if porcentaje_faltante <= 0.0:
            if nota_acumulada >= meta:
                self.label_resultado.setText(
                    f"¡Felicidades! Ya pasaste{nombre_materia} con una nota de {nota_acumulada:.2f}.")
                self.label_resultado.setStyleSheet("color: green; font-size: 14px; font-weight: bold;")
            else:
                self.label_resultado.setText(
                    f"Tu nota final{nombre_materia} es {nota_acumulada:.2f}. No alcanzó para aprobar.")
                self.label_resultado.setStyleSheet("color: red; font-size: 14px; font-weight: bold;")
            return

        nota_necesaria = (meta - nota_acumulada) / (porcentaje_faltante / 100.0)

        if nota_necesaria <= 0:
            self.label_resultado.setText(f"¡Ya pasaste{nombre_materia}! Llevas {nota_acumulada:.2f} acumulado.")
            self.label_resultado.setStyleSheet("color: green; font-size: 14px; font-weight: bold;")
        elif nota_necesaria > 5.0:  # Asumiendo 5.0 como nota máxima
            self.label_resultado.setText(
                f"Necesitas {nota_necesaria:.2f} en el {porcentaje_faltante:.1f}% restante para pasar{nombre_materia}.\n¡Matemáticamente imposible!")
            self.label_resultado.setStyleSheet("color: red; font-size: 14px; font-weight: bold;")
        else:
            self.label_resultado.setText(
                f"Para pasar{nombre_materia}, necesitas sacar {nota_necesaria:.2f} en el {porcentaje_faltante:.1f}% restante.")
            self.label_resultado.setStyleSheet("color: blue; font-size: 14px; font-weight: bold;")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = CalculadoraApp()
    ventana.show()
    sys.exit(app.exec())