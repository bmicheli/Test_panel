import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")
import io
import base64
from dash_iconify import DashIconify
from config import *

def create_header():
    """Create the modern header component with glass morphism"""
    return html.Div([
        dbc.Button(
            [DashIconify(icon="mdi:menu", width=20)],
            id="sidebar-toggle",
            color="primary",
            className="me-2",
            style={
                "position": "absolute", 
                "top": "15px", 
                "right": "15px",
                "zIndex": "1000",
                "borderRadius": "50%",
                "width": "40px",
                "height": "40px",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center"
            }
        ),
        html.Div([
            html.H1([
                DashIconify(icon="mdi:dna", width=32, className="me-3", style={"color": "#00BCD4"}),
                "Panel Builder"
            ], className="app-title mb-0", style={"fontSize": "2rem"}),
        ])
    ], className="glass-card app-header", style={"padding": "1.2rem"})

def create_sidebar():
    """Create sidebar with glass morphism effect"""
    return dbc.Offcanvas(
        id="sidebar-offcanvas",
        title=[
            DashIconify(icon="mdi:bookmark-multiple", width=20, className="me-2"),
            "Panel Presets"
        ],
        is_open=False,
        placement="start",
        backdrop=False,
        style={"width": "380px"},
        children=[
            html.Div([
                html.Div(id="preset-buttons", children=[
                    dbc.Button([
                        DashIconify(icon=preset["icon"], width=16, className="me-2"),
                        html.Div([
                            html.Strong(preset["name"], style={"fontSize": "14px"}),
                            html.Br(),
                        ])
                    ],
                    id={"type": "preset-btn", "index": key},
                    className="preset-btn w-100 mb-2",
                    n_clicks=0,
                    style={"fontSize": "13px", "padding": "10px 12px"}
                    ) for key, preset in PANEL_PRESETS.items()
                ])
            ], className="p-2")
        ]
    )

# NO TITLES FOR BOXES
def create_panel_selection_card():
    """Create panel selection card - NO TITLE"""
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label([
                        DashIconify(icon="flag-gb", width=14, className="me-1"),
                        "PanelApp UK"
                    ], className="fw-bold text-primary", style={"fontSize": "13px"}),
                    dcc.Dropdown(
                        id="dropdown-uk", 
                        placeholder="Select UK panels...", 
                        multi=True,
                        className="mb-2",
                        style={"fontSize": "13px"}
                    )
                ], width=4),
                dbc.Col([
                    html.Label([
                        DashIconify(icon="flag-au", width=14, className="me-1"),
                        "PanelApp Australia"
                    ], className="fw-bold text-primary", style={"fontSize": "13px"}),
                    dcc.Dropdown(
                        id="dropdown-au", 
                        placeholder="Select AU panels...", 
                        multi=True,
                        className="mb-2",
                        style={"fontSize": "13px"}
                    )
                ], width=4),
                dbc.Col([
                    html.Label([
                        DashIconify(icon="mdi:hospital-building", width=14, className="me-1"),
                        "Internal Panels"
                    ], className="fw-bold text-primary", style={"fontSize": "13px"}),
                    dcc.Dropdown(
                        id="dropdown-internal", 
                        placeholder="Select internal panels...", 
                        multi=True,
                        className="mb-2",
                        style={"fontSize": "13px"}
                    )
                ], width=4)
            ])
        ], style={"padding": "1rem"})
    ], className="glass-card mb-3 fade-in-up")

def create_options_card():
    """Create options and filters card - NO TITLE"""
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label([
                        DashIconify(icon="mdi:text-box-plus", width=14, className="me-1"),
                        "Manual Genes"
                    ], className="fw-bold text-primary", style={"fontSize": "13px"}),
                    dcc.Textarea(
                        id="manual-genes", 
                        placeholder="Enter gene symbols, one per line...",
                        style={
                            "width": "100%", 
                            "height": "100px",
                            "borderRadius": "8px",
                            "border": "1px solid rgba(0, 188, 212, 0.3)",
                            "fontSize": "13px"
                        },
                        className="mb-2"
                    )
                ], width=4),
                dbc.Col([
                    html.Label([
                        DashIconify(icon="mdi:filter", width=14, className="me-1"),
                        "Confidence Level Filter"
                    ], className="fw-bold text-primary", style={"fontSize": "13px"}),
                    html.Div([
                        dbc.Checklist(
                            id="confidence-filter",
                            options=[
                                {"label": " Green (High Confidence)", "value": 3},
                                {"label": " Amber (Moderate Confidence)", "value": 2},
                                {"label": " Red (Low Confidence)", "value": 1}
                            ],
                            value=[3, 2],
                            inline=False,
                            style={"fontSize": "13px"}
                        )
                    ], className="mb-2")
                ], width=4),
                dbc.Col([
                    html.Label([
                        DashIconify(icon="mdi:magnify", width=14, className="me-1"),
                        "HPO Terms"
                    ], className="fw-bold text-primary", style={"fontSize": "13px"}),
                    dcc.Dropdown(
                        id="hpo-search-dropdown",
                        placeholder="Type to search HPO terms...",
                        multi=True,
                        searchable=True,
                        options=[],
                        className="mb-2",
                        style={"fontSize": "13px"}
                    ),
                    html.Div([
                        html.Small([
                            DashIconify(icon="mdi:information", width=12, className="me-1"),
                            "Auto-generated from AU panels"
                        ], className="text-muted", style={"fontSize": "11px"}),
                        dcc.Loading(
                            id="hpo-loading",
                            type="default",
                            children=html.Div(id="hpo-loading-output"),
                            style={
                                "display": "inline-block", 
                                "marginLeft": "80px",
                                "transform": "scale(0.5)"
                            }
                        )
                    ], style={"display": "flex", "alignItems": "center"})
                ], width=4)
            ])
        ], style={"padding": "1rem"})
    ], className="glass-card mb-3 fade-in-up")

