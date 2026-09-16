"""
build_updated_app.py
Compiles index.html integrating both the Canonical Knowledge Core (rdso_canonical_kg.json)
and Deep Extracted Dossiers (rdso_extracted_knowledge.json) with Semantic Modes and
Engineering Answer Cards in full compliance with the Knowledge Graph Improvement Blueprint.
"""

import json
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(REPO_ROOT, "data")
ext_path = os.path.join(data_dir, "rdso_extracted_knowledge.json")
can_path = os.path.join(data_dir, "rdso_canonical_kg.json")
man_path = os.path.join(data_dir, "rdso_manuals_knowledge.json")

with open(ext_path, "r", encoding="utf-8") as f:
    extracted_knowledge = json.load(f)

with open(can_path, "r", encoding="utf-8") as f:
    canonical_kg = json.load(f)

manuals_knowledge = {}
if os.path.exists(man_path):
    with open(man_path, "r", encoding="utf-8") as f:
        manuals_knowledge = json.load(f)

extracted_json_str = json.dumps(extracted_knowledge)
canonical_json_str = json.dumps(canonical_kg)
manuals_json_str = json.dumps(manuals_knowledge)

html_template = r'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RDSO Railway Track Knowledge Graph Studio | Intelligent Rail Ontology & Asset Digital Twin</title>
  <style>
    :root {
      --bg-space: #060911;
      --bg-panel: rgba(11, 17, 30, 0.94);
      --bg-card: rgba(18, 27, 46, 0.88);
      --bg-hover: rgba(28, 42, 70, 0.95);
      --border-subtle: rgba(56, 96, 160, 0.35);
      --border-glow: rgba(0, 240, 255, 0.55);
      --border-amber: rgba(255, 214, 10, 0.55);
      --border-crimson: rgba(255, 51, 102, 0.6);
      --text-main: #f0f4fc;
      --text-muted: #8fa0b8;
      --text-dim: #5c6c82;
      --accent-cyan: #00f0ff;
      --accent-green: #00ff88;
      --accent-orange: #ff9d00;
      --accent-purple: #9d4edd;
      --accent-red: #ff3366;
      --accent-yellow: #ffd60a;
      --accent-blue: #3a86ff;
      --accent-pink: #f72585;
      --font-stack: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", Helvetica, Arial, sans-serif;
      --font-mono: "SF Mono", Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      user-select: none;
    }

    body {
      background-color: var(--bg-space);
      color: var(--text-main);
      font-family: var(--font-stack);
      overflow: hidden;
      height: 100vh;
      width: 100vw;
    }

    #kg-canvas-container {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      z-index: 1;
    }

    /* Command Header */
    header {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 64px;
      background: linear-gradient(180deg, rgba(6, 10, 18, 0.96) 0%, rgba(6, 10, 18, 0.75) 100%);
      backdrop-filter: blur(14px);
      border-bottom: 1px solid var(--border-subtle);
      z-index: 10;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 20px;
    }

    .brand-section {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .brand-icon {
      font-size: 26px;
      filter: drop-shadow(0 0 10px var(--accent-cyan));
    }

    .brand-titles h1 {
      font-size: 15px;
      font-weight: 800;
      letter-spacing: 0.5px;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .badge-ver {
      font-size: 9px;
      padding: 2px 7px;
      border-radius: 4px;
      background: rgba(0, 240, 255, 0.18);
      border: 1px solid var(--accent-cyan);
      color: var(--accent-cyan);
      font-family: var(--font-mono);
      font-weight: 700;
    }

    .brand-titles p {
      font-size: 10.5px;
      color: var(--text-muted);
      margin-top: 2px;
    }

    /* Semantic Modes Selector */
    .semantic-modes-bar {
      display: flex;
      align-items: center;
      background: rgba(14, 22, 38, 0.9);
      border: 1px solid var(--border-subtle);
      border-radius: 8px;
      padding: 3px;
      gap: 2px;
    }

    .semantic-mode-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-size: 11px;
      font-weight: 700;
      padding: 6px 12px;
      border-radius: 6px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .semantic-mode-btn:hover {
      color: #fff;
      background: rgba(255, 255, 255, 0.08);
    }

    .semantic-mode-btn.active {
      background: linear-gradient(135deg, rgba(0, 240, 255, 0.25) 0%, rgba(58, 134, 255, 0.3) 100%);
      color: var(--accent-cyan);
      border: 1px solid var(--border-glow);
      box-shadow: 0 0 12px rgba(0, 240, 255, 0.25);
    }

    /* Global Search */
    .search-wrapper {
      position: relative;
      width: 260px;
    }

    .search-input {
      width: 100%;
      height: 34px;
      background: rgba(18, 27, 46, 0.85);
      border: 1px solid var(--border-subtle);
      border-radius: 6px;
      padding: 0 34px 0 32px;
      color: #fff;
      font-size: 11.5px;
      font-family: var(--font-stack);
      outline: none;
      transition: all 0.2s;
    }

    .search-input:focus {
      border-color: var(--accent-cyan);
      box-shadow: 0 0 10px rgba(0, 240, 255, 0.3);
      background: rgba(24, 36, 62, 0.95);
    }

    .search-icon {
      position: absolute;
      left: 10px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 13px;
      color: var(--text-muted);
    }

    .search-shortcut {
      position: absolute;
      right: 10px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 10px;
      background: rgba(255, 255, 255, 0.12);
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 4px;
      padding: 1px 5px;
      color: var(--text-muted);
      font-family: var(--font-mono);
    }

    .search-dropdown {
      position: absolute;
      top: 40px;
      left: 0;
      right: 0;
      background: var(--bg-panel);
      border: 1px solid var(--border-glow);
      border-radius: 6px;
      max-height: 320px;
      overflow-y: auto;
      display: none;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.7);
      z-index: 100;
    }

    .search-item {
      padding: 8px 12px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
      transition: background 0.15s;
    }

    .search-item:hover {
      background: rgba(0, 240, 255, 0.15);
    }

    .search-item-title {
      font-size: 11px;
      font-weight: 600;
      color: #fff;
    }

    .search-item-badge {
      font-size: 9px;
      padding: 2px 6px;
      border-radius: 3px;
      font-family: var(--font-mono);
    }

    /* Layout Switcher */
    .layout-switcher {
      display: flex;
      background: rgba(14, 22, 38, 0.9);
      border: 1px solid var(--border-subtle);
      border-radius: 6px;
      padding: 2px;
      gap: 2px;
    }

    .layout-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-size: 11px;
      font-weight: 600;
      padding: 5px 10px;
      border-radius: 4px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 5px;
      transition: all 0.15s;
    }

    .layout-btn:hover {
      color: #fff;
      background: rgba(255, 255, 255, 0.06);
    }

    .layout-btn.active {
      background: rgba(0, 240, 255, 0.2);
      color: var(--accent-cyan);
      border: 1px solid var(--border-glow);
    }

    /* Actions */
    .header-actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .btn {
      background: rgba(18, 27, 46, 0.9);
      border: 1px solid var(--border-subtle);
      color: var(--text-main);
      padding: 6px 12px;
      font-size: 11px;
      font-weight: 600;
      border-radius: 6px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s;
    }

    .btn:hover {
      background: var(--bg-hover);
      border-color: var(--accent-cyan);
      color: #fff;
    }

    .btn-primary {
      background: linear-gradient(135deg, rgba(0, 240, 255, 0.3) 0%, rgba(58, 134, 255, 0.3) 100%);
      border-color: var(--accent-cyan);
      color: #fff;
    }

    .btn-primary:hover {
      background: linear-gradient(135deg, rgba(0, 240, 255, 0.5) 0%, rgba(58, 134, 255, 0.5) 100%);
      box-shadow: 0 0 15px rgba(0, 240, 255, 0.4);
    }

    /* Left Floating Dock */
    #left-tools-dock {
      position: absolute;
      top: 76px;
      left: 16px;
      width: 250px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      z-index: 5;
    }

    .dock-card {
      background: var(--bg-panel);
      backdrop-filter: blur(16px);
      border: 1px solid var(--border-subtle);
      border-radius: 8px;
      padding: 12px;
      box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
    }

    .card-title {
      font-size: 10px;
      font-weight: 800;
      letter-spacing: 0.8px;
      color: var(--accent-cyan);
      text-transform: uppercase;
      margin-bottom: 8px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .domain-chips-list {
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
    }

    .domain-chip {
      font-size: 9.5px;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 4px;
      cursor: pointer;
      border: 1px solid transparent;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      transition: all 0.15s;
    }

    .domain-chip.active {
      border-color: currentColor;
      box-shadow: 0 0 8px currentColor;
    }

    .domain-chip.dimmed {
      opacity: 0.35;
    }

    /* Alteration Scrubber */
    .scrubber-wrap {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .scrubber-slider {
      width: 100%;
      height: 6px;
      border-radius: 3px;
      background: #182844;
      outline: none;
      accent-color: var(--accent-green);
      cursor: pointer;
    }

    .scrubber-desc {
      font-size: 10px;
      color: var(--text-muted);
      line-height: 1.4;
    }

    /* RIGHT MULTI-TAB ENTITY INTELLIGENCE DRAWER (EXPANDED 490PX) */
    #intelligence-drawer {
      position: absolute;
      top: 64px;
      right: 0;
      bottom: 28px;
      width: 490px;
      background: var(--bg-panel);
      backdrop-filter: blur(20px);
      border-left: 1px solid var(--border-glow);
      box-shadow: -10px 0 40px rgba(0, 0, 0, 0.85);
      z-index: 10;
      display: flex;
      flex-direction: column;
      transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1);
    }

    #intelligence-drawer.collapsed {
      transform: translateX(100%);
    }

    .drawer-header {
      padding: 14px 16px;
      border-bottom: 1px solid var(--border-subtle);
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      background: rgba(6, 10, 18, 0.6);
    }

    .drawer-title-block h2 {
      font-size: 14px;
      font-weight: 800;
      color: #fff;
      line-height: 1.3;
    }

    .drawer-title-block .meta-tag {
      font-size: 9px;
      font-family: var(--font-mono);
      font-weight: 700;
      color: var(--accent-cyan);
      display: inline-block;
      margin-bottom: 4px;
    }

    .close-drawer-btn {
      background: transparent;
      border: 1px solid var(--border-subtle);
      border-radius: 4px;
      color: var(--text-muted);
      font-size: 14px;
      width: 26px;
      height: 26px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.15s;
    }

    .close-drawer-btn:hover {
      border-color: var(--accent-red);
      color: var(--accent-red);
      background: rgba(255, 51, 102, 0.15);
    }

    /* Engineering Answer Card */
    .answer-card-container {
      background: rgba(14, 23, 40, 0.95);
      border-bottom: 1px solid var(--border-subtle);
      padding: 12px 16px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .answer-provenance-box {
      background: rgba(0, 0, 0, 0.4);
      border: 1px solid rgba(0, 240, 255, 0.25);
      border-radius: 6px;
      padding: 8px 10px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }

    .answer-crop-thumb {
      width: 60px;
      height: 40px;
      border-radius: 4px;
      border: 1px solid var(--border-subtle);
      object-fit: cover;
      cursor: pointer;
      transition: transform 0.2s, border-color 0.2s;
    }

    .answer-crop-thumb:hover {
      transform: scale(1.08);
      border-color: var(--accent-cyan);
    }

    .provenance-details {
      flex: 1;
      font-size: 10px;
      line-height: 1.4;
    }

    .confidence-badge {
      font-size: 8.5px;
      padding: 2px 5px;
      border-radius: 3px;
      background: rgba(0, 255, 136, 0.15);
      border: 1px solid var(--accent-green);
      color: var(--accent-green);
      font-weight: 700;
      font-family: var(--font-mono);
      display: inline-flex;
      align-items: center;
      gap: 3px;
    }

    /* Drawer Tab Bar */
    .drawer-nav-tabs {
      display: flex;
      border-bottom: 1px solid var(--border-subtle);
      background: rgba(10, 16, 28, 0.95);
      overflow-x: auto;
    }

    .drawer-tab {
      flex: 1;
      min-width: 85px;
      padding: 10px 4px;
      font-size: 10.5px;
      font-weight: 700;
      color: var(--text-muted);
      background: transparent;
      border: none;
      border-bottom: 2px solid transparent;
      cursor: pointer;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 3px;
      transition: all 0.2s;
    }

    .drawer-tab:hover {
      color: #fff;
      background: rgba(255, 255, 255, 0.04);
    }

    .drawer-tab.active {
      color: var(--accent-cyan);
      border-bottom-color: var(--accent-cyan);
      background: rgba(0, 240, 255, 0.08);
    }

    .drawer-tab-badge {
      font-size: 8.5px;
      padding: 1px 5px;
      border-radius: 8px;
      background: rgba(0, 240, 255, 0.2);
      color: var(--accent-cyan);
      font-family: var(--font-mono);
    }

    .drawer-content {
      flex: 1;
      overflow-y: auto;
      padding: 14px 16px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    .tab-pane {
      display: none;
      flex-direction: column;
      gap: 12px;
    }

    .tab-pane.active {
      display: flex;
    }

    /* Tab 1: Notes Cards */
    .notes-search-box {
      position: relative;
      width: 100%;
    }

    .notes-search-input {
      width: 100%;
      height: 32px;
      background: rgba(18, 27, 46, 0.9);
      border: 1px solid var(--border-subtle);
      border-radius: 6px;
      padding: 0 10px 0 28px;
      color: #fff;
      font-size: 11px;
      outline: none;
    }

    .notes-search-input:focus {
      border-color: var(--accent-yellow);
    }

    .notes-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
      max-height: 480px;
      overflow-y: auto;
    }

    .note-card {
      background: rgba(18, 27, 46, 0.7);
      border: 1px solid var(--border-subtle);
      border-left: 3px solid var(--accent-yellow);
      border-radius: 4px;
      padding: 9px 11px;
      display: flex;
      flex-direction: column;
      gap: 4px;
      font-size: 11px;
      line-height: 1.45;
    }

    .note-card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .note-badge {
      font-size: 9px;
      font-family: var(--font-mono);
      font-weight: 800;
      color: var(--accent-yellow);
    }

    .note-dwg-ref {
      font-size: 8.5px;
      color: var(--text-dim);
      font-family: var(--font-mono);
    }

    .note-body {
      color: var(--text-main);
    }

    /* Tab 2: Tables View */
    .table-subnav {
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
      margin-bottom: 8px;
    }

    .table-subnav-btn {
      background: rgba(18, 27, 46, 0.8);
      border: 1px solid var(--border-subtle);
      border-radius: 4px;
      padding: 4px 8px;
      font-size: 9.5px;
      font-weight: 700;
      color: var(--text-muted);
      cursor: pointer;
    }

    .table-subnav-btn.active {
      border-color: var(--accent-green);
      background: rgba(0, 255, 136, 0.15);
      color: var(--accent-green);
    }

    .data-table-wrap {
      max-height: 440px;
      overflow-y: auto;
      border: 1px solid var(--border-subtle);
      border-radius: 4px;
    }

    .rdso-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 10.5px;
    }

    .rdso-table th {
      position: sticky;
      top: 0;
      background: #0f1828;
      color: var(--accent-cyan);
      font-weight: 700;
      text-align: left;
      padding: 7px 9px;
      border-bottom: 1px solid var(--border-subtle);
      font-size: 9.5px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .rdso-table td {
      padding: 6px 9px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      color: var(--text-main);
    }

    .rdso-table tr:hover {
      background: rgba(0, 240, 255, 0.08);
    }

    /* Tab 3: Blueprint Viewer */
    .blueprint-controls {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 6px;
    }

    .blueprint-crop-select {
      background: rgba(18, 27, 46, 0.9);
      border: 1px solid var(--border-subtle);
      border-radius: 4px;
      padding: 4px 8px;
      color: #fff;
      font-size: 10px;
      outline: none;
    }

    .blueprint-preview-box {
      border: 1px solid var(--border-glow);
      border-radius: 6px;
      overflow: hidden;
      background: #000;
      position: relative;
      cursor: zoom-in;
    }

    .blueprint-img {
      width: 100%;
      height: 240px;
      object-fit: contain;
      display: block;
      background: #050810;
    }

    .blueprint-overlay-hint {
      position: absolute;
      bottom: 8px;
      right: 8px;
      background: rgba(0, 0, 0, 0.8);
      border: 1px solid var(--border-glow);
      border-radius: 4px;
      padding: 3px 8px;
      font-size: 9px;
      color: var(--accent-cyan);
    }

    /* Tab 4: 3D Twin */
    .digital-twin-box {
      background: rgba(6, 10, 18, 0.85);
      border: 1px solid var(--border-subtle);
      border-radius: 6px;
      padding: 8px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .twin-badge {
      font-size: 9px;
      font-family: var(--font-mono);
      color: var(--accent-cyan);
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .twin-canvas-wrap {
      width: 100%;
      height: 200px;
      border-radius: 4px;
      overflow: hidden;
      background: #03060d;
      border: 1px solid rgba(0, 240, 255, 0.2);
    }

    .twin-controls-hint {
      font-size: 9px;
      color: var(--text-dim);
      text-align: center;
    }

    .specs-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 10.5px;
    }

    .specs-table td {
      padding: 5px 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }

    .specs-table td:first-child {
      color: var(--text-muted);
      width: 45%;
    }

    .specs-table td:last-child {
      font-weight: 700;
      color: #fff;
    }

    /* Lineage Tags */
    .lineage-tags-list {
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
    }

    .lineage-tag {
      background: rgba(0, 240, 255, 0.1);
      border: 1px solid rgba(0, 240, 255, 0.3);
      border-radius: 4px;
      padding: 3px 7px;
      font-size: 9.5px;
      color: #fff;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      cursor: pointer;
    }

    .lineage-tag:hover {
      background: rgba(0, 240, 255, 0.25);
      border-color: var(--accent-cyan);
    }

    /* Tab 5: Risks & Failure */
    .failure-risk-box {
      background: rgba(255, 51, 102, 0.12);
      border: 1px solid var(--border-crimson);
      border-radius: 6px;
      padding: 10px;
    }

    .failure-risk-header {
      font-size: 11px;
      font-weight: 800;
      color: var(--accent-red);
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 4px;
    }

    .failure-risk-desc {
      font-size: 10.5px;
      color: var(--text-main);
      line-height: 1.4;
    }

    /* Bottom Telemetry Bar */
    #telemetry-bar {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      height: 28px;
      background: rgba(6, 10, 18, 0.95);
      border-top: 1px solid var(--border-subtle);
      z-index: 10;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 16px;
      font-size: 10px;
      color: var(--text-muted);
      font-family: var(--font-mono);
    }

    .telemetry-item {
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .status-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--accent-green);
      box-shadow: 0 0 8px var(--accent-green);
    }

    /* Fullscreen Modal */
    #blueprint-modal {
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background: rgba(0, 0, 0, 0.92);
      backdrop-filter: blur(12px);
      z-index: 1000;
      display: none;
      flex-direction: column;
      padding: 24px;
    }

    .blueprint-modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }

    .blueprint-modal-body {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: auto;
    }

    .blueprint-modal-img {
      max-width: 95%;
      max-height: 90vh;
      object-fit: contain;
      box-shadow: 0 0 35px rgba(0, 240, 255, 0.25);
      border-radius: 6px;
    }
  </style>
  <script src="./lib/three.min.js"></script>
  <script src="./lib/OrbitControls.js"></script>
