
import argparse
from inspect import signature
from math import ceil, floor, log10
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

import gradio as gr
import pandas as pd

from analyzer import load_data, calculate_metrics
from visualizer import sales_by_category, daily_sales_trend


PROJECT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT / "data/kaggle_dataset/SuperMarket Analysis.csv"
CURRENCY_SYMBOL = "$"

METRICS = (
    ("Total sales (including tax)", "Total sales", "money"),
    ("Transactions", "Transactions", "count"),
    ("Units sold", "Units sold", "count"),
    ("Average transaction value", "Avg. transaction", "money"),
    ("Average rating", "Avg. rating", "rating"),
)

CSS = """
#smartdata {
    max-width: 1440px;
    margin: 0 auto;
    padding: 20px;
    background: #f1f5f9;
    border-radius: 16px;
}
#smartdata h1 { color: #0f2742; }
#bi-sidebar, .bi-chart {
    background: #ffffff;
    border: 1px solid #dbe4ee;
    border-radius: 12px;
}
#bi-sidebar { padding: 16px; }
.bi-kpi {
    min-height: 110px;
    padding: 14px;
    border: 1px solid #dbe4ee;
    border-radius: 12px;
    background: #ffffff;
    color: #0f2742;
}
.bi-kpi.hero {
    background: #0f2742;
    border-color: #0f2742;
    color: #ffffff;
}
.bi-kpi-label { color: #475569; font-size: .85rem; }
.bi-kpi-value {
    color: #0f2742;
    margin: 4px 0;
    font-size: clamp(1.3rem, 2vw, 1.8rem);
    font-weight: 700;
    font-variant-numeric: tabular-nums;
}
.bi-kpi-delta { color: #475569; font-size: .78rem; }
.bi-kpi-delta.up { color: #166534; }
.bi-kpi-delta.down { color: #991b1b; }
.bi-kpi.hero .bi-kpi-label { color: #dbeafe; }
.bi-kpi.hero .bi-kpi-delta { color: #cbd5e1; }
.bi-kpi.hero .bi-kpi-delta.up { color: #99f6e4; }
.bi-kpi.hero .bi-kpi-delta.down { color: #fecaca; }
/* Unified KPI cards */
#smartdata .bi-kpi {
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    min-height: 144px;
    border-top: 3px solid #0f766e;
    background: #ffffff;
}
#smartdata .bi-kpi.hero {
    background: #edf7f5;
    border-color: #cce5e0;
    border-top-color: #0f766e;
}
#smartdata .bi-kpi .bi-kpi-label { color: #475569; }
#smartdata .bi-kpi .bi-kpi-value { color: #0f2742; }
#smartdata .bi-kpi .bi-kpi-delta {
    min-height: 2.7em;
    margin-top: auto;
    line-height: 1.35;
    color: #475569;
}
#smartdata .bi-kpi .bi-kpi-delta.up { color: #166534; }
#smartdata .bi-kpi .bi-kpi-delta.down { color: #991b1b; }
"""


def format_metric(value, kind):
    if value is None or pd.isna(value):
        return "—"
    if kind == "money":
        return f"{CURRENCY_SYMBOL}{value:,.0f}"
    if kind == "rating":
        return f"{value:.2f}"
    return f"{value:,.0f}"


def metric_card(label, value, kind, previous=None, note=""):
    direction = ""
    if note:
        delta = note if label == "Total sales" and not pd.isna(value) else ""
    elif pd.isna(previous) or previous == 0 or pd.isna(value):
        delta = "Comparison unavailable"
    else:
        percent = 100 * (value - previous) / previous
        displayed = round(percent, 1)
        direction = "up" if displayed > 0 else "down" if displayed < 0 else ""
        delta = (
            f"{displayed:+.1f}% vs prior period"
            if displayed else "0.0% vs prior period"
        )

    return (
        f'<div class="bi-kpi{" hero" if label == "Total sales" else ""}">'
        f'<div class="bi-kpi-label">{label}</div>'
        f'<div class="bi-kpi-value">{format_metric(value, kind)}</div>'
        f'<div class="bi-kpi-delta {direction}">{delta}</div>'
        f'</div>'
    )


def compact_money(value):
    if abs(value) < 1000:
        return f"{CURRENCY_SYMBOL}{value:,.0f}"
    scale, suffix = (1_000_000, "M") if abs(value) >= 1_000_000 else (1000, "K")
    number = f"{value / scale:,.1f}".removesuffix(".0")
    return f"{CURRENCY_SYMBOL}{number}{suffix}"


