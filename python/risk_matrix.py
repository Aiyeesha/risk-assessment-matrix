from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal, Optional

RiskLevel = Literal["critical", "high", "medium", "low"]


def get_level(score: int) -> RiskLevel:
    if score >= 20: return "critical"
    if score >= 12: return "high"
    if score >= 6:  return "medium"
    return "low"


def get_color(level: RiskLevel) -> str:
    return {"critical": "#dc2626", "high": "#f97316", "medium": "#eab308", "low": "#22c55e"}[level]


@dataclass
class Risk:
    id: str
    title: str
    category: str
    likelihood: int
    impact: int
    description: str = ""
    existing_controls: str = ""
    mitigation: str = ""
    owner: str = ""
    due_date: str = ""
    status: str = "open"

    @property
    def score(self) -> int:
        return self.likelihood * self.impact

    @property
    def level(self) -> RiskLevel:
        return get_level(self.score)

    @property
    def color(self) -> str:
        return get_color(self.level)


@dataclass
class RiskRegister:
    organization: str
    assessor: str
    assessment_date: str
    risks: List[Risk] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "RiskRegister":
        register = cls(
            organization=data.get("organization", "Organization"),
            assessor=data.get("assessor", "Security Analyst"),
            assessment_date=data.get("assessment_date", datetime.utcnow().date().isoformat()),
        )
        for r in data.get("risks", []):
            register.risks.append(Risk(
                id=r.get("id", ""),
                title=r["title"],
                category=r.get("category", ""),
                likelihood=int(r["likelihood"]),
                impact=int(r["impact"]),
                description=r.get("description", ""),
                existing_controls=r.get("existing_controls", ""),
                mitigation=r.get("mitigation", ""),
                owner=r.get("owner", ""),
                due_date=r.get("due_date", ""),
                status=r.get("status", "open"),
            ))
        return register

    def sorted_risks(self) -> List[Risk]:
        return sorted(self.risks, key=lambda r: r.score, reverse=True)

    def summary(self) -> dict:
        levels = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for r in self.risks:
            levels[r.level] += 1
        return levels
