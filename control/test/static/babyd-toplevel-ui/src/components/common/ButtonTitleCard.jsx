import { Card } from 'react-bootstrap';

function ButtonTitleCard({ title, children, actions }) {
  return (
    <Card className="mb-4">
      <Card.Header className="d-flex align-items-center">
        <span>{title}</span>
        {actions && actions.length > 0 && (
          <div className="ms-3 d-flex">
            {actions.map((action, index) => (
              <div key={index} className="ms-2">
                {action}
              </div>
            ))}
          </div>
        )}
      </Card.Header>
      <Card.Body>{children}</Card.Body>
    </Card>
  );
}

export default ButtonTitleCard;