def style_category_chart(figure):
    bars = [trace for trace in figure.data if trace.type == "bar"]
    largest = max((float(value) for trace in bars for value in trace.x), default=0)
    for trace in bars:
        trace.update(
            text=[compact_money(float(value)) for value in trace.x],
            marker_color="#0F766E",
            texttemplate="%{text}",
            cliponaxis=False,
        )

    if largest > 0:
        target = largest / 4
        magnitude = 10 ** floor(log10(target))
        step = next(magnitude * n for n in (1, 2, 5, 10) if magnitude * n >= target)
        ticks = [i * step for i in range(ceil(largest / step) + 1)]
        figure.update_xaxes(
            range=[0, max(ticks[-1], largest * 1.16)],
            tickmode="array",
            tickvals=ticks,
            ticktext=[compact_money(value) for value in ticks],
        )
    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    figure.update_xaxes(showgrid=False)
    figure.update_yaxes(showgrid=False)
    return figure


def style_trend_chart(figure):
    figure.update_traces(
        mode="lines",
        fill="tozeroy",
        line_color="#0F766E",
        marker_color="#0F766E",
        fillcolor="rgba(15, 118, 110, 0.10)",
        selector=dict(type="scatter"),
    )
    for trace in figure.data:
        if trace.type == "scatter" and trace.x is not None and len(trace.x) == 1:
            day = pd.Timestamp(trace.x[0])
            half_day = pd.Timedelta(hours=12)
            trace.update(mode="markers", marker=dict(size=10), fill="none")
            figure.update_xaxes(
                range=[day - half_day, day + half_day],
                tickmode="array",
                tickvals=[day],
                ticktext=[day.strftime("%d %b %Y")],
            )

    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    figure.update_xaxes(showgrid=False)
    figure.update_yaxes(showgrid=False)
    figure.update_yaxes(rangemode="tozero")
    return figure


def css_options(target):
    return {"css": CSS} if "css" in signature(target).parameters else {}


def build_sales_forecasts_tab():
    import plotly.express as px

    gr.Markdown(
        "## Historical forecast evaluation\n"
        "10–30 March 2019 · Next-day forecasts compared with recorded sales."
    )
    forecast_path = PROJECT / "reports" / "final_test_predictions.csv"
    if not forecast_path.is_file():
        gr.Markdown("March forecast results are unavailable.")
        return

    forecasts = pd.read_csv(forecast_path, parse_dates=["Date"])
    forecasts = forecasts.sort_values("Date")
    branches = sorted(forecasts["Branch"].unique())
    methods = ["Ridge regression", "Yesterday"]

    def show_branch(branch):
        rows = forecasts.loc[forecasts["Branch"].eq(branch)]
        actual = rows["Observed"]
        errors = rows[methods].sub(actual, axis=0).abs()

        # Percentage errors are calculated on days with positive sales.
        positive_sales = actual.gt(0)
        close = errors.loc[positive_sales].le(
            actual.loc[positive_sales] * 0.20, axis=0
        )

        metrics = [
            [
                method,
                round(errors[method].mean(), 2),
                f"{close[method].sum()} of {positive_sales.sum()}",
            ]
            for method in methods
        ]

        # Leave gaps on dates that were excluded from scoring.
        chart_data = rows.set_index("Date").reindex(
            pd.date_range("2019-03-10", "2019-03-30", name="Date")
        ).reset_index().rename(columns={
            "Observed": "Actual sales",
            "Yesterday": "Yesterday baseline",
        })
        chart = px.line(
            chart_data,
            x="Date",
            y=["Actual sales", "Ridge regression", "Yesterday baseline"],
            markers=True,
            color_discrete_sequence=["#304C67", "#008477", "#8195A6"],
            labels={"value": "Sales", "variable": ""},
            title=f"{branch} · Actual sales and forecasts",
        )
        chart.update_traces(connectgaps=False)
        return chart, metrics

    branch = gr.Dropdown(choices=branches, value=branches[0], label="Branch")
    initial_chart, initial_metrics = show_branch(branches[0])
    chart = gr.Plot(value=initial_chart)
    metrics = gr.Dataframe(
        headers=["Method", "Average error (MAE)", "Forecasts within 20%"],
        datatype=["str", "number", "str"],
        value=initial_metrics,
        interactive=False,
    )
    branch.change(fn=show_branch, inputs=branch, outputs=[chart, metrics])


