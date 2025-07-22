"""
Early Warning System - Task 2.1.3

Provides EarlyWarningSystem for quality degradation detection
and AlertManager for automated alert generation and management.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import time

from .quality_predictor import QualityTrendAnalyzer, PredictiveRiskAssessment, RiskAssessment


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning" 
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status states"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class Alert:
    """Represents a quality degradation alert"""
    id: str
    title: str
    description: str
    severity: AlertSeverity
    status: AlertStatus
    created_at: datetime
    updated_at: datetime
    source_metric: str
    current_value: float
    threshold_value: float
    predicted_impact: str
    recommended_actions: List[str]
    confidence_level: float
    risk_assessment: Optional[RiskAssessment] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary for serialization"""
        data = asdict(self)
        # Convert datetime objects to ISO format
        for field in ['created_at', 'updated_at', 'acknowledged_at', 'resolved_at']:
            if data[field]:
                data[field] = data[field].isoformat()
        # Convert enums to values
        data['severity'] = self.severity.value
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Alert':
        """Create alert from dictionary"""
        # Convert ISO format to datetime objects
        for field in ['created_at', 'updated_at', 'acknowledged_at', 'resolved_at']:
            if data.get(field):
                data[field] = datetime.fromisoformat(data[field])
        
        # Convert enum values back to enums
        data['severity'] = AlertSeverity(data['severity'])
        data['status'] = AlertStatus(data['status'])
        
        return cls(**data)


@dataclass
class AlertRule:
    """Defines rules for alert generation"""
    id: str
    name: str
    metric_name: str
    condition: str  # 'below', 'above', 'declining', 'increasing'
    threshold: float
    severity: AlertSeverity
    enabled: bool = True
    cooldown_hours: int = 24  # Minimum hours between similar alerts
    description: str = ""


