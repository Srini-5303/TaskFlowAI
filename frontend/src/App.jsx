import React, { useState } from 'react';
import './App.css';
import { WorkflowGraph } from './components/WorkflowGraph';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '20px', backgroundColor: '#fee', color: '#c00', borderRadius: '8px' }}>
          <h3>Something went wrong with the visualization</h3>
          <p>Error: {this.state.error?.message}</p>
          <button onClick={() => this.setState({ hasError: false, error: null })}>
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

function AgentOverlay({ currentAgent, message, visible }) {
  if (!visible) return null;

  const getAgentEmoji = (agent) => {
    const emojiMap = {
      'system': '⚙️',
      'planner': '📋',
      'timeline': '⏱️',
      'dependency': '🔗',
      'formatter': '📄'
    };
    return emojiMap[agent] || '🤖';
  };

  const getAgentColor = (agent) => {
    const colorMap = {
      'system': '#6366f1',
      'planner': '#8b5cf6', 
      'timeline': '#06b6d4',
      'dependency': '#10b981',
      'formatter': '#f59e0b'
    };
    return colorMap[agent] || '#6b7280';
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.7)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        backgroundColor: 'white',
        padding: '40px',
        borderRadius: '16px',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        textAlign: 'center',
        minWidth: '400px'
      }}>
        <div style={{
          fontSize: '48px',
          marginBottom: '20px',
          animation: 'pulse 2s infinite'
        }}>
          {getAgentEmoji(currentAgent)}
        </div>
        
        <h3 style={{
          color: getAgentColor(currentAgent),
          marginBottom: '10px',
          fontSize: '24px',
          fontWeight: 'bold'
        }}>
          {currentAgent?.charAt(0).toUpperCase() + currentAgent?.slice(1)} Agent
        </h3>
        
        <p style={{
          color: '#4b5563',
          fontSize: '16px',
          margin: 0
        }}>
          {message}
        </p>
        
        <div style={{
          marginTop: '20px',
          display: 'flex',
          justifyContent: 'center'
        }}>
          <div style={{
            width: '40px',
            height: '4px',
            backgroundColor: getAgentColor(currentAgent),
            borderRadius: '2px',
            animation: 'loading 1.5s ease-in-out infinite'
          }}></div>
        </div>
      </div>
    </div>
  );
}


function App() {
  const [projectInput, setProjectInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [planData, setPlanData] = useState(null);
  const [error, setError] = useState(null);

  const [currentAgent, setCurrentAgent] = useState(null);
  const [agentMessage, setAgentMessage] = useState('');

const handleSubmit = async () => {
  if (!projectInput.trim()) {
    setError('Please enter a project description');
    return;
  }

  setLoading(true);
  setError(null);
  setPlanData(null);
  setCurrentAgent('system');
  setAgentMessage('Connecting to agents...');

  try {
    const response = await fetch('http://localhost:8000/api/generate-plan', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        project_statement: projectInput
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            
            if (data.status === 'running') {
              setCurrentAgent(data.agent);
              setAgentMessage(data.message);
            } else if (data.status === 'completed') {
              setCurrentAgent(null);
              setAgentMessage('');
              setPlanData(data.data);
            } else if (data.status === 'error') {
              setError(data.message);
              setCurrentAgent(null);
              setAgentMessage('');
            }
          } catch (e) {
            console.error('Error parsing SSE data:', e);
          }
        }
      }
    }
  } catch (err) {
    setError('Failed to connect to the server. Make sure FastAPI is running.');
    console.error('Error:', err);
    setCurrentAgent(null);
    setAgentMessage('');
  } finally {
    setLoading(false);
  }
};

  const formatOutput = (data) => {
    if (!data || !data.formatted_output) return 'No output available';
    
    const output = data.formatted_output;
    let result = '';
    
    // Add summary
    if (output.summary) {
      result += `PROJECT SUMMARY\n`;
      result += `Total Tasks: ${output.summary.total_tasks}\n`;
      result += `Estimated Duration: ${output.summary.estimated_duration_days} days\n\n`;
    }
    
    // Add markdown output
    if (output.markdown) {
      result += output.markdown;
    }
    
    // Add Mermaid Gantt chart
    if (output.mermaid_gantt) {
      result += '\n\nGANTT CHART (Mermaid.js)\n';
      result += '```mermaid\n';
      result += output.mermaid_gantt;
      result += '\n```';
    }
    
    return result;
  };

  return (
    <div className="container">
      <AgentOverlay 
      currentAgent={currentAgent} 
      message={agentMessage} 
      visible={loading && currentAgent} 
    />

      <h1 className="title">AgentPlanner</h1>

      <div className="card">
        <label htmlFor="project-input" className="label">Enter your project idea:</label>
        <textarea
          id="project-input"
          className="textarea"
          value={projectInput}
          onChange={(e) => setProjectInput(e.target.value)}
          placeholder="e.g., Build a chatbot web app with user authentication, real-time chat, and file sharing capabilities using React and Node.js..."
          disabled={loading}
        />
        <button 
          onClick={handleSubmit} 
          className="button"
          disabled={loading || !projectInput.trim()}
        >
          {loading ? 'Generating Plan...' : 'Generate Plan'}
        </button>
        
        {error && (
          <div className="error-message" style={{ 
            color: 'red', 
            marginTop: '10px', 
            padding: '10px', 
            backgroundColor: '#fee', 
            borderRadius: '4px' 
          }}>
            {error}
          </div>
        )}
      </div>

      {(planData || loading) && (
        <div className="grid">
          <div className="card" style={{ gridColumn: 'span 2' }}>
            <h2 className="subtitle"> Generated Project Plan</h2>
            <div 
              className="output-container"
              style={{
                minHeight: '200px',
                maxHeight: '600px',
                overflow: 'auto',
                backgroundColor: '#f8f9fa',
                padding: '15px',
                borderRadius: '4px',
                border: '1px solid #dee2e6'
              }}
            >
              {loading ? (
                <div>Agents are working on your plan...</div>
              ) : (
                <pre style={{ 
                  whiteSpace: 'pre-wrap', 
                  margin: 0,
                  fontSize: '14px',
                  lineHeight: '1.4'
                }}>
                  {formatOutput(planData)}
                </pre>
              )}
            </div>
          </div>

          {planData && (
            <div className="card workflow-card" style={{ gridColumn: 'span 2' }}>
              <h2 className="subtitle">🕸️ Workflow Visualization</h2>
              <ErrorBoundary>
                <WorkflowGraph planData={planData} />
              </ErrorBoundary>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;