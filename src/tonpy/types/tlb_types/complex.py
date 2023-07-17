from tonpy.types.tlb import TLB
from tonpy.types.tlb_types.reft import RefT, FakeCell
from tonpy.types.tlb_types.nat import NatWidth


class TLBComplex(TLB):
    constants = {"t_RefCell": RefT(FakeCell()), "t_Nat": NatWidth(32)}

    def __init__(self):
        super().__init__()