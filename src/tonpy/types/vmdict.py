from typing import Union, Iterable, Optional

from tonpy.libs.python_ton import PyDict, PyCellSlice, PyAugmentationCheckData

from tonpy.types.cell import Cell
from tonpy.types.cellslice import CellSlice
from tonpy.types.cellbuilder import CellBuilder
from tonpy.utils.bit_converter import convert_str_to_int
from tonpy.utils.bit_int import test_value_len


class AugmentedData:
    def eval_leaf(self, cs: CellSlice) -> (bool, Optional[CellSlice]):
        """Extract extra from leaf value ``cs``"""
        raise NotImplementedError

    def skip_extra(self, cs: CellSlice) -> (bool, Optional[CellSlice]):
        """Skip extra from leaf, return updated ``cs``"""
        raise NotImplementedError

    def eval_fork(self, left: CellSlice, right: CellSlice) -> (bool, Optional[CellSlice]):
        raise NotImplementedError

    def eval_empty(self) -> (bool, Optional[CellSlice]):
        raise NotImplementedError

    def _eval_leaf(self, cs: PyCellSlice):
        answer = list(self.eval_leaf(CellSlice(cs)))

        if len(answer) > 1:
            answer[1] = answer[1].cell_slice
        return tuple(answer)

    def _skip_extra(self, cs: PyCellSlice):
        answer = list(self.skip_extra(CellSlice(cs)))

        if len(answer) > 1:
            answer[1] = answer[1].cell_slice
        return tuple(answer)

    def _eval_fork(self, left: PyCellSlice, right: PyCellSlice):
        answer = list(self.eval_fork(CellSlice(left), CellSlice(right)))

        if len(answer) > 1:
            answer[1] = answer[1].cell_slice
        return tuple(answer)

    def _eval_empty(self):
        answer = list(self.eval_empty())

        if len(answer) > 1:
            answer[1] = answer[1].cell_slice
        return tuple(answer)

    def get_base_aug(self):
        return PyAugmentationCheckData(self._eval_leaf, self._skip_extra,
                                       self._eval_fork, self._eval_empty)


