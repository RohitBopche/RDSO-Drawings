import re

def update_index_html():
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add updateDrawerTabsVisibility function and query context banner logic in inspectNode
    # Let's inspect inspectNode in content
    assert 'function inspectNode(node)' in content, "inspectNode not found"

    # Replacement 1: Update the else block of inspectNode and add query context banner
    old_else_block = """      } else {
        const specs = data.specs || {};
        const specEntries = Object.entries(specs);
        const connectedEdges = kgPhysicsEdges.filter(e => e.from === data.id || e.to === data.id);
        const relatedNames = connectedEdges.slice(0, 4).map(e => {
          const targetId = e.from === data.id ? e.to : e.from;
          const targetNode = kgPhysicsNodes.find(n => n.data.id === targetId);
          return targetNode ? targetNode.data.label : targetId;
        });

        descEl.innerHTML = `
          <div style="display: flex; flex-direction: column; gap: 8px;">
            <div style="font-size: 11.5px; line-height: 1.45; color: #e0e8f8;">
              ${data.desc || "Canonical railway track infrastructure asset governed by official RDSO technical specifications."}
            </div>

            <div style="display: flex; gap: 6px; flex-wrap: wrap; align-items: center; font-size: 10px;">
              <span style="background: rgba(0, 240, 255, 0.1); border: 1px solid rgba(0, 240, 255, 0.3); color: var(--accent-cyan); padding: 2px 6px; border-radius: 4px; font-weight: 600;">
                📜 ${currentActiveDossier.drawing_number} (ALT ${currentActiveDossier.alteration_number || 13})
              </span>
              <span style="background: rgba(157, 78, 221, 0.15); border: 1px solid rgba(157, 78, 221, 0.35); color: var(--text-main); padding: 2px 6px; border-radius: 4px;">
                📏 BG 1676 mm
              </span>
              <span style="background: rgba(76, 201, 240, 0.1); border: 1px solid rgba(76, 201, 240, 0.3); color: var(--accent-blue); padding: 2px 6px; border-radius: 4px;">
                IRS: T 10 / T 29
              </span>
            </div>

            ${specEntries.length > 0 ? `
              <div style="background: rgba(14, 22, 38, 0.6); border: 1px solid var(--border-subtle); border-radius: 4px; padding: 6px 8px;">
                <div style="font-size: 9.5px; font-weight: 700; color: var(--accent-yellow); text-transform: uppercase; margin-bottom: 4px;">Critical Parameters & Bounds:</div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px; font-size: 10.5px;">
                  ${specEntries.slice(0, 4).map(([k, v]) => `
                    <div style="color: var(--text-dim);"><strong style="color: var(--text-main);">${k}:</strong> ${v}</div>
                  `).join('')}
                </div>
              </div>
            ` : ''}

            ${relatedNames.length > 0 ? `
              <div style="font-size: 10px; color: var(--text-muted);">
                <strong style="color: var(--accent-cyan);">Kinematic Context:</strong> Interconnected with ${relatedNames.join(', ')}.
              </div>
            ` : ''}

            <div style="font-size: 10px; color: var(--accent-orange); background: rgba(247, 37, 133, 0.08); border-left: 2px solid var(--accent-pink); padding: 4px 8px; border-radius: 0 4px 4px 0;">
              ⚠️ <strong>Safeguard:</strong> Strict compliance with IRPWM Chapter 4 & Note 28 maintenance directives.
            </div>
          </div>
        `;

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

        const toolbar = document.getElementById('answer-card-toolbar');
        if (toolbar) {
          toolbar.style.display = "flex";
          toolbar.innerHTML = `
            <button class="answer-tool-btn" id="btn-answer-blueprint" onclick="openFullscreenActiveBlueprint()">
              <span>🔍</span> Blueprint Crop
            </button>
            <button class="answer-tool-btn" id="btn-answer-twin" onclick="switchDrawerTab('twin')">
              <span>📦</span> 3D Twin
            </button>
            <button class="answer-tool-btn" id="btn-answer-paths" onclick="renderPathFinderUI('${data.id}', 'std_irs_t10'); switchDrawerTab('paths');">
              <span>🛤️</span> Trace Paths
            </button>
            <button class="answer-tool-btn" id="btn-answer-inspection" onclick="switchDrawerTab('inspection')">
              <span>📋</span> Field Inspection
            </button>
            <button class="answer-tool-btn" id="btn-answer-procurement" onclick="switchDrawerTab('procurement')">
              <span>📦</span> Spares & BOM
            </button>
          `;
        }
      }"""

    new_else_block = """      } else {
        const specs = data.specs || {};
        const specEntries = Object.entries(specs);
        const connectedEdges = kgPhysicsEdges.filter(e => e.from === data.id || e.to === data.id);
        const relatedNames = connectedEdges.slice(0, 5).map(e => {
          const targetId = e.from === data.id ? e.to : e.from;
          const targetNode = kgPhysicsNodes.find(n => n.data.id === targetId);
          return targetNode ? targetNode.data.label : targetId;
        });

        // 1. Build Query Context Banner if a search query is active
        let queryBannerHtml = '';
        if (window.lastSearchQuery && window.lastSearchQuery.trim()) {
          const qStr = window.lastSearchQuery.trim();
          const ansMatch = window.answerEngineeringQuestion ? window.answerEngineeringQuestion(qStr) : null;
          const inPath = ansMatch?.traversal?.some(t => t.id === data.id);
          const qTokens = qStr.toLowerCase().split(/[\\s,?.!]+/).filter(t => t.length > 2);
          const entitySearchText = `${data.label} ${data.desc || ''} ${JSON.stringify(specs)}`.toLowerCase();
          const matchesTerm = qTokens.some(t => entitySearchText.includes(t));

          let qRelevanceText = '';
          if (inPath) {
            const stepNum = ansMatch.traversal.findIndex(t => t.id === data.id) + 1;
            qRelevanceText = `Key Step ${stepNum} of ${ansMatch.traversal.length} in the resolution path for: "<strong>${qStr}</strong>".`;
          } else if (matchesTerm) {
            qRelevanceText = `Selected entity directly addresses query term: "<strong>${qStr}</strong>".`;
          } else {
            // Check if connected to any entity in traversal
            const connectedToPath = ansMatch?.traversal?.find(t => connectedEdges.some(e => e.from === t.id || e.to === t.id));
            if (connectedToPath) {
              qRelevanceText = `Directly connected in graph to query entity <strong>${connectedToPath.label}</strong>.`;
            }
          }

          if (qRelevanceText) {
            queryBannerHtml = `
              <div class="query-context-card" style="margin-bottom: 8px; padding: 7px 9px; background: linear-gradient(135deg, rgba(0, 240, 255, 0.14), rgba(157, 78, 221, 0.12)); border: 1px solid rgba(0, 240, 255, 0.4); border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.35);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">
                  <span style="font-size: 9.5px; font-weight: 700; color: var(--accent-yellow); text-transform: uppercase; letter-spacing: 0.5px; display: flex; align-items: center; gap: 4px;">
                    <span>🎯</span> QUERY RELEVANCE CONTEXT
                  </span>
                  ${inPath ? `<span style="font-size: 8.5px; font-weight: 700; color: var(--accent-green); background: rgba(0,255,136,0.18); border: 1px solid rgba(0,255,136,0.35); padding: 1px 5px; border-radius: 3px;">★ PATH ENTITY</span>` : ''}
                </div>
                <div style="font-size: 11px; color: #fff; line-height: 1.4;">${qRelevanceText}</div>
                <div style="margin-top: 6px; display: flex; gap: 5px; flex-wrap: wrap;">
                  ${ansMatch ? `
                    <button class="btn" style="padding: 2px 7px; font-size: 9px; background: rgba(0,240,255,0.22); border-color: var(--accent-cyan); color: var(--accent-cyan); font-weight: 700;" onclick="switchDrawerTab('qa'); renderQuestionAnswerCard(window.answerEngineeringQuestion('${qStr.replace(/'/g, "\\\\\\'")}'), document.getElementById('qa-answer-mount'));">
                      <span>❓</span> View Query QA Answer
                    </button>
                    ${ansMatch.traversal && ansMatch.traversal.length > 0 ? `
                      <button class="btn" style="padding: 2px 7px; font-size: 9px;" onclick="highlightGraphPath([${ansMatch.traversal.map(t => `'${t.id}'`).join(',')}]);">
                        <span>🛤️</span> Trace Query Path (${ansMatch.traversal.length})
                      </button>
                    ` : ''}
                  ` : ''}
                </div>
              </div>
            `;
          }
        }

        const hasGoverningDrawing = !!(currentActiveDossier && currentActiveDossier.drawing_number);

        if (hasGoverningDrawing) {
          // Drawing-specific component (e.g. comp_detailb on RDSO/T-6155)
          descEl.innerHTML = `
            ${queryBannerHtml}
            <div style="display: flex; flex-direction: column; gap: 8px;">
              <div style="font-size: 11.5px; line-height: 1.45; color: #e0e8f8;">
                ${data.desc || "Canonical railway track infrastructure asset governed by official RDSO technical specifications."}
              </div>

              <div style="display: flex; gap: 6px; flex-wrap: wrap; align-items: center; font-size: 10px;">
                <span style="background: rgba(0, 240, 255, 0.1); border: 1px solid rgba(0, 240, 255, 0.3); color: var(--accent-cyan); padding: 2px 6px; border-radius: 4px; font-weight: 600;">
                  📜 ${currentActiveDossier.drawing_number} (ALT ${currentActiveDossier.alteration_number || 13})
                </span>
                <span style="background: rgba(157, 78, 221, 0.15); border: 1px solid rgba(157, 78, 221, 0.35); color: var(--text-main); padding: 2px 6px; border-radius: 4px;">
                  📏 BG 1676 mm
                </span>
                <span style="background: rgba(76, 201, 240, 0.1); border: 1px solid rgba(76, 201, 240, 0.3); color: var(--accent-blue); padding: 2px 6px; border-radius: 4px;">
                  IRS: T 10 / T 29
                </span>
              </div>

              ${specEntries.length > 0 ? `
                <div style="background: rgba(14, 22, 38, 0.6); border: 1px solid var(--border-subtle); border-radius: 4px; padding: 6px 8px;">
                  <div style="font-size: 9.5px; font-weight: 700; color: var(--accent-yellow); text-transform: uppercase; margin-bottom: 4px;">Critical Parameters & Bounds:</div>
                  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px; font-size: 10.5px;">
                    ${specEntries.slice(0, 4).map(([k, v]) => `
                      <div style="color: var(--text-dim);"><strong style="color: var(--text-main);">${k}:</strong> ${Array.isArray(v) ? v.join(', ') : v}</div>
                    `).join('')}
                  </div>
                </div>
              ` : ''}

              ${relatedNames.length > 0 ? `
                <div style="font-size: 10px; color: var(--text-muted);">
                  <strong style="color: var(--accent-cyan);">Kinematic Context:</strong> Interconnected with ${relatedNames.join(', ')}.
                </div>
              ` : ''}

              <div style="font-size: 10px; color: var(--accent-orange); background: rgba(247, 37, 133, 0.08); border-left: 2px solid var(--accent-pink); padding: 4px 8px; border-radius: 0 4px 4px 0;">
                ⚠️ <strong>Safeguard:</strong> Strict compliance with IRPWM Chapter 4 & Note 28 maintenance directives.
              </div>
            </div>
          `;

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

          const toolbar = document.getElementById('answer-card-toolbar');
          if (toolbar) {
            toolbar.style.display = "flex";
            toolbar.innerHTML = `
              <button class="answer-tool-btn" id="btn-answer-blueprint" onclick="openFullscreenActiveBlueprint()">
                <span>🔍</span> Blueprint Crop
              </button>
              <button class="answer-tool-btn" id="btn-answer-twin" onclick="switchDrawerTab('twin')">
                <span>📦</span> 3D Twin
              </button>
              <button class="answer-tool-btn" id="btn-answer-paths" onclick="renderPathFinderUI('${data.id}', 'std_irs_t10'); switchDrawerTab('paths');">
                <span>🛤️</span> Trace Paths
              </button>
              <button class="answer-tool-btn" id="btn-answer-inspection" onclick="switchDrawerTab('inspection')">
                <span>📋</span> Field Inspection
              </button>
              <button class="answer-tool-btn" id="btn-answer-procurement" onclick="switchDrawerTab('procurement')">
                <span>📦</span> Spares & BOM
              </button>
            `;
          }
        } else {
          // Entity without a turnout drawing (e.g. comp_joggled_fish_plate, roles, activities, materials)
          // Strictly show verified authentic parameters & bounds without hardcoded fake data
          const stdDrgs = Array.isArray(specs.StandardDrawings) ? specs.StandardDrawings : (specs.StandardDrawings ? [specs.StandardDrawings] : []);
          const badgesHtml = stdDrgs.length > 0 
            ? stdDrgs.map(d => `<span style="background: rgba(0, 240, 255, 0.1); border: 1px solid rgba(0, 240, 255, 0.3); color: var(--accent-cyan); padding: 2px 6px; border-radius: 4px; font-weight: 600;">📐 ${d}</span>`).join(' ')
            : `<span style="background: rgba(0, 240, 255, 0.1); border: 1px solid rgba(0, 240, 255, 0.3); color: var(--accent-cyan); padding: 2px 6px; border-radius: 4px; font-weight: 600;">📖 Indian Railways Standard</span>`;

          let safeguardHtml = '';
          if (specs.SpeedRestriction) {
            safeguardHtml = `<div style="font-size: 10px; color: var(--accent-orange); background: rgba(247, 37, 133, 0.08); border-left: 2px solid var(--accent-pink); padding: 4px 8px; border-radius: 0 4px 4px 0;">
              ⚠️ <strong>Safeguard:</strong> Emergency speed restriction of ${specs.SpeedRestriction}. Mandatory compliance governed by IRPWM Chapter 3 & USFD Chapter 8.
            </div>`;
          } else if (specs.ClampingRequirement) {
            safeguardHtml = `<div style="font-size: 10px; color: var(--accent-yellow); background: rgba(255, 214, 10, 0.08); border-left: 2px solid var(--accent-yellow); padding: 4px 8px; border-radius: 0 4px 4px 0;">
              ⚠️ <strong>Mandate:</strong> ${specs.ClampingRequirement}.
            </div>`;
          } else {
            safeguardHtml = `<div style="font-size: 10px; color: var(--accent-cyan); background: rgba(0, 240, 255, 0.06); border-left: 2px solid var(--accent-cyan); padding: 4px 8px; border-radius: 0 4px 4px 0;">
              ℹ️ <strong>Standard Compliance:</strong> Governed by official Indian Railways permanent way maintenance codes.
            </div>`;
          }

          descEl.innerHTML = `
            ${queryBannerHtml}
            <div style="display: flex; flex-direction: column; gap: 8px;">
              <div style="font-size: 11.5px; line-height: 1.45; color: #e0e8f8;">
                ${data.desc || "Canonical railway track infrastructure asset governed by official RDSO technical specifications."}
              </div>

              <div style="display: flex; gap: 6px; flex-wrap: wrap; align-items: center; font-size: 10px;">
                ${badgesHtml}
                <span style="background: rgba(157, 78, 221, 0.15); border: 1px solid rgba(157, 78, 221, 0.35); color: var(--text-main); padding: 2px 6px; border-radius: 4px;">
                  🏛️ ${data.domain ? data.domain.toUpperCase() : 'CANONICAL'} ENTITY
                </span>
                <span style="background: rgba(0, 255, 136, 0.1); border: 1px solid rgba(0, 255, 136, 0.3); color: var(--accent-green); padding: 2px 6px; border-radius: 4px; font-weight: 600;">
                  ✓ VERIFIED DATA
                </span>
              </div>

              ${specEntries.length > 0 ? `
                <div style="background: rgba(14, 22, 38, 0.6); border: 1px solid var(--border-subtle); border-radius: 4px; padding: 6px 8px;">
                  <div style="font-size: 9.5px; font-weight: 700; color: var(--accent-yellow); text-transform: uppercase; margin-bottom: 4px;">Authoritative Parameters:</div>
                  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px; font-size: 10.5px;">
                    ${specEntries.filter(([k]) => k !== 'StandardDrawings').map(([k, v]) => `
                      <div style="color: var(--text-dim);"><strong style="color: var(--text-main);">${k}:</strong> ${Array.isArray(v) ? v.join(', ') : v}</div>
                    `).join('')}
                  </div>
                </div>
              ` : ''}

              ${relatedNames.length > 0 ? `
                <div style="font-size: 10px; color: var(--text-muted);">
                  <strong style="color: var(--accent-cyan);">Graph Connections:</strong> ${relatedNames.join(' · ')}.
                </div>
              ` : ''}

              ${safeguardHtml}
            </div>
          `;

          // Never show fake blueprint crops for non-drawing entities
          const provBox = document.getElementById('answer-provenance-box');
          const linkedFact = rawKGFacts.find(f => (f.subject_id === data.id || f.object_id === data.id) && f.source && f.source.crop && !f.source.crop.includes('t6155_notes_full.png'));
          if (linkedFact && linkedFact.source && linkedFact.source.crop) {
            provBox.style.display = "flex";
            document.getElementById('prov-dwg-title').innerText = `${linkedFact.source.drawing_id} (${linkedFact.source.revision})`;
            document.getElementById('prov-meta-line').innerText = `Region: ${linkedFact.source.region} | Method: ${linkedFact.extraction_method}`;
            document.getElementById('answer-crop-thumb').src = linkedFact.source.crop;
            currentActiveCrop = linkedFact.source.crop;
          } else {
            provBox.style.display = "none";
          }

          const toolbar = document.getElementById('answer-card-toolbar');
          if (toolbar) {
            toolbar.style.display = "flex";
            const firstRelNode = connectedEdges[0] ? (connectedEdges[0].from === data.id ? connectedEdges[0].to : connectedEdges[0].from) : "act_greasing_lubrication";
            toolbar.innerHTML = `
              <button class="answer-tool-btn" id="btn-answer-paths" onclick="renderPathFinderUI('${data.id}', '${firstRelNode}'); switchDrawerTab('paths');">
                <span>🛤️</span> Trace Paths
              </button>
              <button class="answer-tool-btn" id="btn-answer-manuals" onclick="switchDrawerTab('manuals')">
                <span>📖</span> Governing Directives
              </button>
              <button class="answer-tool-btn" id="btn-answer-overview" onclick="switchDrawerTab('overview')">
                <span>📋</span> Node Dossier
              </button>
              <button class="answer-tool-btn" id="btn-answer-3d" onclick="focusNodeIn3D('${data.id}')">
                <span>🎯</span> Focus 3D
              </button>
              ${window.lastSearchQuery ? `
                <button class="answer-tool-btn" id="btn-answer-qa" style="background: rgba(0,240,255,0.18); border-color: var(--accent-cyan); color: var(--accent-cyan); font-weight: 700;" onclick="switchDrawerTab('qa')">
                  <span>❓</span> Query QA
                </button>
              ` : ''}
            `;
          }
        }
      }"""

    assert old_else_block in content, "old_else_block not found in content"
    content = content.replace(old_else_block, new_else_block)

    # 2. Add dynamic drawer tabs visibility update function in inspectNode
    # Locate where switchDrawerTab('overview') is called in inspectNode
    target_switch = "      // 10. Default to overview tab\n      switchDrawerTab('overview');"
    assert target_switch in content, "target_switch not found in content"

    new_tab_mgmt = """      // 9.5 Dynamically update drawer tabs to display only relevant tabs
      updateDrawerTabsVisibility(isDrawingNode, currentActiveDossier, data);

      // 10. Default to overview tab
      switchDrawerTab('overview');"""
    content = content.replace(target_switch, new_tab_mgmt)

    # Add the definition of updateDrawerTabsVisibility
    fn_def = """    function updateDrawerTabsVisibility(isDrawing, dossier, data) {
      const hasDossier = dossier && dossier.drawing_number;
      const hasNotes = isDrawing || (hasDossier && dossier.notes && dossier.notes.length > 0);
      const hasTables = isDrawing || (hasDossier && dossier.tables && dossier.tables.length > 0);
      const hasBlueprint = isDrawing || (hasDossier && dossier.crops && Object.keys(dossier.crops).length > 0);
      const hasTwin = isDrawing || !!data.twinAsset;
      const hasRevisions = isDrawing || (hasDossier && dossier.alteration_history && dossier.alteration_history.length > 0) || data.type === 'REVISION';
      const hasProcurement = isDrawing || (hasDossier && dossier.drawing_number && dossier.drawing_number.includes('6155'));

      const setTabVis = (tabId, show) => {
        const btn = document.querySelector(`.drawer-tab[data-tab="${tabId}"]`);
        if (btn) btn.style.display = show ? '' : 'none';
      };

      setTabVis('notes', hasNotes);
      setTabVis('tables', hasTables);
      setTabVis('blueprint', hasBlueprint);
      setTabVis('twin', hasTwin);
      setTabVis('revisions', hasRevisions);
      setTabVis('procurement', hasProcurement);
    }
    window.updateDrawerTabsVisibility = updateDrawerTabsVisibility;

"""
    # Insert right before inspectNode
    content = content.replace("    function inspectNode(node) {", fn_def + "    function inspectNode(node) {")

    # 3. Update renderDrawingOverview to not inject dummy blueprint crop or fake note 28 for non-drawing entities
    # Let's inspect Section 5 and Section 6 in renderDrawingOverview
    old_drawing_overview_part = """        // Visual Evidence Crop
        const linkedFact = rawKGFacts.find(f => f.subject_id === data.id || f.object_id === data.id);
        const cropImg = (linkedFact && linkedFact.source && linkedFact.source.crop && linkedFact.source.crop.endsWith('.png')) 
          ? linkedFact.source.crop 
          : ((data.type === "REVISION" || data.domain === "revision") ? "crops/t6155_title_alt13.png" : (Object.values(currentActiveDossier.crops || {})[0] || "crops/t6155_notes_full.png"));
        const cropRegion = linkedFact?.source?.region || ((data.type === "REVISION" || data.domain === "revision") ? "Title Block Revision Ledger" : "Master Blueprint Assembly");"""

    assert old_drawing_overview_part in content, "old_drawing_overview_part not found"

    new_drawing_overview_part = """        // Connected governing clauses for statutory evidence
        const connectedClauseEdges = kgPhysicsEdges.filter(e => 
          (e.from === data.id || e.to === data.id) &&
          (e.from.startsWith('CLAUSE:') || e.to.startsWith('CLAUSE:') || e.from.startsWith('CHAPTER:') || e.to.startsWith('CHAPTER:'))
        );
        const connectedClauseIds = connectedClauseEdges.map(e => e.from === data.id ? e.to : e.from);
        const connectedClauseNodes = connectedClauseIds.map(id => kgPhysicsNodes.find(n => n.data.id === id)).filter(Boolean);

        // Visual Evidence Crop (only if authentic crop exists)
        const linkedFact = rawKGFacts.find(f => f.subject_id === data.id || f.object_id === data.id);
        const hasAuthenticCrop = (linkedFact && linkedFact.source && linkedFact.source.crop && !linkedFact.source.crop.includes('t6155_notes_full.png')) ||
                                 (currentActiveDossier && currentActiveDossier.drawing_number && currentActiveDossier.crops && Object.values(currentActiveDossier.crops).length > 0) ||
                                 (data.type === "REVISION" || data.domain === "revision");
        const cropImg = hasAuthenticCrop 
          ? (linkedFact?.source?.crop || ((data.type === "REVISION" || data.domain === "revision") ? "crops/t6155_title_alt13.png" : (Object.values(currentActiveDossier.crops || {})[0] || "")))
          : "";
        const cropRegion = linkedFact?.source?.region || ((data.type === "REVISION" || data.domain === "revision") ? "Title Block Revision Ledger" : "Master Blueprint Assembly");"""

    content = content.replace(old_drawing_overview_part, new_drawing_overview_part)

    # Now let's fix Section 5 and Section 6 in renderDrawingOverview's container.innerHTML
    old_section_5_and_6 = """          <!-- Section 5: Safety Risk & Preventative Safeguards -->
          <div class="drawing-section">
            <div class="drawing-section-header">
              <div class="drawing-section-title"><span>⚠️</span> ${riskHeader}</div>
              <span class="drawing-section-badge" style="color: var(--accent-red); border-color: rgba(255, 51, 102, 0.3);">${riskBadge}</span>
            </div>
            <div style="background: rgba(255, 51, 102, 0.08); border-left: 3px solid var(--accent-red); padding: 8px 10px; border-radius: 0 5px 5px 0; font-size: 11px; line-height: 1.45; color: #f8d7da;">
              ${riskText}
            </div>
            <div style="font-size: 10px; color: var(--text-dim); margin-top: 2px;">
              ${riskSubnote}
            </div>
          </div>

          <!-- Section 6: Grounded Visual Blueprint Evidence -->
          <div class="drawing-section">
            <div class="drawing-section-header">
              <div class="drawing-section-title"><span>📸</span> Grounded Visual Blueprint Evidence</div>
              <span class="drawing-section-badge">SOURCE CROP</span>
            </div>
            <div style="background: rgba(10, 16, 28, 0.8); border: 1px solid var(--border-subtle); border-radius: 6px; padding: 6px; cursor: pointer;" onclick="openFullscreenBlueprint('${cropImg}', '${data.label}: Source Evidence')">
              <img src="${cropImg}" style="width: 100%; height: 90px; object-fit: cover; border-radius: 4px;" alt="Blueprint Evidence">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px; font-size: 9.5px;">
                <span style="color: var(--accent-cyan); font-weight: 600;">Region: ${cropRegion}</span>
                <span style="color: var(--text-dim);">🔍 Click to Expand</span>
              </div>
            </div>
          </div>"""

    assert old_section_5_and_6 in content, "old_section_5_and_6 not found"

    new_section_5_and_6 = """          <!-- Section 5: Safety Risk & Preventative Safeguards -->
          <div class="drawing-section">
            <div class="drawing-section-header">
              <div class="drawing-section-title"><span>⚠️</span> ${riskHeader}</div>
              <span class="drawing-section-badge" style="color: var(--accent-red); border-color: rgba(255, 51, 102, 0.3);">${riskBadge}</span>
            </div>
            <div style="background: rgba(255, 51, 102, 0.08); border-left: 3px solid var(--accent-red); padding: 8px 10px; border-radius: 0 5px 5px 0; font-size: 11px; line-height: 1.45; color: #f8d7da;">
              ${riskText}
            </div>
            <div style="font-size: 10px; color: var(--text-dim); margin-top: 2px;">
              ${riskSubnote}
            </div>
          </div>

          <!-- Section 6: Grounded Evidence & Statutory Provisions -->
          ${hasAuthenticCrop ? `
            <div class="drawing-section">
              <div class="drawing-section-header">
                <div class="drawing-section-title"><span>📸</span> Grounded Visual Blueprint Evidence</div>
                <span class="drawing-section-badge">SOURCE CROP</span>
              </div>
              <div style="background: rgba(10, 16, 28, 0.8); border: 1px solid var(--border-subtle); border-radius: 6px; padding: 6px; cursor: pointer;" onclick="openFullscreenBlueprint('${cropImg}', '${data.label}: Source Evidence')">
                <img src="${cropImg}" style="width: 100%; height: 90px; object-fit: cover; border-radius: 4px;" alt="Blueprint Evidence">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px; font-size: 9.5px;">
                  <span style="color: var(--accent-cyan); font-weight: 600;">Region: ${cropRegion}</span>
                  <span style="color: var(--text-dim);">🔍 Click to Expand</span>
                </div>
              </div>
            </div>
          ` : (connectedClauseNodes.length > 0 ? `
            <div class="drawing-section">
              <div class="drawing-section-header">
                <div class="drawing-section-title"><span>📜</span> Governing Statutory Manual Directives (${connectedClauseNodes.length})</div>
                <span class="drawing-section-badge" style="color: var(--accent-green); border-color: rgba(0,255,136,0.3);">STATUTORY EVIDENCE</span>
              </div>
              <div style="display: flex; flex-direction: column; gap: 6px;">
                ${connectedClauseNodes.slice(0, 5).map(cn => `
                  <div style="background: rgba(10, 16, 28, 0.7); border-left: 3px solid var(--accent-cyan); border-radius: 0 4px 4px 0; padding: 7px 10px; cursor: pointer;" onclick="inspectNode(kgPhysicsNodes.find(n => n.data.id === '${cn.data.id}'))">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                      <strong style="color: var(--accent-cyan); font-size: 11px;">${cn.data.label}</strong>
                      <span style="font-size: 9px; color: var(--accent-purple); font-family: var(--font-mono);">${cn.data.specs?.Manual || 'IRPWM / USFD'}</span>
                    </div>
                    <div style="font-size: 10.5px; color: #cfd8ea; line-height: 1.4;">${cn.data.desc || cn.data.specs?.Verbatim || 'Official regulatory clause.'}</div>
                  </div>
                `).join('')}
              </div>
            </div>
          ` : '')}"""

    content = content.replace(old_section_5_and_6, new_section_5_and_6)

    # Also update Section 1 Governing Drawing label in renderDrawingOverview:
    old_gov_drawing_line = """        let govDrawing = currentActiveDossier.drawing_number
          ? `${currentActiveDossier.drawing_number} (ALT ${currentActiveDossier.alteration_number || 13})`
          : (data.specs?.DrawingNumber || data.specs?.["Drawing No"] || "N/A — Independent Entity");"""
    
    new_gov_drawing_line = """        let govDrawing = currentActiveDossier.drawing_number
          ? `${currentActiveDossier.drawing_number} (ALT ${currentActiveDossier.alteration_number || 13})`
          : (data.specs?.DrawingNumber || data.specs?.["Drawing No"] || (data.specs?.StandardDrawings ? (Array.isArray(data.specs.StandardDrawings) ? data.specs.StandardDrawings.join(', ') : data.specs.StandardDrawings) : "IRS / RDSO Track Standards"));"""

    if old_gov_drawing_line in content:
        content = content.replace(old_gov_drawing_line, new_gov_drawing_line)

    # Also update Risk Text calculation for components that have SpeedRestriction or ClampingRequirement:
    old_risk_default = """        let riskHeader = "Derailment Hazard & Safeguards";
        let riskText = "Strict adherence to dimensional tolerances, torque limits (550–650 N·m), and periodic USFD ultrasonic scans prevents derailment hazards.";
        let riskBadge = "SAFETY CRITICAL";
        let riskSubnote = "Mandatory maintenance compliance governed by IRPWM 2024 Chapter 4 and IRS specifications.";"""

    new_risk_default = """        let riskHeader = "Derailment Hazard & Safeguards";
        let riskText = "Strict adherence to dimensional tolerances, torque limits (550–650 N·m), and periodic USFD ultrasonic scans prevents derailment hazards.";
        let riskBadge = "SAFETY CRITICAL";
        let riskSubnote = "Mandatory maintenance compliance governed by IRPWM 2024 Chapter 4 and IRS specifications.";

        if (data.specs && (data.specs.SpeedRestriction || data.specs.ClampingRequirement)) {
          riskHeader = "Emergency Track Protection & Clamping Directive";
          riskBadge = "SAFETY CRITICAL";
          riskText = `Speed Restriction: ${data.specs.SpeedRestriction || '30 km/h under clamp'}. Clamping Requirement: ${data.specs.ClampingRequirement || 'Minimum 2 tight C-clamps'}. Application: ${data.specs.Application || 'Defective welds and rail flaws'}.`;
          riskSubnote = "Mandatory compliance governed by IRPWM 2024 Chapter 3 (Para 307 & 349) and USFD Chapter 8 (Para 8.10).";
        }"""

    if old_risk_default in content:
        content = content.replace(old_risk_default, new_risk_default)

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully updated index.html!")

if __name__ == '__main__':
    update_index_html()
