"""
backend/app/agent/skills/artifact_gen.py

Artifact generation skill: creates complete, modern HTML/CSS components
or structured Markdown documents grounded in conversation context.
"""

from typing import Dict, Any
from app.llm.base import LLMProvider
from app.core.sanitizer import sanitize_html_artifact

HTML_SAMPLE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Growth & Product Strategy One-Pager</title>
  <style>
    :root {
      --bg: #0f172a;
      --card: #1e293b;
      --card-border: #334155;
      --accent: #38bdf8;
      --accent-glow: rgba(56, 189, 248, 0.15);
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --success: #34d399;
      --warning: #fbbf24;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, sans-serif; }
    body { background: var(--bg); color: var(--text); padding: 2rem; line-height: 1.6; }
    .container { max-width: 900px; margin: 0 auto; }
    .header { margin-bottom: 2rem; border-bottom: 1px solid var(--card-border); padding-bottom: 1.5rem; }
    .tag { display: inline-block; background: var(--accent-glow); color: var(--accent); padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.75rem; border: 1px solid rgba(56,189,248,0.3); }
    h1 { font-size: 2rem; font-weight: 700; color: var(--text); letter-spacing: -0.02em; margin-bottom: 0.5rem; }
    p.lead { color: var(--text-muted); font-size: 1.05rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1.25rem; margin-bottom: 2rem; }
    .card { background: var(--card); border: 1px solid var(--card-border); border-radius: 12px; padding: 1.25rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    .card h3 { font-size: 1rem; color: var(--text); margin-bottom: 0.5rem; display: flex; align-items: center; justify-content: space-between; }
    .metric { font-size: 2rem; font-weight: 700; color: var(--accent); margin: 0.5rem 0; }
    .metric-sub { font-size: 0.85rem; color: var(--text-muted); }
    .section { background: var(--card); border: 1px solid var(--card-border); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; }
    .section-title { font-size: 1.2rem; font-weight: 600; margin-bottom: 1rem; color: var(--text); border-bottom: 1px solid var(--card-border); padding-bottom: 0.5rem; }
    table { width: 100%; border-collapse: collapse; margin-top: 0.75rem; font-size: 0.9rem; }
    th { text-align: left; padding: 0.75rem; color: var(--text-muted); border-bottom: 1px solid var(--card-border); }
    td { padding: 0.75rem; border-bottom: 1px solid rgba(255,255,255,0.05); }
    .status-badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
    .status-active { background: rgba(52, 211, 153, 0.2); color: var(--success); }
    .status-warn { background: rgba(251, 191, 36, 0.2); color: var(--warning); }
    ul { list-style-position: inside; color: var(--text-muted); margin-top: 0.5rem; }
    li { margin-bottom: 0.4rem; }
    strong { color: var(--text); }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <span class="tag">Growth Framework • Lenny Transcript Synthesis</span>
      <h1>Product-Market Fit & Leadership Scorecard</h1>
      <p class="lead">Operational benchmark modeled on Airbnb's product review rhythm and Superhuman's PMF engine.</p>
    </div>

    <div class="grid">
      <div class="card">
        <h3>PMF Conviction Score <span>🎯</span></h3>
        <div class="metric">68%</div>
        <div class="metric-sub">Target: &gt;40% 'Very Disappointed' (Sean Ellis Benchmark)</div>
      </div>
      <div class="card">
        <h3>Founder Immersion Index <span>⚡</span></h3>
        <div class="metric">9.2/10</div>
        <div class="metric-sub">Direct leadership product engagement (Brian Chesky Playbook)</div>
      </div>
      <div class="card">
        <h3>Core Loop Retention <span>🔄</span></h3>
        <div class="metric">54%</div>
        <div class="metric-sub">Day-30 cohort retention flattening (Elena Verna Model)</div>
      </div>
    </div>

    <div class="section">
      <div class="section-title">Strategic Pillars Comparison</div>
      <table>
        <thead>
          <tr>
            <th>Operating Dimension</th>
            <th>Feature Team Anti-Pattern</th>
            <th>Empowered High-Agency Standard</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Leadership Engagement</strong></td>
            <td>Hands-off delegation to committees</td>
            <td>Founder/Leader in design details &amp; customer journey</td>
            <td><span class="status-badge status-active">Optimal</span></td>
          </tr>
          <tr>
            <td><strong>Discovery Rhythm</strong></td>
            <td>PRDs handed down from sales/execs</td>
            <td>Continuous customer interviews + prototypes weekly</td>
            <td><span class="status-badge status-active">Optimal</span></td>
          </tr>
          <tr>
            <td><strong>Growth Acceleration</strong></td>
            <td>Top-of-funnel paid ads masking churn</td>
            <td>Compounding product viral loops &amp; natural retention</td>
            <td><span class="status-badge status-warn">Reviewing</span></td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="section">
      <div class="section-title">Key Operational Directives</div>
      <ul>
        <li><strong>Review Figma work weekly:</strong> Ensure product leads inspect actual customer flows rather than slide presentations.</li>
        <li><strong>Instrument the 'Very Disappointed' metric:</strong> Survey high-frequency users continuously to detect PMF drift early.</li>
        <li><strong>Kill low-retention feature bloat:</strong> Remove features that do not directly drive user activation or core retention curves.</li>
      </ul>
    </div>
  </div>
</body>
</html>
"""

class ArtifactGeneratorSkill:
    async def generate(
        self,
        prompt: str,
        artifact_type: str = "html",
        provider: LLMProvider = None,
        context: str = ""
    ) -> Dict[str, Any]:
        artifact_type = artifact_type.lower().strip()
        if artifact_type not in ["html", "markdown"]:
            artifact_type = "html"

        if provider and provider.name != "simulated":
            # Real LLM call for artifact generation
            system = (
                f"You are an expert full-stack designer and product architect. "
                f"Generate a complete, self-contained {artifact_type.upper()} artifact based on the request. "
                f"If HTML, write complete HTML with modern embedded CSS styling in a <style> tag. "
                f"Use a sleek dark theme (#0f172a background, vibrant accents, glassmorphic cards). "
                f"Do not include explanation text; output ONLY the artifact."
            )
            resp = await provider.complete(
                messages=[{"role": "user", "content": f"Request: {prompt}\nContext: {context}"}],
                system_prompt=system,
                max_tokens=3000
            )
            raw_content = resp.content
            # Strip markdown code fence if present
            if raw_content.startswith("```"):
                lines = raw_content.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                raw_content = "\n".join(lines)
        else:
            # Deterministic, beautiful template
            if artifact_type == "html":
                raw_content = HTML_SAMPLE_TEMPLATE
            else:
                raw_content = (
                    "# Product Strategy One-Pager\n\n"
                    "## Executive Summary\n"
                    "This one-pager synthesizes key operating frameworks from Lenny's Podcast.\n\n"
                    "### 1. The Superhuman PMF Engine\n"
                    "- Survey users: 'How would you feel if you could no longer use the product?'\n"
                    "- Target: >40% 'Very Disappointed'\n"
                    "- Segment the lovers: Analyze who loves the product and double down on their use cases.\n\n"
                    "### 2. Founder Mode Leadership\n"
                    "- Maintain deep visibility into product craft (Brian Chesky)\n"
                    "- Eliminate bureaucratic layers between leadership and user feedback.\n\n"
                    "### 3. Sustainable Growth Loops\n"
                    "- Growth tactics amplify existing product retention; they cannot fix poor retention (Elena Verna).\n"
                )

        # Sanitize HTML defense-in-depth
        final_content = sanitize_html_artifact(raw_content) if artifact_type == "html" else raw_content

        title = "Growth Framework & Strategy One-Pager"
        if "scorecard" in prompt.lower():
            title = "Product-Market Fit Scorecard"
        elif "retention" in prompt.lower():
            title = "Cohort Retention Visualizer"

        return {
            "title": title,
            "type": artifact_type,
            "content": final_content
        }

artifact_skill = ArtifactGeneratorSkill()
