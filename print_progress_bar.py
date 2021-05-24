class PrintProgressBar:
    """
    The class is purposed for output custom progress bar.

    Attributes
    ----------
    decimals : int, default=1
        Number of decimal digits in progress percentage.
    fill : str, default='█'
        A symbol to fill the progress bar.
    iteration : int
        Initializes by start value.
    length : int, default=100
        Number of symbols in the progress bar.
    prefix : str, default=''
        String before the progress bar.
    print_end : str, default='\n'
        String at the end of print, escape sequences as option.
    suffix : str, default=''
        String after the progress bar.
    total : int
        Steps number.

    Methods
    -------
    print_progress_bar()
        Output progress bar to console.
    """
    def __init__(self, start: int, total: int, prefix='', suffix='', decimals=1, length=100, fill='█', print_end="\n"):
        self.iteration = start
        self.total = total
        self.prefix = prefix
        self.suffix = suffix
        self.decimals = decimals
        self.length = length
        self.fill = fill
        self.print_end = print_end
        self.print_progress_bar()

    # Выводит в консоль шкалу прогресса
    def print_progress_bar(self):
        """
        Output progress bar to console.

        Returns
        -------
        None
        """
        percent = ("{0:." + str(self.decimals) + "f}").format(100 * (self.iteration / float(self.total)))
        filled_length = int(self.length * self.iteration // self.total)
        bar = self.fill * filled_length + '-' * (self.length - filled_length)
        print(f'{self.prefix} |{bar}| {percent}% {self.suffix}', end=self.print_end)
        # Переносит каретку на новую строку, если цикл завершён
        if self.iteration == self.total:
            print()
        # Увеличивает счётчик на единицу
        self.iteration += 1
