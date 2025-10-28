#!/usr/bin/env python3

import logging
import yaml
import os
from datetime import datetime
from modules.update_detector import UpdateDetector
from modules.deployment_manager import DeploymentManager
from modules.report_generator import ReportGenerator

class AutoPatch:
    def __init__(self, config_path='config.yaml'):
        self.config = self.load_config(config_path)
        self.setup_logging()
        
        self.update_detector = UpdateDetector(self.config['autopatch']['container_runtime'])
        self.deployment_manager = DeploymentManager(self.config['autopatch']['container_runtime'])
        self.report_generator = ReportGenerator(self.config)
        
        self.logger = logging.getLogger('autopatch')
    
    def load_config(self, config_path):
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_config = self.config['autopatch']['logging']
        os.makedirs(os.path.dirname(log_config['log_file']), exist_ok=True)
        
        logging.basicConfig(
            level=log_config['log_level'],
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_config['log_file']),
                logging.StreamHandler()
            ]
        )
    
    def run_update_cycle(self):
        """Execute complete update cycle"""
        self.logger.info("Starting AutoPatch update cycle")
        
        update_results = []
        
        try:
            # Get outdated containers
            outdated_containers = self.update_detector.get_outdated_containers()
            self.logger.info(f"Found {len(outdated_containers)} containers with updates")
            
            # Process each outdated container
            for item in outdated_containers:
                result = {
                    'container_name': item['container_name'],
                    'old_image': item['container']['Image'],
                    'new_image': item['new_image'],
                    'timestamp': datetime.now().isoformat(),
                    'status': 'pending'
                }
                
                try:
                    # Get container configuration
                    container_config = self.deployment_manager.get_container_config(item['container'])
                    if not container_config:
                        result['status'] = 'failed'
                        result['error'] = 'Could not get container configuration'
                        update_results.append(result)
                        continue
                    
                    # Redeploy container
                    success = self.deployment_manager.redeploy_container(container_config, item['new_image'])
                    
                    if success:
                        result['status'] = 'success'
                    else:
                        result['status'] = 'failed'
                        result['error'] = 'Redeployment failed'
                    
                except Exception as e:
                    result['status'] = 'failed'
                    result['error'] = str(e)
                
                update_results.append(result)
            
            # Generate report
            report = self.report_generator.generate_report(update_results)
            self.logger.info("AutoPatch update cycle completed")
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error during update cycle: {e}")
            return None

def main():
    """Main function"""
    autopatch = AutoPatch()
    autopatch.run_update_cycle()

if __name__ == "__main__":
    main()