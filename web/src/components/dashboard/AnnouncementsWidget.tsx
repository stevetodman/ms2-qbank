import { DashboardWidget } from './DashboardWidget.tsx';

export interface DashboardAnnouncement {
  id: string;
  title: string;
  message: string;
  dateLabel: string;
  actionLabel?: string;
  onAction?: () => void;
}

interface AnnouncementsWidgetProps {
  announcements: DashboardAnnouncement[];
}

export const AnnouncementsWidget = ({ announcements }: AnnouncementsWidgetProps) => {
  return (
    <DashboardWidget
      title="Announcements"
      description="Stay informed about platform updates and scheduled maintenance."
    >
      <ul className="dashboard-announcements">
        {announcements.map((announcement) => (
          <li key={announcement.id} className="dashboard-announcements__item">
            <div className="dashboard-announcements__header">
              <h3>{announcement.title}</h3>
              <span className="dashboard-announcements__date">{announcement.dateLabel}</span>
            </div>
            <p>{announcement.message}</p>
            {announcement.actionLabel && announcement.onAction && (
              <button type="button" className="secondary-button" onClick={announcement.onAction}>
                {announcement.actionLabel}
              </button>
            )}
          </li>
        ))}
      </ul>
    </DashboardWidget>
  );
};
