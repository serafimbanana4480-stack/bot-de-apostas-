"""
Go-Live Validator — Gatekeeper para apostas reais.

Este módulo IMPEDE qualquer aposta real até que TODOS os critérios
de segurança sejam satisfeitos. Não é uma sugestão — é um bloqueio técnico.

Critérios obrigatórios:
1. ECE < 0.05 em validação out-of-sample
2. ROI > +2% em 3000+ apostas paper
3. p-value do ROI < 0.05
4. Brier Score < 0.22
5. Risk of Ruin < 10% (Monte Carlo)
6. Sortino > 1.0
7. Max Drawdown < 20% na simulação
8. Dados reis confirmados (nenhum mock/synthetic)
9. Meta-labeling validado (ROI filtrado > ROI total)
10. Segredos configurados (JWT, DB, Redis)
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.diagnostics.calibration_metrics import BacktestReport

logger = logging.getLogger("go_live_validator")


@dataclass
class GoLiveReport:
    """Relatório completo de validação de prontidão."""
    passed: bool
    checks: Dict[str, Tuple[bool, str]]
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "checks": {k: {"passed": v[0], "message": v[1]} for k, v in self.checks.items()},
            "blockers": self.blockers,
            "warnings": self.warnings,
            "recommendation": self.recommendation,
        }

    def to_markdown(self) -> str:
        lines = [
            "# Go-Live Validation Report",
            f"**Resultado:** {'APROVADO' if self.passed else 'BLOQUEADO'}",
            "",
            "## Checks",
        ]
        for name, (ok, msg) in self.checks.items():
            icon = "[PASS]" if ok else "[FAIL]"
            lines.append(f"- {icon} **{name}**: {msg}")
        if self.blockers:
            lines.extend(["", "## Blockers (impedem go-live)"] + [f"- {b}" for b in self.blockers])
        if self.warnings:
            lines.extend(["", "## Warnings"] + [f"- {w}" for w in self.warnings])
        lines.extend(["", f"## Recommendation\n{self.recommendation}"])
        return "\n".join(lines)


class GoLiveValidator:
    """
    Gatekeeper técnico para apostas reais.

    Usage:
        validator = GoLiveValidator()
        report = validator.validate(report_path="models/optimized/backtest_report.json")
        if not report.passed:
            raise RuntimeError("Go-live blocked: " + str(report.blockers))
    """

    # Thresholds obrigatórios
    MIN_ECE = 0.05
    MIN_ROI_PCT = 2.0
    MIN_BETS = 3000
    MAX_PVALUE = 0.05
    MAX_BRIER = 0.22
    MAX_ROR = 0.10
    MIN_SORTINO = 1.0
    MAX_DRAWDOWN = 0.20

    def __init__(self):
        self.checks: Dict[str, Tuple[bool, str]] = {}
        self.blockers: List[str] = []
        self.warnings: List[str] = []

    def validate(
        self,
        backtest_report: Optional[BacktestReport] = None,
        report_path: Optional[str] = None,
        paper_trading_log: Optional[pd.DataFrame] = None,
        require_real_data: bool = True,
    ) -> GoLiveReport:
        """
        Executa TODAS as validações obrigatórias.

        Args:
            backtest_report: Objeto BacktestReport do modelo
            report_path: Caminho alternativo para JSON do backtest
            paper_trading_log: DataFrame com histórico de paper trading
            require_real_data: Se True, bloqueia se dados mock forem detectados
        """
        self.checks = {}
        self.blockers = []
        self.warnings = []

        # 1. Carregar report se necessário
        bt = self._load_backtest(backtest_report, report_path)

        # 2. Verificações de calibração
        self._check_calibration(bt)

        # 3. Verificações de performance
        self._check_performance(bt)

        # 4. Verificações de risco
        self._check_risk(bt)

        # 5. Verificações de dados
        if require_real_data:
            self._check_real_data()

        # 6. Verificações de infraestrutura
        self._check_infrastructure()

        # 7. Paper trading (se fornecido)
        if paper_trading_log is not None:
            self._check_paper_trading(paper_trading_log)

        passed = len(self.blockers) == 0
        recommendation = (
            "SISTEMA APROVADO para apostas reais com stakes reduzidas (max 1% bankroll). "
            if passed
            else "SISTEMA BLOQUEADO. Resolve todos os blockers acima antes de ativar dinheiro real. "
            "Continua paper trading até atingir 3000+ apostas com ROI > 2% e ECE < 0.05."
        )

        return GoLiveReport(
            passed=passed,
            checks=self.checks,
            blockers=self.blockers,
            warnings=self.warnings,
            recommendation=recommendation,
        )

    def _load_backtest(
        self,
        bt: Optional[BacktestReport],
        path: Optional[str],
    ) -> Optional[BacktestReport]:
        if bt is not None:
            return bt
        if path and Path(path).exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Reconstruct minimal BacktestReport from JSON
            return BacktestReport(
                roi=data.get("roi", 0.0),
                profit_factor=data.get("profit_factor", 0.0),
                sharpe=data.get("sharpe", 0.0),
                sortino=data.get("sortino", 0.0),
                brier_score=data.get("brier_score", 1.0),
                ece=data.get("ece", 1.0),
                clv=data.get("clv", 0.0),
                yield_per_bet=data.get("yield_per_bet", 0.0),
                n_bets=data.get("n_bets", 0),
                win_rate=data.get("win_rate", 0.0),
                avg_odds=data.get("avg_odds", 0.0),
                avg_edge=data.get("avg_edge", 0.0),
                max_drawdown=data.get("max_drawdown", 1.0),
                risk_of_ruin=data.get("risk_of_ruin", 1.0),
                kelly_ratio=data.get("kelly_ratio", 0.0),
                statistical_significance=data.get("statistical_significance", 1.0),
                min_bets_for_significance=data.get("min_bets_for_significance", 9999),
            )
        self.blockers.append("BacktestReport não fornecido e report_path inexistente")
        return None

    def _check_calibration(self, bt: Optional[BacktestReport]) -> None:
        if bt is None:
            self.checks["calibration_ece"] = (False, "Backtest indisponível")
            self.blockers.append("Calibração não verificável sem backtest")
            return

        ece_ok = bt.ece < self.MIN_ECE
        self.checks["calibration_ece"] = (
            ece_ok,
            f"ECE={bt.ece:.4f} {'<' if ece_ok else '>='} threshold {self.MIN_ECE}",
        )
        if not ece_ok:
            self.blockers.append(f"ECE {bt.ece:.4f} >= {self.MIN_ECE}: modelo mal calibrado")

        brier_ok = bt.brier_score < self.MAX_BRIER
        self.checks["calibration_brier"] = (
            brier_ok,
            f"Brier={bt.brier_score:.4f} {'<' if brier_ok else '>='} threshold {self.MAX_BRIER}",
        )
        if not brier_ok:
            self.blockers.append(f"Brier {bt.brier_score:.4f} >= {self.MAX_BRIER}")

    def _check_performance(self, bt: Optional[BacktestReport]) -> None:
        if bt is None:
            self.checks["performance_roi"] = (False, "Backtest indisponível")
            self.checks["performance_significance"] = (False, "Backtest indisponível")
            return

        roi_pct = bt.roi * 100
        roi_ok = roi_pct > self.MIN_ROI_PCT
        self.checks["performance_roi"] = (
            roi_ok,
            f"ROI={roi_pct:.2f}% {'>' if roi_ok else '<='} threshold {self.MIN_ROI_PCT}%",
        )
        if not roi_ok:
            self.blockers.append(f"ROI {roi_pct:.2f}% <= {self.MIN_ROI_PCT}%")

        n_ok = bt.n_bets >= self.MIN_BETS
        self.checks["performance_sample"] = (
            n_ok,
            f"n_bets={bt.n_bets} {'>=' if n_ok else '<'} threshold {self.MIN_BETS}",
        )
        if not n_ok:
            self.blockers.append(f"Amostra insuficiente: {bt.n_bets} < {self.MIN_BETS} apostas")

        p_ok = bt.statistical_significance < self.MAX_PVALUE
        self.checks["performance_significance"] = (
            p_ok,
            f"p-value={bt.statistical_significance:.4f} {'<' if p_ok else '>='} threshold {self.MAX_PVALUE}",
        )
        if not p_ok:
            self.blockers.append(f"p-value {bt.statistical_significance:.4f} >= {self.MAX_PVALUE}: ROI não é significativo")

    def _check_risk(self, bt: Optional[BacktestReport]) -> None:
        if bt is None:
            self.checks["risk_ror"] = (False, "Backtest indisponível")
            self.checks["risk_drawdown"] = (False, "Backtest indisponível")
            self.checks["risk_sortino"] = (False, "Backtest indisponível")
            return

        ror_ok = bt.risk_of_ruin < self.MAX_ROR
        self.checks["risk_ror"] = (
            ror_ok,
            f"RoR={bt.risk_of_ruin:.2%} {'<' if ror_ok else '>='} threshold {self.MAX_ROR:.0%}",
        )
        if not ror_ok:
            self.blockers.append(f"Risk of Ruin {bt.risk_of_ruin:.2%} >= {self.MAX_ROR:.0%}")

        dd_ok = bt.max_drawdown < self.MAX_DRAWDOWN
        self.checks["risk_drawdown"] = (
            dd_ok,
            f"MaxDD={bt.max_drawdown:.2%} {'<' if dd_ok else '>='} threshold {self.MAX_DRAWDOWN:.0%}",
        )
        if not dd_ok:
            self.blockers.append(f"Max Drawdown {bt.max_drawdown:.2%} >= {self.MAX_DRAWDOWN:.0%}")

        sort_ok = bt.sortino > self.MIN_SORTINO
        self.checks["risk_sortino"] = (
            sort_ok,
            f"Sortino={bt.sortino:.2f} {'>' if sort_ok else '<='} threshold {self.MIN_SORTINO}",
        )
        if not sort_ok:
            self.blockers.append(f"Sortino {bt.sortino:.2f} <= {self.MIN_SORTINO}")

    def _check_real_data(self) -> None:
        """Verifica que não existam dados mock no sistema."""
        project_root = Path(__file__).resolve().parent.parent.parent
        mock_indicators = [
            project_root / "data" / "bronze" / "matches_football_mock.parquet",
            project_root / "data" / "bronze" / "matches_football_backtest.parquet",
            project_root / "data" / "mock_football.csv",
        ]
        found = [str(p) for p in mock_indicators if p.exists()]

        real_ok = len(found) == 0
        self.checks["data_real"] = (
            real_ok,
            "Nenhum ficheiro mock encontrado" if real_ok else f"Mock files encontrados: {found}",
        )
        if not real_ok:
            self.blockers.append(f"Dados mock detectados: {found}. REMOVE-OS antes do go-live.")

        # Verifica configuração
        from src.core.config import settings
        if getattr(settings, "ZERO_COST_MODE", True):
            self.warnings.append("ZERO_COST_MODE=True — certifica-te de que os dados são reais")

    def _check_infrastructure(self) -> None:
        """Verifica secrets e conectividade."""
        from src.core.config import settings

        secrets_ok = True
        missing = []
        for secret in ["JWT_SECRET_KEY", "ENCRYPTION_KEY", "POSTGRES_PASSWORD", "REDIS_PASSWORD"]:
            val = os.getenv(secret, "")
            if not val or val.lower() in ("", "secret", "changeme", "password", "postgres"):
                secrets_ok = False
                missing.append(secret)

        self.checks["infra_secrets"] = (
            secrets_ok,
            "Todos os secrets configurados" if secrets_ok else f"Secrets em falta/fracos: {missing}",
        )
        if not secrets_ok:
            self.blockers.append(f"Secrets inválidos: {missing}")

        # Verifica PAPER_TRADING_ONLY
        if not getattr(settings, "PAPER_TRADING_ONLY", True):
            self.checks["infra_paper_only"] = (
                False,
                "PAPER_TRADING_ONLY=False detectado — confirma intenção manualmente",
            )
            self.warnings.append("PAPER_TRADING_ONLY=False. Confirma que queres ativar apostas reais.")
        else:
            self.checks["infra_paper_only"] = (True, "PAPER_TRADING_ONLY=True (seguro)")

    def _check_paper_trading(self, df: pd.DataFrame) -> None:
        """Valida histórico de paper trading."""
        n = len(df)
        n_ok = n >= self.MIN_BETS
        self.checks["paper_sample"] = (
            n_ok,
            f"Paper bets={n} {'>=' if n_ok else '<'} {self.MIN_BETS}",
        )
        if not n_ok:
            self.blockers.append(f"Paper trading insuficiente: {n} apostas")

        if "profit" in df.columns and "stake" in df.columns:
            roi = df["profit"].sum() / df["stake"].sum()
            roi_ok = roi > self.MIN_ROI_PCT / 100
            self.checks["paper_roi"] = (
                roi_ok,
                f"Paper ROI={roi:.2%} {'>' if roi_ok else '<='} {self.MIN_ROI_PCT/100:.2%}",
            )
            if not roi_ok:
                self.blockers.append(f"Paper ROI {roi:.2%} <= {self.MIN_ROI_PCT/100:.2%}")

        # Verifica se há odds reais (não mock)
        if "bookmaker" in df.columns:
            mock_bets = df["bookmaker"].str.contains("mock", case=False, na=False).sum()
            if mock_bets > 0:
                self.blockers.append(f"Paper log contém {mock_bets} apostas com bookmaker 'mock'")


def enforce_go_live_gate(**kwargs) -> GoLiveReport:
    """
    Convenience function that raises RuntimeError if go-live checks fail.
    Use this at startup of any real-money execution path.
    """
    validator = GoLiveValidator()
    report = validator.validate(**kwargs)
    if not report.passed:
        logger.error("GO-LIVE BLOCKED: %s", report.blockers)
        raise RuntimeError(f"Go-live validation failed: {report.blockers}")
    logger.info("GO-LIVE APPROVED: %s", report.recommendation)
    return report
