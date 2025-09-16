"""
Utility functions for PanelBuilder
Contains API calls, data processing, and helper functions
"""

import requests
import pandas as pd
import numpy as np
import time
import concurrent.futures
from functools import lru_cache
import base64
import json
import os
import hashlib
import re
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib_venn import venn2, venn3
import io
from config import *

# =============================================================================
# API FUNCTIONS
# =============================================================================

def fetch_panels(base_url):
    """Fetch list of panels from a PanelApp instance (UK or Australia)"""
    panels = []
    url = f"{base_url}panels/"
    
    try:
        while url:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                logger.error(f"Failed to fetch panels from {url}, status: {response.status_code}")
                return pd.DataFrame(columns=["id", "name"])
            data = response.json()
            panels.extend(data.get('results', []))
            url = data.get('next')  # For pagination
    except Exception as e:
        logger.error(f"Exception while fetching panels: {e}")
        return pd.DataFrame(columns=["id", "name"])
    
    return pd.DataFrame(panels)

def fetch_panel_genes(base_url, panel_id):
    """Fetch gene list for a specific panel ID with detailed gene information"""
    url = f"{base_url}panels/{panel_id}/"
    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch panel genes from {url}")
    
    panel_data = response.json()
    genes = panel_data.get("genes", [])
    
    def format_omim_links(omim_list):
        """Format OMIM IDs as clickable links"""
        if not omim_list:
            return ""
        
        links = []
        for omim_id in omim_list:
            if omim_id:
                links.append(f'[{omim_id}](https://omim.org/entry/{omim_id})')
        
        return " | ".join(links) if links else ""
    
    def format_hgnc_link(hgnc_id):
        """Format HGNC ID as clickable link"""
        if not hgnc_id:
            return ""
        
        return f'[{hgnc_id}](https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/{hgnc_id})'
    
    df_genes = pd.DataFrame([
        {
            "gene_symbol": g["gene_data"].get("gene_symbol", ""),
            "omim_id": format_omim_links(g["gene_data"].get("omim_gene", [])),
            "hgnc_id": format_hgnc_link(g["gene_data"].get("hgnc_id", "")),
            "entity_type": g.get("entity_type", ""),
            "biotype": g["gene_data"].get("biotype", ""),
            "mode_of_inheritance": g.get("mode_of_inheritance", ""),
            "confidence_level": g.get("confidence_level"),
            "penetrance": g.get("penetrance"),
            "source": g.get("source"),
        }
        for g in genes
    ])
    
    # Return panel data which includes name, version, and other metadata
    panel_info = {
        "name": panel_data.get("name"),
        "version": panel_data.get("version"),
        "id": panel_data.get("id"),
        "status": panel_data.get("status"),
        "disease_group": panel_data.get("disease_group"),
        "disease_sub_group": panel_data.get("disease_sub_group")
    }
    
    return df_genes, panel_info

# =============================================================================
# CACHED FUNCTIONS FOR PERFORMANCE
# =============================================================================

@lru_cache(maxsize=200)
def fetch_panel_genes_cached(base_url, panel_id):
    """Cached version of fetch_panel_genes - avoids repeated API calls"""
    try:
        return fetch_panel_genes(base_url, panel_id)
    except Exception as e:
        logger.error(f"Error fetching panel {panel_id}: {e}")
        return pd.DataFrame(), {}

@lru_cache(maxsize=500)
def fetch_hpo_term_details_cached(term_id):
    """Cached version of HPO term fetching"""
    return fetch_hpo_term_details(term_id)

@lru_cache(maxsize=100)
def fetch_panel_disorders_cached(base_url, panel_id):
    """Cached version of panel disorders fetching"""
    return fetch_panel_disorders(base_url, panel_id)

# =============================================================================
# PARALLEL PROCESSING FUNCTIONS
# =============================================================================

