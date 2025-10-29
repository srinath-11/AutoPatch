import React from 'react';
import { Card, CardContent, Typography } from '@mui/material';

const SystemInfo = () => {
  return (
    <Card>
      <CardContent>
        <Typography variant="h6">System Information</Typography>
        <Typography>Loading system info...</Typography>
      </CardContent>
    </Card>
  );
};

export default SystemInfo;