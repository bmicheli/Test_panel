"""
Utility functions for PanelBuilder
Contains API calls, data processing, and helper functions
"""
import re
import requests
from functools import lru_cache
import json
import time
from collections import Counter
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

# =============================================================================
# MAPPING MÉDICAL AMÉLIORÉ POUR HPO
# =============================================================================

# Dictionnaire de mapping entre termes médicaux et HPO terms fréquents
MEDICAL_TO_HPO_MAPPING = {
    # Système nerveux
    'epilepsy': ['HP:0001250', 'HP:0002197'],
    'seizure': ['HP:0001250', 'HP:0011097'],
    'neurodevelopmental': ['HP:0012759', 'HP:0001263'],
    'intellectual': ['HP:0001249', 'HP:0001263'],
    'autism': ['HP:0000717', 'HP:0012759'],
    'microcephaly': ['HP:0000252', 'HP:0001249'],
    'macrocephaly': ['HP:0000256', 'HP:0001250'],
    'ataxia': ['HP:0001251', 'HP:0002066'],
    'spasticity': ['HP:0001257', 'HP:0002061'],
    'neuropathy': ['HP:0009830', 'HP:0000762'],
    'muscular': ['HP:0003560', 'HP:0003198'],
    'dystrophy': ['HP:0003560', 'HP:0003198'],
    'myopathy': ['HP:0003198', 'HP:0009063'],
    
    # Système cardiovasculaire
    'cardiomyopathy': ['HP:0001638', 'HP:0006515'],
    'arrhythmia': ['HP:0011675', 'HP:0001645'],
    'cardiac': ['HP:0001627', 'HP:0001638'],
    'heart': ['HP:0001627', 'HP:0001638'],
    'aortic': ['HP:0002616', 'HP:0001645'],
    'hypertrophic': ['HP:0001639', 'HP:0001638'],
    'dilated': ['HP:0001644', 'HP:0001638'],
    
    # Système visuel
    'retinal': ['HP:0000479', 'HP:0000504'],
    'blindness': ['HP:0000618', 'HP:0000505'],
    'vision': ['HP:0000504', 'HP:0000479'],
    'optic': ['HP:0000648', 'HP:0000504'],
    'cataract': ['HP:0000518', 'HP:0000479'],
    'glaucoma': ['HP:0000501', 'HP:0000479'],
    
    # Système auditif
    'hearing': ['HP:0000365', 'HP:0000407'],
    'deafness': ['HP:0000365', 'HP:0000407'],
    'auditory': ['HP:0000364', 'HP:0000365'],
    
    # Système rénal
    'kidney': ['HP:0000077', 'HP:0000083'],
    'renal': ['HP:0000077', 'HP:0000083'],
    'nephritis': ['HP:0000123', 'HP:0000077'],
    'cystic': ['HP:0000107', 'HP:0000077'],
    
    # Métabolisme
    'diabetes': ['HP:0000819', 'HP:0001998'],
    'obesity': ['HP:0001513', 'HP:0000819'],
    'metabolic': ['HP:0001939', 'HP:0000819'],
    'growth': ['HP:0001507', 'HP:0004322'],
    'short': ['HP:0004322', 'HP:0001507'],
    'tall': ['HP:0000098', 'HP:0001519'],
    
    # Système immunitaire
    'immune': ['HP:0002715', 'HP:0005406'],
    'immunodeficiency': ['HP:0002721', 'HP:0005406'],
    'autoimmune': ['HP:0002960', 'HP:0002715'],
    
    # Système digestif
    'liver': ['HP:0001392', 'HP:0001394'],
    'hepatic': ['HP:0001392', 'HP:0001394'],
    'pancreatic': ['HP:0001735', 'HP:0001738'],
    'gastrointestinal': ['HP:0011024', 'HP:0002013'],
    
    # Développement
    'skeletal': ['HP:0000924', 'HP:0002652'],
    'bone': ['HP:0000924', 'HP:0002652'],
    'facial': ['HP:0001999', 'HP:0000271'],
    'cleft': ['HP:0000175', 'HP:0001999'],
    
    # Cancer
    'cancer': ['HP:0002664', 'HP:0030731'],
    'tumor': ['HP:0002664', 'HP:0100633'],
    'malignant': ['HP:0002664', 'HP:0030731'],
}

# Mots-clés à ignorer (trop génériques ou non médicaux)
STOP_WORDS = {
    'panel', 'gene', 'genes', 'list', 'testing', 'analysis', 'comprehensive',
    'extended', 'broad', 'focused', 'clinical', 'diagnostic', 'genomic',
    'inherited', 'familial', 'congenital', 'syndrome', 'syndromes',
    'disorder', 'disorders', 'disease', 'diseases', 'condition', 'conditions',
    'defect', 'defects', 'abnormality', 'abnormalities', 'version', 'updated',
    'v1', 'v2', 'v3', 'v4', 'v5', 'australia', 'australian', 'genomics',
    'england', 'primary', 'secondary', 'rare', 'common', 'early', 'late',
    'onset', 'adult', 'paediatric', 'pediatric', 'childhood', 'neonatal'
}

