#!/usr/bin/env python3
"""
Pipeline monitoring script for AppMagician pipeline.
Monitors pipeline health, tracks metrics, and generates reports.
"""

import os
import sys
import json
import sqlite3
import argparse
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import re


@dataclass
class PipelineMetrics:
    """Data class for pipeline metrics."""
    timestamp: str
    app_name: str
    pipeline_id: str
    total_duration: float
    stages: Dict[str, Dict[str, Any]]
    test_coverage: float
    code_quality_score: float
    build_success: bool
    errors_count: int
    warnings_count: int
    success_rate: float


class PipelineMonitor:
    def __init__(self, db_path: str = "pipeline_metrics.db"):
        self.db_path = Path(db_path)
        self.metrics_history: List[PipelineMetrics] = []
        self.current_metrics: Optional[PipelineMetrics] = None
        self.alert_thresholds = {
            'success_rate': 0.8,  # 80% minimum success rate
            'build_time': 1800,    # 30 minutes maximum build time
            'test_coverage': 70.0, # 70% minimum test coverage
            'error_rate': 0.1      # 10% maximum error rate
        }
        
    def initialize_database(self):
        """Initialize SQLite database for storing metrics."""
        try:
            # Ensure directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pipeline_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    app_name TEXT NOT NULL,
                    pipeline_id TEXT NOT NULL,
                    total_duration REAL NOT NULL,
                    stages TEXT NOT NULL,
                    test_coverage REAL NOT NULL,
                    code_quality_score REAL NOT NULL,
                    build_success BOOLEAN NOT NULL,
                    errors_count INTEGER NOT NULL,
                    warnings_count INTEGER NOT NULL,
                    success_rate REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pipeline_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            print(f"✅ Database initialized: {self.db_path}")
            
        except Exception as e:
            print(f"❌ Failed to initialize database: {e}")
            return False
        
        return True
    
    def collect_current_metrics(self, app_root: str) -> bool:
        """Collect current pipeline metrics."""
        print("📊 Collecting current pipeline metrics...")
        
        app_path = Path(app_root)
        if not app_path.exists():
            print(f"❌ App directory does not exist: {app_root}")
            return False
        
        # Change to app directory
        os.chdir(app_path)
        
        # Generate pipeline ID
        pipeline_id = f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Collect metrics
        start_time = time.time()
        
        try:
            # Get app name
            app_name = app_path.name
            
            # Run flutter analyze to get code quality metrics
            analyze_result = self.run_flutter_analyze()
            
            # Run flutter test to get test coverage
            test_result = self.run_flutter_test()
            
            # Check build success
            build_result = self.run_flutter_build()
            
            # Calculate metrics
            total_duration = time.time() - start_time
            
            # Parse analyze results
            errors_count = len(re.findall(r"error •", analyze_result.get('output', '')))
            warnings_count = len(re.findall(r"warning •", analyze_result.get('output', '')))
            
            # Calculate code quality score (0-100)
            code_quality_score = self.calculate_code_quality_score(
                errors_count, warnings_count, analyze_result.get('returncode', 1)
            )
            
            # Get test coverage
            test_coverage = self.extract_test_coverage(test_result.get('output', ''))
            
            # Calculate success rate
            success_rate = self.calculate_success_rate(
                analyze_result.get('returncode', 1),
                test_result.get('returncode', 1),
                build_result.get('returncode', 1)
            )
            
            # Create metrics object
            self.current_metrics = PipelineMetrics(
                timestamp=datetime.now().isoformat(),
                app_name=app_name,
                pipeline_id=pipeline_id,
                total_duration=total_duration,
                stages={
                    'analyze': analyze_result,
                    'test': test_result,
                    'build': build_result
                },
                test_coverage=test_coverage,
                code_quality_score=code_quality_score,
                build_success=build_result.get('returncode', 1) == 0,
                errors_count=errors_count,
                warnings_count=warnings_count,
                success_rate=success_rate
            )
            
            print(f"✅ Metrics collected for {app_name}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to collect metrics: {e}")
            return False
    
    def run_flutter_analyze(self) -> Dict[str, Any]:
        """Run flutter analyze and return results."""
        try:
            result = subprocess.run(
                ['flutter', 'analyze'],
                capture_output=True,
                text=True,
                timeout=120
            )
            return {
                'returncode': result.returncode,
                'output': result.stdout + result.stderr,
                'duration': 0  # Could be measured if needed
            }
        except subprocess.TimeoutExpired:
            return {
                'returncode': 124,
                'output': 'Flutter analyze timed out',
                'duration': 120
            }
        except Exception as e:
            return {
                'returncode': 1,
                'output': f'Flutter analyze failed: {e}',
                'duration': 0
            }
    
    def run_flutter_test(self) -> Dict[str, Any]:
        """Run flutter test and return results."""
        try:
            result = subprocess.run(
                ['flutter', 'test', '--coverage'],
                capture_output=True,
                text=True,
                timeout=300
            )
            return {
                'returncode': result.returncode,
                'output': result.stdout + result.stderr,
                'duration': 0  # Could be measured if needed
            }
        except subprocess.TimeoutExpired:
            return {
                'returncode': 124,
                'output': 'Flutter test timed out',
                'duration': 300
            }
        except Exception as e:
            return {
                'returncode': 1,
                'output': f'Flutter test failed: {e}',
                'duration': 0
            }
    
    def run_flutter_build(self) -> Dict[str, Any]:
        """Run flutter build and return results."""
        try:
            result = subprocess.run(
                ['flutter', 'build', 'ios', '--no-codesign'],
                capture_output=True,
                text=True,
                timeout=600
            )
            return {
                'returncode': result.returncode,
                'output': result.stdout + result.stderr,
                'duration': 0  # Could be measured if needed
            }
        except subprocess.TimeoutExpired:
            return {
                'returncode': 124,
                'output': 'Flutter build timed out',
                'duration': 600
            }
        except Exception as e:
            return {
                'returncode': 1,
                'output': f'Flutter build failed: {e}',
                'duration': 0
            }
    
    def calculate_code_quality_score(self, errors: int, warnings: int, returncode: int) -> float:
        """Calculate code quality score (0-100)."""
        if returncode == 0:
            # No errors, score based on warnings
            if warnings == 0:
                return 100.0
            elif warnings <= 5:
                return 95.0
            elif warnings <= 10:
                return 90.0
            elif warnings <= 20:
                return 80.0
            else:
                return 70.0
        else:
            # Has errors, score based on error count
            if errors == 0:
                return 80.0  # Warnings only
            elif errors <= 2:
                return 60.0
            elif errors <= 5:
                return 40.0
            elif errors <= 10:
                return 20.0
            else:
                return 0.0
    
    def extract_test_coverage(self, test_output: str) -> float:
        """Extract test coverage percentage from test output."""
        # Look for coverage percentage in output
        coverage_match = re.search(r'(\d+(?:\.\d+)?)%\s+coverage', test_output)
        if coverage_match:
            return float(coverage_match.group(1))
        
        # Look for coverage in lcov.info file
        coverage_file = Path('coverage/lcov.info')
        if coverage_file.exists():
            try:
                with open(coverage_file, 'r') as f:
                    content = f.read()
                
                # Extract coverage from lcov format
                lines_match = re.search(r'LF:(\d+)\s+LH:(\d+)', content)
                if lines_match:
                    total_lines = int(lines_match.group(1))
                    covered_lines = int(lines_match.group(2))
                    if total_lines > 0:
                        return (covered_lines / total_lines) * 100
            except Exception:
                pass
        
        return 0.0
    
    def calculate_success_rate(self, analyze_rc: int, test_rc: int, build_rc: int) -> float:
        """Calculate overall success rate."""
        total_steps = 3
        successful_steps = 0
        
        if analyze_rc == 0:
            successful_steps += 1
        if test_rc == 0:
            successful_steps += 1
        if build_rc == 0:
            successful_steps += 1
        
        return (successful_steps / total_steps) * 100
    
    def save_metrics(self) -> bool:
        """Save current metrics to database."""
        if not self.current_metrics:
            print("❌ No metrics to save")
            return False
        
        try:
            # Use absolute path to ensure we're connecting to the right database
            db_path = self.db_path.resolve()
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Insert metrics
            cursor.execute('''
                INSERT INTO pipeline_metrics (
                    timestamp, app_name, pipeline_id, total_duration,
                    stages, test_coverage, code_quality_score,
                    build_success, errors_count, warnings_count, success_rate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.current_metrics.timestamp,
                self.current_metrics.app_name,
                self.current_metrics.pipeline_id,
                self.current_metrics.total_duration,
                json.dumps(self.current_metrics.stages),
                self.current_metrics.test_coverage,
                self.current_metrics.code_quality_score,
                self.current_metrics.build_success,
                self.current_metrics.errors_count,
                self.current_metrics.warnings_count,
                self.current_metrics.success_rate
            ))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Metrics saved to database")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save metrics: {e}")
            return False
    
    def load_metrics_history(self, days: int = 30) -> List[PipelineMetrics]:
        """Load metrics history from database."""
        try:
            # Use absolute path to ensure we're connecting to the right database
            db_path = self.db_path.resolve()
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Get metrics from last N days
            cutoff_date = datetime.now() - timedelta(days=days)
            
            cursor.execute('''
                SELECT * FROM pipeline_metrics 
                WHERE created_at >= ? 
                ORDER BY created_at DESC
            ''', (cutoff_date.isoformat(),))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convert to PipelineMetrics objects
            metrics_list = []
            for row in rows:
                metrics = PipelineMetrics(
                    timestamp=row[1],
                    app_name=row[2],
                    pipeline_id=row[3],
                    total_duration=row[4],
                    stages=json.loads(row[5]),
                    test_coverage=row[6],
                    code_quality_score=row[7],
                    build_success=bool(row[8]),
                    errors_count=row[9],
                    warnings_count=row[10],
                    success_rate=row[11]
                )
                metrics_list.append(metrics)
            
            self.metrics_history = metrics_list
            return metrics_list
            
        except Exception as e:
            print(f"❌ Failed to load metrics history: {e}")
            return []
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check for pipeline health alerts."""
        if not self.current_metrics:
            return []
        
        alerts = []
        
        # Check success rate
        if self.current_metrics.success_rate < self.alert_thresholds['success_rate'] * 100:
            alerts.append({
                'type': 'low_success_rate',
                'message': f'Success rate {self.current_metrics.success_rate:.1f}% is below threshold {self.alert_thresholds["success_rate"] * 100:.1f}%',
                'severity': 'warning'
            })
        
        # Check build time
        if self.current_metrics.total_duration > self.alert_thresholds['build_time']:
            alerts.append({
                'type': 'slow_build',
                'message': f'Build time {self.current_metrics.total_duration:.1f}s exceeds threshold {self.alert_thresholds["build_time"]}s',
                'severity': 'warning'
            })
        
        # Check test coverage
        if self.current_metrics.test_coverage < self.alert_thresholds['test_coverage']:
            alerts.append({
                'type': 'low_coverage',
                'message': f'Test coverage {self.current_metrics.test_coverage:.1f}% is below threshold {self.alert_thresholds["test_coverage"]:.1f}%',
                'severity': 'warning'
            })
        
        # Check error rate
        total_issues = self.current_metrics.errors_count + self.current_metrics.warnings_count
        if total_issues > 0:
            error_rate = self.current_metrics.errors_count / total_issues
            if error_rate > self.alert_thresholds['error_rate']:
                alerts.append({
                    'type': 'high_error_rate',
                    'message': f'Error rate {error_rate:.1%} exceeds threshold {self.alert_thresholds["error_rate"]:.1%}',
                    'severity': 'error'
                })
        
        # Save alerts to database
        self.save_alerts(alerts)
        
        return alerts
    
    def save_alerts(self, alerts: List[Dict[str, Any]]):
        """Save alerts to database."""
        if not alerts:
            return
        
        try:
            # Use absolute path to ensure we're connecting to the right database
            db_path = self.db_path.resolve()
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            for alert in alerts:
                cursor.execute('''
                    INSERT INTO pipeline_alerts (
                        timestamp, alert_type, message, severity
                    ) VALUES (?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    alert['type'],
                    alert['message'],
                    alert['severity']
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Failed to save alerts: {e}")
    
    def generate_health_report(self) -> str:
        """Generate comprehensive pipeline health report."""
        if not self.current_metrics:
            return "❌ No metrics available for report generation"
        
        report = []
        report.append("=" * 80)
        report.append("📊 PIPELINE HEALTH REPORT")
        report.append("=" * 80)
        
        # Current metrics
        report.append(f"\n🕐 Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"📱 App: {self.current_metrics.app_name}")
        report.append(f"🆔 Pipeline ID: {self.current_metrics.pipeline_id}")
        
        # Overall health score
        health_score = self.calculate_health_score()
        report.append(f"\n🏥 OVERALL HEALTH SCORE: {health_score:.1f}/100")
        
        # Current metrics
        report.append(f"\n📈 CURRENT METRICS:")
        report.append(f"  ⏱️  Build Duration: {self.current_metrics.total_duration:.1f}s")
        report.append(f"  ✅ Success Rate: {self.current_metrics.success_rate:.1f}%")
        report.append(f"  🧪 Test Coverage: {self.current_metrics.test_coverage:.1f}%")
        report.append(f"  🔍 Code Quality: {self.current_metrics.code_quality_score:.1f}/100")
        report.append(f"  ❌ Errors: {self.current_metrics.errors_count}")
        report.append(f"  ⚠️  Warnings: {self.current_metrics.warnings_count}")
        report.append(f"  🔨 Build Success: {'✅' if self.current_metrics.build_success else '❌'}")
        
        # Historical trends
        if self.metrics_history:
            report.append(f"\n📊 HISTORICAL TRENDS (Last {len(self.metrics_history)} runs):")
            
            # Calculate averages
            avg_duration = sum(m.total_duration for m in self.metrics_history) / len(self.metrics_history)
            avg_success_rate = sum(m.success_rate for m in self.metrics_history) / len(self.metrics_history)
            avg_coverage = sum(m.test_coverage for m in self.metrics_history) / len(self.metrics_history)
            avg_quality = sum(m.code_quality_score for m in self.metrics_history) / len(self.metrics_history)
            
            report.append(f"  ⏱️  Avg Build Duration: {avg_duration:.1f}s")
            report.append(f"  ✅ Avg Success Rate: {avg_success_rate:.1f}%")
            report.append(f"  🧪 Avg Test Coverage: {avg_coverage:.1f}%")
            report.append(f"  🔍 Avg Code Quality: {avg_quality:.1f}/100")
            
            # Trend analysis
            if len(self.metrics_history) >= 2:
                recent = self.metrics_history[0]
                previous = self.metrics_history[1]
                
                report.append(f"\n📈 TREND ANALYSIS:")
                duration_trend = "📈" if recent.total_duration > previous.total_duration else "📉"
                success_trend = "📈" if recent.success_rate > previous.success_rate else "📉"
                coverage_trend = "📈" if recent.test_coverage > previous.test_coverage else "📉"
                quality_trend = "📈" if recent.code_quality_score > previous.code_quality_score else "📉"
                
                report.append(f"  ⏱️  Build Duration: {duration_trend} {abs(recent.total_duration - previous.total_duration):.1f}s")
                report.append(f"  ✅ Success Rate: {success_trend} {abs(recent.success_rate - previous.success_rate):.1f}%")
                report.append(f"  🧪 Test Coverage: {coverage_trend} {abs(recent.test_coverage - previous.test_coverage):.1f}%")
                report.append(f"  🔍 Code Quality: {quality_trend} {abs(recent.code_quality_score - previous.code_quality_score):.1f}")
        
        # Alerts
        alerts = self.check_alerts()
        if alerts:
            report.append(f"\n🚨 ACTIVE ALERTS ({len(alerts)}):")
            for alert in alerts:
                severity_icon = "🔴" if alert['severity'] == 'error' else "🟡"
                report.append(f"  {severity_icon} {alert['message']}")
        else:
            report.append(f"\n✅ NO ACTIVE ALERTS")
        
        # Recommendations
        report.append(f"\n💡 RECOMMENDATIONS:")
        recommendations = self.generate_recommendations()
        for rec in recommendations:
            report.append(f"  • {rec}")
        
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def calculate_health_score(self) -> float:
        """Calculate overall health score (0-100)."""
        if not self.current_metrics:
            return 0.0
        
        # Weighted score calculation
        weights = {
            'success_rate': 0.3,
            'test_coverage': 0.25,
            'code_quality': 0.25,
            'build_time': 0.1,
            'error_rate': 0.1
        }
        
        # Normalize metrics to 0-100 scale
        success_score = self.current_metrics.success_rate
        coverage_score = self.current_metrics.test_coverage
        quality_score = self.current_metrics.code_quality_score
        
        # Build time score (inverse relationship)
        build_time_score = max(0, 100 - (self.current_metrics.total_duration / 60) * 10)
        
        # Error rate score (inverse relationship)
        total_issues = self.current_metrics.errors_count + self.current_metrics.warnings_count
        error_rate_score = 100 if total_issues == 0 else max(0, 100 - (self.current_metrics.errors_count / max(1, total_issues)) * 100)
        
        # Calculate weighted average
        health_score = (
            success_score * weights['success_rate'] +
            coverage_score * weights['test_coverage'] +
            quality_score * weights['code_quality'] +
            build_time_score * weights['build_time'] +
            error_rate_score * weights['error_rate']
        )
        
        return health_score
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on current metrics."""
        recommendations = []
        
        if not self.current_metrics:
            return recommendations
        
        # Success rate recommendations
        if self.current_metrics.success_rate < 90:
            recommendations.append("Improve pipeline reliability by fixing failing stages")
        
        # Test coverage recommendations
        if self.current_metrics.test_coverage < 80:
            recommendations.append("Increase test coverage by adding more unit and integration tests")
        
        # Code quality recommendations
        if self.current_metrics.code_quality_score < 80:
            recommendations.append("Improve code quality by addressing analyze warnings and errors")
        
        # Build time recommendations
        if self.current_metrics.total_duration > 600:  # 10 minutes
            recommendations.append("Optimize build performance by reducing dependencies or parallelizing tasks")
        
        # Error rate recommendations
        if self.current_metrics.errors_count > 5:
            recommendations.append("Focus on reducing compilation errors to improve build stability")
        
        # General recommendations
        if not recommendations:
            recommendations.append("Pipeline is performing well - maintain current practices")
        
        return recommendations
    
    def generate_dashboard(self) -> str:
        """Generate dashboard-like output for pipeline status."""
        if not self.current_metrics:
            return "❌ No metrics available for dashboard"
        
        dashboard = []
        dashboard.append("┌" + "─" * 78 + "┐")
        dashboard.append("│" + " " * 25 + "🚀 PIPELINE DASHBOARD" + " " * 25 + "│")
        dashboard.append("├" + "─" * 78 + "┤")
        
        # Health score with visual indicator
        health_score = self.calculate_health_score()
        health_bar = self.create_progress_bar(health_score, 100, 20)
        dashboard.append(f"│ 🏥 Health Score: {health_score:5.1f}/100 {health_bar} │")
        
        # Success rate
        success_bar = self.create_progress_bar(self.current_metrics.success_rate, 100, 20)
        dashboard.append(f"│ ✅ Success Rate: {self.current_metrics.success_rate:5.1f}% {success_bar} │")
        
        # Test coverage
        coverage_bar = self.create_progress_bar(self.current_metrics.test_coverage, 100, 20)
        dashboard.append(f"│ 🧪 Test Coverage: {self.current_metrics.test_coverage:5.1f}% {coverage_bar} │")
        
        # Code quality
        quality_bar = self.create_progress_bar(self.current_metrics.code_quality_score, 100, 20)
        dashboard.append(f"│ 🔍 Code Quality: {self.current_metrics.code_quality_score:5.1f}/100 {quality_bar} │")
        
        dashboard.append("├" + "─" * 78 + "┤")
        
        # Build info
        build_status = "✅ SUCCESS" if self.current_metrics.build_success else "❌ FAILED"
        dashboard.append(f"│ 🔨 Build Status: {build_status:<20} ⏱️  Duration: {self.current_metrics.total_duration:6.1f}s │")
        
        # Issues
        dashboard.append(f"│ ❌ Errors: {self.current_metrics.errors_count:<15} ⚠️  Warnings: {self.current_metrics.warnings_count:<15} │")
        
        dashboard.append("├" + "─" * 78 + "┤")
        
        # App info
        dashboard.append(f"│ 📱 App: {self.current_metrics.app_name:<30} 🆔 ID: {self.current_metrics.pipeline_id:<25} │")
        dashboard.append(f"│ 🕐 Timestamp: {self.current_metrics.timestamp:<65} │")
        
        dashboard.append("└" + "─" * 78 + "┘")
        
        return "\n".join(dashboard)
    
    def create_progress_bar(self, value: float, max_value: float, width: int) -> str:
        """Create a visual progress bar."""
        if max_value == 0:
            return " " * width
        
        percentage = value / max_value
        filled = int(percentage * width)
        bar = "█" * filled + "░" * (width - filled)
        
        return f"[{bar}]"
    
    def export_metrics(self, format: str = 'json', output_file: str = None) -> bool:
        """Export metrics to file."""
        if not self.current_metrics:
            print("❌ No metrics to export")
            return False
        
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"pipeline_metrics_{timestamp}.{format}"
        
        try:
            if format.lower() == 'json':
                with open(output_file, 'w') as f:
                    json.dump(asdict(self.current_metrics), f, indent=2)
            elif format.lower() == 'csv':
                import csv
                with open(output_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['timestamp', 'app_name', 'pipeline_id', 'total_duration', 
                                   'test_coverage', 'code_quality_score', 'build_success', 
                                   'errors_count', 'warnings_count', 'success_rate'])
                    writer.writerow([
                        self.current_metrics.timestamp,
                        self.current_metrics.app_name,
                        self.current_metrics.pipeline_id,
                        self.current_metrics.total_duration,
                        self.current_metrics.test_coverage,
                        self.current_metrics.code_quality_score,
                        self.current_metrics.build_success,
                        self.current_metrics.errors_count,
                        self.current_metrics.warnings_count,
                        self.current_metrics.success_rate
                    ])
            else:
                print(f"❌ Unsupported format: {format}")
                return False
            
            print(f"✅ Metrics exported to: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to export metrics: {e}")
            return False


def main():
    """Main entry point for the pipeline monitor script."""
    parser = argparse.ArgumentParser(
        description="Monitor pipeline health and generate reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
    # Monitor current pipeline
    python3 Python/pipeline_monitor.py --app-root /path/to/app
    
    # Generate health report
    python3 Python/pipeline_monitor.py --report --app-root /path/to/app
    
    # Show dashboard
    python3 Python/pipeline_monitor.py --dashboard --app-root /path/to/app
    
    # Export metrics
    python3 Python/pipeline_monitor.py --export json --app-root /path/to/app
    
    # Load history and show trends
    python3 Python/pipeline_monitor.py --history 7 --app-root /path/to/app

PIPELINE MONITORING FEATURES:
    ✅ Track success/failure rates of each pipeline step
    ✅ Monitor build times and identify bottlenecks
    ✅ Track test coverage trends over time
    ✅ Monitor code quality metrics (analyze warnings, errors)
    ✅ Generate pipeline health reports
    ✅ Alert on pipeline degradation
    ✅ Store metrics in SQLite database for historical analysis
    ✅ Provide dashboard-like output for pipeline status
    ✅ Export metrics to JSON/CSV formats
    ✅ Generate recommendations for improvement

EXIT CODES:
    0    Pipeline monitoring successful
    1    Pipeline monitoring failed
        """
    )
    
    parser.add_argument(
        '--app-root',
        help='Path to the app root directory (default: $HOME/AppMagician/$APP_DIR)'
    )
    
    parser.add_argument(
        '--db-path',
        default='pipeline_metrics.db',
        help='Path to SQLite database file (default: pipeline_metrics.db)'
    )
    
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate comprehensive health report'
    )
    
    parser.add_argument(
        '--dashboard',
        action='store_true',
        help='Show dashboard-like output'
    )
    
    parser.add_argument(
        '--export',
        choices=['json', 'csv'],
        help='Export metrics to file'
    )
    
    parser.add_argument(
        '--history',
        type=int,
        default=30,
        help='Load metrics history for N days (default: 30)'
    )
    
    parser.add_argument(
        '--init-db',
        action='store_true',
        help='Initialize database only'
    )
    
    args = parser.parse_args()
    
    # Get app directory from environment or use default
    app_dir = os.environ.get('APP_DIR', 'test_todo_app')
    if args.app_root:
        app_root = args.app_root
    else:
        app_root = os.environ.get('APP_ROOT', f"{os.environ.get('HOME', '/tmp')}/AppMagician/{app_dir}")
    
    # Create monitor instance
    monitor = PipelineMonitor(args.db_path)
    
    # Initialize database
    if not monitor.initialize_database():
        sys.exit(1)
    
    # If only initializing database, exit
    if args.init_db:
        print("✅ Database initialized successfully")
        sys.exit(0)
    
    # Collect current metrics
    if not monitor.collect_current_metrics(app_root):
        print("❌ Failed to collect metrics")
        sys.exit(1)
    
    # Save metrics to database
    monitor.save_metrics()
    
    # Load metrics history
    monitor.load_metrics_history(args.history)
    
    # Generate outputs based on arguments
    if args.report:
        print(monitor.generate_health_report())
    
    if args.dashboard:
        print(monitor.generate_dashboard())
    
    if args.export:
        monitor.export_metrics(args.export)
    
    # If no specific output requested, show basic status
    if not any([args.report, args.dashboard, args.export]):
        print("📊 Pipeline monitoring completed successfully")
        print(f"📱 App: {monitor.current_metrics.app_name}")
        print(f"✅ Success Rate: {monitor.current_metrics.success_rate:.1f}%")
        print(f"🧪 Test Coverage: {monitor.current_metrics.test_coverage:.1f}%")
        print(f"🔍 Code Quality: {monitor.current_metrics.code_quality_score:.1f}/100")
        print(f"⏱️  Build Duration: {monitor.current_metrics.total_duration:.1f}s")
        
        # Show alerts if any
        alerts = monitor.check_alerts()
        if alerts:
            print(f"\n🚨 Active Alerts: {len(alerts)}")
            for alert in alerts:
                severity_icon = "🔴" if alert['severity'] == 'error' else "🟡"
                print(f"  {severity_icon} {alert['message']}")
    
    print(f"\n✅ Pipeline monitoring completed successfully")
    sys.exit(0)


if __name__ == "__main__":
    main()
