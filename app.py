import pandas as pd
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash_ag_grid import AgGrid
import os
from dash import Dash
# Read and preprocess CSV
df = pd.read_csv("budget.csv")
df.columns = (
    df.columns.str.strip()
    .str.replace(" ", "_")
    .str.replace("[^a-zA-Z0-9_]", "", regex=True)
)
df['Budgeted_Amount'] = pd.to_numeric(df['Budgeted_Amount'], errors='coerce').fillna(0)
df['Actual_Amount'] = pd.to_numeric(df['Actual_Amount'], errors='coerce').fillna(0)
if "Record_Date" in df.columns:
    df['Record_Date'] = pd.to_datetime(df['Record_Date'], errors='coerce')
df['Variance'] = df['Budgeted_Amount'] - df['Actual_Amount']

GROUPBY_OPTIONS = [
    {"label": "Expenditure Category", "value": "Expenditure_Category"},
    {"label": "Cost Type", "value": "Obj_Class_Name"},
    {"label": "Line Item", "value": "Expenditure_Line_Item"},
    {"label": "Department", "value": "Department"},
    {"label": "Division", "value": "Division"},
    {"label": "Fund Name", "value": "Fund_Name"},
    {"label": "Cost Center", "value": "Cost_Center"},
]

DEEP_BLUE = "#0d1a36"
LIGHT_BLUE = "#64b5f6"
ORANGE = "#ff9800"

KPI_CARD_STYLE_BUDGETED = {
    "background": f"linear-gradient(135deg, {DEEP_BLUE} 60%, #233e6b 100%)",
    "color": "white",
    "border": "none",
    "boxShadow": "0 2px 8px rgba(13, 26, 54, 0.1)",
    "textAlign": "center",
    "borderRadius": "18px",
    "padding": "0.5rem"
}
KPI_CARD_STYLE_ACTUAL = {
    "background": f"linear-gradient(135deg, {LIGHT_BLUE} 60%, #b3e5fc 100%)",
    "color": "white",
    "border": "none",
    "boxShadow": "0 2px 8px rgba(100, 181, 246, 0.1)",
    "textAlign": "center",
    "borderRadius": "18px",
    "padding": "0.5rem"
}
KPI_CARD_STYLE_VARIANCE = {
    "background": f"linear-gradient(135deg, {ORANGE} 60%, #ffe0b2 100%)",
    "color": "white",
    "border": "none",
    "boxShadow": "0 2px 8px rgba(255, 152, 0, 0.1)",
    "textAlign": "center",
    "borderRadius": "18px",
    "padding": "0.5rem"
}
KPI_TEXT_STYLE = {
    "color": "white",
    "fontSize": "2.2rem",
    "fontWeight": "bold",
    "margin": "0"
}

def make_select(id, options, placeholder):
    return dbc.Select(
        id=id,
        options=[{"label": "All", "value": ""}] + [{"label": o, "value": o} for o in options],
        placeholder=placeholder,
        style={"height": "auto", "minHeight": "38px"}
    )

def format_number(n):
    return f"{n:,.0f}".replace(",", " ")  # non-breaking space

def get_slider_marks(vmin, vmax):
    step = (vmax - vmin) // 4 if vmax > vmin else 1
    marks = {}
    for i in range(5):
        val = vmin + i * step
        if val > vmax:
            val = vmax
        marks[val] = format_number(val)
    marks[vmax] = format_number(vmax)
    return marks

variance_min = int(df['Variance'].min())
variance_max = int(df['Variance'].max())