# =============================================================================
# FONCTIONS AMÉLIORÉES POUR EXTRACTION DE MOTS-CLÉS
# =============================================================================

def extract_medical_keywords_enhanced(panel_names):
    """
    Version améliorée de l'extraction de mots-clés médicaux
    """
    if not panel_names:
        return []
    
    keywords = []
    keyword_scores = {}
    
    for name in panel_names:
        if not name:
            continue
        
        # Nettoyage et normalisation
        cleaned_name = name.lower().strip()
        
        # Remplacer les caractères spéciaux par des espaces
        cleaned_name = re.sub(r'[_\-/,;:()&]', ' ', cleaned_name)
        
        # Extraire les mots significatifs
        words = re.findall(r'\b[a-zA-Z]{3,}\b', cleaned_name)
        
        # Traitement des mots
        for word in words:
            if (word not in STOP_WORDS and 
                len(word) >= 3 and 
                not word.isdigit() and
                not re.match(r'^v\d+$', word)):  # Éviter les versions
                
                # Calculer un score basé sur la fréquence et la pertinence
                score = 1
                
                # Bonus si le mot est dans notre mapping médical
                if word in MEDICAL_TO_HPO_MAPPING:
                    score += 5
                
                # Bonus pour les mots plus longs (souvent plus spécifiques)
                if len(word) >= 6:
                    score += 1
                
                # Accumuler les scores
                if word not in keyword_scores:
                    keyword_scores[word] = 0
                keyword_scores[word] += score
    
    # Trier par score décroissant
    sorted_keywords = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Extraire les mots-clés avec les meilleurs scores
    keywords = [word for word, score in sorted_keywords if score >= 2]
    
    return keywords[:8]  # Limiter à 8 mots-clés maximum

# =============================================================================
# RECHERCHE HPO AMÉLIORÉE
# =============================================================================

@lru_cache(maxsize=100)
def search_hpo_with_fallback(query, max_results=3):
    """
    Recherche HPO avec système de fallback amélioré
    """
    results = []
    
    try:
        # 1. Essayer d'abord notre mapping direct
        query_lower = query.lower()
        if query_lower in MEDICAL_TO_HPO_MAPPING:
            mapped_hpo_ids = MEDICAL_TO_HPO_MAPPING[query_lower][:max_results]
            for hpo_id in mapped_hpo_ids:
                try:
                    details = fetch_hpo_term_details_cached(hpo_id)
                    if details and details.get('name'):
                        results.append({
                            'value': hpo_id,
                            'label': f"{details['name']} ({hpo_id})",
                            'keyword': query,
                            'source': 'mapping',
                            'relevance': 10
                        })
                except:
                    continue
        
        # 2. Si pas assez de résultats, chercher via API
        if len(results) < max_results:
            try:
                api_results = search_hpo_via_api(query, max_results - len(results))
                for result in api_results:
                    # Éviter les doublons
                    if not any(r['value'] == result['value'] for r in results):
                        result['source'] = 'api'
                        result['relevance'] = 7
                        results.append(result)
            except Exception as e:
                logger.warning(f"API HPO search failed for '{query}': {e}")
        
        # 3. Si toujours pas assez, essayer des variations du mot
        if len(results) < max_results:
            variations = generate_query_variations(query)
            for variation in variations[:2]:  # Limiter à 2 variations
                try:
                    var_results = search_hpo_via_api(variation, 1)
                    for result in var_results:
                        if not any(r['value'] == result['value'] for r in results):
                            result['source'] = 'variation'
                            result['relevance'] = 5
                            results.append(result)
                            if len(results) >= max_results:
                                break
                except:
                    continue
                
                if len(results) >= max_results:
                    break
    
    except Exception as e:
        logger.error(f"Error in enhanced HPO search for '{query}': {e}")
    
    # Trier par pertinence
    results.sort(key=lambda x: x.get('relevance', 0), reverse=True)
    return results[:max_results]

def search_hpo_via_api(query, limit=5):
    """
    Recherche HPO via l'API JAX avec gestion d'erreurs améliorée
    """
    if not query or len(query.strip()) < 2:
        return []
    
    try:
        url = f"https://ontology.jax.org/api/hp/search"
        params = {
            'q': query.strip(),
            'page': 0,
            'limit': min(limit, 10)
        }
        
        response = requests.get(url, params=params, timeout=8)
        response.raise_for_status()
        
        data = response.json()
        results = []
        
        if 'terms' in data and data['terms']:
            for term in data['terms'][:limit]:
                hpo_id = term.get('id', '')
                hpo_name = term.get('name', '')
                
                if hpo_id and hpo_name:
                    results.append({
                        'value': hpo_id,
                        'label': f"{hpo_name} ({hpo_id})",
                        'keyword': query
                    })
        
        return results
        
    except requests.exceptions.RequestException as e:
        logger.warning(f"HPO API request failed for '{query}': {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in HPO API search for '{query}': {e}")
        return []

