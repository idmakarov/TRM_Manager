import os


class Document:
    """
    The class is purposed for creation and processing document object with properties:
    name, path and phase.

    Attributes
    ----------
    name : str
        Name of the document.
    path : str
        Absolute path to the document.
    phase : str
        Document phase.
    """
    
    def __init__(self, name: str, path: str):
        self.name = name

        if os.path.isabs(path):
            self.path = path
        else:
            self.path = os.path.abspath(path)

        phase = name.split('.')[1]
        self.phase = phase
