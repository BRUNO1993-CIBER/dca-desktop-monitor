from enum import Enum


class TipoOperacao(Enum):
    COMPRA      = "compra"
    VENDA       = "venda"
    VENDA_TOTAL = "venda_total"

    @property
    def label(self) -> str:
        return {
            "COMPRA":      "Compra",
            "VENDA":       "Venda",
            "VENDA_TOTAL": "Venda Total (MAX)",
        }[self.name]

    @property
    def csv_value(self) -> str:
        return {
            "COMPRA":      "compra",
            "VENDA":       "venda",
            "VENDA_TOTAL": "venda",
        }[self.name]

    @classmethod
    def from_label(cls, label: str) -> "TipoOperacao":
        for membro in cls:
            if membro.label == label:
                return membro
        raise KeyError(f"TipoOperacao desconhecido: {label!r}")

    @classmethod
    def labels_crypto(cls) -> list:
        return [m.label for m in cls]

    @classmethod
    def labels_usdt(cls) -> list:
        return [cls.COMPRA.label, cls.VENDA.label]