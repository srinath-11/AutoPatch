import subprocess
import json
import logging

class UpdateDetector:
    def __init__(self, runtime='podman'):
        self.runtime = runtime
        self.logger = logging.getLogger('autopatch')
    
    def get_running_containers(self):
        """Get list of all running containers"""
        try:
            result = subprocess.run(
                ['podman', 'ps', '--format', 'json'],
                capture_output=True, text=True, check=True
            )
            containers = json.loads(result.stdout)
            self.logger.info(f"Found {len(containers)} running containers")
            return containers
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error getting containers: {e}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing container JSON: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return []
    
    def check_image_updates(self, container):
        """Check if newer image is available"""
        try:
            container_name = container['Names'][0] if container['Names'] else container['Id'][:12]
            current_image = container['Image']
            
            self.logger.info(f"Checking updates for {container_name}")
            
            # Pull latest image
            pull_result = subprocess.run(
                ['podman', 'pull', current_image],
                capture_output=True, text=True
            )
            
            if pull_result.returncode == 0:
                self.logger.info(f"Update available for {container_name}")
                return True, current_image
            else:
                self.logger.warning(f"No update for {container_name}")
                return False, current_image
                
        except Exception as e:
            self.logger.error(f"Error checking updates: {e}")
            return False, None
    
    def get_outdated_containers(self):
        """Get containers with available updates"""
        outdated = []
        containers = self.get_running_containers()
        
        for container in containers:
            has_update, new_image = self.check_image_updates(container)
            if has_update:
                outdated.append({
                    'container': container,
                    'new_image': new_image,
                    'container_name': container['Names'][0] if container['Names'] else container['Id'][:12]
                })
        
        return outdated