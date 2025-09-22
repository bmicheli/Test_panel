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

def create_panel_selection_card():
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
							"height": "65px", 
							"borderRadius": "8px",
							"border": "1px solid rgba(0, 188, 212, 0.3)",
							"fontSize": "13px"
						},
						className="mb-2"
					)
				], width=2),
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
					])
				], width=2),
				dbc.Col([
					html.Label([
						DashIconify(icon="mdi:lightbulb", width=14, className="me-1"),
						"HPO Suggestions"
					], className="fw-bold text-primary", style={"fontSize": "13px"}),
					html.Div(id="smart-hpo-suggestions-container", children=[
						html.Div([
							DashIconify(icon="mdi:information", width=16, className="me-2", style={"color": "#6c757d"}),
							"Select panels to see HPO suggestions"
						], className="text-muted text-center", 
						style={"fontSize": "11px", "fontStyle": "italic", "padding": "10px"})
					], style={
						"height": "130px",
						"border": "none",
						"borderRadius": "10px",
						"padding": "10px",
						"backgroundColor": "transparent",
						"display": "flex",
						"flexDirection": "row",
						"alignItems": "center",
						"justifyContent": "center",
						"gap": "8px",
					})
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
							DashIconify(icon="", width=12, className="me-1"),
							"🟢 Auto-generated from AU panels"
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
				], width=3)
			])
		], style={"padding": "1rem"})
	], className="glass-card mb-3 fade-in-up")

def create_enhanced_hpo_suggestion_card(hpo_term, keyword, suggestion_number, total_suggestions, confidence_score=None):
	if confidence_score and confidence_score >= 8:
		border_color = "rgba(40, 167, 69, 0.4)" 
		bg_color = "rgba(212, 237, 218, 0.3)"
		confidence_icon = "bi bi-check-circle-fill"
		confidence_color = "#28a745"
	elif confidence_score and confidence_score >= 5:
		border_color = "rgba(255, 193, 7, 0.4)"
		bg_color = "rgba(255, 248, 225, 0.3)"
		confidence_icon = "bi bi-info-circle-fill"
		confidence_color = "#ffc107"
	else:
		border_color = "rgba(0, 188, 212, 0.3)"
		bg_color = "rgba(248, 249, 250, 0.5)"
		confidence_icon = "bi bi-question-circle-fill"
		confidence_color = "#6c757d"
	
	return html.Div([
		html.Div([
			html.Div([
				html.Div([
					html.I(className=confidence_icon, style={"color": confidence_color, "fontSize": "14px"}),
					html.Small(f"from '{keyword}'", style={
						"fontSize": "9px", 
						"color": "#6c757d", 
						"marginLeft": "4px",
						"fontStyle": "italic"
					})
				], style={
					"display": "flex", 
					"alignItems": "center", 
					"marginBottom": "4px",
					"height": "15px"
				}),
			], style={"marginBottom": "6px"}),

			html.Div([
				html.Strong(hpo_term["name"], 
						style={
							"fontSize": "14px",
							"color": "#2c3e50", 
							"display": "block", 
							"marginBottom": "6px", 
							"lineHeight": "1.3", 
							"textAlign": "center", 
							"fontWeight": "600",
							"wordWrap": "break-word",
							"overflow": "hidden",
							"hyphens": "auto",  
							"padding": "0 4px"
						})
			], style={
				"marginBottom": "8px", 
				"height": "55px",  
				"display": "flex", 
				"alignItems": "center", 
				"justifyContent": "center",
				"overflow": "hidden"
			}),
			
			html.Div([
				dbc.Button(
					html.I(className="bi bi-x-lg", style={"fontSize": "14px"}),  # croix
					id={"type": "horizontal-hpo-skip-btn", "hpo_id": hpo_term["id"], "keyword": keyword},
					color="danger",
					size="sm",
					style={
						"borderRadius": "4px", 
						"width": "28px",
						"height": "28px", 
						"padding": "0",
						"display": "flex",
						"alignItems": "center",
						"justifyContent": "center",
						"backgroundColor": "#dc3545",
						"borderColor": "#dc3545",
						"flexShrink": "0" 
					},
					title="Skip this suggestion",
					n_clicks=0
				),

				html.Code(hpo_term['id'], style={
					"fontSize": "11px",
					"backgroundColor": "#e3f2fd", 
					"padding": "4px 8px",
					"borderRadius": "4px", 
					"display": "flex",
					"alignItems": "center",
					"justifyContent": "center",
					"textAlign": "center", 
					"color": "#1976d2", 
					"fontWeight": "500",
					"margin": "0 8px",  
					"minWidth": "70px",  
					"flexGrow": "1" 
				}),

				dbc.Button(
					html.I(className="bi bi-check-lg", style={"fontSize": "14px"}),  # check
					id={"type": "horizontal-hpo-keep-btn", "hpo_id": hpo_term["id"], "keyword": keyword},
					color="success",
					size="sm",
					style={
						"borderRadius": "4px", 
						"width": "28px",
						"height": "28px", 
						"padding": "0",
						"display": "flex",
						"alignItems": "center",
						"justifyContent": "center",
						"backgroundColor": "#28a745",
						"borderColor": "#28a745",
						"flexShrink": "0"  
					},
					title="Add to HPO terms",
					n_clicks=0
				)
			], style={
				"display": "flex", 
				"alignItems": "center",
				"justifyContent": "space-between",
				"height": "32px",
				"width": "100%"
			})
		], style={
			"display": "flex",
			"flexDirection": "column",
			"height": "100%",
			"justifyContent": "space-between",
			"padding": "8px"
		})
	], 
	id=f"horizontal-hpo-suggestion-{hpo_term['id']}",
	className="horizontal-hpo-card",
	style={
		"background": f"linear-gradient(135deg, #ffffff 0%, {bg_color} 100%)",
		"border": f"2px solid {border_color}",
		"borderRadius": "8px",
		"boxShadow": f"0 2px 6px {border_color}",
		"transition": "all 0.2s ease",
		"height": "120px",
		"width": "calc(33.33% - 8px)", 
		"minWidth": "200px",  
		"maxWidth": "250px",  
		"display": "flex",
		"flexDirection": "column",
		"overflow": "visible",
		"margin": "1px",  
		"flexShrink": "0"
	})

