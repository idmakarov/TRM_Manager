import fnmatch
import os
import re
import sys

import fitz

import config


class Transmittal:
    """
    The class is purposed for creation and processing transmittal with properties:
    name, path, documents and phase.
    
    Attributes
    ----------
    check_docs_name : bool, default=False
        If True, documents name will be checked for correctness: if a name is incorrect, the file will be renamed
        corresponding to the name given in its title page.
    documents : dict
        Documents dictionary, which values contain properties of corresponding document.
    name : str
        Name of the transmittal.
    path : str
        Absolute path to the transmittal folder.
    phase : str
        Phase of documents located in the transmittal folder.

    Methods
    -------
    update(update_docs=False)
        Refreshes the transmittal path and optionally updates files in it.
    """
    def __init__(self, name: str, path: str, check_docs_name=False):
        self.name = name

        if os.path.isabs(path):
            self.path = path
        else:
            self.path = os.path.abspath(path)

        self.check_docs_name = check_docs_name
            
        self.__cfg = config.get_config()
        
        self.phase = None
        self.documents = self.__collect_docs()
    
    def __get_docs_in_subfolders(self):
        """
        Looks for documents in subfolders.

        Returns
        -------
        None
        """
        print('Trying to find docs in subfolders')
        file_list = []
        folder_mask = self.__cfg[1]['vdr_mask']
        # Сформируем маску для поиска папки с именем документа
        folder_mask = folder_mask.split(r'.xlsx')[0]
        for item in os.listdir(self.path):
            subfolder = os.path.join(self.path, item)
            if os.path.isdir(subfolder):
                if fnmatch.fnmatch(item, folder_mask):
                    # Выполним поиск внутри подпапки
                    print('Trying to find docs in {}'.format(subfolder))
                    try:
                        doc_name = self.__get_docs(subfolder)[0]
                        file_list.append(doc_name)
                    except IndexError:
                        print('ERROR: {}.pdf was not found!'.format(item), file=sys.stderr)
        return file_list

    def __get_docs(self, path: str):
        """
        Looks for documents in path provided.

        Parameters
        ----------
        path : str
            Path to folder in which documents are looked for.

        Returns
        -------
        None
        """
        file_list = []
        mask = self.__cfg[1]['vdr_mask']
        mask = mask.split('*')[0] + '*.pdf'
        alt_mask = mask.split('*')[0] + '*.PDF'
        for item in os.listdir(path):
            if (fnmatch.fnmatch(item, mask) or fnmatch.fnmatch(item, alt_mask)) and 'crs' not in item.lower():

                self.phase = item.split('.')[1]
                if self.phase == '0':
                    self.phase = '1'
                if 'att' not in item.lower():
                    doc_name = item

                    if self.check_docs_name:
                        # Проверим название документа на опечатки
                        doc_name = self.__get_doc_name_checked(item, path)

                    # Отбросим ненужную часть названия документа '.pdf'
                    doc_name = doc_name[:-4]
                else:
                    doc_name = item[:-4]
                file_list.append(doc_name)
        return file_list

    def __get_doc_name_checked(self, file_name: str, file_dir: str):
        """
        Checks documents name for correctness.
        If a name is incorrect then renames file in according to filename in title page.

        Parameters
        ----------
        file_dir : str
            Path to folder containing target file.
        file_name : str
            Name of the file to be checked.

        Returns
        -------
        None
        """
        src = os.path.join(file_dir, file_name)
        with fitz.open(src) as f:
            page1_text = f.loadPage(0).getText('text')

        mask = self.__cfg[1]['vdr_mask']
        pattern1 = mask.split('.')[0] + r'.*ER.*\.\w{3}'
        pattern2 = mask.split('.')[0] + r'.*-\d{4}'

        find1 = re.findall(pattern1, page1_text)
        find2 = re.findall(pattern2, page1_text)

        if find1:
            if file_name == find1[0]:
                return file_name
            else:
                print('WARNING: the file name is not correct for {}!'.format(file_name))
                new_name = find1[0]
                dst = os.path.join(file_dir, new_name)
                try:
                    os.rename(src, dst)
                    print('File name was successfully changed')
                except FileNotFoundError:
                    pass
                return new_name
        elif find2:
            s = re.sub(r'_.*$', '', file_name)
            s = re.sub(r'-(?=[\w\d]{2}-[\d]{4})', r'.', s)
            if s == find2[0]:
                return file_name
            else:
                print('WARNING: the file name is not correct for {}!'.format(file_name))
                sub1 = re.sub(r'\.(?=[\w\d]{2}-[\d]{4})', r'-', find2[0])
                sub2 = re.findall(r'_\d\d_\w\w.*$', file_name)[0]
                new_name = sub1 + sub2
                dst = os.path.join(file_dir, sub1 + sub2)
                try:
                    os.rename(src, dst)
                    print('File name was successfully changed')
                except FileNotFoundError:
                    pass
                return new_name
        else:
            return file_name
    
    def __collect_docs(self):
        """
        Collects all required documents in dictionary.

        Returns
        -------
        file_dict : dict
        """
        file_list = self.__get_docs(self.path)
        
        if not file_list:
            print('WARNING: there are no .pdf docs in {}'.format(self.path))
            file_list = self.__get_docs_in_subfolders()
        # Создадим словарь, в который дальше будем записывать
        # данные по каждому документу
        file_dict = dict.fromkeys(file_list)
        return file_dict

    def __update_docs_in_subfolders(self):
        """
        Tries to find documents in subfolders and update them.

        Returns
        -------
        None
        """
        print('Trying to update docs in subfolders')
        folder_mask = self.__cfg[1]['vdr_mask']
        # Сформируем маску для поиска папки с именем документа
        folder_mask = folder_mask.split('.xlsx')[0]
        for item in os.listdir(self.path):
            subfolder = os.path.join(self.path, item)
            if fnmatch.fnmatch(item, folder_mask) and os.path.isdir(subfolder):
                # Выполним поиск внутри подпапки
                print('Trying to find docs in {}'.format(subfolder))
                check = self.__update_docs(subfolder)
                if not check:
                    print('ERROR: there are no .pdf docs in {}'.format(subfolder), file=sys.stderr)

    def __update_docs(self, path: str):
        """
        Tries to find documents and update them using path provided.

        Parameters
        ----------
        path : str

        Returns
        -------
        check : int
            Indicator of file presence.
        """
        mask = self.__cfg[1]['vdr_mask']
        mask = mask.split('*')[0] + '*.pdf'
        alt_mask = mask.split('*')[0] + '*.PDF'
        check = 0
        for item in os.listdir(path):
            if fnmatch.fnmatch(item, mask) or fnmatch.fnmatch(item, alt_mask):
                check += 1
                # Отбросим ненужную часть названия документа '.pdf'
                doc_name = item[:-4]
                
                if doc_name not in self.documents:
                    self.documents[doc_name] = None
        return check

    def update(self, update_docs=False):
        """
        Refreshes the transmittal path and optionally updates files in it.

        Parameters
        ----------
        update_docs : bool, default=False

        Returns
        -------
        None
        """
        # Обновим путь к трансмиттелу, если название папки трансмиттела изменено
        mask = self.name + '*'
        directory = os.path.split(self.path)[0]
        for item in os.listdir(directory):
            if fnmatch.fnmatch(item, mask):
                trm_dir = os.path.split(self.path)
                if trm_dir[1] != item:
                    self.path = os.path.join(trm_dir[0], item)
                    print('Path to {} was successfully updated'.format(self.name))
                    
                    # Добавим документы, если в трансмиттел были добавлены новые
        if update_docs:
            check = self.__update_docs(self.path)
            
            if check == 0:
                self.__update_docs_in_subfolders()