class VmDict:
    def __init__(self, key_len: int,
                 signed: bool = False,
                 cell_root: Union[Union[str, Cell], CellSlice] = None,
                 aug: AugmentedData = None):
        """
        Wrapper of HashmapE (dictionary type of TON)  |br|

        Key are represented as ``key_len`` bits. They can be loaded as ``signed`` or not.  |br|

        :param key_len: Size of keys in bits (up to 257 with ``signed`` or 256)
        :param signed: Load keys as signed integers or not
        :param cell_root: Root of HashmapE, can be BOC string, CellSlice or Cell
        :return:
        """

        if key_len > 256:
            if not (key_len == 257 and signed):
                raise ValueError("Key len must not be larger than 256 for unsigned / 257 for signed")

        self.key_len = key_len
        self.signed = signed

        if cell_root is not None:
            cs = cell_root

            if isinstance(cs, str):
                cs = CellSlice(cs)
            elif isinstance(cs, Cell):
                cs = cs.begin_parse()

            cell_root = cs.cell_slice

        if aug is None:
            self.dict = PyDict(key_len, signed, cell_root)
            self.is_augmented = False
        else:
            self.dict = PyDict(key_len, aug.get_base_aug(), signed, cell_root)
            self.is_augmented = True

    def _process_sgnd(self, key: int = None, signed: bool = None) -> bool:
        """Check ``key`` to be ``signed`` or if ``signed`` is None will use current dict ``self.signed``"""
        if signed is None:
            signed = self.signed

        if key is not None:
            if key < 0 and (signed is False):
                raise ValueError(f"Signed is false, but key < 0")
        return signed

    def set(self, key: int, value: CellSlice, mode: str = "set", signed: bool = None) -> "VmDict":
        """
        Add / Set / Replace ``key`` as ``key_len`` and ``signed`` bits to value ``value``  |br|

        - Set: sets the value associated with ``key_len``-bit key ``key`` in VmDict to value ``value``

        - Add: sets the value associated with key ``key`` to ``value``, but only if ``key`` is not already present in VmDict

        - Replace: sets the value of ``key`` to ``value`` only if the key ``key`` was already present in VmDict

        :param key: Integer to be stored as key
        :param value: CellSlice to be stored
        :param mode: "set" / "replace" / "add"
        :param signed: Signed
        :return: Updated self
        """
        test_value_len(key, self.key_len)
        signed = self._process_sgnd(key, signed)

        if not isinstance(value, CellSlice):
            raise ValueError(f"CellSlice needed")

        self.dict.set_str(str(key), value.cell_slice, mode, 0, signed)
        return self

    def is_empty(self) -> bool:
        """If dict contains no keys - it's empty"""
        return self.dict.is_empty()

    def get_cell(self) -> Cell:
        """Get root cell of dictionary"""
        return Cell(self.dict.get_pycell())

    def lookup_nearest_key(self, key: int, fetch_next: bool = True, allow_eq: bool = False,
                           invert_first: bool = True, signed: bool = None) -> tuple[int, CellSlice]:
        """
        Compute the nearest key to ``key``  |br|

        :param key: ``self.key_len``-bit integer key
        :param fetch_next: If ``True`` will fetch next else will return prev
        :param allow_eq: If ``True`` will return value with ``key`` if exist
        :param invert_first: If ``True`` will respect ``signed`` in operations
        :param signed: Fetch keys as signed or not
        :return: Founded key and value
        """
        test_value_len(key, self.key_len)
        signed = self._process_sgnd(key, signed)

        key, value = self.dict.lookup_nearest_key(str(key), fetch_next, allow_eq, invert_first, 0, signed)
        return int(key), CellSlice(value)

    def get_minmax_key(self, fetch_max: bool = True, invert_first: bool = True, signed: bool = None) -> tuple[
        int, CellSlice]:
        """
        Fetch max / min ``key, value``  |br|

        :param fetch_max: If ``True`` will fetch max key, else will fetch min key in dict
        :param invert_first: If ``True`` will respect ``signed`` in operations
        :param signed: Fetch keys as signed or not
        :return: Key and CellSlice that stored in key
        """
        signed = self._process_sgnd(signed=signed)

        key, value = self.dict.get_minmax_key(fetch_max, invert_first, 0, signed)
        return int(key), CellSlice(value)

    def get_minmax_key_ref(self, fetch_max: bool = True, inver_first: bool = False, signed: bool = None) -> tuple[
        int, Cell]:
        """
        Same as get_minmax, but fetch Cell by key (stored in ref)  |br|

        :param fetch_max: If ``True`` will fetch max key, else will fetch min key in dict
        :param invert_first: If ``True`` will respect ``signed`` in operations
        :param signed: Fetch keys as signed or not
        :return: Key and Cell that stored in key
        """

        key, value = self.dict.get_minmax_key_ref(fetch_max, inver_first, 0, signed)
        return int(key), Cell(value)

    def set_ref(self, key: int, value: Cell, mode: str = "set", signed: bool = None) -> "VmDict":
        """
        Same as set, but store Cell to ref (by key)  |br|

        :param key: Integer to be stored as key
        :param value: CellSlice to be stored
        :param mode: "set" / "replace" / "add"
        :param signed: Signed
        :return: Updated self
        """

        test_value_len(key, self.key_len)
        signed = self._process_sgnd(key, signed)

        if not isinstance(value, Cell):
            raise ValueError(f"Only Cell accepted as value")

        self.dict.set_ref_str(str(key), value.cell, mode, 0, signed)
        return self

    def set_builder(self, key: int, value: CellBuilder, mode: str = "set", signed: bool = None) -> "VmDict":
        """
        Set cell builder stored to ``key``, you can load it by ``lookup`` method  |br|

        :param key: Integer to be stored as key
        :param value: CellSlice to be stored
        :param mode: "set" / "replace" / "add"
        :param signed: Signed
        :return: Updated self
        """

        test_value_len(key, self.key_len)
        signed = self._process_sgnd(key, signed)

        if not isinstance(value, CellBuilder):
            raise ValueError(f"CellBuilder needed")

        self.dict.set_builder_str(str(key), value.builder, mode, 0, signed)
        return self

    def lookup(self, key: int, signed: bool = None) -> CellSlice:
        """
        Fetch CellSlice stored in ``key``  |br|

        :param key: Integer to be loaded as ``self.key_len`` bit and used as key to search
        :param signed: Signed
        :return: CellSlice that stored by key
        """
        test_value_len(key, self.key_len)
        signed = self._process_sgnd(key, signed)

        return CellSlice(self.dict.lookup_str(str(key), 0, signed))

    def lookup_delete(self, key: int, signed: bool = None) -> CellSlice:
        """
        Same as lookup, but delete ``(key, value)`` from VmDict  |br|

        :param key: Integer to be loaded as ``self.key_len`` bit and used as key to search
        :param signed: Signed
        :return: CellSlice that stored by key
        """
        test_value_len(key, self.key_len)
        signed = self._process_sgnd(key, signed)

        return CellSlice(self.dict.lookup_delete_str(str(key), 0, signed))

    def lookup_ref(self, key, signed: bool = None) -> Cell:
        """
        Same as lookup, but fetch ref stored by ``set_ref``  |br|

        :param key:  Integer to be loaded as ``self.key_len`` bit and used as key to search
        :param signed: Signed
        :return: Cell that stored by key
        """
        test_value_len(key, self.key_len)
        signed = self._process_sgnd(key, signed)

        return Cell(self.dict.lookup_ref_str(str(key), 0, signed))

    def lookup_delete_ref(self, key: int, signed: bool = None) -> Cell:
        """
        Same as ```lookup_delete`` but delete the ref stored by ``set_ref``  |br|

        :param key:  Integer to be loaded as ``self.key_len`` bit and used as key to search
        :param signed: Signed
        :return: Cell that stored by key
        """
        test_value_len(key, self.key_len)
        signed = self._process_sgnd(key, signed)

        return Cell(self.dict.lookup_delete_ref_str(str(key), 0, signed))

    def get_iter(self, direction=False) -> Iterable[tuple[int, CellSlice]]:
        """Simple dict iterator"""

        key, value = self.get_minmax_key(direction)
        yield key, value

        while True:
            try:
                key, value = self.lookup_nearest_key(key, not direction)
                yield key, value
            except RuntimeError:
                return

    def __setitem__(self, key: Union[int, str], value: Union[Union[Union[str, CellSlice], Cell], CellBuilder]):
        if isinstance(key, str):
            key = convert_str_to_int(key)

        test_value_len(key, self.key_len)
        self._process_sgnd(key, None)

        if isinstance(value, str):
            self.set(key, CellSlice(value))
        elif isinstance(value, CellSlice):
            self.set(key, value)
        elif isinstance(value, Cell):
            self.set_ref(key, value)
        elif isinstance(value, CellBuilder):
            self.set_builder(key, value)

    def __getitem__(self, key: Union[int, str]):
        if isinstance(key, str):
            key = convert_str_to_int(key)

        test_value_len(key, self.key_len)
        self._process_sgnd(key, None)

        return self.lookup(key)

    def __repr__(self):
        return self.dict.__repr__()

    def __iter__(self):
        return self.get_iter(False)

    def __reversed__(self):
        return self.get_iter(True)
