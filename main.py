"""
Main application file for PanelBuilder
VISUAL CHANGES ONLY - KEEP ALL ORIGINAL FUNCTIONALITY
IMPORT FUNCTIONALITY REMOVED - Z-INDEX ISSUES FIXED
SPINNER FULL SCREEN ADDED
HPO SUGGESTIONS INTERACTIVES ADDED
"""

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Output, Input, State, callback_context, ALL, dash_table
import pandas as pd
import json
import time
from datetime import datetime
import threading
import schedule
import os
import base64
import matplotlib.pyplot as plt
from matplotlib_venn import venn2, venn3
import io
import numpy as np
import concurrent.futures
from functools import lru_cache

# Import local modules
from config import *
from utils import *
from components import *

# =============================================================================
# GLOBAL VARIABLES FOR PANEL DATA
# =============================================================================

panels_uk_df = None
panels_au_df = None
internal_df = None
internal_panels = None
last_refresh = None

# =============================================================================
# PANEL REFRESH FUNCTIONS (ORIGINAL)
# =============================================================================

def refresh_panels():
    """Refresh panel data"""
    global panels_uk_df, panels_au_df, internal_df, internal_panels, last_refresh
    
    try:
        logger.info(f"🔄 Refreshing panels at {datetime.now()}")
        
        fetch_panel_genes_cached.cache_clear()
        fetch_hpo_term_details_cached.cache_clear()
        fetch_panel_disorders_cached.cache_clear()
        
        logger.info("Fetching UK panels...")
        panels_uk_df = fetch_panels(PANELAPP_UK_BASE)
        logger.info(f"✅ Loaded {len(panels_uk_df)} UK panels")
        
        logger.info("Fetching AU panels...")
        panels_au_df = fetch_panels(PANELAPP_AU_BASE)
        logger.info(f"✅ Loaded {len(panels_au_df)} AU panels")
        
        logger.info("Loading internal panels...")
        internal_df, internal_panels = load_internal_panels_from_files()
        logger.info(f"✅ Loaded {len(internal_panels)} internal panels")
        
        last_refresh = datetime.now()
        logger.info(f"✅ Panels refresh completed at {last_refresh}")
        
    except Exception as e:
        logger.error(f"❌ Error refreshing panels: {e}")

def schedule_panel_refresh():
    schedule.every().monday.at("06:00").do(refresh_panels)
    
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("📅 Panel refresh scheduler started")

def initialize_panels():
    logger.info("Initializing PanelBuilder...")
    start_time = time.time()
    
    refresh_panels()
    schedule_panel_refresh()
    
    logger.info(f"Initialization completed in {time.time() - start_time:.2f} seconds")

# =============================================================================
# APP INITIALIZATION
# =============================================================================

app = dash.Dash(__name__, external_stylesheets=EXTERNAL_STYLESHEETS, suppress_callback_exceptions=True)
app.title = "PanelBuilder"

app.index_string = f'''
<!DOCTYPE html>
<html>
    <head>
        {{%metas%}}
        <title>{{%title%}}</title>
        {{%favicon%}}
        {{%css%}}
        <style>
            {CUSTOM_CSS}
            
            /* FORCE DROPDOWN Z-INDEX - SOLUTION DÉFINITIVE */
            .Select-menu-outer,
            .Select-menu,
            .dropdown-menu,
            .dash-dropdown .Select-menu-outer,
            .dash-dropdown .dropdown-menu,
            .css-26l3qy-menu,
            .css-1pahdxg-control,
            ._dash-undo-redo,
            .dash-spinner,
            [class*="menu"], 
            [class*="Menu"], 
            [class*="dropdown"], 
            [class*="Dropdown"] {{
                z-index: 999999 !important;
                position: relative !important;
            }}
            
            /* ASSURER QUE LES DROPDOWNS SONT AU-DESSUS DE TOUT */
            .Select-control {{
                z-index: 999998 !important;
            }}
        </style>
        <script>
            // SCRIPT POUR FORCER LE Z-INDEX DES DROPDOWNS
            document.addEventListener('DOMContentLoaded', function() {{
                function fixDropdownZIndex() {{
                    // Cibler tous les éléments dropdown possibles
                    const dropdownSelectors = [
                        '.Select-menu-outer',
                        '.Select-menu', 
                        '.dropdown-menu',
                        '.dash-dropdown .Select-menu-outer',
                        '.dash-dropdown .dropdown-menu',
                        '.css-26l3qy-menu',
                        '.css-1pahdxg-control',
                        '._dash-undo-redo',
                        '[class*="menu"]',
                        '[class*="Menu"]',
                        '[class*="dropdown"]',
                        '[class*="Dropdown"]'
                    ];
                    
                    dropdownSelectors.forEach(selector => {{
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(element => {{
                            element.style.zIndex = '999999';
                            element.style.position = 'relative';
                        }});
                    }});
                }}
                
                // Exécuter immédiatement
                fixDropdownZIndex();
                
                // Ré-exécuter après un délai pour les éléments dynamiques
                setTimeout(fixDropdownZIndex, 1000);
                
                // Observer les changements DOM pour les nouveaux dropdowns
                const observer = new MutationObserver(fixDropdownZIndex);
                observer.observe(document.body, {{ childList: true, subtree: true }});
                
                // Ré-exécuter périodiquement
                setInterval(fixDropdownZIndex, 2000);
            }});
        </script>
    </head>
    <body>
        {{%app_entry%}}
        <footer>
            {{%config%}}
            {{%scripts%}}
            {{%renderer%}}
        </footer>
    </body>
</html>
'''

initialize_panels()

# =============================================================================
# APP LAYOUT - AVEC LES NOUVEAUX STORES
# =============================================================================

app.layout = dbc.Container([
    # Download component for gene export
    dcc.Download(id="download-genes"),
    
    # NOUVEAU: Spinner full screen
    html.Div(
        id="fullscreen-spinner",
        className="fullscreen-spinner-overlay hide",
        children=[
            html.Div([
                html.Div(className="custom-spinner"),
                html.Div("Building Panel...", className="spinner-text"),
                html.Div("Please wait while we process your data", className="spinner-subtext")
            ], className="spinner-container")
        ]
    ),

    # Sidebar
    create_sidebar(),
    
    # Header
    create_header(),
    
    # Panel Selection - NO TITLE
    create_panel_selection_card(),
    
    # Options & Filters - NO TITLE  
    create_options_card(),
    
    # Action Buttons
    create_action_buttons(),
    
    # Visualization section - NOW WRAPPED IN GLASS CARD
    html.Div(id="venn-hpo-row", style={"marginBottom": "20px", "display": "none"}, children=[
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col(
                        html.Div(id="venn-container"), 
                        width=7, 
                        style={
                            "paddingRight": "15px", 
                            "display": "flex", 
                            "flexDirection": "column",
                            "height": "600px"  
                        }
                    ),
                    dbc.Col(
                        html.Div(id="hpo-terms-table-container"), 
                        width=5, 
                        style={
                            "paddingLeft": "5px",
                            "display": "flex", 
                            "flexDirection": "column",
                            "height": "600px"  
                        }
                    )
                ], className="no-gutters", style={"display": "flex", "flexWrap": "nowrap"})
            ], style={"padding": "1rem"})
        ], className="glass-card fade-in-up")
    ]),
    
    # Gene table section (keep original functionality)
    html.Div(id="gene-table-output"),
    
    # Export section - NOW WRAPPED IN GLASS CARD (PANEL SUMMARY ONLY)
    html.Div(
        id="generate-code-section",
        style={"display": "none", "width": "100%"},
        children=[
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        dbc.Button("Generate Panel Summary", id="generate-code-btn", color="primary", className="me-2"),
                        dbc.Button("Export Genes", id="export-genes-btn", color="success")
                    ], style={"textAlign": "center", "marginBottom": "15px"}),
                    html.Div([
                        html.Label("Panel Summary:", style={"fontWeight": "bold", "marginBottom": "8px", "fontSize": "14px"}),
                        dcc.Textarea(id="panel-summary-output", 
                                    style={"width": "100%", "height": "70px", 
                                        "margin": "0 auto", "display": "block",
                                        "borderRadius": "8px", "border": "1px solid rgba(0, 188, 212, 0.3)",
                                        "fontSize": "13px"}, readOnly=True),
                        html.Div(id="copy-notification-summary", 
                                style={"textAlign": "center", "marginTop": "8px", "height": "25px"})
                    ], id="panel-summary-container-text")
                ], style={"padding": "1.5rem"})
            ], className="glass-card fade-in-up", style={"marginBottom": "20px"})
        ]
    ),
    
    # Data stores (keep original + new stores)
    dcc.Store(id="gene-list-store"),
    dcc.Store(id="gene-data-store"),
    # NOUVEAUX STORES POUR LES SUGGESTIONS HPO
    dcc.Store(id="rejected-hpo-store", data=[]),
    dcc.Store(id="suggestion-counter-store", data=0),
	dcc.Store(id="hpo-debug-info-store", data={}),
	dcc.Store(id="hpo-quality-metrics", data={}),
    
], fluid=True, style={
    "minHeight": "100vh",
    "background": "linear-gradient(135deg, #00BCD4 0%, #4DD0E1 50%, #80E5A3 100%)"
})

