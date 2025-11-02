import logging
import json
from datetime import datetime
import os
import pandas as pd
from fpdf import FPDF

class ReportGenerator:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger('autopatch')

    def generate_on_demand_report(self, data, report_format):
        if report_format == 'json':
            return self._generate_json_report(data)
        elif report_format == 'csv':
            return self._generate_csv_report(data)
        elif report_format == 'pdf':
            return self._generate_pdf_report(data)
        else:
            raise ValueError(f"Unsupported report format: {report_format}")

    def _generate_json_report(self, data):
        report = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        return json.dumps(report, indent=2).encode('utf-8'), 'application/json'

    def _generate_csv_report(self, data):
        df = pd.DataFrame(data)
        csv_data = df.to_csv(index=False).encode('utf-8')
        return csv_data, 'text/csv'

    def _generate_pdf_report(self, data):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'AutoPatch Report', 0, 1, 'C')
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f"Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1, 'C')
        pdf.ln(10)

        for section_title, section_data in data.items():
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, section_title.capitalize(), 0, 1)
            pdf.ln(5)

            if not section_data:
                pdf.set_font('Arial', '', 12)
                pdf.cell(0, 10, "No data available.", 0, 1)
                pdf.ln(5)
                continue

            for item in section_data:
                for key, value in item.items():
                    pdf.set_font('Arial', 'B', 10)
                    pdf.cell(40, 10, f"{key}:")
                    pdf.set_font('Arial', '', 10)
                    pdf.multi_cell(0, 10, str(value))
                pdf.ln(5)

        return pdf.output(dest='S').encode('latin-1'), 'application/pdf'
    
    def generate_report(self, update_results):
        """Generate update report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_checked': len(update_results),
                'updated': len([r for r in update_results if r['status'] == 'success']),
                'failed': len([r for r in update_results if r['status'] == 'failed'])
            },
            'details': update_results
        }
        
        # Save to file
        self.save_report_to_file(report)
        return report
    
    def save_report_to_file(self, report):
        """Save report to JSON file"""
        try:
            report_dir = self.config['autopatch']['logging']['report_dir']
            os.makedirs(report_dir, exist_ok=True)
            
            filename = f"autopatch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(report_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.logger.info(f"Report saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Error saving report: {e}")