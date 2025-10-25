import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

from db_helper import DatabaseHelper
from sql_tables import Manager, ManagerScore, Roster
from sleeper import get_manager_matchups, get_week

def main():
    """
    This is just a scrappy code to make a nice plot for weekly score comparisons
    """
    db = DatabaseHelper()
    
    q = db.db_session.query(Manager)
    q = q.join(Roster, Manager.manager_id == Roster.manager_id)
    q = q.add_columns(Roster.roster_id)
    result = q.all()
    managers = [_m for _m, _ in result]
    rosters = {_r: _m for _m, _r in result}
    week = get_week()

    matchup_responses = get_manager_matchups(week=week)
    matchup_details = {}
    for matchup_response in matchup_responses:
        matchup_id = matchup_response.get("matchup_id", 1)
        if matchup_id in matchup_details.keys():
            matchup_details[matchup_id].append(matchup_response)
        else:
            matchup_details[matchup_id] = [matchup_response]
        sorted(matchup_details[matchup_id], key=lambda m: m["points"])
    matchups = []
    for matchup_id, matchup_pair in matchup_details.items():
        roster_id1 = matchup_pair[0]["roster_id"]
        roster_id2 = matchup_pair[1]["roster_id"]
        matchups.append((rosters[roster_id1], rosters[roster_id2]))

    titles = [f"<b>{matchup[0]} vs {matchup[1]} Summary</b>" for matchup in matchups]
    vspace = 0.085
    fig2 = make_subplots(rows=4, cols=1, vertical_spacing=vspace, subplot_titles=titles)
    
    # time_ranges = [(1760055300, 1760068800), (1760275800, 1760328000), (1760397300, 1760414400)]
    # time_ranges = [(1760660100, 1760674500), (1760880600, 1760932800), (1761001200, 1761024600)]
    time_ranges = [(1761264900, 1761277500), (1761498000, 1761537600), (1761524100, 1761536700)]
    for num, match in enumerate(matchups):
        p1, p2 = match
        fig2.layout.annotations[num].update(text=f"<b>{p1} vs {p2}</b>", font={"color": "#000000"}, yanchor="bottom", y=1.03 - num * .25 - vspace / 4 * num)
        fig2.update_layout(yaxis = {
            "title": {"text": "<b>Points</b>", "font": {"color": "#000000"}}},
            **{
                f"xaxis{num+1}": {"linecolor": "#000000", "color": "#000000"},
                f"yaxis{num+1}": {"linecolor": "#000000", "color": "#000000", "title": "<b>Points</b>"},
                f"legend{num+2}": {
                    "orientation": "h",
                    "yanchor": "bottom",
                    "y": 1 - num * .25 - vspace / 4 * num,
                    "xanchor": "center",
                    "x": .5,
                    "borderwidth": 1,
                    "bordercolor": "#000000"
            },
        })
        for manager in match:
            timestamps = []
            actual_scores = []
            projected_scores = []

            ellapsed_time = 0
            for time_range in time_ranges:
                lower_time, upper_time = time_range
                q = db.db_session.query(Manager)
                q = q.where(Manager.display_name == manager.display_name)
                q = q.join(ManagerScore, ManagerScore.manager_id == Manager.manager_id)
                q = q.where(ManagerScore.timestamp > lower_time)
                q = q.where(ManagerScore.timestamp < upper_time)
                q = q.add_columns(ManagerScore)
                q = q.order_by(ManagerScore.timestamp)
                results = q.all()

                for _, manager_score in results:
                    #timestamps.append(datetime.fromtimestamp(manager_score.timestamp))
                    time_in_period = manager_score.timestamp - lower_time
                    timestamps.append((time_in_period + ellapsed_time) / 3600)
                    actual_scores.append(manager_score.current_score)
                    projected_scores.append(manager_score.projected_score)
                ellapsed_time += upper_time - lower_time

            if manager == match[0]:
                line = {"color": "forestgreen"}
            else:
                line = {"color": "crimson"}
            legend_name = f"legend{num+2}"
            fig2.add_scatter(x=timestamps, y=actual_scores, name=f"{manager} Actual", mode="lines", line=line, row=num+1, col=1, legend=legend_name)
            line["dash"] = "dot"
            fig2.add_scatter(x=timestamps, y=projected_scores, name=f"{manager} Projected", line=line, row=num+1, col=1, legend=legend_name)
    layout = {
        "template": "plotly_white",
        "xaxis4": {"title": "<b>Ellapsed Football Time (hours)</b>", "color": "#000000", "linecolor": "#000000"},
        "width": 950,
        "height": 1500,
        "legend": {
            "orientation": "h",
            "yanchor": "top",
            "y": 1.1,
            "xanchor": "center",
            "x": .5,
            "borderwidth": 1,
            "bordercolor": "#000000"
        }
    }
    fig2.update_layout(**layout)
    pio.write_html(fig2, f"assets/week_{week}.html")

    # for matchup in matchups:

    #     layout = {
    #         "template": "plotly_white",
    #         "title": {"text": f"<b>{matchup[0]} vs {matchup[1]} Week {week} Summary</b>", "font": {"color": "#000000"}, "xanchor": "center", "x": .5},
    #         "yaxis": {"title": "<b>Points Scored</b>", "color": "#000000", "linecolor": "#000000", "range": [0, 200]},
    #         "xaxis": {"title": "<b>Ellapsed Football Time (hours)</b>", "color": "#000000", "linecolor": "#000000"},
    #         "width": 950,
    #         "height": 550,
    #         "legend": {
    #             "orientation": "h",
    #             "yanchor": "top",
    #             "y": 1.1,
    #             "xanchor": "center",
    #             "x": .5,
    #             "borderwidth": 1,
    #             "bordercolor": "#000000"
    #         }
    #     }
    #     fig = go.Figure(layout=layout)

    #     for manager in matchup:
    #         timestamps = []
    #         actual_scores = []
    #         projected_scores = []

    #         # time_ranges = [(1760055300, 1760068800), (1760275800, 1760328000), (1760397300, 1760414400)]
    #         # time_ranges = [(1760660100, 1760674500), (1760880600, 1760932800), (1761001200, 1761024600)]
    #         time_ranges = [(1761264900, 1761277500), (1761498000, 1761537600), (1761524100, 1761536700)]
    #         ellapsed_time = 0
    #         for idx, time_range in enumerate(time_ranges):
    #             lower_time, upper_time = time_range
    #             q = db.db_session.query(Manager)
    #             q = q.where(Manager.display_name == manager)
    #             q = q.join(ManagerScore, ManagerScore.manager_id == Manager.manager_id)
    #             q = q.where(ManagerScore.timestamp > lower_time)
    #             q = q.where(ManagerScore.timestamp < upper_time)
    #             q = q.add_columns(ManagerScore)
    #             q = q.order_by(ManagerScore.timestamp)
    #             results = q.all()

    #             for _, manager_score in results:
    #                 #timestamps.append(datetime.fromtimestamp(manager_score.timestamp))
    #                 time_in_period = manager_score.timestamp - lower_time
    #                 timestamps.append((time_in_period + ellapsed_time) / 3600)
    #                 actual_scores.append(manager_score.current_score)
    #                 projected_scores.append(manager_score.projected_score)
    #             ellapsed_time += upper_time - lower_time

    #         if manager == matchup[0]:
    #             line = {"color": "forestgreen"}
    #         else:
    #             line = {"color": "crimson"}

    #         fig.add_scatter(x=timestamps, y=actual_scores, name=f"{manager} Actual", mode="lines", line=line)
    #         line["dash"] = "dot"
    #         fig.add_scatter(x=timestamps, y=projected_scores, name=f"{manager} Projected", line=line)
    #         pio.write_html(fig, f"assets/week{week}_{matchup[0]}_{matchup[1]}.html")



if __name__ == "__main__":
    main()
