import plotly.graph_objects as go
import plotly.io as pio

from db_helper import DatabaseHelper
from sql_tables import Manager, ManagerScore
from datetime import datetime

def main():
    db = DatabaseHelper()
    
    q = db.db_session.query(Manager)
    managers = q.all()

    # matchups = [
    #     ("Magmarr", "TomBradyIsACheater"),
    #     ("WrightTeam", "Jroll22"),
    #     ("Ryman1994", "crsnyder"),
    #     ("Mint8erryCrunch", "Trevbawt")
    # ]

    week = 6
    matchups = [
        ("crsnyder", "Trevbawt"),
        ("Mint8erryCrunch", "Ryman1994"),
        ("Jroll22", "TomBradyIsACheater"),
        ("WrightTeam", "Magmarr")
    ]

    for matchup in matchups:

        layout = {
            "template": "plotly_white",
            "title": {"text": f"<b>{matchup[0]} vs {matchup[1]} Week 5 Summary</b>", "font": {"color": "#000000"}, "xanchor": "center", "x": .5},
            "yaxis": {"title": "<b>Points Scored</b>", "color": "#000000", "linecolor": "#000000", "range": [0, 200]},
            "xaxis": {"title": "<b>Ellapsed Football Time (hours)</b>", "color": "#000000", "linecolor": "#000000"},
            "width": 950,
            "height": 550,
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
        fig = go.Figure(layout=layout)

        for manager in matchup:
            timestamps = []
            actual_scores = []
            projected_scores = []

            time_ranges = [(1760055300, 1760068800), (1760275800, 1760328000), (1760397300, 1760414400)]
            ellapsed_time = 0
            for idx, time_range in enumerate(time_ranges):
                lower_time, upper_time = time_range
                q = db.db_session.query(Manager)
                q = q.where(Manager.display_name == manager)
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

            if manager == matchup[0]:
                line = {"color": "forestgreen"}
            else:
                line = {"color": "crimson"}

            fig.add_scatter(x=timestamps, y=actual_scores, name=manager, mode="lines", line=line)
            #fig.add_scatter(x=timestamps, y=projected_scores, name="Projected Score")
            pio.write_html(fig, f"assets/week6_{matchup[0]}_{matchup[1]}.html")



if __name__ == "__main__":
    main()
