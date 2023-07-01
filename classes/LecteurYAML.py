import yaml


class LecteurYAML:
    def __init__(self, file_path):
        """
        Initialise un objet de la classe LecteurYAML.
        Code par M.Sanjasé et I.Tabiai dans le cadre du cours de MGA802 donné à l'été 23 à l'ÉTS

        Args:
            file_path (str): Chemin du fichier YAML.
        """
        self.file_path = file_path

    def read_yaml(self):
        """
        Lit le fichier YAML spécifié par le chemin et retourne son contenu.
        Code par M.Sanjasé et I.Tabiai dans le cadre du cours de MGA802 donné à l'été 23 à l'ÉTS

        :return: (dict) Contenu du fichier YAML sous forme de dictionnaire.

        :raises yaml.YAMLError: S'il y a une erreur de lecture du fichier YAML.
        """
        with open(self.file_path, 'r') as file:
            try:
                data = yaml.safe_load(file)
                return data
            except yaml.YAMLError as e:
                print(f"Error reading YAML file: {e}")

    def validate_numeric_value_int_float(self, key, value):
        """
        Valide si la valeur spécifiée est un nombre entier ou flottant.

        :param key: (str) Clé correspondant à la valeur en cours de validation.
        :param value: Valeur à valider.

        :raises ValueError: Si la valeur n'est pas un nombre entier ou flottant.
        """
        if not isinstance(value, (int, float)):
            raise ValueError(f"{key} doit être un nombre (int ou float).")

    def validate_numeric_value_int(self, key, value):
        """
        Valide si la valeur spécifiée est un nombre entier.

        :param key: (str) Clé correspondant à la valeur en cours de validation.
        :param value: Valeur à valider.

        :raises ValueError: Si la valeur n'est pas un nombre entier.
        """
        if not isinstance(value, int):
            raise ValueError(f"{key} doit être un nombre entier.")

    def validate_numeric_value_bool(self, key, value):
        """
        Valide si la valeur spécifiée est un booléen.

        :param key: (str) Clé correspondant à la valeur en cours de validation.
        :param value: Valeur à valider.

        :raises ValueError: Si la valeur n'est pas un booléen.
        """
        if not isinstance(value, bool):
            raise ValueError(f"{key} doit être un booléen.")

    def inferiorite(self, key1, key2, val1, val2):
        """
        Vérifie si une valeur est inférieure à une autre valeur donnée.

        :param key1: (str) Clé correspondant à la première valeur.
        :param key2: (str) Clé correspondant à la deuxième valeur.
        :param val1: Première valeur à comparer.
        :param val2: Deuxième valeur à comparer.

        :raises ValueError: Si la première valeur n'est pas inférieure à la deuxième valeur.
        """
        if val1 >= val2:
            raise ValueError(f"La valeur de {key1} doit être inférieure à la valeur de {key2}.")



