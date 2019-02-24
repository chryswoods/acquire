
__all__ = ["lazy_import"]


class lazy_import:
    @staticmethod
    def lazy_module(m):
        return __import__(m)