</head>
<body>

  <!-- Fullscreen 3D Knowledge Graph Viewport -->
  <div id="kg-canvas-container"></div>

  <!-- Command Header -->
  <header>
    <div class="brand-section">
      <div class="brand-icon">🌐</div>
      <div class="brand-titles">
        <h1>RDSO Track Knowledge Graph Studio <span class="badge-ver">v3.5 CANONICAL</span></h1>
        <p>Revision-Aware Ontology & Deep Blueprint Extraction</p>
      </div>
    </div>

    <!-- Semantic Graph Modes Switcher -->
    <div class="semantic-modes-bar">
      <button class="semantic-mode-btn active" data-mode="explore" onclick="switchSemanticMode('explore')">
        <span>🌌</span> Explore
      </button>
      <button class="semantic-mode-btn" data-mode="trace" onclick="switchSemanticMode('trace')">
        <span>🔗</span> Dependency Trace
      </button>
      <button class="semantic-mode-btn" data-mode="revision" onclick="switchSemanticMode('revision')">
        <span>⏳</span> Revision Impact
      </button>
      <button class="semantic-mode-btn" data-mode="failure" onclick="switchSemanticMode('failure')">
        <span>⚠️</span> Failure Analysis
      </button>
      <button class="semantic-mode-btn" data-mode="bom" onclick="switchSemanticMode('bom')">
        <span>📦</span> Procurement & BOM
      </button>
      <button class="semantic-mode-btn" data-mode="manuals" onclick="switchSemanticMode('manuals')">
        <span>📖</span> Codes & Manuals
      </button>
    </div>

    <!-- Global Search -->
    <div class="search-wrapper">
      <span class="search-icon">🔍</span>
      <input type="text" id="global-search" class="search-input" placeholder="Search notes, BOM, sleepers, specs...">
      <span class="search-shortcut">/</span>
      <div id="search-dropdown" class="search-dropdown"></div>
    </div>

    <!-- Layout Switcher -->
    <div class="layout-switcher">
      <button class="layout-btn active" data-layout="cosmic" onclick="switchGraphLayout('cosmic')">
        <span>🌌</span> 3D Cosmic
      </button>
      <button class="layout-btn" data-layout="planar" onclick="switchGraphLayout('planar')">
        <span>📐</span> 2D Planar
      </button>
      <button class="layout-btn" data-layout="dag" onclick="switchGraphLayout('dag')">
        <span>🌲</span> Hierarchical
      </button>
      <button class="layout-btn" data-layout="concentric" onclick="switchGraphLayout('concentric')">
        <span>🎯</span> Concentric
      </button>
    </div>

    <!-- Header Actions -->
    <div class="header-actions">
      <button class="btn" onclick="exportGraph('cypher')">
        <span>💾</span> Cypher
      </button>
      <button class="btn btn-primary" onclick="openIngestModal()">
        <span>➕</span> Ingest Node
      </button>
    </div>
  </header>

  <!-- Left Floating Dock -->
  <div id="left-tools-dock">
    <!-- Domain Filters -->
    <div class="dock-card">
      <div class="card-title">
        <span>Ontology Domains</span>
        <span style="font-size: 9px; color: var(--text-dim);" id="domain-active-label">ALL</span>
      </div>
      <div class="domain-chips-list" id="domain-chips-list">
        <!-- Rendered dynamically -->
      </div>
    </div>

    <!-- Alteration Scrubber -->
    <div class="dock-card">
      <div class="card-title">
        <span>Alteration Time-Travel</span>
        <span style="font-size: 9px; color: var(--accent-green); font-family: var(--font-mono);" id="alt-tag-display">ALT 13 (LATEST)</span>
      </div>
      <div class="scrubber-wrap">
        <input type="range" min="1" max="13" value="13" class="scrubber-slider" id="alt-slider" oninput="onAlterationScrub(this.value)">
        <div class="scrubber-desc" id="alt-desc-display">
          Showing complete active track architecture including Note 25/26 dowels, LIST-A spares, and Thick-Web ZU-1-60 profiles.
        </div>
      </div>
    </div>

    <!-- Mode Details Card -->
    <div class="dock-card">
      <div class="card-title">
        <span>Active Semantic Mode</span>
        <span style="font-size: 9px; color: var(--accent-cyan);" id="mode-active-indicator">EXPLORE</span>
      </div>
      <div style="font-size: 10.5px; color: var(--text-muted); line-height: 1.4;" id="mode-active-desc">
        Holistic exploration mode. Left drag to orbit, right drag to pan, scroll to zoom. Click any node to open its Engineering Answer Card.
      </div>
    </div>
  </div>

  <!-- RIGHT MULTI-TAB ENTITY INTELLIGENCE DRAWER -->
  <div id="intelligence-drawer" class="collapsed">
    <div class="drawer-header">
      <div class="drawer-title-block">
        <div class="meta-tag" id="drawer-domain">COMPONENT ENTITY</div>
        <h2 id="drawer-title">Select Any 3D Node</h2>
      </div>
      <button class="close-drawer-btn" onclick="toggleIntelligenceDrawer(false)">✕</button>
    </div>

    <!-- Engineering Answer Card (Executive Summary & Evidence Provenance) -->
    <div class="answer-card-container" id="drawer-answer-card">
      <div style="font-size: 11px; color: var(--text-main); line-height: 1.4;" id="answer-card-desc">
        Click any entity in the 3D canvas or search above to view its canonical facts, governing directives, and source evidence.
      </div>
      <div class="answer-provenance-box" id="answer-provenance-box" style="display: none;">
        <img id="answer-crop-thumb" class="answer-crop-thumb" src="" alt="Evidence Crop" onclick="openFullscreenActiveBlueprint()">
        <div class="provenance-details">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
            <span style="font-weight: 700; color: #fff;" id="prov-dwg-title">RDSO/T-6155</span>
            <span class="confidence-badge">✓ 100% VERIFIED</span>
          </div>
          <div style="color: var(--text-muted); font-size: 9.5px;" id="prov-meta-line">Rev: ALT 13 | Region: General Notes</div>
          <div style="color: var(--accent-cyan); font-size: 9px; cursor: pointer; margin-top: 2px;" onclick="openFullscreenActiveBlueprint()">🔍 Inspect Source Crop</div>
        </div>
      </div>
    </div>

    <!-- Multi-Tab Navigation Bar -->
    <div class="drawer-nav-tabs">
      <button class="drawer-tab active" data-tab="notes" onclick="switchDrawerTab('notes')">
        <span>📑</span> Notes <span class="drawer-tab-badge" id="notes-tab-count">28</span>
      </button>
      <button class="drawer-tab" data-tab="tables" onclick="switchDrawerTab('tables')">
        <span>📊</span> Tables & BOM
      </button>
      <button class="drawer-tab" data-tab="blueprint" onclick="switchDrawerTab('blueprint')">
        <span>🔍</span> Blueprint View
      </button>
      <button class="drawer-tab" data-tab="twin" onclick="switchDrawerTab('twin')">
        <span>📦</span> 3D Asset Twin
      </button>
      <button class="drawer-tab" data-tab="risks" onclick="switchDrawerTab('risks')">
        <span>⚠️</span> Risks & SOPs
      </button>
    </div>

    <div class="drawer-content">
      <!-- 1. TAB: GENERAL NOTES & DIRECTIVES -->
      <div class="tab-pane active" id="tab-pane-notes">
        <div class="notes-search-box">
          <input type="text" id="notes-filter-input" class="notes-search-input" placeholder="Search verbatim notes (e.g. dowel, epoxy, 10%, versine)..." oninput="filterCurrentNotes(this.value)">
        </div>
        <div class="notes-list" id="drawer-notes-list">
          <!-- Populated dynamically -->
        </div>
      </div>

      <!-- 2. TAB: ENGINEERING TABLES & SCHEDULES -->
      <div class="tab-pane" id="tab-pane-tables">
        <div class="table-subnav" id="drawer-table-subnav">
          <!-- Dynamically populated table buttons -->
        </div>
        <div class="data-table-wrap" id="drawer-table-content">
          <!-- Active Table Rendered Here -->
        </div>
      </div>

      <!-- 3. TAB: BLUEPRINT SOURCE CROP VIEWER -->
      <div class="tab-pane" id="tab-pane-blueprint">
        <div class="blueprint-controls">
          <label style="font-size: 10px; font-weight: 700; color: var(--text-muted); text-transform: uppercase;">Source Drawing Region:</label>
          <select class="blueprint-crop-select" id="blueprint-crop-select" onchange="changeActiveBlueprintCrop(this.value)">
            <!-- Options populated dynamically -->
          </select>
        </div>
        <div class="blueprint-preview-box" onclick="openFullscreenActiveBlueprint()">
          <img id="blueprint-crop-img" class="blueprint-img" src="" alt="RDSO Blueprint Crop">
          <div class="blueprint-overlay-hint">🔍 Click to Expand High-Res</div>
        </div>
      </div>

      <!-- 4. TAB: EMBEDDED 3D PHYSICAL DIGITAL TWIN -->
      <div class="tab-pane" id="tab-pane-twin">
        <div class="digital-twin-box" id="twin-box">
          <div class="twin-badge">
            <span>📦</span> <span id="twin-badge-text">PHYSICAL 3D ASSET TWIN</span>
          </div>
          <div class="twin-canvas-wrap">
            <canvas id="component-twin-canvas"></canvas>
          </div>
          <div class="twin-controls-hint">🖱️ Left Drag: Rotate | Right Drag: Pan | Scroll: Zoom</div>
        </div>

        <div>
          <div class="card-title">Engineering Parameters & Specifications</div>
          <table class="specs-table" id="drawer-specs-table"></table>
        </div>

        <div>
          <div class="card-title">Typed Connected Hops</div>
          <div class="lineage-tags-list" id="drawer-lineage-list"></div>
        </div>
      </div>

      <!-- 5. TAB: RISKS & FIELD SOPS -->
      <div class="tab-pane" id="tab-pane-risks">
        <div class="failure-risk-box" id="drawer-risk-box">
          <div class="failure-risk-header">
            <span>⚠️</span> <span id="drawer-risk-title">High Derailment Risk Mode</span>
          </div>
          <div class="failure-risk-desc" id="drawer-risk-desc">
            Select an entity to review tethered failure mechanisms and preventative maintenance actions.
          </div>
        </div>
        <div>
          <div class="card-title">Governing Standard Specifications</div>
          <div style="font-size: 11.5px; color: var(--text-muted); line-height: 1.5;" id="drawer-sop-text">
            Mandatory compliance with IRS: T 10 (Curved Switches) and IRS: T 29 (Cast Manganese Steel Crossings).
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Bottom Telemetry Bar -->
  <div id="telemetry-bar">
    <div class="telemetry-item">
      <div class="status-dot"></div>
      <span>ONTOLOGY CORE: ONLINE</span>
    </div>
    <div class="telemetry-item">
      <span>ENTITIES: <strong id="telem-nodes" style="color: #fff;">0</strong></span>
      <span style="color: var(--border-subtle);">|</span>
      <span>TYPED EDGES: <strong id="telem-edges" style="color: #fff;">0</strong></span>
      <span style="color: var(--border-subtle);">|</span>
      <span>FACTS: <strong id="telem-facts" style="color: var(--accent-green);">0</strong></span>
    </div>
    <div class="telemetry-item">
      <span>SIM: <span id="telem-sim" style="color: var(--accent-green);">LIVE 60 FPS</span></span>
    </div>
  </div>

  <!-- Fullscreen Blueprint Modal -->
  <div id="blueprint-modal">
    <div class="blueprint-modal-header">
      <h3 style="font-size: 14px; color: #fff;" id="blueprint-modal-title">RDSO High-Resolution Blueprint Source Crop</h3>
      <button class="close-drawer-btn" onclick="closeFullscreenBlueprint()">✕</button>
    </div>
    <div class="blueprint-modal-body">
      <img id="blueprint-modal-img" class="blueprint-modal-img" src="" alt="RDSO Blueprint Full Resolution">
    </div>
  </div>

  <!-- Ingest Node Modal -->
  <div id="ingest-modal" style="display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.8); z-index: 1000; align-items: center; justify-content: center;">
    <div style="background: var(--bg-panel); border: 1px solid var(--border-glow); border-radius: 8px; padding: 20px; width: 440px; display: flex; flex-direction: column; gap: 12px;">
      <h3 style="font-size: 14px; color: #fff;">➕ Ingest New Knowledge Entity</h3>
      <div>
        <label style="font-size: 10px; color: var(--text-muted);">Entity Label</label>
        <input type="text" id="in-node-title" style="width: 100%; height: 32px; background: #0c1424; border: 1px solid var(--border-subtle); color: #fff; padding: 0 8px; border-radius: 4px;">
      </div>
      <div>
        <label style="font-size: 10px; color: var(--text-muted);">Ontology Domain</label>
        <select id="in-node-domain" style="width: 100%; height: 32px; background: #0c1424; border: 1px solid var(--border-subtle); color: #fff; padding: 0 8px; border-radius: 4px;">
          <option value="component">COMPONENT</option>
          <option value="specification">SPECIFICATION</option>
          <option value="defect">DEFECT</option>
          <option value="sop">SOP</option>
        </select>
      </div>
      <div>
        <label style="font-size: 10px; color: var(--text-muted);">Parent Entity</label>
        <select id="in-node-parent" style="width: 100%; height: 32px; background: #0c1424; border: 1px solid var(--border-subtle); color: #fff; padding: 0 8px; border-radius: 4px;"></select>
      </div>
      <div>
        <label style="font-size: 10px; color: var(--text-muted);">Description</label>
        <textarea id="in-node-desc" rows="3" style="width: 100%; background: #0c1424; border: 1px solid var(--border-subtle); color: #fff; padding: 8px; border-radius: 4px;"></textarea>
      </div>
      <div style="display: flex; justify-content: flex-end; gap: 8px;">
        <button class="btn" onclick="closeIngestModal()">Cancel</button>
        <button class="btn btn-primary" onclick="submitIngestNode()">Submit Entity</button>
      </div>
    </div>
  </div>

  <!-- APPLICATION LOGIC & CANONICAL KNOWLEDGE GRAPH -->
  <script>
    // Injected Canonical Knowledge Core, Extracted Dossiers, and Railway Manuals
    const RDSO_EXTRACTED_KNOWLEDGE = __EXTRACTED_KNOWLEDGE_JSON__;
    const CANONICAL_DATA = __CANONICAL_KG_JSON__;
    const RDSO_MANUALS_KNOWLEDGE = __MANUALS_KNOWLEDGE_JSON__;
    window.RDSO_MANUALS_KNOWLEDGE = RDSO_MANUALS_KNOWLEDGE;

    const rawKGNodes = CANONICAL_DATA.entities;
    const rawKGEdges = CANONICAL_DATA.edges;
    const rawKGFacts = CANONICAL_DATA.facts || [];

    const DOMAIN_METADATA = {
      drawing: { label: "Drawings & Blueprints", color: "#00f0ff", icon: "📐" },
      revision: { label: "Revisions & History", color: "#a2d2ff", icon: "⏳" },
      component: { label: "Components & Assemblies", color: "#00ff88", icon: "⚙️" },
      turnout_layout: { label: "Sleepers & Layout Zones", color: "#72efdd", icon: "🛤️" },
      specification: { label: "Directives, Notes & Tolerances", color: "#ffd60a", icon: "🔬" },
      materials: { label: "Materials & Metallurgy", color: "#b5179e", icon: "🧪" },
      standards: { label: "Governing Standards", color: "#7209b7", icon: "📜" },
      procurement: { label: "BOM & LIST-A Spares", color: "#f72585", icon: "📦" },
      signaling: { label: "S&T Point Interlocking", color: "#ff3366", icon: "⚡" },
      defect: { label: "Failure Modes & Hazards", color: "#d90429", icon: "⚠️" },
      sop: { label: "Field SOPs & Protocols", color: "#9d4edd", icon: "📋" },
      manual: { label: "Codes & Manuals", color: "#ff007f", icon: "📖" },
      tolerance: { label: "Tolerances & Limits", color: "#fee440", icon: "📏" },
      equipment: { label: "Tools & Equipment", color: "#f15bb5", icon: "🛠️" }
    };

    const PREDICATE_COLORS = {
      CONTAINS: 0x00f0ff,
      HAS_NOTE: 0xffbe0b,
      HAS_REVISION: 0xa2d2ff,
      SUPERSEDES: 0x3a86ff,
      SPECIFIES: 0xffd60a,
      GOVERNS: 0x9d4edd,
      REQUIRES: 0xb5179e,
      INTERFACES_WITH: 0x00ff88,
      INSTALLED_ON: 0x72efdd,
      CONNECTED_TO: 0x00ff88,
      FASTENED_BY: 0x48cae4,
      CONTAINS_SLEEPER: 0x72efdd,
      APPLIES_TO: 0x00f0ff,
      HAS_BOM_ITEM: 0xf72585,
      HAS_SPARE: 0xf72585,
      CAN_CAUSE: 0xff3366,
      MITIGATED_BY: 0x00ff88,
      INTRODUCED_IN: 0xa2d2ff,
      REFERENCES: 0x00f0ff,
      INSPECTED_BY: 0x00f5d4,
      MAINTAINED_BY: 0x00f5d4
    };

    // Global State
    let kgScene, kgCamera, kgRenderer, kgControls;
    let kgPhysicsNodes = [];
    let kgPhysicsEdges = [];
    let currentLayout = "cosmic";
    let currentSemanticMode = "explore";
    let currentSelectedNode = null;
    let currentActiveDossier = null;
    let currentActiveCrop = null;
    let activeFilterDomain = "all";
    let activeAlterationLevel = 13;
    let isPhysicsPaused = false;

    // Simulation Physics Parameters
    let k_repulsion = 60.0;
    let k_spring = 0.05;
    let l0_spring = 5.0;
    let damping = 0.88;

    function initKnowledgeGraphApp() {
      const container = document.getElementById('kg-canvas-container');
      const w = window.innerWidth;
      const h = window.innerHeight;

      // 1. Scene & Atmosphere
      kgScene = new THREE.Scene();
      kgScene.background = new THREE.Color(0x060911);
      kgScene.fog = new THREE.FogExp2(0x060911, 0.012);

      // Starfield
      const starGeo = new THREE.BufferGeometry();
      const starPos = new Float32Array(800 * 3);
      for (let i = 0; i < 800 * 3; i += 3) {
        starPos[i] = (Math.random() - 0.5) * 160;
        starPos[i + 1] = (Math.random() - 0.5) * 160;
        starPos[i + 2] = (Math.random() - 0.5) * 160;
      }
      starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
      const starMat = new THREE.PointsMaterial({ color: 0x304466, size: 0.8, transparent: true, opacity: 0.65 });
      kgScene.add(new THREE.Points(starGeo, starMat));

      // 2. Camera & Orbit Controls
      kgCamera = new THREE.PerspectiveCamera(45, w / h, 0.1, 1000);
      kgCamera.position.set(0, 16, 36);

      kgRenderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
      kgRenderer.setSize(w, h);
      kgRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      container.appendChild(kgRenderer.domElement);

      kgControls = new THREE.OrbitControls(kgCamera, kgRenderer.domElement);
      kgControls.enableDamping = true;
      kgControls.dampingFactor = 0.06;
      kgControls.maxDistance = 140;
      kgControls.minDistance = 3;

      // 3. Lighting
      kgScene.add(new THREE.AmbientLight(0xffffff, 0.95));

      const dir1 = new THREE.DirectionalLight(0x00f0ff, 1.2);
      dir1.position.set(20, 40, 30);
      kgScene.add(dir1);

      const dir2 = new THREE.DirectionalLight(0x9d4edd, 0.8);
      dir2.position.set(-20, -30, -20);
      kgScene.add(dir2);

      // 4. Ingest Canonical Entities & Edges
      rawKGNodes.forEach(n => addNodeToGraph(n));
      rawKGEdges.forEach(e => addEdgeToGraph(e));

      // 5. Initialize UI
      renderDomainChips();
      populateParentSelect();
      initSearchAutocomplete();
      initComponentTwinViewer();
      updateTelemetryCounters();

      // 6. Animation Loop
      function animate() {
        requestAnimationFrame(animate);
        if (!isPhysicsPaused) stepGraphPhysics();
        kgControls.update();
        kgRenderer.render(kgScene, kgCamera);
      }
      animate();

      // 7. Raycasting for Clicking Nodes
      setupRaycasting();

      // 8. Resize Listener
      window.addEventListener('resize', onWindowResize);
    }

    function createBillboardSprite(text, color, domain) {
      const canvas = document.createElement('canvas');
      canvas.width = 280;
      canvas.height = 76;
      const ctx = canvas.getContext('2d');

      ctx.fillStyle = "rgba(6, 10, 18, 0.90)";
      ctx.strokeStyle = color;
      ctx.lineWidth = 3;

      const r = 12;
      ctx.beginPath();
      ctx.moveTo(r, 0);
      ctx.lineTo(280 - r, 0);
      ctx.quadraticCurveTo(280, 0, 280, r);
      ctx.lineTo(280, 76 - r);
      ctx.quadraticCurveTo(280, 76, 280 - r, 76);
      ctx.lineTo(r, 76);
      ctx.quadraticCurveTo(0, 76, 0, 76 - r);
      ctx.lineTo(0, r);
      ctx.quadraticCurveTo(0, 0, r, 0);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = color;
      ctx.font = "bold 14px -apple-system, sans-serif";
      ctx.fillText((DOMAIN_METADATA[domain]?.label || domain).toUpperCase().slice(0, 26), 14, 26);

      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 17px -apple-system, sans-serif";
      const displayLabel = text.length > 22 ? text.substring(0, 21) + "…" : text;
      ctx.fillText(displayLabel, 14, 56);

      const texture = new THREE.CanvasTexture(canvas);
      texture.minFilter = THREE.LinearFilter;
      const spriteMat = new THREE.SpriteMaterial({ map: texture, transparent: true });
      const sprite = new THREE.Sprite(spriteMat);
      sprite.scale.set(4.2, 1.15, 1.0);
      sprite.position.y = 1.35;
      return sprite;
    }

    function addNodeToGraph(data) {
      const nodeGroup = new THREE.Group();
      let coreMesh;
      const colorObj = new THREE.Color(data.color);

      if (data.type === "DRAWING") {
        const sphereGeo = new THREE.SphereGeometry(0.75, 24, 24);
        const sphereMat = new THREE.MeshStandardMaterial({ color: colorObj, emissive: colorObj, emissiveIntensity: 0.55, metalness: 0.8, roughness: 0.2 });
        coreMesh = new THREE.Mesh(sphereGeo, sphereMat);
        nodeGroup.add(coreMesh);

        const ringGeo = new THREE.RingGeometry(1.0, 1.25, 32);
        const ringMat = new THREE.MeshBasicMaterial({ color: colorObj, side: THREE.DoubleSide, transparent: true, opacity: 0.45 });
        const ringMesh = new THREE.Mesh(ringGeo, ringMat);
        ringMesh.rotation.x = Math.PI / 2.5;
        nodeGroup.add(ringMesh);
      } else if (data.type === "REVISION") {
        const octGeo = new THREE.OctahedronGeometry(0.65, 0);
        const octMat = new THREE.MeshStandardMaterial({ color: colorObj, emissive: colorObj, emissiveIntensity: 0.6, metalness: 0.5, roughness: 0.2 });
        coreMesh = new THREE.Mesh(octGeo, octMat);
        nodeGroup.add(coreMesh);
      } else if (data.type === "NOTE") {
        const boxGeo = new THREE.BoxGeometry(0.85, 0.65, 0.4);
        const boxMat = new THREE.MeshStandardMaterial({ color: colorObj, emissive: colorObj, emissiveIntensity: 0.6, metalness: 0.4, roughness: 0.3 });
        coreMesh = new THREE.Mesh(boxGeo, boxMat);
        nodeGroup.add(coreMesh);
      } else if (data.type === "ZONE" || data.type === "SLEEPER") {
        const cylGeo = new THREE.CylinderGeometry(0.4, 0.5, 0.7, 8);
        const cylMat = new THREE.MeshStandardMaterial({ color: colorObj, emissive: colorObj, emissiveIntensity: 0.5, metalness: 0.6, roughness: 0.3 });
        coreMesh = new THREE.Mesh(cylGeo, cylMat);
        nodeGroup.add(coreMesh);
      } else if (data.domain === "defect" || data.type === "FAILURE_MODE" || data.type === "HAZARD") {
        const octGeo = new THREE.OctahedronGeometry(0.7, 0);
        const octMat = new THREE.MeshStandardMaterial({ color: colorObj, emissive: colorObj, emissiveIntensity: 0.75, metalness: 0.3, roughness: 0.2 });
        coreMesh = new THREE.Mesh(octGeo, octMat);
        nodeGroup.add(coreMesh);
      } else {
        const sphereGeo = new THREE.SphereGeometry(0.55, 24, 24);
        const sphereMat = new THREE.MeshStandardMaterial({ color: colorObj, emissive: colorObj, emissiveIntensity: 0.45, metalness: 0.7, roughness: 0.25 });
        coreMesh = new THREE.Mesh(sphereGeo, sphereMat);
        nodeGroup.add(coreMesh);
      }

      const sprite = createBillboardSprite(data.label, data.color, data.domain);
      nodeGroup.add(sprite);

      const initX = data.x !== undefined ? data.x : (Math.random() - 0.5) * 20;
      const initY = data.y !== undefined ? data.y : (Math.random() - 0.5) * 12;
      const initZ = data.z !== undefined ? data.z : (Math.random() - 0.5) * 20;

      nodeGroup.position.set(initX, initY, initZ);
      kgScene.add(nodeGroup);

      const nodeObj = {
        data: data,
        group: nodeGroup,
        mesh: coreMesh,
        sprite: sprite,
        x: initX,
        y: initY,
        z: initZ,
        vx: 0,
        vy: 0,
        vz: 0,
        targetX: initX,
        targetY: initY,
        targetZ: initZ
      };

      kgPhysicsNodes.push(nodeObj);
      return nodeObj;
    }

    function addEdgeToGraph(edgeData) {
      const predColor = PREDICATE_COLORS[edgeData.rel] || 0x00f0ff;
      const lineMat = new THREE.LineBasicMaterial({ color: predColor, transparent: true, opacity: 0.45, linewidth: 1.5 });
      const dummyGeo = new THREE.BufferGeometry();
      const lineMesh = new THREE.Line(dummyGeo, lineMat);
      kgScene.add(lineMesh);

      kgPhysicsEdges.push({
        from: edgeData.from,
        to: edgeData.to,
        rel: edgeData.rel,
        line: lineMesh,
        color: predColor
      });
    }

    // Force Simulation
    function stepGraphPhysics() {
      if (currentLayout === "cosmic") stepCosmicForces();
      else if (currentLayout === "planar") stepPlanarForces();
      else interpolateToTargets();

      kgPhysicsNodes.forEach(n => n.group.position.set(n.x, n.y, n.z));

      kgPhysicsEdges.forEach(e => {
        const n1 = kgPhysicsNodes.find(n => n.data.id === e.from);
        const n2 = kgPhysicsNodes.find(n => n.data.id === e.to);
        if (n1 && n2 && n1.group.visible && n2.group.visible) {
          e.line.visible = true;
          const posArr = new Float32Array([n1.x, n1.y, n1.z, n2.x, n2.y, n2.z]);
          e.line.geometry.setAttribute('position', new THREE.BufferAttribute(posArr, 3));
          e.line.geometry.attributes.position.needsUpdate = true;
        } else {
          e.line.visible = false;
        }
      });
    }

    function stepCosmicForces() {
      const numNodes = kgPhysicsNodes.length;

      for (let i = 0; i < numNodes; i++) {
        const n1 = kgPhysicsNodes[i];
        if (!n1.group.visible) continue;

        for (let j = i + 1; j < numNodes; j++) {
          const n2 = kgPhysicsNodes[j];
          if (!n2.group.visible) continue;

          const dx = n2.x - n1.x;
          const dy = n2.y - n1.y;
          const dz = n2.z - n1.z;
          const d2 = dx * dx + dy * dy + dz * dz + 0.05;
          const d = Math.sqrt(d2);

          const force = k_repulsion / d2;
          const fx = (dx / d) * force;
          const fy = (dy / d) * force;
          const fz = (dz / d) * force;

          n1.vx -= fx * 0.016;
          n1.vy -= fy * 0.016;
          n1.vz -= fz * 0.016;

          n2.vx += fx * 0.016;
          n2.vy += fy * 0.016;
          n2.vz += fz * 0.016;
        }
      }

      kgPhysicsEdges.forEach(e => {
        const n1 = kgPhysicsNodes.find(n => n.data.id === e.from);
        const n2 = kgPhysicsNodes.find(n => n.data.id === e.to);
        if (!n1 || !n2 || !n1.group.visible || !n2.group.visible) return;

        const dx = n2.x - n1.x;
        const dy = n2.y - n1.y;
        const dz = n2.z - n1.z;
        const d = Math.sqrt(dx * dx + dy * dy + dz * dz) || 0.001;
        const displacement = d - l0_spring;
        const force = k_spring * displacement;

        const fx = (dx / d) * force;
        const fy = (dy / d) * force;
        const fz = (dz / d) * force;

        n1.vx += fx * 0.016;
        n1.vy += fy * 0.016;
        n1.vz += fz * 0.016;

        n2.vx -= fx * 0.016;
        n2.vy -= fy * 0.016;
        n2.vz -= fz * 0.016;
      });

      kgPhysicsNodes.forEach(n => {
        if (!n.group.visible) return;
        n.vx -= n.x * 0.008;
        n.vy -= n.y * 0.008;
        n.vz -= n.z * 0.008;

        n.vx *= damping;
        n.vy *= damping;
        n.vz *= damping;

        n.x += n.vx;
        n.y += n.vy;
        n.z += n.vz;
      });
    }

    function stepPlanarForces() {
      stepCosmicForces();
      kgPhysicsNodes.forEach(n => {
        n.z += (0 - n.z) * 0.15;
        n.vz = 0;
      });
    }

    function interpolateToTargets() {
      const alpha = 0.08;
      kgPhysicsNodes.forEach(n => {
        n.x += (n.targetX - n.x) * alpha;
        n.y += (n.targetY - n.y) * alpha;
        n.z += (n.targetZ - n.z) * alpha;
      });
    }

    // =========================================================================
    // SEMANTIC GRAPH MODES IMPLEMENTATION
    // =========================================================================
    function switchSemanticMode(mode) {
      currentSemanticMode = mode;
      document.querySelectorAll('.semantic-mode-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.mode === mode);
      });

      const indicator = document.getElementById('mode-active-indicator');
      const desc = document.getElementById('mode-active-desc');

      if (mode === "explore") {
        indicator.innerText = "EXPLORE";
        desc.innerText = "Holistic exploration mode. All active entities visible. Filter by domain or click any node to open its Answer Card.";
        resetNodeOpacities();
      } else if (mode === "trace") {
        indicator.innerText = "DEPENDENCY TRACE";
        desc.innerText = "Mechanical & governance dependency lineage. Traces upstream drawing/standard directives and downstream physical clearances.";
        if (currentSelectedNode) traceNodeDependencies(currentSelectedNode.data.id);
        else selectGraphNode("comp_detailb");
      } else if (mode === "revision") {
        indicator.innerText = "REVISION IMPACT";
        desc.innerText = "Revision evolution mode. Scrubber highlights entities introduced, modified, or superseded by the selected alteration level.";
        highlightRevisionEcosystem(activeAlterationLevel);
      } else if (mode === "failure") {
        indicator.innerText = "FAILURE ANALYSIS";
        desc.innerText = "Derailment risk & failure propagation. Traces mechanical defects to operational hazards and governing SOP mitigations.";
        highlightFailureEcosystem();
      } else if (mode === "bom") {
        indicator.innerText = "PROCUREMENT & BOM";
        desc.innerText = "Bill of Materials & LIST-A wear spares mode. Highlights physical component counts and mandatory 10% inventory buffers.";
        highlightProcurementEcosystem();
      } else if (mode === "manuals") {
        indicator.innerText = "CODES & MANUALS";
        desc.innerText = "Regulatory governance & standard SOP lineage. Connects official codes (IRPWM, USFD, AT Weld, FBW, TMM, STMM) to drawings and field tolerances.";
        highlightManualsEcosystem();
      }
    }

    function highlightManualsEcosystem() {
      const manualIds = new Set();
      kgPhysicsNodes.forEach(n => {
        if (n.data.domain === "manual" || n.data.domain === "tolerance" || n.data.domain === "equipment" ||
            n.data.type === "DOCUMENT" || n.data.type === "SPECIFICATION" || n.data.type === "SOP" ||
            n.data.type === "TOLERANCE" || n.data.type === "EQUIPMENT") {
          manualIds.add(n.data.id);
        }
      });

      // Expand to 1-hop connected drawings, components, notes
      kgPhysicsEdges.forEach(e => {
        if (manualIds.has(e.from)) manualIds.add(e.to);
        if (manualIds.has(e.to)) manualIds.add(e.from);
      });

      kgPhysicsNodes.forEach(n => {
        const isHit = manualIds.has(n.data.id);
        n.mesh.material.opacity = isHit ? 1.0 : 0.15;
        n.mesh.material.transparent = !isHit;
        n.sprite.material.opacity = isHit ? 1.0 : 0.15;
      });

      kgPhysicsEdges.forEach(e => {
        const isHit = manualIds.has(e.from) && manualIds.has(e.to);
        e.line.material.opacity = isHit ? 0.95 : 0.08;
        if (isHit) e.line.material.color.setHex(0x00f5d4);
        else e.line.material.color.setHex(0x182844);
      });
    }

    function resetNodeOpacities() {
      kgPhysicsNodes.forEach(n => {
        n.mesh.material.opacity = 1.0;
        n.mesh.material.transparent = false;
        n.sprite.material.opacity = 1.0;
      });
      kgPhysicsEdges.forEach(e => {
        e.line.material.color.setHex(e.color);
        e.line.material.opacity = 0.45;
      });
    }

    function traceNodeDependencies(nodeId) {
      const activeIds = new Set([nodeId]);
      // 1-hop & 2-hop traversal
      kgPhysicsEdges.forEach(e => {
        if (e.from === nodeId) activeIds.add(e.to);
        if (e.to === nodeId) activeIds.add(e.from);
      });

      kgPhysicsNodes.forEach(n => {
        const isHit = activeIds.has(n.data.id);
        n.mesh.material.opacity = isHit ? 1.0 : 0.15;
        n.mesh.material.transparent = !isHit;
        n.sprite.material.opacity = isHit ? 1.0 : 0.15;
      });

      kgPhysicsEdges.forEach(e => {
        const isHit = activeIds.has(e.from) && activeIds.has(e.to);
        e.line.material.opacity = isHit ? 0.95 : 0.08;
        if (isHit) e.line.material.color.setHex(0x00ff88);
        else e.line.material.color.setHex(0x182844);
      });
    }

    function highlightRevisionEcosystem(altLevel) {
      kgPhysicsNodes.forEach(n => {
        const isTargetAlt = (n.data.alt === altLevel);
        const isPreceding = (n.data.alt <= altLevel);
        n.mesh.material.opacity = isTargetAlt ? 1.0 : (isPreceding ? 0.4 : 0.1);
        n.mesh.material.transparent = true;
        n.sprite.material.opacity = isTargetAlt ? 1.0 : (isPreceding ? 0.4 : 0.1);
      });

      kgPhysicsEdges.forEach(e => {
        const isRevRel = (e.rel === "SUPERSEDES" || e.rel === "HAS_REVISION" || e.rel === "INTRODUCED_IN");
        e.line.material.opacity = isRevRel ? 0.95 : 0.1;
        if (isRevRel) e.line.material.color.setHex(0x3a86ff);
        else e.line.material.color.setHex(0x182844);
      });
    }

    function highlightFailureEcosystem() {
      const failureIds = new Set();
      kgPhysicsNodes.forEach(n => {
        if (n.data.domain === "defect" || n.data.type === "FAILURE_MODE" || n.data.type === "HAZARD" || n.data.type === "SOP") {
          failureIds.add(n.data.id);
        }
      });

      // Expand to connected mitigations and components
      kgPhysicsEdges.forEach(e => {
        if (failureIds.has(e.from)) failureIds.add(e.to);
        if (failureIds.has(e.to)) failureIds.add(e.from);
      });

      kgPhysicsNodes.forEach(n => {
        const isHit = failureIds.has(n.data.id);
        n.mesh.material.opacity = isHit ? 1.0 : 0.15;
        n.mesh.material.transparent = !isHit;
        n.sprite.material.opacity = isHit ? 1.0 : 0.15;
      });

      kgPhysicsEdges.forEach(e => {
        const isHit = failureIds.has(e.from) && failureIds.has(e.to);
        e.line.material.opacity = isHit ? 0.95 : 0.08;
        if (isHit) e.line.material.color.setHex(0xff3366);
        else e.line.material.color.setHex(0x182844);
      });
    }

    function highlightProcurementEcosystem() {
      const bomIds = new Set();
      kgPhysicsNodes.forEach(n => {
        if (n.data.domain === "procurement" || n.data.type === "BOM_ITEM" || n.data.type === "SPARE_PART") {
          bomIds.add(n.data.id);
        }
      });

      kgPhysicsEdges.forEach(e => {
        if (bomIds.has(e.from)) bomIds.add(e.to);
        if (bomIds.has(e.to)) bomIds.add(e.from);
      });

      kgPhysicsNodes.forEach(n => {
        const isHit = bomIds.has(n.data.id);
        n.mesh.material.opacity = isHit ? 1.0 : 0.15;
        n.mesh.material.transparent = !isHit;
        n.sprite.material.opacity = isHit ? 1.0 : 0.15;
      });

      kgPhysicsEdges.forEach(e => {
        const isHit = bomIds.has(e.from) && bomIds.has(e.to);
        e.line.material.opacity = isHit ? 0.95 : 0.08;
        if (isHit) e.line.material.color.setHex(0xf72585);
        else e.line.material.color.setHex(0x182844);
      });
    }

    // =========================================================================
    // SELECTION & ENGINEERING ANSWER CARD LOGIC
    // =========================================================================
    function setupRaycasting() {
      const raycaster = new THREE.Raycaster();
      const mouse = new THREE.Vector2();

      kgRenderer.domElement.addEventListener('click', (e) => {
        if (e.target !== kgRenderer.domElement) return;

        mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
        mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;

        raycaster.setFromCamera(mouse, kgCamera);
        const coreMeshes = kgPhysicsNodes.filter(n => n.group.visible).map(n => n.mesh);
        const intersects = raycaster.intersectObjects(coreMeshes);

        if (intersects.length > 0) {
          const hit = kgPhysicsNodes.find(n => n.mesh === intersects[0].object);
          if (hit) inspectNode(hit);
        }
      });
    }

    function inspectNode(node) {
      currentSelectedNode = node;
      const data = node.data;

      // Camera Fly-to
      kgControls.target.set(node.x, node.y, node.z);
      kgCamera.position.set(node.x + 4, node.y + 3, node.z + 10);
      kgControls.update();

      // Drawer Header
      document.getElementById('drawer-domain').innerText = `${data.type} · ${(DOMAIN_METADATA[data.domain]?.label || data.domain).toUpperCase()}`;
      document.getElementById('drawer-domain').style.color = data.color;
      document.getElementById('drawer-title').innerText = data.label;

      // Find governing drawing dossier
      let dossierKey = "RDSO_T_6155";
      if (data.id.includes("6154")) dossierKey = "RDSO_T_6154";
      else if (data.id.includes("6216")) dossierKey = "RDSO_T_6216";
      else if (data.id.includes("6280")) dossierKey = "RDSO_T_6280";
      else if (data.id.includes("6275")) dossierKey = "RDSO_T_6275";
      currentActiveDossier = RDSO_EXTRACTED_KNOWLEDGE[dossierKey] || RDSO_EXTRACTED_KNOWLEDGE["RDSO_T_6155"];

      // 1. POPULATE ENGINEERING ANSWER CARD
      const descEl = document.getElementById('answer-card-desc');
      const manClause = (window.RDSO_MANUALS_KNOWLEDGE?.clauses || []).find(c => c.id === data.id);
      const manDoc = window.RDSO_MANUALS_KNOWLEDGE?.manuals?.[data.id];
      const manTol = (window.RDSO_MANUALS_KNOWLEDGE?.tolerances || []).find(t => t.id === data.id);
      const manEq = (window.RDSO_MANUALS_KNOWLEDGE?.equipment || []).find(e => e.id === data.id);

      if (manClause) {
        descEl.innerHTML = `
          <div style="margin-bottom:8px;">
            <strong style="color:var(--accent-cyan); font-size:13px;">${manClause.title}</strong>
            <span style="font-size:11px; color:var(--accent-pink); background:rgba(247,37,133,0.15); padding:2px 6px; border-radius:4px; border:1px solid rgba(247,37,133,0.3); margin-left:6px;">${manClause.ref} · ${manClause.page}</span>
          </div>
          <blockquote style="border-left:3px solid var(--accent-cyan); padding-left:10px; margin:8px 0; font-style:italic; color:#e0e8f8; font-size:12px; line-height:1.5;">"${manClause.verbatim_text}"</blockquote>
          <div style="margin-top:10px; font-size:11px; font-weight:600; color:var(--accent-green); text-transform:uppercase;">Mandatory Regulatory Rules:</div>
          <ul style="margin:4px 0 0 16px; font-size:11px; color:var(--text-main); line-height:1.4;">
            ${(manClause.governing_rules || []).map(r => `<li>${r}</li>`).join('')}
          </ul>
          ${manClause.responsible_authorities ? `
            <div style="margin-top:8px; display:flex; gap:8px; flex-wrap:wrap;">
              ${Object.entries(manClause.responsible_authorities).map(([k,v]) => `<div style="font-size:10px; background:rgba(0,240,255,0.08); border:1px solid rgba(0,240,255,0.25); border-radius:4px; padding:4px 8px;"><strong style="color:var(--accent-cyan);">${k.replace('_', ' ').toUpperCase()}:</strong> ${v}</div>`).join('')}
            </div>
          ` : ''}
        `;
      } else if (manDoc) {
        descEl.innerHTML = `
          <div style="margin-bottom:8px;"><strong style="color:var(--accent-pink); font-size:13px;">${manDoc.title}</strong></div>
          <p style="font-size:12px; line-height:1.5; color:#e0e8f8; margin-bottom:8px;">${manDoc.scope}</p>
          <div style="font-size:11px; background:rgba(255,0,127,0.1); border:1px solid rgba(255,0,127,0.3); border-radius:6px; padding:8px; margin-top:8px;">
            <div><strong>Issuing Authority:</strong> ${manDoc.issuing_authority}</div>
            <div style="margin-top:4px;"><strong>Edition:</strong> ${manDoc.edition}</div>
            <div style="margin-top:4px;"><strong>Volume:</strong> ${manDoc.pages} Pages</div>
            <div style="margin-top:4px;"><strong>Local Archive:</strong> <code style="color:var(--accent-cyan);">manuals/${manDoc.filename}</code></div>
          </div>
        `;
      } else if (manTol) {
        descEl.innerHTML = `
          <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
            <span style="font-size:20px; font-weight:700; color:var(--accent-yellow); font-family:var(--font-mono);">${manTol.value}</span>
            <span style="font-size:10px; color:var(--accent-cyan); background:rgba(0,240,255,0.1); padding:2px 6px; border-radius:4px; border:1px solid rgba(0,240,255,0.3);">${manTol.clause}</span>
          </div>
          <p style="font-size:12px; line-height:1.5; color:#e0e8f8;"><strong>Safety & Engineering Purpose:</strong> ${manTol.purpose}</p>
          <div style="margin-top:8px; font-size:11px; color:var(--text-muted); font-family:var(--font-mono);">Design Limits: [${manTol.min_val} ${manTol.unit} — ${manTol.max_val} ${manTol.unit}]</div>
        `;
      } else if (manEq) {
        descEl.innerHTML = `
          <div style="margin-bottom:8px;"><strong style="color:var(--accent-cyan); font-size:13px;">${manEq.label}</strong></div>
          <p style="font-size:12px; line-height:1.5; color:#e0e8f8;">${manEq.desc}</p>
          <div style="margin-top:8px; font-size:11px; color:var(--accent-green);">Source Code: ${manEq.source_doc}</div>
        `;
      } else {
        descEl.innerText = data.desc || "Canonical railway track infrastructure asset governed by official RDSO technical specifications.";
      }
      
      const provBox = document.getElementById('answer-provenance-box');
      const linkedFact = rawKGFacts.find(f => f.subject_id === data.id || f.object_id === data.id);
      if (linkedFact && linkedFact.source) {
        provBox.style.display = "flex";
        document.getElementById('prov-dwg-title').innerText = `${linkedFact.source.drawing_id} (${linkedFact.source.revision})`;
        document.getElementById('prov-meta-line').innerText = `Region: ${linkedFact.source.region} | Method: ${linkedFact.extraction_method}`;
        const cropImg = (linkedFact.source.crop && linkedFact.source.crop.endsWith('.png')) ? linkedFact.source.crop : "crops/t6155_notes_full.png";
        document.getElementById('answer-crop-thumb').src = cropImg;
        currentActiveCrop = cropImg;
      } else {
        provBox.style.display = "flex";
        document.getElementById('prov-dwg-title').innerText = `${currentActiveDossier.drawing_number} (ALT ${currentActiveDossier.alteration_number || 13})`;
        document.getElementById('prov-meta-line').innerText = `Region: Master Blueprint | Method: Coordinate Crop`;
        const firstCrop = Object.values(currentActiveDossier.crops || {})[0] || "crops/t6155_notes_full.png";
        document.getElementById('answer-crop-thumb').src = firstCrop;
        currentActiveCrop = firstCrop;
      }

      // 2. Render Notes Tab
      renderDossierNotes(currentActiveDossier);

      // 3. Render Tables Tab
      renderDossierTables(currentActiveDossier);

      // 4. Render Blueprint Tab
      renderDossierBlueprints(currentActiveDossier);

      // 5. Render 3D Twin & Specs Tab
      renderComponentPhysicalTwin(data.twinAsset || data.id);

      const specsTable = document.getElementById('drawer-specs-table');
      specsTable.innerHTML = '';
      const specs = data.specs || { "Designation": data.label, "Domain": data.domain, "Standard": "IRS / RDSO" };
      Object.entries(specs).forEach(([k, v]) => {
        const row = document.createElement('tr');
        row.innerHTML = `<td>${k}</td><td>${v}</td>`;
        specsTable.appendChild(row);
      });

      // Connected Typed Hops
      const lineageList = document.getElementById('drawer-lineage-list');
      lineageList.innerHTML = '';
      const hops = [];
      kgPhysicsEdges.forEach(e => {
        if (e.from === data.id) hops.push({ id: e.to, rel: e.rel, type: "out" });
        if (e.to === data.id) hops.push({ id: e.from, rel: e.rel, type: "in" });
      });

      hops.forEach(h => {
        const targetNode = kgPhysicsNodes.find(n => n.data.id === h.id);
        if (targetNode) {
          const tag = document.createElement('div');
          tag.className = "lineage-tag";
          tag.innerHTML = `<span>${h.type === 'out' ? '➔' : '⬅'} ${h.rel}:</span> <strong>${targetNode.data.label}</strong>`;
          tag.onclick = () => inspectNode(targetNode);
          lineageList.appendChild(tag);
        }
      });

      // 6. Render Risks Tab
      if (data.domain === "defect" || data.type === "FAILURE_MODE" || data.type === "HAZARD") {
        document.getElementById('drawer-risk-title').innerText = data.label;
        document.getElementById('drawer-risk-desc').innerText = data.desc;
      } else {
        document.getElementById('drawer-risk-title').innerText = "Tethered Engineering Safeguard";
        document.getElementById('drawer-risk-desc').innerText = data.desc || "Strict adherence to tolerances prevents derailment hazards.";
      }

      // If in Dependency Trace mode, update trace
      if (currentSemanticMode === "trace") {
        traceNodeDependencies(data.id);
      }

      // Open Drawer
      toggleIntelligenceDrawer(true);
    }

    window.selectGraphNode = function(idOrQuery) {
      if (!idOrQuery) return false;
      const q = String(idOrQuery).toLowerCase().trim();
      let node = kgPhysicsNodes.find(n => n.data.id === idOrQuery || n.data.id.toLowerCase() === q);
      if (!node) {
        node = kgPhysicsNodes.find(n => {
          const nid = n.data.id.toLowerCase();
          const nlbl = n.data.label.toLowerCase();
          return nid === q.replace('rdso_t_', 'drg_') ||
                 nid === 'drg_' + q.replace('rdso_t_', '').replace('t_', '').replace('t-', '') ||
                 nlbl.includes(q) ||
                 q.includes(nid);
        });
      }
      if (node) {
        inspectNode(node);
        return true;
      }
      console.warn('Node not found for query:', idOrQuery);
      return false;
    };
    window.inspectNode = inspectNode;
    window.switchSemanticMode = switchSemanticMode;
    window.switchDrawerTab = switchDrawerTab;

    function switchDrawerTab(tabId) {
      document.querySelectorAll('.drawer-tab').forEach(t => {
        t.classList.toggle('active', t.dataset.tab === tabId);
      });
      document.querySelectorAll('.tab-pane').forEach(p => {
        p.classList.toggle('active', p.id === `tab-pane-${tabId}`);
      });
    }

    function renderDossierNotes(dossier) {
      const container = document.getElementById('drawer-notes-list');
      const countBadge = document.getElementById('notes-tab-count');
      container.innerHTML = '';

      const notes = dossier.general_notes || [];
      countBadge.innerText = notes.length;

      if (notes.length === 0) {
        container.innerHTML = '<div style="padding: 12px; font-size: 11px; color: var(--text-dim);">No specific notes cataloged for this drawing. Refer to master layout RDSO/T-6154.</div>';
        return;
      }

      notes.forEach(note => {
        const card = document.createElement('div');
        card.className = "note-card";
        card.innerHTML = `
          <div class="note-card-header">
            <span class="note-badge">NOTE ${note.note_number}</span>
            <span class="note-dwg-ref">${dossier.drawing_number}</span>
          </div>
          <div class="note-body">${note.text}</div>
        `;
        container.appendChild(card);
      });
    }

    function filterCurrentNotes(query) {
      const q = query.toLowerCase().trim();
      document.querySelectorAll('.note-card').forEach(card => {
        const text = card.innerText.toLowerCase();
        card.style.display = (!q || text.includes(q)) ? "flex" : "none";
      });
    }

    function renderDossierTables(dossier) {
      const subnav = document.getElementById('drawer-table-subnav');
      const content = document.getElementById('drawer-table-content');
      subnav.innerHTML = '';
      content.innerHTML = '';

      const availableTables = [];
      if (dossier.sleeper_schedule) availableTables.push({ id: "sleepers", label: "Sleeper Schedule (1-64)" });
      if (dossier.bom_table) availableTables.push({ id: "bom", label: "Bill of Materials (BOM)" });
      if (dossier.list_a_spares) availableTables.push({ id: "list_a", label: "LIST - A 10% Spares (24 Items)" });
      if (dossier.versine_table) availableTables.push({ id: "versine", label: "Curve Versines (Checking)" });
      if (dossier.switch_gap_schedule) availableTables.push({ id: "gap", label: "Switch Gap Schedule" });
      if (dossier.alteration_history) availableTables.push({ id: "alts", label: "Alteration History" });

      if (availableTables.length === 0) {
        content.innerHTML = '<div style="padding: 14px; font-size: 11px; color: var(--text-dim);">No tabular schedules attached to this item.</div>';
        return;
      }

      availableTables.forEach((tabInfo, idx) => {
        const btn = document.createElement('button');
        btn.className = `table-subnav-btn ${idx === 0 ? 'active' : ''}`;
        btn.innerText = tabInfo.label;
        btn.onclick = () => {
          document.querySelectorAll('.table-subnav-btn').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          showActiveTable(dossier, tabInfo.id);
        };
        subnav.appendChild(btn);
      });

      showActiveTable(dossier, availableTables[0].id);
    }

    function showActiveTable(dossier, tableId) {
      const content = document.getElementById('drawer-table-content');
      content.innerHTML = '';

      if (tableId === "sleepers") {
        let html = `
          <table class="rdso-table">
            <thead>
              <tr>
                <th>Station</th>
                <th>Drawing No.</th>
                <th>Length (mm)</th>
                <th>Zone / Function</th>
              </tr>
            </thead>
            <tbody>
        `;
        (dossier.sleeper_schedule || []).forEach(row => {
          html += `
            <tr>
              <td style="font-weight: 700; color: #fff;">${row.sleeper_no}</td>
              <td style="font-family: var(--font-mono); color: var(--accent-cyan);">${row.drg_no}</td>
              <td style="font-weight: 700;">${row.length_mm}</td>
              <td style="color: var(--text-muted); font-size: 10px;">${row.zone}</td>
            </tr>
          `;
        });
        html += '</tbody></table>';
        content.innerHTML = html;
      } else if (tableId === "bom") {
        let html = `
          <table class="rdso-table">
            <thead>
              <tr>
                <th>Drawing No.</th>
                <th>Part Description</th>
                <th>Quantity</th>
                <th>Unit</th>
              </tr>
            </thead>
            <tbody>
        `;
        (dossier.bom_table || []).forEach(row => {
          html += `
            <tr>
              <td style="font-family: var(--font-mono); color: var(--accent-cyan);">${row.drg_no || '-'}</td>
              <td style="font-weight: 600;">${row.item}</td>
              <td style="font-weight: 800; color: #fff;">${row.qty}</td>
              <td style="color: var(--text-muted);">${row.unit || 'Nos.'}</td>
            </tr>
          `;
        });
        html += '</tbody></table>';
        content.innerHTML = html;
      } else if (tableId === "list_a") {
        let html = `
          <table class="rdso-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Drawing / Part No.</th>
                <th>Wear / Breakage Spare Item</th>
                <th>Qty</th>
              </tr>
            </thead>
            <tbody>
        `;
        (dossier.list_a_spares || []).forEach(row => {
          html += `
            <tr>
              <td style="color: var(--text-dim);">${row.item_no}</td>
              <td style="font-family: var(--font-mono); color: var(--accent-cyan);">${row.drg_no}</td>
              <td style="font-weight: 600;">${row.description}</td>
              <td style="font-weight: 800; color: var(--accent-green);">${row.qty}</td>
            </tr>
          `;
        });
        html += '</tbody></table>';
        content.innerHTML = html;
      } else if (tableId === "versine") {
        const v = dossier.versine_table;
        content.innerHTML = `
          <div style="padding: 14px; display: flex; flex-direction: column; gap: 10px;">
            <div style="font-size: 11.5px; font-weight: 800; color: var(--accent-cyan);">${v.description}</div>
            <table class="specs-table">
              <tr><td>Chord Length (C)</td><td>${v.chord_length_mm} mm</td></tr>
              <tr><td>Versine at C/4 Station</td><td style="color: var(--accent-green); font-size: 13px;">${v.versine_c_quarter_mm} mm</td></tr>
              <tr><td>Versine at C/2 Mid-Point</td><td style="color: var(--accent-green); font-size: 13px;">${v.versine_c_half_mm} mm</td></tr>
              <tr><td>Versine at 3C/4 Station</td><td style="color: var(--accent-green); font-size: 13px;">${v.versine_c_three_quarter_mm} mm</td></tr>
            </table>
            <div style="font-size: 10.5px; color: var(--text-muted); line-height: 1.4; background: rgba(0,0,0,0.3); padding: 8px; border-radius: 6px;">
              Mandatory field checking requirement to confirm tongue rail pre-curvature before laying in track (IRPWM Annexure 4/6).
            </div>
          </div>
        `;
      }
    }

    function renderDossierBlueprints(dossier) {
      const select = document.getElementById('blueprint-crop-select');
      select.innerHTML = '';

      const crops = dossier.crops || {};
      const cropEntries = Object.entries(crops);

      if (cropEntries.length === 0) {
        select.innerHTML = '<option value="">No crops cataloged</option>';
        document.getElementById('blueprint-crop-img').src = '';
        return;
      }

      cropEntries.forEach(([name, path]) => {
        const opt = document.createElement('option');
        opt.value = path;
        opt.innerText = name.toUpperCase().replace('_', ' ');
        select.appendChild(opt);
      });

      changeActiveBlueprintCrop(cropEntries[0][1]);
    }

    function changeActiveBlueprintCrop(src) {
      currentActiveCrop = src;
      document.getElementById('blueprint-crop-img').src = src;
    }

    function openFullscreenActiveBlueprint() {
      if (!currentActiveCrop) return;
      document.getElementById('blueprint-modal-img').src = currentActiveCrop;
      document.getElementById('blueprint-modal-title').innerText = `RDSO Official Blueprint Source Inspection: ${currentActiveDossier.drawing_number}`;
      document.getElementById('blueprint-modal').style.display = "flex";
    }

    function closeFullscreenBlueprint() {
      document.getElementById('blueprint-modal').style.display = "none";
    }

    function toggleIntelligenceDrawer(open) {
      const drawer = document.getElementById('intelligence-drawer');
      if (open === undefined) drawer.classList.toggle('collapsed');
      else drawer.classList.toggle('collapsed', !open);
    }

    // 3D Mini-Viewport CAD Twin
    let twinScene, twinCamera, twinRenderer, twinControls, twinAssetGroup;

    function initComponentTwinViewer() {
      const canvas = document.getElementById('component-twin-canvas');
      const box = document.getElementById('twin-box');
      const w = box.clientWidth || 440;
      const h = 200;

      twinScene = new THREE.Scene();
      twinScene.background = new THREE.Color(0x050914);

      twinCamera = new THREE.PerspectiveCamera(40, w / h, 0.1, 100);
      twinCamera.position.set(0.6, 0.5, 0.8);

      twinRenderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true });
      twinRenderer.setSize(w, h);
      twinRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

      twinControls = new THREE.OrbitControls(twinCamera, canvas);
      twinControls.enableDamping = true;
      twinControls.dampingFactor = 0.08;

      twinScene.add(new THREE.AmbientLight(0xffffff, 0.9));

      const pt1 = new THREE.PointLight(0x00f0ff, 1.4, 20);
      pt1.position.set(2, 3, 2);
      twinScene.add(pt1);

      const pt2 = new THREE.PointLight(0xffaa00, 0.8, 20);
      pt2.position.set(-2, 1, -2);
      twinScene.add(pt2);

      const grid = new THREE.GridHelper(2, 20, 0x00f0ff, 0x182844);
      grid.position.y = -0.15;
      twinScene.add(grid);

      twinAssetGroup = new THREE.Group();
      twinScene.add(twinAssetGroup);

      function animateTwin() {
        requestAnimationFrame(animateTwin);
        twinControls.update();
        twinRenderer.render(twinScene, twinCamera);
      }
      animateTwin();
    }

    function renderComponentPhysicalTwin(assetKey) {
      if (!twinAssetGroup) return;
      while (twinAssetGroup.children.length > 0) {
        twinAssetGroup.remove(twinAssetGroup.children[0]);
      }

      document.getElementById('twin-badge-text').innerText = `PHYSICAL 3D ASSET TWIN: ${assetKey.toUpperCase()}`;

      const steelMat = new THREE.MeshStandardMaterial({ color: 0x48cae4, metalness: 0.85, roughness: 0.25 });
      const darkSteelMat = new THREE.MeshStandardMaterial({ color: 0x223344, metalness: 0.9, roughness: 0.35 });

      if (assetKey === "slide_chair") {
        const base = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.05, 0.5), darkSteelMat);
        const table = new THREE.Mesh(new THREE.BoxGeometry(0.25, 0.04, 0.3), steelMat);
        table.position.set(0, 0.045, -0.05);
        const stop = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.08, 0.3), steelMat);
        stop.position.set(0.12, 0.065, -0.05);
        twinAssetGroup.add(base, table, stop);
      } else if (assetKey === "bent_tiebar") {
        const barLeft = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.35, 12), steelMat);
        barLeft.rotation.z = Math.PI / 2;
        barLeft.position.set(-0.25, 0.1, 0);

        const dropArm = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.22, 12), steelMat);
        dropArm.position.set(-0.1, 0, 0);

        const bottomSpan = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.48, 12), steelMat);
        bottomSpan.rotation.z = Math.PI / 2;
        bottomSpan.position.set(0.14, -0.1, 0);

        twinAssetGroup.add(barLeft, dropArm, bottomSpan);
      } else {
        const rail = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.18, 0.8), steelMat);
        const pad = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.02, 0.3), darkSteelMat);
        pad.position.y = -0.1;
        twinAssetGroup.add(rail, pad);
      }

      twinCamera.position.set(0.5, 0.4, 0.6);
      twinControls.target.set(0, 0, 0);
      twinControls.update();
    }

    // UI Tools
    function renderDomainChips() {
      const container = document.getElementById('domain-chips-list');
      container.innerHTML = '';

      const allChip = document.createElement('div');
      allChip.className = "domain-chip active";
      allChip.style.background = "rgba(0, 240, 255, 0.2)";
      allChip.style.color = "#00f0ff";
      allChip.innerText = "ALL DOMAINS";
      allChip.onclick = () => filterByDomain('all');
      container.appendChild(allChip);

      Object.entries(DOMAIN_METADATA).forEach(([domKey, meta]) => {
        const chip = document.createElement('div');
        chip.className = "domain-chip";
        chip.style.background = `${meta.color}22`;
        chip.style.color = meta.color;
        chip.innerHTML = `${meta.icon} ${meta.label}`;
        chip.onclick = () => filterByDomain(domKey);
        container.appendChild(chip);
      });
    }

    function filterByDomain(domain) {
      activeFilterDomain = domain;
      document.getElementById('domain-active-label').innerText = domain.toUpperCase();
      document.querySelectorAll('.domain-chip').forEach(c => {
        const txt = c.innerText.toLowerCase();
        c.classList.toggle('active', (domain === 'all' && txt.includes('all')) || txt.includes(domain));
      });

      kgPhysicsNodes.forEach(n => {
        const match = (domain === 'all' || n.data.domain === domain);
        n.group.visible = match;
      });
    }

    function onAlterationScrub(val) {
      activeAlterationLevel = parseInt(val);
      document.getElementById('alt-tag-display').innerText = `ALT ${val.padStart(2, '0')}`;
      
      const desc = document.getElementById('alt-desc-display');
      if (activeAlterationLevel >= 13) {
        desc.innerText = "Alt 13 (Latest): Enforces Note 28 LIST-A 10% inventory spares across 24 critical wear items.";
      } else if (activeAlterationLevel >= 12) {
        desc.innerText = "Alt 12: Introduces Note 25 & 26 epoxy dowel core hole retrofit protocol (IS:12994 L-100).";
      } else if (activeAlterationLevel >= 11) {
        desc.innerText = "Alt 11: Mandates Detail 'B' Bent Tie Bar 222 mm drop bend clearing Point Lock machine rods.";
      } else if (activeAlterationLevel >= 10) {
        desc.innerText = "Alt 10: Introduces Welded Joint 'W' eradicating fatigue-prone Machined Joint 'M'.";
      } else {
        desc.innerText = `Alt ${val}: Baseline turnout architecture.`;
      }

      if (currentSemanticMode === "revision") {
        highlightRevisionEcosystem(activeAlterationLevel);
      }
    }

    function switchGraphLayout(layout) {
      currentLayout = layout;
      document.querySelectorAll('.layout-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.layout === layout);
      });

      if (layout === "planar") {
        kgControls.target.set(0, 0, 0);
        kgCamera.position.set(0, 0, 36);
        kgControls.update();
      } else if (layout === "dag") {
        const rankY = { drawing: 8, revision: 5, component: 2, turnout_layout: 0, specification: -3, materials: -5, procurement: -5, signaling: -2, defect: -7, sop: -8 };
        kgPhysicsNodes.forEach(node => {
          node.targetY = rankY[node.data.domain] !== undefined ? rankY[node.data.domain] : 0;
          node.targetX = (Math.random() - 0.5) * 26;
          node.targetZ = (Math.random() - 0.5) * 6;
        });
        kgControls.target.set(0, 0, 0);
        kgCamera.position.set(0, 10, 36);
        kgControls.update();
      }
    }

    function initSearchAutocomplete() {
      const input = document.getElementById('global-search');
      const dropdown = document.getElementById('search-dropdown');

      input.addEventListener('input', () => {
        const q = input.value.trim().toLowerCase();
        if (!q) {
          dropdown.style.display = "none";
          return;
        }

        const matches = kgPhysicsNodes.filter(n => {
          const specsStr = JSON.stringify(n.data.specs || {}).toLowerCase();
          return n.data.id.toLowerCase().includes(q) ||
                 n.data.label.toLowerCase().includes(q) ||
                 (n.data.desc && n.data.desc.toLowerCase().includes(q)) ||
                 n.data.domain.toLowerCase().includes(q) ||
                 specsStr.includes(q);
        });

        if (matches.length === 0) {
          dropdown.innerHTML = `<div style="padding: 10px; font-size: 11px; color: var(--text-dim);">No entities match "${q}"</div>`;
          dropdown.style.display = "block";
          return;
        }

        dropdown.innerHTML = '';
        matches.slice(0, 8).forEach(m => {
          const item = document.createElement('div');
          item.className = "search-item";
          item.innerHTML = `
            <span class="search-item-title">${m.data.label}</span>
            <span class="search-item-badge" style="background: ${m.data.color}22; color: ${m.data.color};">${m.data.domain}</span>
          `;
          item.onclick = () => {
            inspectNode(m);
            dropdown.style.display = "none";
            input.value = m.data.label;
          };
          dropdown.appendChild(item);
        });
        dropdown.style.display = "block";
      });

      window.addEventListener('keydown', (e) => {
        if (e.key === '/' && document.activeElement !== input) {
          e.preventDefault();
          input.focus();
        }
      });
    }

    function populateParentSelect() {
      const sel = document.getElementById('in-node-parent');
      if (!sel) return;
      sel.innerHTML = '';
      kgPhysicsNodes.forEach(n => {
        const opt = document.createElement('option');
        opt.value = n.data.id;
        opt.innerText = n.data.label;
        sel.appendChild(opt);
      });
    }

    function openIngestModal() {
      document.getElementById('ingest-modal').style.display = "flex";
      populateParentSelect();
    }

    function closeIngestModal() {
      document.getElementById('ingest-modal').style.display = "none";
    }

    function submitIngestNode() {
      const title = document.getElementById('in-node-title').value.trim();
      const domain = document.getElementById('in-node-domain').value;
      const parentId = document.getElementById('in-node-parent').value;
      const desc = document.getElementById('in-node-desc').value.trim();

      if (!title) return alert("Entity Label is required");

      const newId = `custom_${Date.now()}`;
      const color = DOMAIN_METADATA[domain]?.color || "#00f0ff";

      const newNodeData = {
        id: newId,
        label: title,
        type: domain.toUpperCase(),
        domain: domain,
        color: color,
        alt: 13,
        desc: desc,
        specs: { "Source": "Live Field Ingestion", "Timestamp": new Date().toISOString().split('T')[0] }
      };

      const nodeObj = addNodeToGraph(newNodeData);
      addEdgeToGraph({ from: parentId, to: newId, rel: "CONNECTED_TO" });

      closeIngestModal();
      document.getElementById('in-node-title').value = '';
      document.getElementById('in-node-desc').value = '';

      renderDomainChips();
      populateParentSelect();
      updateTelemetryCounters();
      inspectNode(nodeObj);
    }

    function exportGraph(format) {
      const nodes = kgPhysicsNodes.map(n => n.data);
      const edges = kgPhysicsEdges.map(e => ({ from: e.from, to: e.to, rel: e.rel }));

      if (format === 'cypher') {
        let cypher = "// Exported Cypher from RDSO Track Knowledge Graph Studio\n";
        nodes.forEach(n => {
          cypher += `MERGE (n:${n.domain.toUpperCase()} {id: "${n.id}", label: "${n.label}"});\n`;
        });
        edges.forEach(e => {
          cypher += `MATCH (a {id: "${e.from}"}), (b {id: "${e.to}"}) MERGE (a)-[:${e.rel}]->(b);\n`;
        });
        const blob = new Blob([cypher], { type: "text/plain" });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = "rdso_canonical_graph.cypher";
        a.click();
      }
    }

    function updateTelemetryCounters() {
      document.getElementById('telem-nodes').innerText = kgPhysicsNodes.length;
      document.getElementById('telem-edges').innerText = kgPhysicsEdges.length;
      document.getElementById('telem-facts').innerText = rawKGFacts.length;
    }

    function onWindowResize() {
      const w = window.innerWidth;
      const h = window.innerHeight;
      kgCamera.aspect = w / h;
      kgCamera.updateProjectionMatrix();
      kgRenderer.setSize(w, h);
    }

    window.addEventListener('DOMContentLoaded', initKnowledgeGraphApp);
  </script>
</body>
</html>
'''

final_html = html_template.replace("__EXTRACTED_KNOWLEDGE_JSON__", extracted_json_str).replace("__CANONICAL_KG_JSON__", canonical_json_str).replace("__MANUALS_KNOWLEDGE_JSON__", manuals_json_str)

output_html_path = os.path.join(REPO_ROOT, "index.html")
with open(output_html_path, "w", encoding="utf-8") as f:
    f.write(final_html)

print(f"[+] Successfully compiled index.html with Canonical Knowledge Core! Size: {len(final_html)} bytes")
print(f"    Target: {output_html_path}")
