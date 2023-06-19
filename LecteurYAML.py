"""
Code par M.Sanjasé et I.Tabiai dans le cadre du cours de MGA802 donné à l'été 23 à l'ÉTS
"""
import yaml


class LecteurYAML:
    def __init__(self, file_path):
        self.file_path = file_path

    def read_yaml(self):
        with open(self.file_path, 'r') as file:
            try:
                data = yaml.safe_load(file)
                return data
            except yaml.YAMLError as e:
                print(f"Error reading YAML file: {e}")

    def validate_numeric_value_int_float(self, key, value):
        if not isinstance(value, (int, float)):
            raise ValueError(f"{key} doit être un nombre (int ou float).")

    def validate_numeric_value_int(self, key, value):
        if not isinstance(value, int):
            raise ValueError(f"{key} doit être un nombre entier.")



