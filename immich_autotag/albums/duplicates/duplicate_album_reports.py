from typing import List, Dict, Iterator, Any
import attrs

@attrs.define(auto_attribs=True, slots=True)
class DuplicateAlbumReports:
    """
    Encapsula la lista de diccionarios de duplicados de álbumes para un manejo más claro y seguro.
    """
    items: List[Dict[str, Any]] = attrs.field(factory=list)

    def append(self, item: Dict[str, Any]) -> None:
        self.items.append(item)

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, idx):
        return self.items[idx]

    def to_list(self) -> List[Dict[str, Any]]:
        return list(self.items)

    def clear(self) -> None:
        self.items.clear()
