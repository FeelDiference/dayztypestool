import os
import xml.etree.ElementTree as ET
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox, QSlider, QComboBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

class MassEditDialog(QDialog):
    def __init__(self, xml_logic, parent=None):
        super().__init__(parent)
        self.xml_logic = xml_logic
        self.parent = parent

        # Initialize slider values
        self.lifetime_slider_value = parent.lifetime_slider_value
        self.restock_slider_value = parent.restock_slider_value

        # Initialize original values
        self.original_values = {
            'lifetime': self.get_initial_values('lifetime'),
            'restock': self.get_initial_values('restock')
        }

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Mass Edit")
        self.setGeometry(100, 100, 400, 600)

        layout = QVBoxLayout()

        # Create multiplier buttons
        multiplier_layout = QHBoxLayout()
        self.multiplier_buttons = {
            'x10': QPushButton("X10", self),
            'x5': QPushButton("X5", self),
            'x2': QPushButton("X2", self),
            'standard': QPushButton("Standard", self),
            'div2': QPushButton("/2", self),
            'div5': QPushButton("/5", self),
            'div10': QPushButton("/10", self)
        }
        for key, button in self.multiplier_buttons.items():
            button.setIcon(QIcon(os.path.join('icons', f'{key}.png')))
            button.clicked.connect(self.onMultiplierClicked)
            multiplier_layout.addWidget(button)
        layout.addLayout(multiplier_layout)

        # Create checkboxes and input fields
        self.parameters = ['nominal', 'min', 'lifetime', 'restock']
        self.checkboxes = {}
        self.input_fields = {}
        for param in self.parameters:
            param_layout = QHBoxLayout()
            checkbox = QCheckBox(param.capitalize(), self)
            self.checkboxes[param] = checkbox
            param_layout.addWidget(checkbox)

            input_field = QLineEdit(self)
            input_field.setPlaceholderText("Enter value manually")
            input_field.textChanged.connect(lambda text, param=param: self.onInputChanged(param))
            self.input_fields[param] = input_field
            param_layout.addWidget(input_field)

            layout.addLayout(param_layout)

        # Create category dropdown
        category_layout = QHBoxLayout()
        category_label = QLabel("Category:", self)
        self.category_combo = QComboBox(self)
        self.category_combo.addItems(self.xml_logic.category_options)
        category_layout.addWidget(category_label)
        category_layout.addWidget(self.category_combo)
        layout.addLayout(category_layout)

        # Create sliders for lifetime and restock
        self.create_slider(layout, "Lifetime")
        self.create_slider(layout, "Restock")

        # Create buttons to add Usage, Value, Tag
        self.create_add_button(layout, "Usage")
        self.create_add_button(layout, "Value")
        self.create_add_button(layout, "Tag")

        # Create OK and Cancel buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK", self)
        ok_button.clicked.connect(self.onOk)
        button_layout.addWidget(ok_button)

        cancel_button = QPushButton("Cancel", self)
        cancel_button.clicked.connect(self.onCancel)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def create_slider(self, layout, param):
        slider_layout = QHBoxLayout()
        slider_label = QLabel(f"{param} (%):", self)
        slider = QSlider(Qt.Horizontal, self)
        slider.setMinimum(10)
        slider.setMaximum(200)
        slider.setTickInterval(10)
        slider.setTickPosition(QSlider.TicksBelow)
        slider_value_label = QLabel(f"{getattr(self, f'{param.lower()}_slider_value')}%", self)
        slider.setValue(getattr(self, f'{param.lower()}_slider_value'))
        slider.valueChanged.connect(lambda value: self.update_slider_label(slider_value_label, value, param.lower()))

        avg_value_label = QLabel(self)
        self.update_avg_value_label(param.lower(), avg_value_label)

        slider_layout.addWidget(slider_label)
        slider_layout.addWidget(slider)
        slider_layout.addWidget(slider_value_label)
        slider_layout.addWidget(avg_value_label)

        if param.lower() == "lifetime":
            self.lifetime_slider = slider
            self.lifetime_slider_label = slider_value_label
            self.lifetime_avg_label = avg_value_label
        elif param.lower() == "restock":
            self.restock_slider = slider
            self.restock_slider_label = slider_value_label
            self.restock_avg_label = avg_value_label

        layout.addLayout(slider_layout)

    def create_add_button(self, layout, param):
        add_layout = QHBoxLayout()
        add_button = QPushButton(f"Add {param}", self)
        add_combo = QComboBox(self)
        add_combo.addItems(getattr(self.xml_logic, f"{param.lower()}_options"))
        add_button.clicked.connect(lambda: self.onAddClicked(param, add_combo))
        add_layout.addWidget(add_button)
        add_layout.addWidget(add_combo)
        layout.addLayout(add_layout)
        setattr(self, f"{param.lower()}_combo", add_combo)
        setattr(self, f"{param.lower()}_layouts", [])

    def onAddClicked(self, param, combo):
        layout = QHBoxLayout()
        label = QLabel(f"{param}:", self)
        value_combo = QComboBox(self)
        value_combo.addItems(combo.itemText(i) for i in range(combo.count()))
        remove_button = QPushButton("Remove", self)
        remove_button.clicked.connect(lambda: self.onRemoveClicked(layout, param, value_combo))

        layout.addWidget(label)
        layout.addWidget(value_combo)
        layout.addWidget(remove_button)

        self.layout().insertLayout(self.layout().count() - 3, layout)
        getattr(self, f"{param.lower()}_layouts").append((layout, value_combo))

    def onRemoveClicked(self, layout, param, combo):
        self.layout().removeItem(layout)
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        getattr(self, f"{param.lower()}_layouts").remove((layout, combo))

    def update_slider_label(self, label, value, param):
        label.setText(f"{value}%")
        print(f"Slider {label.text()} updated to {value}%")
        self.update_avg_value_label(param, getattr(self, f"{param}_avg_label"), value)

    def update_avg_value_label(self, param, label, slider_value=100):
        original_values = self.original_values[param]
        if original_values:
            total_value = sum(original_values)
            avg_value = total_value / len(original_values)
            adjusted_avg_value = avg_value * (slider_value / 100)
            adjusted_avg_value_minutes = adjusted_avg_value / 60
            label.setText(f"Avg: {adjusted_avg_value_minutes:.2f} min")

    def onMultiplierClicked(self):
        sender = self.sender()
        multiplier = 1
        if sender == self.multiplier_buttons['x10']:
            multiplier = 10
        elif sender == self.multiplier_buttons['x5']:
            multiplier = 5
        elif sender == self.multiplier_buttons['x2']:
            multiplier = 2
        elif sender == self.multiplier_buttons['div2']:
            multiplier = 0.5
        elif sender == self.multiplier_buttons['div5']:
            multiplier = 0.2
        elif sender == self.multiplier_buttons['div10']:
            multiplier = 0.1
        elif sender == self.multiplier_buttons['standard']:
            self.loadStandardValues()
            return

        self.xml_logic.saveCurrentItemDetails()  # Сохранить текущий объект перед массовыми изменениями

        for param in self.parameters:
            if self.checkboxes[param].isChecked() and not self.input_fields[param].text():
                for item in self.xml_logic.get_selected_items():
                    element = item.find(param)
                    if element is not None and element.text.isdigit():
                        current_value = int(element.text)
                        new_value = int(current_value * multiplier)
                        element.text = str(new_value)
                        self.xml_logic.viewer.update_item_in_list(item)

    def onInputChanged(self, param):
        self.checkboxes[param].setEnabled(not self.input_fields[param].text())

    def onOk(self):
        self.xml_logic.saveCurrentItemDetails()  # Сохранить текущий объект перед массовыми изменениями

        selected_items = self.xml_logic.get_selected_items()

        for param in self.parameters:
            if self.input_fields[param].text():
                new_value = self.input_fields[param].text()
                for item in selected_items:
                    element = item.find(param)
                    if element is not None:
                        element.text = new_value
                        self.xml_logic.viewer.update_item_in_list(item)

        # Apply category
        new_category = self.category_combo.currentText()
        for item in selected_items:
            category_element = item.find('category')
            if category_element is not None:
                category_element.set('name', new_category)
            else:
                ET.SubElement(item, 'category', name=new_category)
            self.xml_logic.viewer.update_item_in_list(item)

        # Apply Usage, Value, Tag
        self.apply_combo_values('usage', selected_items)
        self.apply_combo_values('value', selected_items)
        self.apply_combo_values('tag', selected_items)

        # Apply slider values
        self.apply_slider_value('lifetime', self.lifetime_slider.value())
        self.apply_slider_value('restock', self.restock_slider.value())

        # Save slider values
        self.lifetime_slider_value = self.lifetime_slider.value()
        self.restock_slider_value = self.restock_slider.value()
        print(f"Saving slider values: Lifetime: {self.lifetime_slider_value}%, Restock: {self.restock_slider_value}%")

        self.parent.lifetime_slider_value = self.lifetime_slider_value
        self.parent.restock_slider_value = self.restock_slider_value

        self.accept()
        self.xml_logic.viewer.loadXMLItems()  # Перезагрузить элементы XML

        # Восстановить последний активный элемент
        if selected_items:
            last_item_name = selected_items[-1].get('name')
            for index in range(self.xml_logic.viewer.list_widget.count()):
                list_item = self.xml_logic.viewer.list_widget.item(index)
                if list_item.text() == last_item_name:
                    self.xml_logic.viewer.list_widget.setCurrentItem(list_item)
                    self.xml_logic.viewer.displayItemDetails(list_item)
                    break

    def apply_combo_values(self, param, selected_items):
        layouts = getattr(self, f"{param}_layouts")
        for layout, combo in layouts:
            value = combo.currentText()
            for item in selected_items:
                if param == 'tag':
                    tag_element = ET.SubElement(item, param, name=value)
                    tag_element.set('name', value)
                else:
                    ET.SubElement(item, param, name=value)
                self.xml_logic.viewer.update_item_in_list(item)

    def onCancel(self):
        self.reject()

    def apply_slider_value(self, param, slider_value):
        selected_items = self.xml_logic.get_selected_items()
        for item in selected_items:
            element = item.find(param)
            if element is not None and element.text.isdigit():
                original_value = self.original_values[param][selected_items.index(item)]
                new_value = int(original_value * (slider_value / 100))
                element.text = str(new_value)
                self.xml_logic.viewer.update_item_in_list(item)

    def loadStandardValues(self):
        config_file = os.path.join('Config', 'default_config.xml')
        if os.path.exists(config_file):
            tree = ET.parse(config_file)
            root = tree.getroot()
            for param in self.parameters:
                standard_value = root.find(param).text
                for item in self.xml_logic.get_selected_items():
                    element = item.find(param)
                    if element is not None:
                        element.text = standard_value
                        self.xml_logic.viewer.update_item_in_list(item)

    def load_slider_values(self):
        self.lifetime_slider.setValue(self.lifetime_slider_value)
        self.lifetime_slider_label.setText(f"{self.lifetime_slider_value}%")
        self.restock_slider.setValue(self.restock_slider_value)
        self.restock_slider_label.setText(f"{self.restock_slider_value}%")
        print(f"Loading slider values: Lifetime: {self.lifetime_slider_value}%, Restock: {self.restock_slider_value}%")

    def showEvent(self, event):
        super().showEvent(event)
        self.load_slider_values()

    def closeEvent(self, event):
        super().closeEvent(event)
        self.lifetime_slider_value = self.lifetime_slider.value()
        self.restock_slider_value = self.restock_slider.value()
        print(f"Closing dialog. Current slider values: Lifetime: {self.lifetime_slider_value}%, Restock: {self.restock_slider_value}%")

    def get_initial_values(self, param):
        return [
            int(item.find(param).text) for item in self.xml_logic.get_selected_items() if item.find(param) is not None and item.find(param).text.isdigit()
        ]