# Table columns: 11 columns, date first
TABLE_COLS = [
    "Record_Date", "Department", "Division", "Cost_Center", "Fund_Name",
    "Budgeted_Amount", "Actual_Amount", "Variance",
    "Obj_Class_Name", "Expenditure_Category", "Expenditure_Line_Item"
]

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    html.H2("Budget Dashboard", className="my-4 text-center"),

    dbc.Card([
        dbc.CardBody([
            html.H4("Filters", className="mb-3"),
            dbc.Row([
                dbc.Col([
                    html.Label("Department", style={"fontWeight": "bold"}),
                    make_select(
                        "department-filter",
                        sorted(df["Department"].dropna().unique()) if "Department" in df.columns else [],
                        "Select Department"
                    )
                ], width=3),
                dbc.Col([
                    html.Label("Division", style={"fontWeight": "bold"}),
                    make_select(
                        "division-filter",
                        sorted(df["Division"].dropna().unique()) if "Division" in df.columns else [],
                        "Select Division"
                    )
                ], width=3),
                dbc.Col([
                    html.Label("Cost Center", style={"fontWeight": "bold"}),
                    make_select(
                        "costcenter-filter",
                        sorted(df["Cost_Center"].dropna().unique()) if "Cost_Center" in df.columns else [],
                        "Select Cost Center"
                    )
                ], width=3),
                dbc.Col([
                    html.Label("Variance Range", style={"fontWeight": "bold"}),
                    dcc.RangeSlider(
                        id="variance-slider",
                        min=variance_min,
                        max=variance_max,
                        value=[variance_min, variance_max],
                        marks=get_slider_marks(variance_min, variance_max),
                        tooltip={"placement": "bottom", "always_visible": False},
                        allowCross=False
                    )
                ], width=3),
            ], className="mb-4"),
        ])
    ], className="mb-4", style={"background": "white"}),

    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Total Budgeted", style={"background": "transparent", "color": "white", "border": "none"}),
                    dbc.CardBody(html.H4(id="kpi-budget", className="card-title", style=KPI_TEXT_STYLE))
                ], style=KPI_CARD_STYLE_BUDGETED), width=4),
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Total Actual", style={"background": "transparent", "color": "white", "border": "none"}),
                    dbc.CardBody(html.H4(id="kpi-actual", className="card-title", style=KPI_TEXT_STYLE))
                ], style=KPI_CARD_STYLE_ACTUAL), width=4),
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Total Variance", style={"background": "transparent", "color": "white", "border": "none"}),
                    dbc.CardBody(html.H4(id="kpi-variance", className="card-title", style=KPI_TEXT_STYLE))
                ], style=KPI_CARD_STYLE_VARIANCE), width=4),
            ], className="mb-4"),
            html.H3(id="active-filters", className="mb-3", style={
                "textAlign": "center", "fontWeight": "bold", "fontSize": "2rem", "color": "#0d1a36"
            }),
            html.H5("Group by", className="mb-2"),
            dbc.Row([
                dbc.Col(
                    dbc.Select(
                        id="groupby-bar",
                        options=GROUPBY_OPTIONS,
                        value="Expenditure_Category",
                        style={"height": "auto", "minHeight": "38px"}
                    ),
                    width=12
                ),
            ], className="mb-4"),
            dcc.Graph(id="bar-chart", style={"height": "50vh"}),
        ])
    ], style={"background": "white"}),

    html.Hr(),
    html.H4("Select filter or click a bar to see details below", className="mt-4 mb-2", id="details-title"),
    AgGrid(
        id="details-table",
        columnDefs=[],
        rowData=[],
        style={"height": "500px", "width": "100%"},
        theme="alpine",
        dashGridOptions={
            "pagination": True,
            "paginationPageSize": 15,
        },
        columnSize="sizeToFit"
    )
], fluid=True, style={"height": "100vh", "width": "100vw", "padding": "0", "background": "#f8f9fa"})

# --- Filter dropdowns are synchronized based on selection ---
@app.callback(
    Output("division-filter", "options"),
    Output("division-filter", "value"),
    Output("costcenter-filter", "options"),
    Output("costcenter-filter", "value"),
    Output("department-filter", "options"),
    Output("department-filter", "value"),
    Input("department-filter", "value"),
    Input("division-filter", "value"),
    Input("costcenter-filter", "value"),
)
def sync_filters(department, division, costcenter):
    filtered = df.copy()
    department_options = sorted(filtered["Department"].dropna().unique())
    if department and department not in department_options:
        department = ""
    filtered2 = filtered.copy()
    if department:
        filtered2 = filtered2[filtered2["Department"] == department]
    division_options = sorted(filtered2["Division"].dropna().unique())
    if division and division not in division_options:
        division = ""
    filtered3 = filtered2.copy()
    if division:
        filtered3 = filtered3[filtered3["Division"] == division]
    costcenter_options = sorted(filtered3["Cost_Center"].dropna().unique())
    if costcenter and costcenter not in costcenter_options:
        costcenter = ""
    return (
        [{"label": "All", "value": ""}] + [{"label": o, "value": o} for o in division_options],
        division,
        [{"label": "All", "value": ""}] + [{"label": o, "value": o} for o in costcenter_options],
        costcenter,
        [{"label": "All", "value": ""}] + [{"label": o, "value": o} for o in department_options],
        department
    )

