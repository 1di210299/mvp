# api/report_generator.py
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF
import io
import base64
from datetime import datetime
import json

class ReportGenerator:
    """Generate automated reports in multiple formats"""
    
    def __init__(self, data, report_config=None):
        self.data = data
        self.config = report_config or {}
        self.plots = []
        self.insights = []
    
    def generate_eda_report(self):
        """Generate an exploratory data analysis report"""
        df = pd.DataFrame(self.data)
        
        # Basic statistics
        numeric_cols = df.select_dtypes(include=['number']).columns
        stats = df[numeric_cols].describe().to_dict()
        
        # Missing values
        missing = df.isnull().sum().to_dict()
        
        # Correlation matrix for numeric columns
        if len(numeric_cols) > 1:
            corr_matrix = df[numeric_cols].corr().to_dict()
        else:
            corr_matrix = {}
        
        # Generate plots and save as base64
        for col in numeric_cols:
            fig = plt.figure(figsize=(10, 6))
            sns.histplot(df[col], kde=True)
            plt.title(f'Distribución de {col}')
            plt.tight_layout()
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            plot_data = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)
            
            self.plots.append({
                'name': f'distribution_{col}',
                'type': 'histogram',
                'data': plot_data,
                'title': f'Distribución de {col}'
            })
        
        # Generate insights
        self.insights = [
            {
                'type': 'summary',
                'text': f'El dataset contiene {len(df)} filas y {len(df.columns)} columnas.'
            },
            {
                'type': 'missing_data',
                'text': f'Hay columnas con datos faltantes: {", ".join([f"{k} ({v} valores)" for k, v in missing.items() if v > 0])}' if any(missing.values()) else 'No hay datos faltantes.'
            }
        ]
        
        # Add insights based on statistical patterns
        for col in numeric_cols:
            if stats[col]['std'] > stats[col]['mean'] * 2:
                self.insights.append({
                    'type': 'high_variance',
                    'text': f'La columna {col} muestra alta variabilidad, lo que podría indicar outliers o segmentos diferenciados.'
                })
        
        # Return the complete report
        return {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'rows': len(df),
                'columns': len(df.columns)
            },
            'statistics': stats,
            'missing_data': missing,
            'correlation': corr_matrix,
            'plots': self.plots,
            'insights': self.insights
        }
    
    def export_to_pdf(self, filename=None):
        """Export report to PDF"""
        # Implementation using FPDF
        # ...
        
    def export_to_excel(self, filename=None):
        """Export report to Excel"""
        # Implementation using pandas
        # ...