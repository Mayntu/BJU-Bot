class ReportLimitExceeded(Exception):
    def __init__(self, hours: int, max_limit : int):
        self.hours = hours
        self.max_limit = max_limit
        super().__init__("Превышен лимит генерации отчётов")

