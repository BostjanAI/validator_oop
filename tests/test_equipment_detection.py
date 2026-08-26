from validator_oop.utils import is_equipment_tip


def test_is_equipment_tip_accepts_naprava() -> None:
    assert is_equipment_tip("naprava") is True


def test_is_equipment_tip_accepts_avtoklav() -> None:
    assert is_equipment_tip("avtoklav") is True

