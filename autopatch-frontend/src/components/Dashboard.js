import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Typography,
  Card,
  CardContent,
  Box,
  Tabs,
  Tab,
  AppBar,
  CircularProgress,
  Alert,
  Button,
  Chip,
  Paper,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Computer,
  Storage,
  Update,
  List,
  Settings,
  Refresh,
  Assessment, // New icon for reports
  DataObject, // New icon for JSON
  TableView, // New icon for CSV
  PictureAsPdf, // New icon for PDF
} from '@mui/icons-material';
import { apiService } from '../services/api';

// Tab Panel Component
function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const Dashboard = () => {
  const [tabValue, setTabValue] = useState(0);
  const [systemInfo, setSystemInfo] = useState(null);
  const [containers, setContainers] = useState([]);
  const [updates, setUpdates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [lastUpdate, setLastUpdate] = useState('');
  const [backendConnected, setBackendConnected] = useState(false);
  const [reportMenuAnchorEl, setReportMenuAnchorEl] = useState(null);
  const [isReportMenuOpen, setIsReportMenuOpen] = useState(false);

  const handleReportMenuOpen = (event) => {
    setReportMenuAnchorEl(event.currentTarget);
    setIsReportMenuOpen(true);
  };

  const handleReportMenuClose = () => {
    setReportMenuAnchorEl(null);
    setIsReportMenuOpen(false);
  };

  const handleGenerateReport = async (format) => {
    handleReportMenuClose();
    try {
      setLoading(true);
      const response = await apiService.generateReport(format);
      // Handle file download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `autopatch-report.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError('Failed to generate report.');
    } finally {
      setLoading(false);
    }
  };

  const fetchData = async () => {
    try {
      setLoading(true);
      setError('');

      // First check if backend is healthy
      try {
        await apiService.checkHealth();
        setBackendConnected(true);
      } catch (healthError) {
        setBackendConnected(false);
        setError('Backend server is not running. Please start the Flask server on port 5000.');
        setLoading(false);
        return;
      }

      // Fetch all data in parallel
      const [systemResponse, containersResponse, updatesResponse] = await Promise.all([
        apiService.getSystemInfo(),
        apiService.getContainers(),
        apiService.checkUpdates()
      ]);

      setSystemInfo(systemResponse.data);
      setContainers(containersResponse.data.containers || []);
      setUpdates(updatesResponse.data.updates || []);
      setLastUpdate(new Date().toLocaleTimeString());
      setError('');
    } catch (err) {
      setBackendConnected(false);
      setError('Failed to fetch data from backend server. Make sure Flask is running on port 5000.');
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunUpdate = async () => {
    try {
      setLoading(true);
      const response = await apiService.runUpdate();
      if (response.data.success) {
        setError('');
        // Refresh data after update
        await fetchData();
      } else {
        setError(`Update failed: ${response.data.error}`);
      }
    } catch (err) {
      setError('Error running update. Check backend connection.');
    } finally {
      setLoading(false);
    }
  };

  const handleContainerAction = async (action, containerName) => {
    try {
      setLoading(true);
      if (action === 'restart') {
        await apiService.restartContainer(containerName);
      } else if (action === 'stop') {
        await apiService.stopContainer(containerName);
      }
      // Refresh data after action
      await fetchData();
    } catch (err) {
      setError(`Failed to ${action} container ${containerName}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    
    // Refresh data every 30 seconds if backend is connected
    const interval = setInterval(() => {
      if (backendConnected) {
        fetchData();
      }
    }, 30000);
    
    return () => clearInterval(interval);
  }, [backendConnected]);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  // System Overview Component
  const SystemOverview = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Computer sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6">System</Typography>
            </Box>
            {systemInfo ? (
              <>
                <Typography variant="body2" color="text.secondary">
                  <strong>Platform:</strong> {systemInfo.system?.platform}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  <strong>Python:</strong> {systemInfo.system?.python_version}
                </Typography>
              </>
            ) : (
              <Typography variant="body2">Loading system info...</Typography>
            )}
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Storage sx={{ mr: 1, color: 'secondary.main' }} />
              <Typography variant="h6">Containers</Typography>
            </Box>
            <Typography variant="h4" color="primary.main">
              {containers.length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Running containers
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Update sx={{ mr: 1, color: 'warning.main' }} />
              <Typography variant="h6">Updates</Typography>
            </Box>
            <Typography variant="h4" color={updates.length > 0 ? 'warning.main' : 'success.main'}>
              {updates.length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Available updates
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      {/* Quick Actions */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Button
                variant="contained"
                startIcon={<Refresh />}
                onClick={fetchData}
                disabled={loading}
              >
                Refresh Data
              </Button>
              <Button
                variant="outlined"
                startIcon={<Update />}
                onClick={fetchData}
                disabled={loading}
              >
                Check Updates
              </Button>
              <Button
                variant="contained"
                color="warning"
                startIcon={<Update />}
                onClick={handleRunUpdate}
                disabled={loading || updates.length === 0 || !backendConnected}
              >
                Run AutoPatch
              </Button>
              <Button
                variant="contained"
                color="info"
                startIcon={<Assessment />}
                onClick={handleReportMenuOpen}
                disabled={loading || !backendConnected}
              >
                Generate Report
              </Button>
              <Menu
                anchorEl={reportMenuAnchorEl}
                open={isReportMenuOpen}
                onClose={handleReportMenuClose}
              >
                <MenuItem onClick={() => handleGenerateReport('json')}>
                  <ListItemIcon>
                    <DataObject />
                  </ListItemIcon>
                  <ListItemText primary="JSON" />
                </MenuItem>
                <MenuItem onClick={() => handleGenerateReport('csv')}>
                  <ListItemIcon>
                    <TableView />
                  </ListItemIcon>
                  <ListItemText primary="CSV" />
                </MenuItem>
                <MenuItem onClick={() => handleGenerateReport('pdf')}>
                  <ListItemIcon>
                    <PictureAsPdf />
                  </ListItemIcon>
                  <ListItemText primary="PDF" />
                </MenuItem>
              </Menu>
            </Box>
            {lastUpdate && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Last updated: {lastUpdate}
              </Typography>
            )}
            {backendConnected && (
              <Chip 
                label="Backend Connected" 
                color="success" 
                size="small" 
                sx={{ mt: 1 }}
              />
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  // Containers Management Component
  const ContainersManagement = () => (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">Container Management</Typography>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={fetchData}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {!backendConnected ? (
        <Alert severity="warning">
          Backend server not connected. Please start the Flask server to manage containers.
        </Alert>
      ) : containers.length === 0 ? (
        <Alert severity="info">
          No containers running. Start some containers to see them here.
        </Alert>
      ) : (
        <Grid container spacing={2}>
          {containers.map((container, index) => (
            <Grid item xs={12} md={6} key={container.id || index}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Typography variant="h6" component="div">
                      {container.name || container.Names?.[0]}
                    </Typography>
                    <Chip
                      label={container.status || container.State}
                      color={(container.state === 'running' || container.Status?.includes('Up')) ? 'success' : 'default'}
                      size="small"
                    />
                  </Box>
                  
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Image: {container.image || container.Image}
                  </Typography>
                  
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    ID: {container.id || container.Id?.substring(0, 12)}
                  </Typography>

                  <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={() => handleContainerAction('restart', container.name || container.Names?.[0])}
                      disabled={loading}
                    >
                      Restart
                    </Button>
                    <Button
                      size="small"
                      variant="outlined"
                      color="error"
                      onClick={() => handleContainerAction('stop', container.name || container.Names?.[0])}
                      disabled={loading}
                    >
                      Stop
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );

  // Updates Management Component
  const UpdatesManagement = () => (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">Update Management</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={fetchData}
            disabled={loading}
          >
            Check Updates
          </Button>
          <Button
            variant="contained"
            color="warning"
            startIcon={<Update />}
            onClick={handleRunUpdate}
            disabled={loading || updates.length === 0 || !backendConnected}
          >
            Apply All Updates
          </Button>
        </Box>
      </Box>

      {!backendConnected ? (
        <Alert severity="warning">
          Backend server not connected. Please start the Flask server to check for updates.
        </Alert>
      ) : updates.length === 0 ? (
        <Alert severity="success">
          All containers are up to date! No updates available.
        </Alert>
      ) : (
        <Grid container spacing={2}>
          {updates.map((update, index) => (
            <Grid item xs={12} key={index}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Typography variant="h6" component="div">
                      {update.container_name}
                    </Typography>
                    <Chip label="Update Available" color="warning" />
                  </Box>
                  
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <Paper variant="outlined" sx={{ p: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Current Version
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {update.current_image}
                        </Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Paper variant="outlined" sx={{ p: 2, borderColor: 'warning.main' }}>
                        <Typography variant="subtitle2" gutterBottom color="warning.main">
                          Available Update
                        </Typography>
                        <Typography variant="body2" color="warning.main">
                          {update.new_image}
                        </Typography>
                      </Paper>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );

  // System Information Component
  const SystemInformation = () => (
    <Box>
      <Typography variant="h5" gutterBottom>
        System Information
      </Typography>
      
      {!backendConnected ? (
        <Alert severity="warning">
          Backend server not connected. Please start the Flask server to view system information.
        </Alert>
      ) : systemInfo ? (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  System Details
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  <strong>Platform:</strong> {systemInfo.system?.platform}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  <strong>Python Version:</strong> {systemInfo.system?.python_version}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Podman Information
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  <strong>Version:</strong> {systemInfo.podman?.version || 'Unknown'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  <strong>Running Containers:</strong> {systemInfo.podman?.containers_running || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  <strong>OS:</strong> {systemInfo.podman?.os || 'Unknown'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      ) : (
        <Alert severity="info">
          Loading system information...
        </Alert>
      )}
    </Box>
  );

  return (
    <Container maxWidth="lg" sx={{ mt: 2, mb: 4 }}>
      {/* Header */}
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom color="primary">
          AutoPatch Dashboard
        </Typography>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          Automated Container Update Management System
        </Typography>
        
        {backendConnected ? (
          <Alert severity="success" sx={{ mt: 2 }}>
            ✅ Connected to backend server
          </Alert>
        ) : (
          <Alert severity="warning" sx={{ mt: 2 }}>
            ⚠️ Backend server not connected. Please start the Flask server.
          </Alert>
        )}
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Loading Indicator */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Tabs Navigation */}
      <AppBar position="static" color="default" sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab icon={<Computer />} label="Overview" />
          <Tab icon={<List />} label="Containers" />
          <Tab icon={<Update />} label="Updates" />
          <Tab icon={<Settings />} label="System Info" />
        </Tabs>
      </AppBar>

      {/* Tab Panels */}
      <TabPanel value={tabValue} index={0}>
        <SystemOverview />
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <ContainersManagement />
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <UpdatesManagement />
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        <SystemInformation />
      </TabPanel>
    </Container>
  );
};

export default Dashboard;