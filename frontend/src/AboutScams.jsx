import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './AboutScams.css';

function AboutScams() {
  const navigate = useNavigate();
  const [expandedCard, setExpandedCard] = useState(null);
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    return saved ? JSON.parse(saved) : false;
  });

  // Apply dark mode preference from localStorage or Home page
  useEffect(() => {
    localStorage.setItem('darkMode', JSON.stringify(darkMode));
    if (darkMode) {
      document.documentElement.classList.add('dark-mode');
    } else {
      document.documentElement.classList.remove('dark-mode');
    }
  }, [darkMode]);

  const scamTypes = [
    {
      id: 1,
      title: 'Phishing Scams',
      icon: '🎣',
      color: '#dc3545',
      deception: [
        'Fake emails/messages impersonating legitimate banks or companies',
        'Urgent requests to "verify" account information',
        'Links that redirect to fake websites looking identical to real ones',
        'Requests for passwords, credit card numbers, or personal details'
      ],
      tips: [
        'Never click links in unsolicited emails - go directly to the official website',
        'Check sender email addresses carefully for misspellings',
        'Banks never ask for passwords via email or phone',
        'Look for HTTPS and padlock icon in browser address bar',
        'Enable two-factor authentication on accounts'
      ]
    },
    {
      id: 2,
      title: 'Lottery & Prize Scams',
      icon: '🎰',
      color: '#ffc107',
      deception: [
        'Claims you won a prize you never entered',
        'Requires upfront payment to claim fake winnings',
        'Messages say you must act quickly or miss the prize',
        'Uses excitement and urgency to cloud judgment'
      ],
      tips: [
        'Legitimate lotteries never require upfront fees',
        'If you didn\'t enter a contest, you can\'t win it',
        'Never send money to claim prizes',
        'Be skeptical of unexpected winnings',
        'Verify with official lottery websites'
      ]
    },
    {
      id: 3,
      title: 'Romance Scams',
      icon: '💔',
      color: '#e83e8c',
      deception: [
        'Scammers create fake profiles on dating apps',
        'Build emotional relationships over time',
        'Eventually ask for money for "emergencies"',
        'May ask to move conversations to private platforms'
      ],
      tips: [
        'Be cautious of people who quickly declare love',
        'Never send money to people you\'ve never met',
        'Video chat before becoming emotionally invested',
        'Watch for inconsistencies in their stories',
        'Reverse image search profile photos'
      ]
    },
    {
      id: 4,
      title: 'Job Offer Scams',
      icon: '💼',
      color: '#17a2b8',
      deception: [
        'Too-good-to-be-true job postings',
        'High pay for minimal work or experience',
        'Requests for upfront fees for training or equipment',
        'No actual interview or vague job descriptions'
      ],
      tips: [
        'Research the company thoroughly before applying',
        'Never pay for job training or application fees',
        'Conduct video interviews with legitimate companies',
        'Check company reviews on Glassdoor or Indeed',
        'Verify contact information matches official website'
      ]
    },
    {
      id: 5,
      title: 'Tech Support Scams',
      icon: '🖥️',
      color: '#6f42c1',
      deception: [
        'Pop-ups claiming your device is infected',
        'Urgent messages to call a support number',
        'Remote access requests to "fix" problems',
        'Charges for fake software or repairs'
      ],
      tips: [
        'Never call numbers from unsolicited pop-ups',
        'Contact official support through official channels only',
        'Don\'t grant remote access to unknown people',
        'Run antivirus from legitimate security companies',
        'Close pop-ups by closing your browser entirely'
      ]
    },
    {
      id: 6,
      title: 'Wire Transfer Scams',
      icon: '💸',
      color: '#28a745',
      deception: [
        'Urgent requests for wire transfers',
        'Claims that money is needed for emergencies',
        'Impersonates trusted contacts or officials',
        'Creates false urgency to prevent verification'
      ],
      tips: [
        'Always verify requests through official channels',
        'Never wire money based on unsolicited requests',
        'Call the person back using a known phone number',
        'Wire transfers are difficult to reverse - be cautious',
        'Legitimate businesses use formal payment methods'
      ]
    },
    {
      id: 7,
      title: 'Advance Fee Scams',
      icon: '💰',
      color: '#fd7e14',
      deception: [
        'Promises of loans, grants, or inheritance',
        'Claims you need to pay upfront fees first',
        'Says fees are for processing or administration',
        'Promises guaranteed approval despite poor credit'
      ],
      tips: [
        'Legitimate lenders don\'t guarantee approval',
        'Never pay fees upfront for loans or grants',
        'Government grants are never advertised via email',
        'Research lenders through official regulatory websites',
        'Read all terms and conditions carefully'
      ]
    },
    {
      id: 8,
      title: 'Invoice & Payment Scams',
      icon: '📄',
      color: '#20c997',
      deception: [
        'Fake invoices that look legitimate',
        'Requests for payment to wrong accounts',
        'Impersonates known vendors or contractors',
        'Exploits busy professionals who don\'t verify'
      ],
      tips: [
        'Verify invoices through official channels',
        'Check sender email addresses carefully',
        'Call the company before processing payments',
        'Implement payment verification procedures',
        'Keep records of all official invoices'
      ]
    }
  ];

  const generalTips = [
    {
      title: 'Trust Your Instincts',
      icon: '🎯',
      description: 'If something feels wrong or too good to be true, it probably is. Don\'t ignore red flags.'
    },
    {
      title: 'Verify Everything',
      icon: '✅',
      description: 'Always verify requests independently using official contact information, not provided details.'
    },
    {
      title: 'Protect Personal Information',
      icon: '🔒',
      description: 'Never share passwords, PINs, SSN, or financial information via email or phone.'
    },
    {
      title: 'Use Strong Passwords',
      icon: '🔐',
      description: 'Create unique, complex passwords for each account and use password managers.'
    },
    {
      title: 'Enable 2FA',
      icon: '📱',
      description: 'Two-factor authentication adds an extra security layer to protect your accounts.'
    },
    {
      title: 'Check URLs Carefully',
      icon: '🌐',
      description: 'Hover over links to see the actual URL before clicking. Watch for misspelled domain names.'
    },
    {
      title: 'Update Software',
      icon: '🔄',
      description: 'Keep your operating system, browser, and antivirus software updated regularly.'
    },
    {
      title: 'Use Secure Networks',
      icon: '🛡️',
      description: 'Avoid public WiFi for sensitive transactions. Use VPN if necessary.'
    }
  ];

  const redFlags = [
    'Urgent or threatening language',
    'Requests for immediate payment',
    'Too good to be true offers',
    'Spelling and grammar errors',
    'Unknown sender or email address',
    'Requests for personal information',
    'Pressure to make decisions quickly',
    'Suspicious links or attachments',
    'Unusual payment methods',
    'Unsolicited contact'
  ];

  return (
    <div className="about-scams-container">
      {/* Header */}
      <header className="about-header">
        <div className="header-content">
          <button className="back-btn" onClick={() => navigate('/home')}>
            ← Back to Home
          </button>
          <div className="header-title">
            <h1>🛡️ About Financial Scams</h1>
            <p>Learn how to identify, understand, and protect yourself from common scams</p>
          </div>
          <button 
            className="theme-toggle-btn-about"
            onClick={() => setDarkMode(!darkMode)}
            title={darkMode ? 'Light Mode' : 'Dark Mode'}
          >
            {darkMode ? '☀️' : '🌙'}
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="about-main">
        {/* Introduction Section */}
        <section className="intro-section">
          <div className="intro-card">
            <h2>What Are Financial Scams?</h2>
            <p>
              Financial scams are fraudulent schemes designed to trick people into giving away money or personal 
              information. Scammers use psychological manipulation, urgency, and deception to exploit victims' 
              trust and vulnerabilities.
            </p>
            <div className="key-stats">
              <div className="stat">
                <strong>💬 Millions</strong>
                <p>People fall victim annually</p>
              </div>
              <div className="stat">
                <strong>💵 Billions</strong>
                <p>Lost to scams every year</p>
              </div>
              <div className="stat">
                <strong>📱 24/7</strong>
                <p>Scammers are always active</p>
              </div>
            </div>
          </div>
        </section>

        {/* Red Flags Section */}
        <section className="red-flags-section">
          <h2>🚨 Common Red Flags</h2>
          <p className="section-subtitle">Watch out for these warning signs in any communication</p>
          <div className="red-flags-grid">
            {redFlags.map((flag, idx) => (
              <div key={idx} className="red-flag-item">
                <span className="flag-icon">⚠️</span>
                <span className="flag-text">{flag}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Scam Types Section */}
        <section className="scam-types-section">
          <h2>📚 Types of Financial Scams</h2>
          <p className="section-subtitle">Understand common scam tactics and how to protect yourself</p>
          
          <div className="scam-cards-grid">
            {scamTypes.map((scam) => (
              <div 
                key={scam.id} 
                className={`scam-card ${expandedCard === scam.id ? 'expanded' : ''}`}
                style={{ borderTopColor: scam.color }}
              >
                <div 
                  className="scam-header"
                  onClick={() => setExpandedCard(expandedCard === scam.id ? null : scam.id)}
                >
                  <div className="scam-title-group">
                    <span className="scam-icon" style={{ fontSize: '2rem' }}>
                      {scam.icon}
                    </span>
                    <h3>{scam.title}</h3>
                  </div>
                  <span className="expand-icon">
                    {expandedCard === scam.id ? '▼' : '▶'}
                  </span>
                </div>

                {expandedCard === scam.id && (
                  <div className="scam-content">
                    <div className="scam-section">
                      <h4>How They Deceive:</h4>
                      <ul className="deceive-list">
                        {scam.deception.map((item, idx) => (
                          <li key={idx}>
                            <span className="deceive-icon">🎯</span>
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="scam-section">
                      <h4>Tips to Avoid:</h4>
                      <ul className="tips-list">
                        {scam.tips.map((tip, idx) => (
                          <li key={idx}>
                            <span className="tip-icon">✓</span>
                            {tip}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* General Tips Section */}
        <section className="general-tips-section">
          <h2>💡 General Safety Tips</h2>
          <p className="section-subtitle">Best practices to protect yourself from all types of scams</p>
          
          <div className="tips-grid">
            {generalTips.map((tip, idx) => (
              <div key={idx} className="tip-card">
                <div className="tip-icon-large">{tip.icon}</div>
                <h3>{tip.title}</h3>
                <p>{tip.description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* What to Do Section */}
        <section className="action-section">
          <h2>🆘 What to Do If You're Targeted</h2>
          
          <div className="action-cards">
            <div className="action-card warning">
              <h3>Immediate Steps</h3>
              <ol className="action-list">
                <li>Stop communication with the scammer immediately</li>
                <li>Don't send any money or personal information</li>
                <li>Don't click any links or download anything</li>
                <li>Save all evidence (messages, emails, screenshots)</li>
                <li>Document the scammer's contact information</li>
              </ol>
            </div>

            <div className="action-card critical">
              <h3>If Money Was Sent</h3>
              <ol className="action-list">
                <li>Contact your bank or payment service immediately</li>
                <li>Report the fraud to your financial institution</li>
                <li>Ask them to cancel any pending transfers</li>
                <li>File a report with your local police</li>
                <li>Report to the FTC at ReportFraud.ftc.gov</li>
              </ol>
            </div>

            <div className="action-card success">
              <h3>Reporting Resources</h3>
              <ul className="resource-list">
                <li>🇺🇸 FTC Complaint Assistant: reportfraud.ftc.gov</li>
                <li>📱 FBI IC3: ic3.gov</li>
                <li>🏦 Your Bank/Credit Card Company</li>
                <li>📞 Local Police Department</li>
                <li>💳 Credit Bureaus (Equifax, Experian, TransUnion)</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Resources Section */}
        <section className="resources-section">
          <h2>📚 Additional Resources</h2>
          <div className="resources-grid">
            <div className="resource-card">
              <h3>🛡️ Government Resources</h3>
              <ul>
                <li>Federal Trade Commission (FTC.gov)</li>
                <li>FBI's Internet Crime Complaint Center (IC3)</li>
                <li>Consumer Finance Protection Bureau (CFPB)</li>
                <li>Better Business Bureau (BBB)</li>
              </ul>
            </div>

            <div className="resource-card">
              <h3>🔐 Security Tools</h3>
              <ul>
                <li>Antivirus software (Norton, McAfee, Kaspersky)</li>
                <li>Password managers (LastPass, 1Password)</li>
                <li>VPN services for public WiFi</li>
                <li>Email verification tools</li>
              </ul>
            </div>

            <div className="resource-card">
              <h3>📖 Education</h3>
              <ul>
                <li>Cybersecurity courses online</li>
                <li>Bank security guides</li>
                <li>Consumer protection articles</li>
                <li>Scam alert newsletters</li>
              </ul>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="cta-section">
          <h2>Stay Protected</h2>
          <p>
            Use our Financial Scam Detection tool to analyze suspicious messages and emails. 
            Our AI-powered system helps identify potential scams before you become a victim.
          </p>
          <button className="cta-btn" onClick={() => navigate('/home')}>
            🚀 Analyze a Message Now
          </button>
        </section>
      </main>

      {/* Footer */}
      <footer className="about-footer">
        <p>&copy; 2024 Financial Scam Detection. Protecting you from fraud.</p>
        <p className="disclaimer">
          This information is for educational purposes. Always contact official authorities for legal advice.
        </p>
      </footer>
    </div>
  );
}

export default AboutScams;
