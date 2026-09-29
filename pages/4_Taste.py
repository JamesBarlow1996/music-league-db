import streamlit as st
import plotly.express as px
from src.dashboard import load_data
from src.metrics import taste_summary
from src.ui import award_card
from src.theme import apply_retro_theme

data = load_data()
apply_retro_theme()
st.title("Taste")
if "submissions" not in data or "players" not in data:
    st.info("Run refresh_data.py first to create the processed tables.")
    st.stop()
enrichment = data.get("track_enrichment")
if enrichment is None or enrichment.get("popularity_score") is None or enrichment["popularity_score"].notna().sum() == 0:
    st.info("Spotify details are missing. Add your Spotify credentials and run refresh_data.py again.")
    st.stop()

players, tracks = taste_summary(data["submissions"], enrichment, data["players"])
for column in ["top_genre", "genre_share"]:
    if column not in players.columns:
        players[column] = None
eligible = players.loc[players["total_submissions"] >= 2]
if eligible.empty:
    eligible = players.dropna(subset=["average_popularity"])

st.subheader("Spotify awards")
pop_idol = eligible.sort_values("average_popularity", ascending=False).iloc[0]
hipster = eligible.sort_values("average_popularity").iloc[0]
basic = tracks.sort_values("popularity_score", ascending=False).iloc[0]
underground = tracks.sort_values("popularity_score").iloc[0]
row = st.columns(2)
award_card(row[0], "Pop Idol", pop_idol["player_name"], f'{pop_idol["average_popularity"]:.1f} average popularity', "Highest average Spotify popularity.")
award_card(row[1], "The Hipster", hipster["player_name"], f'{hipster["average_popularity"]:.1f} average popularity', "Lowest average Spotify popularity.")
row = st.columns(2)
award_card(row[0], "Basic", basic["track_name"], f'{basic["popularity_score"]:.0f} Spotify popularity', "The single most popular track on Spotify.")
award_card(row[1], "Underground", underground["track_name"], f'{underground["popularity_score"]:.0f} Spotify popularity', "The single least popular track on Spotify.")

st.subheader("Mainstream vs League")
st.caption("Does being popular on Spotify actually help a song in this league?")
scatter = tracks.merge(data["players"][["player_id", "player_name"]], on="player_id", how="left")
valid_scatter = scatter.dropna(subset=["total_points"]).copy()
scored_scatter = valid_scatter.dropna(subset=["popularity_score"])
correlation = scored_scatter[["popularity_score", "total_points"]].corr().iloc[0, 1]
strength = "little" if abs(correlation) < 0.2 else "a weak" if abs(correlation) < 0.4 else "a moderate" if abs(correlation) < 0.6 else "a strong"
direction = "positive" if correlation > 0 else "negative" if correlation < 0 else "flat"
st.metric("Popularity/points correlation", f"{correlation:.2f}")
if direction == "positive":
    st.caption(f"There is {strength} positive relationship: more popular Spotify tracks tend to score a little better here.")
elif direction == "negative":
    st.caption(f"There is {strength} negative relationship: less popular Spotify tracks tend to score a little better here.")
else:
    st.caption("Spotify popularity and league points are basically unrelated.")
valid_scatter["chart_popularity"] = valid_scatter["popularity_score"].fillna(-1)
valid_scatter["Spotify score status"] = valid_scatter["popularity_score"].notna().map({True: "Available", False: "Unknown"})
figure = px.scatter(valid_scatter, x="chart_popularity", y="total_points", hover_name="track_name", hover_data={"artist_display":True, "player_name":True, "Spotify score status":True}, color="player_name", labels={"chart_popularity":"Spotify popularity", "total_points":"Music League points", "player_name":"Submitted by"})
figure.update_xaxes(tickvals=[-1, 0, 20, 40, 60, 80, 100], ticktext=["Unknown", "0", "20", "40", "60", "80", "100"], range=[-5, 100])
figure.update_layout(legend_title_text="Submitted by")
st.plotly_chart(figure, use_container_width=True)
st.caption(f"Showing all {len(valid_scatter)} songs; {len(valid_scatter) - len(scored_scatter)} have no Spotify popularity score and are shown as Unknown.")