def fetch_panels_parallel(uk_ids=None, au_ids=None, max_workers=5):
    """Fetch multiple panels in parallel instead of sequentially"""
    results = {}
    
    if not uk_ids and not au_ids:
        return results
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_panel = {}
        
        if uk_ids:
            for panel_id in uk_ids:
                future = executor.submit(fetch_panel_genes_cached, PANELAPP_UK_BASE, panel_id)
                future_to_panel[future] = ('UK', panel_id)
        
        if au_ids:
            for panel_id in au_ids:
                future = executor.submit(fetch_panel_genes_cached, PANELAPP_AU_BASE, panel_id)
                future_to_panel[future] = ('AU', panel_id)
        
        for future in concurrent.futures.as_completed(future_to_panel, timeout=30):
            source, panel_id = future_to_panel[future]
            try:
                df, panel_info = future.result()
                results[f"{source}_{panel_id}"] = (df, panel_info)
            except Exception as e:
                logger.error(f"Failed to fetch {source} panel {panel_id}: {e}")
                results[f"{source}_{panel_id}"] = (pd.DataFrame(), {})
    
    return results

def fetch_hpo_terms_parallel(hpo_terms, max_workers=10):
    """Fetch multiple HPO terms in parallel"""
    if not hpo_terms:
        return []
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_term = {
            executor.submit(fetch_hpo_term_details_cached, term_id): term_id 
            for term_id in hpo_terms
        }
        
        for future in concurrent.futures.as_completed(future_to_term, timeout=20):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                term_id = future_to_term[future]
                logger.error(f"Failed to fetch HPO term {term_id}: {e}")
                results.append({
                    "id": term_id,
                    "name": term_id,
                    "definition": "Unable to fetch definition"
                })
    
    return results

# =============================================================================
# INTERNAL PANELS MANAGEMENT
# =============================================================================

def load_internal_panels_from_files(directory_path="data/internal_panels"):
    """Load internal panels directly from .txt files in the specified directory"""
    
    internal_data = []
    panel_info = []
    
    if not os.path.exists(directory_path):
        logger.warning(f"Directory {directory_path} does not exist")
        return pd.DataFrame(), pd.DataFrame()
    
    txt_files = sorted([f for f in os.listdir(directory_path) if f.endswith('.txt')])
    
    def generate_stable_id(filename):
        import hashlib
        
        base_name = filename.replace('.txt', '')
        parts = base_name.split('_')
        
        version_idx = -1
        for i, part in enumerate(parts):
            if part.startswith('v') and part[1:].isdigit():
                version_idx = i
                break
        
        if version_idx == -1:
            panel_name_for_id = base_name
        else:
            if version_idx > 0 and parts[version_idx - 1].isdigit():
                panel_name_parts = parts[:version_idx - 1]
            else:
                panel_name_parts = parts[:version_idx]
            
            panel_name_for_id = '_'.join(panel_name_parts)
        
        hash_obj = hashlib.md5(panel_name_for_id.encode())
        hash_hex = hash_obj.hexdigest()[:8]
        hash_int = int(hash_hex, 16) % 8999 + 2000
        return hash_int
    
    for file_name in txt_files:
        try:
            base_name = file_name.replace('.txt', '')
            parts = base_name.split('_')
            
            version_idx = -1
            for i, part in enumerate(parts):
                if part.startswith('v') and part[1:].isdigit():
                    version_idx = i
                    break
            
            if version_idx == -1:
                logger.warning(f"Could not parse version from {file_name}")
                continue
            
            version = int(parts[version_idx][1:])
            
            if version_idx > 0 and parts[version_idx - 1].isdigit():
                gene_count_from_filename = int(parts[version_idx - 1])
                panel_name_parts = parts[:version_idx - 1]
            else:
                gene_count_from_filename = 0
                panel_name_parts = parts[:version_idx]
            
            panel_name = '_'.join(panel_name_parts)
            panel_id = generate_stable_id(file_name)
            
            file_path = os.path.join(directory_path, file_name)
            with open(file_path, 'r', encoding='utf-8') as f:
                genes = [line.strip() for line in f if line.strip()]
            
            actual_gene_count = len(genes)
            
            panel_info.append({
                'panel_id': panel_id,
                'panel_name': panel_name,
                'version': version,
                'gene_count': actual_gene_count,
                'gene_count_filename': gene_count_from_filename,
                'file_name': file_name,
                'base_name': base_name
            })
            
            for gene in genes:
                internal_data.append({
                    'panel_id': panel_id,
                    'panel_name': panel_name,
                    'gene_symbol': gene,
                    'confidence_level': 3  # Default to Green confidence
                })
        
        except Exception as e:
            logger.error(f"Error processing file {file_name}: {e}")
            continue
    
    internal_df = pd.DataFrame(internal_data)
    internal_panels = pd.DataFrame(panel_info).sort_values('panel_id')
    
    return internal_df, internal_panels

