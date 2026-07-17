#!/usr/bin/env python3
"""
Générateur de Rapports Complets - JurisBot CI
Exécutez ce script pour générer un rapport complet en HTML/JSON
"""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

from analysis import FeedbackAnalyzer
from recommendations import RecommendationEngine

def generate_html_report(analyzer, engine):
    """Génère un rapport HTML élégant"""
    satisfaction = analyzer.get_user_satisfaction()
    problems = analyzer.get_problem_areas()
    strengths = analyzer.get_strengths()
    quick_wins = engine.get_quick_wins()
    roadmap = engine.get_personalized_roadmap()

    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>JurisBot CI - Rapport d'Analyse</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: #f5f5f5;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                border-radius: 8px;
                margin-bottom: 30px;
            }}
            .header h1 {{
                margin: 0;
                font-size: 2.5em;
            }}
            .timestamp {{
                opacity: 0.9;
                font-size: 0.9em;
            }}
            .metrics {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 20px;
                margin-bottom: 30px;
            }}
            .metric-card {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
            }}
            .metric-value {{
                font-size: 2em;
                font-weight: bold;
                color: #667eea;
                margin: 10px 0;
            }}
            .metric-label {{
                color: #666;
                font-size: 0.9em;
            }}
            .section {{
                background: white;
                padding: 30px;
                margin-bottom: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .section h2 {{
                border-bottom: 3px solid #667eea;
                padding-bottom: 10px;
                margin-top: 0;
            }}
            .problem {{
                border-left: 4px solid #dc3545;
                padding: 15px;
                margin-bottom: 15px;
                background: #f8f9fa;
                border-radius: 4px;
            }}
            .problem.HIGH {{
                border-left-color: #fd7e14;
            }}
            .problem.MEDIUM {{
                border-left-color: #ffc107;
            }}
            .severity {{
                display: inline-block;
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 0.85em;
                margin-bottom: 10px;
            }}
            .severity.CRITICAL {{
                background: #dc3545;
                color: white;
            }}
            .severity.HIGH {{
                background: #fd7e14;
                color: white;
            }}
            .severity.MEDIUM {{
                background: #ffc107;
                color: #333;
            }}
            .strength {{
                border-left: 4px solid #28a745;
                padding: 15px;
                margin-bottom: 15px;
                background: #f8f9fa;
                border-radius: 4px;
            }}
            .quick-win {{
                border-left: 4px solid #667eea;
                padding: 15px;
                margin-bottom: 15px;
                background: #f8f9fa;
                border-radius: 4px;
            }}
            .actions {{
                background: #f0f4ff;
                padding: 10px;
                border-radius: 4px;
                margin: 10px 0;
                font-size: 0.9em;
            }}
            .recommendation {{
                background: #e7f3ff;
                border-left: 4px solid #2196F3;
                padding: 10px;
                margin: 10px 0;
                border-radius: 4px;
            }}
            @media print {{
                body {{
                    background: white;
                }}
                .section {{
                    page-break-inside: avoid;
                    box-shadow: none;
                    border: 1px solid #ddd;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>⚖️ JurisBot CI - Rapport d'Analyse</h1>
            <p class="timestamp">Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}</p>
        </div>

        <div class="metrics">
            <div class="metric-card">
                <div class="metric-label">Score Satisfaction</div>
                <div class="metric-value">{satisfaction['satisfaction_score']:.1f}/5</div>
                <div style="color: #667eea;">{satisfaction['interpretation']}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total Réponses</div>
                <div class="metric-value">{analyzer.response_stats.get('total_responses', 0)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Taux Hallucination</div>
                <div class="metric-value">{analyzer.response_stats.get('hallucination_rate', 0):.1f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total Feedbacks</div>
                <div class="metric-value">{satisfaction['total_feedbacks']}</div>
            </div>
        </div>

        <div class="section">
            <h2>✨ Forces du Système</h2>
    """

    if strengths:
        for strength in strengths:
            html += f"""
            <div class="strength">
                <strong>{strength['area']}</strong> (Score: {strength['score']:.1f})
                <p>{strength['description']}</p>
                <p><em>Valeur: {strength['value']}</em></p>
            </div>
            """
    else:
        html += "<p>Aucune force identifiée pour le moment.</p>"

    html += """
        </div>
    """

    if problems:
        html += f"""
        <div class="section">
            <h2>⚠️ Zones Problématiques ({len(problems)})</h2>
        """

        for problem in problems:
            html += f"""
            <div class="problem {problem['severity']}">
                <span class="severity {problem['severity']}">{problem['severity']}</span>
                <h3 style="margin-top: 0;">{problem['area']}</h3>
                <p>{problem['description']}</p>
                <p><strong>Impact:</strong> {problem['impact']}</p>
                <div class="recommendation">
                    <strong>💡 Recommandation:</strong> {problem['recommendation']}
                </div>
            </div>
            """

        html += """
        </div>
        """

    if quick_wins:
        html += f"""
        <div class="section">
            <h2>⚡ Quick Wins ({len(quick_wins)})</h2>
        """

        for win in quick_wins:
            html += f"""
            <div class="quick-win">
                <h3 style="margin-top: 0;">{win['title']}</h3>
                <p><strong>Priorité:</strong> {win['priority']} | <strong>Effort:</strong> {win['effort']} | <strong>Temps:</strong> {win['estimated_time']}</p>
                <p>{win['description']}</p>
                <div class="actions">
                    <strong>Actions:</strong><br>
                    {'<br>'.join(win['actions'])}
                </div>
                <p><strong>Impact attendu:</strong> {win['expected_impact']}</p>
                <p><strong>✓ Critère de succès:</strong> {win['success_metric']}</p>
            </div>
            """

        html += """
        </div>
        """

    roadmap_phases = roadmap.get('long_term', [])
    if roadmap_phases:
        html += """
        <div class="section">
            <h2>🗺️ Roadmap</h2>
        """

        for phase in roadmap_phases:
            html += f"""
            <div style="margin-bottom: 20px;">
                <h3>{phase['phase']}</h3>
                <p><strong>Timeline:</strong> {phase['timeline']}</p>
                <p>{phase['description']}</p>
                <ul>
            """
            for initiative in phase['initiatives']:
                html += f"<li>{initiative}</li>"

            html += """
                </ul>
            </div>
            """

        html += """
        </div>
        """

    html += """
        <div class="section" style="background: #f8f9fa; border-top: 3px solid #667eea;">
            <p style="text-align: center; color: #666; margin: 0;">
                <em>Rapport généré automatiquement par JurisBot CI Analytics</em>
            </p>
        </div>
    </body>
    </html>
    """

    return html

def main():
    print("=" * 60)
    print("📊 GÉNÉRATEUR DE RAPPORTS - JurisBot CI")
    print("=" * 60)
    print()

    print("🔄 Chargement des données...")
    analyzer = FeedbackAnalyzer()
    engine = RecommendationEngine()

    print(f"✅ {len(analyzer.responses)} réponses chargées")
    print(f"✅ {len(analyzer.feedbacks)} feedbacks chargés")
    print()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("📝 Génération des rapports...")

    json_report_path = analyzer.export_report_json(f"jurisbot_report_analysis_{timestamp}.json")
    print(f"✅ Rapport d'analyse JSON: {json_report_path}")

    json_recommendations_path = engine.export_recommendations(f"jurisbot_report_recommendations_{timestamp}.json")
    print(f"✅ Rapport de recommandations JSON: {json_recommendations_path}")

    html_report_path = f"jurisbot_report_{timestamp}.html"
    html_content = generate_html_report(analyzer, engine)
    with open(html_report_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ Rapport HTML: {html_report_path}")

    print()
    print("=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    print(f"Satisfaction globale: {analyzer.get_user_satisfaction()['satisfaction_score']:.1f}/5")
    print(f"Taux hallucination: {analyzer.response_stats.get('hallucination_rate', 0):.1f}%")
    print(f"Problèmes identifiés: {len(analyzer.get_problem_areas())}")
    print(f"Quick wins recommandés: {len(engine.get_quick_wins())}")
    print()
    print("📁 Fichiers générés:")
    print(f"  - {json_report_path}")
    print(f"  - {json_recommendations_path}")
    print(f"  - {html_report_path}")
    print()
    print("✅ Rapports générés avec succès!")

if __name__ == "__main__":
    main()
