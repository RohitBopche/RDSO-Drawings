import re

def fix_search_and_add_destressing_qa():
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add qa_destressing_temperature to CANONICAL_QA_DATABASE
    assert 'const CANONICAL_QA_DATABASE = [' in content, "CANONICAL_QA_DATABASE not found"
    
    destressing_qa_entry = """      {
        id: "qa_destressing_temperature",
        intent: "SPECIFICATION_GOVERNANCE",
        keywords: [
          "destressing temperature", "destressing temp", "de-stressing temperature", "destressing",
          "td temperature", "range of destressing temperature", "destressing of lwr", "thermal forces in lwr",
          "destressing without rail tensors", "destressing with rail tensors", "mean rail temperature tm",
          "lwr destressing", "stress-free temperature", "sft"
        ],
        question: "What is the destressing temperature range (td) for LWR/CWR track?",
        statement: `Destressing temperature (**td**) and thermal forces in Continuous / Long Welded Rails (LWR/CWR) are mandated by **IRPWM 2024 Chapter 3 (Paras 333, 335, 338, 339, 340, 341 & 347)**:

1. **Standard Destressing Temperature Window (td) per Zone (Para 335)**:
   The range of destressing temperature (**td** or **t0**) shall be within statutory limits based on Mean Annual Rail Temperature (**tm**):
   • **Temperature Zones I, II, and III (All rail sections 52 kg / 60 kg)**:
     **tm to (tm + 5°C)**
   • **Temperature Zone IV (52 kg/m & heavier sections)**:
     **(tm + 5°C) to (tm + 10°C)**

2. **Permitted Reduced Destressing Range (Para 335)**:
   Laying of LWR on wider base sleepers with 60 kg rail and sleeper density of 1660 nos./km permits a reduced de-stressing temperature range for superior track buckling resistance.

3. **Supervision & Traffic Block Protocol (Para 339)**:
   • The work of de-stressing must strictly be executed during a **traffic block** under the personal supervision of **JE / SSE / P.Way**.
   • Mobile temperature thermometers must be positioned along the rail during the entire operation.

4. **Destressing With vs. Without Rail Tensors (Paras 340 & 341)**:
   • **Without Rail Tensors (Natural td)**: Allowed only when ambient rail temperature falls naturally within the specified **td** range during the work window.
   • **With Rail Tensors (Hydraulic Tensor)**: Compulsory when rail temperature is below **td**. The tensor pulls the rail to the calculated extension: **L = α · L0 · (td - tp)**, where α = 1.152 × 10⁻⁵ / °C.

5. **Stress-Free Temperature (SFT) & Maintenance Limits (Para 347)**:
   In ideal conditions, stress-free temperature equals destressing temperature. Abnormal SEJ gaps (exceeding Annexure 3/9) or rail creep > 20 mm mandate immediate investigation by ADEN and re-destressing.`,
        params: [
          { name: "Destressing Temp (Zones I-III)", nominal: "tm to (tm + 5°C)", limit: "tm to tm+5°C", unit: "°C", risk: "Under-destressing causes high tensile winter fractures; over-destressing induces severe summer buckling", remedy: "Perform tensor-controlled destressing within specified td range" },
          { name: "Destressing Temp (Zone IV)", nominal: "tm + 5°C to tm + 10°C", limit: "tm+5 to tm+10°C", unit: "°C", risk: "Severe track buckling under high temperature range in Zone IV", remedy: "Maintain 1660 sleeper density and consolidate ballast shoulder" },
          { name: "Supervisory Level", nominal: "JE / SSE / P.Way", limit: "Personal Supervision", unit: "Mandatory", risk: "Unauthorized or uncalibrated destressing causes major track geometry derailments", remedy: "Conduct work under traffic block supervised by JE/SSE/P.Way" },
          { name: "Thermal Expansion Coeff (α)", nominal: "1.152 × 10⁻⁵ / °C", limit: "Standard Rail Steel", unit: "per °C", risk: "Incorrect extension calculation causes residual compressive or tensile stresses", remedy: "Calculate tensor stroke strictly per L = α · L0 · (td - tp)" }
        ],
        traversal: [
          { id: "CLAUSE:IRPWM:CH_03:PARA_335", label: "IRPWM Para 335: Thermal Forces & Destressing Temp (td)", universe: "manuals" },
          { id: "CLAUSE:IRPWM:CH_03:PARA_339", label: "IRPWM Para 339: De-stressing Operation of LWR", universe: "manuals" },
          { id: "CLAUSE:IRPWM:CH_03:PARA_341", label: "IRPWM Para 341: De-stressing with Rail Tensors", universe: "manuals" },
          { id: "CLAUSE:IRPWM:CH_03:PARA_347", label: "IRPWM Para 347: Destressing during Maintenance & SFT", universe: "manuals" },
          { id: "CHAPTER:IRPWM:CH_03", label: "IRPWM Chapter 3: Welded Rails (LWR/CWR)", universe: "manuals" },
          { id: "CHAPTER:STMM:CH_09", label: "STMM Chapter 9: 70t Hydraulic Rail Tensor", universe: "manuals" }
        ],
        primaryNodeId: "CLAUSE:IRPWM:CH_03:PARA_335",
        provenance: {
          doc: "Indian Railways Permanent Way Manual (IRPWM 2024 ACS-14)",
          edition: "2024 Canonical Regulatory Core",
          chapter: "Chapter 3: Installation and Maintenance of Welded Rails",
          clause: "Paras 333, 335, 338, 339, 340, 341 & 347",
          status: "VERIFIED",
          confidence: 0.99
        },
        conflictNote: null,
        workflow: { label: "Open Chapter 3 in Manuals TOC", tab: "manuals" }
      },
"""

    content = content.replace("    const CANONICAL_QA_DATABASE = [\n", "    const CANONICAL_QA_DATABASE = [\n" + destressing_qa_entry)

    # 2. Update detectQuestionIntent to recognize technical topics
    old_detect = """      const isQ = (
        q.endsWith("?") ||
        /^(what|which|how|where|can|is|tell|explain|give|show|list|in which)\\b/i.test(q) ||
        /(wear|throw|tolerance|clearance|standard|specification|irs:|is 2062|usfd|inspect|alt 10|alt 11|alt 12|buffer|spare|crack|defect|mitigat|greas|lubricat|joggled|provisions?)/i.test(q)
      );"""

    new_detect = """      const isQ = (
        q.endsWith("?") ||
        /^(what|which|how|where|can|is|tell|explain|give|show|list|in which)\\b/i.test(q) ||
        /(wear|throw|tolerance|clearance|standard|specification|irs:|is 2062|usfd|inspect|alt 10|alt 11|alt 12|buffer|spare|crack|defect|mitigat|greas|lubricat|joggled|provisions?|destress|temperature|tensor|expansion|welded|lwr|cwr|curve|sleeper|ballast|joint|derail|gauge|cant|versine)/i.test(q)
      );"""

    assert old_detect in content, "old_detect not found"
    content = content.replace(old_detect, new_detect)

    # Also update intent detection inside detectQuestionIntent for destressing/temperature:
    old_intent_branch = """      if (/(standard|specification|irs:|irs |is:|\\bis 2062\\b|\\bis 814\\b|govern|material|grade)/i.test(q)) {
        return { isQuestion: true, intent: "SPECIFICATION_GOVERNANCE", confidence: 0.96 };
      }"""

    new_intent_branch = """      if (/(destress|temperature|td\\b|tensor|standard|specification|irs:|irs |is:|\\bis 2062\\b|\\bis 814\\b|govern|material|grade)/i.test(q)) {
        return { isQuestion: true, intent: "SPECIFICATION_GOVERNANCE", confidence: 0.96 };
      }"""

    assert old_intent_branch in content, "old_intent_branch not found"
    content = content.replace(old_intent_branch, new_intent_branch)

    # 3. Fix rankHybridSearchResults:
    # Remove unconditional score for DRAWING (line 9970) and ensure sGraph only applies if there is text match
    old_hybrid_meta = """        // Level 2: Metadata
        const isDrawingQuery = ['6155', '6154', '6216', '6280', '6275', 'drg', 'drawing', 't-'].some(k => q.includes(k));
        if (type === 'DRAWING' && isDrawingQuery) sMetadata += 300;
        else if (type === 'DRAWING') sMetadata += 100;
        if (type.toLowerCase() === q || domain === q) sMetadata += 150;

        // Level 3: Graph centrality
        const edges = (data.edges || []);
        sGraph += Math.min(edges.length * 10, 80);"""

    new_hybrid_meta = """        // Multi-token lexical matching
        const qTokens = q.split(/[\\s,._-]+/).filter(t => t.length > 2);
        let tokenMatches = 0;
        qTokens.forEach(tok => {
          if (allText.includes(tok)) tokenMatches++;
        });
        if (tokenMatches > 0) {
          sLexical += tokenMatches * 80;
          if (tokenMatches === qTokens.length && qTokens.length > 1) {
            sLexical += 300; // All tokens matched in this entity!
          }
        }

        // Level 2: Metadata - ONLY boost drawings if query actually relates to drawings!
        const isDrawingQuery = ['6155', '6154', '6216', '6280', '6275', 'drg', 'drawing', 't-'].some(k => q.includes(k));
        if (type === 'DRAWING' && isDrawingQuery) sMetadata += 300;
        if (type.toLowerCase() === q || domain === q) sMetadata += 150;

        // Level 3: Graph centrality - ONLY add if node had actual lexical or semantic relevance!
        if (sLexical > 0 || sSemantic > 0 || isDrawingQuery) {
          const edges = (data.edges || []);
          sGraph += Math.min(edges.length * 10, 80);
        }"""

    assert old_hybrid_meta in content, "old_hybrid_meta not found"
    content = content.replace(old_hybrid_meta, new_hybrid_meta)

    # 4. Fix rankSearchResults:
    # Remove unconditional score for DRAWING and add token matching
    old_rank_search = """        // 3. Entity type prioritization for drawings
        const isDrawingQuery = ['6155', '6154', '6216', '6280', '6275', 'drg', 'drawing', 't-'].some(k => q.includes(k));
        if (type === 'DRAWING' && isDrawingQuery) {
          score += 300;
        } else if (type === 'DRAWING') {
          score += 100;
        }

        // 4. Domain & Type match
        if (type.toLowerCase() === q || domain === q) {
          score += 150;
        }

        // 5. Description / Specs match
        if (desc.includes(q)) {
          score += 80;
        }
        if (specsStr.includes(q)) {
          score += 60;
        }"""

    new_rank_search = """        // Multi-token lexical matching
        const allText = id + ' ' + label + ' ' + desc + ' ' + specsStr;
        const qTokens = q.split(/[\\s,._-]+/).filter(t => t.length > 2);
        let tokenMatches = 0;
        qTokens.forEach(tok => {
          if (allText.includes(tok)) tokenMatches++;
        });
        if (tokenMatches > 0) {
          score += tokenMatches * 80;
          if (tokenMatches === qTokens.length && qTokens.length > 1) {
            score += 300; // All tokens matched in this entity!
          }
        }

        // 3. Entity type prioritization for drawings - ONLY if query mentions drawings!
        const isDrawingQuery = ['6155', '6154', '6216', '6280', '6275', 'drg', 'drawing', 't-'].some(k => q.includes(k));
        if (type === 'DRAWING' && isDrawingQuery) {
          score += 300;
        }

        // 4. Domain & Type match
        if (type.toLowerCase() === q || domain === q) {
          score += 150;
        }

        // 5. Description / Specs match
        if (desc.includes(q)) {
          score += 80;
        }
        if (specsStr.includes(q)) {
          score += 60;
        }"""

    assert old_rank_search in content, "old_rank_search not found"
    content = content.replace(old_rank_search, new_rank_search)

    # 5. Fix executeHeroQuery to use rankHybridSearchResults and auto-switch universe
    old_exec_hero = """      const ans = answerEngineeringQuestion(q);
      if (ans) {
        toggleIntelligenceDrawer(true);
        switchDrawerTab('qa');
        renderQuestionAnswerCard(ans, document.getElementById('qa-answer-mount'));
        if (ans.traversal && ans.traversal.length > 0) {
          highlightGraphPath(ans.traversal.map(t => t.id));
        }
      } else {
        const results = rankSearchResults(q);
        if (results.length > 0) {
          inspectNode(results[0]);
          toggleIntelligenceDrawer(true);
        }
      }"""

    new_exec_hero = """      const ans = answerEngineeringQuestion(q);
      if (ans) {
        toggleIntelligenceDrawer(true);
        switchDrawerTab('qa');
        renderQuestionAnswerCard(ans, document.getElementById('qa-answer-mount'));
        if (ans.traversal && ans.traversal.length > 0) {
          highlightGraphPath(ans.traversal.map(t => t.id));
        }
      } else {
        const results = rankHybridSearchResults(q);
        if (results.length > 0) {
          const topNode = results[0].node;
          const targetUniv = getNodeUniverse(topNode.data);
          if (currentKnowledgeUniverse !== 'combined' && currentKnowledgeUniverse !== targetUniv) {
            switchKnowledgeUniverse(targetUniv);
          }
          inspectNode(topNode);
          toggleIntelligenceDrawer(true);
        }
      }"""

    assert old_exec_hero in content, "old_exec_hero not found"
    content = content.replace(old_exec_hero, new_exec_hero)

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully updated index.html with search fixes and destressing QA!")

if __name__ == '__main__':
    fix_search_and_add_destressing_qa()
