import os
import pickle
import sys
from typing import Union

from document import Document
from transmittal import Transmittal


class DataBase:
    """
    The class is purposed for creation database object to keep required information
    about each TRM and its contents and VDR as well.

    Attributes
    ----------
    path : str, write-only
        The database location path.

    Methods
    -------
    add_item(item: object)
        Adds an item to the database.
    clear_db()
        Cleans up the database.
    get_item(self, id: int)
        Gets the item from the database using id.
    get_item_names()
        Gets the items name from the database.
    is_empty()
        Checks the database for content presence.
    load_db()
        Loads the database from file.
        If file doesn't exist it creates new database as a dictionary.
    save_db()
        Backing up the database.
    update_db(update_docs=False)
        Refreshes the database and documents (as an option).
    """

    def __init__(self, path: str):
        self.__db = {}

        if os.path.isabs(path):
            self.__path = path
        else:
            self.__path = os.path.abspath(path)
        self.load_db()

    def add_item(self, item: object):
        """
        Adds an item to the database.

        Parameters
        ----------
        item : object

        Returns
        -------
        None
        """
        id_ = len(self.__db)
        self.__db[id_] = item

    def get_item(self, id_: int) -> Union[Transmittal, Document, None]:
        """
        Gets the item from the database using id.

        Parameters
        ----------
        id_ : int
            The value must be non-negative integer.

        Returns
        -------
        Union[Transmittal, Document, None]
        """
        if self.is_empty():
            print('ERROR: database is empty!')
            return None
        elif id_ >= len(self.__db) or id_ < 0:
            print('ERROR: required item id does not exist!', file=sys.stderr)
            return None
        else:
            return self.__db[id_]
        
    def get_item_names(self):
        """
        Gets the items name from the database.

        Returns
        -------
        item_names : list
            List of items name.
        """
        item_names = [item.name for item in self.__db.values()]
        return item_names

    def is_empty(self):
        """
        Checks the database if empty.

        Returns
        -------
        state : bool
            Returns True, if the database is empty, else - False.
        """
        if not self.__db:
            return True
        else:
            return False

    def update_db(self, update_docs=False):
        """
        Refreshes the database and documents (as an option).

        Parameters
        ----------
        update_docs : bool, default=False

        Returns
        -------
        None
        """
        for item in self.__db.values():
            try:
                item.update(update_docs)
            except AttributeError:
                pass
        self.save_db()

    def load_db(self):
        """
        Loads the database from file.
        If file doesn't exist it creates new database as a dictionary.

        Returns
        -------
        None
        """
        file_name = os.path.split(self.__path)[1]
        db_name = file_name.split('.')[0]
        
        try:
            with open(self.__path, 'rb') as f:
                self.__db = pickle.load(f)
                print('DB was successfully loaded')
        except FileNotFoundError:
            print('WARNING: when uploading the {}, its file was not found!'.format(db_name))
            print('Empty DB was created')
            self.__db = {}

    def save_db(self):
        """
        Backing up the database.

        Returns
        -------
        None
        """
        with open(self.__path, 'wb') as f:
            pickle.dump(self.__db, f)

    def clear_db(self):
        """
        Cleans up the database.

        Returns
        -------
        None
        """
        self.__db = {}
        self.save_db()
        print('DB was cleaned')
