import plotly.graph_objects as go
import plotly.io as pio

from db_helper import DatabaseHelper
from sql_tables import Manager, ManagerScore
from datetime import datetime

def main():
    db = DatabaseHelper()
    
    q = db.db_session.query(Manager)
    managers = q.all()

    for manager in managers:
        q = db.db_session.query(Manager)
        q = q.where(Manager.display_name == manager.display_name)
        q = q.join(ManagerScore, ManagerScore.manager_id == Manager.manager_id)
        q = q.add_columns(ManagerScore)
        q = q.order_by(ManagerScore.timestamp)

        timestamps = []
        actual_scores = []
        projected_scores = []
        for manager, manager_score in q.all():
            timestamps.append(datetime.fromtimestamp(manager_score.timestamp))
            actual_scores.append(manager_score.current_score)
            projected_scores.append(manager_score.projected_score)

        ymax = 1.1 * (max(projected_scores) if max(projected_scores) > max(actual_scores) else max(actual_scores))

        layout = {
            "template": "plotly_white",
            "title": {"text": f"<b>@{manager} Week 4 Summary</b>", "font": {"color": "#000000"}, "xanchor": "center", "x": .5},
            "yaxis": {"title": "<b>Points Scored</b>", "color": "#000000", "linecolor": "#000000", "range": [0, ymax]},
            "xaxis": {"color": "#000000", "linecolor": "#000000"},
            "width": 950,
            "height": 550,
            "legend": {
                "orientation": "h",
                "yanchor": "bottom",
                "y": -.2,
                "xanchor": "center",
                "x": .5,
                "borderwidth": 1,
                "bordercolor": "#000000"
            }
        }

        fig = go.Figure(layout=layout)
        fig.add_scatter(x=timestamps, y=actual_scores, name="Actual Score")
        fig.add_scatter(x=timestamps, y=projected_scores, name="Projected Score")
        pio.write_html(fig, f"assets/{manager}.html")



if __name__ == "__main__":
    main()