# =============================================================================
# DATA PROCESSING FUNCTIONS
# =============================================================================

def clean_confidence_level_fast(df):
    """Vectorized confidence level cleaning - much faster than original"""
    if 'confidence_level' not in df.columns:
        return df
    
    df = df.copy()
    
    confidence_map = {
        '3': 3, '3.0': 3, 'green': 3, 'high': 3,
        '2': 2, '2.0': 2, 'amber': 2, 'orange': 2, 'medium': 2,
        '1': 1, '1.0': 1, 'red': 1, 'low': 1,
        '0': 0, '0.0': 0, '': 0, 'nan': 0, 'none': 0
    }
    
    df['confidence_level'] = (df['confidence_level']
                            .astype(str)
                            .str.lower()
                            .str.strip()
                            .map(confidence_map)
                            .fillna(0)
                            .astype(int))
    
    return df

def deduplicate_genes_fast(df_all):
    """Fast gene deduplication with proper confidence handling"""
    if df_all.empty:
        return df_all
    
    df_all["confidence_level"] = pd.to_numeric(df_all["confidence_level"], errors='coerce').fillna(0).astype(int)
    
    df_all = df_all[df_all["gene_symbol"].notna() & (df_all["gene_symbol"] != "")]
    
    df_sorted = df_all.sort_values(['confidence_level', 'gene_symbol'], 
                                ascending=[False, True])
    
    df_unique = df_sorted.drop_duplicates(subset=['gene_symbol'], keep='first')
    
    return df_unique.sort_values(['confidence_level', 'gene_symbol'], 
                                ascending=[False, True])

# =============================================================================
# HPO FUNCTIONS
# =============================================================================

def fetch_panel_disorders(base_url, panel_id):
    """Fetch disorders associated with a panel to extract HPO terms"""
    try:
        base_url = base_url.rstrip('/')
        url = f"{base_url}/panels/{panel_id}/"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        relevant_disorders = data.get('relevant_disorders', [])
        
        if not relevant_disorders:
            return []
        
        hpo_terms = []
        
        for disorder in relevant_disorders:
            if isinstance(disorder, str):
                hpo_matches = re.findall(r'HP:\d{7}', disorder)
                hpo_terms.extend(hpo_matches)
        
        hpo_terms = list(dict.fromkeys(hpo_terms))
        
        return hpo_terms
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.warning(f"Panel {panel_id} not found (404)")
        else:
            logger.error(f"HTTP error {e.response.status_code} for panel {panel_id}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error fetching disorders for panel {panel_id}: {e}")
        return []

def search_hpo_terms(query, limit=100):
    """Search for HPO terms using the JAX ontology API"""
    if not query or len(query.strip()) < 2:
        return []
    
    try:
        url = f"https://ontology.jax.org/api/hp/search?q={query}&page=0&limit={limit}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        options = []
        if 'terms' in data:
            for term in data['terms']:
                label = f"{term.get('name', '')} ({term.get('id', '')})"
                value = term.get('id', '')
                options.append({"label": label, "value": value})
        
        return options
    except Exception as e:
        logger.error(f"Error searching HPO terms: {e}")
        return []

def fetch_hpo_term_details(term_id):
    """Fetch detailed information for an HPO term"""
    try:
        url = f"https://ontology.jax.org/api/hp/terms/{term_id}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            term_data = response.json()
            return {
                "id": term_id,
                "name": term_data.get("name", term_id),
                "definition": term_data.get("definition", "No definition available")
            }
        else:
            return {
                "id": term_id,
                "name": term_id,
                "definition": "Unable to fetch definition"
            }
    except Exception as e:
        return {
            "id": term_id,
            "name": term_id,
            "definition": "Unable to fetch definition"
        }

def get_hpo_terms_from_panels(uk_ids=None, au_ids=None):
    """Extract HPO terms from Australia panels"""
    all_hpo_terms = set() 
    if au_ids:
        for panel_id in au_ids:
            hpo_terms = fetch_panel_disorders_cached(PANELAPP_AU_BASE, panel_id)
            all_hpo_terms.update(hpo_terms)
    
    return list(all_hpo_terms)

# =============================================================================
# VISUALIZATION FUNCTIONS
# =============================================================================

