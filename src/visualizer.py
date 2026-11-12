
import plotly.express as px


def sales_by_category(df):
    """Create a horizontal chart of sales by product category."""

    # Add up sales for each product category
    category_sales = (
        df.groupby("Product line", as_index=False)["Sales"]
        .sum()
        .sort_values("Sales", ascending=True)
    )

    # Create the interactive chart
    fig = px.bar(
        category_sales,
        x="Sales",
        y="Product line",
        orientation="h",
        title="Sales by Product Category",
        labels={
            "Sales": "Total sales (including tax)",
            "Product line": "Product category"
        },
        text="Sales",
        template="plotly_white"
    )

    fig.update_traces(
        marker_color="#2563EB",
        texttemplate="%{x:,.2f}",
        textposition="outside",
        cliponaxis=False,
        hovertemplate="%{y}<br>Sales: %{x:,.2f}<extra></extra>"
    )

    fig.update_layout(
        height=450,
        xaxis_tickformat=",.0f",
        yaxis={"categoryorder": "total ascending"},
        margin={"l": 30, "r": 100, "t": 70, "b": 50}
    )

    return fig


def daily_sales_trend(df):
    """Create a line chart showing total sales for each recorded date."""

    # Add up all transaction amounts for each date
    daily_sales = (
        df.groupby("Date", as_index=False)["Sales"]
        .sum()
        .sort_values("Date")
    )

    fig = px.line(
        daily_sales,
        x="Date",
        y="Sales",
        markers=True,
        title="Daily Sales Trend",
        labels={
            "Date": "Purchase date",
            "Sales": "Total sales (including tax)"
        },
        template="plotly_white"
    )

    fig.update_traces(
        line_color="#2563EB",
        hovertemplate=(
            "Date: %{x|%d %b %Y}"
            "<br>Sales: %{y:,.2f}<extra></extra>"
        )
    )

    fig.update_layout(
        height=450,
        yaxis_tickformat=",.0f",
        hovermode="x unified"
    )

    return fig
