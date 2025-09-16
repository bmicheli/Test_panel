"""
Configuration file for PanelBuilder
Contains all constants, paths, and configuration settings
ADAPTED FROM VARIANTVISUALIZER STYLE
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
        "icon": "", #mdi:head-cog
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
# CUSTOM CSS - ADAPTED FROM VARIANTVISUALIZER
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

/* HARMONIZED TYPOGRAPHY */
h1 {
    font-size: 2rem !important;
    font-weight: 700 !important;
}

h2 {
    font-size: 1.6rem !important;
    font-weight: 650 !important;
}

h3 {
    font-size: 1.4rem !important;
    font-weight: 600 !important;
}

h4 {
    font-size: 1.2rem !important;
    font-weight: 600 !important;
}

h5 {
    font-size: 1.1rem !important;
    font-weight: 600 !important;
}

h6 {
    font-size: 1rem !important;
    font-weight: 600 !important;
}

label, .form-label {
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #2c3e50;
}

p {
    font-size: 13px !important;
    line-height: 1.5 !important;
}

.text-muted {
    font-size: 12px !important;
    color: #6c757d !important;
}

/* CONTAINER SPACING */
.container-fluid {
    padding: 20px !important;
}

/* CUSTOM ANIMATIONS */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(15px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.fade-in-up {
    animation: fadeInUp 0.5s ease-out;
}

/* RESPONSIVE IMPROVEMENTS */
@media (max-width: 768px) {
    .app-title {
        font-size: 1.8rem !important;
    }
    
    .container-fluid {
        padding: 12px !important;
    }
    
    .btn {
        font-size: 12px !important;
        padding: 0.4rem 0.8rem !important;
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
'''