def create_upset_plot(gene_sets, panel_names):
    """Create an UpSet plot for visualizing intersections of multiple sets"""
    from itertools import combinations, chain
    
    all_genes = set()
    for genes in gene_sets.values():
        all_genes.update(genes)
    
    if not all_genes:
        return None
    
    gene_memberships = {}
    sets_list = list(gene_sets.keys())
    
    for gene in all_genes:
        membership = tuple(i for i, (name, genes) in enumerate(gene_sets.items()) if gene in genes)
        if membership not in gene_memberships:
            gene_memberships[membership] = []
        gene_memberships[membership].append(gene)
    
    single_sets = []
    multi_sets = []
    
    for membership, genes in gene_memberships.items():
        if len(membership) == 1:
            single_sets.append((membership, genes))
        else:
            multi_sets.append((membership, genes))
    
    single_sets.sort(key=lambda x: len(x[1]), reverse=True)
    multi_sets.sort(key=lambda x: len(x[1]), reverse=True)
    
    sorted_intersections = single_sets + multi_sets
    max_intersections = min(15, len(sorted_intersections))
    sorted_intersections = sorted_intersections[:max_intersections]
    
    num_intersections = len(sorted_intersections)
    num_sets = len(sets_list)
    figure_height = 5
    dpi = 180

    if num_intersections <= 6:
        figure_width = 6.5
    elif num_intersections <= 10:
        figure_width = 8.5
    else:
        figure_width = 10
    
    fig, (ax_bars, ax_matrix) = plt.subplots(2, 1, figsize=(figure_width, figure_height), dpi=dpi,
                                        gridspec_kw={'height_ratios': [1, 1]})
    
    if num_intersections <= 6:
        bar_width = 0.8
        title_fontsize = 14
        label_fontsize = 12
        value_fontsize = 10
        ytick_fontsize = 10
    elif num_intersections <= 10:
        bar_width = 0.7
        title_fontsize = 13
        label_fontsize = 11
        value_fontsize = 9
        ytick_fontsize = 9
    else:
        bar_width = 0.6
        title_fontsize = 12
        label_fontsize = 10
        value_fontsize = 8
        ytick_fontsize = 8
    
    intersection_sizes = [len(genes) for _, genes in sorted_intersections]
    x_pos = np.arange(len(intersection_sizes))
    
    bar_colors = []
    for membership, _ in sorted_intersections:
        if len(membership) == 1:
            bar_colors.append('#3498db')
        else:
            bar_colors.append('#2c3e50')
    
    bars = ax_bars.bar(x_pos, intersection_sizes, color=bar_colors, alpha=0.8, width=bar_width,
                    edgecolor='white', linewidth=1)
    
    ax_bars.set_ylabel('Number of Genes', fontsize=label_fontsize, fontweight='bold')
    ax_bars.set_title('Gene Panel Intersections', fontsize=title_fontsize, fontweight='bold', pad=20)
    ax_bars.set_xticks([])
    ax_bars.grid(True, alpha=0.3, axis='y')
    ax_bars.spines['top'].set_visible(False)
    ax_bars.spines['right'].set_visible(False)
    ax_bars.set_xlim(-0.5, len(sorted_intersections) - 0.5)
    
    max_height = max(intersection_sizes) if intersection_sizes else 1
    for i, (bar, size) in enumerate(zip(bars, intersection_sizes)):
        ax_bars.text(i, bar.get_height() + max_height * 0.01, 
                    str(size), ha='center', va='bottom', fontweight='bold', 
                    fontsize=value_fontsize)
    
    matrix_data = np.zeros((len(sets_list), len(sorted_intersections)))
    for j, (membership, _) in enumerate(sorted_intersections):
        for i in membership:
            matrix_data[i, j] = 1
    
    ax_matrix.clear()
    ax_matrix.set_xlim(-0.5, len(sorted_intersections) - 0.5)
    ax_matrix.set_ylim(-0.5, len(sets_list) - 0.5)
    
    circle_radius = 0.1
    line_width = 2.0
    
    for i in range(len(sets_list)):
        for j in range(len(sorted_intersections)):
            x_center = float(j)
            y_center = float(i)
            
            if matrix_data[i, j] == 1:
                circle = plt.Circle((x_center, y_center), circle_radius, 
                                color='black', zorder=2, clip_on=False)
                ax_matrix.add_patch(circle)
            else:
                empty_radius = circle_radius * 0.8
                circle = plt.Circle((x_center, y_center), empty_radius, 
                                fill=False, color='lightgray', 
                                linewidth=0.8, alpha=0.5, zorder=2, clip_on=False)
                ax_matrix.add_patch(circle)
    
    for j in range(len(sorted_intersections)):
        connected = [k for k in range(len(sets_list)) if matrix_data[k, j] == 1]
        if len(connected) > 1:
            min_y, max_y = min(connected), max(connected)
            x_line = float(j)
            ax_matrix.plot([x_line, x_line], [min_y, max_y], 'k-', linewidth=line_width, 
                        alpha=0.95, zorder=1, solid_capstyle='round')
    
    display_names = []
    for name in sets_list:
        set_size = len(gene_sets[name])
        
        if name == "Manual":
            display_names.append(f"Manual ({set_size})")
        elif name.startswith("UK_"):
            panel_id = name.replace("UK_", "")
            display_names.append(f"UK_{panel_id} ({set_size})")
        elif name.startswith("AUS_"):
            panel_id = name.replace("AUS_", "")
            display_names.append(f"AUS_{panel_id} ({set_size})")
        elif name.startswith("INT-"):
            panel_id = name.replace("INT-", "")
            display_names.append(f"INT_{panel_id} ({set_size})")
        else:
            display_names.append(f"{name} ({set_size})")
    
    ax_matrix.set_yticks(range(len(sets_list)))
    ax_matrix.set_yticklabels(display_names, fontsize=ytick_fontsize)
    ax_matrix.set_xticks([])
    ax_matrix.set_xlabel('')
    
    ax_matrix.grid(False)
    for spine in ax_matrix.spines.values():
        spine.set_visible(False)
    
    ax_matrix.invert_yaxis()
    
    if num_intersections <= 10:
        pad = 1.8
    else:
        pad = 1.2
    
    plt.tight_layout(pad=pad)
    ax_matrix.set_facecolor('white')
    ax_bars.set_facecolor('white')
    fig.patch.set_facecolor('white')
    
    return fig

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def panel_options(df):
    """Generate options for panel dropdowns"""
    options = []
    for _, row in df.iterrows():
        version_text = f" v{row['version']}" if 'version' in row and pd.notna(row['version']) else ""
        label = f"{row['name']}{version_text} (ID {row['id']})"
        options.append({"label": label, "value": row["id"]})
    return options

