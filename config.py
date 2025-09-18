"""
Configuration file for PanelBuilder
Contains all constants, paths, and configuration settings
ADAPTED FROM VARIANTVISUALIZER STYLE WITH COMPACT HPO SUGGESTIONS
"""

import os
import logging

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# PERFORMANCE CONFIGURATION
# =============================================================================

# Cache settings
CACHE_TIMEOUT = 600  # 10 minutes
MAX_CONCURRENT_FETCHES = 10  # Maximum parallel API requests

# =============================================================================
# API CONFIGURATION
# =============================================================================

PANELAPP_UK_BASE = "https://panelapp.genomicsengland.co.uk/api/v1/"
PANELAPP_AU_BASE = "https://panelapp-aus.org/api/v1/"

# =============================================================================
# PANEL PRESETS CONFIGURATION
# =============================================================================

PANEL_PRESETS = {
	"neurodevelopmental": {
        "name": "Neurodevelopmental Disorders",
        "icon": "mdi:head-cog",
        "uk_panels": [285],
        "au_panels": [250],
        "internal": [8801],
        "conf": [3],
        "manual": [],
        "hpo_terms": [] 
    }
}

# =============================================================================
# UI CONFIGURATION
# =============================================================================

# Color mappings adapted from VariantVisualizer
CONFIDENCE_COLORS = {
    3: '#d4edda',  # Green
    2: '#fff3cd',  # Amber
    1: '#f8d7da',  # Red
    0: '#d1ecf1'   # Manual (light blue)
}

# =============================================================================
# EXTERNAL STYLESHEETS
# =============================================================================

EXTERNAL_STYLESHEETS = [
    "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
]

# =============================================================================
# CUSTOM CSS - ADAPTED FROM VARIANTVISUALIZER + COMPACT HPO SUGGESTIONS
# =============================================================================

