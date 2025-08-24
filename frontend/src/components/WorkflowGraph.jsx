import React from 'react';

export function WorkflowGraph({ planData }) {
  if (!planData || !planData.dependency_tasks || planData.dependency_tasks.length === 0) {
    return (
      <div style={{ 
        height: 200, 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        backgroundColor: '#f8f9fa',
        borderRadius: '8px',
        border: '1px solid #dee2e6'
      }}>
        <p style={{ color: '#6c757d' }}>No tasks to visualize</p>
      </div>
    );
  }

  const tasks = planData.dependency_tasks;

return (
  <div 
    className="workflow-container" 
    style={{
      position: 'relative', // so arrows position relative to this container
      padding: '20px',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '300px'
    }}
  >
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '40px', // more space so arrows don’t overlap tasks
      alignItems: 'center',
      maxWidth: '600px',
      width: '100%'
    }}>
      {tasks.map((task, index) => (
        <div 
          key={task.id} 
          style={{ 
            display: 'flex', 
            flexDirection: 'column',
            alignItems: 'center',
            position: 'relative'
          }}
        >
          {/* Step number */}
          <div style={{
            width: '30px',
            height: '30px',
            borderRadius: '50%',
            backgroundColor: getPriorityColor(task.priority),
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '14px',
            fontWeight: 'bold'
          }}>
            {index + 1}
          </div>

          {/* Task info */}
          <div style={{
            marginTop: '10px',
            padding: '10px 15px',
            backgroundColor: '#fff',
            border: '1px solid #e0e0e0',
            borderRadius: '8px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            textAlign: 'center',
            width: '100%'
          }}>
            <div style={{ fontWeight: 'bold', fontSize: '14px' }}>
              {task.name}
            </div>
            <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
              {task.estimated_duration_days} days • {task.category}
            </div>
          </div>

          {/* Arrow */}
          {index < tasks.length - 1 && (
            <div style={{
              marginTop: '10px',
              fontSize: '20px',
              color: '#ccc'
            }}>
              ↓
            </div>
          )}
        </div>
      ))}
    </div>
  </div>
);
}

function getPriorityColor(priority) {
  switch (priority) {
    case 'high': return '#ef4444';
    case 'medium': return '#f59e0b';
    case 'low': return '#10b981';
    default: return '#6b7280';
  }
}