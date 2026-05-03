/**
 * Risk matrix logic: scoring, color mapping, and state management.
 */

export const RISK_COLORS = {
  critical: '#dc2626',
  high:     '#f97316',
  medium:   '#eab308',
  low:      '#22c55e',
};

export function getRiskLevel(score) {
  if (score >= 20) return 'critical';
  if (score >= 12) return 'high';
  if (score >= 6)  return 'medium';
  return 'low';
}

export function getRiskColor(score) {
  return RISK_COLORS[getRiskLevel(score)];
}

export function calcScore(likelihood, impact) {
  return likelihood * impact;
}

/**
 * Generate a 5x5 matrix cell descriptor array.
 * Returns: { likelihood, impact, score, level, color }
 */
export function buildMatrixCells() {
  const cells = [];
  for (let impact = 5; impact >= 1; impact--) {
    for (let likelihood = 1; likelihood <= 5; likelihood++) {
      const score = calcScore(likelihood, impact);
      cells.push({
        likelihood,
        impact,
        score,
        level: getRiskLevel(score),
        color: getRiskColor(score),
      });
    }
  }
  return cells;
}

/**
 * In-memory risk register.
 */
export class RiskRegister {
  constructor() {
    this._risks = [];
    this._nextId = 1;
  }

  add(risk) {
    const entry = {
      id: `R${String(this._nextId++).padStart(3, '0')}`,
      ...risk,
      score: calcScore(risk.likelihood, risk.impact),
      level: getRiskLevel(calcScore(risk.likelihood, risk.impact)),
      createdAt: new Date().toISOString(),
    };
    this._risks.push(entry);
    return entry;
  }

  remove(id) {
    this._risks = this._risks.filter((r) => r.id !== id);
  }

  update(id, updates) {
    const idx = this._risks.findIndex((r) => r.id === id);
    if (idx === -1) return;
    const risk = { ...this._risks[idx], ...updates };
    risk.score = calcScore(risk.likelihood, risk.impact);
    risk.level = getRiskLevel(risk.score);
    this._risks[idx] = risk;
  }

  getAll() {
    return [...this._risks].sort((a, b) => b.score - a.score);
  }

  getByCell(likelihood, impact) {
    return this._risks.filter(
      (r) => r.likelihood === likelihood && r.impact === impact
    );
  }

  getSummary() {
    const all = this._risks;
    return {
      total: all.length,
      critical: all.filter((r) => r.level === 'critical').length,
      high:     all.filter((r) => r.level === 'high').length,
      medium:   all.filter((r) => r.level === 'medium').length,
      low:      all.filter((r) => r.level === 'low').length,
    };
  }

  loadFromJSON(data) {
    for (const r of data.risks ?? []) {
      this.add(r);
    }
  }

  toJSON() {
    return {
      exportedAt: new Date().toISOString(),
      risks: this.getAll(),
    };
  }

  toCSV() {
    const header = 'ID,Title,Category,Likelihood,Impact,Score,Level,Owner,Status,Due Date';
    const rows = this.getAll().map((r) =>
      [
        r.id, `"${(r.title ?? '').replace(/"/g, '""')}"`,
        r.category ?? '',
        r.likelihood, r.impact, r.score,
        r.level,
        `"${(r.owner ?? '').replace(/"/g, '""')}"`,
        r.status ?? '',
        r.due_date ?? '',
      ].join(',')
    );
    return [header, ...rows].join('\n');
  }
}
