import subprocess
import json
import logging

class DeploymentManager:
    def __init__(self, runtime='podman'):
        self.runtime = runtime
        self.logger = logging.getLogger('autopatch')
    
    def get_container_config(self, container):
        """Extract container configuration"""
        try:
            container_id = container['Id']
            result = subprocess.run(
                ['podman', 'inspect', container_id],
                capture_output=True, text=True, check=True
            )
            container_info = json.loads(result.stdout)[0]
            
            return {
                'name': container_info['Name'].lstrip('/'),
                'image': container_info['Config']['Image'],
                'env': container_info['Config']['Env'] or [],
                'ports': [],
                'volumes': [],
                'restart_policy': 'no'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting container config: {e}")
            return None
    
    def redeploy_container(self, container_config, new_image):
        """Redeploy container with new image"""
        try:
            container_name = container_config['name']
            
            self.logger.info(f"Stopping container: {container_name}")
            # Stop container
            subprocess.run(['podman', 'stop', container_name], check=True)
            
            self.logger.info(f"Removing container: {container_name}")
            # Remove container
            subprocess.run(['podman', 'rm', container_name], check=True)
            
            self.logger.info(f"Creating new container: {container_name}")
            # Create new container
            run_cmd = ['podman', 'run', '-d', '--name', container_name, new_image]
            
            result = subprocess.run(run_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"Successfully redeployed {container_name}")
                return True
            else:
                self.logger.error(f"Failed to redeploy {container_name}: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error redeploying {container_name}: {e}")
            return False