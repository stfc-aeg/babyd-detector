import { Alert } from 'react-bootstrap';

function WSStatusBox({ label, type = 'success', children }) {
  return (
    <Alert variant={type} style={{ whiteSpace: 'pre-wrap' }}>
      <div>
        {label ? `${label}: ` : ''}
        {children}
      </div>
    </Alert>
  );
}

export default WSStatusBox;