class EarlyWarningSystem:
    """
    Advanced early warning system for quality degradation detection.
    
    Capabilities:
    - Real-time quality monitoring with <30 second detection
    - Configurable alert rules and thresholds
    - Multi-level severity classification
    - Predictive alerts based on trend analysis
    - Automated escalation procedures
    """
    
    def __init__(self, quality_analyzer: QualityTrendAnalyzer, 
                 risk_assessor: PredictiveRiskAssessment,
                 storage_path: str = None):
        """Initialize the early warning system"""
        self.quality_analyzer = quality_analyzer
        self.risk_assessor = risk_assessor
        
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(__file__), '..', '..', '..', '..', 
            'Lab', 'Project Management', 'workflow-automation', 'alerts.json'
        )
        
        self.alert_rules: List[AlertRule] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.alert_callbacks: List[Callable[[Alert], None]] = []
        
        self._monitoring_active = False
        self._monitor_thread: Optional[threading.Thread] = None
        
        self._initialize_default_rules()
        self._load_alerts()
    
    def _initialize_default_rules(self) -> None:
        """Initialize default alert rules"""
        default_rules = [
            AlertRule(
                id="doc_coverage_critical",
                name="Documentation Coverage Critical",
                metric_name="doc_coverage",
                condition="below",
                threshold=50.0,
                severity=AlertSeverity.CRITICAL,
                description="Documentation coverage has fallen below critical threshold"
            ),
            AlertRule(
                id="doc_coverage_warning",
                name="Documentation Coverage Warning", 
                metric_name="doc_coverage",
                condition="below",
                threshold=70.0,
                severity=AlertSeverity.WARNING,
                description="Documentation coverage is below recommended threshold"
            ),
            AlertRule(
                id="code_quality_critical",
                name="Code Quality Critical",
                metric_name="code_quality_score",
                condition="below",
                threshold=60.0,
                severity=AlertSeverity.CRITICAL,
                description="Code quality score has dropped to critical levels"
            ),
            AlertRule(
                id="code_quality_declining",
                name="Code Quality Declining",
                metric_name="code_quality_score",
                condition="declining",
                threshold=10.0,  # 10% decline
                severity=AlertSeverity.WARNING,
                description="Code quality showing declining trend"
            ),
            AlertRule(
                id="complexity_explosion",
                name="Complexity Explosion",
                metric_name="complexity_score",
                condition="above",
                threshold=40.0,
                severity=AlertSeverity.ERROR,
                description="Code complexity has increased beyond acceptable levels"
            ),
            AlertRule(
                id="test_coverage_critical",
                name="Test Coverage Critical",
                metric_name="test_coverage",
                condition="below",
                threshold=50.0,
                severity=AlertSeverity.CRITICAL,
                description="Test coverage has fallen below critical threshold"
            ),
            AlertRule(
                id="maintainability_declining",
                name="Maintainability Declining",
                metric_name="maintainability_index",
                condition="declining",
                threshold=15.0,  # 15% decline
                severity=AlertSeverity.WARNING,
                description="Code maintainability showing concerning decline"
            ),
            AlertRule(
                id="technical_debt_explosion",
                name="Technical Debt Explosion",
                metric_name="technical_debt_ratio",
                condition="above",
                threshold=25.0,
                severity=AlertSeverity.ERROR,
                description="Technical debt ratio has exceeded safe limits"
            )
        ]
        
        self.alert_rules.extend(default_rules)
    
    def add_alert_rule(self, rule: AlertRule) -> None:
        """Add a new alert rule"""
        # Remove existing rule with same ID if present
        self.alert_rules = [r for r in self.alert_rules if r.id != rule.id]
        self.alert_rules.append(rule)
    
    def remove_alert_rule(self, rule_id: str) -> bool:
        """Remove an alert rule by ID"""
        original_count = len(self.alert_rules)
        self.alert_rules = [r for r in self.alert_rules if r.id != rule_id]
        return len(self.alert_rules) < original_count
    
    def update_alert_rule(self, rule_id: str, **updates) -> bool:
        """Update an existing alert rule"""
        for rule in self.alert_rules:
            if rule.id == rule_id:
                for key, value in updates.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
                return True
        return False
    
    def start_monitoring(self, check_interval_seconds: int = 30) -> None:
        """Start continuous quality monitoring"""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(check_interval_seconds,),
            daemon=True
        )
        self._monitor_thread.start()
    
    def stop_monitoring(self) -> None:
        """Stop continuous quality monitoring"""
        self._monitoring_active = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
    
    def _monitor_loop(self, check_interval: int) -> None:
        """Main monitoring loop"""
        while self._monitoring_active:
            try:
                self.check_all_metrics()
                time.sleep(check_interval)
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(check_interval)
    
    def check_all_metrics(self) -> List[Alert]:
        """Check all metrics against alert rules and generate alerts if needed"""
        new_alerts = []
        
        # Get current quality trends
        quality_trends = self.quality_analyzer.get_overall_quality_trend()
        individual_trends = quality_trends['individual_trends']
        
        # Check each alert rule
        for rule in self.alert_rules:
            if not rule.enabled:
                continue
            
            alert = self._check_rule_against_trends(rule, individual_trends)
            if alert:
                new_alerts.append(alert)
        
        # Check for predictive risks
        risk_alerts = self._generate_risk_based_alerts()
        new_alerts.extend(risk_alerts)
        
        # Process new alerts
        for alert in new_alerts:
            self._process_new_alert(alert)
        
        return new_alerts
    
    def _check_rule_against_trends(self, rule: AlertRule, 
                                 trends: Dict[str, Any]) -> Optional[Alert]:
        """Check a specific rule against current trends"""
        trend = trends.get(rule.metric_name)
        if not trend:
            return None
        
        current_value = trend.current_value
        predicted_value = trend.predicted_value_7d
        
        # Check if alert should be triggered
        should_alert = False
        threshold_value = rule.threshold
        
        if rule.condition == "below":
            should_alert = current_value < rule.threshold
        elif rule.condition == "above":
            should_alert = current_value > rule.threshold
        elif rule.condition == "declining":
            decline_percent = ((current_value - predicted_value) / current_value) * 100
            should_alert = decline_percent > rule.threshold
            threshold_value = decline_percent
        elif rule.condition == "increasing":
            increase_percent = ((predicted_value - current_value) / current_value) * 100
            should_alert = increase_percent > rule.threshold
            threshold_value = increase_percent
        
        if not should_alert:
            return None
        
        # Check cooldown period
        if self._is_in_cooldown(rule.id):
            return None
        
        # Generate alert
        alert_id = f"{rule.id}_{int(datetime.now().timestamp())}"
        
        # Generate recommended actions based on rule
        recommended_actions = self._generate_rule_based_actions(rule, trend)
        
        # Determine predicted impact
        predicted_impact = self._assess_predicted_impact(rule, trend)
        
        alert = Alert(
            id=alert_id,
            title=rule.name,
            description=self._generate_alert_description(rule, trend),
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            source_metric=rule.metric_name,
            current_value=current_value,
            threshold_value=threshold_value,
            predicted_impact=predicted_impact,
            recommended_actions=recommended_actions,
            confidence_level=trend.confidence_level
        )
        
        return alert
    
    def _generate_risk_based_alerts(self) -> List[Alert]:
        """Generate alerts based on predictive risk assessment"""
        alerts = []
        
        # Get risk assessments
        risks = self.risk_assessor.assess_risks()
        
        for risk in risks:
            # Only create alerts for high-probability, high-impact risks
            if risk.probability < 0.5 or risk.impact_severity in ['low']:
                continue
            
            # Check cooldown
            cooldown_id = f"risk_{risk.risk_type.lower().replace(' ', '_')}"
            if self._is_in_cooldown(cooldown_id):
                continue
            
            # Determine alert severity based on risk
            if risk.impact_severity == 'critical':
                severity = AlertSeverity.CRITICAL
            elif risk.impact_severity == 'high':
                severity = AlertSeverity.ERROR
            else:
                severity = AlertSeverity.WARNING
            
            alert_id = f"risk_{cooldown_id}_{int(datetime.now().timestamp())}"
            
            alert = Alert(
                id=alert_id,
                title=f"Predicted Risk: {risk.risk_type}",
                description=f"High probability ({risk.probability:.1%}) of {risk.risk_type.lower()} "
                           f"within {risk.predicted_timeline}",
                severity=severity,
                status=AlertStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                source_metric="predictive_risk",
                current_value=risk.probability,
                threshold_value=0.5,
                predicted_impact=f"{risk.impact_severity} impact expected {risk.predicted_timeline}",
                recommended_actions=risk.mitigation_suggestions,
                confidence_level=risk.confidence_level,
                risk_assessment=risk
            )
            
            alerts.append(alert)
        
        return alerts
    
    def _is_in_cooldown(self, rule_id: str) -> bool:
        """Check if a rule is in cooldown period"""
        # Find the most recent alert for this rule
        recent_alerts = [
            alert for alert in self.alert_history
            if alert.id.startswith(rule_id) or alert.id.startswith(f"risk_{rule_id}")
        ]
        
        if not recent_alerts:
            return False
        
        # Sort by creation time, most recent first
        recent_alerts.sort(key=lambda a: a.created_at, reverse=True)
        most_recent = recent_alerts[0]
        
        # Check if within cooldown period (default 24 hours)
        cooldown_hours = 24  # Could be made configurable per rule
        cooldown_delta = timedelta(hours=cooldown_hours)
        
        return datetime.now() - most_recent.created_at < cooldown_delta
    
    def _generate_rule_based_actions(self, rule: AlertRule, trend: Any) -> List[str]:
        """Generate recommended actions based on the alert rule"""
        actions = []
        
        if rule.metric_name == "doc_coverage":
            actions.extend([
                "Run auto-documentation generator on affected modules",
                "Schedule documentation review session",
                "Update code comments and docstrings"
            ])
        elif rule.metric_name == "code_quality_score":
            actions.extend([
                "Run code linting and fix reported issues",
                "Perform code review on recent changes",
                "Refactor complex or problematic code sections"
            ])
        elif rule.metric_name == "complexity_score":
            actions.extend([
                "Identify and refactor most complex methods",
                "Break down large functions into smaller units",
                "Review and simplify complex logic"
            ])
        elif rule.metric_name == "test_coverage":
            actions.extend([
                "Add unit tests for uncovered code paths",
                "Review and update existing test cases",
                "Implement integration tests for critical workflows"
            ])
        elif rule.metric_name == "maintainability_index":
            actions.extend([
                "Address technical debt in affected modules",
                "Refactor code to improve readability",
                "Update outdated dependencies and libraries"
            ])
        elif rule.metric_name == "technical_debt_ratio":
            actions.extend([
                "Prioritize technical debt reduction tasks",
                "Schedule refactoring sprint",
                "Implement architectural improvements"
            ])
        
        # Add trend-specific actions
        if hasattr(trend, 'trend_direction') and trend.trend_direction == 'declining':
            actions.append("Monitor trend closely for further degradation")
            actions.append("Consider implementing additional quality gates")
        
        return actions
    
    def _assess_predicted_impact(self, rule: AlertRule, trend: Any) -> str:
        """Assess the predicted impact of the quality issue"""
        if rule.severity == AlertSeverity.CRITICAL:
            return "High impact: May cause significant project delays or quality issues"
        elif rule.severity == AlertSeverity.ERROR:
            return "Medium impact: May affect project quality and maintainability"
        elif rule.severity == AlertSeverity.WARNING:
            return "Low impact: Early warning of potential quality degradation"
        else:
            return "Informational: Quality metric requires attention"
    
    def _generate_alert_description(self, rule: AlertRule, trend: Any) -> str:
        """Generate detailed alert description"""
        base_description = rule.description
        
        if hasattr(trend, 'current_value') and hasattr(trend, 'predicted_value_7d'):
            if rule.condition in ['declining', 'increasing']:
                change = abs(trend.current_value - trend.predicted_value_7d)
                direction = "decline" if trend.current_value > trend.predicted_value_7d else "increase"
                base_description += f" (Current: {trend.current_value:.1f}, "
                base_description += f"Predicted 7-day {direction}: {change:.1f})"
            else:
                base_description += f" (Current value: {trend.current_value:.1f}, "
                base_description += f"Threshold: {rule.threshold:.1f})"
        
        if hasattr(trend, 'confidence_level'):
            confidence_desc = "high" if trend.confidence_level > 0.8 else "medium" if trend.confidence_level > 0.5 else "low"
            base_description += f" [Confidence: {confidence_desc}]"
        
        return base_description
    
    def _process_new_alert(self, alert: Alert) -> None:
        """Process a new alert (store, notify, etc.)"""
        # Add to active alerts
        self.active_alerts[alert.id] = alert
        
        # Add to history
        self.alert_history.append(alert)
        
        # Save to storage
        self._save_alerts()
        
        # Trigger callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                print(f"Error in alert callback: {e}")
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "system") -> bool:
        """Acknowledge an active alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.now()
            alert.updated_at = datetime.now()
            
            self._save_alerts()
            return True
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an active alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now()
            alert.updated_at = datetime.now()
            
            # Remove from active alerts
            del self.active_alerts[alert_id]
            
            self._save_alerts()
            return True
        return False
    
    def suppress_alert(self, alert_id: str) -> bool:
        """Suppress an active alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.SUPPRESSED
            alert.updated_at = datetime.now()
            
            self._save_alerts()
            return True
        return False
    
    def get_active_alerts(self, severity_filter: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get all active alerts, optionally filtered by severity"""
        alerts = list(self.active_alerts.values())
        
        if severity_filter:
            alerts = [a for a in alerts if a.severity == severity_filter]
        
        # Sort by severity (critical first) then by creation time
        severity_order = {
            AlertSeverity.CRITICAL: 0,
            AlertSeverity.ERROR: 1,
            AlertSeverity.WARNING: 2,
            AlertSeverity.INFO: 3
        }
        
        alerts.sort(key=lambda a: (severity_order[a.severity], a.created_at))
        return alerts
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get comprehensive alert statistics"""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        # Count alerts by time period
        recent_alerts_24h = [a for a in self.alert_history if a.created_at >= last_24h]
        recent_alerts_7d = [a for a in self.alert_history if a.created_at >= last_7d]
        
        # Count by severity
        severity_counts = {
            'critical': len([a for a in self.active_alerts.values() if a.severity == AlertSeverity.CRITICAL]),
            'error': len([a for a in self.active_alerts.values() if a.severity == AlertSeverity.ERROR]),
            'warning': len([a for a in self.active_alerts.values() if a.severity == AlertSeverity.WARNING]),
            'info': len([a for a in self.active_alerts.values() if a.severity == AlertSeverity.INFO])
        }
        
        # Count by status
        status_counts = {
            'active': len([a for a in self.active_alerts.values() if a.status == AlertStatus.ACTIVE]),
            'acknowledged': len([a for a in self.active_alerts.values() if a.status == AlertStatus.ACKNOWLEDGED]),
            'suppressed': len([a for a in self.active_alerts.values() if a.status == AlertStatus.SUPPRESSED])
        }
        
        # Most frequent alert types
        metric_counts = {}
        for alert in recent_alerts_7d:
            metric = alert.source_metric
            metric_counts[metric] = metric_counts.get(metric, 0) + 1
        
        most_frequent_metrics = sorted(
            metric_counts.items(), key=lambda x: x[1], reverse=True
        )[:5]
        
        return {
            'active_alerts_total': len(self.active_alerts),
            'alerts_last_24h': len(recent_alerts_24h),
            'alerts_last_7d': len(recent_alerts_7d),
            'alerts_total_history': len(self.alert_history),
            'severity_distribution': severity_counts,
            'status_distribution': status_counts,
            'most_frequent_metrics': most_frequent_metrics,
            'monitoring_active': self._monitoring_active,
            'enabled_rules': len([r for r in self.alert_rules if r.enabled])
        }
    
    def add_alert_callback(self, callback: Callable[[Alert], None]) -> None:
        """Add a callback function to be called when new alerts are generated"""
        self.alert_callbacks.append(callback)
    
    def remove_alert_callback(self, callback: Callable[[Alert], None]) -> bool:
        """Remove an alert callback"""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)
            return True
        return False
    
    def _load_alerts(self) -> None:
        """Load alerts from storage"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    
                    # Load active alerts
                    for alert_data in data.get('active_alerts', []):
                        alert = Alert.from_dict(alert_data)
                        self.active_alerts[alert.id] = alert
                    
                    # Load alert history
                    for alert_data in data.get('alert_history', []):
                        alert = Alert.from_dict(alert_data)
                        self.alert_history.append(alert)
        except Exception as e:
            print(f"Warning: Could not load alerts: {e}")
    
    def _save_alerts(self) -> None:
        """Save alerts to storage"""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            
            data = {
                'active_alerts': [alert.to_dict() for alert in self.active_alerts.values()],
                'alert_history': [alert.to_dict() for alert in self.alert_history[-1000:]]  # Keep last 1000
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save alerts: {e}")


class AlertManager:
    """
    Centralized alert management system with notification capabilities.
    
    Capabilities:
    - Centralized alert aggregation
    - Multi-channel notification support
    - Alert escalation procedures
    - Alert analytics and reporting
    """
    
    def __init__(self, early_warning_system: EarlyWarningSystem):
        """Initialize alert manager"""
        self.ews = early_warning_system
        self.notification_channels: Dict[str, Callable] = {}
        self.escalation_rules: List[Dict[str, Any]] = []
        
        # Register for alert callbacks
        self.ews.add_alert_callback(self._handle_new_alert)
        
        # Initialize default notification channels
        self._initialize_default_channels()
    
    def _initialize_default_channels(self) -> None:
        """Initialize default notification channels"""
        # Console notification channel
        self.add_notification_channel("console", self._console_notification)
        
        # File log notification channel
        self.add_notification_channel("file_log", self._file_log_notification)
    
    def add_notification_channel(self, name: str, handler: Callable[[Alert], None]) -> None:
        """Add a notification channel"""
        self.notification_channels[name] = handler
    
    def remove_notification_channel(self, name: str) -> bool:
        """Remove a notification channel"""
        if name in self.notification_channels:
            del self.notification_channels[name]
            return True
        return False
    
    def add_escalation_rule(self, rule: Dict[str, Any]) -> None:
        """Add an alert escalation rule"""
        self.escalation_rules.append(rule)
    
    def _handle_new_alert(self, alert: Alert) -> None:
        """Handle new alert through notification and escalation"""
        # Send notifications
        for channel_name, handler in self.notification_channels.items():
            try:
                handler(alert)
            except Exception as e:
                print(f"Error in notification channel {channel_name}: {e}")
        
        # Check escalation rules
        self._check_escalation(alert)
    
    def _check_escalation(self, alert: Alert) -> None:
        """Check if alert should be escalated"""
        for rule in self.escalation_rules:
            if self._should_escalate(alert, rule):
                self._escalate_alert(alert, rule)
    
    def _should_escalate(self, alert: Alert, rule: Dict[str, Any]) -> bool:
        """Check if alert meets escalation criteria"""
        # Check severity
        if 'min_severity' in rule:
            severity_order = ['info', 'warning', 'error', 'critical']
            alert_severity_idx = severity_order.index(alert.severity.value)
            min_severity_idx = severity_order.index(rule['min_severity'])
            if alert_severity_idx < min_severity_idx:
                return False
        
        # Check time since creation
        if 'escalate_after_minutes' in rule:
            time_elapsed = datetime.now() - alert.created_at
            if time_elapsed.total_seconds() / 60 < rule['escalate_after_minutes']:
                return False
        
        # Check if already acknowledged
        if rule.get('skip_if_acknowledged', True) and alert.status == AlertStatus.ACKNOWLEDGED:
            return False
        
        return True
    
    def _escalate_alert(self, alert: Alert, rule: Dict[str, Any]) -> None:
        """Escalate an alert according to the rule"""
        escalation_actions = rule.get('actions', [])
        
        for action in escalation_actions:
            if action == 'increase_severity':
                if alert.severity == AlertSeverity.WARNING:
                    alert.severity = AlertSeverity.ERROR
                elif alert.severity == AlertSeverity.ERROR:
                    alert.severity = AlertSeverity.CRITICAL
            elif action == 'notify_all_channels':
                # Already handled by default notification
                pass
            elif action.startswith('notify_'):
                channel_name = action[7:]  # Remove 'notify_' prefix
                if channel_name in self.notification_channels:
                    self.notification_channels[channel_name](alert)
    
    def _console_notification(self, alert: Alert) -> None:
        """Send alert notification to console"""
        severity_symbols = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.ERROR: "❌",
            AlertSeverity.CRITICAL: "🚨"
        }
        
        symbol = severity_symbols.get(alert.severity, "📢")
        
        print(f"\n{symbol} ALERT [{alert.severity.value.upper()}]: {alert.title}")
        print(f"   Description: {alert.description}")
        print(f"   Metric: {alert.source_metric} (Current: {alert.current_value:.1f})")
        print(f"   Created: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if alert.recommended_actions:
            print("   Recommended Actions:")
            for action in alert.recommended_actions[:3]:  # Show top 3 actions
                print(f"   • {action}")
        print()
    
    def _file_log_notification(self, alert: Alert) -> None:
        """Send alert notification to log file"""
        log_path = os.path.join(
            os.path.dirname(self.ews.storage_path), 'alert_notifications.log'
        )
        
        try:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            
            log_entry = {
                'timestamp': alert.created_at.isoformat(),
                'alert_id': alert.id,
                'severity': alert.severity.value,
                'title': alert.title,
                'description': alert.description,
                'metric': alert.source_metric,
                'current_value': alert.current_value,
                'confidence': alert.confidence_level
            }
            
            with open(log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            print(f"Warning: Could not write to alert log: {e}")
    
    def get_notification_summary(self) -> Dict[str, Any]:
        """Get summary of notification system status"""
        return {
            'active_channels': list(self.notification_channels.keys()),
            'escalation_rules': len(self.escalation_rules),
            'monitoring_active': self.ews._monitoring_active,
            'total_alerts_today': len([
                a for a in self.ews.alert_history 
                if a.created_at.date() == datetime.now().date()
            ])
        }
    
    def test_notifications(self) -> None:
        """Test all notification channels with a sample alert"""
        test_alert = Alert(
            id="test_alert",
            title="Test Alert",
            description="This is a test alert to verify notification channels",
            severity=AlertSeverity.INFO,
            status=AlertStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            source_metric="test_metric",
            current_value=100.0,
            threshold_value=80.0,
            predicted_impact="No impact - this is a test",
            recommended_actions=["Ignore this test alert"],
            confidence_level=1.0
        )
        
        print("Testing notification channels:")
        for name, handler in self.notification_channels.items():
            try:
                print(f"  Testing {name}...")
                handler(test_alert)
                print(f"  ✓ {name} test successful")
            except Exception as e:
                print(f"  ✗ {name} test failed: {e}")