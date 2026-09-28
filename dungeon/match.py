PARTY_SIZE = 5
ILVL_TOLERANCE = 20
LEVEL_RANGE = 10
PING_LIMIT = 100
CONFIRM_TIMEOUT = 40
REQUIRED_ROLES = ("tank", "healer", "dps")
ROLE_BONUS = {"tank": 1.5, "healer": 1.5}


class MatchMaker:
    def __init__(self):
        self.queue = []
        self.parties = []

    def enqueue(self, player):
        self.queue.append(player)

    def _avg(self, party, key):
        vals = [p[key] for p in party if key in p]
        return sum(vals) / len(vals) if vals else None

    def _eligible(self, candidate, avg_ilvl, avg_level, region):
        if avg_ilvl is not None and "ilvl" in candidate:
            if abs(candidate["ilvl"] - avg_ilvl) > ILVL_TOLERANCE:
                return False
        if avg_level is not None and "level" in candidate:
            if abs(candidate["level"] - avg_level) > LEVEL_RANGE:
                return False
        if region is not None and candidate.get("ping", 0) >= PING_LIMIT:
            return False
        return True

    def find_match(self, party):
        needed = PARTY_SIZE - len(party)
        if needed <= 0:
            return []
        avg_ilvl = self._avg(party, "ilvl")
        avg_level = self._avg(party, "level")
        regions = {p["region"] for p in party if "region" in p}
        region = regions.pop() if regions else None

        candidates = [
            p for p in self.queue
            if self._eligible(p, avg_ilvl, avg_level, region)
        ]
        candidates.sort(key=lambda p: (
            0 if region is None or p.get("region") == region else 1,
            abs(p.get("ilvl", avg_ilvl or 0) - (avg_ilvl or 0)),
        ))

        selected = []
        present = {p.get("role") for p in party}
        for role in REQUIRED_ROLES:
            if len(selected) >= needed:
                break
            if role in present:
                continue
            pick = next((c for c in candidates if c.get("role") == role
                         and c not in selected), None)
            if pick is not None:
                selected.append(pick)
        for c in candidates:
            if len(selected) >= needed:
                break
            if c not in selected:
                selected.append(c)
        return selected[:needed]

    def confirm_match(self, party_id, player_id):
        for p in self.parties:
            if p["id"] == party_id:
                p["confirmed"].add(player_id)
                return True
        return False

    def all_confirmed(self, party_id):
        for p in self.parties:
            if p["id"] == party_id:
                return len(p["confirmed"]) == len(p["members"])
        return False

    def process_afk_timeout(self, party_id, now):
        for p in self.parties:
            if p["id"] == party_id:
                afk = p.get("afk", set())
                p["members"] = [m for m in p["members"]
                                if m not in afk or m in p["confirmed"]]
                return True
        return False

    def process_confirm_timeout(self, now):
        for p in list(self.parties):
            deadline = p.get("confirm_deadline")
            if deadline is None or now <= deadline:
                continue
            p["members"] = [m for m in p["members"] if m in p["confirmed"]]
            if not p["members"]:
                self.parties.remove(p)

    def calc_reward(self, role, base):
        return base * ROLE_BONUS.get(role, 1.0)

    def can_join(self, party_id, player):
        for p in self.parties:
            if p["id"] != party_id:
                continue
            roles_needed = p.get("roles_needed")
            if roles_needed and player.get("role") not in roles_needed:
                return False
            if "min_ilvl" in p and player.get("ilvl", 0) < p["min_ilvl"]:
                return False
            if "max_ilvl" in p and player.get("ilvl", 0) > p["max_ilvl"]:
                return False
            if "min_level" in p and player.get("level", 0) < p["min_level"]:
                return False
            if "max_level" in p and player.get("level", 0) > p["max_level"]:
                return False
            return True
        return False