def internal_options(df):
    """Generate options for internal panel dropdowns"""
    options = []
    for _, row in df.iterrows():
        version_text = f" v{row['version']}" if 'version' in row and pd.notna(row['version']) else ""
        display_name = row['panel_name'].replace('_', ' ')
        label = f"{display_name}{version_text} (ID {row['panel_id']})"
        options.append({"label": label, "value": row["panel_id"]})
    return options

def generate_panel_summary(uk_ids, au_ids, internal_ids, confs, manual_genes_list, panels_uk_df, panels_au_df, internal_panels):
    """Generate a formatted summary of panels and genes"""
    summary_parts = []
    
    def get_confidence_notation(conf_list):
        if not conf_list:
            return ""
        conf_set = set(conf_list)
        if conf_set == {3}:
            return "_G"
        elif conf_set == {2}:
            return "_O"  
        elif conf_set == {1}:
            return "_R"
        elif conf_set == {3, 2}:
            return "_GO"
        elif conf_set == {3, 1}:
            return "_GR"
        elif conf_set == {2, 1}:
            return "_OR"
        elif conf_set == {3, 2, 1}:
            return "_GOR"
        else:
            return ""
    
    confidence_suffix = get_confidence_notation(confs)
    
    # Process UK panels
    if uk_ids:
        for panel_id in uk_ids:
            panel_row = panels_uk_df[panels_uk_df['id'] == panel_id]
            if not panel_row.empty:
                panel_info = panel_row.iloc[0]
                panel_name = panel_info['name'].replace(' ', '_').replace('/', '_').replace(',', '_')
                version = f"_v{panel_info['version']}" if pd.notna(panel_info.get('version')) else ""
                summary_parts.append(f"PanelApp_UK({panel_id})/{panel_name}{version}{confidence_suffix}")
    
    # Process AU panels
    if au_ids:
        for panel_id in au_ids:
            panel_row = panels_au_df[panels_au_df['id'] == panel_id]
            if not panel_row.empty:
                panel_info = panel_row.iloc[0]
                panel_name = panel_info['name'].replace(' ', '_').replace('/', '_').replace(',', '_')
                version = f"_v{panel_info['version']}" if pd.notna(panel_info.get('version')) else ""
                summary_parts.append(f"PanelApp_AUS({panel_id})/{panel_name}{version}{confidence_suffix}")
    
    # Process Internal panels
    if internal_ids:
        for panel_id in internal_ids:
            panel_row = internal_panels[internal_panels['panel_id'] == panel_id]
            if not panel_row.empty:
                panel_info = panel_row.iloc[0]
                base_name = panel_info.get('base_name', panel_info['panel_name'])
                summary_parts.append(f"Panel_HUG/{base_name}")
    
    # Add manual genes
    if manual_genes_list:
        summary_parts.extend(manual_genes_list)
    
    return ",".join(summary_parts)

