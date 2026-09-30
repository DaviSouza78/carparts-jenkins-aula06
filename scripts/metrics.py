"""Calcula métricas observadas da API Jenkins; não imputa deploys inexistentes."""
import csv
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path


def iso(ms):
    return datetime.fromtimestamp(ms / 1000, timezone.utc).isoformat()


def summarize(builds):
    finished = [b for b in builds if not b.get('building') and b.get('result')]
    if not finished:
        return {'builds': 0}
    ok = [b for b in finished if b['result'] == 'SUCCESS']
    return {
        'builds': len(finished),
        'success': len(ok),
        'success_rate_percent': round(100 * len(ok) / len(finished), 1),
        'median_duration_seconds': round(statistics.median(b['duration'] for b in finished) / 1000, 1),
        'first_build_utc': iso(min(b['timestamp'] for b in finished)),
        'last_build_utc': iso(max(b['timestamp'] for b in finished)),
        'results': {str(b['number']): b['result'] for b in sorted(finished, key=lambda item: item['number'])},
    }


def production_metrics(path):
    if not path.exists():
        return {'status': 'sem deploys de produção observados'}
    with path.open(newline='', encoding='utf-8') as stream:
        rows = [row for row in csv.DictReader(stream) if row['environment'].lower() == 'production']
    if not rows:
        return {'status': 'sem deploys de produção observados'}
    lead_hours = []
    failures = 0
    for row in rows:
        commit = datetime.fromisoformat(row['commit_at_utc'].replace('Z', '+00:00'))
        deployed = datetime.fromisoformat(row['deployed_at_utc'].replace('Z', '+00:00'))
        lead_hours.append((deployed - commit).total_seconds() / 3600)
        failures += row['incident'].lower() in ('yes', 'true', '1', 'sim')
    dates = [datetime.fromisoformat(row['deployed_at_utc'].replace('Z', '+00:00')) for row in rows]
    span_days = max(7, (max(dates) - min(dates)).total_seconds() / 86400)
    return {
        'production_deploys': len(rows),
        'median_lead_hours': round(statistics.median(lead_hours), 2),
        'deploys_per_week': round(7 * len(rows) / span_days, 2),
        'change_failure_percent': round(100 * failures / len(rows), 1),
    }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemExit('Uso: python scripts/metrics.py builds.json [deployments.csv]')
    data = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    builds = data.get('builds', data) if isinstance(data, dict) else data
    result = {'ci': summarize(builds), 'production': production_metrics(Path(sys.argv[2])) if len(sys.argv) > 2 else {'status': 'sem deploys de produção observados'}}
    print(json.dumps(result, ensure_ascii=False, indent=2))
