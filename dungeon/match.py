
class MatchMaker:
    def __init__(self):
        self.queue = []
        self.parties = []

    def enqueue(self, player):
        self.queue.append(player)

    def find_match(self, party):
        # BUG: 只看装等
        avg_ilvl = sum(p["ilvl"] for p in party) / len(party) if party else 0
        candidates = sorted(self.queue, key=lambda p: abs(p["ilvl"] - avg_ilvl))
        needed = 5 - len(party)
        return candidates[:needed]

    def confirm_match(self, party_id, player_id):
        for p in self.parties:
            if p["id"] == party_id:
                p["confirmed"].add(player_id)
                return True
        return False

    def all_confirmed(self, party_id):
        for p in self.parties:
            if p["id"] == party_id:
                # BUG: 不处理AFK
                return len(p["confirmed"]) == len(p["members"])
        return False
