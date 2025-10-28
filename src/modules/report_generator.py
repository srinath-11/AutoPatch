import logging
import json
from datetime import datetime
import os

class ReportGenerator:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger('autopatch')
    
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