st.subheader("Era awards")
old_soul = eligible.sort_values("average_release_year").iloc[0]
new_music = eligible.sort_values("average_release_year", ascending=False).iloc[0]
time_traveller = eligible.sort_values("release_year_range", ascending=False).iloc[0]
trend_chaser = eligible.sort_values("average_track_age").iloc[0]
row = st.columns(2)
award_card(row[0], "Old Soul", old_soul["player_name"], f'{old_soul["average_release_year"]:.0f} average release year', "Usually picks older music.")
award_card(row[1], "New Music Addict", new_music["player_name"], f'{new_music["average_release_year"]:.0f} average release year', "Usually picks newer music.")
row = st.columns(2)
award_card(row[0], "Time Traveller", time_traveller["player_name"], f'{time_traveller["release_year_range"]:.0f}-year range', "Has the widest gap between oldest and newest picks.")
award_card(row[1], "Trend Chaser", trend_chaser["player_name"], f'{trend_chaser["average_track_age"]:.1f} years old when submitted', "Picks songs closest to their original release date.")

st.subheader("Submission habits")
repeat = eligible.sort_values("repeat_rate", ascending=False).iloc[0]
explorer = eligible.sort_values("artist_diversity", ascending=False).iloc[0]
decade = eligible.dropna(subset=["decade_share"]).sort_values("decade_share", ascending=False).iloc[0]
row = st.columns(2)
award_card(row[0], "Repeat Offender", repeat["player_name"], f'{repeat["repeat_rate"]:.0%} repeated artists', "Goes back to the same artists most often.")
award_card(row[1], "Explorer", explorer["player_name"], f'{explorer["artist_diversity"]:.0%} unique artists', "Spreads their picks across the most artists.")
row = st.columns(2)
award_card(row[0], "Decade Specialist", decade["player_name"], f'{decade["decade_share"]:.0%} from the {int(decade["top_decade"])}s', "Has the strongest attachment to one decade.")

genre_players = eligible.dropna(subset=["genre_share"]) if "genre_share" in eligible.columns else eligible.iloc[0:0]
if genre_players.empty:
    st.info("Genre Loyalist will appear once genre details are available. Spotify's track response does not currently include genre labels for these songs.")
else:
    loyalist = genre_players.sort_values("genre_share", ascending=False).iloc[0]
    award_card(row[1], "Genre Loyalist", loyalist["player_name"], f'{loyalist["genre_share"]:.0%} {loyalist["top_genre"]}', "Sticks closest to one Spotify genre label.")

st.subheader("Everyone's taste")
taste_table = players.rename(columns={"player_name":"Player", "average_popularity":"Average popularity", "average_release_year":"Average release year", "release_year_range":"Year range", "average_track_age":"Average track age", "artist_diversity":"Artist diversity", "repeat_rate":"Repeat rate", "top_decade":"Top decade", "decade_share":"Top decade share", "top_genre":"Top genre", "genre_share":"Top genre share"})
for column in ["Artist diversity", "Repeat rate", "Top decade share", "Top genre share"]:
    taste_table[column] *= 100
st.dataframe(taste_table[["Player", "Average popularity", "Average release year", "Year range", "Average track age", "Artist diversity", "Repeat rate", "Top decade", "Top decade share", "Top genre", "Top genre share"]], hide_index=True, use_container_width=True, column_config={"Artist diversity": st.column_config.NumberColumn(format="%.0f%%"), "Repeat rate": st.column_config.NumberColumn(format="%.0f%%"), "Top decade share": st.column_config.NumberColumn(format="%.0f%%"), "Top genre share": st.column_config.NumberColumn(format="%.0f%%")})
