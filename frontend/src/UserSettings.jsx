import React, { useState } from 'react';
import './UserSettings.css';

function UserSettings({ userName, userEmail, onClose, onUpdateSuccess }) {
  const [activeTab, setActiveTab] = useState('username');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Username form state
  const [newUsername, setNewUsername] = useState('');

  // Email form state
  const [newEmail, setNewEmail] = useState('');

  // Password form state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const token = localStorage.getItem('token');

  const handleUpdateUsername = async (e) => {
    e.preventDefault();
    if (!newUsername.trim()) {
      setError('Please enter a new username');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch('http://localhost:5000/api/auth/update-username', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ newUsername })
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess('Username updated successfully!');
        setNewUsername('');
        setTimeout(() => {
          onUpdateSuccess(data.user);
        }, 1500);
      } else {
        setError(data.message || 'Failed to update username');
      }
    } catch (err) {
      setError('Error updating username: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateEmail = async (e) => {
    e.preventDefault();
    if (!newEmail.trim()) {
      setError('Please enter a new email');
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(newEmail)) {
      setError('Please enter a valid email address');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch('http://localhost:5000/api/auth/update-email', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ newEmail })
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess('Email updated successfully!');
        setNewEmail('');
        setTimeout(() => {
          onUpdateSuccess(data.user);
        }, 1500);
      } else {
        setError(data.message || 'Failed to update email');
      }
    } catch (err) {
      setError('Error updating email: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdatePassword = async (e) => {
    e.preventDefault();

    if (!currentPassword || !newPassword || !confirmPassword) {
      setError('Please fill in all password fields');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('New passwords do not match');
      return;
    }

    if (newPassword.length < 6) {
      setError('New password must be at least 6 characters');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch('http://localhost:5000/api/auth/update-password', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ currentPassword, newPassword, confirmPassword })
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess('Password updated successfully!');
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
        setTimeout(() => {
          onUpdateSuccess(null);
        }, 1500);
      } else {
        setError(data.message || 'Failed to update password');
      }
    } catch (err) {
      setError('Error updating password: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCloseModal = () => {
    setError('');
    setSuccess('');
    setNewUsername('');
    setNewEmail('');
    setCurrentPassword('');
    setNewPassword('');
    setConfirmPassword('');
    onClose();
  };

  return (
    <div className="settings-modal-overlay" onClick={handleCloseModal}>
      <div className="settings-modal" onClick={(e) => e.stopPropagation()}>
        <div className="settings-header">
          <h2>User Settings</h2>
          <button className="close-btn" onClick={handleCloseModal}>✕</button>
        </div>

        <div className="settings-tabs">
          <button
            className={`tab-btn ${activeTab === 'username' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('username');
              setError('');
              setSuccess('');
            }}
          >
            Change Username
          </button>
          <button
            className={`tab-btn ${activeTab === 'email' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('email');
              setError('');
              setSuccess('');
            }}
          >
            Change Email
          </button>
          <button
            className={`tab-btn ${activeTab === 'password' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('password');
              setError('');
              setSuccess('');
            }}
          >
            Update Password
          </button>
        </div>

        <div className="settings-content">
          {/* Error Message */}
          {error && (
            <div className="settings-alert error">
              <span className="alert-icon">❌</span>
              <span>{error}</span>
            </div>
          )}

          {/* Success Message */}
          {success && (
            <div className="settings-alert success">
              <span className="alert-icon">✓</span>
              <span>{success}</span>
            </div>
          )}

          {/* Username Tab */}
          {activeTab === 'username' && (
            <form onSubmit={handleUpdateUsername} className="settings-form">
              <div className="form-group">
                <label htmlFor="currentUsername">Current Username</label>
                <input
                  type="text"
                  id="currentUsername"
                  value={userName}
                  disabled
                  className="input-field disabled"
                />
              </div>
              <div className="form-group">
                <label htmlFor="newUsername">New Username</label>
                <input
                  type="text"
                  id="newUsername"
                  value={newUsername}
                  onChange={(e) => setNewUsername(e.target.value)}
                  placeholder="Enter new username"
                  className="input-field"
                  disabled={loading}
                />
              </div>
              <button type="submit" className="submit-btn" disabled={loading}>
                {loading ? 'Updating...' : 'Update Username'}
              </button>
            </form>
          )}

          {/* Email Tab */}
          {activeTab === 'email' && (
            <form onSubmit={handleUpdateEmail} className="settings-form">
              <div className="form-group">
                <label htmlFor="currentEmail">Current Email</label>
                <input
                  type="email"
                  id="currentEmail"
                  value={userEmail}
                  disabled
                  className="input-field disabled"
                />
              </div>
              <div className="form-group">
                <label htmlFor="newEmail">New Email</label>
                <input
                  type="email"
                  id="newEmail"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  placeholder="Enter new email"
                  className="input-field"
                  disabled={loading}
                />
              </div>
              <button type="submit" className="submit-btn" disabled={loading}>
                {loading ? 'Updating...' : 'Update Email'}
              </button>
            </form>
          )}

          {/* Password Tab */}
          {activeTab === 'password' && (
            <form onSubmit={handleUpdatePassword} className="settings-form">
              <div className="form-group">
                <label htmlFor="currentPassword">Current Password</label>
                <input
                  type="password"
                  id="currentPassword"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="Enter current password"
                  className="input-field"
                  disabled={loading}
                />
              </div>
              <div className="form-group">
                <label htmlFor="newPassword">New Password</label>
                <input
                  type="password"
                  id="newPassword"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Enter new password (min 6 characters)"
                  className="input-field"
                  disabled={loading}
                />
              </div>
              <div className="form-group">
                <label htmlFor="confirmPassword">Confirm New Password</label>
                <input
                  type="password"
                  id="confirmPassword"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm new password"
                  className="input-field"
                  disabled={loading}
                />
              </div>
              <button type="submit" className="submit-btn" disabled={loading}>
                {loading ? 'Updating...' : 'Update Password'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

export default UserSettings;
