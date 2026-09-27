def generate_lore(summary, submissions):
    facts = []
    if len(summary) >= 2:
        top, second = summary.sort_values("rank").iloc[:2]; facts.append(f"{top.player_name} leads the league by {int(top.total_points-second.total_points)} points over {second.player_name}.")
    if not submissions.empty:
        hit = submissions.loc[submissions.total_points.idxmax()]; facts.append(f"{hit.track_name} is the current biggest hit with {int(hit.total_points)} points.")
        if "release_year" in submissions and submissions.release_year.notna().any():
            old = submissions.loc[submissions.release_year.idxmin()]; facts.append(f"{old.track_name} is the oldest release in the dataset ({int(old.release_year)}).")
    return facts[:5]
