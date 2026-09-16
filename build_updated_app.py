import json
import os

with open("rdso_extracted_knowledge.json", "r", encoding="utf-8") as f:
    extracted_knowledge = json.load(f)

extracted_json_str = json.dumps(extracted_knowledge, indent=2)

html_template = r'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RDSO Railway Track Knowledge Graph Studio | Intelligent Rail Ontology & Asset Digital Twin</title>
  <style>
    :root {
      --bg-space: #060911;
      --bg-panel: rgba(11, 17, 30, 0.92);
      --bg-card: rgba(18, 27, 46, 0.85);
      --border-subtle: rgba(56, 96, 160, 0.32);
      --border-glow: rgba(0, 220, 255, 0.55);
      --text-main: #f0f4fc;
      --text-muted: #8fa0b8;
      --text-dim: #5c6c82;
      --accent-cyan: #00f0ff;
      --accent-green: #00ff88;
      --accent-orange: #ff9d00;
      --accent-purple: #9d4edd;
      --accent-red: #ff3366;
      --accent-yellow: #ffd60a;
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

    /* Fullscreen 3D Knowledge Graph Canvas */
    #kg-canvas-container {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      z-index: 1;
    }

    /* Glassmorphism Header */
    header {
      position: absolute;
      top: 14px;
      left: 18px;
      right: 18px;
      z-index: 20;
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 20px;
      background: var(--bg-panel);
      backdrop-filter: blur(20px);
      border: 1px solid var(--border-subtle);
      border-radius: 12px;
      box-shadow: 0 10px 35px rgba(0, 0, 0, 0.7);
    }

    .brand-section {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .brand-icon {
      width: 38px;
      height: 38px;
      background: linear-gradient(135deg, var(--accent-cyan), #0044ff);
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      box-shadow: 0 0 18px rgba(0, 240, 255, 0.45);
    }

    .brand-titles h1 {
      font-size: 15px;
      font-weight: 800;
      letter-spacing: 0.6px;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .brand-titles h1 .badge-ver {
      background: rgba(0, 240, 255, 0.15);
      border: 1px solid var(--accent-cyan);
      color: var(--accent-cyan);
      font-size: 10px;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: 4px;
    }

    .brand-titles p {
      font-size: 11px;
      color: var(--text-muted);
      letter-spacing: 0.2px;
    }

    /* Global Search Box */
    .search-wrapper {
      position: relative;
      width: 320px;
    }

    .search-input {
      width: 100%;
      background: rgba(4, 8, 16, 0.65);
      border: 1px solid var(--border-subtle);
      border-radius: 8px;
      padding: 8px 12px 8px 34px;
      color: #fff;
      font-size: 12px;
      font-family: inherit;
      outline: none;
      transition: all 0.25s ease;
    }

    .search-input:focus {
      border-color: var(--accent-cyan);
      box-shadow: 0 0 14px rgba(0, 240, 255, 0.35);
      background: rgba(4, 8, 16, 0.95);
    }

    .search-icon {
      position: absolute;
      left: 10px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 13px;
      color: var(--text-dim);
      pointer-events: none;
    }

    .search-shortcut {
      position: absolute;
      right: 10px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 10px;
      background: rgba(255,255,255,0.08);
      padding: 2px 5px;
      border-radius: 4px;
      color: var(--text-muted);
      pointer-events: none;
      font-family: var(--font-mono);
    }

    .search-dropdown {
      position: absolute;
      top: calc(100% + 6px);
      left: 0;
      right: 0;
      background: var(--bg-panel);
      backdrop-filter: blur(16px);
      border: 1px solid var(--border-subtle);
      border-radius: 8px;
      max-height: 280px;
      overflow-y: auto;
      display: none;
      box-shadow: 0 12px 30px rgba(0,0,0,0.8);
      z-index: 50;
    }

    .search-item {
      padding: 8px 12px;
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid rgba(255,255,255,0.04);
      font-size: 12px;
      transition: background 0.15s;
    }

    .search-item:hover {
      background: rgba(0, 240, 255, 0.12);
    }

    .search-item-title {
      color: #fff;
      font-weight: 600;
    }

    .search-item-badge {
      font-size: 9px;
      padding: 2px 6px;
      border-radius: 4px;
      text-transform: uppercase;
      font-weight: 700;
    }

    /* Layout Mode Switcher */
    .layout-switcher {
      display: flex;
      background: rgba(0, 0, 0, 0.5);
      border: 1px solid var(--border-subtle);
      border-radius: 8px;
      padding: 3px;
      gap: 3px;
    }

    .layout-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      padding: 6px 12px;
      font-size: 11.5px;
      font-weight: 600;
      border-radius: 6px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s;
    }

    .layout-btn:hover {
      color: #fff;
      background: rgba(255,255,255,0.06);
    }

    .layout-btn.active {
      background: linear-gradient(135deg, rgba(0, 240, 255, 0.25), rgba(0, 85, 255, 0.35));
      color: var(--accent-cyan);
      border: 1px solid rgba(0, 240, 255, 0.5);
      box-shadow: 0 0 10px rgba(0, 240, 255, 0.25);
    }

    /* Header Action Buttons */
    .header-actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .btn {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border-subtle);
      color: var(--text-main);
      padding: 7px 14px;
      font-size: 12px;
      font-weight: 600;
      border-radius: 8px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s ease;
    }

    .btn:hover {
      background: rgba(255, 255, 255, 0.12);
      border-color: rgba(255, 255, 255, 0.3);
      color: #fff;
    }

    .btn-primary {
      background: linear-gradient(135deg, var(--accent-cyan), #0066ff);
      color: #000;
      border: none;
      font-weight: 700;
      box-shadow: 0 0 14px rgba(0, 240, 255, 0.4);
    }

    .btn-primary:hover {
      background: linear-gradient(135deg, #4df3ff, #2b7fff);
      box-shadow: 0 0 20px rgba(0, 240, 255, 0.6);
      color: #000;
    }

    /* Floating Left Tool Dock */
    #left-tools-dock {
      position: absolute;
      top: 84px;
      left: 18px;
      bottom: 24px;
      width: 270px;
      z-index: 15;
      display: flex;
      flex-direction: column;
      gap: 12px;
      pointer-events: none;
    }

    .dock-card {
      pointer-events: auto;
      background: var(--bg-panel);
      backdrop-filter: blur(18px);
      border: 1px solid var(--border-subtle);
      border-radius: 12px;
      padding: 14px;
      box-shadow: 0 8px 30px rgba(0,0,0,0.65);
    }

    .card-title {
      font-size: 11px;
      font-weight: 800;
      color: var(--accent-cyan);
      letter-spacing: 0.8px;
      text-transform: uppercase;
      margin-bottom: 10px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    /* Domain Filter Chips */
    .domain-chips-list {
      display: flex;
      flex-direction: column;
      gap: 5px;
    }

    .domain-chip {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 6px 10px;
      background: rgba(0, 0, 0, 0.35);
      border: 1px solid rgba(255,255,255,0.06);
      border-radius: 6px;
      cursor: pointer;
      font-size: 11.5px;
      font-weight: 600;
      transition: all 0.2s;
    }

    .domain-chip:hover {
      background: rgba(255,255,255,0.08);
      border-color: rgba(255,255,255,0.18);
    }

    .domain-chip.active {
      border-color: currentColor;
      background: rgba(255,255,255,0.1);
      box-shadow: 0 0 10px rgba(0,0,0,0.4);
    }

    .domain-left {
      display: flex;
      align-items: center;
      gap: 7px;
    }

    .domain-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
    }

    .domain-count {
      font-size: 10px;
      font-family: var(--font-mono);
      background: rgba(255,255,255,0.1);
      padding: 1px 6px;
      border-radius: 10px;
      color: var(--text-muted);
    }

    /* Alteration Scrubber */
    .scrubber-wrap {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .scrubber-header {
      display: flex;
      justify-content: space-between;
      font-size: 11px;
      font-weight: 700;
    }

    .scrubber-slider {
      width: 100%;
      accent-color: var(--accent-cyan);
      cursor: pointer;
    }

    .scrubber-desc {
      font-size: 10.5px;
      color: var(--text-muted);
      line-height: 1.35;
      background: rgba(0,0,0,0.3);
      padding: 6px 8px;
      border-radius: 4px;
      border-left: 2px solid var(--accent-cyan);
    }

    /* Simulation Control Buttons */
    .dock-actions {
      display: flex;
      gap: 6px;
      margin-top: 6px;
    }

    .dock-actions .btn {
      flex: 1;
      justify-content: center;
      font-size: 11px;
      padding: 6px;
    }

    /* =========================================================================
       RIGHT MULTI-TAB ENTITY INTELLIGENCE DRAWER (EXPANDED 460PX)
       ========================================================================= */
    #intelligence-drawer {
      position: absolute;
      top: 84px;
      right: 18px;
      bottom: 24px;
      width: 480px;
      background: var(--bg-panel);
      backdrop-filter: blur(24px);
      border: 1px solid var(--border-subtle);
      border-radius: 14px;
      z-index: 15;
      display: flex;
      flex-direction: column;
      box-shadow: -12px 0 45px rgba(0, 0, 0, 0.8);
      transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1);
      overflow: hidden;
    }

    #intelligence-drawer.collapsed {
      transform: translateX(calc(100% + 24px));
    }

    .drawer-header {
      padding: 12px 18px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      background: rgba(0, 0, 0, 0.35);
    }

    .drawer-title-block h2 {
      font-size: 14.5px;
      font-weight: 800;
      color: #fff;
      margin-bottom: 3px;
    }

    .drawer-title-block .meta-tag {
      font-size: 10px;
      font-weight: 700;
      color: var(--accent-cyan);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .close-drawer-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      cursor: pointer;
      font-size: 18px;
      line-height: 1;
      padding: 4px;
    }

    .close-drawer-btn:hover {
      color: #fff;
    }

    /* Drawer Tab Bar */
    .drawer-nav-tabs {
      display: flex;
      background: rgba(0, 0, 0, 0.4);
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      padding: 0 10px;
      gap: 4px;
    }

    .drawer-tab {
      background: transparent;
      border: none;
      border-bottom: 2px solid transparent;
      color: var(--text-muted);
      font-size: 11px;
      font-weight: 700;
      padding: 10px 10px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s;
    }

    .drawer-tab:hover {
      color: #fff;
    }

    .drawer-tab.active {
      color: var(--accent-cyan);
      border-bottom-color: var(--accent-cyan);
      background: rgba(0, 240, 255, 0.06);
    }

    .drawer-tab-badge {
      font-size: 9.5px;
      padding: 1px 5px;
      border-radius: 10px;
      background: rgba(255, 255, 255, 0.1);
      color: var(--text-main);
      font-family: var(--font-mono);
    }

    .drawer-content {
      padding: 16px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 14px;
      flex: 1;
    }

    .tab-pane {
      display: none;
      flex-direction: column;
      gap: 12px;
    }

    .tab-pane.active {
      display: flex;
    }

    /* Notes Tab Styling */
    .notes-search-box {
      display: flex;
      align-items: center;
      background: rgba(0,0,0,0.4);
      border: 1px solid var(--border-subtle);
      border-radius: 6px;
      padding: 6px 10px;
      gap: 8px;
    }

    .notes-search-input {
      background: transparent;
      border: none;
      color: #fff;
      font-size: 11.5px;
      outline: none;
      width: 100%;
      font-family: inherit;
    }

    .notes-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
      max-height: 480px;
      overflow-y: auto;
    }

    .note-card {
      background: rgba(0, 0, 0, 0.35);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 8px;
      padding: 10px 12px;
      display: flex;
      flex-direction: column;
      gap: 5px;
      transition: all 0.2s;
    }

    .note-card:hover {
      border-color: rgba(0, 240, 255, 0.3);
      background: rgba(0, 240, 255, 0.04);
    }

    .note-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .note-num-badge {
      font-size: 10px;
      font-weight: 800;
      color: var(--accent-cyan);
      background: rgba(0, 240, 255, 0.12);
      padding: 2px 7px;
      border-radius: 4px;
      letter-spacing: 0.5px;
    }

    .note-body {
      font-size: 11px;
      color: #d8e2f0;
      line-height: 1.45;
    }

    /* Tables Tab Styling */
    .table-subnav {
      display: flex;
      gap: 6px;
      overflow-x: auto;
      padding-bottom: 4px;
    }

    .table-subnav-btn {
      background: rgba(0,0,0,0.4);
      border: 1px solid var(--border-subtle);
      color: var(--text-muted);
      font-size: 10.5px;
      font-weight: 700;
      padding: 4px 8px;
      border-radius: 5px;
      cursor: pointer;
      white-space: nowrap;
    }

    .table-subnav-btn.active {
      background: rgba(0, 240, 255, 0.2);
      border-color: var(--accent-cyan);
      color: #fff;
    }

    .data-table-wrap {
      max-height: 480px;
      overflow-y: auto;
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 8px;
      background: rgba(0, 0, 0, 0.4);
    }

    .rdso-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 11px;
      text-align: left;
    }

    .rdso-table th {
      background: rgba(14, 24, 44, 0.95);
      position: sticky;
      top: 0;
      padding: 8px 10px;
      color: var(--accent-cyan);
      font-weight: 800;
      border-bottom: 1px solid rgba(255, 255, 255, 0.12);
      font-size: 10px;
      letter-spacing: 0.5px;
      text-transform: uppercase;
      z-index: 2;
    }

    .rdso-table td {
      padding: 7px 10px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
      color: #d8e2f0;
    }

    .rdso-table tr:hover td {
      background: rgba(0, 240, 255, 0.08);
    }

    /* Blueprint Viewer Tab */
    .blueprint-controls {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }

    .blueprint-crop-select {
      background: rgba(0,0,0,0.5);
      border: 1px solid var(--border-subtle);
      color: #fff;
      font-size: 11px;
      padding: 4px 8px;
      border-radius: 6px;
      outline: none;
    }

    .blueprint-preview-box {
      border: 1px solid rgba(0, 240, 255, 0.3);
      border-radius: 8px;
      overflow: hidden;
      background: #020408;
      position: relative;
      cursor: pointer;
    }

    .blueprint-img {
      width: 100%;
      height: auto;
      display: block;
      transition: transform 0.25s;
    }

    .blueprint-preview-box:hover .blueprint-img {
      transform: scale(1.02);
    }

    .blueprint-overlay-hint {
      position: absolute;
      bottom: 8px;
      right: 8px;
      background: rgba(0,0,0,0.75);
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 10px;
      color: var(--accent-cyan);
      border: 1px solid var(--accent-cyan);
    }

    /* Embedded 3D Digital Twin Viewport */
    .digital-twin-box {
      background: rgba(3, 7, 15, 0.85);
      border: 1px solid rgba(0, 240, 255, 0.35);
      border-radius: 10px;
      overflow: hidden;
      position: relative;
      box-shadow: inset 0 0 20px rgba(0, 240, 255, 0.15);
    }

    .twin-canvas-wrap {
      width: 100%;
      height: 220px;
      position: relative;
    }

    #component-twin-canvas {
      width: 100%;
      height: 100%;
      display: block;
    }

    .twin-badge {
      position: absolute;
      top: 8px;
      left: 10px;
      background: rgba(0, 0, 0, 0.7);
      backdrop-filter: blur(8px);
      border: 1px solid var(--accent-cyan);
      color: var(--accent-cyan);
      font-size: 9.5px;
      font-weight: 800;
      padding: 2px 7px;
      border-radius: 4px;
      letter-spacing: 0.5px;
      display: flex;
      align-items: center;
      gap: 5px;
    }

    .twin-controls-hint {
      position: absolute;
      bottom: 6px;
      right: 8px;
      font-size: 9px;
      color: var(--text-dim);
      background: rgba(0,0,0,0.6);
      padding: 2px 6px;
      border-radius: 4px;
      pointer-events: none;
    }

    /* Specs Table */
    .specs-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 11px;
    }

    .specs-table tr {
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }

    .specs-table td {
      padding: 6px 4px;
    }

    .specs-table td:first-child {
      color: var(--text-muted);
      width: 42%;
      font-weight: 600;
    }

    .specs-table td:last-child {
      color: #fff;
      font-weight: 700;
      text-align: right;
    }

    /* Lineage & Connected Hops */
    .lineage-tags-list {
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
      margin-top: 5px;
    }

    .lineage-tag {
      font-size: 10.5px;
      padding: 4px 8px;
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 6px;
      color: var(--text-main);
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 5px;
      transition: all 0.2s;
    }

    .lineage-tag:hover {
      background: rgba(0, 240, 255, 0.15);
      border-color: var(--accent-cyan);
      color: #fff;
    }

    /* Failure Mode Warning Alert */
    .failure-risk-box {
      background: rgba(255, 51, 102, 0.12);
      border: 1px solid rgba(255, 51, 102, 0.35);
      border-radius: 8px;
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
      font-size: 11px;
      color: #ffcad4;
      line-height: 1.4;
    }

    /* Bottom Telemetry Bar */
    #telemetry-bar {
      position: absolute;
      bottom: 12px;
      left: 300px;
      right: 510px;
      height: 32px;
      background: var(--bg-panel);
      backdrop-filter: blur(14px);
      border: 1px solid var(--border-subtle);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 14px;
      font-size: 10.5px;
      color: var(--text-muted);
      z-index: 10;
    }

    .telemetry-item {
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .telemetry-val {
      color: #fff;
      font-family: var(--font-mono);
      font-weight: 700;
    }

    /* Physics Tuner Popover */
    #physics-popover {
      position: absolute;
      top: 74px;
      right: 18px;
      width: 280px;
      background: var(--bg-panel);
      backdrop-filter: blur(20px);
      border: 1px solid var(--border-subtle);
      border-radius: 12px;
      padding: 14px;
      box-shadow: 0 12px 35px rgba(0,0,0,0.8);
      z-index: 30;
      display: none;
    }

    .tuner-slider-row {
      display: flex;
      flex-direction: column;
      gap: 4px;
      margin-bottom: 10px;
    }

    .tuner-label-val {
      display: flex;
      justify-content: space-between;
      font-size: 10.5px;
      font-weight: 700;
      color: var(--text-muted);
    }

    /* Ingestion Modal */
    #ingest-modal {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(2, 5, 12, 0.85);
      backdrop-filter: blur(12px);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 100;
    }

    .modal-box {
      width: 500px;
      background: var(--bg-panel);
      border: 1px solid var(--accent-cyan);
      box-shadow: 0 0 40px rgba(0, 240, 255, 0.3);
      border-radius: 14px;
      padding: 22px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    .modal-box h3 {
      font-size: 16px;
      font-weight: 800;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .form-group {
      display: flex;
      flex-direction: column;
      gap: 5px;
    }

    .form-group label {
      font-size: 11px;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .form-control {
      background: rgba(0, 0, 0, 0.45);
      border: 1px solid var(--border-subtle);
      border-radius: 6px;
      padding: 8px 10px;
      color: #fff;
      font-size: 12px;
      outline: none;
      font-family: inherit;
    }

    .form-control:focus {
      border-color: var(--accent-cyan);
    }

    /* Fullscreen Blueprint Modal */
    #blueprint-modal {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.92);
      backdrop-filter: blur(16px);
      display: none;
      flex-direction: column;
      z-index: 200;
    }

    .blueprint-modal-header {
      padding: 12px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      background: rgba(10, 15, 26, 0.9);
    }

    .blueprint-modal-body {
      flex: 1;
      overflow: auto;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }

    .blueprint-modal-img {
      max-width: 100%;
      max-height: 90vh;
      border: 1px solid var(--accent-cyan);
      box-shadow: 0 0 30px rgba(0, 240, 255, 0.25);
      border-radius: 8px;
    }
  </style>
  <script src="./lib/three.min.js"></script>
  <script src="./lib/OrbitControls.js"></script>
</head>
<body>

  <!-- Fullscreen 3D Knowledge Graph Viewport -->
  <div id="kg-canvas-container"></div>

  <!-- Glassmorphism Command Header -->
  <header>
    <div class="brand-section">
      <div class="brand-icon">🌐</div>
      <div class="brand-titles">
        <h1>RDSO Track Knowledge Graph Studio <span class="badge-ver">v3.0 ENTERPRISE</span></h1>
        <p>Deep Blueprint Extraction, Notes & Multi-Ontology Intelligence</p>
      </div>
    </div>

    <!-- Global Search -->
    <div class="search-wrapper">
      <span class="search-icon">🔍</span>
      <input type="text" id="global-search" class="search-input" placeholder="Search notes, BOM parts, sleepers, drawings...">
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
      <button class="btn" id="physics-tuner-btn" onclick="togglePhysicsPopover()">
        <span>⚙️</span> Physics
      </button>
      <button class="btn" onclick="exportGraph('cypher')">
        <span>💾</span> Cypher
      </button>
      <button class="btn btn-primary" onclick="openIngestModal()">
        <span>➕</span> Ingest Node
      </button>
    </div>
  </header>

  <!-- Floating Left Tool Dock -->
  <div id="left-tools-dock">
    <!-- Domain Filters -->
    <div class="dock-card">
      <div class="card-title">
        <span>Ontology Domains</span>
        <span style="font-size: 9px; color: var(--text-dim);">FILTER VIEW</span>
      </div>
      <div class="domain-chips-list" id="domain-chips-list">
        <!-- Dynamically rendered domain chips -->
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

    <!-- Simulation Actions -->
    <div class="dock-card">
      <div class="card-title">
        <span>Graph Tools</span>
      </div>
      <button class="btn" style="width: 100%; justify-content: center; background: rgba(255, 51, 102, 0.15); border-color: var(--accent-red); color: #ff6688; margin-bottom: 6px;" onclick="triggerActiveFailurePropagation()">
        <span>💥</span> Simulate Failure Propagation
      </button>
      <div class="dock-actions">
        <button class="btn" onclick="jiggleGraphPhysics()">
          <span>🔄</span> Jiggle
        </button>
        <button class="btn" id="physics-pause-btn" onclick="togglePhysicsPause()">
          <span>⏸</span> Pause
        </button>
      </div>
    </div>
  </div>

  <!-- Multi-Tab Entity Intelligence Drawer -->
  <div id="intelligence-drawer" class="collapsed">
    <div class="drawer-header">
      <div class="drawer-title-block">
        <div class="meta-tag" id="drawer-domain">COMPONENT ENTITY</div>
        <h2 id="drawer-title">Select Any 3D Node</h2>
      </div>
      <button class="close-drawer-btn" onclick="toggleIntelligenceDrawer(false)">✕</button>
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
          <span>🔍</span>
          <input type="text" id="notes-filter-input" class="notes-search-input" placeholder="Search verbatim notes (e.g. dowel, epoxy, 10%, versine)..." oninput="filterCurrentNotes(this.value)">
        </div>
        <div class="notes-list" id="drawer-notes-list">
          <!-- Populated dynamically -->
        </div>
      </div>

      <!-- 2. TAB: ENGINEERING TABLES & SCHEDULES -->
      <div class="tab-pane" id="tab-pane-tables">
        <div class="table-subnav" id="drawer-table-subnav">
          <!-- Dynamically populated table buttons (BOM, Sleepers 1-64, LIST-A, Gap Schedule, Versines) -->
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

        <button class="btn" id="drawer-blossom-btn" style="width: 100%; justify-content: center; background: rgba(157, 78, 221, 0.25); border-color: var(--accent-purple); color: #d094ff; display: none;" onclick="toggleCurrentBlossom()">
          🌸 Blossom Sub-Components in 3D
        </button>

        <div>
          <div class="card-title">Engineering Parameters & Standards</div>
          <table class="specs-table" id="drawer-specs-table"></table>
        </div>

        <div>
          <div class="card-title">Connected Ontology Hops</div>
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
      <span>ENTITIES:</span>
      <span class="telemetry-val" id="telem-nodes">32</span>
    </div>
    <div class="telemetry-item">
      <span>ACTIVE SPRINGS:</span>
      <span class="telemetry-val" id="telem-edges">46</span>
    </div>
    <div class="telemetry-item">
      <span>LAYOUT:</span>
      <span class="telemetry-val" id="telem-layout" style="color: var(--accent-cyan);">3D Cosmic Force</span>
    </div>
    <div class="telemetry-item">
      <span>SIMULATION:</span>
      <span class="telemetry-val" id="telem-sim" style="color: var(--accent-green);">LIVE 60 FPS</span>
    </div>
  </div>

  <!-- Floating Physics Tuner Popover -->
  <div id="physics-popover">
    <div class="card-title" style="margin-bottom: 12px;">
      <span>Physics Engine Parameters</span>
      <span style="font-size: 14px; cursor: pointer;" onclick="togglePhysicsPopover(false)">✕</span>
    </div>

    <div class="tuner-slider-row">
      <div class="tuner-label-val">
        <span>Coulomb Charge Repulsion</span>
        <span id="val-repulsion">55</span>
      </div>
      <input type="range" min="10" max="150" value="55" class="scrubber-slider" oninput="updatePhysicsParam('repulsion', this.value)">
    </div>

    <div class="tuner-slider-row">
      <div class="tuner-label-val">
        <span>Hooke Spring Stiffness</span>
        <span id="val-spring">0.06</span>
      </div>
      <input type="range" min="0.01" max="0.2" step="0.01" value="0.06" class="scrubber-slider" oninput="updatePhysicsParam('spring', this.value)">
    </div>

    <div class="tuner-slider-row">
      <div class="tuner-label-val">
        <span>Target Spring Length</span>
        <span id="val-length">4.5</span>
      </div>
      <input type="range" min="2" max="10" step="0.5" value="4.5" class="scrubber-slider" oninput="updatePhysicsParam('length', this.value)">
    </div>

    <div class="tuner-slider-row">
      <div class="tuner-label-val">
        <span>Verlet Velocity Damping</span>
        <span id="val-damping">0.88</span>
      </div>
      <input type="range" min="0.70" max="0.98" step="0.01" value="0.88" class="scrubber-slider" oninput="updatePhysicsParam('damping', this.value)">
    </div>
  </div>

  <!-- Ingestion Modal -->
  <div id="ingest-modal">
    <div class="modal-box">
      <h3><span>➕</span> Ingest Knowledge Node into 3D Ontology</h3>
      <div class="form-group">
        <label>Entity Title</label>
        <input type="text" id="in-node-title" class="form-control" placeholder="e.g. Ultrasonic Flaw Finding at Heel Sleeper 22">
      </div>
      <div class="form-group">
        <label>Domain</label>
        <select id="in-node-domain" class="form-control">
          <option value="drawing">Drawing & Standard (Blue)</option>
          <option value="component">Component & Metallurgy (Green)</option>
          <option value="signaling">S&T & Interlocking (Red)</option>
          <option value="specification">Track Physics & Spec (Amber)</option>
          <option value="defect">Failure Mode & Defect (Crimson)</option>
          <option value="sop">Maintenance SOP (Purple)</option>
        </select>
      </div>
      <div class="form-group">
        <label>Governing Parent Node</label>
        <select id="in-node-parent" class="form-control"></select>
      </div>
      <div class="form-group">
        <label>Ontology Relationship</label>
        <select id="in-node-relation" class="form-control">
          <option value="INCORPORATES">INCORPORATES</option>
          <option value="MOUNTS_ON">MOUNTS_ON</option>
          <option value="CLEARS_MECHANISM">CLEARS_MECHANISM</option>
          <option value="GOVERNED_BY_SOP">GOVERNED_BY_SOP</option>
          <option value="CAUSES_FAILURE">CAUSES_FAILURE</option>
          <option value="DETECTED_DEFECT">DETECTED_DEFECT</option>
        </select>
      </div>
      <div class="form-group">
        <label>Technical Field Notes</label>
        <textarea id="in-node-desc" class="form-control" rows="3" placeholder="Enter metallurgical properties, axle load conditions, or corrective actions..."></textarea>
      </div>
      <div style="display: flex; justify-content: flex-end; gap: 8px; margin-top: 6px;">
        <button class="btn" onclick="closeIngestModal()">Cancel</button>
        <button class="btn btn-primary" onclick="submitIngestNode()">Submit & Attach Springs</button>
      </div>
    </div>
  </div>

  <!-- Fullscreen Blueprint Modal -->
  <div id="blueprint-modal">
    <div class="blueprint-modal-header">
      <h3 style="font-size: 15px; color: #fff;" id="blueprint-modal-title">RDSO High-Resolution Blueprint Source Crop</h3>
      <button class="close-drawer-btn" onclick="closeFullscreenBlueprint()">✕</button>
    </div>
    <div class="blueprint-modal-body">
      <img id="blueprint-modal-img" class="blueprint-modal-img" src="" alt="RDSO Blueprint Full Resolution">
    </div>
  </div>

  <!-- APPLICATION LOGIC & EXTRACTED KNOWLEDGE DATABASE -->
  <script>
    // Embedded Exhaustive Extracted Database
    const RDSO_EXTRACTED_KNOWLEDGE = __EXTRACTED_KNOWLEDGE_JSON__;

    // Mapping of components to their governing drawings for deep knowledge access
    const COMPONENT_DRAWING_MAPPING = {
      drg_6155: "RDSO_T_6155",
      comp_chair: "RDSO_T_6155",
      comp_detailb: "RDSO_T_6155",
      comp_cpl: "RDSO_T_6155",
      sop_dowel: "RDSO_T_6155",
      sop_lista: "RDSO_T_6155",
      defect_chipping: "RDSO_T_6155",
      defect_fatigue: "RDSO_T_6155",

      drg_6154: "RDSO_T_6154",
      comp_sleeper: "RDSO_T_6154",
      comp_erc: "RDSO_T_6154",
      comp_grsp: "RDSO_T_6154",
      spec_throw: "RDSO_T_6154",

      drg_6216: "RDSO_T_6216",
      comp_ssd_unit: "RDSO_T_6216",
      spec_joh_gap: "RDSO_T_6216",

      drg_6280: "RDSO_T_6280",
      comp_cms_unit: "RDSO_T_6280",
      defect_cms_batter: "RDSO_T_6280",

      drg_6275: "RDSO_T_6275",
      comp_checkrail: "RDSO_T_6275",
      spec_flange: "RDSO_T_6275"
    };

    // Knowledge Graph Entities
    const rawKGNodes = [
      { id: "drg_6154", label: "RDSO/T-6154 (1:12 Turnout)", domain: "drawing", color: "#00f0ff", x: 0, y: 6, z: 0, alt: 6, desc: "Master layout of 1 in 12 Turnout 60 kg (UIC) on PSC Sleepers (64 sleepers total).", specs: { "Rail Section": "60 kg (UIC) / 60E1", "Gauge": "1673 mm", "Speed (Main)": "160 km/h", "Speed (Loop)": "50 km/h", "Turnout Radius": "441.36 m" } },
      { id: "drg_6155", label: "RDSO/T-6155 (Curved Switch)", domain: "drawing", color: "#00f0ff", x: -6, y: 4, z: 2, alt: 13, canBlossom: true, desc: "10125 mm Curved Switch with ZU-1-60/60E1A1 Thick-Web Tongue Rails on PSC Sleepers.", specs: { "Switch Length": "10125 mm", "Stock Rail": "13000 mm", "Tongue Rail": "12480 mm", "Throw at Toe": "160 mm", "Specification": "IRS: T 10" } },
      { id: "drg_6216", label: "RDSO/T-6216 (SSD Assembly)", domain: "drawing", color: "#3a86ff", x: -2, y: 3, z: -5, alt: 5, canBlossom: true, desc: "Spring Setting Device for Thick Web Switches at Sleeper 13 (JOH).", specs: { "Location": "Sleeper 13 (JOH)", "Nominal Gap": "60 mm", "Stroke": "160 mm", "Function": "Dynamic flangeway preservation" } },
      { id: "drg_6280", label: "RDSO/T-6280 (CMS Crossing)", domain: "drawing", color: "#00f0ff", x: 7, y: 4, z: 2, alt: 4, canBlossom: true, desc: "1 in 12 Cast Manganese Steel Crossing with special bearing plates.", specs: { "Angle": "1 in 12 (4° 45' 49\")", "Crossing Length": "4350 mm", "TNC Station": "Sleeper 48", "Specification": "IRS: T 29" } },
      { id: "drg_6275", label: "RDSO/T-6275 (Check Rails)", domain: "drawing", color: "#ff9d00", x: 4, y: 3, z: -5, alt: 4, desc: "Check Rail arrangement (5000 mm) with flared ends for 60 kg UIC turnout.", specs: { "Length": "5000 mm", "Flangeway": "44 mm (41-45 mm)", "Flare Openings": "89 mm", "Mounting": "Check blocks with high-tensile bolts" } },
      
      { id: "comp_chair", label: "Cast Steel Slide Chair (T-9616)", domain: "component", color: "#00ff88", x: -9, y: 0, z: 4, alt: 10, twinAsset: "slide_chair", desc: "Sleepers 04-20: machined elevated slide table supporting ZU-1-60 tongue rails.", specs: { "Material": "Cast Steel Gr 230-450W (IS:1030)", "Quantity": "34 per Turnout", "Fasteners": "4 Plate Screws T-3913", "Machined Table": "180 x 220 mm" } },
      { id: "comp_detailb", label: "Detail 'B' Bent Tie Bar (T-9010)", domain: "component", color: "#00ff88", x: -6, y: -1, z: 6, alt: 11, twinAsset: "bent_tiebar", desc: "Forged M.S. tie bar with 222 mm drop bend to clear S&T Clamp Lock drive rod.", specs: { "Drop Bend": "222 mm", "Bottom Span": "485 mm", "Material": "Mild Steel (IS: 2062)", "Clearance": "12 mm over sleeper" } },
      { id: "comp_cpl", label: "Clamp Point Lock (S-3454)", domain: "signaling", color: "#ff3366", x: -8, y: -4, z: 8, alt: 8, twinAsset: "clamp_lock", desc: "Signal interlocking point lock machine ensuring positive tongue rail closure.", specs: { "Throw Stroke": "220 mm", "Drive Rod": "Solid forged steel", "Safety Integrity": "SIL 4", "Clearance Required": "222 mm under rail foot" } },
      { id: "comp_ssd_unit", label: "SSD Spring Mechanism", domain: "component", color: "#00ff88", x: -2, y: -1, z: -7, alt: 5, twinAsset: "ssd_unit", desc: "Helical spring and turnbuckle unit maintaining 60 mm heel clearance.", specs: { "Spring Wire": "18 mm Cr-V Spring Steel", "Pre-compression": "35 mm", "Turnbuckle": "M24 Left/Right Thread", "Insulation": "Nylon-66 Bushing" } },
      { id: "comp_cms_unit", label: "CMS Monoblock Unit (T-6279)", domain: "component", color: "#00ff88", x: 9, y: 0, z: 4, alt: 2, twinAsset: "cms_crossing", desc: "Austenitic manganese casting, initial 220 BHN work-hardening to 350 BHN.", specs: { "Initial Hardness": "220 BHN", "Work Hardened": "350 BHN", "Metallurgy": "12-14% Mn, 1.2% C", "Testing": "Radiographic Class 1" } },
      { id: "comp_checkrail", label: "Check Rail Unit (T-6275)", domain: "component", color: "#00ff88", x: 5, y: -1, z: -7, alt: 4, twinAsset: "check_rail", desc: "High carbon guard rail preventing wheel flange derailment past the unguided crossing gap.", specs: { "Profile": "60 kg UIC Machined", "Flangeway": "44 mm", "Tension": "High tensile clamp bolts", "Torque": "380 N-m" } },
      { id: "comp_erc", label: "Elastic Rail Clip Mk-V (T-5919)", domain: "component", color: "#00ff88", x: -4, y: 1, z: -2, alt: 6, twinAsset: "erc_clip", desc: "Heavy-duty 23 mm diameter elastic rail clip providing 1200-1500 kgf toe load.", specs: { "Diameter": "23 mm", "Material": "55Si7 Spring Steel", "Toe Load": "1200 - 1500 kgf", "Toe Deflection": "13.5 mm" } },
      { id: "comp_grsp", label: "10 mm GRSP Pad (T-3711)", domain: "component", color: "#00ff88", x: -1, y: 0, z: 2, alt: 7, twinAsset: "grsp_pad", desc: "High-attenuation grooved rubber sole plate absorbing 25t axle dynamic impact.", specs: { "Thickness": "10 mm", "Material": "Natural Rubber Compound", "Volume Resistivity": "10^8 ohm-cm", "Tensile Strength": "> 12 MPa" } },
      { id: "comp_sleeper", label: "PSC Turnout Sleeper (T-4219)", domain: "component", color: "#00ff88", x: 1, y: -2, z: 0, alt: 8, twinAsset: "psc_sleeper", desc: "Prestressed concrete turnout sleeper with recessed canted rail seats.", specs: { "Concrete Grade": "M60", "Prestressing Wires": "18 x 3 mm HTS", "Weight": "285 kg", "Fastener Inserts": "SGCI Dowels (Note 25/26)" } },

      { id: "spec_flange", label: "Check Flangeway: 44 mm", domain: "specification", color: "#ffd60a", x: 6, y: -4, z: -4, alt: 1, desc: "Critical safety clearance preventing wheel flanges from striking crossing nose.", specs: { "Nominal": "44 mm", "Min Permissible": "41 mm", "Max Permissible": "45 mm", "Inspection Frequency": "Monthly" } },
      { id: "spec_joh_gap", label: "JOH Flangeway: 60 mm", domain: "specification", color: "#ffd60a", x: -3, y: -4, z: -6, alt: 1, desc: "Minimum clearance between tongue and stock rail at Junction of Head.", specs: { "Nominal": "60 mm", "Min Permissible": "58 mm", "Governing Component": "SSD (RDSO/T-6216)", "Wheel Gauge Tolerance": "+3 / -1 mm" } },
      { id: "spec_drop", label: "Tie Bar Drop: 222 mm", domain: "specification", color: "#ffd60a", x: -5, y: -4, z: 4, alt: 11, desc: "Physical clearance requirement avoiding collision with S&T Point Machine drive rods.", specs: { "Drop Dimension": "222 mm", "Bottom Length": "485 mm", "Tolerance": "± 2.0 mm", "Mandated Revision": "Alt 11 (Note 21)" } },
      
      { id: "sop_dowel", label: "Epoxy Dowel Retrofit (Note 25/26)", domain: "sop", color: "#9d4edd", x: -10, y: -3, z: 2, alt: 12, desc: "Repair procedure for stripped sleeper inserts: 35x165 mm core, IS:12994 L-100 epoxy, 24 hr cure.", specs: { "Core Hole": "35 mm Dia x 165 mm Depth", "Resin": "Epoxy L-100 (IS:12994)", "Cure Time": "24 Hours Mandatory", "Tensile Pull-out": "> 65 kN" } },
      { id: "sop_lista", label: "LIST - A Spares 10% (Note 28)", domain: "sop", color: "#9d4edd", x: -9, y: 5, z: -2, alt: 13, desc: "Mandatory procurement buffer enforcing 10% inventory on 24 critical wear/breakage components.", specs: { "Buffer Rate": "10% of Turnout Bill of Materials", "Components Covered": "24 High-Wear Items", "Compliance Audit": "Pre-commissioning mandatory" } },
      { id: "sop_usfd", label: "USFD Ultrasonic Flaw Detection", domain: "sop", color: "#9d4edd", x: 4, y: 6, z: 5, alt: 3, desc: "Non-destructive testing protocol scanning tongue rail machined joints and crossing noses.", specs: { "Probe Angle": "70° Tandem + 0° Normal", "Scan Interval": "Every 4 GMT traffic", "Flaw Classification": "IMR / REM / OBS" } },

      { id: "defect_fatigue", label: "Joint 'M' Fatigue Crack", domain: "defect", color: "#ff3366", x: -4, y: -6, z: 0, alt: 9, desc: "Machined Joint 'M' stress concentration fracture under 25t axle hunting loads -> eliminated by Welded Joint 'W'.", specs: { "Failure Cause": "Machining stress notch + 25t axle loads", "Resolution": "Alt 10: Welded Joint 'W'", "Risk Level": "CRITICAL DERAILMENT" } },
      { id: "defect_chipping", label: "Tongue Rail Toe Chipping", domain: "defect", color: "#ff3366", x: -7, y: -6, z: 2, alt: 5, desc: "Wheel flange back-strike against switch rail toe due to incorrect switch opening or worn slide chairs.", specs: { "Permissible Chipping": "Max 200 mm length x 6 mm depth", "Mitigation": "Ensure 160 mm throw & lubricate chairs" } },
      { id: "defect_grsp_crush", label: "10 mm GRSP Pad Crushing", domain: "defect", color: "#ff3366", x: -1, y: -5, z: 4, alt: 7, desc: "Pad degradation under heavy freight routes causing severe toe load loss and rail cant distortion.", specs: { "Consequence": "Toe load drops below 800 kgf", "Secondary Risk": "ERC clip fallout & gauge widening" } },
      { id: "defect_cms_batter", label: "CMS Nose Flow & Battering", domain: "defect", color: "#ff3366", x: 8, y: -4, z: 6, alt: 3, desc: "Manganese metal flow and work hardening spall at Actual Nose of Crossing (ANC).", specs: { "Wear Limit": "10 mm vertical wear", "Rectification": "Translamatic robotic welding / hardfacing" } }
    ];

    const rawKGEdges = [
      { from: "drg_6154", to: "drg_6155", rel: "INCORPORATES_SWITCH" },
      { from: "drg_6154", to: "drg_6216", rel: "INTEGRATES_SSD" },
      { from: "drg_6154", to: "drg_6280", rel: "INCORPORATES_CROSSING" },
      { from: "drg_6154", to: "drg_6275", rel: "INCORPORATES_CHECK_RAIL" },
      { from: "drg_6154", to: "comp_sleeper", rel: "RESTS_ON_SLEEPERS" },
      { from: "drg_6155", to: "comp_chair", rel: "MOUNTS_ON_CHAIRS" },
      { from: "drg_6155", to: "comp_detailb", rel: "INCORPORATES_TIEBAR" },
      { from: "drg_6155", to: "comp_erc", rel: "FASTENED_BY" },
      { from: "drg_6155", to: "comp_grsp", rel: "ISOLATED_BY_PAD" },
      { from: "comp_detailb", to: "comp_cpl", rel: "CLEARS_MECHANISM" },
      { from: "comp_detailb", to: "spec_drop", rel: "ENFORCES_DIMENSION" },
      { from: "drg_6216", to: "comp_ssd_unit", rel: "CONTAINS_MECHANISM" },
      { from: "comp_ssd_unit", to: "spec_joh_gap", rel: "MAINTAINS_GAP" },
      { from: "drg_6280", to: "comp_cms_unit", rel: "INCLUDES_CASTING" },
      { from: "drg_6275", to: "comp_checkrail", rel: "ASSEMBLES_GUARD" },
      { from: "comp_checkrail", to: "spec_flange", rel: "ENFORCES_CLEARANCE" },
      { from: "spec_flange", to: "comp_cms_unit", rel: "PROTECTS_NOSE" },
      { from: "comp_chair", to: "comp_sleeper", rel: "ANCHORED_INTO" },
      { from: "comp_chair", to: "sop_dowel", rel: "GOVERNED_BY_RETROFIT" },
      { from: "drg_6155", to: "sop_lista", rel: "MANDATES_BUFFER" },
      { from: "drg_6155", to: "defect_fatigue", rel: "HISTORICAL_FAILURE" },
      { from: "comp_chair", to: "defect_chipping", rel: "DEFECT_PROPAGATION" },
      { from: "comp_grsp", to: "defect_grsp_crush", rel: "DEGRADATION_MODE" },
      { from: "comp_cms_unit", to: "defect_cms_batter", rel: "WEAR_PROFILE" },
      { from: "sop_usfd", to: "defect_fatigue", rel: "DETECTS" },
      { from: "sop_usfd", to: "defect_cms_batter", rel: "MONITORS" }
    ];

    const blossomRegistry = {
      drg_6216: [
        { id: "ssd_p1", label: "Helical Spring (T-6217/1)", domain: "component", color: "#00ff88", desc: "Heavy chrome-vanadium compression spring absorbing 25t lateral wheel impacts." },
        { id: "ssd_p4", label: "Turnbuckle & Rod (T-6217/4)", domain: "component", color: "#00ff88", desc: "M24 reverse threaded adjustment turnbuckle for field setting of 60 mm heel clearance." },
        { id: "ssd_p2", label: "Mounting Bracket (T-6217/2)", domain: "component", color: "#00ff88", desc: "Rigid anchor bracket fastened to Sleeper 13 turnout tie plate." },
        { id: "ssd_p12", label: "Insulating Bush (T-6217/12)", domain: "signaling", color: "#ff3366", desc: "Nylon-66 insulating bush maintaining 100% track circuit signal isolation." }
      ],
      drg_6155: [
        { id: "sw_tl", label: "Left ZU-1-60 Tongue Rail", domain: "component", color: "#00ff88", desc: "12480 mm asymmetric thick-web tongue rail with machined foot and 1:20 cant." },
        { id: "sw_tr", label: "Right ZU-1-60 Tongue Rail", domain: "component", color: "#00ff88", desc: "Curved ZU-1-60 tongue rail machined for turnout lead curve alignment." },
        { id: "sw_screws", label: "Plate Screws T-3913", domain: "component", color: "#00ff88", desc: "High tensile M22 plate screws securing slide chairs into sleeper dowels." }
      ],
      drg_6280: [
        { id: "cms_nose", label: "Theoretical Nose of Crossing", domain: "specification", color: "#ffd60a", desc: "Geometric apex at Sleeper 48 with 1 in 12 divergence angle." },
        { id: "cms_plates", label: "Special Crossing Baseplates", domain: "component", color: "#00ff88", desc: "Continuous heavy steel bearing plates spanning Sleepers 46 to 50." }
      ]
    };

    const DOMAIN_METADATA = {
      drawing: { label: "Drawings & Standards", color: "#00f0ff", icon: "📐" },
      component: { label: "Components & Metallurgy", color: "#00ff88", icon: "⚙️" },
      signaling: { label: "S&T & Interlocking", color: "#ff3366", icon: "⚡" },
      specification: { label: "Track Physics & Tolerances", color: "#ffd60a", icon: "🔬" },
      defect: { label: "Failure Modes & Defects", color: "#ff3366", icon: "⚠️" },
      sop: { label: "Maintenance SOPs", color: "#9d4edd", icon: "📋" }
    };

    // Global App State
    let kgScene, kgCamera, kgRenderer, kgControls;
    let kgPhysicsNodes = [];
    let kgPhysicsEdges = [];
    let currentLayout = "cosmic";
    let currentSelectedNode = null;
    let currentActiveDossier = null;
    let currentActiveCrop = null;
    let blossomedNodesMap = {};
    let activeFilterDomain = "all";
    let isPhysicsPaused = false;

    // Simulation Parameters
    let k_repulsion = 55.0;
    let k_spring = 0.06;
    let l0_spring = 4.5;
    let damping = 0.88;

    function initKnowledgeGraphApp() {
      const container = document.getElementById('kg-canvas-container');
      const w = window.innerWidth;
      const h = window.innerHeight;

      // 1. Scene & Background
      kgScene = new THREE.Scene();
      kgScene.background = new THREE.Color(0x060911);
      kgScene.fog = new THREE.FogExp2(0x060911, 0.015);

      // Starfield Particle Background
      const starGeo = new THREE.BufferGeometry();
      const starCount = 1200;
      const starPos = new Float32Array(starCount * 3);
      for (let i = 0; i < starCount * 3; i += 3) {
        starPos[i] = (Math.random() - 0.5) * 140;
        starPos[i + 1] = (Math.random() - 0.5) * 140;
        starPos[i + 2] = (Math.random() - 0.5) * 140;
      }
      starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
      const starMat = new THREE.PointsMaterial({ color: 0x304466, size: 0.8, transparent: true, opacity: 0.6 });
      const starField = new THREE.Points(starGeo, starMat);
      kgScene.add(starField);

      // 2. Camera & Orbit Controls
      kgCamera = new THREE.PerspectiveCamera(45, w / h, 0.1, 1000);
      kgCamera.position.set(0, 14, 32);

      kgRenderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
      kgRenderer.setSize(w, h);
      kgRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      container.appendChild(kgRenderer.domElement);

      kgControls = new THREE.OrbitControls(kgCamera, kgRenderer.domElement);
      kgControls.enableDamping = true;
      kgControls.dampingFactor = 0.06;
      kgControls.maxDistance = 120;
      kgControls.minDistance = 3;

      // 3. Lighting
      const ambLight = new THREE.AmbientLight(0xffffff, 0.9);
      kgScene.add(ambLight);

      const dirLight = new THREE.DirectionalLight(0x00f0ff, 1.2);
      dirLight.position.set(20, 40, 30);
      kgScene.add(dirLight);

      const backLight = new THREE.DirectionalLight(0x9d4edd, 0.8);
      backLight.position.set(-20, -30, -20);
      kgScene.add(backLight);

      // 4. Ingest Initial Nodes & Edges
      rawKGNodes.forEach(n => addNodeToGraph(n));
      rawKGEdges.forEach(e => addEdgeToGraph(e));

      // 5. Initialize UI Components
      renderDomainChips();
      populateParentSelect();
      initSearchAutocomplete();
      initComponentTwinViewer();

      // 6. Animation Loop
      function animate() {
        requestAnimationFrame(animate);
        if (!isPhysicsPaused) {
          stepGraphPhysics();
        }
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
      ctx.font = "bold 15px -apple-system, sans-serif";
      ctx.fillText(domain.toUpperCase(), 14, 26);

      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 18px -apple-system, sans-serif";
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

      if (data.domain === "drawing") {
        const sphereGeo = new THREE.SphereGeometry(0.75, 24, 24);
        const sphereMat = new THREE.MeshStandardMaterial({ color: colorObj, emissive: colorObj, emissiveIntensity: 0.55, metalness: 0.8, roughness: 0.2 });
        coreMesh = new THREE.Mesh(sphereGeo, sphereMat);
        nodeGroup.add(coreMesh);

        const ringGeo = new THREE.RingGeometry(1.0, 1.25, 32);
        const ringMat = new THREE.MeshBasicMaterial({ color: colorObj, side: THREE.DoubleSide, transparent: true, opacity: 0.45 });
        const ringMesh = new THREE.Mesh(ringGeo, ringMat);
        ringMesh.rotation.x = Math.PI / 2.5;
        nodeGroup.add(ringMesh);
      } else if (data.domain === "signaling") {
        const cylGeo = new THREE.CylinderGeometry(0.65, 0.65, 0.8, 6);
        const cylMat = new THREE.MeshStandardMaterial({ color: colorObj, emissive: colorObj, emissiveIntensity: 0.6, metalness: 0.5, roughness: 0.3 });
        coreMesh = new THREE.Mesh(cylGeo, cylMat);
        nodeGroup.add(coreMesh);
      } else if (data.domain === "defect") {
        const octGeo = new THREE.OctahedronGeometry(0.7, 0);
        const octMat = new THREE.MeshStandardMaterial({ color: colorObj, emissive: colorObj, emissiveIntensity: 0.7, metalness: 0.4, roughness: 0.2 });
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

      nodeGroup.position.set(data.x || 0, data.y || 0, data.z || 0);
      kgScene.add(nodeGroup);

      const nodeObj = {
        data: data,
        group: nodeGroup,
        mesh: coreMesh,
        sprite: sprite,
        x: data.x || 0, y: data.y || 0, z: data.z || 0,
        vx: (Math.random() - 0.5) * 0.05,
        vy: (Math.random() - 0.5) * 0.05,
        vz: (Math.random() - 0.5) * 0.05,
        targetX: data.x || 0, targetY: data.y || 0, targetZ: data.z || 0
      };

      kgPhysicsNodes.push(nodeObj);
      updateTelemetryCounters();
      return nodeObj;
    }

    function addEdgeToGraph(edgeData) {
      const lineMat = new THREE.LineBasicMaterial({ color: 0x00f0ff, transparent: true, opacity: 0.45, linewidth: 1.5 });
      const dummyGeo = new THREE.BufferGeometry();
      const lineMesh = new THREE.Line(dummyGeo, lineMat);
      kgScene.add(lineMesh);

      kgPhysicsEdges.push({
        from: edgeData.from,
        to: edgeData.to,
        rel: edgeData.rel,
        line: lineMesh
      });
      updateTelemetryCounters();
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

          n1.vx -= fx * 0.01; n1.vy -= fy * 0.01; n1.vz -= fz * 0.01;
          n2.vx += fx * 0.01; n2.vy += fy * 0.01; n2.vz += fz * 0.01;
        }
      }

      kgPhysicsEdges.forEach(e => {
        const n1 = kgPhysicsNodes.find(n => n.data.id === e.from);
        const n2 = kgPhysicsNodes.find(n => n.data.id === e.to);
        if (!n1 || !n2 || !n1.group.visible || !n2.group.visible) return;

        const dx = n2.x - n1.x;
        const dy = n2.y - n1.y;
        const dz = n2.z - n1.z;
        const d = Math.sqrt(dx * dx + dy * dy + dz * dz) + 0.001;

        const displacement = d - l0_spring;
        const force = k_spring * displacement;
        const fx = (dx / d) * force;
        const fy = (dy / d) * force;
        const fz = (dz / d) * force;

        n1.vx += fx; n1.vy += fy; n1.vz += fz;
        n2.vx -= fx; n2.vy -= fy; n2.vz -= fz;
      });

      kgPhysicsNodes.forEach(n => {
        if (!n.group.visible) return;
        n.vx -= n.x * 0.004;
        n.vy -= n.y * 0.004;
        n.vz -= n.z * 0.004;

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
        n.y += (0 - n.y) * 0.15;
        n.vy = 0;
      });
    }

    function interpolateToTargets() {
      kgPhysicsNodes.forEach(n => {
        n.x += (n.targetX - n.x) * 0.1;
        n.y += (n.targetY - n.y) * 0.1;
        n.z += (n.targetZ - n.z) * 0.1;
      });
    }

    function switchGraphLayout(mode) {
      currentLayout = mode;
      document.querySelectorAll('.layout-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.layout === mode);
      });

      const labelMap = {
        cosmic: "3D Cosmic Force",
        planar: "2D Planar Topological",
        dag: "Hierarchical Dependency DAG",
        concentric: "Concentric Radial Orbit"
      };
      document.getElementById('telem-layout').innerText = labelMap[mode] || mode;

      if (mode === "dag") computeHierarchicalLayout();
      else if (mode === "concentric") computeConcentricLayout(currentSelectedNode ? currentSelectedNode.data.id : "drg_6154");
      else if (mode === "planar") {
        kgControls.target.set(0, 0, 0);
        kgCamera.position.set(0, 35, 0.01);
        kgControls.update();
      } else if (mode === "cosmic") jiggleGraphPhysics();
    }

    function computeHierarchicalLayout() {
      const layers = {
        drawing: { y: 8, items: [] },
        component: { y: 2, items: [] },
        signaling: { y: -2, items: [] },
        specification: { y: -5, items: [] },
        defect: { y: -8, items: [] },
        sop: { y: -8, items: [] }
      };

      kgPhysicsNodes.forEach(n => {
        const dom = n.data.domain || "component";
        if (layers[dom]) layers[dom].items.push(n);
        else layers.component.items.push(n);
      });

      Object.values(layers).forEach(layer => {
        const count = layer.items.length;
        const span = Math.min(count * 3.5, 36);
        layer.items.forEach((n, idx) => {
          const x = count === 1 ? 0 : -span / 2 + (span / (count - 1)) * idx;
          n.targetX = x;
          n.targetY = layer.y;
          n.targetZ = (Math.random() - 0.5) * 2;
        });
      });

      kgControls.target.set(0, 0, 0);
      kgCamera.position.set(0, 0, 36);
      kgControls.update();
    }

    function computeConcentricLayout(centerId) {
      const centerNode = kgPhysicsNodes.find(n => n.data.id === centerId) || kgPhysicsNodes[0];
      if (!centerNode) return;

      centerNode.targetX = 0; centerNode.targetY = 0; centerNode.targetZ = 0;

      const hop1Ids = [];
      kgPhysicsEdges.forEach(e => {
        if (e.from === centerId) hop1Ids.push(e.to);
        if (e.to === centerId) hop1Ids.push(e.from);
      });

      const uniqueHop1 = [...new Set(hop1Ids)];
      const r1 = 8.5;
      uniqueHop1.forEach((id, idx) => {
        const node = kgPhysicsNodes.find(n => n.data.id === id);
        if (node) {
          const angle = (Math.PI * 2 / uniqueHop1.length) * idx;
          node.targetX = Math.cos(angle) * r1;
          node.targetY = Math.sin(angle) * r1 * 0.4;
          node.targetZ = Math.sin(angle) * r1;
        }
      });

      const outerNodes = kgPhysicsNodes.filter(n => n.data.id !== centerId && !uniqueHop1.includes(n.data.id));
      const r2 = 17.0;
      outerNodes.forEach((node, idx) => {
        const angle = (Math.PI * 2 / outerNodes.length) * idx;
        node.targetX = Math.cos(angle) * r2;
        node.targetY = Math.sin(angle) * r2 * 0.35;
        node.targetZ = Math.sin(angle) * r2;
      });

      kgControls.target.set(0, 0, 0);
      kgCamera.position.set(0, 18, 30);
      kgControls.update();
    }

    function jiggleGraphPhysics() {
      kgPhysicsNodes.forEach(n => {
        n.vx += (Math.random() - 0.5) * 0.6;
        n.vy += (Math.random() - 0.5) * 0.6;
        n.vz += (Math.random() - 0.5) * 0.6;
      });
    }

    function togglePhysicsPause() {
      isPhysicsPaused = !isPhysicsPaused;
      const btn = document.getElementById('physics-pause-btn');
      btn.innerHTML = isPhysicsPaused ? "<span>▶</span> Resume" : "<span>⏸</span> Pause";
      document.getElementById('telem-sim').innerText = isPhysicsPaused ? "PAUSED" : "LIVE 60 FPS";
      document.getElementById('telem-sim').style.color = isPhysicsPaused ? "var(--accent-orange)" : "var(--accent-green)";
    }

    // =========================================================================
    // MULTI-TAB ENTITY INTELLIGENCE DRAWER LOGIC
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

      // Highlight Connected Edges
      kgPhysicsEdges.forEach(e => {
        if (e.from === data.id || e.to === data.id) {
          e.line.material.color.setHex(0xffd60a);
          e.line.material.opacity = 0.95;
        } else {
          e.line.material.color.setHex(0x00f0ff);
          e.line.material.opacity = 0.2;
        }
      });

      // Update Intelligence Drawer Header
      document.getElementById('drawer-domain').innerText = (DOMAIN_METADATA[data.domain]?.label || data.domain).toUpperCase();
      document.getElementById('drawer-domain').style.color = data.color;
      document.getElementById('drawer-title').innerText = data.label;

      // Find governing drawing dossier
      const dossierKey = COMPONENT_DRAWING_MAPPING[data.id] || (data.domain === "drawing" ? data.id.replace("drg_", "RDSO_T_") : "RDSO_T_6155");
      currentActiveDossier = RDSO_EXTRACTED_KNOWLEDGE[dossierKey] || RDSO_EXTRACTED_KNOWLEDGE["RDSO_T_6155"];

      // 1. Render Notes Tab
      renderDossierNotes(currentActiveDossier);

      // 2. Render Tables Tab
      renderDossierTables(currentActiveDossier);

      // 3. Render Blueprint Tab
      renderDossierBlueprints(currentActiveDossier);

      // 4. Render 3D Twin & Specs Tab
      renderComponentPhysicalTwin(data.twinAsset || data.id);

      const specsTable = document.getElementById('drawer-specs-table');
      specsTable.innerHTML = '';
      const specs = data.specs || { "Designation": data.label, "Domain": data.domain, "Standard": "IRS / RDSO" };
      Object.entries(specs).forEach(([k, v]) => {
        const row = document.createElement('tr');
        row.innerHTML = `<td>${k}</td><td>${v}</td>`;
        specsTable.appendChild(row);
      });

      // Connected Hops
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
          tag.innerHTML = `<span>${h.type === 'out' ? '➔' : '⬅'}</span> <span>${targetNode.data.label}</span>`;
          tag.onclick = () => inspectNode(targetNode);
          lineageList.appendChild(tag);
        }
      });

      // Blossom Button
      const blossomBtn = document.getElementById('drawer-blossom-btn');
      if (data.canBlossom || blossomRegistry[data.id]) {
        blossomBtn.style.display = "flex";
        const isBlossomed = blossomedNodesMap[data.id];
        blossomBtn.innerText = isBlossomed ? "🌸 Collapse Sub-Components" : "🌸 Blossom Sub-Components in 3D";
      } else {
        blossomBtn.style.display = "none";
      }

      // 5. Render Risks Tab
      const riskBox = document.getElementById('drawer-risk-box');
      if (data.domain === "defect") {
        document.getElementById('drawer-risk-title').innerText = data.label;
        document.getElementById('drawer-risk-desc').innerText = data.desc;
      } else {
        document.getElementById('drawer-risk-title').innerText = "Tethered Engineering Safeguard";
        document.getElementById('drawer-risk-desc').innerText = data.desc || "Strict adherence to tolerances prevents derailment hazards.";
      }

      // Open Drawer
      toggleIntelligenceDrawer(true);
    }

    window.selectGraphNode = function(idOrQuery) {
      if (!idOrQuery) return false;
      const q = String(idOrQuery).toLowerCase().trim();
      // Try exact id match
      let node = kgPhysicsNodes.find(n => n.data.id === idOrQuery || n.data.id.toLowerCase() === q);
      // Try fuzzy / alias matches
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
          <div class="note-header">
            <span class="note-num-badge">NOTE ${note.num}</span>
            <span style="font-size: 9.5px; color: var(--text-dim); font-family: var(--font-mono);">${dossier.drawing_number}</span>
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

      // Show First Table by default
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
      } else if (tableId === "gap") {
        let html = `
          <table class="rdso-table">
            <thead>
              <tr>
                <th>Turnout Ratio</th>
                <th>Switch Drg</th>
                <th>Sleeper #</th>
                <th>Hole Dist.</th>
                <th>Tongue Mouth</th>
                <th>Nominal Gap</th>
              </tr>
            </thead>
            <tbody>
        `;
        (dossier.switch_gap_schedule || []).forEach(row => {
          html += `
            <tr>
              <td style="font-weight: 800; color: var(--accent-cyan);">${row.turnout_ratio}</td>
              <td>${row.switch_drg}</td>
              <td style="font-weight: 700;">Sl ${row.ssd_sleeper_no}</td>
              <td>${row.distance_from_cl_mm} mm</td>
              <td>Sleepers ${row.tongue_mouth_sleepers}</td>
              <td style="color: var(--accent-green); font-weight: 800;">${row.nominal_gap_mm} mm</td>
            </tr>
          `;
        });
        html += '</tbody></table>';
        content.innerHTML = html;
      } else if (tableId === "alts") {
        let html = `
          <table class="rdso-table">
            <thead>
              <tr>
                <th>Alt</th>
                <th>Date</th>
                <th>Engineering Alteration Description</th>
              </tr>
            </thead>
            <tbody>
        `;
        (dossier.alteration_history || []).forEach(row => {
          html += `
            <tr>
              <td style="font-weight: 800; color: var(--accent-orange);">Alt ${row.alt}</td>
              <td style="font-family: var(--font-mono); font-size: 10px; color: var(--text-muted);">${row.date}</td>
              <td style="font-size: 11px;">${row.desc}</td>
            </tr>
          `;
        });
        html += '</tbody></table>';
        content.innerHTML = html;
      }
    }

    function renderDossierBlueprints(dossier) {
      const select = document.getElementById('blueprint-crop-select');
      const img = document.getElementById('blueprint-crop-img');
      select.innerHTML = '';

      const crops = dossier.crops || {};
      const cropKeys = Object.keys(crops);

      if (cropKeys.length === 0) {
        img.src = "";
        img.style.display = "none";
        return;
      }

      img.style.display = "block";
      cropKeys.forEach(k => {
        const opt = document.createElement('option');
        opt.value = crops[k];
        opt.innerText = k.replace('_', ' ').toUpperCase();
        select.appendChild(opt);
      });

      currentActiveCrop = crops[cropKeys[0]];
      img.src = currentActiveCrop;
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

    // =========================================================================
    // EMBEDDED 3D PHYSICAL DIGITAL TWIN INSPECTOR
    // =========================================================================
    let twinScene, twinCamera, twinRenderer, twinControls, twinAssetGroup;

    function initComponentTwinViewer() {
      const canvas = document.getElementById('component-twin-canvas');
      const box = document.getElementById('twin-box');
      const w = box.clientWidth || 440;
      const h = 220;

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

      const amb = new THREE.AmbientLight(0xffffff, 0.9);
      twinScene.add(amb);

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
      while (twinAssetGroup.children.length > 0) {
        twinAssetGroup.remove(twinAssetGroup.children[0]);
      }

      const matSteel = new THREE.MeshStandardMaterial({ color: 0x8a99ad, metalness: 0.85, roughness: 0.25 });
      const matCastChair = new THREE.MeshStandardMaterial({ color: 0xd4a017, metalness: 0.65, roughness: 0.35 });
      const matSlideTable = new THREE.MeshStandardMaterial({ color: 0xddccaa, metalness: 0.9, roughness: 0.15 });
      const matERC = new THREE.MeshStandardMaterial({ color: 0x00ff88, metalness: 0.75, roughness: 0.3 });
      const matConcrete = new THREE.MeshStandardMaterial({ color: 0x5a6370, roughness: 0.85 });

      document.getElementById('twin-badge-text').innerText = "PHYSICAL 3D ASSET TWIN: " + assetKey.toUpperCase();

      if (assetKey === "slide_chair" || assetKey === "comp_chair") {
        const base = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.04, 0.35), matCastChair);
        const table = new THREE.Mesh(new THREE.BoxGeometry(0.24, 0.04, 0.3), matSlideTable);
        table.position.set(0.1, 0.04, 0);
        const rib = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.08, 0.32), matCastChair);
        rib.position.set(-0.16, 0.04, 0);
        twinAssetGroup.add(base);
        twinAssetGroup.add(table);
        twinAssetGroup.add(rib);
        twinCamera.position.set(0.6, 0.4, 0.6);
      } else if (assetKey === "bent_tiebar" || assetKey === "comp_detailb") {
        const topBar = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.02, 0.6), matSteel);
        const drop1 = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.22, 0.02), matSteel);
        drop1.position.set(0, -0.11, -0.2);
        const drop2 = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.22, 0.02), matSteel);
        drop2.position.set(0, -0.11, 0.2);
        const lowerBar = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.02, 0.4), matSteel);
        lowerBar.position.set(0, -0.22, 0);
        twinAssetGroup.add(topBar);
        twinAssetGroup.add(drop1);
        twinAssetGroup.add(drop2);
        twinAssetGroup.add(lowerBar);
        twinCamera.position.set(0.6, 0.2, 0.6);
      } else if (assetKey === "erc_clip" || assetKey === "comp_erc") {
        const curve = new THREE.CatmullRomCurve3([
          new THREE.Vector3(0, 0, 0),
          new THREE.Vector3(0.08, 0.16, 0),
          new THREE.Vector3(0.24, 0.2, 0.08),
          new THREE.Vector3(0.32, 0.08, 0.12),
          new THREE.Vector3(0.2, 0.04, 0.16),
          new THREE.Vector3(0.08, 0.08, 0.08)
        ]);
        const tube = new THREE.Mesh(new THREE.TubeGeometry(curve, 24, 0.024, 8, false), matERC);
        twinAssetGroup.add(tube);
        twinCamera.position.set(0.5, 0.3, 0.5);
      } else if (assetKey === "ssd_unit" || assetKey === "drg_6216") {
        const cyl = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.6, 16), new THREE.MeshStandardMaterial({ color: 0x3366cc }));
        cyl.rotation.z = Math.PI / 2;
        const turnbuckle = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.12, 0.16), matSteel);
        turnbuckle.position.set(0.35, 0, 0);
        twinAssetGroup.add(cyl);
        twinAssetGroup.add(turnbuckle);
        twinCamera.position.set(0.6, 0.3, 0.6);
      } else if (assetKey === "cms_crossing" || assetKey === "comp_cms_unit" || assetKey === "drg_6280") {
        const cmsBody = new THREE.Mesh(new THREE.BoxGeometry(0.25, 0.12, 0.8), new THREE.MeshStandardMaterial({ color: 0xa0b0c0, metalness: 0.9 }));
        const wingL = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.14, 0.6), matSteel);
        wingL.position.set(-0.16, 0.02, 0);
        const wingR = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.14, 0.6), matSteel);
        wingR.position.set(0.16, 0.02, 0);
        twinAssetGroup.add(cmsBody);
        twinAssetGroup.add(wingL);
        twinAssetGroup.add(wingR);
        twinCamera.position.set(0.7, 0.4, 0.7);
      } else if (assetKey === "psc_sleeper" || assetKey === "comp_sleeper") {
        const sleeper = new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.14, 0.22), matConcrete);
        const pad1 = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.015, 0.18), new THREE.MeshStandardMaterial({ color: 0x111115 }));
        pad1.position.set(-0.25, 0.075, 0);
        const pad2 = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.015, 0.18), new THREE.MeshStandardMaterial({ color: 0x111115 }));
        pad2.position.set(0.25, 0.075, 0);
        twinAssetGroup.add(sleeper);
        twinAssetGroup.add(pad1);
        twinAssetGroup.add(pad2);
        twinCamera.position.set(0.7, 0.4, 0.7);
      } else {
        const rail = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.18, 0.8), matSteel);
        twinAssetGroup.add(rail);
        twinCamera.position.set(0.6, 0.3, 0.6);
      }

      twinControls.target.set(0, 0, 0);
      twinControls.update();
    }

    function toggleCurrentBlossom() {
      if (!currentSelectedNode) return;
      const parentId = currentSelectedNode.data.id;
      const isBlossomed = blossomedNodesMap[parentId];

      if (isBlossomed) {
        const children = blossomRegistry[parentId] || [];
        children.forEach(c => {
          const idx = kgPhysicsNodes.findIndex(n => n.data.id === c.id);
          if (idx !== -1) {
            kgScene.remove(kgPhysicsNodes[idx].group);
            kgPhysicsNodes.splice(idx, 1);
          }
          const eIdx = kgPhysicsEdges.findIndex(e => e.to === c.id);
          if (eIdx !== -1) {
            kgScene.remove(kgPhysicsEdges[eIdx].line);
            kgPhysicsEdges.splice(eIdx, 1);
          }
        });
        blossomedNodesMap[parentId] = false;
        document.getElementById('drawer-blossom-btn').innerText = "🌸 Blossom Sub-Components in 3D";
      } else {
        const children = blossomRegistry[parentId] || [];
        const p = currentSelectedNode;
        children.forEach((c, idx) => {
          const angle = (Math.PI * 2 / children.length) * idx;
          const burstDist = 3.5;
          const childData = {
            ...c,
            x: p.x + Math.cos(angle) * burstDist,
            y: p.y + (Math.random() - 0.5) * 2,
            z: p.z + Math.sin(angle) * burstDist
          };
          addNodeToGraph(childData);
          addEdgeToGraph({ from: parentId, to: c.id, rel: "BLOSSOM_CHILD" });
        });
        blossomedNodesMap[parentId] = true;
        document.getElementById('drawer-blossom-btn').innerText = "🌸 Collapse Sub-Components";
      }

      jiggleGraphPhysics();
      populateParentSelect();
    }

    function triggerActiveFailurePropagation() {
      const defectNode = (currentSelectedNode && currentSelectedNode.data.domain === "defect")
        ? currentSelectedNode
        : kgPhysicsNodes.find(n => n.data.domain === "defect");

      if (!defectNode) return alert("Please select a failure mode / defect node first!");

      inspectNode(defectNode);

      let shockHop = 0;
      const visited = new Set([defectNode.data.id]);
      const currentHop = [defectNode.data.id];

      function propagatePulse() {
        if (currentHop.length === 0 || shockHop > 3) return;

        const nextHop = [];
        currentHop.forEach(id => {
          const node = kgPhysicsNodes.find(n => n.data.id === id);
          if (node && node.mesh.material && node.mesh.material.emissive) {
            node.mesh.material.emissive.setHex(0xff0044);
            node.mesh.material.emissiveIntensity = 1.0;
            setTimeout(() => {
              node.mesh.material.emissive.set(new THREE.Color(node.data.color));
              node.mesh.material.emissiveIntensity = 0.5;
            }, 1200);
          }

          kgPhysicsEdges.forEach(e => {
            if ((e.from === id && !visited.has(e.to)) || (e.to === id && !visited.has(e.from))) {
              const otherId = e.from === id ? e.to : e.from;
              visited.add(otherId);
              nextHop.push(otherId);

              e.line.material.color.setHex(0xff3366);
              e.line.material.opacity = 1.0;
              setTimeout(() => {
                e.line.material.color.setHex(0x00f0ff);
                e.line.material.opacity = 0.45;
              }, 1200);
            }
          });
        });

        shockHop++;
        currentHop.length = 0;
        currentHop.push(...nextHop);
        setTimeout(propagatePulse, 400);
      }

      propagatePulse();
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
          return n.data.label.toLowerCase().includes(q) ||
                 (n.data.desc && n.data.desc.toLowerCase().includes(q)) ||
                 n.data.domain.toLowerCase().includes(q);
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

      document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-wrapper')) {
          dropdown.style.display = "none";
        }
      });
    }

    function renderDomainChips() {
      const container = document.getElementById('domain-chips-list');
      container.innerHTML = '';

      const allCount = kgPhysicsNodes.length;
      const allChip = document.createElement('div');
      allChip.className = "domain-chip active";
      allChip.innerHTML = `
        <div class="domain-left">
          <div class="domain-dot" style="background: #00f0ff;"></div>
          <span>All Domains</span>
        </div>
        <span class="domain-count">${allCount}</span>
      `;
      allChip.onclick = () => filterByDomain("all", allChip);
      container.appendChild(allChip);

      Object.entries(DOMAIN_METADATA).forEach(([domKey, meta]) => {
        const count = kgPhysicsNodes.filter(n => n.data.domain === domKey).length;
        const chip = document.createElement('div');
        chip.className = "domain-chip";
        chip.style.color = meta.color;
        chip.innerHTML = `
          <div class="domain-left">
            <div class="domain-dot" style="background: ${meta.color};"></div>
            <span>${meta.label}</span>
          </div>
          <span class="domain-count">${count}</span>
        `;
        chip.onclick = () => filterByDomain(domKey, chip);
        container.appendChild(chip);
      });
    }

    function filterByDomain(domain, chipEl) {
      activeFilterDomain = domain;
      document.querySelectorAll('.domain-chip').forEach(c => c.classList.remove('active'));
      chipEl.classList.add('active');

      kgPhysicsNodes.forEach(n => {
        const visible = (domain === 'all' || n.data.domain === domain);
        n.group.visible = visible;
      });
    }

    function onAlterationScrub(altVal) {
      const val = parseInt(altVal);
      document.getElementById('alt-tag-display').innerText = `ALT ${val} ${val === 13 ? '(LATEST)' : ''}`;

      const descMap = {
        1: "Alt 1: Initial standard layout of 1:12 Turnout 60 kg UIC on PSC Sleepers.",
        4: "Alt 4: Introduction of 5000 mm check rail arrangement with flared ends (T-6275).",
        5: "Alt 5: Spring Setting Device (SSD) integrated at Sleeper 13 for thick web switches.",
        8: "Alt 8: S&T Clamp Point Lock (S-3454) mounting interface standardized.",
        10: "Alt 10: Welded Joint 'W' supersedes machined Joint 'M' to eliminate heel fatigue cracks.",
        11: "Alt 11: Detail 'B' Bent Tie Bar introduced with 222 mm drop bend clearing drive rod.",
        12: "Alt 12: Note 25/26 Epoxy dowel retrofit standard mandated for concrete sleepers.",
        13: "Alt 13: Note 28 LIST-A 10% spare buffer enforced across 24 high-wear turnout components."
      };
      document.getElementById('alt-desc-display').innerText = descMap[val] || `Revision level Alt ${val} track asset modifications and tolerances.`;

      kgPhysicsNodes.forEach(n => {
        const nodeAlt = n.data.alt || 1;
        const isPastOrPresent = nodeAlt <= val;
        n.group.visible = isPastOrPresent && (activeFilterDomain === 'all' || n.data.domain === activeFilterDomain);
      });
    }

    function openIngestModal() {
      document.getElementById('ingest-modal').style.display = "flex";
    }

    function closeIngestModal() {
      document.getElementById('ingest-modal').style.display = "none";
    }

    function populateParentSelect() {
      const sel = document.getElementById('in-node-parent');
      sel.innerHTML = '';
      kgPhysicsNodes.forEach(n => {
        const opt = document.createElement('option');
        opt.value = n.data.id;
        opt.innerText = n.data.label;
        sel.appendChild(opt);
      });
    }

    function submitIngestNode() {
      const title = document.getElementById('in-node-title').value.trim();
      if (!title) return alert("Please enter an entity title.");

      const domain = document.getElementById('in-node-domain').value;
      const parentId = document.getElementById('in-node-parent').value;
      const relation = document.getElementById('in-node-relation').value;
      const desc = document.getElementById('in-node-desc').value.trim() || "Field engineering report / finding.";

      const parentNode = kgPhysicsNodes.find(n => n.data.id === parentId);
      const newId = "usr_" + Date.now();
      const offset = 3.5;

      const newNodeData = {
        id: newId,
        label: title,
        domain: domain,
        color: DOMAIN_METADATA[domain]?.color || "#00f0ff",
        x: (parentNode ? parentNode.x : 0) + (Math.random() - 0.5) * offset,
        y: (parentNode ? parentNode.y : 0) + (Math.random() - 0.5) * offset,
        z: (parentNode ? parentNode.z : 0) + (Math.random() - 0.5) * offset,
        alt: 13,
        desc: desc,
        specs: { "Source": "Live Field Ingestion", "Timestamp": new Date().toISOString().split('T')[0] }
      };

      const nodeObj = addNodeToGraph(newNodeData);
      addEdgeToGraph({ from: parentId, to: newId, rel: relation });

      closeIngestModal();
      document.getElementById('in-node-title').value = '';
      document.getElementById('in-node-desc').value = '';

      renderDomainChips();
      populateParentSelect();
      jiggleGraphPhysics();
      inspectNode(nodeObj);
    }

    function exportGraph(format) {
      const nodes = kgPhysicsNodes.map(n => n.data);
      const edges = kgPhysicsEdges.map(e => ({ from: e.from, to: e.to, rel: e.rel }));

      if (format === 'cypher') {
        let cypher = "// Exported Cypher from RDSO Railway Track Knowledge Graph Studio\n";
        nodes.forEach(n => {
          cypher += `MERGE (n:${n.domain.toUpperCase()} {id: "${n.id}", label: "${n.label}"});\n`;
        });
        edges.forEach(e => {
          cypher += `MATCH (a {id: "${e.from}"}), (b {id: "${e.to}"}) MERGE (a)-[:${e.rel}]->(b);\n`;
        });
        const blob = new Blob([cypher], { type: "text/plain" });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = "rdso_track_knowledge_graph.cypher";
        a.click();
      }
    }

    function togglePhysicsPopover(forceOpen) {
      const p = document.getElementById('physics-popover');
      if (forceOpen === undefined) p.style.display = p.style.display === "block" ? "none" : "block";
      else p.style.display = forceOpen ? "block" : "none";
    }

    function updatePhysicsParam(param, val) {
      const v = parseFloat(val);
      if (param === 'repulsion') {
        k_repulsion = v;
        document.getElementById('val-repulsion').innerText = v;
      } else if (param === 'spring') {
        k_spring = v;
        document.getElementById('val-spring').innerText = v;
      } else if (param === 'length') {
        l0_spring = v;
        document.getElementById('val-length').innerText = v;
      } else if (param === 'damping') {
        damping = v;
        document.getElementById('val-damping').innerText = v;
      }
    }

    function updateTelemetryCounters() {
      document.getElementById('telem-nodes').innerText = kgPhysicsNodes.length;
      document.getElementById('telem-edges').innerText = kgPhysicsEdges.length;
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

final_html = html_template.replace("__EXTRACTED_KNOWLEDGE_JSON__", extracted_json_str)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(final_html)

print(f"[+] Successfully compiled index.html with embedded knowledge dossiers! Size: {len(final_html)} bytes")