def build_dashboard():
    df = load_data(DATA_PATH)
    first_day = df["Date"].min().normalize()
    last_day = df["Date"].max().normalize()
    date_choices = pd.date_range(first_day, last_day).strftime("%Y-%m-%d").tolist()
    first_date, last_date = date_choices[0], date_choices[-1]
    export_dir = TemporaryDirectory(prefix="smartdata_")

    def blank_view(message):
        cards = [
            metric_card(label, None, kind, note=message)
            for _, label, kind in METRICS
        ]
        return (*cards, None, None, None, message)

    def refresh(branch, start_date, end_date):
        if not start_date or not end_date:
            return blank_view("Select both a start date and an end date.")

        start, end = pd.Timestamp(start_date), pd.Timestamp(end_date)
        if start > end:
            return blank_view("Start date must be on or before end date.")

        branch_data = df if branch == "All branches" else df[df["Branch"] == branch]

        def transactions_between(first, last):
            day_after = last + pd.Timedelta(days=1)
            return branch_data[
                (branch_data["Date"] >= first) & (branch_data["Date"] < day_after)
            ]

        selected = transactions_between(start, end)
        if selected.empty:
            return blank_view("No transactions match. Try a wider date range.")

        prior_end = start - pd.Timedelta(days=1)
        prior_start = start - (end - start + pd.Timedelta(days=1))
        prior_metrics = {}
        note = ""
        if prior_start < first_day:
            note = "No prior period in dataset"
        else:
            prior = transactions_between(prior_start, prior_end)
            if prior.empty:
                note = "No prior transactions"
            else:
                prior_metrics = calculate_metrics(prior)

        metrics = calculate_metrics(selected)
        cards = [
            metric_card(label, metrics[key], kind, prior_metrics.get(key), note)
            for key, label, kind in METRICS
        ]

        category = style_category_chart(sales_by_category(selected))
        trend = style_trend_chart(daily_sales_trend(selected))

        export_path = Path(export_dir.name) / uuid4().hex / "smartdata_transactions.csv"
        export_path.parent.mkdir()
        selected.to_csv(export_path, index=False)
        return (*cards, category, trend, str(export_path), "")

    initial = refresh("All branches", first_date, last_date)

    with gr.Blocks(title="SmartData | Supermarket Sales", **css_options(gr.Blocks)) as demo:
        with gr.Tabs():
            with gr.Tab("Sales Dashboard"):
                with gr.Column(elem_id="smartdata"):
                    gr.Markdown("# SmartData | Supermarket Sales")

                    with gr.Row():
                        with gr.Column(scale=1, min_width=220, elem_id="bi-sidebar"):
                            gr.Markdown("## Filters")
                            branch = gr.Dropdown(
                                ["All branches"] + sorted(df["Branch"].unique()),
                                value="All branches",
                                label="Branch",
                            )
                            start = gr.Dropdown(date_choices, value=first_date, label="Start date")
                            end = gr.Dropdown(date_choices, value=last_date, label="End date")
                            message = gr.Markdown(value=initial[8])
                            download = gr.File(
                                value=initial[7],
                                label="Download transactions (CSV)",
                                interactive=False,
                            )
                            gr.Markdown(
                                "Sales include tax. The `$` symbol is for display. "
                                "The source does not specify a currency."
                            )

                        with gr.Column(scale=4, min_width=320):
                            with gr.Row():
                                cards = [
                                    gr.HTML(value=initial[i], min_width=145)
                                    for i in range(len(METRICS))
                                ]
                            with gr.Row():
                                category = gr.Plot(
                                    value=initial[5], show_label=False, elem_classes=["bi-chart"]
                                )
                                trend = gr.Plot(
                                    value=initial[6], show_label=False, elem_classes=["bi-chart"]
                                )

                    gr.on(
                        triggers=[branch.change, start.change, end.change],
                        fn=refresh,
                        inputs=[branch, start, end],
                        outputs=[*cards, category, trend, download, message],
                        trigger_mode="always_last",
                    )

            with gr.Tab("Sales Forecasts"):
                build_sales_forecasts_tab()

    return demo


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--share", action="store_true")
    args = parser.parse_args()
    demo = build_dashboard()
    demo.launch(share=args.share, **css_options(demo.launch))
