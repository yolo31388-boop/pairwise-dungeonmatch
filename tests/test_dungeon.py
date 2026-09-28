
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dungeon.match import MatchMaker


def test_match_considers_roles():
    mm = MatchMaker()
    party = [{"id": "p1", "ilvl": 100, "role": "tank"}]
    mm.queue = [
        {"id": "p2", "ilvl": 100, "role": "dps"},
        {"id": "p3", "ilvl": 100, "role": "healer"},
    ]
    result = mm.find_match(party)
    roles = [p["role"] for p in result]
    assert "healer" in roles
    assert "dps" in roles


def test_cross_server_ping():
    mm = MatchMaker()
    party = [{"id": "p1", "ilvl": 100, "role": "dps", "region": "cn"}]
    mm.queue = [
        {"id": "p2", "ilvl": 100, "role": "healer", "region": "cn", "ping": 30},
        {"id": "p3", "ilvl": 100, "role": "tank", "region": "us", "ping": 200},
    ]
    result = mm.find_match(party)
    assert all(p["ping"] < 100 for p in result)


def test_afk_auto_kick():
    mm = MatchMaker()
    party = {"id": "party1", "members": ["p1", "p2"], "confirmed": set(), "afk": {"p2"}}
    mm.parties.append(party)
    mm.confirm_match("party1", "p1")
    mm.process_afk_timeout("party1", 100)
    assert "p2" not in party["members"]


def test_role_bonus_reward():
    mm = MatchMaker()
    reward = mm.calc_reward("tank", 100)
    assert reward > 100


def test_preset_role_restriction():
    mm = MatchMaker()
    party = {"id": "p1", "roles_needed": ["healer"], "members": []}
    mm.parties.append(party)
    assert mm.can_join("p1", {"role": "dps"}) == False
    assert mm.can_join("p1", {"role": "healer"}) == True


def test_level_range_dynamic():
    mm = MatchMaker()
    party = [{"id": "p1", "ilvl": 100, "role": "dps", "level": 60}]
    mm.queue = [
        {"id": "p2", "ilvl": 100, "role": "healer", "level": 60},
        {"id": "p3", "ilvl": 100, "role": "tank", "level": 1},
    ]
    result = mm.find_match(party)
    assert all(p["level"] >= 50 for p in result)


def test_full_party_no_match():
    mm = MatchMaker()
    party = [{"id": f"p{i}", "ilvl": 100, "role": "dps"} for i in range(5)]
    assert mm.find_match(party) == []


def test_confirm_timeout():
    mm = MatchMaker()
    party = {"id": "party1", "members": ["p1", "p2"], "confirmed": set(), "confirm_deadline": 0}
    mm.parties.append(party)
    mm.process_confirm_timeout(now=100)
    assert party not in mm.parties or len(party["members"]) < 2


def test_ilvl_tolerance():
    mm = MatchMaker()
    party = [{"id": "p1", "ilvl": 100, "role": "dps"}]
    mm.queue = [{"id": "p2", "ilvl": 50, "role": "healer"}]
    result = mm.find_match(party)
    assert result == []  # 装等差距太大