CUSTOM_CSS = '''
body {
    background: linear-gradient(135deg, #00BCD4 0%, #4DD0E1 50%, #80E5A3 100%);
    min-height: 100vh;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin: 0;
    padding: 0;
    font-size: 13px !important;
}

.glass-card {
    background: rgba(255, 255, 255, 0.95) !important;
    backdrop-filter: blur(10px);
    border-radius: 12px !important;
    box-shadow: 0 3px 15px rgba(0, 0, 0, 0.1) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
}

/* HEADER STYLING */
.app-header {
    background: rgba(255, 255, 255, 0.95) !important;
    backdrop-filter: blur(10px);
    border-radius: 12px !important;
    box-shadow: 0 3px 15px rgba(0, 0, 0, 0.1) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    padding: 1.2rem;
    margin-bottom: 20px;
    position: relative;
}

.app-title {
    font-size: 2rem !important;
    font-weight: 700 !important;
    background: linear-gradient(135deg, #00BCD4, #0097A7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
}

/* SIDEBAR STYLING */
.offcanvas {
    background: rgba(255, 255, 255, 0.98) !important;
    backdrop-filter: blur(15px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 2px 0 15px rgba(0, 0, 0, 0.15);
}

.offcanvas-header {
    background: linear-gradient(135deg, #00BCD4, #0097A7);
    color: white;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
    font-size: 14px !important;
}

.offcanvas-title {
    font-weight: 600;
    font-size: 1.1rem !important;
}

/* SIDEBAR BUTTONS */
.preset-btn {
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(0, 188, 212, 0.3);
    border-radius: 10px;
    transition: all 0.3s ease;
    font-size: 13px !important;
    padding: 10px 12px !important;
    text-align: left;
}

.preset-btn:hover {
    background: rgba(0, 188, 212, 0.1);
    border-color: #00BCD4;
    transform: translateY(-1px);
    box-shadow: 0 3px 10px rgba(0, 188, 212, 0.2);
}

/* FORM CONTROLS */
.form-control, .form-select {
    border-radius: 8px !important;
    border: 1px solid rgba(0, 188, 212, 0.3);
    font-size: 13px !important;
    padding: 0.5rem 0.75rem !important;
    transition: all 0.3s ease;
}

.form-control:focus, .form-select:focus {
    border-color: #00BCD4;
    box-shadow: 0 0 0 0.2rem rgba(0, 188, 212, 0.25);
}

/* BUTTONS */
.btn {
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500;
    padding: 0.5rem 1rem !important;
    transition: all 0.3s ease;
}

.btn-primary {
    background: linear-gradient(135deg, #00BCD4, #0097A7);
    border: none;
    color: white;
}

.btn-primary:hover {
    background: linear-gradient(135deg, #0097A7, #00838F);
    transform: translateY(-1px);
    box-shadow: 0 3px 12px rgba(0, 188, 212, 0.3);
}

.btn-success {
    background: linear-gradient(135deg, #28a745, #20c997);
    border: none;
}

.btn-success:hover {
    background: linear-gradient(135deg, #20c997, #17a2b8);
    transform: translateY(-1px);
    box-shadow: 0 3px 12px rgba(40, 167, 69, 0.3);
}

.btn-danger {
    background: linear-gradient(135deg, #dc3545, #e74c3c);
    border: none;
}

.btn-danger:hover {
    background: linear-gradient(135deg, #e74c3c, #c0392b);
    transform: translateY(-1px);
    box-shadow: 0 3px 12px rgba(220, 53, 69, 0.3);
}

.btn-info {
    background: linear-gradient(135deg, #17a2b8, #20c997);
    border: none;
}

.btn-info:hover {
    background: linear-gradient(135deg, #20c997, #28a745);
    transform: translateY(-1px);
    box-shadow: 0 3px 12px rgba(23, 162, 184, 0.3);
}

.btn-secondary {
    background: linear-gradient(135deg, #6c757d, #5a6268);
    border: none;
}

.btn-secondary:hover {
    background: linear-gradient(135deg, #5a6268, #495057);
    transform: translateY(-1px);
    box-shadow: 0 3px 12px rgba(108, 117, 125, 0.3);
}

/* CARDS AND CONTAINERS */
.card {
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 3px 15px rgba(0, 0, 0, 0.1);
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
}

.card-header {
    background: linear-gradient(135deg, #f8f9fa, #e9ecef);
    border-bottom: 1px solid rgba(0, 188, 212, 0.2);
    border-radius: 12px 12px 0 0 !important;
    font-weight: 600;
    font-size: 14px !important;
    padding: 0.75rem 1rem !important;
}

.card-body {
    padding: 1rem !important;
}

/* TABLES */
.dash-table-container {
    border-radius: 10px;
    box-shadow: 0 3px 15px rgba(0, 0, 0, 0.1);
    overflow: hidden;
}

.dash-table-container .dash-spreadsheet-container {
    border-radius: 10px;
}

.dash-table-container .dash-header {
    background: linear-gradient(135deg, #f8f9fa, #e9ecef);
    font-weight: 600;
    font-size: 12px !important;
}

/* DROPDOWN STYLING - SOLUTION ALTERNATIVE POUR Z-INDEX */
.Select-control {
    border-radius: 8px !important;
    border: 1px solid rgba(0, 188, 212, 0.3) !important;
    font-size: 13px !important;
    min-height: 32px !important;
    position: relative !important;
}

.Select-control:hover {
    border-color: #00BCD4 !important;
}

/* COMPACT HPO SUGGESTIONS STYLING */
.compact-hpo-card {
    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
    border: 1px solid rgba(0, 188, 212, 0.4);
    border-radius: 6px;
    padding: 6px 8px;
    margin-bottom: 3px;
    box-shadow: 0 1px 4px rgba(0, 188, 212, 0.1);
    transition: all 0.2s ease;
    height: 26px;
    display: flex;
    align-items: center;
    animation: slideInFromLeft 0.3s ease-out;
}

.compact-hpo-card:hover {
    transform: translateX(2px);
    box-shadow: 0 2px 8px rgba(0, 188, 212, 0.2);
    border-color: #00BCD4;
}

/* Animation for new compact suggestion cards */
@keyframes slideInFromLeft {
    from {
        opacity: 0;
        transform: translateX(-10px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

/* Compact suggestions container */
#smart-hpo-suggestions-container {
    transition: all 0.3s ease;
}

/* Button styling for compact suggestions */
.compact-hpo-card .btn {
    font-weight: 500;
    transition: all 0.2s ease;
    border-width: 1px;
    width: 20px;
    height: 20px;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
}

.compact-hpo-card .btn:hover {
    transform: scale(1.1);
}

.compact-hpo-card .btn-success {
    background: linear-gradient(135deg, #28a745, #20c997);
    border: none;
}

.compact-hpo-card .btn-success:hover {
    background: linear-gradient(135deg, #20c997, #17a2b8);
    box-shadow: 0 2px 6px rgba(40, 167, 69, 0.3);
}

.compact-hpo-card .btn-outline-secondary {
    border-color: rgba(108, 117, 125, 0.5);
    color: #6c757d;
    background: transparent;
}

.compact-hpo-card .btn-outline-secondary:hover {
    background: rgba(108, 117, 125, 0.15);
    border-color: #6c757d;
    color: #495057;
    box-shadow: 0 2px 6px rgba(108, 117, 125, 0.2);
}

.compact-hpo-card .btn-outline-primary {
    border-color: rgba(0, 188, 212, 0.5);
    color: #00BCD4;
    background: transparent;
}

.compact-hpo-card .btn-outline-primary:hover {
    background: rgba(0, 188, 212, 0.1);
    border-color: #00BCD4;
    color: #0097A7;
    box-shadow: 0 2px 6px rgba(0, 188, 212, 0.2);
}

/* Scrollbar styling for compact suggestions container */
#smart-hpo-suggestions-container::-webkit-scrollbar {
    width: 3px;
}

#smart-hpo-suggestions-container::-webkit-scrollbar-track {
    background: rgba(0, 188, 212, 0.1);
    border-radius: 2px;
}

#smart-hpo-suggestions-container::-webkit-scrollbar-thumb {
    background: rgba(0, 188, 212, 0.4);
    border-radius: 2px;
}

#smart-hpo-suggestions-container::-webkit-scrollbar-thumb:hover {
    background: #00BCD4;
}

/* Remove old suggestion styles */
.smart-hpo-card {
    display: none;
}

#smart-hpo-suggestion-card {
    display: none;
}

/* Loading states for compact suggestions */
.compact-suggestion-loading {
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: loading 1.5s infinite;
    border: 1px dashed rgba(0, 188, 212, 0.3);
}

@keyframes loading {
    0% {
        background-position: 200% 0;
    }
    100% {
        background-position: -200% 0;
    }
}

/* Text styling for compact cards */
.compact-hpo-card code {
    font-size: 8px;
    background-color: #f8f9fa;
    padding: 1px 3px;
    border-radius: 2px;
    margin-right: 4px;
    font-family: 'Courier New', monospace;
}

/* Responsive adjustments for compact cards */
@media (max-width: 768px) {
    .compact-hpo-card {
        height: 24px;
        padding: 4px 6px;
        font-size: 9px;
    }
    
    .compact-hpo-card .btn {
        width: 18px;
        height: 18px;
    }
    
    .compact-hpo-card code {
        font-size: 7px;
        padding: 1px 2px;
    }
}

/* SPINNER FULL SCREEN */
.fullscreen-spinner-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 188, 212, 0.95);
    backdrop-filter: blur(10px);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    z-index: 999999;
    animation: fadeIn 0.3s ease-in;
}

.fullscreen-spinner-overlay.hide {
    display: none;
}

.spinner-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    color: white;
}

.custom-spinner {
    width: 80px;
    height: 80px;
    border: 4px solid rgba(255, 255, 255, 0.3);
    border-left: 4px solid white;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 20px;
}

.spinner-text {
    font-size: 18px;
    font-weight: 600;
    color: white;
    text-align: center;
    animation: pulse 2s ease-in-out infinite;
}

.spinner-subtext {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.8);
    margin-top: 10px;
    text-align: center;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

/* ===================================================================== */
/* NOUVELLES AMÉLIORATIONS POUR LES CARTES HPO AVEC BOUTONS REPOSITIONNÉS */
/* ===================================================================== */

/* Améliorations pour les cartes HPO horizontales */
.horizontal-hpo-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 188, 212, 0.25) !important;
}

/* Amélioration de l'espacement du texte HPO */
.horizontal-hpo-card .hpo-text-container {
    padding: 0 4px;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 3; /* Limite à 3 lignes */
    -webkit-box-orient: vertical;
    line-height: 1.3;
}

/* Optimisation des boutons dans la nouvelle disposition */
.horizontal-hpo-card .btn {
    transition: all 0.15s ease;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.horizontal-hpo-card .btn:hover {
    transform: scale(1.05);
    box-shadow: 0 2px 6px rgba(0,0,0,0.15);
}

/* Amélioration du code HPO au centre */
.horizontal-hpo-card code {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    font-family: 'Courier New', monospace;
    font-weight: 500;
}

/* Animation pour les nouveaux éléments */
.horizontal-hpo-card .hpo-button-row {
    animation: slideInFromBottom 0.3s ease-out;
}

@keyframes slideInFromBottom {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Optimisation de l'espace pour les cartes HPO */
.horizontal-hpo-card {
    flex-shrink: 1 !important; /* Permet aux cartes de se rétrécir si nécessaire */
    flex-grow: 0 !important;
}

/* Amélioration du conteneur de suggestions pour un meilleur fitting */
#smart-hpo-suggestions-container {
    gap: 4px !important; /* Réduit l'espacement entre les cartes */
    padding: 8px !important;
}

/* Optimisation responsive pour les cartes HPO horizontales */
@media (max-width: 1400px) {
    .horizontal-hpo-card {
        minWidth: 180px !important;
        maxWidth: 220px !important;
        width: calc(33.33% - 6px) !important;
    }
}

@media (max-width: 1200px) {
    .horizontal-hpo-card {
        minWidth: 170px !important;
        maxWidth: 200px !important;
        width: calc(33.33% - 5px) !important;
    }
    
    .horizontal-hpo-card .btn {
        width: 26px !important;
        height: 26px !important;
    }
    
    .horizontal-hpo-card code {
        fontSize: 10px !important;
        padding: 3px 6px !important;
    }
}

@media (max-width: 1000px) {
    .horizontal-hpo-card {
        minWidth: 160px !important;
        maxWidth: 180px !important;
        width: calc(33.33% - 4px) !important;
    }
    
    .horizontal-hpo-card strong {
        fontSize: 13px !important;
    }
}

@media (max-width: 768px) {
    .horizontal-hpo-card {
        minWidth: 140px !important;
        maxWidth: 160px !important;
        width: calc(50% - 2px) !important; /* 2 cartes par ligne sur mobile */
    }
    
    .horizontal-hpo-card .btn {
        width: 24px !important;
        height: 24px !important;
    }
    
    .horizontal-hpo-card strong {
        fontSize: 12px !important;
    }
    
    .horizontal-hpo-card code {
        fontSize: 9px !important;
        padding: 2px 4px !important;
    }
}

/* Indicateurs de confiance améliorés */
.confidence-high {
    border-left: 4px solid #28a745 !important;
}

.confidence-medium {
    border-left: 4px solid #ffc107 !important;
}

.confidence-low {
    border-left: 4px solid #6c757d !important;
}

/* Animations d'entrée */
.hpo-suggestion-enter {
    animation: slideInFromBottom 0.3s ease-out;
}

@keyframes slideInFromBottom {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Badge de source */
.hpo-source-badge {
    position: absolute;
    top: 2px;
    right: 2px;
    background: rgba(0, 188, 212, 0.8);
    color: white;
    font-size: 8px;
    padding: 1px 3px;
    border-radius: 2px;
    font-weight: bold;
}

/* Amélioration de la lisibilité du texte HPO long */
.horizontal-hpo-card strong {
    word-wrap: break-word;
    overflow-wrap: break-word;
    hyphens: auto;
    -webkit-hyphens: auto;
    -moz-hyphens: auto;
    -ms-hyphens: auto;
}

/* Animation de chargement pour les suggestions */
.suggestion-loading-spinner {
    animation: spin 1s linear infinite;
}

/* Amélioration des effets de survol pour les boutons HPO */
.horizontal-hpo-card .btn-success:hover {
    background: linear-gradient(135deg, #20c997, #17a2b8) !important;
    border-color: #20c997 !important;
    box-shadow: 0 2px 8px rgba(32, 201, 151, 0.4) !important;
}

.horizontal-hpo-card .btn-danger:hover {
    background: linear-gradient(135deg, #e74c3c, #c0392b) !important;
    border-color: #e74c3c !important;
    box-shadow: 0 2px 8px rgba(231, 76, 60, 0.4) !important;
}

/* Amélioration de la mise en page pour les conteneurs de suggestions */
#smart-hpo-suggestions-container .horizontal-hpo-card {
    flex-shrink: 0;
    margin-right: 8px;
}

#smart-hpo-suggestions-container .horizontal-hpo-card:last-child {
    margin-right: 0;
}

/* Animation de pulsation pour les éléments importants */
.pulse-animation {
    animation: pulseGlow 2s ease-in-out infinite;
}

@keyframes pulseGlow {
    0% {
        box-shadow: 0 0 5px rgba(0, 188, 212, 0.3);
    }
    50% {
        box-shadow: 0 0 20px rgba(0, 188, 212, 0.6);
    }
    100% {
        box-shadow: 0 0 5px rgba(0, 188, 212, 0.3);
    }
}
/* Styles pour les HPO auto-générés - AMÉLIORATION VISUELLE */
.Select__multi-value:has-text("🟢") {
    background-color: #d4edda !important;
    border: 1px solid #28a745 !important;
}

/* Alternative plus compatible */
.css-12jo7m5 {
    background-color: #d4edda !important;
}

/* Forcer la couleur verte pour les éléments auto-générés */
div[class*="multi-value"]:has(div:contains("🟢")) {
    background-color: #d4edda !important;
    border-color: #28a745 !important;
}

'''