def create_action_buttons():
    """Create action buttons with spacing - IMPORT BUTTON REMOVED"""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                dbc.Button([
                    DashIconify(icon="mdi:refresh", width=18, className="me-2"),
                    "Reset"
                ], id="reset-btn", color="danger", size="md", style={"fontSize": "14px"}),
                
                # SPACING BETWEEN BUTTONS
                html.Span(style={"width": "25px", "display": "inline-block"}),
                
                dbc.Button([
                    DashIconify(icon="mdi:hammer-wrench", width=18, className="me-2"),
                    "Build Panel"
                ], id="load-genes-btn", color="primary", size="md", style={"fontSize": "14px"})
                
            ], className="d-flex justify-content-center align-items-center")
        ], style={"padding": "1rem"})
    ], className="glass-card mb-3 fade-in-up")

# KEEP ALL ORIGINAL FUNCTIONALITY - ONLY VISUAL CHANGES
def generate_panel_pie_chart(panel_df, panel_name, version=None):
    """Generate pie chart with ORIGINAL FUNCTIONALITY - ONLY VISUAL CHANGES"""
    panel_df = panel_df[panel_df['confidence_level'] != 0].copy()
    
    conf_counts = panel_df.groupby('confidence_level').size().reset_index(name='count')
    conf_counts = conf_counts.sort_values('confidence_level', ascending=False)
    
    colors = ['#d4edda', '#fff3cd', '#f8d7da']  # Green, Yellow, Red for 3,2,1
    
    labels = [f"{count} genes" for level, count in 
            zip(conf_counts['confidence_level'], conf_counts['count'])]
    
    # SAME SIZE AS ORIGINAL
    fig, ax = plt.subplots(figsize=(9, 5))  
    ax.pie(conf_counts['count'], labels=labels, colors=colors, autopct='%1.1f%%', 
        startangle=90, wedgeprops={'linewidth': 1, 'edgecolor': 'white'})
    ax.axis('equal') 

    title = f"Gene Distribution - {panel_name}"
    if version:
        title += f" (v{version})"
    
    # Convert plot to base64 image
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png", bbox_inches='tight', dpi=100)
    plt.close(fig)
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    
    return html.Div([
        html.H4(title, className="text-center mb-3", style={"fontSize": "16px"}),
        html.Img(src=f"data:image/png;base64,{data}", 
                style={"maxWidth": "100%", "height": "auto", "display": "block", "margin": "auto"})
    ], style={
        "border": "1px solid #999", 
        "padding": "10px", 
        "borderRadius": "8px", 
        "maxWidth": "100%", 
        "margin": "0",
        "height": "580px",  
        "display": "flex",
        "flexDirection": "column",
        "justifyContent": "center"
    })

def create_hpo_terms_table(hpo_details):
    """Create HPO terms table with ORIGINAL FUNCTIONALITY"""
    if not hpo_details:
        return html.Div()
    
    table_data = []
    for term in hpo_details:
        table_data.append({
            "HPO ID": term["id"],
            "Term Name": term["name"],
            "Definition": term["definition"][:80] + "..." if len(term["definition"]) > 80 else term["definition"]
        })
    
    return html.Div([
        html.H5(f"HPO Terms ({len(hpo_details)})", className="mb-3", style={"textAlign": "center", "fontSize": "16px"}),
        dash_table.DataTable(
            columns=[
                {"name": "HPO ID", "id": "HPO ID"},
                {"name": "Term Name", "id": "Term Name"},
                {"name": "Definition", "id": "Definition"}
            ],
            data=table_data,
            style_table={
                "overflowX": "auto",
                "height": "520px",  
                "overflowY": "auto",
                "border": "1px solid #ddd",
                "borderRadius": "8px",
                "width": "100%"
            },
            style_cell={
                "textAlign": "left",
                "padding": "8px",
                "fontFamily": "Arial, sans-serif",
                "fontSize": "11px",
                "whiteSpace": "normal",
                "height": "auto",
                "minWidth": "60px",
                "maxWidth": "120px"
            },
            style_header={
                "fontWeight": "bold",
                "backgroundColor": "#f8f9fa",
                "border": "1px solid #ddd",
                "fontSize": "12px"
            },
            style_data={
                "backgroundColor": "#ffffff",
                "border": "1px solid #eee"
            },
            style_data_conditional=[
                {
                    "if": {"row_index": "odd"},
                    "backgroundColor": "#f8f9fa"
                }
            ],
            page_action="native",  
            page_size=50,  
            virtualization=False,  
            tooltip_data=[
                {
                    "Definition": {"value": term["definition"], "type": "text"}
                    for column in ["HPO ID", "Term Name", "Definition"]
                } for term in hpo_details
            ],
            tooltip_duration=None
        )
    ], style={
        "border": "1px solid #999", 
        "padding": "10px", 
        "borderRadius": "8px",
        "backgroundColor": "#f8f9fa",
        "width": "100%",
        "height": "100%",  
        "display": "flex",
        "flexDirection": "column"
    })