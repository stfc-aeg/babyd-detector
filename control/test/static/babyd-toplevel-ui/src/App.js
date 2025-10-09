import './App.css';
import 'odin-react/dist/index.css';
import 'bootstrap/dist/css/bootstrap.min.css';

import React from 'react';
import { OdinApp } from 'odin-react';
import { useAdapterEndpoint } from 'odin-react';

import CaptureSettings from './components/pages/CaptureSettings';
import Loki from './components/pages/loki';
import ADXDMA from './components/pages/adxdma';

function App() {
  const endpoint_url =
    process.env.NODE_ENV === 'development'
      ? process.env.REACT_APP_ENDPOINT_URL
      : window.location.origin;
  const munirEndpoint = useAdapterEndpoint('babyd', endpoint_url, 500);
  const LokiProxyEndpoint = useAdapterEndpoint('loki_proxy', endpoint_url, 500);

  return (
    <OdinApp
      title="BabyD Top Level Control"
      navLinks={['Captures', 'LOKI', 'ADXDMA']}
    >
      <CaptureSettings munirEndpoint={munirEndpoint} />
      <Loki munirEndpoint={munirEndpoint} LokiProxyEndpoint={LokiProxyEndpoint} />
      <ADXDMA munirEndpoint={munirEndpoint} />
    </OdinApp>
  );
}

export default App;