"""
Report generation classes for molecular analysis.

Provides comprehensive reporting capabilities including HTML, PDF, 
and JSON reports with embedded visualizations and statistical summaries.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import json
import base64
from io import BytesIO
import plotly.graph_objects as go
from plotly.io import to_html, to_json

from ..models.base import BaseRenderer
from ..models.models import PropertyData, AnalysisResult, MoleculeData
from ..models.exceptions import ValidationError, FileIOError
from .renderers import Chart2DRenderer, Molecule3DRenderer


class ReportGenerator(BaseRenderer[Union[AnalysisResult, List[AnalysisResult]]]):
    """
    Comprehensive report generator for molecular analysis results.
    
    Supports multiple output formats including HTML, JSON, and structured
    data exports with embedded visualizations and statistical summaries.
    """
    
    def __init__(self, backend: str = "html"):
        super().__init__(backend)
        self.chart_renderer = Chart2DRenderer()
        self.mol_renderer = Molecule3DRenderer()
        self._template_cache = {}
    
    @property
    def renderer_name(self) -> str:
        return "ReportGenerator"
    
    @property
    def supported_backends(self) -> List[str]:
        return ["html", "json", "markdown", "csv"]
    
    def _render_content(self, data: Union[AnalysisResult, List[AnalysisResult]], **kwargs) -> str:
        """
        Generate report based on analysis results.
        
        Args:
            data: Single result or list of analysis results
            **kwargs: Report configuration including:
                - title: str
                - include_visualizations: bool
                - include_statistics: bool
                - include_molecule_structure: bool
                - template: str (custom template path)
                - export_path: str (file output path)
        
        Returns:
            Generated report as string
        """
        # Prepare report data
        if isinstance(data, AnalysisResult):
            results = [data]
        else:
            results = data
        
        # Generate report based on backend
        if self.backend == "html":
            return self._generate_html_report(results, **kwargs)
        elif self.backend == "json":
            return self._generate_json_report(results, **kwargs)
        elif self.backend == "markdown":
            return self._generate_markdown_report(results, **kwargs)
        elif self.backend == "csv":
            return self._generate_csv_report(results, **kwargs)
        else:
            raise ValidationError(f"Unsupported report backend: {self.backend}")
    
    def _generate_html_report(self, results: List[AnalysisResult], **kwargs) -> str:
        """Generate comprehensive HTML report."""
        title = kwargs.get('title', 'Molecular Analysis Report')
        include_vis = kwargs.get('include_visualizations', True)
        include_stats = kwargs.get('include_statistics', True)
        include_structure = kwargs.get('include_molecule_structure', True)
        
        # Start HTML structure
        html_parts = [
            self._get_html_header(title),
            self._get_report_summary(results),
        ]
        
        # Add individual molecule sections
        for i, result in enumerate(results):
            html_parts.append(self._get_molecule_section(result, i, include_vis, include_structure))
        
        # Add statistical summary if multiple molecules
        if len(results) > 1 and include_stats:
            html_parts.append(self._get_statistical_summary(results))
        
        # Add footer
        html_parts.append(self._get_html_footer())
        
        return '\n'.join(html_parts)
    
    def _get_html_header(self, title: str) -> str:
        """Generate HTML header with CSS styling."""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .summary {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .molecule-section {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .properties-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .properties-table th, .properties-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        .properties-table th {{
            background-color: #f8f9fa;
            font-weight: 600;
        }}
        .properties-table tr:hover {{
            background-color: #f8f9fa;
        }}
        .error {{
            color: #d32f2f;
            font-weight: bold;
        }}
        .warning {{
            color: #f57c00;
            font-weight: bold;
        }}
        .success {{
            color: #388e3c;
            font-weight: bold;
        }}
        .visualization {{
            margin: 20px 0;
            text-align: center;
        }}
        .footer {{
            text-align: center;
            margin-top: 50px;
            padding: 20px;
            color: #666;
            border-top: 1px solid #ddd;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
"""
    
    def _get_report_summary(self, results: List[AnalysisResult]) -> str:
        """Generate summary section of the report."""
        total_molecules = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total_molecules - successful
        
        return f"""
    <div class="summary">
        <h2>Analysis Summary</h2>
        <table class="properties-table">
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Total Molecules Analyzed</td><td>{total_molecules}</td></tr>
            <tr><td>Successful Analyses</td><td class="success">{successful}</td></tr>
            <tr><td>Failed Analyses</td><td class="error">{failed}</td></tr>
            <tr><td>Success Rate</td><td>{(successful/total_molecules)*100:.1f}%</td></tr>
        </table>
    </div>
"""
    
    def _get_molecule_section(self, result: AnalysisResult, index: int, 
                            include_vis: bool, include_structure: bool) -> str:
        """Generate HTML section for individual molecule."""
        molecule = result.molecule
        properties = result.properties
        
        # Molecule header
        mol_name = molecule.name or f"Molecule {index + 1}"
        status_class = "success" if result.success else "error"
        status_text = "✓ Success" if result.success else "✗ Failed"
        
        html = f"""
    <div class="molecule-section">
        <h2>{mol_name} <span class="{status_class}">({status_text})</span></h2>
        <p><strong>SMILES:</strong> <code>{molecule.smiles}</code></p>
"""
        
        # Add 3D structure if requested and successful
        if include_structure and result.success:
            try:
                fig_3d = self.mol_renderer.render(molecule, 
                                                title=f"3D Structure - {mol_name}",
                                                width=600, height=400)
                plot_html = to_html(fig_3d, include_plotlyjs='cdn', div_id=f"mol3d_{index}")
                html += f"""
        <div class="visualization">
            <h3>3D Molecular Structure</h3>
            {plot_html}
        </div>
"""
            except Exception:
                html += "<p><em>3D structure visualization not available</em></p>"
        
        # Add properties table
        if properties and properties.properties:
            html += """
        <h3>Molecular Properties</h3>
        <table class="properties-table">
            <tr><th>Property</th><th>Value</th><th>Unit</th></tr>
"""
            for prop_name, prop_value in properties.properties.items():
                # Format value and determine unit
                if isinstance(prop_value, float):
                    formatted_value = f"{prop_value:.3f}"
                elif isinstance(prop_value, (int, str)):
                    formatted_value = str(prop_value)
                else:
                    formatted_value = str(prop_value)
                
                # Determine unit based on property name
                unit = self._get_property_unit(prop_name)
                
                html += f"<tr><td>{prop_name}</td><td>{formatted_value}</td><td>{unit}</td></tr>"
            
            html += "</table>"
        
        # Add property visualizations if requested
        if include_vis and properties and properties.properties:
            try:
                # Create bar chart of properties
                fig_bar = self.chart_renderer.render(
                    properties,
                    chart_type='bar',
                    title=f"Properties Overview - {mol_name}",
                    width=800, height=400
                )
                plot_html = to_html(fig_bar, include_plotlyjs='cdn', div_id=f"props_{index}")
                html += f"""
        <div class="visualization">
            <h3>Properties Overview</h3>
            {plot_html}
        </div>
"""
            except Exception:
                html += "<p><em>Property visualization not available</em></p>"
        
        # Add errors and warnings
        if result.errors:
            html += """
        <h3>Errors</h3>
        <ul>
"""
            for error in result.errors:
                html += f"<li class='error'>{error}</li>"
            html += "</ul>"
        
        if result.warnings:
            html += """
        <h3>Warnings</h3>
        <ul>
"""
            for warning in result.warnings:
                html += f"<li class='warning'>{warning}</li>"
            html += "</ul>"
        
        html += "    </div>"
        return html
    
    def _get_statistical_summary(self, results: List[AnalysisResult]) -> str:
        """Generate statistical summary for multiple molecules."""
        # Extract all numerical properties
        all_properties = {}
        for result in results:
            if result.success and result.properties:
                for prop_name, prop_value in result.properties.properties.items():
                    if isinstance(prop_value, (int, float)):
                        if prop_name not in all_properties:
                            all_properties[prop_name] = []
                        all_properties[prop_name].append(prop_value)
        
        if not all_properties:
            return "<p><em>No numerical properties available for statistical analysis</em></p>"
        
        html = """
    <div class="molecule-section">
        <h2>Statistical Summary</h2>
        <table class="properties-table">
            <tr><th>Property</th><th>Count</th><th>Mean</th><th>Std Dev</th><th>Min</th><th>Max</th></tr>
"""
        
        for prop_name, values in all_properties.items():
            if len(values) > 0:
                import statistics
                mean_val = statistics.mean(values)
                std_val = statistics.stdev(values) if len(values) > 1 else 0
                min_val = min(values)
                max_val = max(values)
                
                html += f"""
            <tr>
                <td>{prop_name}</td>
                <td>{len(values)}</td>
                <td>{mean_val:.3f}</td>
                <td>{std_val:.3f}</td>
                <td>{min_val:.3f}</td>
                <td>{max_val:.3f}</td>
            </tr>
"""
        
        html += """
        </table>
    </div>
"""
        
        # Add correlation matrix if enough properties
        if len(all_properties) >= 2:
            try:
                fig_corr = self.chart_renderer.render(
                    all_properties,
                    chart_type='correlation',
                    title="Property Correlation Matrix",
                    width=800, height=600
                )
                plot_html = to_html(fig_corr, include_plotlyjs='cdn', div_id="correlation")
                html += f"""
        <div class="visualization">
            <h3>Property Correlations</h3>
            {plot_html}
        </div>
"""
            except Exception:
                pass
        
        return html
    
    def _get_html_footer(self) -> str:
        """Generate HTML footer."""
        return """
    <div class="footer">
        <p>Report generated by Molecular Analyzer</p>
        <p>For more information, visit our documentation</p>
    </div>
</body>
</html>
"""
    
    def _generate_json_report(self, results: List[AnalysisResult], **kwargs) -> str:
        """Generate JSON report."""
        report_data = {
            'metadata': {
                'title': kwargs.get('title', 'Molecular Analysis Report'),
                'generated_at': datetime.now().isoformat(),
                'total_molecules': len(results),
                'successful_analyses': sum(1 for r in results if r.success)
            },
            'results': []
        }
        
        for result in results:
            result_data = {
                'molecule': {
                    'smiles': result.molecule.smiles,
                    'name': result.molecule.name,
                    'source': result.molecule.source
                },
                'success': result.success,
                'properties': result.properties.properties if result.properties else {},
                'errors': result.errors,
                'warnings': result.warnings,
                'calculation_metadata': result.calculation_metadata
            }
            report_data['results'].append(result_data)
        
        return json.dumps(report_data, indent=2, default=str)
    
    def _generate_markdown_report(self, results: List[AnalysisResult], **kwargs) -> str:
        """Generate Markdown report."""
        title = kwargs.get('title', 'Molecular Analysis Report')
        
        markdown_parts = [
            f"# {title}",
            f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "## Summary",
            f"- Total molecules analyzed: {len(results)}",
            f"- Successful analyses: {sum(1 for r in results if r.success)}",
            f"- Failed analyses: {len(results) - sum(1 for r in results if r.success)}",
            ""
        ]
        
        for i, result in enumerate(results):
            mol_name = result.molecule.name or f"Molecule {i + 1}"
            status = "✅ Success" if result.success else "❌ Failed"
            
            markdown_parts.extend([
                f"## {mol_name} {status}",
                f"**SMILES:** `{result.molecule.smiles}`",
                ""
            ])
            
            if result.properties and result.properties.properties:
                markdown_parts.append("### Properties")
                markdown_parts.append("| Property | Value |")
                markdown_parts.append("|----------|-------|")
                
                for prop_name, prop_value in result.properties.properties.items():
                    formatted_value = f"{prop_value:.3f}" if isinstance(prop_value, float) else str(prop_value)
                    markdown_parts.append(f"| {prop_name} | {formatted_value} |")
                
                markdown_parts.append("")
            
            if result.errors:
                markdown_parts.append("### Errors")
                for error in result.errors:
                    markdown_parts.append(f"- ❌ {error}")
                markdown_parts.append("")
            
            if result.warnings:
                markdown_parts.append("### Warnings")
                for warning in result.warnings:
                    markdown_parts.append(f"- ⚠️ {warning}")
                markdown_parts.append("")
        
        return '\n'.join(markdown_parts)
    
    def _generate_csv_report(self, results: List[AnalysisResult], **kwargs) -> str:
        """Generate CSV report with flattened data."""
        # Collect all unique property names
        all_prop_names = set()
        for result in results:
            if result.properties and result.properties.properties:
                all_prop_names.update(result.properties.properties.keys())
        
        all_prop_names = sorted(all_prop_names)
        
        # Create header
        header = ['name', 'smiles', 'success'] + all_prop_names + ['errors', 'warnings']
        csv_lines = [','.join(header)]
        
        # Add data rows
        for i, result in enumerate(results):
            row_data = [
                result.molecule.name or f"Molecule_{i+1}",
                f'"{result.molecule.smiles}"',  # Quote SMILES to handle commas
                str(result.success)
            ]
            
            # Add property values
            for prop_name in all_prop_names:
                if result.properties and prop_name in result.properties.properties:
                    value = result.properties.properties[prop_name]
                    if isinstance(value, float):
                        row_data.append(f"{value:.6f}")
                    else:
                        row_data.append(str(value))
                else:
                    row_data.append("")
            
            # Add errors and warnings
            row_data.append('; '.join(result.errors) if result.errors else "")
            row_data.append('; '.join(result.warnings) if result.warnings else "")
            
            csv_lines.append(','.join(row_data))
        
        return '\n'.join(csv_lines)
    
    def _get_property_unit(self, prop_name: str) -> str:
        """Get appropriate unit for property based on name."""
        unit_map = {
            'molecular_weight': 'g/mol',
            'mw': 'g/mol',
            'mass': 'g/mol',
            'logp': '',
            'tpsa': 'Ų',
            'hbd': '',
            'hba': '',
            'num_atoms': '',
            'num_bonds': '',
            'num_rings': '',
            'energy': 'kcal/mol',
            'dipole': 'Debye',
            'volume': 'ų',
            'surface_area': 'ų',
            'density': 'g/cm³'
        }
        
        prop_lower = prop_name.lower()
        for key, unit in unit_map.items():
            if key in prop_lower:
                return unit
        
        return ''  # Default to no unit
    
    def save_report(self, data: Union[AnalysisResult, List[AnalysisResult]], 
                   file_path: str, **kwargs) -> None:
        """
        Generate and save report to file.
        
        Args:
            data: Analysis results
            file_path: Output file path
            **kwargs: Report configuration options
        """
        try:
            report_content = self.render(data, **kwargs)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
                
        except Exception as e:
            raise FileIOError(f"Failed to save report to {file_path}: {str(e)}") from e