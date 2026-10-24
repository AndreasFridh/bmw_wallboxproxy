from typing import Dict

from modbus_codec import float_to_words
from state import get_float_word_order, get_phase_order, get_power_offset_override, get_register_alias_mode, latest_values, state_lock


def _apply_phase_order(order: str, a: float, b: float, c: float) -> tuple:
    idx = [int(x) - 1 for x in order.split(",")]
    src = (a, b, c)
    return src[idx[0]], src[idx[1]], src[idx[2]]


def get_output_values() -> dict:
    with state_lock:
        snap = latest_values.copy()

    def get(name: str, default: float = 0.0) -> float:
        return float(snap.get(name, default))

    order = get_phase_order()
    u1, u2, u3 = _apply_phase_order(order, get("u1"), get("u2"), get("u3"))
    i1, i2, i3 = _apply_phase_order(order, get("i1"), get("i2"), get("i3"))
    _override = get_power_offset_override()
    offset_watts = _override if _override is not None else snap.get("power_offset", 0.0)
    offset_kw = offset_watts / 1000.0
    p_total = get("p_total") / 1000.0 + offset_kw
    raw_p1 = get("p1") / 1000.0 + offset_kw / 3.0
    raw_p2 = get("p2") / 1000.0 + offset_kw / 3.0
    raw_p3 = get("p3") / 1000.0 + offset_kw / 3.0
    p1, p2, p3 = _apply_phase_order(order, raw_p1, raw_p2, raw_p3)
    if snap.get("pause", 0.0) >= 0.5:
        i1 = i2 = i3 = p_total = p1 = p2 = p3 = 0.0
    freq = get("freq")
    e_import = get("e_import_total")
    e_export = get("e_export_total")

    s_total = abs(p_total)
    s1, s2, s3 = abs(p1), abs(p2), abs(p3)

    return {
        "voltage_avg": (u1 + u2 + u3) / 3.0,
        "u1": u1, "u2": u2, "u3": u3,
        "freq": freq,
        "current_total": i1 + i2 + i3,
        "i1": i1, "i2": i2, "i3": i3,
        "p_total": p_total, "p1": p1, "p2": p2, "p3": p3,
        "q_total": 0.0, "q1": 0.0, "q2": 0.0, "q3": 0.0,
        "s_total": s_total, "s1": s1, "s2": s2, "s3": s3,
        "pf_total": p_total / s_total if s_total else 0.0,
        "pf1": p1 / s1 if s1 else 0.0,
        "pf2": p2 / s2 if s2 else 0.0,
        "pf3": p3 / s3 if s3 else 0.0,
        "e_total": e_import + e_export,
        "e_import": e_import,
        "e_export": e_export,
    }


def get_register_map() -> Dict[int, int]:
    with state_lock:
        snap = latest_values.copy()

    word_order = get_float_word_order()
    alias_mode = get_register_alias_mode()

    regs: Dict[int, int] = {}

    def get_value(name: str, default: float = 0.0) -> float:
        return float(snap.get(name, default))

    def put_float(addr: int, value: float) -> None:
        hi, lo = float_to_words(value, word_order)

        def put_words(base_addr: int) -> None:
            regs[base_addr] = hi
            regs[base_addr + 1] = lo

        put_words(addr)

        if alias_mode in ("alias_minus_1", "alias_both"):
            put_words(addr - 1)
        if alias_mode in ("alias_plus_1", "alias_both"):
            put_words(addr + 1)

    order = get_phase_order()
    u1, u2, u3 = _apply_phase_order(order, get_value("u1"), get_value("u2"), get_value("u3"))
    i1, i2, i3 = _apply_phase_order(order, get_value("i1"), get_value("i2"), get_value("i3"))
    _override = get_power_offset_override()
    offset_watts = _override if _override is not None else snap.get("power_offset", 0.0)
    offset_kw = offset_watts / 1000.0
    p_total = get_value("p_total") / 1000.0 + offset_kw
    raw_p1 = get_value("p1") / 1000.0 + offset_kw / 3.0
    raw_p2 = get_value("p2") / 1000.0 + offset_kw / 3.0
    raw_p3 = get_value("p3") / 1000.0 + offset_kw / 3.0
    p1, p2, p3 = _apply_phase_order(order, raw_p1, raw_p2, raw_p3)
    if snap.get("pause", 0.0) >= 0.5:
        i1 = i2 = i3 = p_total = p1 = p2 = p3 = 0.0
    freq = get_value("freq")
    e_import_total = get_value("e_import_total")
    e_export_total = get_value("e_export_total")

    voltage_avg = (u1 + u2 + u3) / 3.0
    current_total = i1 + i2 + i3

    q_total = 0.0
    q1 = 0.0
    q2 = 0.0
    q3 = 0.0

    s_total = abs(p_total)
    s1 = abs(p1)
    s2 = abs(p2)
    s3 = abs(p3)

    pf_total = p_total / s_total if s_total else 0.0
    pf1 = p1 / s1 if s1 else 0.0
    pf2 = p2 / s2 if s2 else 0.0
    pf3 = p3 / s3 if s3 else 0.0

    e_total_active = e_import_total + e_export_total

    put_float(0x5000, voltage_avg)
    put_float(0x5002, u1)
    put_float(0x5004, u2)
    put_float(0x5006, u3)
    put_float(0x5008, freq)

    put_float(0x500A, current_total)
    put_float(0x500C, i1)
    put_float(0x500E, i2)
    put_float(0x5010, i3)

    put_float(0x5012, p_total)
    put_float(0x5014, p1)
    put_float(0x5016, p2)
    put_float(0x5018, p3)
    put_float(0x501A, q_total)
    put_float(0x501C, q1)
    put_float(0x501E, q2)
    put_float(0x5020, q3)
    put_float(0x5022, s_total)
    put_float(0x5024, s1)
    put_float(0x5026, s2)
    put_float(0x5028, s3)
    put_float(0x502A, pf_total)
    put_float(0x502C, pf1)
    put_float(0x502E, pf2)
    put_float(0x5030, pf3)

    put_float(0x6000, e_total_active)
    put_float(0x6002, e_total_active)
    put_float(0x6004, 0.0)
    put_float(0x6006, 0.0)
    put_float(0x6008, 0.0)
    put_float(0x600A, 0.0)
    put_float(0x600C, e_import_total)
    put_float(0x600E, e_import_total)
    put_float(0x6010, 0.0)
    put_float(0x6012, 0.0)
    put_float(0x6014, 0.0)
    put_float(0x6016, 0.0)
    put_float(0x6018, e_export_total)
    put_float(0x601A, e_export_total)
    put_float(0x601C, 0.0)
    put_float(0x601E, 0.0)
    put_float(0x6020, 0.0)
    put_float(0x6022, 0.0)

    return regs