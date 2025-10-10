import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Button from 'react-bootstrap/Button';
import { TitleCard, StatusBox, ToggleSwitch } from 'odin-react';
import { WithEndpoint } from 'odin-react';

const EndPointButton = WithEndpoint(Button);
const EndpointToggleSwitch = WithEndpoint(ToggleSwitch);

function Loki({ munirEndpoint, LokiProxyEndpoint }) {
  const isLOKIConnected = munirEndpoint?.data?.loki?.connected;
  const isLOKIInitialised = munirEndpoint?.data?.loki?.initialised;
  const isLokiBoardResponding = LokiProxyEndpoint?.data?.node_1
    ? Object.keys(LokiProxyEndpoint.data.node_1).length > 0
    : false;

  return (
    <TitleCard title="Loki & BabyD Hardware">
      <Row>
        <Col sm={12} md={6} lg={6} xl={6} xxl={6}>
          <TitleCard title="LOKI">
            <Row>
              <Col sm={12} md={6} lg={4} xl={4} xxl={4}>
                <StatusBox label="Board Status">
                  {isLokiBoardResponding ? 'Connected' : 'Disconnected'}
                </StatusBox>
              </Col>
              <Col sm={12} md={6} lg={4} xl={4} xxl={4}>
                <StatusBox label="CPU">
                  {Math.round(
                    LokiProxyEndpoint?.data?.node_1?.environment?.temperature?.zynq_ps
                  ) + ' \u00b0C'}
                </StatusBox>
              </Col>
              <Col sm={12} md={6} lg={4} xl={4} xxl={4}>
                <StatusBox label="Board">
                  {Math.round(
                    LokiProxyEndpoint?.data?.node_1?.environment?.temperature?.BOARD
                  ) + ' \u00b0C'}
                </StatusBox>
              </Col>
            </Row>
          </TitleCard>
        </Col>

        <Col sm={12} md={6} lg={6} xl={6} xxl={6}>
          <TitleCard
            title={
              <div className="ms-3 d-flex">
                <span>BabyD</span>

                <div className="ms-3 d-flex" style={{ gap: '15px' }}>
                  <EndPointButton
                    endpoint={munirEndpoint}
                    event_type="click"
                    fullpath="loki/connected"
                    value={!isLOKIConnected}
                    className="w-100"
                    style={{ whiteSpace: 'nowrap' }}
                    variant={isLOKIConnected ? 'danger' : 'success'}
                  >
                    {isLOKIConnected ? 'Disconnect' : 'Connect'}
                  </EndPointButton>
                  <EndPointButton
                    endpoint={munirEndpoint}
                    event_type="click"
                    fullpath="loki/initialised"
                    value={!isLOKIInitialised}
                    className="w-100"
                    style={{ whiteSpace: 'nowrap' }}
                    variant={isLOKIInitialised ? 'danger' : 'success'}
                  >
                    {isLOKIInitialised ? 'Re-Inititalise' : 'Inititalise'}
                  </EndPointButton>
                  <EndpointToggleSwitch
                    endpoint={munirEndpoint}
                    event_type="click"
                    label="Manual SYNC"
                    fullpath="loki/sync"
                    checked={munirEndpoint.data.loki?.sync}
                    value={munirEndpoint.data.loki?.sync}
                  />
                </div>
              </div>
            }
          >
            <Row>
              <Col sm={12} md={6} lg={4} xl={4} xxl={4}>
                <StatusBox label="BabyD ASIC">
                  {LokiProxyEndpoint?.data?.node_1?.application?.system_state?.ASIC_EN
                    ? 'Enabled'
                    : 'Disabled'}
                </StatusBox>
              </Col>
              <Col sm={12} md={6} lg={4} xl={4} xxl={4}>
                <StatusBox label="BabyD Chip ">
                  {LokiProxyEndpoint?.data?.node_1?.environment?.temperature
                    ?.BD_MIC_IN + ' \u00b0C'}
                </StatusBox>
              </Col>
              <Col sm={12} md={6} lg={4} xl={4} xxl={4}></Col>
            </Row>
          </TitleCard>
        </Col>
      </Row>
    </TitleCard>
  );
}

export default Loki;