/**
 * Account settings and profile management route
 */

import { useState } from 'react';
import { useAuth } from '../context/AuthContext';

export const AccountRoute = () => {
  const { user, updateUserProfile, loading } = useAuth();
  const [editing, setEditing] = useState(false);
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [examDate, setExamDate] = useState(user?.exam_date || '');
  const [saveStatus, setSaveStatus] = useState('');

  if (!user) {
    return (
      <div className="stack" data-page="account">
        <section className="card">
          <p>Loading user profile...</p>
        </section>
      </div>
    );
  }

  const handleSave = async () => {
    try {
      setSaveStatus('Saving...');
      await updateUserProfile({
        full_name: fullName,
        exam_date: examDate || null,
      });
      setSaveStatus('Saved successfully!');
      setEditing(false);
      setTimeout(() => setSaveStatus(''), 3000);
    } catch (err) {
      setSaveStatus(err instanceof Error ? err.message : 'Failed to save');
    }
  };

  const handleCancel = () => {
    setFullName(user.full_name);
    setExamDate(user.exam_date || '');
    setEditing(false);
    setSaveStatus('');
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Not set';
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <div className="stack" data-page="account">
      <section className="card stack">
        <header className="stack">
          <h1>Account Settings</h1>
          <p>
            Manage your learner profile, adjust notifications, and control connected integrations.
          </p>
        </header>

        {saveStatus && (
          <div className={`message ${saveStatus.includes('success') ? 'success' : 'error'}`}>
            {saveStatus}
          </div>
        )}

        <div className="profile-section">
          <h2>Profile Information</h2>

          {!editing ? (
            <div className="profile-display">
              <div className="profile-row">
                <strong>Name:</strong>
                <span>{user.full_name}</span>
              </div>
              <div className="profile-row">
                <strong>Email:</strong>
                <span>{user.email}</span>
              </div>
              <div className="profile-row">
                <strong>Exam Date:</strong>
                <span>{formatDate(user.exam_date)}</span>
              </div>
              <div className="profile-row">
                <strong>Subscription:</strong>
                <span>{user.subscription_tier}</span>
              </div>
              <div className="profile-row">
                <strong>Member since:</strong>
                <span>{formatDate(user.created_at)}</span>
              </div>
              <div className="profile-row">
                <strong>Last login:</strong>
                <span>{formatDate(user.last_login)}</span>
              </div>

              <button
                type="button"
                onClick={() => setEditing(true)}
                className="primary-button"
              >
                Edit Profile
              </button>
            </div>
          ) : (
            <div className="profile-edit">
              <div className="form-group">
                <label htmlFor="fullName">
                  Full Name
                  <input
                    id="fullName"
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    disabled={loading}
                  />
                </label>
              </div>

              <div className="form-group">
                <label htmlFor="email">
                  Email Address
                  <input
                    id="email"
                    type="email"
                    value={user.email}
                    disabled
                    title="Email cannot be changed"
                  />
                </label>
                <small>Email address cannot be changed</small>
              </div>

              <div className="form-group">
                <label htmlFor="examDate">
                  USMLE Step 1 Exam Date
                  <input
                    id="examDate"
                    type="date"
                    value={examDate ? new Date(examDate).toISOString().split('T')[0] : ''}
                    onChange={(e) => setExamDate(e.target.value)}
                    disabled={loading}
                  />
                </label>
              </div>

              <div className="button-group">
                <button
                  type="button"
                  onClick={handleSave}
                  className="primary-button"
                  disabled={loading}
                >
                  Save Changes
                </button>
                <button
                  type="button"
                  onClick={handleCancel}
                  className="secondary-button"
                  disabled={loading}
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="profile-section">
          <h2>Subscription</h2>
          <p>
            Current plan: <strong>{user.subscription_tier}</strong>
          </p>
          {user.subscription_end && (
            <p>Valid until: {formatDate(user.subscription_end)}</p>
          )}
          <p>
            <em>Subscription management is coming soon. Contact support to update your subscription.</em>
          </p>
        </div>
      </section>
    </div>
  );
};
