import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import * as analyticsApi from '../api/userAnalytics';
import '../styles/analytics.css';

export function UserAnalyticsDashboard() {
  const { token } = useAuth();
  const [analytics, setAnalytics] = useState<analyticsApi.UserAnalytics | null>(null);
  const [percentile, setPercentile] = useState<analyticsApi.PercentileRanking | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState(30);

  useEffect(() => {
    loadAnalytics();
  }, [token, timeRange]);

  const loadAnalytics = async () => {
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const [analyticsData, percentileData] = await Promise.all([
        analyticsApi.getUserAnalytics(timeRange, token),
        analyticsApi.getPercentileRanking(token),
      ]);

      setAnalytics(analyticsData);
      setPercentile(percentileData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="analytics-container">
        <div className="empty-state">
          <h2>Analytics Not Available</h2>
          <p>Please log in to view your performance analytics.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="analytics-container">
        <div className="loading-state">Loading analytics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analytics-container">
        <div className="error-state">
          <p>Error: {error}</p>
          <button className="btn-primary" onClick={loadAnalytics}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!analytics || analytics.total_attempts === 0) {
    return (
      <div className="analytics-container">
        <div className="empty-state">
          <h2>No Data Yet</h2>
          <p>Start answering questions to see your performance analytics!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="analytics-container">
      <div className="analytics-header">
        <div>
          <h1>Performance Analytics</h1>
          <p>Track your progress and identify areas for improvement</p>
        </div>
        <div className="time-range-selector">
          <label>Time Range:</label>
          <select value={timeRange} onChange={(e) => setTimeRange(Number(e.target.value))}>
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
            <option value={365}>Last year</option>
          </select>
        </div>
      </div>

      {/* Overall Statistics */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📊</div>
          <div className="stat-content">
            <div className="stat-label">Accuracy</div>
            <div
              className="stat-value"
              style={{ color: analyticsApi.getAccuracyColor(analytics.accuracy_percent) }}
            >
              {analytics.accuracy_percent.toFixed(1)}%
            </div>
            <div className="stat-detail">
              {analytics.correct_attempts} / {analytics.total_attempts} correct
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">📝</div>
          <div className="stat-content">
            <div className="stat-label">Questions Attempted</div>
            <div className="stat-value">{analytics.total_attempts}</div>
            <div className="stat-detail">{analytics.questions_attempted_count} unique</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">⏱️</div>
          <div className="stat-content">
            <div className="stat-label">Avg Time</div>
            <div className="stat-value">{analyticsApi.formatTime(analytics.average_time_seconds)}</div>
            <div className="stat-detail">
              {analyticsApi.formatHours(analytics.total_study_time_hours)} total
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">🔥</div>
          <div className="stat-content">
            <div className="stat-label">Current Streak</div>
            <div className="stat-value">{analytics.current_streak_days}</div>
            <div className="stat-detail">days</div>
          </div>
        </div>

        {percentile && percentile.total_users > 1 && (
          <div className="stat-card">
            <div className="stat-icon">📈</div>
            <div className="stat-content">
              <div className="stat-label">Overall Percentile</div>
              <div className="stat-value">{percentile.overall_percentile.toFixed(0)}th</div>
              <div className="stat-detail">
                {analyticsApi.getPercentileLabel(percentile.overall_percentile)}
              </div>
            </div>
          </div>
        )}

        <div className="stat-card">
          <div className="stat-icon">✅</div>
          <div className="stat-content">
            <div className="stat-label">Assessments</div>
            <div className="stat-value">{analytics.assessments_completed}</div>
            <div className="stat-detail">completed</div>
          </div>
        </div>
      </div>

      {/* Subject Performance */}
      {analytics.by_subject.length > 0 && (
        <div className="analytics-section">
          <h2>Performance by Subject</h2>
          <div className="performance-table">
            <table>
              <thead>
                <tr>
                  <th>Subject</th>
                  <th>Attempts</th>
                  <th>Correct</th>
                  <th>Accuracy</th>
                  <th>Avg Time</th>
                  <th>Trend</th>
                </tr>
              </thead>
              <tbody>
                {analytics.by_subject.map((subject) => (
                  <tr key={subject.subject}>
                    <td>
                      <strong>{subject.subject}</strong>
                    </td>
                    <td>{subject.total_attempts}</td>
                    <td>{subject.correct}</td>
                    <td>
                      <div
                        className="accuracy-badge"
                        style={{
                          backgroundColor: analyticsApi.getAccuracyColor(subject.accuracy_percent),
                        }}
                      >
                        {subject.accuracy_percent.toFixed(1)}%
                      </div>
                    </td>
                    <td>{analyticsApi.formatTime(subject.average_time_seconds)}</td>
                    <td>
                      <div className="progress-bar-mini">
                        <div
                          className="progress-fill-mini"
                          style={{ width: `${subject.accuracy_percent}%` }}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* System Performance */}
      {analytics.by_system.length > 0 && (
        <div className="analytics-section">
          <h2>Performance by Organ System</h2>
          <div className="performance-table">
            <table>
              <thead>
                <tr>
                  <th>System</th>
                  <th>Attempts</th>
                  <th>Correct</th>
                  <th>Accuracy</th>
                  <th>Avg Time</th>
                  <th>Trend</th>
                </tr>
              </thead>
              <tbody>
                {analytics.by_system.map((system) => (
                  <tr key={system.system}>
                    <td>
                      <strong>{system.system}</strong>
                    </td>
                    <td>{system.total_attempts}</td>
                    <td>{system.correct}</td>
                    <td>
                      <div
                        className="accuracy-badge"
                        style={{
                          backgroundColor: analyticsApi.getAccuracyColor(system.accuracy_percent),
                        }}
                      >
                        {system.accuracy_percent.toFixed(1)}%
                      </div>
                    </td>
                    <td>{analyticsApi.formatTime(system.average_time_seconds)}</td>
                    <td>
                      <div className="progress-bar-mini">
                        <div
                          className="progress-fill-mini"
                          style={{ width: `${system.accuracy_percent}%` }}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Difficulty Breakdown */}
      {analytics.by_difficulty.length > 0 && (
        <div className="analytics-section">
          <h2>Performance by Difficulty</h2>
          <div className="difficulty-grid">
            {analytics.by_difficulty.map((diff) => (
              <div key={diff.difficulty} className="difficulty-card">
                <div className="difficulty-header">{diff.difficulty}</div>
                <div className="difficulty-stats">
                  <div className="difficulty-accuracy">
                    <span
                      className="accuracy-circle"
                      style={{
                        backgroundColor: analyticsApi.getAccuracyColor(diff.accuracy_percent),
                      }}
                    >
                      {diff.accuracy_percent.toFixed(0)}%
                    </span>
                  </div>
                  <div className="difficulty-details">
                    <div>
                      {diff.correct} / {diff.total_attempts} correct
                    </div>
                    <div className="text-muted">{diff.total_attempts} attempts</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Weak Areas */}
      {analytics.weak_areas.length > 0 && (
        <div className="analytics-section weak-areas-section">
          <h2>⚠️ Areas Needing Improvement</h2>
          <p className="section-description">
            Focus your study time on these topics to improve your overall performance
          </p>
          <div className="weak-areas-grid">
            {analytics.weak_areas.map((area) => (
              <div key={`${area.category}-${area.name}`} className="weak-area-card">
                <div className="weak-area-header">
                  <span className="weak-area-category">{area.category}</span>
                  <span className="weak-area-rank">#{area.rank}</span>
                </div>
                <div className="weak-area-name">{area.name}</div>
                <div className="weak-area-stats">
                  <div className="weak-area-accuracy" style={{ color: '#ef4444' }}>
                    {area.accuracy_percent.toFixed(1)}% accuracy
                  </div>
                  <div className="weak-area-attempts">{area.total_attempts} attempts</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Daily Performance Chart */}
      {analytics.daily_performance.length > 0 && (
        <div className="analytics-section">
          <h2>Daily Activity</h2>
          <div className="daily-chart">
            {analytics.daily_performance.map((day) => {
              const maxHeight = 100;
              const heightPercent = Math.min(
                (day.total_attempts / Math.max(...analytics.daily_performance.map((d) => d.total_attempts))) * maxHeight,
                maxHeight
              );

              return (
                <div key={day.date} className="daily-bar-container">
                  <div
                    className="daily-bar"
                    style={{
                      height: `${heightPercent}%`,
                      backgroundColor: analyticsApi.getAccuracyColor(day.accuracy_percent),
                    }}
                    title={`${day.date}: ${day.total_attempts} questions, ${day.accuracy_percent.toFixed(1)}% accuracy`}
                  />
                  <div className="daily-label">
                    {new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Percentile Rankings */}
      {percentile && percentile.total_users > 1 && (
        <div className="analytics-section">
          <h2>Percentile Rankings</h2>
          <p className="section-description">
            Your performance compared to {percentile.total_users} total users
          </p>
          <div className="percentile-grid">
            <div className="percentile-card">
              <div className="percentile-label">Overall</div>
              <div className="percentile-value">{percentile.overall_percentile.toFixed(1)}th</div>
              <div className="percentile-bar">
                <div
                  className="percentile-fill"
                  style={{ width: `${percentile.overall_percentile}%` }}
                />
              </div>
            </div>

            <div className="percentile-card">
              <div className="percentile-label">Accuracy</div>
              <div className="percentile-value">{percentile.accuracy_percentile.toFixed(1)}th</div>
              <div className="percentile-bar">
                <div
                  className="percentile-fill"
                  style={{ width: `${percentile.accuracy_percentile}%` }}
                />
              </div>
            </div>

            <div className="percentile-card">
              <div className="percentile-label">Speed</div>
              <div className="percentile-value">{percentile.speed_percentile.toFixed(1)}th</div>
              <div className="percentile-bar">
                <div
                  className="percentile-fill"
                  style={{ width: `${percentile.speed_percentile}%` }}
                />
              </div>
            </div>

            <div className="percentile-card">
              <div className="percentile-label">Volume</div>
              <div className="percentile-value">{percentile.volume_percentile.toFixed(1)}th</div>
              <div className="percentile-bar">
                <div
                  className="percentile-fill"
                  style={{ width: `${percentile.volume_percentile}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Strengths and Weaknesses Summary */}
      {(analytics.strongest_subject || analytics.weakest_subject) && (
        <div className="analytics-section">
          <h2>Summary</h2>
          <div className="summary-grid">
            {analytics.strongest_subject && (
              <div className="summary-card success">
                <div className="summary-icon">💪</div>
                <div className="summary-content">
                  <div className="summary-label">Strongest Subject</div>
                  <div className="summary-value">{analytics.strongest_subject}</div>
                </div>
              </div>
            )}

            {analytics.weakest_subject && (
              <div className="summary-card warning">
                <div className="summary-icon">📚</div>
                <div className="summary-content">
                  <div className="summary-label">Needs Most Study</div>
                  <div className="summary-value">{analytics.weakest_subject}</div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
