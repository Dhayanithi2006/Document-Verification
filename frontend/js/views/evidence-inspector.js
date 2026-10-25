// AICTE Pre-Scrutiny & Deficiency Resolution Platform
// View: Primary USP — Split-Screen Evidence Inspector (evidence-inspector.js)
import { icons } from '../icons.js';
import { renderBreadcrumbs, renderBadge } from '../components.js';
import { syntheticFindings, syntheticApplications } from '../sample-data.js';

export function renderEvidenceInspector(state, params) {
  const findingId = params.finding_id || 'find_0042';
  const appId = params.id || 'app_9812';
  
  const finding = syntheticFindings.find(f => f.id === findingId) || syntheticFindings[0];
  const app = syntheticApplications.find(a => a.id === appId) || syntheticApplications[0];

  const breadcrumbs = renderBreadcrumbs([
    { label: 'Home', href: '#/dashboard' },
    { label: 'Applications', href: '#/applications' },
    { label: app.applicationNumber, href: `#/applications/${app.id}` },
    { label: `Evidence Inspector (${finding.id})` }
  ]);

  // Convert normalized bounding box to CSS percentages
  const box = finding.evidence.boundingBox;
  const boxTop = (box.ymin * 100).toFixed(1) + '%';
  const boxLeft = (box.xmin * 100).toFixed(1) + '%';
  const boxWidth = ((box.xmax - box.xmin) * 100).toFixed(1) + '%';
  const boxHeight = ((box.ymax - box.ymin) * 100).toFixed(1) + '%';

  return `
    ${breadcrumbs}
    <div class="content-container">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-4); flex-wrap: wrap; gap: var(--space-2);">
        <div>
          <h1 style="font-size: var(--text-xl);">Split-Screen Regulatory Evidence Inspector</h1>
          <p style="color: var(--text-muted); font-size: var(--text-xs); margin-top: 2px;">
            AICTE Decision-Support Engine: Visual Evidence Grounding & Rule Cross-Matching
          </p>
        </div>
        <div style="display: flex; gap: var(--space-2);">
          <a href="#/applications/${app.id}" class="btn btn-secondary btn-sm">
            ${icons.chevronRight}
            <span>Back to Checklist</span>
          </a>
          <a href="#/applications/${app.id}/deficiencies" class="btn btn-danger btn-sm">
            <span>Deficiency Resolution Bridge</span>
          </a>
        </div>
      </div>

      <!-- Split-Screen USP Layout -->
      <div class="split-screen-container">
        
        <!-- LEFT PANE: Finding Details & Regulatory Rule Grounding -->
        <div class="evidence-finding-pane">
          <div class="finding-pane-header">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--space-1);">
              <span style="font-family: var(--font-mono); font-size: var(--text-xs); font-weight: bold; color: var(--color-blue-700);">
                Finding #${finding.id}
              </span>
              ${renderBadge(finding.severity, finding.severity)}
            </div>
            <h2 style="font-size: var(--text-base); margin-top: 4px;">${finding.ruleTitle}</h2>
            <div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;">
              Rule Code: <strong>${finding.ruleCode}</strong> (v${finding.ruleVersion})
            </div>
          </div>

          <div class="finding-pane-body">
            <!-- Official Regulatory Source -->
            <div style="background-color: var(--color-blue-50); border-left: 3px solid var(--color-blue-600); padding: var(--space-2) var(--space-3); border-radius: var(--radius-xs); margin-bottom: var(--space-4); font-size: var(--text-xs);">
              <div style="font-weight: 600; color: var(--color-blue-800);">Official Regulatory Authority:</div>
              <div style="color: var(--color-blue-700);">${finding.officialSource}</div>
            </div>

            <!-- Plain-Language Explanation -->
            <div style="margin-bottom: var(--space-4);">
              <div class="val-label">Reason for Discrepancy Flag</div>
              <p style="font-size: var(--text-sm); color: var(--text-primary); line-height: 1.5;">
                ${finding.explanation}
              </p>
            </div>

            <!-- Expected vs Observed Parameter Comparison -->
            <div class="deficiency-values-box" style="margin-bottom: var(--space-4);">
              <div>
                <div class="val-label">Expected Value (APH Norm)</div>
                <div class="val-data expected">${finding.expectedValue}</div>
              </div>
              <div>
                <div class="val-label">Observed Value (Extracted)</div>
                <div class="val-data observed">${finding.observedValue}</div>
              </div>
            </div>

            <!-- Extracted Snippet & Provenance Metadata -->
            <div style="background-color: var(--color-slate-50); border: 1px solid var(--border-light); border-radius: var(--radius-sm); padding: var(--space-3); margin-bottom: var(--space-4);">
              <div class="val-label" style="display: flex; justify-content: space-between;">
                <span>Extracted Document Text</span>
                <span style="color: var(--color-green-700); font-weight: bold;">Confidence: ${(finding.evidence.confidence * 100).toFixed(1)}%</span>
              </div>
              <div style="font-family: var(--font-mono); font-size: 11px; color: var(--color-slate-800); background-color: var(--color-white); padding: var(--space-2); border-radius: var(--radius-xs); border: 1px solid var(--border-light); margin-top: var(--space-1); line-height: 1.4;">
                "${finding.evidence.extractedSnippet}"
              </div>
              <div style="font-size: 10px; color: var(--text-muted); margin-top: var(--space-2); display: flex; justify-content: space-between;">
                <span>Method: ${finding.evidence.extractionMethod}</span>
                <span>Coordinates: Page ${finding.evidence.pageNumber}</span>
              </div>
            </div>

            <!-- Recommended Remediation -->
            <div style="background-color: var(--color-amber-50); border: 1px solid var(--color-amber-100); border-radius: var(--radius-sm); padding: var(--space-3);">
              <div style="font-size: var(--text-xs); font-weight: bold; color: var(--color-amber-700); margin-bottom: 2px;">
                Recommended Institutional Action:
              </div>
              <div style="font-size: var(--text-xs); color: var(--color-slate-700); line-height: 1.4;">
                ${finding.recommendedAction}
              </div>
            </div>
          </div>

          <div class="finding-pane-footer">
            <button class="btn btn-primary" onclick="alert('Prototype Notice: The Deficiency Resolution Bridge will open the v2 upload modal in Phase P3.');">
              ${icons.upload}
              <span>Upload Corrected Version (v2)</span>
            </button>
          </div>
        </div>

        <!-- RIGHT PANE: Document Viewer with Visual Bounding-Box Overlay -->
        <div class="evidence-document-pane">
          <div class="document-viewer-toolbar">
            <div class="toolbar-group">
              <span style="font-weight: 600; color: #FFFFFF;">${finding.evidence.documentTitle}</span>
              <span style="color: var(--color-slate-400);">• Page ${finding.evidence.pageNumber} of 4</span>
            </div>
            <div class="toolbar-group">
              <button class="toolbar-btn" onclick="alert('Zoom Out');">- 100% +</button>
              <button class="toolbar-btn" onclick="alert('Rotate 90 deg');">Rotate</button>
              <button class="toolbar-btn" onclick="alert('Downloading original PDF: ${finding.evidence.documentTitle}');">
                Download Original
              </button>
            </div>
          </div>

          <div class="document-canvas-viewport">
            <!-- Simulated High-Fidelity PDF Document Page -->
            <div class="mock-pdf-page">
              
              <!-- Official Document Header -->
              <div class="pdf-header-emblem">
                <div style="font-size: 10pt; color: #475569; letter-spacing: 0.1em;">GOVERNMENT OF KARNATAKA</div>
                <div class="pdf-gov-title">OFFICE OF THE SPECIAL DEPUTY COMMISSIONER</div>
                <div style="font-size: 9pt; color: #64748b;">Revenue Department, Bengaluru Urban District</div>
              </div>

              <div style="display: flex; justify-content: space-between; font-size: 9pt; margin-bottom: 16px;">
                <span>Ref No: ALN/CR/2021-22/44</span>
                <span>Date of Issue: 14th June 2021</span>
              </div>

              <div class="pdf-doc-title">
                OFFICIAL CONVERSION ORDER & LAND USE CERTIFICATE
              </div>

              <div class="pdf-body-p">
                Subject: Permission for conversion of agricultural land into non-agricultural institutional use under Section 95 of Karnataka Land Revenue Act, 1964.
              </div>

              <div class="pdf-body-p">
                Preamble: In exercise of powers conferred upon the Deputy Commissioner, application submitted by the Principal, Apex Educational Trust, requesting permission to divert land from agricultural purpose to Educational Institutional use was examined by the competent survey and town planning authority.
              </div>

              <div class="pdf-body-p">
                ORDER: It is hereby ordered that sanction is accorded for conversion of the scheduled parcel of land subject to statutory conditions of the Master Plan.
              </div>

              <div class="pdf-body-p" style="margin-top: 24px; padding: 12px; border: 1px solid #cbd5e1; background-color: #f8fafc; font-size: 9pt;">
                <strong>SCHEDULE OF PROPERTY CONVERTED:</strong><br>
                Village: Electronic City, Begur Hobli, Bengaluru South Taluk.<br>
                District: Bengaluru Urban.<br>
                Extent Converted: 5.20 Acres (Five Acres and Twenty Guntas).<br>
                Zoning Classification: Public & Semi-Public (Educational).
              </div>

              <!-- Interactive Bounding-Box Overlay for Discrepancy -->
              <div class="bounding-box-highlight" style="top: ${boxTop}; left: ${boxLeft}; width: ${boxWidth}; height: ${boxHeight};" title="Click to view extraction detail">
                <div class="bounding-box-tag">
                  ${icons.alertTriangle}
                  <span>${finding.observedValue}</span>
                </div>
              </div>

              <div class="pdf-body-p" style="margin-top: 36px;">
                Given under my hand and seal of the Office of the Deputy Commissioner, Bengaluru Urban, this 14th day of June 2021.
              </div>

              <div style="margin-top: 48px; text-align: right; font-size: 9pt;">
                <strong>(Sd/-)</strong><br>
                Special Deputy Commissioner<br>
                Bengaluru Urban District
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  `;
}