# --- Main chart and KPIs update based on filters ---
@app.callback(
    Output("active-filters", "children"),
    Output("bar-chart", "figure"),
    Output("kpi-budget", "children"),
    Output("kpi-actual", "children"),
    Output("kpi-variance", "children"),
    Input("department-filter", "value"),
    Input("division-filter", "value"),
    Input("costcenter-filter", "value"),
    Input("variance-slider", "value"),
    Input("groupby-bar", "value"),
)
def update_bar_chart(department, division, costcenter, variance_range, group_col):
    filters = []
    if department:
        filters.append(f"Department: {department}")
    if division:
        filters.append(f"Division: {division}")
    if costcenter:
        filters.append(f"Cost Center: {costcenter}")
    filters.append(f"Variance: {variance_range[0]:,.0f} – {variance_range[1]:,.0f}")
    filters_text = " | ".join(filters) if filters else "All data"

    filtered = df.copy()
    if department:
        filtered = filtered[filtered["Department"] == department]
    if division:
        filtered = filtered[filtered["Division"] == division]
    if costcenter:
        filtered = filtered[filtered["Cost_Center"] == costcenter]
    filtered = filtered[
        (filtered["Variance"] >= variance_range[0]) &
        (filtered["Variance"] <= variance_range[1])
    ]

    chart_df = (
        filtered.groupby(group_col)[["Budgeted_Amount", "Actual_Amount", "Variance"]]
        .sum()
        .reset_index()
    )

    fig = go.Figure()
    fig.add_bar(
        x=chart_df[group_col],
        y=chart_df["Budgeted_Amount"],
        name="Budgeted",
        marker_color=DEEP_BLUE
    )
    fig.add_bar(
        x=chart_df[group_col],
        y=chart_df["Actual_Amount"],
        name="Actual",
        marker_color=LIGHT_BLUE
    )
    # Add Variance as a line (no markers)
    fig.add_trace(
        go.Scatter(
            x=chart_df[group_col],
            y=chart_df["Variance"],
            name="Variance",
            mode="lines",
            line=dict(color=ORANGE, width=3, dash="dash"),
            yaxis="y2"
        )
    )
    fig.update_layout(
        barmode="group",
        title=f"Budget vs Actual by {group_col.replace('_', ' ')}",
        xaxis_title=group_col.replace('_', ' '),
        yaxis_title="Amount",
        yaxis2=dict(
            title="Variance",
            overlaying="y",
            side="right",
            showgrid=False,
            zeroline=True
        ),
        margin=dict(l=40, r=40, t=60, b=40),
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )
    fig.update_xaxes(automargin=True)

    total_budget = filtered["Budgeted_Amount"].sum()
    total_actual = filtered["Actual_Amount"].sum()
    total_variance = total_budget - total_actual

    return (
        filters_text,
        fig,
        f"${format_number(total_budget)}",
        f"${format_number(total_actual)}",
        f"${format_number(total_variance)}"
    )

# --- Details table updates on bar click or filter change ---
@app.callback(
    Output("details-title", "children"),
    Output("details-table", "columnDefs"),
    Output("details-table", "rowData"),
    Input("bar-chart", "clickData"),
    Input("department-filter", "value"),
    Input("division-filter", "value"),
    Input("costcenter-filter", "value"),
    Input("variance-slider", "value"),
    Input("groupby-bar", "value"),
)
def update_details_table(clickData, department, division, costcenter, variance_range, group_col):
    # Filter the dataframe based on dropdowns and slider
    filtered = df.copy()
    if department:
        filtered = filtered[filtered["Department"] == department]
    if division:
        filtered = filtered[filtered["Division"] == division]
    if costcenter:
        filtered = filtered[filtered["Cost_Center"] == costcenter]
    filtered = filtered[
        (filtered["Variance"] >= variance_range[0]) &
        (filtered["Variance"] <= variance_range[1])
    ]

    # If a bar is clicked, filter for that group value
    if clickData and "points" in clickData and len(clickData["points"]) > 0:
        group_value = clickData["points"][0]["x"]
        details = filtered[filtered[group_col] == group_value]
        title = f"Details for: {group_col.replace('_', ' ')} = {group_value}"
    else:
        details = filtered
        title = "Select filter or click a bar to see details below"

    table_df = details.copy()
    # Format date as string if present
    if "Record_Date" in table_df.columns:
        table_df["Record_Date"] = table_df["Record_Date"].dt.strftime("%Y-%m-%d")
    table_df["Variance"] = table_df["Budgeted_Amount"] - table_df["Actual_Amount"]

    # Only include columns that exist in the dataframe
    ordered_cols = [col for col in TABLE_COLS if col in table_df.columns]
    if not ordered_cols:
        return title, [], []

    # Build column definitions for AG Grid
    columnDefs = []
    for col in ordered_cols:
        coldef = {"headerName": col.replace("_", " "), "field": col}
        if pd.api.types.is_numeric_dtype(table_df[col]):
            coldef["filter"] = "agNumberColumnFilter"
        else:
            coldef["filter"] = "agTextColumnFilter"
        columnDefs.append(coldef)

    rowData = table_df[ordered_cols].to_dict("records")

    return title, columnDefs, rowData


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))  # 8050 az alapértelmezett, de Render felülírja
    app.run(host="0.0.0.0", port=port)