def create_action_buttons():
	return dbc.Card([
		dbc.CardBody([
			html.Div([
				dbc.Button([
					DashIconify(icon="mdi:refresh", width=18, className="me-2"),
					"Reset"
				], id="reset-btn", color="danger", size="md", style={"fontSize": "14px"}),

				html.Span(style={"width": "25px", "display": "inline-block"}),
				
				dbc.Button([
					DashIconify(icon="mdi:hammer-wrench", width=18, className="me-2"),
					"Build Panel"
				], id="load-genes-btn", color="primary", size="md", style={"fontSize": "14px"})
				
			], className="d-flex justify-content-center align-items-center")
		], style={"padding": "1rem"})
	], className="glass-card mb-3 fade-in-up")

def generate_panel_pie_chart(panel_df, panel_name, version=None):
	panel_df = panel_df[panel_df['confidence_level'] != 0].copy()
	
	conf_counts = panel_df.groupby('confidence_level').size().reset_index(name='count')
	conf_counts = conf_counts.sort_values('confidence_level', ascending=False)
	
	colors = ['#d4edda', '#fff3cd', '#f8d7da'] 
	
	labels = [f"{count} genes" for level, count in 
			zip(conf_counts['confidence_level'], conf_counts['count'])]

	fig, ax = plt.subplots(figsize=(9, 5), facecolor='none')
	ax.set_facecolor('none') 

	ax.pie(conf_counts['count'], labels=labels, colors=colors, autopct='%1.1f%%', 
		startangle=90, wedgeprops={'linewidth': 1, 'edgecolor': 'white'})
	ax.axis('equal') 

	title = f"Gene Distribution - {panel_name}"
	if version:
		title += f" (v{version})"

#	ax.set_title(title, fontsize=16, fontweight='bold', color='#2c3e50', pad=20)
	
	buf = io.BytesIO()
	plt.tight_layout()
	plt.savefig(buf, format="png", bbox_inches='tight', dpi=100, 
				facecolor='none', edgecolor='none', transparent=True)
	plt.close(fig)
	data = base64.b64encode(buf.getbuffer()).decode("ascii")
	
	return html.Div([
		html.H4(title, className="text-center mb-3", style={"fontSize": "16px"}),
		html.Img(src=f"data:image/png;base64,{data}", 
				style={"maxWidth": "100%", "height": "auto", "display": "block", "margin": "auto"})
	], style={
		"border": "none", 
		"padding": "10px", 
		"borderRadius": "8px", 
		"maxWidth": "100%", 
		"margin": "0",
		"height": "580px",  
		"display": "flex",
		"flexDirection": "column",
		"justifyContent": "center",
		"backgroundColor": "transparent"
	})

def create_hpo_terms_table(hpo_details):
	if not hpo_details:
		return html.Div()
	
	table_data = []
	for term in hpo_details:
		table_data.append({
			"HPO ID": term["id"],
			"Term Name": term["name"],
			"Definition": term["definition"][:120] + "..." if len(term["definition"]) > 120 else term["definition"]
		})
	
	return html.Div([
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
				"border": "none",
				"borderRadius": "8px",
				"width": "100%",
				"backgroundColor": "transparent"
			},
			style_cell={
				"textAlign": "left",
				"padding": "8px",
				"fontFamily": "Arial, sans-serif",
				"fontSize": "11px",
				"whiteSpace": "normal",
				"height": "auto",
				"minWidth": "60px",
				"maxWidth": "120px",
				"color": "#2c3e50",
				"backgroundColor": "transparent",
				"border": "none"
			},
			style_header={
				"fontWeight": "bold",
				"backgroundColor": "rgba(255, 255, 255, 0.4)",
				"border": "none",
				"fontSize": "12px",
				"color": "#2c3e50",
				"borderBottom": "1px solid rgba(200, 200, 200, 0.3)"
			},
			style_data={
				"backgroundColor": "transparent",
				"border": "none",
				"borderBottom": "1px solid rgba(200, 200, 200, 0.3)"
			},
			style_data_conditional=[
				{
					"if": {"row_index": "odd"},
					"backgroundColor": "rgba(255, 255, 255, 0.1)"
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
		"border": "none", 
		"padding": "10px", 
		"borderRadius": "8px",
		"background": "transparent",
		"width": "100%",
		"height": "100%",  
		"display": "flex",
		"flexDirection": "column"
	})
