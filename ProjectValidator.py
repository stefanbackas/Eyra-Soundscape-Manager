class ProjectValidator:
    def __init__(self, tracklists, groups, pools, slots):
        self.tracklists = tracklists
        self.groups = groups
        self.pools = pools
        self.slots = slots
        self.errors = []

    def validate(self):
        self.errors.clear()
        self.validate_tracklists()
        self.validate_groups()
        self.validate_pools()
        self.validate_slots()
        return self.errors

    def validate_tracklists(self):
        for name, tracklist in self.tracklists.items():
            # primary_group
            pg = tracklist.get("primary_group")
            if pg and pg not in self.groups:
                self.errors.append(f"Tracklist '{name}' hänvisar till okänd primary_group '{pg}'")
            # groups
            for g in tracklist.get("groups", []):
                if g not in self.groups:
                    self.errors.append(f"Tracklist '{name}' innehåller okänd grupp '{g}'")
            # pools
            for p in tracklist.get("pools", []):
                if p not in self.pools:
                    self.errors.append(f"Tracklist '{name}' hänvisar till okänd pool '{p}'")

    def validate_groups(self):
        for name, group in self.groups.items():
            # pools
            for p in group.get("pools", []):
                if p not in self.pools:
                    self.errors.append(f"Grupp '{name}' hänvisar till okänd pool '{p}'")
            # tracklists
            for t in group.get("tracklists", []):
                if t not in self.tracklists:
                    self.errors.append(f"Grupp '{name}' hänvisar till okänd tracklist '{t}'")
            # slots (om grupper skulle ha slots i framtiden – kan kommenteras bort om ej aktuellt)
            for s in group.get("slots", []):
                if s not in self.slots:
                    self.errors.append(f"Grupp '{name}' hänvisar till okänd slot '{s}'")

    def validate_pools(self):
        for name, pool in self.pools.items():
            # slots
            for s in pool.get("slots", []):
                if s not in self.slots:
                    self.errors.append(f"Pool '{name}' hänvisar till okänd slot '{s}'")
            # tracklists
            for t in pool.get("tracklists", []):
                if t not in self.tracklists:
                    self.errors.append(f"Pool '{name}' hänvisar till okänd tracklist '{t}'")
            # groups
            for g in pool.get("groups", []):
                if g not in self.groups:
                    self.errors.append(f"Pool '{name}' hänvisar till okänd grupp '{g}'")

    def validate_slots(self):
        for name, slot in self.slots.items():
            # tracklist
            t = slot.get("tracklist")
            if t and t not in self.tracklists:
                self.errors.append(f"Slot '{name}' hänvisar till okänd tracklist '{t}'")
            # group
            g = slot.get("group")
            if g and g not in self.groups:
                self.errors.append(f"Slot '{name}' hänvisar till okänd grupp '{g}'")
            # pool
            p = slot.get("pool")
            if p and p not in self.pools:
                self.errors.append(f"Slot '{name}' hänvisar till okänd pool '{p}'")


def validate_exported_project_structure(data):
    """Validera relationer mellan tracklists, grupper, pooler och slots i en exporterad JSON."""
    errors = []
    warnings = []

    # Samla namn
    tracklists = set(data.get("tracklists", {}).keys())
    groups = set(data.get("groups", {}).keys())
    pools = set(data.get("pools", {}).keys())
    slots = set(data.get("slots", {}).keys())

    # Håll koll på refererade objekt
    referenced_tracklists = set()
    referenced_groups = set()
    referenced_pools = set()

    # Kontroll: Tracklists refererar till grupper
    for tl_name, tl_data in data.get("tracklists", {}).items():
        for group in tl_data.get("groups", []):
            if group not in groups:
                errors.append(f"Tracklist '{tl_name}' refererar till okänd grupp '{group}'")
            else:
                referenced_groups.add(group)

    # Kontroll: Grupper refererar till tracklists och grupper
    for group_name, group_data in data.get("groups", {}).items():
        for tl in group_data.get("tracklists", []):
            if tl not in tracklists:
                errors.append(f"Grupp '{group_name}' refererar till okänd tracklist '{tl}'")
            else:
                referenced_tracklists.add(tl)
        for sub_group in group_data.get("groups", []):
            if sub_group not in groups:
                errors.append(f"Grupp '{group_name}' refererar till okänd undergrupp '{sub_group}'")
            else:
                referenced_groups.add(sub_group)

    # Kontroll: Pools refererar till tracklists och grupper
    for pool_name, pool_data in data.get("pools", {}).items():
        for tl in pool_data.get("tracklists", []):
            if tl not in tracklists:
                errors.append(f"Pool '{pool_name}' refererar till okänd tracklist '{tl}'")
            else:
                referenced_tracklists.add(tl)
        for gr in pool_data.get("groups", []):
            if gr not in groups:
                errors.append(f"Pool '{pool_name}' refererar till okänd grupp '{gr}'")
            else:
                referenced_groups.add(gr)

    # Kontroll: Slots refererar till tracklist, group, pool
    for slot_name, slot_data in data.get("slots", {}).items():
        tl = slot_data.get("tracklist")
        gr = slot_data.get("group")
        po = slot_data.get("pool")

        if tl != "Ingen":
            if tl not in tracklists:
                errors.append(f"Slot '{slot_name}' refererar till okänd tracklist '{tl}'")
            else:
                referenced_tracklists.add(tl)

        if gr != "Ingen":
            if gr not in groups:
                errors.append(f"Slot '{slot_name}' refererar till okänd grupp '{gr}'")
            else:
                referenced_groups.add(gr)

        if po != "Ingen":
            if po not in pools:
                errors.append(f"Slot '{slot_name}' refererar till okänd pool '{po}'")
            else:
                referenced_pools.add(po)

    # Varningar: Oanvända objekt
    unreferenced_tracklists = tracklists - referenced_tracklists
    unreferenced_groups = groups - referenced_groups
    unreferenced_pools = pools - referenced_pools

    for name in sorted(unreferenced_tracklists):
        warnings.append(f"Tracklist '{name}' har inga relationer till grupper, pooler eller slots")

    for name in sorted(unreferenced_groups):
        warnings.append(f"Grupp '{name}' har inga relationer till andra grupper, pooler eller slots")

    for name in sorted(unreferenced_pools):
        warnings.append(f"Pool '{name}' används inte i någon slot")

    return errors, warnings
