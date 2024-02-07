import os.path
import shutil
import pandas as pd
import re
from datetime import date


FILELIST_PATH = 'filelist.csv'
KEYWORDS_PATH = 'parameters.xlsx'


class GeomechClassifier:

    def __init__(self):
        self.filelist_df = self.load_filelist(FILELIST_PATH)
        self.keywords_df = self.load_keywords(KEYWORDS_PATH)
        self.patterns_dict = self.create_patterns()
        self.pathlist = []
        self.labels = []
        self.n_keywords = []
        self.report_df = pd.DataFrame()
        self.tmp_folder = r""

    @staticmethod
    def load_filelist(filelist_path):
        try:
            return pd.read_csv(filelist_path, encoding='utf-8')
        except FileNotFoundError:
            print(f"Filelist: {filelist_path} not found")

    @staticmethod
    def load_keywords(keywords_path):
        try:
            df = pd.read_excel(keywords_path, skiprows=3)
            df.columns = df.columns.str.upper()

            # Text prepreocessing (mirroring self.text_preprocessing)
            # Removing special characters
            df = df.replace(r'\W', ' ', regex=True)
            # Remove single characters
            df = df.replace(r'\s+[a-zA-Z]\s+', ' ', regex=True)
            # Remove single characters from the start
            df = df.replace(r'\^[a-zA-Z]\s+', ' ', regex=True)
            # Substituting multiple spaces with single space
            df = df.replace(r'\s+', ' ', regex=True)
            # Removing prefixed 'b'
            df = df.replace(r'^b\s+', '', regex=True)
            # Apply lowercase
            df = df.apply(lambda x: x.str.lower())

            return df

        except FileNotFoundError:
            print(f"Filelist: {keywords_path} not found")

    def create_patterns(self):

        def series_to_pattern(col, df=self.keywords_df):
            pattern = "|".join(r"\b" + df[col].dropna() + r"\b")
            return f"({pattern})"

        patterns = {}

        dcm = series_to_pattern('DCM')
        lot = series_to_pattern('LOT')
        geomech = series_to_pattern('GEOMECH')
        wells = series_to_pattern('WELLS')

        patterns['DCM'] = dcm
        patterns['LOT'] = lot
        patterns['GEOMECH'] = geomech
        patterns['WELLS'] = wells

        return patterns

    def classify(self, ext, n=0):

        print(f"{ext} cLassification started.")

        if type(ext) == list:
            for format in ext:
                print(f"{format} format")
                self.classify(format, n)
            return

        ext = self.clean_ext(ext)
        self.pathlist = self.filter_format(ext)
        self.labels = []
        self.n_keywords = []
        self.kwords = []

        if n > 0:
            self.pathlist = self.pathlist[:n]

        for i, path in enumerate(self.pathlist, start=1):

            if ext in ('.XLS'):
                self.excel(path)

            elif ext in ('.DSB', '.OUT', '.FAO', '.TB', '.STR', '.LOG', '.TXT'):
                self.txt(path)

            else:
                print(f"File extension {ext} not recognized. Update the code. \nDefaulting to text file.")
                self.txt(path)


            if i % 10 == 0:
                print(f'File {i}')

        self.report_df = pd.DataFrame(
            {'ABSPATH': self.pathlist,
             'LABEL': self.labels,
             'N_KEYWORDS': self.n_keywords,
             'KEYWORDS': self.kwords}
        )

        self.report_df.to_csv(
            os.path.join('Reports',
                         f'report_{ext[1:]}_{date.today().strftime("%Y%m%d")}.csv'),
                              encoding='utf-8')
        print('Report saved.')

        self.clean_up()

        print('Finished.')

    def excel(self, path):
        from xlrd.biffh import XLRDError
        from xlrd.formula import FormulaError

        try:
            workbook = pd.read_excel(path, engine='xlrd', sheet_name=None)
        except XLRDError:
            self.labels.append('FILE NOT SUPPORTED')
            self.n_keywords.append('FILE NOT SUPPORTED')
            self.kwords.append('FILE NOT SUPPORTED')
            return
        except FileNotFoundError:
            long_path = self.long_path(path)
            self.excel(long_path)
            return
        except FormulaError:
            self.labels.append('FORMULA ERROR')
            self.n_keywords.append('FORMULA ERROR')
            self.kwords.append('FORMULA ERROR')
            return
        except:
            self.labels.append('OTHER ERROR')
            self.n_keywords.append('OTHER ERROR')
            self.kwords.append('OTHER ERROR')
            return

        wb_labels_dict = {'DCM': 0,
                          'Probable DCM': 0,
                          'GEOMECH': 0,
                          'LOT': 0,
                          'WELLS': 0,
                          'CHECK MANUALLY': 0}

        wb_kwords_dict = {'DCM': '',
                          'Probable DCM': '',
                          'GEOMECH': '',
                          'LOT': '',
                          'WELLS': '',
                          'CHECK MANUALLY': ''}

        for tab in workbook.values():
            document = tab.dropna(how='all').to_string()
            label, n_keywords, kwords = self.check_keywords(document)
            wb_labels_dict[label] += n_keywords
            wb_kwords_dict[label] += str(kwords)

        # Only leave labels with more than 0 keywords unless no labels were found (thus label = 'CHECK MANUALLY')
        if set(wb_labels_dict.values()) == {0}:
            wb_labels_dict = {'CHECK MANUALLY': 0}
            wb_kwords_dict = {'CHECK MANUALLY': ''}
        else:
            wb_labels_dict = {key: val for (key, val) in wb_labels_dict.items() if val > 0}
            wb_kwords_dict = {key: val for (key, val) in wb_kwords_dict.items() if len(val) > 0}

        wb_labels = ';'.join(wb_labels_dict.keys())
        wb_n_keywords = ';'.join(map(str, wb_labels_dict.values()))
        wb_kwords = ';'.join(map(str, wb_kwords_dict.values()))

        self.labels.append(wb_labels)
        self.n_keywords.append(wb_n_keywords)
        self.kwords.append(wb_kwords)

    def check_keywords(self, document: str):

        # Preprocessing step
        document = self.text_preprocessing(document, special_chars=True)

        dcm_test = re.findall(self.patterns_dict['DCM'], document)
        if dcm_test:
            return 'DCM', len(dcm_test), dcm_test

        dcm_probable_test = re.findall('dcm', document)
        if dcm_probable_test:
            return 'Probable DCM', len(dcm_probable_test), dcm_probable_test

        lot_test = re.findall(self.patterns_dict['LOT'], document)
        if lot_test:
            return 'LOT', len(lot_test), lot_test

        geomech_test = re.findall(self.patterns_dict['GEOMECH'], document)
        if geomech_test:
            return 'GEOMECH', len(geomech_test), geomech_test

        wells_test = re.findall(self.patterns_dict['WELLS'], document)
        if wells_test:
            return 'WELLS', len(wells_test), wells_test

        # If no keywords were found
        return 'CHECK MANUALLY', 0, ''

    def txt(self, path):
        try:
            with open(path) as txtfile:
                document = txtfile.read()
        except FileNotFoundError:
            long_path = self.long_path(path)
            self.txt(long_path)
            return

        label, n_keywords, kwords = self.check_keywords(document)

        self.labels.append(label)
        self.n_keywords.append(n_keywords)
        self.kwords.append(kwords)

    def tmp(self, path):
        """Copies file into tmp folder. Used when filepath is too large to correctly read file."""
        tmp_path = shutil.copy(path, self.tmp_folder)

        return tmp_path

    def long_path(self, path):
        """
        Fixes paths with over 258 characters to be used in Windows
        https://stackoverflow.com/questions/29557760/long-paths-in-python-on-windows
        """

        if path.startswith(u"\\\\"):
            long_path = u"\\\\?\\UNC\\" + path[2:]
        else:
            long_path = u"\\\\?\\" + path

        return long_path

    @staticmethod
    def clean_ext(ext):
        ext = ext.upper()
        if not ext.startswith('.'):
            ext = '.' + ext
        return ext

    def filter_format(self, ext):
        df = self.filelist_df
        return df[df['FORMAT'] == ext]['ABSPATH'].to_list()

    @staticmethod
    def text_preprocessing(doc, special_chars=True):
        # Remove NaNs
        doc = re.sub(r'NaN', ' ', doc)
        # Remove special characters
        if special_chars:
            doc = re.sub(r'\W', ' ', doc)
        # Remove single characters
        doc = re.sub(r'\s+[a-zA-Z]\s+', ' ', doc)
        # Remove single characters from the start
        doc = re.sub(r'\^[a-zA-Z]\s+', ' ', doc)
        # Substituting multiple spaces with single space
        doc = re.sub(r'\s+', ' ', doc, flags=re.I)
        # Removing prefixed 'b'
        doc = re.sub(r'^b\s+', '', doc)
        # Converting to Lowercase
        doc = doc.lower()

        return doc

    def clean_up(self):
        """Post classification clean-up"""

        # Removing contents of tmp folder
        for file in os.listdir(self.tmp_folder):
            os.remove(file)


if __name__ == '__main__':
    gc = GeomechClassifier()