# =============================================================================
# CALLBACKS - DROPDOWN OPTIONS (ORIGINAL)
# =============================================================================

@app.callback(
    [Output("dropdown-uk", "options"),
     Output("dropdown-au", "options"), 
     Output("dropdown-internal", "options")],
    [Input("dropdown-uk", "id")]
)
def update_dropdown_options(_):
    uk_options = panel_options(panels_uk_df) if panels_uk_df is not None else []
    au_options = panel_options(panels_au_df) if panels_au_df is not None else []
    internal_options_list = internal_options(internal_panels) if internal_panels is not None else []
    
    return uk_options, au_options, internal_options_list

# =============================================================================
# CALLBACKS - SIDEBAR MANAGEMENT (ORIGINAL)
# =============================================================================

@app.callback(
    Output("sidebar-offcanvas", "is_open"),
    Input("sidebar-toggle", "n_clicks"),
    State("sidebar-offcanvas", "is_open"),
    prevent_initial_call=True
)
def toggle_sidebar(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

@app.callback(
    [Output("dropdown-uk", "value", allow_duplicate=True),
     Output("dropdown-au", "value", allow_duplicate=True),
     Output("dropdown-internal", "value", allow_duplicate=True),
     Output("confidence-filter", "value", allow_duplicate=True),
     Output("manual-genes", "value", allow_duplicate=True),
     Output("hpo-search-dropdown", "value", allow_duplicate=True),
     Output("hpo-search-dropdown", "options", allow_duplicate=True),
     Output("sidebar-offcanvas", "is_open", allow_duplicate=True)],
    Input({"type": "preset-btn", "index": ALL}, "n_clicks"),
    State("hpo-search-dropdown", "options"),
    prevent_initial_call=True
)
def apply_preset(n_clicks_list, current_hpo_options):
    ctx = callback_context
    if not ctx.triggered or all(n == 0 for n in n_clicks_list):
        raise dash.exceptions.PreventUpdate
    
    prop_id = ctx.triggered[0]["prop_id"]
    preset_key = json.loads(prop_id.split(".")[0])["index"]
    preset = PANEL_PRESETS[preset_key]
    
    uk_panels = preset.get("uk_panels", [])
    au_panels = preset.get("au_panels", [])
    internal_panels = preset.get("internal", [])
    conf_levels = preset.get("conf", [3, 2])
    manual_genes_list = preset.get("manual", [])
    manual_genes_text = "\n".join(manual_genes_list) if manual_genes_list else ""
    hpo_terms = preset.get("hpo_terms", [])
    
    updated_hpo_options = current_hpo_options or []
    existing_option_values = [opt["value"] for opt in updated_hpo_options]
    
    new_hpo_terms = [term for term in hpo_terms if term not in existing_option_values]
    if new_hpo_terms:
        hpo_details_list = fetch_hpo_terms_parallel(new_hpo_terms)
        
        for hpo_details in hpo_details_list:
            option = {
                "label": f"{hpo_details['name']} ({hpo_details['id']})",
                "value": hpo_details['id']
            }
            updated_hpo_options.append(option)
    
    return (uk_panels, au_panels, internal_panels, conf_levels, manual_genes_text, 
            hpo_terms, updated_hpo_options, False)

# =============================================================================
# CALLBACKS - HPO MANAGEMENT (ORIGINAL)
# =============================================================================

@app.callback(
    Output("hpo-search-dropdown", "value", allow_duplicate=True),
    Output("hpo-search-dropdown", "options", allow_duplicate=True),
    Output("hpo-loading-output", "children", allow_duplicate=True),
    Input("dropdown-au", "value"),
    State("hpo-search-dropdown", "value"),
    State("hpo-search-dropdown", "options"),
    prevent_initial_call=True
)
def auto_generate_hpo_from_panels_preview(au_ids, current_hpo_values, current_hpo_options):
    # SOLUTION: Vérifier si au_ids est vide dès le début
    if not au_ids:
        # Ne pas afficher de spinner et retourner les valeurs actuelles
        return current_hpo_values or [], current_hpo_options or [], html.Div()
    
    panel_hpo_terms = get_hpo_terms_from_panels(uk_ids=None, au_ids=au_ids)
    
    if not panel_hpo_terms:
        return current_hpo_values or [], current_hpo_options or [], html.Div()
    
    hpo_details_list = fetch_hpo_terms_parallel(panel_hpo_terms)
    
    new_hpo_options = []
    new_hpo_values = []
    
    for hpo_details in hpo_details_list:
        hpo_id = hpo_details['id']
        option = {
            "label": f"{hpo_details['name']} ({hpo_id})",
            "value": hpo_id
        }
        new_hpo_options.append(option)
        new_hpo_values.append(hpo_id)
    
    current_values = current_hpo_values or []
    current_options = current_hpo_options or []
    
    all_values = list(set(current_values + new_hpo_values))
    
    existing_option_values = [opt["value"] for opt in current_options]
    all_options = current_options.copy()
    
    for option in new_hpo_options:
        if option["value"] not in existing_option_values:
            all_options.append(option)
    
    return all_values, all_options, html.Div()

@app.callback(
    Output("hpo-search-dropdown", "options", allow_duplicate=True),
    Input("hpo-search-dropdown", "search_value"),
    State("hpo-search-dropdown", "value"),
    State("hpo-search-dropdown", "options"),
    prevent_initial_call=True
)
def update_hpo_options(search_value, current_values, current_options):
    selected_options = []
    if current_values and current_options:
        selected_options = [opt for opt in current_options if opt["value"] in current_values]
    
    new_options = []
    if search_value and len(search_value.strip()) >= 2:
        new_options = search_hpo_terms(search_value)
    
    all_options = selected_options.copy()
    
    existing_values = [opt["value"] for opt in selected_options]
    for opt in new_options:
        if opt["value"] not in existing_values:
            all_options.append(opt)
    
    return all_options

# =============================================================================
# NOUVEAUX CALLBACKS POUR LES SUGGESTIONS HPO SIMPLIFIÉES
# =============================================================================

"""
Callback amélioré pour les suggestions HPO dans main.py
Remplace le callback existant update_horizontal_hpo_suggestions
"""

@app.callback(
    [Output("smart-hpo-suggestions-container", "children"),
     Output("smart-hpo-suggestions-container", "style"),
     Output("hpo-debug-info-store", "data")],  # Nouveau store pour debug
    [Input("dropdown-uk", "value"),
     Input("dropdown-au", "value"),
     Input("dropdown-internal", "value"),
     Input("rejected-hpo-store", "data"),
     Input("suggestion-counter-store", "data")],
    [State("hpo-search-dropdown", "value")],
    prevent_initial_call=True
)
def update_horizontal_hpo_suggestions_enhanced(uk_ids, au_ids, internal_ids, rejected_hpo_terms, 
                                             counter, current_hpo_values):
    
    # Style de container fixe
    fixed_container_style = {
        "height": "130px",
        "borderRadius": "10px",
        "padding": "10px",
        "display": "flex",
        "flexDirection": "row",
        "gap": "8px",
        "alignItems": "stretch"
    }
    
    # Initialiser les données de debug
    debug_data = {
        "panel_names": [],
        "keywords": [],
        "suggestions": [],
        "processing_time": 0,
        "errors": []
    }
    
    start_time = time.time()
    
    # Vérifier si des panels sont sélectionnés
    if not any([uk_ids, au_ids, internal_ids]):
        return ([
            html.Div([
                DashIconify(icon="mdi:information", width=16, className="me-2", style={"color": "#6c757d"}),
                "Select panels to see intelligent HPO suggestions"
            ], className="text-muted text-center", 
               style={
                   "fontSize": "11px", 
                   "fontStyle": "italic", 
                   "padding": "10px",
                   "display": "flex",
                   "alignItems": "center",
                   "justifyContent": "center",
                   "width": "100%",
                   "height": "100%"
               })
        ], {
            **fixed_container_style,
            "border": "2px dashed rgba(0, 188, 212, 0.3)",
            "backgroundColor": "rgba(248, 249, 250, 0.5)",
            "justifyContent": "center"
        }, debug_data)
    
    try:
        # Étape 1: Récupérer les noms des panels
        panel_names = get_panel_names_from_selections(
            uk_ids, au_ids, internal_ids, 
            panels_uk_df, panels_au_df, internal_panels
        )
        debug_data["panel_names"] = panel_names
        
        logger.info(f"🏥 Processing {len(panel_names)} panel names: {panel_names}")
        
        if not panel_names:
            debug_data["errors"].append("No panel names found")
            return ([
                html.Div([
                    DashIconify(icon="mdi:alert-circle", width=16, className="me-2", style={"color": "#ffc107"}),
                    "No panel names found - check panel selections"
                ], className="text-warning text-center", 
                   style={
                       "fontSize": "11px", 
                       "fontStyle": "italic", 
                       "padding": "10px",
                       "display": "flex",
                       "alignItems": "center",
                       "justifyContent": "center",
                       "width": "100%",
                       "height": "100%"
                   })
            ], {
                **fixed_container_style,
                "border": "2px dashed rgba(255, 193, 7, 0.3)",
                "backgroundColor": "rgba(255, 248, 225, 0.5)",
                "justifyContent": "center"
            }, debug_data)
        
        # Étape 2: Extraire les mots-clés médicaux (version améliorée)
        keywords = extract_keywords_from_panel_names(panel_names)
        debug_data["keywords"] = keywords
        
        logger.info(f"🔑 Extracted keywords: {keywords}")
        
        if not keywords:
            debug_data["errors"].append("No relevant keywords extracted")
            return ([
                html.Div([
                    DashIconify(icon="mdi:magnify", width=16, className="me-2", style={"color": "#6c757d"}),
                    "No relevant medical keywords found in panel names"
                ], className="text-muted text-center", 
                   style={
                       "fontSize": "11px", 
                       "fontStyle": "italic", 
                       "padding": "10px",
                       "display": "flex",
                       "alignItems": "center",
                       "justifyContent": "center",
                       "width": "100%",
                       "height": "100%"
                   })
            ], {
                **fixed_container_style,
                "border": "2px dashed rgba(0, 188, 212, 0.3)",
                "backgroundColor": "rgba(248, 249, 250, 0.5)",
                "justifyContent": "center"
            }, debug_data)
        
        # Étape 3: Rechercher les termes HPO (version améliorée)
        suggested_terms = search_hpo_terms_by_keywords(keywords, max_per_keyword=4)
        debug_data["suggestions"] = suggested_terms
        
        logger.info(f"🎯 Found {len(suggested_terms)} HPO suggestions")
        
        # Étape 4: Filtrer les termes rejetés et déjà sélectionnés
        rejected_hpo_terms = rejected_hpo_terms or []
        current_hpo_values = current_hpo_values or []
        
        filtered_suggestions = []
        for term in suggested_terms:
            if (term["value"] not in rejected_hpo_terms and 
                term["value"] not in current_hpo_values):
                filtered_suggestions.append(term)
        
        logger.info(f"✅ {len(filtered_suggestions)} suggestions after filtering")
        
        # Étape 5: Gérer le cas où toutes les suggestions ont été traitées
        if not filtered_suggestions:
            return ([
                html.Div([
                    html.Div([
                        DashIconify(icon="mdi:check-circle", width=16, className="me-2", style={"color": "#28a745"}),
                        "All HPO suggestions reviewed!"
                    ], style={"marginBottom": "8px", "fontSize": "11px", "display": "flex", "alignItems": "center"}),
                    html.Div([
                        dbc.Button(
                            [DashIconify(icon="mdi:refresh", width=12, className="me-1"), "Get new suggestions"],
                            id="reset-hpo-suggestions-btn",
                            color="outline-primary",
                            size="sm",
                            style={"fontSize": "9px", "borderRadius": "4px", "padding": "3px 8px"},
                            n_clicks=0
                        )
                    ], style={"textAlign": "center"})
                ], className="text-success", 
                   style={
                       "fontSize": "10px", 
                       "padding": "10px",
                       "display": "flex",
                       "flexDirection": "column",
                       "alignItems": "center",
                       "justifyContent": "center",
                       "width": "100%",
                       "height": "100%"
                   })
            ], {
                **fixed_container_style,
                "border": "2px solid rgba(40, 167, 69, 0.3)",
                "backgroundColor": "rgba(212, 237, 218, 0.5)",
                "justifyContent": "center"
            }, debug_data)
        
        # Étape 6: Créer les cartes de suggestion (max 3)
        top_suggestions = filtered_suggestions[:3]
        total_available = len(filtered_suggestions)
        
        suggestion_cards = []
        for i, suggestion in enumerate(top_suggestions):
            # Calculer un score de confiance basé sur la source et la pertinence
            confidence_score = suggestion.get('relevance', 5)
            
            try:
                card = create_enhanced_hpo_suggestion_card(
                    {
                        "id": suggestion["value"],
                        "name": suggestion["label"].split(" (")[0]  # Extraire le nom sans l'ID
                    },
                    suggestion["keyword"],
                    i + 1,
                    min(3, total_available),
                    confidence_score
                )
                
                # Ajouter une classe CSS basée sur le score de confiance
                if confidence_score >= 8:
                    card.className += " confidence-high"
                elif confidence_score >= 5:
                    card.className += " confidence-medium"
                else:
                    card.className += " confidence-low"
                
                # Ajouter l'animation d'entrée
                card.className += " hpo-suggestion-enter"
                
                suggestion_cards.append(card)
                
            except Exception as e:
                logger.error(f"Error creating suggestion card for {suggestion['value']}: {e}")
                debug_data["errors"].append(f"Card creation error: {str(e)}")
                continue
        
        # Si aucune carte n'a pu être créée
        if not suggestion_cards:
            debug_data["errors"].append("No suggestion cards could be created")
            return ([
                html.Div([
                    DashIconify(icon="mdi:alert-circle", width=16, className="me-2", style={"color": "#dc3545"}),
                    "Error creating suggestion cards"
                ], className="text-danger text-center", 
                   style={
                       "fontSize": "11px", 
                       "fontStyle": "italic", 
                       "padding": "10px",
                       "display": "flex",
                       "alignItems": "center",
                       "justifyContent": "center",
                       "width": "100%",
                       "height": "100%"
                   })
            ], {
                **fixed_container_style,
                "border": "2px dashed rgba(220, 53, 69, 0.3)",
                "backgroundColor": "rgba(248, 215, 218, 0.5)",
                "justifyContent": "center"
            }, debug_data)
        
        # Ajouter un indicateur de progression si il y a plus de suggestions disponibles
        if total_available > 3:
            progress_indicator = html.Div([
                html.Small(f"+{total_available - 3} more available", 
                          style={"fontSize": "9px", "color": "#6c757d", "fontStyle": "italic"})
            ], style={
                "position": "absolute",
                "bottom": "2px",
                "right": "5px",
                "zIndex": "10"
            })
            suggestion_cards.append(progress_indicator)
        
        # Calculer le temps de traitement
        debug_data["processing_time"] = round(time.time() - start_time, 3)
        logger.info(f"⏱️ HPO processing completed in {debug_data['processing_time']}s")
        
        return (suggestion_cards, fixed_container_style, debug_data)
        
    except Exception as e:
        error_msg = f"Unexpected error in HPO suggestions: {str(e)}"
        logger.error(error_msg)
        debug_data["errors"].append(error_msg)
        debug_data["processing_time"] = round(time.time() - start_time, 3)
        
        return ([
            html.Div([
                DashIconify(icon="mdi:alert-circle", width=16, className="me-2", style={"color": "#dc3545"}),
                "Error loading HPO suggestions"
            ], className="text-danger text-center", 
               style={
                   "fontSize": "11px", 
                   "fontStyle": "italic", 
                   "padding": "10px",
                   "display": "flex",
                   "alignItems": "center",
                   "justifyContent": "center",
                   "width": "100%",
                   "height": "100%"
               })
        ], {
            **fixed_container_style,
            "border": "2px dashed rgba(220, 53, 69, 0.3)",
            "backgroundColor": "rgba(248, 215, 218, 0.5)",
            "justifyContent": "center"
        }, debug_data)

# Callback optionnel pour afficher les informations de debug (en mode développement)
@app.callback(
    Output("hpo-debug-collapse", "is_open"),
    Output("hpo-debug-collapse", "children"),
    Input("hpo-debug-toggle", "n_clicks"),
    State("hpo-debug-info-store", "data"),
    prevent_initial_call=True
)
def toggle_hpo_debug_info(n_clicks, debug_data):
    """
    Toggle pour afficher/masquer les informations de debug HPO
    """
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    
    if not debug_data:
        debug_content = html.P("No debug data available", className="text-muted")
    else:
        debug_content = create_hpo_debug_info(
            debug_data.get("panel_names", []),
            debug_data.get("keywords", []),
            debug_data.get("suggestions", [])
        )
    
    return not (n_clicks % 2 == 0), debug_content

# Callback pour la validation et l'amélioration continue
@app.callback(
    Output("hpo-quality-feedback", "children"),
    Input("validate-hpo-suggestions", "n_clicks"),
    State("hpo-debug-info-store", "data"),
    prevent_initial_call=True
)
def validate_hpo_quality(n_clicks, debug_data):
    """
    Validation de la qualité des suggestions HPO pour amélioration continue
    """
    if not n_clicks or not debug_data:
        raise dash.exceptions.PreventUpdate
    
    panel_names = debug_data.get("panel_names", [])
    suggestions = debug_data.get("suggestions", [])
    
    validation_result = validate_hpo_suggestions(panel_names, suggestions)
    
    # Créer un indicateur visuel de la qualité
    quality_percentage = validation_result.get("percentage", 0)
    
    if quality_percentage >= 70:
        alert_color = "success"
        icon = "mdi:check-circle"
        message = f"Excellent quality ({quality_percentage:.1f}%)"
    elif quality_percentage >= 40:
        alert_color = "warning" 
        icon = "mdi:alert-circle"
        message = f"Good quality ({quality_percentage:.1f}%)"
    else:
        alert_color = "danger"
        icon = "mdi:close-circle"
        message = f"Needs improvement ({quality_percentage:.1f}%)"
    
    return dbc.Alert([
        DashIconify(icon=icon, width=16, className="me-2"),
        html.Strong(message),
        html.Br(),
        html.Small(f"Score: {validation_result['score']}/{validation_result['max_possible']}")
    ], color=alert_color, className="mt-2")

@app.callback(
    [Output("hpo-search-dropdown", "value", allow_duplicate=True),
     Output("hpo-search-dropdown", "options", allow_duplicate=True),
     Output("suggestion-counter-store", "data", allow_duplicate=True)],
    Input({"type": "horizontal-hpo-keep-btn", "hpo_id": ALL, "keyword": ALL}, "n_clicks"),
    [State("hpo-search-dropdown", "value"),
     State("hpo-search-dropdown", "options"),
     State("suggestion-counter-store", "data")],
    prevent_initial_call=True
)
def handle_horizontal_hpo_keep(n_clicks_list, current_hpo_values, current_hpo_options, counter):
    """Handle horizontal HPO suggestion acceptance - add to HPO dropdown and trigger new suggestions"""
    ctx = callback_context
    
    if not ctx.triggered or all(n == 0 for n in n_clicks_list):
        raise dash.exceptions.PreventUpdate
    
    # Find which keep button was clicked
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    hpo_data = json.loads(button_id)
    hpo_id = hpo_data["hpo_id"]
    
    # Initialize current values and options if None
    current_values = current_hpo_values or []
    current_options = current_hpo_options or []
    
    # Check if HPO term is already selected
    if hpo_id in current_values:
        return current_values, current_options, counter + 1
    
    # Check if HPO term option already exists
    existing_option_values = [opt["value"] for opt in current_options]
    if hpo_id not in existing_option_values:
        # Fetch the HPO term details and add it to options
        try:
            hpo_details = fetch_hpo_term_details_cached(hpo_id)
            new_option = {
                "label": f"{hpo_details['name']} ({hpo_details['id']})",
                "value": hpo_details['id']
            }
            current_options.append(new_option)
        except Exception as e:
            logger.error(f"Error fetching details for HPO term {hpo_id}: {e}")
            # Add basic option even if details fetch fails
            current_options.append({
                "label": f"{hpo_id} (Details unavailable)",
                "value": hpo_id
            })
    
    # Add the HPO term to selected values
    new_values = current_values + [hpo_id]
    
    return new_values, current_options, counter + 1

@app.callback(
    [Output("rejected-hpo-store", "data", allow_duplicate=True),
     Output("suggestion-counter-store", "data", allow_duplicate=True)],
    Input({"type": "horizontal-hpo-skip-btn", "hpo_id": ALL, "keyword": ALL}, "n_clicks"),
    [State("rejected-hpo-store", "data"),
     State("suggestion-counter-store", "data")],
    prevent_initial_call=True
)
def handle_horizontal_hpo_skip(n_clicks_list, rejected_hpo_terms, counter):
    """Handle horizontal HPO suggestion rejection - add to rejected list and trigger new suggestions"""
    ctx = callback_context
    
    if not ctx.triggered or all(n == 0 for n in n_clicks_list):
        raise dash.exceptions.PreventUpdate
    
    # Find which skip button was clicked
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    hpo_data = json.loads(button_id)
    hpo_id = hpo_data["hpo_id"]
    
    # Add to rejected list
    rejected_hpo_terms = rejected_hpo_terms or []
    if hpo_id not in rejected_hpo_terms:
        rejected_hpo_terms.append(hpo_id)
    
    return rejected_hpo_terms, counter + 1

def handle_compact_hpo_keep(n_clicks_list, current_hpo_values, current_hpo_options, counter):
    """Handle compact HPO suggestion acceptance - add to HPO dropdown and trigger new suggestions"""
    ctx = callback_context
    
    if not ctx.triggered or all(n == 0 for n in n_clicks_list):
        raise dash.exceptions.PreventUpdate
    
    # Find which keep button was clicked
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    hpo_data = json.loads(button_id)
    hpo_id = hpo_data["hpo_id"]
    
    # Initialize current values and options if None
    current_values = current_hpo_values or []
    current_options = current_hpo_options or []
    
    # Check if HPO term is already selected
    if hpo_id in current_values:
        return current_values, current_options, counter + 1
    
    # Check if HPO term option already exists
    existing_option_values = [opt["value"] for opt in current_options]
    if hpo_id not in existing_option_values:
        # Fetch the HPO term details and add it to options
        try:
            hpo_details = fetch_hpo_term_details_cached(hpo_id)
            new_option = {
                "label": f"{hpo_details['name']} ({hpo_details['id']})",
                "value": hpo_details['id']
            }
            current_options.append(new_option)
        except Exception as e:
            logger.error(f"Error fetching details for HPO term {hpo_id}: {e}")
            # Add basic option even if details fetch fails
            current_options.append({
                "label": f"{hpo_id} (Details unavailable)",
                "value": hpo_id
            })
    
    # Add the HPO term to selected values
    new_values = current_values + [hpo_id]
    
    return new_values, current_options, counter + 1

@app.callback(
    [Output("rejected-hpo-store", "data", allow_duplicate=True),
     Output("suggestion-counter-store", "data", allow_duplicate=True)],
    Input({"type": "compact-hpo-skip-btn", "hpo_id": ALL, "keyword": ALL}, "n_clicks"),
    [State("rejected-hpo-store", "data"),
     State("suggestion-counter-store", "data")],
    prevent_initial_call=True
)
def handle_compact_hpo_skip(n_clicks_list, rejected_hpo_terms, counter):
    """Handle compact HPO suggestion rejection - add to rejected list and trigger new suggestions"""
    ctx = callback_context
    
    if not ctx.triggered or all(n == 0 for n in n_clicks_list):
        raise dash.exceptions.PreventUpdate
    
    # Find which skip button was clicked
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    hpo_data = json.loads(button_id)
    hpo_id = hpo_data["hpo_id"]
    
    # Add to rejected list
    rejected_hpo_terms = rejected_hpo_terms or []
    if hpo_id not in rejected_hpo_terms:
        rejected_hpo_terms.append(hpo_id)
    
    return rejected_hpo_terms, counter + 1
    
    # Check if HPO term is already selected
    if hpo_id in current_values:
        return current_values, current_options, counter + 1
    
    # Check if HPO term option already exists
    existing_option_values = [opt["value"] for opt in current_options]
    if hpo_id not in existing_option_values:
        # Fetch the HPO term details and add it to options
        try:
            hpo_details = fetch_hpo_term_details_cached(hpo_id)
            new_option = {
                "label": f"{hpo_details['name']} ({hpo_details['id']})",
                "value": hpo_details['id']
            }
            current_options.append(new_option)
        except Exception as e:
            logger.error(f"Error fetching details for HPO term {hpo_id}: {e}")
            # Add basic option even if details fetch fails
            current_options.append({
                "label": f"{hpo_id} (Details unavailable)",
                "value": hpo_id
            })
    
    # Add the HPO term to selected values
    new_values = current_values + [hpo_id]
    
    return new_values, current_options, counter + 1

@app.callback(
    [Output("rejected-hpo-store", "data", allow_duplicate=True),
     Output("suggestion-counter-store", "data", allow_duplicate=True)],
    Input({"type": "smart-hpo-skip-btn", "hpo_id": ALL, "keyword": ALL}, "n_clicks"),
    [State("rejected-hpo-store", "data"),
     State("suggestion-counter-store", "data")],
    prevent_initial_call=True
)
def handle_smart_hpo_skip(n_clicks_list, rejected_hpo_terms, counter):
    """Handle smart HPO suggestion rejection - add to rejected list and trigger new suggestion"""
    ctx = callback_context
    
    if not ctx.triggered or all(n == 0 for n in n_clicks_list):
        raise dash.exceptions.PreventUpdate
    
    # Find which skip button was clicked
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    hpo_data = json.loads(button_id)
    hpo_id = hpo_data["hpo_id"]
    
    # Add to rejected list
    rejected_hpo_terms = rejected_hpo_terms or []
    if hpo_id not in rejected_hpo_terms:
        rejected_hpo_terms.append(hpo_id)
    
    return rejected_hpo_terms, counter + 1

@app.callback(
    [Output("rejected-hpo-store", "data", allow_duplicate=True),
     Output("suggestion-counter-store", "data", allow_duplicate=True)],
    Input("reset-hpo-suggestions-btn", "n_clicks"),
    prevent_initial_call=True
)
def reset_smart_hpo_suggestions(n_clicks):
    """Reset smart HPO suggestions - clear rejected list and get new suggestions"""
    if n_clicks:
        return [], 0
    raise dash.exceptions.PreventUpdate
	
# =============================================================================
# CALLBACKS - SPINNER MANAGEMENT (OPTIMISÉ PYTHON PUR)
# =============================================================================

@app.callback(
    Output("fullscreen-spinner", "className", allow_duplicate=True),
    Input("load-genes-btn", "n_clicks"),
    prevent_initial_call=True
)
def show_spinner_immediately(n_clicks):
    """Affiche le spinner immédiatement quand on clique sur Build Panel"""
    if n_clicks:
        return "fullscreen-spinner-overlay"
    return "fullscreen-spinner-overlay hide"

@app.callback(
    Output("fullscreen-spinner", "className", allow_duplicate=True),
    Input("gene-table-output", "children"),
    prevent_initial_call=True
)
def hide_spinner_when_done(gene_table_content):
    """Masque le spinner quand les résultats sont affichés"""
    if gene_table_content and gene_table_content != "":
        return "fullscreen-spinner-overlay hide"
    return dash.no_update

# =============================================================================
# CALLBACKS - UI MANAGEMENT (ORIGINAL - IMPORT REMOVED)
# =============================================================================

@app.callback(
    Output("generate-code-section", "style"),
    Output("venn-hpo-row", "style"),
    Input("load-genes-btn", "n_clicks"),
    Input("reset-btn", "n_clicks"),
    prevent_initial_call=True
)
def toggle_code_visibility(n_build, n_reset):
    ctx = callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if triggered_id == "load-genes-btn":
        return {"display": "block"}, {"display": "block", "marginBottom": "20px"}
    elif triggered_id == "reset-btn":
        return {"display": "none"}, {"display": "none"}
    return dash.no_update, dash.no_update

# =============================================================================
# CALLBACKS - RESET (AVEC LES NOUVEAUX STORES)
# =============================================================================

@app.callback(
    [Output("dropdown-uk", "value"),
     Output("dropdown-au", "value"),
     Output("dropdown-internal", "value"),
     Output("confidence-filter", "value"),
     Output("manual-genes", "value"),
     Output("hpo-search-dropdown", "value"),
     Output("hpo-search-dropdown", "options"),
     Output("gene-table-output", "children"),
     Output("venn-container", "children"),
     Output("hpo-terms-table-container", "children"),
     Output("gene-list-store", "data"),
     Output("panel-summary-output", "value"),
     Output("rejected-hpo-store", "data", allow_duplicate=True),
     Output("suggestion-counter-store", "data", allow_duplicate=True)],
    Input("reset-btn", "n_clicks"),
    prevent_initial_call=True
)
def handle_reset_with_hpo_stores(n_reset):
    if not n_reset:
        raise dash.exceptions.PreventUpdate

    return None, None, None, [3, 2], "", [], [], "", "", "", [], "", [], 0

# =============================================================================
# CALLBACKS - MAIN PANEL PROCESSING (ORIGINAL WITH GENE SEARCH + SPINNER)
# =============================================================================

@app.callback(
    [Output("gene-table-output", "children", allow_duplicate=True),
     Output("venn-container", "children", allow_duplicate=True),
     Output("hpo-terms-table-container", "children", allow_duplicate=True),
     Output("gene-list-store", "data", allow_duplicate=True),
     Output("hpo-search-dropdown", "value", allow_duplicate=True),
     Output("hpo-search-dropdown", "options", allow_duplicate=True),
     Output("panel-summary-output", "value", allow_duplicate=True),
     Output("gene-data-store", "data", allow_duplicate=True)],
    Input("load-genes-btn", "n_clicks"),
    State("dropdown-uk", "value"),
    State("dropdown-au", "value"),
    State("dropdown-internal", "value"),
    State("confidence-filter", "value"),
    State("manual-genes", "value"),
    State("hpo-search-dropdown", "value"),
    State("hpo-search-dropdown", "options"),
    prevent_initial_call=True
)
def display_panel_genes_optimized(n_clicks, selected_uk_ids, selected_au_ids, 
                                selected_internal_ids, selected_confidences, 
                                manual_genes, selected_hpo_terms, current_hpo_options):
    """OPTIMIZED version of the main callback with ORIGINAL FUNCTIONALITY"""
    if not n_clicks:
        return "", "", "", [], [], [], "", {}

    start_time = time.time()
    print(f"Building panel with {len(selected_uk_ids or [])} UK, {len(selected_au_ids or [])} AU, {len(selected_internal_ids or [])} internal panels...")
    
    all_hpo_terms = selected_hpo_terms or []
    updated_hpo_options = current_hpo_options or []

    genes_combined = []
    gene_sets = {}
    manual_genes_list = []
    panel_dataframes = {} 
    panel_names = {}      
    panel_versions = {}    

    # PARALLEL FETCHING - This is the biggest performance improvement
    if selected_uk_ids or selected_au_ids:
        panel_results = fetch_panels_parallel(selected_uk_ids, selected_au_ids)
        
        # Process results from parallel fetching
        for result_key, (df, panel_info) in panel_results.items():
            if df.empty:
                continue
                
            source, pid_str = result_key.split('_', 1)
            pid = int(pid_str)
            
            # Fast confidence cleaning
            df = clean_confidence_level_fast(df)
            panel_dataframes[result_key] = df.copy()
            
            # Filter by confidence
            df_filtered = df[df["confidence_level"].isin(selected_confidences)].copy()
            
            # Ensure required columns exist with default values
            required_cols = ["gene_symbol", "confidence_level", "omim_id", "hgnc_id", "entity_type", "biotype", "mode_of_inheritance"]
            for col in required_cols:
                if col not in df_filtered.columns:
                    df_filtered[col] = "" if col != "confidence_level" else 0
            
            genes_combined.append(df_filtered[required_cols])
            gene_sets[result_key] = set(df_filtered["gene_symbol"])
            
            # Panel names
            panel_name = f"{source} Panel {pid}"
            panel_version = None
            if panel_info:
                if 'name' in panel_info:
                    panel_name = panel_info['name']
                if 'version' in panel_info:
                    panel_version = panel_info['version']
            
            panel_names[result_key] = panel_name
            panel_versions[result_key] = panel_version

    # Process internal panels (optimized)
    if selected_internal_ids:
        for pid in selected_internal_ids:
            try:
                panel_df = internal_df[internal_df["panel_id"] == pid].copy()
                
                # Fast confidence cleaning
                panel_df = clean_confidence_level_fast(panel_df)
                
                # Add missing columns for internal panels with default values
                panel_df["omim_id"] = ""
                panel_df["hgnc_id"] = ""
                panel_df["entity_type"] = "gene"
                panel_df["biotype"] = "unknown"
                panel_df["mode_of_inheritance"] = "unknown"
                
                panel_dataframes[f"INT-{pid}"] = panel_df.copy()
                
                panel_df_filtered = panel_df[panel_df["confidence_level"].isin(selected_confidences)].copy()
                required_cols = ["gene_symbol", "confidence_level", "omim_id", "hgnc_id", "entity_type", "biotype", "mode_of_inheritance"]
                genes_combined.append(panel_df_filtered[required_cols])
                gene_sets[f"INT-{pid}"] = set(panel_df_filtered["gene_symbol"])
                
                panel_name = next((row['panel_name'] for _, row in internal_panels.iterrows() if row['panel_id'] == pid), f"Internal Panel {pid}")
                panel_names[f"INT-{pid}"] = panel_name
                panel_version = next((row['version'] for _, row in internal_panels.iterrows() if row['panel_id'] == pid), None)
                panel_versions[f"INT-{pid}"] = panel_version
                
            except Exception as e:
                print(f"Error processing internal panel {pid}: {e}")
                continue

    # Handle manual genes
    if manual_genes:
        manual_genes_list = [g.strip() for g in manual_genes.strip().splitlines() if g.strip()]
        if manual_genes_list:  
            manual_df = pd.DataFrame({
                "gene_symbol": manual_genes_list, 
                "confidence_level": [0] * len(manual_genes_list),
                "omim_id": [""] * len(manual_genes_list),
                "hgnc_id": [""] * len(manual_genes_list),
                "entity_type": ["gene"] * len(manual_genes_list),
                "biotype": ["manual"] * len(manual_genes_list),
                "mode_of_inheritance": ["manual"] * len(manual_genes_list)
            })
            genes_combined.append(manual_df)
            gene_sets["Manual"] = set(manual_genes_list)
            panel_dataframes["Manual"] = manual_df
            panel_names["Manual"] = "Manual Gene List"
            panel_versions["Manual"] = None

    if not genes_combined:
        return "No gene found.", "", "", [], all_hpo_terms, updated_hpo_options, "", {}

    # FAST GENE PROCESSING
    df_all = pd.concat(genes_combined, ignore_index=True)
    df_all = df_all.copy()
    
    # Remove any rows with completely missing gene symbols
    df_all = df_all[df_all["gene_symbol"].notna() & (df_all["gene_symbol"] != "")]
    
    if df_all.empty:
        return "No valid genes found.", "", "", [], all_hpo_terms, updated_hpo_options, "", {}
    
    # Fast deduplication
    df_unique = deduplicate_genes_fast(df_all)
    
    print(f"Data processing completed in {time.time() - start_time:.2f} seconds")
    
    # Rename columns for display
    df_unique = df_unique.rename(columns={
        "gene_symbol": "Gene Symbol",
        "confidence_level": "Confidence",
        "omim_id": "OMIM ID",
        "hgnc_id": "HGNC ID", 
        "entity_type": "Type",
        "biotype": "Biotype",
        "mode_of_inheritance": "Mode of Inheritance"
    })

    # ORIGINAL SUMMARY TABLE WITH GENE SEARCH FUNCTIONALITY - NOW WRAPPED IN GLASS CARD
    total_genes = pd.DataFrame({"Number of genes in panel": [df_unique.shape[0]]})
    summary = df_unique.groupby("Confidence").size().reset_index(name="Number of genes")
    summary_table = dbc.Row([
        dbc.Col(dash_table.DataTable(columns=[{"name": col, "id": col} for col in total_genes.columns], data=total_genes.to_dict("records"), style_cell={"textAlign": "left"}, style_table={"marginBottom": "20px", "width": "100%"}), width=4),
        dbc.Col(dash_table.DataTable(columns=[{"name": col, "id": col} for col in ["Confidence", "Number of genes"]], data=summary.to_dict("records"), style_cell={"textAlign": "left"}, style_table={"width": "100%"}), width=8)
    ])

    # Visualization logic (Venn diagrams/UpSet plots) - ORIGINAL
    venn_component = html.Div()
    all_sets = {k: v for k, v in gene_sets.items() if len(v) > 0}
    total_sets = len(all_sets)

    if total_sets == 1:
        single_panel_id = next(iter(all_sets.keys()))
        panel_df = panel_dataframes[single_panel_id]
        panel_name = panel_names[single_panel_id]
        panel_version = panel_versions[single_panel_id]
        venn_component = generate_panel_pie_chart(panel_df, panel_name, panel_version)
    elif 2 <= total_sets <= 3:
        venn_sets = all_sets
        set_items = list(venn_sets.items())
        labels = []
        for panel_key, _ in set_items:
            if panel_key == "Manual":
                labels.append("Manual")
            elif panel_key.startswith("UK_"):
                panel_id = panel_key.replace("UK_", "")
                labels.append(f"UK_{panel_id}")
            elif panel_key.startswith("AUS_"):
                panel_id = panel_key.replace("AUS_", "")
                labels.append(f"AUS_{panel_id}")
            elif panel_key.startswith("INT-"):
                panel_id = panel_key.replace("INT-", "")
                labels.append(f"INT_{panel_id}")
            else:
                labels.append(panel_key)
        
        sets = [s[1] for s in set_items]
        fig, ax = plt.subplots(figsize=(9, 5))
        try:
            if len(sets) == 2:
                venn2(sets, set_labels=labels)
            elif len(sets) == 3:
                venn3(sets, set_labels=labels)
            
            buf = io.BytesIO()
            plt.tight_layout()
            plt.savefig(buf, format="png", bbox_inches='tight', dpi=100)
            plt.close(fig)
            data = base64.b64encode(buf.getbuffer()).decode("ascii")
            
            venn_component = html.Div([
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
                "alignItems": "center",
                "justifyContent": "center"
            })
        except Exception as e:
            venn_component = html.Div(f"Could not generate Venn diagram: {str(e)}", style={
                "textAlign": "center", 
                "fontStyle": "italic", 
                "color": "#666",
                "height": "580px",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center"
            })
    elif total_sets >= 4:
        upset_sets = all_sets
        try:
            fig = create_upset_plot(upset_sets, panel_names)
            if fig:
                buf = io.BytesIO()
                plt.tight_layout()
                plt.savefig(buf, format="png", bbox_inches='tight', dpi=100)
                plt.close(fig)
                data = base64.b64encode(buf.getbuffer()).decode("ascii")
                
                venn_component = html.Div([
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
            else:
                venn_component = html.Div("Could not generate UpSet plot.", style={
                    "textAlign": "center", 
                    "fontStyle": "italic", 
                    "color": "#666",
                    "height": "580px",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center"
                })
        except Exception as e:
            venn_component = html.Div(f"Error generating UpSet plot: {str(e)}", style={
                "textAlign": "center", 
                "fontStyle": "italic", 
                "color": "#666",
                "height": "580px",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center"
            })
    else:
        venn_component = html.Div("No panels selected.", style={
            "textAlign": "center", 
            "fontStyle": "italic", 
            "color": "#666",
            "height": "580px",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center"
        })

    # OPTIMIZED HPO PROCESSING - Use parallel fetching
    hpo_details = []
    if all_hpo_terms:
        hpo_details = fetch_hpo_terms_parallel(all_hpo_terms)

    hpo_table_component = html.Div()
    if hpo_details:
        hpo_table_component = create_hpo_terms_table(hpo_details)

    confidence_levels_present = sorted(df_unique["Confidence"].unique(), reverse=True)

    # Create buttons with proper IDs and confidence-based colors
    buttons = []
    for level in confidence_levels_present:
        # Set button color based on confidence level
        if level == 3:
            button_color = "success"  # Green
        elif level == 2:
            button_color = "warning"  # Amber/Orange
        elif level == 1:
            button_color = "danger"   # Red
        else:
            button_color = "secondary"  # Default
            
        button = dbc.Button(
            f"Gene list (confidence {level})", 
            id={"type": "btn-confidence", "level": str(level)}, 
            color=button_color, 
            className="me-1 mb-1", 
            n_clicks=0,
            size="sm"
        )
        buttons.append(button)

    # Add manual genes button if present
    if manual_genes_list:
        manual_button = dbc.Button(
            "Manual Genes", 
            id={"type": "btn-confidence", "level": "Manual"}, 
            color="info",  # Light blue for manual
            className="me-1 mb-1", 
            n_clicks=0,
            size="sm"
        )
        buttons.append(manual_button)

    # Define enhanced table columns
    table_columns = [
        {"name": "Gene Symbol", "id": "Gene Symbol", "type": "text"},
        {"name": "OMIM ID", "id": "OMIM ID", "type": "text", "presentation": "markdown"},
        {"name": "HGNC ID", "id": "HGNC ID", "type": "text", "presentation": "markdown"},
        {"name": "Type", "id": "Type", "type": "text"},
        {"name": "Biotype", "id": "Biotype", "type": "text"},
        {"name": "Mode of Inheritance", "id": "Mode of Inheritance", "type": "text"},
        {"name": "Confidence", "id": "Confidence", "type": "numeric"}
    ]

    tables_by_level = {
        str(level): dash_table.DataTable(
            columns=table_columns,
            data=df_unique[df_unique["Confidence"] == level].to_dict("records"),
            style_table={"overflowX": "auto", "maxHeight": "400px", "overflowY": "auto"},
            style_cell={
                "textAlign": "left", 
                "padding": "6px",
                "fontSize": "11px",
                "fontFamily": "Arial, sans-serif",
                "whiteSpace": "normal",
                "height": "auto"
            },
            style_header={
                "fontWeight": "bold",
                "backgroundColor": "#f8f9fa",
                "border": "1px solid #ddd",
                "fontSize": "12px"
            },
            style_data_conditional=[
                {"if": {"filter_query": "{Confidence} = 3", "column_id": "Confidence"}, "backgroundColor": "#d4edda"},
                {"if": {"filter_query": "{Confidence} = 2", "column_id": "Confidence"}, "backgroundColor": "#fff3cd"},
                {"if": {"filter_query": "{Confidence} = 1", "column_id": "Confidence"}, "backgroundColor": "#f8d7da"},
                {"if": {"filter_query": "{Confidence} = 0", "column_id": "Confidence"}, "backgroundColor": "#d1ecf1"},
            ],
            style_cell_conditional=[
                {"if": {"column_id": "Gene Symbol"}, "width": "100px", "minWidth": "100px"},
                {"if": {"column_id": "OMIM ID"}, "width": "150px", "minWidth": "150px"},
                {"if": {"column_id": "HGNC ID"}, "width": "110px", "minWidth": "110px"},
                {"if": {"column_id": "Type"}, "width": "70px", "minWidth": "70px"},
                {"if": {"column_id": "Biotype"}, "width": "110px", "minWidth": "110px"},
                {"if": {"column_id": "Mode of Inheritance"}, "width": "180px", "minWidth": "180px"},
                {"if": {"column_id": "Confidence"}, "width": "80px", "minWidth": "80px"},
            ],
            page_action="none",
            markdown_options={"link_target": "_blank"}
        )
        for level in confidence_levels_present
    }

    # Handle manual genes table
    if manual_genes_list:
        manual_table_data = []
        for gene in manual_genes_list:
            manual_table_data.append({
                "Gene Symbol": gene,
                "OMIM ID": "",
                "HGNC ID": "",
                "Type": "manual",
                "Biotype": "manual",
                "Mode of Inheritance": "manual",
                "Confidence": 0
            })
        
        tables_by_level["Manual"] = dash_table.DataTable(
            columns=table_columns,
            data=manual_table_data,
            style_table={"overflowX": "auto", "maxHeight": "400px", "overflowY": "auto"},
            style_cell={
                "textAlign": "left", 
                "padding": "6px",
                "fontSize": "11px",
                "fontFamily": "Arial, sans-serif",
                "whiteSpace": "normal",
                "height": "auto"
            },
            style_header={
                "fontWeight": "bold",
                "backgroundColor": "#f8f9fa",
                "border": "1px solid #ddd",
                "fontSize": "12px"
            },
            style_data_conditional=[
                {"if": {"filter_query": "{Confidence} = 0", "column_id": "Confidence"}, "backgroundColor": "#d1ecf1"}
            ],
            style_cell_conditional=[
                {"if": {"column_id": "Gene Symbol"}, "width": "100px", "minWidth": "100px"},
                {"if": {"column_id": "OMIM ID"}, "width": "150px", "minWidth": "150px"},
                {"if": {"column_id": "HGNC ID"}, "width": "110px", "minWidth": "110px"},
                {"if": {"column_id": "Type"}, "width": "70px", "minWidth": "70px"},
                {"if": {"column_id": "Biotype"}, "width": "110px", "minWidth": "110px"},
                {"if": {"column_id": "Mode of Inheritance"}, "width": "180px", "minWidth": "180px"},
                {"if": {"column_id": "Confidence"}, "width": "80px", "minWidth": "80px"},
            ],
            page_action="none",
            markdown_options={"link_target": "_blank"}
        )

    table_output = html.Div(id="table-per-confidence")

    # ORIGINAL SUMMARY LAYOUT WITH GENE SEARCH BAR - NOW WRAPPED IN GLASS CARD
    summary_layout = dbc.Card([
        dbc.CardBody([
            # Summary table first
            html.Div(summary_table, id="summary-table-content", style={"marginBottom": "20px"}),
            
            # GENE SEARCH BAR AND CONFIDENCE BUTTONS ROW
            dbc.Row([
                dbc.Col([
                    dbc.InputGroup([
                        dbc.Input(id="gene-check-input", type="text", placeholder="Search for a gene in custom panel...", className="form-control", debounce=True, n_submit=0),
                        dbc.Button("Search", id="gene-check-btn", color="secondary", n_clicks=0)
                    ])
                ], width=6),
                dbc.Col([
                    html.Div(id="gene-check-result", className="mt-2", style={"fontStyle": "italic"})
                ], width=3),
                dbc.Col([
                    # Gene list confidence buttons moved here
                    html.Div(buttons, id="confidence-buttons-container", style={"display": "flex", "flexWrap": "wrap", "gap": "5px"})
                ], width=3)
            ], style={"marginTop": "10px"})
        ], style={"padding": "1rem"})
    ], className="glass-card fade-in-up", style={"marginBottom": "20px"})

    print(f"Total processing time: {time.time() - start_time:.2f} seconds")

    return (html.Div([
            html.Div(summary_layout, className="mb-3"),
            # Only table output - buttons are now in the summary card
            html.Div(table_output, style={"marginBottom": "30px"})  # Added spacing
        ]), 
        venn_component, 
        hpo_table_component,  
        df_unique["Gene Symbol"].tolist(),
        all_hpo_terms,       
        updated_hpo_options,
        "",  # Clear panel summary
        tables_by_level)

# =============================================================================
# CALLBACKS - GENE SEARCH (KEEP ORIGINAL)
# =============================================================================

@app.callback(
    Output("gene-check-result", "children"),
    Output("gene-check-input", "value"),
    Input("gene-check-btn", "n_clicks"),
    Input("gene-check-input", "n_submit"),
    State("gene-check-input", "value"),
    State("gene-list-store", "data"),
    prevent_initial_call=True
)
def check_gene_in_panel(n_clicks, n_submit, gene_name, gene_list):
    if not gene_name or not gene_list:
        return "", ""
    
    if gene_name.upper() in [g.upper() for g in gene_list]:
        return f"Gene '{gene_name}' is present in the custom panel.", ""
    else:
        return f"Gene '{gene_name}' is NOT present in the custom panel.", ""

# =============================================================================
# CALLBACKS - TABLE INTERACTION (ORIGINAL)
# =============================================================================

@app.callback(
    Output("table-per-confidence", "children"),
    Input({"type": "btn-confidence", "level": ALL}, "n_clicks"),
    State("gene-data-store", "data"),
    prevent_initial_call=True
)
def update_table_by_confidence(btn_clicks, data):
    ctx = callback_context
    if not ctx.triggered:
        return ""
    
    # Check if any button was actually clicked (not just initialized)
    if all(n == 0 for n in btn_clicks):
        return ""
    
    triggered = ctx.triggered[0]["prop_id"].split(".")[0]
    triggered_dict = json.loads(triggered)
    level = triggered_dict["level"]
    
    return data.get(level, "")

# =============================================================================
# CALLBACKS - CODE GENERATION (ORIGINAL - FONCTION RENOMMÉE POUR ÉVITER CONFLIT)
# =============================================================================

@app.callback(
    Output("panel-summary-output", "value", allow_duplicate=True),
    Input("generate-code-btn", "n_clicks"),
    State("dropdown-uk", "value"),
    State("dropdown-au", "value"),
    State("dropdown-internal", "value"),
    State("confidence-filter", "value"),
    State("manual-genes", "value"),
    State("hpo-search-dropdown", "value"),
    prevent_initial_call=True
)
def create_panel_summary_callback(n_clicks, uk_ids, au_ids, internal_ids, confs, manual, hpo_terms):
    """RENOMMÉ POUR ÉVITER CONFLIT AVEC FONCTION UTILS"""
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
        
    manual_list = [g.strip() for g in manual.strip().splitlines() if g.strip()] if manual else []
    
    # Appeler la fonction du module utils avec le bon nom
    summary = generate_panel_summary(
        uk_ids or [], 
        au_ids or [], 
        internal_ids or [], 
        confs or [], 
        manual_list, 
        panels_uk_df, 
        panels_au_df, 
        internal_panels
    )
    
    return summary

# =============================================================================
# CALLBACKS - EXPORT (ORIGINAL)
# =============================================================================

@app.callback(
    Output("download-genes", "data"),
    Input("export-genes-btn", "n_clicks"),
    State("gene-list-store", "data"),
    State("dropdown-uk", "value"),
    State("dropdown-au", "value"),
    State("dropdown-internal", "value"),
    State("manual-genes", "value"),
    prevent_initial_call=True
)
def export_gene_list(n_clicks, gene_list, uk_ids, au_ids, internal_ids, manual_genes):
    if n_clicks and gene_list:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        
        panel_parts = []
        if uk_ids:
            panel_parts.append(f"UK{len(uk_ids)}")
        if au_ids:
            panel_parts.append(f"AU{len(au_ids)}")
        if internal_ids:
            panel_parts.append(f"INT{len(internal_ids)}")
        if manual_genes and manual_genes.strip():
            manual_count = len([g.strip() for g in manual_genes.strip().splitlines() if g.strip()])
            panel_parts.append(f"MAN{manual_count}")
        
        panel_desc = "_".join(panel_parts) if panel_parts else "Panel"
        filename = f"CustomPanel_{len(gene_list)}genes_{timestamp}.txt"
        
        content = "\n".join(sorted(gene_list))
        
        return dcc.send_string(content, filename)
    
    raise dash.exceptions.PreventUpdate

# =============================================================================
# CLIENTSIDE CALLBACKS FOR UX (ORIGINAL - KEEP CLIPBOARD FUNCTIONALITY)
# =============================================================================

app.clientside_callback(
    """
    function(panel_summary) {
        if (panel_summary && panel_summary.trim() !== '') {
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(panel_summary).then(function() {
                    console.log('Panel summary copied to clipboard successfully');
                    showCopyNotificationSummary('✅ Panel summary copied to clipboard!', 'success');
                }).catch(function(err) {
                    console.error('Failed to copy panel summary: ', err);
                    showCopyNotificationSummary('❌ Failed to copy panel summary', 'error');
                });
            } else {
                const textArea = document.createElement('textarea');
                textArea.value = panel_summary;
                textArea.style.position = 'fixed';
                textArea.style.left = '-999999px';
                textArea.style.top = '-999999px';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                try {
                    document.execCommand('copy');
                    console.log('Panel summary copied to clipboard successfully (fallback)');
                    showCopyNotificationSummary('✅ Panel summary copied to clipboard!', 'success');
                } catch (err) {
                    console.error('Failed to copy panel summary (fallback): ', err);
                    showCopyNotificationSummary('❌ Failed to copy panel summary', 'error');
                }
                document.body.removeChild(textArea);
            }
        }
        return window.dash_clientside.no_update;
    }
    
    function showCopyNotificationSummary(message, type) {
        const notification = document.getElementById('copy-notification-summary');
        if (notification) {
            notification.textContent = message;
            notification.style.color = type === 'success' ? '#28a745' : '#dc3545';
            notification.style.fontWeight = 'bold';
            notification.style.fontSize = '14px';
            
            setTimeout(function() {
                notification.textContent = '';
            }, 3000);
        }
    }
    """,
    Output("panel-summary-output", "id"),
    Input("panel-summary-output", "value")
)

# =============================================================================
# APP STARTUP AND RUN
# =============================================================================

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=False)