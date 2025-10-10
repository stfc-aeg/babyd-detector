import { Col } from 'react-bootstrap';
import WSStatusBox from './WSStatusBox';
import { formatData } from '../functions/utils';

function generateCoreInfo(adxdmaData) {
  if (!adxdmaData) {
    return [];
  }

  const numFrameCounts = Object.keys(adxdmaData).filter((key) =>
    key.startsWith('frame_count')
  ).length;

  return [...Array(numFrameCounts).keys()].map((index) => {
    const frameCount = adxdmaData[`frame_count_${index}`];
    const linkStatus = adxdmaData[`link_status_${index}`];

    return (
      <Col sm={12} md={6} lg={6} xl={6} xxl={3} key={index}>
        <WSStatusBox label={`Core ${index}`}>
          {`\nFrame Count:\n${formatData(frameCount)}\nLink Status:\n${formatData(
            linkStatus
          )}`}
        </WSStatusBox>
      </Col>
    );
  });
}

function CoreInfoDisplay({ adxdmaData }) {
  return <>{generateCoreInfo(adxdmaData)}</>;
}

export default CoreInfoDisplay;