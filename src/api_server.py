from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import json
import os
import logging
from datetime import datetime
import subprocess
import platform
import io
import yaml
from modules.report_generator import ReportGenerator

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('autopatch-api')

# Load config
config = {
    'autopatch': {
        'logging': {
            'report_dir': 'logs/reports'
        }
    }
}

class AutoPatchManager:
    def __init__(self):
        self.logger = logger
    
    def get_running_containers(self):
        """Get list of running containers using Podman"""
        try:
            result = subprocess.run(
                ['podman', 'ps', '--format', 'json'],
                capture_output=True, text=True, check=True
            )
            containers = json.loads(result.stdout)
            
            container_list = []
            for container in containers:
                container_list.append({
                    'id': container['Id'][:12],
                    'name': container['Names'][0] if container['Names'] else 'Unknown',
                    'image': container['Image'],
                    'status': container['Status'],
                    'created': container['CreatedAt'],
                    'ports': container.get('Ports', []),
                    'state': container.get('State', 'unknown')
                })
            
            return container_list
        except Exception as e:
            logger.error(f"Error getting containers: {e}")
            return []
    
    def check_updates(self):
        """Check for container updates"""
        try:
            containers = self.get_running_containers()
            updates_available = []
            
            for container in containers:
                image_name = container['image']
                
                try:
                    # Pull latest image to check for updates
                    pull_result = subprocess.run(
                        ['podman', 'pull', image_name],
                        capture_output=True, text=True
                    )
                    
                    if pull_result.returncode == 0:
                        updates_available.append({
                            'container_name': container['name'],
                            'current_image': container['image'],
                            'new_image': image_name,
                            'has_update': True
                        })
                except Exception as e:
                    logger.warning(f"Failed to check updates for {container['name']}: {e}")
                    continue
            
            return updates_available
        except Exception as e:
            logger.error(f"Error checking updates: {e}")
            return []
    
    def run_autopatch(self):
        """Run the AutoPatch update process"""
        try:
            updates = self.check_updates()
            results = []
            
            for update in updates:
                try:
                    container_name = update['container_name']
                    
                    # Stop container
                    self.logger.info(f"Stopping container: {container_name}")
                    stop_result = subprocess.run(
                        ['podman', 'stop', container_name], 
                        capture_output=True, text=True
                    )
                    
                    if stop_result.returncode != 0:
                        self.logger.warning(f"Failed to stop container {container_name}: {stop_result.stderr}")
                        continue
                    
                    # Remove container
                    self.logger.info(f"Removing container: {container_name}")
                    rm_result = subprocess.run(
                        ['podman', 'rm', container_name], 
                        capture_output=True, text=True
                    )
                    
                    if rm_result.returncode != 0:
                        self.logger.warning(f"Failed to remove container {container_name}: {rm_result.stderr}")
                        continue
                    
                    # Run new container
                    self.logger.info(f"Starting new container: {container_name}")
                    run_result = subprocess.run(
                        ['podman', 'run', '-d', '--name', container_name, update['new_image']], 
                        capture_output=True, text=True
                    )
                    
                    if run_result.returncode == 0:
                        results.append({
                            'container_name': container_name,
                            'status': 'success',
                            'old_image': update['current_image'],
                            'new_image': update['new_image']
                        })
                        self.logger.info(f"Successfully updated {container_name}")
                    else:
                        results.append({
                            'container_name': container_name,
                            'status': 'failed',
                            'error': run_result.stderr
                        })
                        self.logger.error(f"Failed to start new container {container_name}: {run_result.stderr}")
                        
                except Exception as e:
                    results.append({
                        'container_name': update['container_name'],
                        'status': 'failed',
                        'error': str(e)
                    })
                    self.logger.error(f"Error updating {update['container_name']}: {e}")
            
            return {
                'success': True,
                'updated_containers': len([r for r in results if r['status'] == 'success']),
                'failed_containers': len([r for r in results if r['status'] == 'failed']),
                'results': results
            }
        except Exception as e:
            logger.error(f"Error running autopatch: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_system_info(self):
        """Get system information"""
        try:
            # Podman info
            podman_info = subprocess.run(
                ['podman', 'info', '--format', 'json'], 
                capture_output=True, text=True
            )
            podman_data = json.loads(podman_info.stdout) if podman_info.returncode == 0 else {}
            
            # Get container count
            containers = self.get_running_containers()
            
            return {
                'system': {
                    'platform': platform.platform(),
                    'python_version': platform.python_version(),
                },
                'podman': {
                    'version': podman_data.get('version', {}).get('Version', 'Unknown'),
                    'containers_running': len(containers),
                    'os': podman_data.get('host', {}).get('os', {}).get('distribution', 'Unknown')
                }
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {'error': str(e)}

# Initialize AutoPatch manager and Report Generator
ap_manager = AutoPatchManager()
report_generator = ReportGenerator(config)

# Root endpoint
@app.route('/')
def home():
    return jsonify({
        'message': 'AutoPatch API Server is running!',
        'version': '1.0.0',
        'endpoints': {
            '/api/health': 'Health check',
            '/api/containers': 'Get running containers',
            '/api/check-updates': 'Check for container updates',
            '/api/run-update': 'Run AutoPatch update process',
            '/api/system-info': 'Get system information',
            '/api/generate-report': 'Generate a report of containers and updates'
        }
    })

# API Routes
@app.route('/api/generate-report', methods=['GET'])
def generate_report():
    try:
        report_format = request.args.get('format', 'json')
        containers = ap_manager.get_running_containers()
        updates = ap_manager.check_updates()
        data = {
            'containers': containers,
            'updates': updates
        }
        report_data, content_type = report_generator.generate_on_demand_report(data, report_format)

        return send_file(
            io.BytesIO(report_data),
            mimetype=content_type,
            as_attachment=True,
            download_name=f'autopatch-report.{report_format}'
        )
    except Exception as e:
        import traceback
        logger.error(f"Error in /api/generate-report: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/containers', methods=['GET'])
def get_containers():
    try:
        containers = ap_manager.get_running_containers()
        return jsonify({'containers': containers})
    except Exception as e:
        logger.error(f"Error in /api/containers: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/check-updates', methods=['GET'])
def check_updates():
    try:
        updates = ap_manager.check_updates()
        return jsonify({
            'updates_available': len(updates),
            'updates': updates
        })
    except Exception as e:
        logger.error(f"Error in /api/check-updates: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/run-update', methods=['POST'])
def run_update():
    try:
        result = ap_manager.run_autopatch()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in /api/run-update: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system-info', methods=['GET'])
def system_info():
    try:
        info = ap_manager.get_system_info()
        return jsonify(info)
    except Exception as e:
        logger.error(f"Error in /api/system-info: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/container/<name>/restart', methods=['POST'])
def restart_container(name):
    try:
        result = subprocess.run(
            ['podman', 'restart', name], 
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return jsonify({'success': True, 'message': f'Container {name} restarted successfully'})
        else:
            return jsonify({'success': False, 'error': result.stderr}), 500
    except Exception as e:
        logger.error(f"Error restarting container {name}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/container/<name>/stop', methods=['POST'])
def stop_container(name):
    try:
        result = subprocess.run(
            ['podman', 'stop', name], 
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return jsonify({'success': True, 'message': f'Container {name} stopped successfully'})
        else:
            return jsonify({'success': False, 'error': result.stderr}), 500
    except Exception as e:
        logger.error(f"Error stopping container {name}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Handle 404 errors
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'available_endpoints': {
            'GET /': 'API information',
            'GET /api/health': 'Health check',
            'GET /api/containers': 'Get running containers',
            'GET /api/check-updates': 'Check for container updates',
            'POST /api/run-update': 'Run AutoPatch update process',
            'GET /api/system-info': 'Get system information',
            'POST /api/container/<name>/restart': 'Restart container',
            'POST /api/container/<name>/stop': 'Stop container'
        }
    }), 404

if __name__ == '__main__':
    print("🚀 Starting AutoPatch API Server...")
    print("📡 Server running on: http://127.0.0.1:5000")
    print("🔗 Available endpoints:")
    print("   GET  /              - API information")
    print("   GET  /api/health    - Health check")
    print("   GET  /api/containers - Get running containers")
    print("   GET  /api/check-updates - Check for updates")
    print("   POST /api/run-update - Run AutoPatch")
    print("   GET  /api/system-info - System information")
    print("   POST /api/container/<name>/restart - Restart container")
    print("   POST /api/container/<name>/stop - Stop container")
    print("\nPress CTRL+C to stop the server")
    
    app.run(host='0.0.0.0', port=5000, debug=True)