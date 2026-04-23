import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import UserSettings from './UserSettings';
import './Home.css';

function Home() {
  const navigate = useNavigate();
  const [text, setText] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [userName, setUserName] = useState('User');
  const [userInitial, setUserInitial] = useState('U');
  const [showDropdown, setShowDropdown] = useState(false);
  const [wordImportance, setWordImportance] = useState(null);
  const [explainLoading, setExplainLoading] = useState(false);
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    return saved ? JSON.parse(saved) : false;
  });
  const [showSettings, setShowSettings] = useState(false);

  // Fetch user info and history on component mount
  useEffect(() => {
    fetchUserInfo();
    fetchSearchHistory();
  }, []);

  // Save dark mode preference to localStorage and apply to document
  useEffect(() => {
    localStorage.setItem('darkMode', JSON.stringify(darkMode));
    if (darkMode) {
      document.documentElement.classList.add('dark-mode');
    } else {
      document.documentElement.classList.remove('dark-mode');
    }
  }, [darkMode]);

  const fetchUserInfo = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await fetch('http://localhost:5000/api/auth/me', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();
      if (data.user) {
        const name = data.user.username || data.user.email || 'User';
        setUserName(name);
        setUserInitial(name.charAt(0).toUpperCase());
        localStorage.setItem('userEmail', data.user.email);
      }
    } catch (err) {
      console.error('Failed to fetch user info:', err);
    }
  };

  const fetchSearchHistory = async () => {
    try {
      setHistoryLoading(true);
      const token = localStorage.getItem('token');
      
      if (!token) return;

      const response = await fetch('http://localhost:5000/api/search-history?limit=5', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();
      if (data.success) {
        setHistory(data.data);
      }
    } catch (err) {
      console.error('Failed to fetch search history:', err);
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    window.location.href = '/login';
  };

  const handleSettingsClose = () => {
    setShowSettings(false);
    setShowDropdown(false);
  };

  const handleUpdateSuccess = (updatedUser) => {
    if (updatedUser) {
      setUserName(updatedUser.username);
      setUserInitial(updatedUser.username.charAt(0).toUpperCase());
      localStorage.setItem('userEmail', updatedUser.email);
    }
    setTimeout(() => {
      handleSettingsClose();
    }, 1000);
  };

  const handleAnalyze = async () => {
    if (!text.trim()) {
      setError('Please enter some text to analyze');
      return;
    }

    setLoading(true);
    setExplainLoading(true);
    setError('');
    setResult(null);
    setWordImportance(null);

    try {
      const response = await fetch('http://localhost:5001/api/combined-analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Failed to analyze text');
      }

      // Check if input is primarily a URL
      const trimmedText = text.trim();
      const isUrlInput = trimmedText.match(/^https?:\/\//i);
      
      let transformedResult = {
        classification: data.summary?.text_classification || 'unknown',
        confidence: data.text_analysis?.confidence || 0,
        scam_score: calculateScamScore(data.text_analysis?.classification, data.text_analysis?.confidence),
        insights: data.text_analysis?.insights || [],
        riskLevel: data.risk_assessment?.risk_level,
        urlAnalysis: data.url_analysis,
        textAnalysis: data.text_analysis
      };

      // If input is a URL and URL analysis says it's safe, override the text analysis score
      if (isUrlInput && data.url_analysis?.urls && data.url_analysis.urls.length > 0) {
        const firstUrl = data.url_analysis.urls[0];
        if (firstUrl.classification === 'legitimate') {
          // URL is safe, so override text analysis with low scam score
          transformedResult.classification = 'not_a_scam';
          transformedResult.scam_score = 0.01; // 1% - safe
          transformedResult.insights = ['✓ URL is verified as legitimate'];
          transformedResult.riskLevel = 'LOW';
        }
      }

      setResult(transformedResult);
      
      // Fetch SHAP explanation (word importance)
      try {
        console.log('Fetching word importance...');
        const explainResponse = await fetch('http://localhost:5001/api/explain', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            text: text,
            top_k: 8
          })
        });

        if (explainResponse.ok) {
          const explainData = await explainResponse.json();
          if (explainData.explanation?.word_importance && explainData.explanation.word_importance.length > 0) {
            console.log('Word importance received:', explainData.explanation.word_importance);
            setWordImportance(explainData.explanation.word_importance);
          }
        } else {
          console.warn('Explanation endpoint returned:', explainResponse.status);
        }
      } catch (explainErr) {
        console.warn('Word importance not available:', explainErr.message);
      }

      // Save to history
      const token = localStorage.getItem('token');
      if (token) {
        await fetch('http://localhost:5000/api/search-history', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            text: text,
            classification: transformedResult.classification,
            confidence: transformedResult.confidence,
            insights: transformedResult.insights
          })
        });
        fetchSearchHistory();
      }
    } catch (err) {
      setError(err.message || 'Failed to connect to ML service');
    } finally {
      setLoading(false);
      setExplainLoading(false);
    }
  };

  const handleClear = () => {
    setText('');
    setResult(null);
    setError('');
  };

  const getScamCategory = (text) => {
    const lower = text.toLowerCase();
    if (lower.includes('bank') || lower.includes('payment')) return 'Banking Phishing';
    if (lower.includes('amazon') || lower.includes('ebay')) return 'E-commerce Scam';
    if (lower.includes('verify') || lower.includes('confirm')) return 'Verification Scam';
    if (lower.includes('prize') || lower.includes('reward')) return 'Lottery Scam';
    return 'Financial Scam';
  };

  const getRiskColor = (riskLevel) => {
    switch (riskLevel?.toUpperCase()) {
      case 'HIGH':
        return '#dc3545';
      case 'MEDIUM':
        return '#ffc107';
      case 'LOW':
        return '#28a745';
      default:
        return '#6c757d';
    }
  };

  return (
    <div className="home-container-new">
      {/* Header */}
      <header className="header-new">
        <div className="header-left">
          <div className="logo-section">
            <div className="logo-icon">🛡️</div>
            <div className="logo-text">
              <h1>Financial Scam Detection</h1>
            </div>
          </div>
        </div>

        <nav className="header-nav">
          <button className="nav-link">Dashboard</button>
          <button className="nav-link" onClick={() => navigate('/about-scams')}>About Scams</button>
        </nav>

        <div className="header-right">
          <button 
            className="theme-toggle-btn"
            onClick={() => setDarkMode(!darkMode)}
            title={darkMode ? 'Light Mode' : 'Dark Mode'}
          >
            {darkMode ? '☀️' : '🌙'}
          </button>
          <div className="user-profile" onClick={() => setShowDropdown(!showDropdown)}>
            <div className="user-initial">{userInitial}</div>
            <div className="user-dropdown">
              <span className="user-name">Welcome, {userName.split(' ')[0]} ▼</span>
              {showDropdown && (
                <div className="dropdown-menu">
                  <button className="dropdown-item">Profile</button>
                  <button className="dropdown-item" onClick={() => setShowSettings(true)}>Settings</button>
                  <button className="dropdown-item" onClick={handleLogout}>Logout</button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content-new">
        {/* Hero Section */}
        <section className="hero-section-new">
          <div className="hero-left">
            <h2>Is This Message a Scam?</h2>
            <p>Enter a suspicious message below to check if it's a scam.</p>

            <div className="input-group-new">
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder='e.g., "Your account is locked, click this link to verify your details..."'
                className="textarea-new"
                disabled={loading}
              />
              <div className="button-group-new">
                <button
                  onClick={handleAnalyze}
                  className="analyze-btn-new"
                  disabled={loading || !text.trim()}
                >
                  {loading ? 'Analyzing...' : 'Analyze'}
                </button>
              </div>
            </div>

            {error && (
              <div className="error-box">
                <span className="error-icon">❌</span>
                <div>
                  <strong>Error</strong>
                  <p>{error}</p>
                </div>
              </div>
            )}

            {result && (
              <div className={`result-box result-${result.riskLevel?.toLowerCase()}`}>
                <div className="result-header">
                  <div className="result-icon">⚠️</div>
                  <div className="result-title">
                    <strong>{getMainResultTitle(result.scam_score)}</strong>
                  </div>
                </div>

                {result.insights && result.insights.length > 0 && (
                  <div className="result-detail">
                    <strong>Reason:</strong>
                    <p>{result.insights[0]}</p>
                  </div>
                )}

                <div className="result-detail">
                  <strong>Category:</strong>
                  <p>{getScamCategory(text)}</p>
                </div>

                <div className="result-detail">
                  <strong>Scam Risk Score:</strong>
                  <p>{Math.round(result.scam_score * 100)}%</p>
                </div>

                <div className="result-detail">
                  <strong>Advice:</strong>
                  <p>{getAdviceText(result.scam_score)}</p>
                </div>

                {/* URL Analysis */}
                {result.urlAnalysis?.urls && result.urlAnalysis.urls.length > 0 && (
                  <div className="url-risks">
                    {result.urlAnalysis.urls.map((url, idx) => (
                      <div key={idx} className="url-risk-item">
                        <span>🔗 URL Check:</span>
                        <strong>
                          {url.classification === 'phishing' ? 'Phishing Link Detected' : 'Link Appears Safe'}
                        </strong>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Safety Tips */}
            <div className="safety-tips-section">
              <div className="safety-header">
                <div className="safety-icon">ℹ️</div>
                <h3>Safety Tips</h3>
              </div>
              <div className="safety-grid">
                <div className="safety-item">
                  <div className="safety-item-icon">⏰</div>
                  <h4>Be Cautious of Urgent Requests</h4>
                  <p>Scammers often create a sense of urgency.</p>
                </div>
                <div className="safety-item">
                  <div className="safety-item-icon">🔒</div>
                  <h4>Avoid Clicking Links</h4>
                  <p>Check URLs carefully before clicking.</p>
                </div>
              </div>
            </div>
          </div>

          {/* Right Panel - Threat Analysis */}
          <div className="threat-panel">
            <h3>Threat Analysis</h3>

            {result ? (
              <>
                {/* Scam Likelihood */}
                <div className="threat-item">
                  <div className="threat-label">
                    <span className="threat-icon">🚨</span>
                    <span>Scam Likelihood</span>
                  </div>
                  <div className="threat-bar">
                    <div 
                      className="threat-fill" 
                      style={{ 
                        width: `${result.scam_score * 100}%`,
                        backgroundColor: getRiskColor(result.riskLevel)
                      }}
                    />
                  </div>
                  <div className="threat-percentage">
                    {Math.round(result.scam_score * 100)}% {getThreatLabel(result.scam_score)}
                  </div>
                </div>

                {/* URL Check */}
                {result.urlAnalysis?.urls && result.urlAnalysis.urls.length > 0 && (
                  <div className="threat-item">
                    <div className="threat-label">
                      <span className="threat-icon">🔗</span>
                      <span>URL Check</span>
                    </div>
                    <div className="threat-value">
                      {result.urlAnalysis.urls[0].classification === 'phishing' 
                        ? 'Phishing Link Detected' 
                        : 'No Phishing Detected'}
                    </div>
                  </div>
                )}

                {/* Scam Type */}
                <div className="threat-item">
                  <div className="threat-label">
                    <span className="threat-icon">🏷️</span>
                    <span>Scam Type</span>
                  </div>
                  <div className="threat-value">
                    {getScamCategory(text)}
                  </div>
                </div>
              </>
            ) : (
              <div className="threat-empty">
                <p>Analyze a message to see threat details</p>
              </div>
            )}
          </div>
        </section>

        {/* Recent Checks */}
        {!historyLoading && history.length > 0 && (
          <section className="recent-checks">
            <h3>Recent Checks</h3>
            <div className="recent-table">
              <div className="table-header">
                <div className="table-col-message">Message</div>
                <div className="table-col-result">Result</div>
                <div className="table-col-type">Type</div>
              </div>
              {history.map((item) => (
                <div key={item._id} className="table-row">
                  <div className="table-col-message">
                    {item.text.substring(0, 50)}...
                  </div>
                  <div className="table-col-result">
                    <span className={`result-badge result-${item.classification}`}>
                      {item.classification === 'scam' ? 'Scam' : item.classification === 'suspicious' ? 'Suspicious' : 'Safe'}
                    </span>
                  </div>
                  <div className="table-col-type">
                    {getScamCategory(item.text)}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
      </main>

      {/* User Settings Modal */}
      {showSettings && (
        <UserSettings 
          userName={userName}
          userEmail={localStorage.getItem('userEmail') || ''}
          onClose={handleSettingsClose}
          onUpdateSuccess={handleUpdateSuccess}
        />
      )}
    </div>
  );
}

function getRiskLevelText(riskLevel) {
  switch (riskLevel?.toUpperCase()) {
    case 'HIGH':
      return 'High Risk';
    case 'MEDIUM':
      return 'Medium Risk';
    case 'LOW':
      return 'Low Risk';
    default:
      return 'Unknown';
  }
}

function calculateRiskFromScore(score) {
  const percentage = Math.round(score * 100);
  if (percentage >= 70) {
    return 'High Risk';
  } else if (percentage >= 40) {
    return 'Medium Risk';
  } else {
    return 'Low Risk';
  }
}

function calculateScamScore(classification, confidence) {
  // Transform the confidence based on classification
  // Backend returns: 'not_a_scam', 'suspicious', 'scam'
  if (!classification || confidence === null && confidence !== 0) return 0;
  
  classification = classification.toLowerCase().trim();
  confidence = parseFloat(confidence) || 0;
  
  // Ensure confidence is between 0 and 1
  if (confidence > 1) {
    confidence = confidence / 100; // If it's 0-100, convert to 0-1
  }
  
  if (classification === 'not_a_scam' || classification === 'safe') {
    // Safe message: invert the confidence to get scam score (LOW RISK: 0-40%)
    // If model is 95% confident it's safe, scam_score should be 5%
    return Math.max(0, Math.min(0.4, 1 - confidence));
  } else if (classification === 'suspicious') {
    // Suspicious: map to MEDIUM RISK range (40-70%)
    // Spread confidence across the medium risk range
    // If confidence is 0.5, scam_score = 0.55 (55%)
    // If confidence is 0.99, scam_score = 0.695 (69.5%)
    return Math.max(0.4, Math.min(0.7, 0.4 + confidence * 0.3));
  } else if (classification === 'scam') {
    // Scam: HIGH RISK range (70-100%)
    // If model is 95% confident it's scam, scam_score should be 95%
    return Math.max(0.7, Math.min(1, confidence));
  } else {
    return 0;
  }
}

function getAdviceText(scamScore) {
  const percentage = Math.round(scamScore * 100);
  
  if (percentage >= 70) {
    return '🚨 HIGH RISK: Do not click any links or download anything. Contact your bank/service immediately.';
  } else if (percentage >= 40) {
    return '⚠️ MEDIUM RISK: Be cautious. Don\'t click suspicious links. Verify the sender before taking action.';
  } else {
    return '✓ LOW RISK: This message appears safe, but always stay vigilant against phishing attempts.';
  }
}

function getMainResultTitle(scamScore) {
  const percentage = Math.round(scamScore * 100);
  
  if (percentage > 70) {
    return 'High Risk: Scam Detected!';
  } else if (percentage >= 40) {
    return 'Medium Risk: Suspicious';
  } else {
    return 'Low Risk: Safe';
  }
}

function getThreatLabel(scamScore) {
  // Convert scam score to a threat label based on risk level
  const percentage = Math.round(scamScore * 100);
  
  if (percentage > 70) {
    return 'Scam';
  } else if (percentage >= 40) {
    return 'Suspicious';
  } else {
    return 'Safe';
  }
}

function getClassificationLabel(classification) {
  if (!classification) return 'Unknown';
  
  classification = classification.toLowerCase();
  
  if (classification === 'scam') {
    return 'Scam';
  } else if (classification === 'suspicious') {
    return 'Suspicious';
  } else {
    return 'Not Scam';
  }
}

export default Home;
