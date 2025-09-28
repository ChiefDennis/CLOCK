/**
 * Represents a single alarm record, matching the backend's data model.
 */
export interface Alarm {
  id: number;
  timestamp: string;
  // We define this as a generic string to handle any casing from the API.
  severity: string; 
  event_type: string;
  message: string;
  is_acknowledged: boolean;
}

/**
 * Represents the structure of the paginated API response when fetching alarms.
 */
export interface AlarmApiResponse {
  alarms: Alarm[];
  next_page_token: number | null;
}