def generate_query_variations(query):
    """
    Génère des variations d'un terme de recherche pour améliorer les résultats HPO
    """
    variations = []
    
    # Version singulier/pluriel
    if query.endswith('s') and len(query) > 4:
        variations.append(query[:-1])  # Retirer le 's'
    elif not query.endswith('s'):
        variations.append(query + 's')  # Ajouter un 's'
    
    # Variations communes de terminaisons médicales
    medical_variants = {
        'ic': ['ical', 'y'],  # cardiac -> cardiacal, cardiacu
        'al': ['ic'],         # neural -> neuric
        'ism': ['tic'],       # metabolism -> metabolic
        'ity': ['ic'],        # spasticity -> spastic
        'osis': ['otic'],     # neurosis -> neurotic
        'pathy': ['pathic'],  # neuropathy -> neuropathic
    }
    
    for suffix, replacements in medical_variants.items():
        if query.endswith(suffix):
            base = query[:-len(suffix)]
            for replacement in replacements:
                variations.append(base + replacement)
    
    return variations

# =============================================================================
# FONCTION PRINCIPALE AMÉLIORÉE
# =============================================================================

def search_hpo_terms_by_keywords_enhanced(keywords, max_per_keyword=2):
    """
    Version améliorée de la recherche HPO basée sur les mots-clés
    """
    if not keywords:
        return []
    
    logger.info(f"🔍 Searching HPO terms for keywords: {keywords}")
    
    suggested_hpo_terms = []
    processed_hpo_ids = set()
    
    # Traiter chaque mot-clé
    for keyword in keywords[:6]:  # Limiter à 6 mots-clés pour éviter trop d'appels API
        try:
            # Utiliser notre fonction améliorée
            keyword_results = search_hpo_with_fallback(keyword, max_per_keyword)
            
            for result in keyword_results:
                hpo_id = result['value']
                
                # Éviter les doublons
                if hpo_id not in processed_hpo_ids:
                    processed_hpo_ids.add(hpo_id)
                    suggested_hpo_terms.append(result)
        
        except Exception as e:
            logger.error(f"Error processing keyword '{keyword}': {e}")
            continue
    
    # Trier par pertinence (les résultats du mapping direct en premier)
    suggested_hpo_terms.sort(key=lambda x: (
        x.get('relevance', 0),
        -len(x.get('keyword', ''))  # Préférer les mots-clés plus longs
    ), reverse=True)
    
    logger.info(f"✅ Found {len(suggested_hpo_terms)} HPO suggestions")
    
    return suggested_hpo_terms[:8]  # Retourner maximum 8 suggestions

# =============================================================================
# FONCTIONS MISES À JOUR POUR LE SYSTÈME PRINCIPAL
# =============================================================================

def extract_keywords_from_panel_names(panel_names):
    """
    Version mise à jour qui utilise le système amélioré
    """
    return extract_medical_keywords_enhanced(panel_names)

def search_hpo_terms_by_keywords(keywords, max_per_keyword=2):
    """
    Version mise à jour qui utilise le système amélioré
    """
    return search_hpo_terms_by_keywords_enhanced(keywords, max_per_keyword)

# =============================================================================
# FONCTIONS DE DEBUG ET VALIDATION
# =============================================================================

def validate_hpo_suggestions(panel_names, suggested_hpo_terms):
    """
    Fonction pour valider la qualité des suggestions HPO
    """
    if not panel_names or not suggested_hpo_terms:
        return {"score": 0, "details": "No data to validate"}
    
    validation_score = 0
    details = []
    
    # Extraire les mots-clés des panels
    keywords = extract_medical_keywords_enhanced(panel_names)
    
    for suggestion in suggested_hpo_terms:
        hpo_name = suggestion.get('label', '').lower()
        keyword = suggestion.get('keyword', '').lower()
        
        # Points si le mot-clé apparaît dans le nom HPO
        if keyword in hpo_name:
            validation_score += 2
            details.append(f"✓ '{keyword}' found in '{hpo_name}'")
        
        # Points si c'est un mapping direct
        if suggestion.get('source') == 'mapping':
            validation_score += 3
            details.append(f"✓ Direct mapping for '{keyword}'")
    
    return {
        "score": validation_score,
        "max_possible": len(suggested_hpo_terms) * 3,
        "percentage": (validation_score / max(len(suggested_hpo_terms) * 3, 1)) * 100,
        "details": details
    }

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