def extract_keywords_from_panel_names(panel_names):
    """Extract relevant medical keywords from panel names for HPO suggestion"""
    import re
    
    # Medical keywords that are likely to have corresponding HPO terms
    medical_keywords = []
    
    for name in panel_names:
        if not name:
            continue
            
        # Clean the panel name
        cleaned_name = name.lower()
        
        # Remove common non-medical words and patterns
        stop_words = ['panel', 'gene', 'genes', 'list', 'testing', 'analysis', 'v1', 'v2', 'v3', 
                     'version', 'updated', 'comprehensive', 'extended', 'broad', 'focused',
                     'clinical', 'diagnostic', 'genomic', 'inherited', 'familial', 'congenital',
                     'syndrome', 'syndromes', 'disorder', 'disorders', 'disease', 'diseases',
                     'condition', 'conditions', 'defect', 'defects', 'abnormality', 'abnormalities']
        
        # Extract meaningful medical terms (remove punctuation and split)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', cleaned_name)
        
        for word in words:
            if (word not in stop_words and 
                len(word) >= 4 and  # Minimum length for medical terms
                not word.isdigit()):
                medical_keywords.append(word.capitalize())
    
    # Remove duplicates while preserving order
    unique_keywords = list(dict.fromkeys(medical_keywords))
    
    return unique_keywords[:10]  # Limit to 10 keywords for API efficiency

def search_hpo_terms_by_keywords(keywords, max_per_keyword=2):
    """Search HPO terms based on medical keywords extracted from panel names"""
    if not keywords:
        return []
    
    suggested_hpo_terms = []
    
    for keyword in keywords:
        try:
            # Search HPO terms for each keyword
            url = f"https://ontology.jax.org/api/hp/search?q={keyword}&page=0&limit=5"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                terms_found = 0
                
                if 'terms' in data:
                    for term in data['terms']:
                        if terms_found >= max_per_keyword:
                            break
                            
                        hpo_id = term.get('id', '')
                        hpo_name = term.get('name', '')
                        
                        if hpo_id and hpo_name and hpo_id not in [t['value'] for t in suggested_hpo_terms]:
                            suggested_hpo_terms.append({
                                "label": f"{hpo_name} ({hpo_id})",
                                "value": hpo_id,
                                "keyword": keyword
                            })
                            terms_found += 1
                            
        except Exception as e:
            logger.error(f"Error searching HPO terms for keyword '{keyword}': {e}")
            continue
    
    # Sort by relevance (could be enhanced with better scoring)
    return suggested_hpo_terms[:8]  # Return max 8 suggestions

def get_panel_names_from_selections(uk_ids, au_ids, internal_ids, panels_uk_df, panels_au_df, internal_panels):
    """Extract panel names from current selections for keyword analysis"""
    panel_names = []
    
    # UK panels
    if uk_ids and panels_uk_df is not None:
        for panel_id in uk_ids:
            panel_row = panels_uk_df[panels_uk_df['id'] == panel_id]
            if not panel_row.empty:
                panel_names.append(panel_row.iloc[0]['name'])
    
    # AU panels
    if au_ids and panels_au_df is not None:
        for panel_id in au_ids:
            panel_row = panels_au_df[panels_au_df['id'] == panel_id]
            if not panel_row.empty:
                panel_names.append(panel_row.iloc[0]['name'])
    
    # Internal panels
    if internal_ids and internal_panels is not None:
        for panel_id in internal_ids:
            panel_row = internal_panels[internal_panels['panel_id'] == panel_id]
            if not panel_row.empty:
                panel_names.append(panel_row.iloc[0]['panel_name'].replace('_', ' '))
    
    return panel_names