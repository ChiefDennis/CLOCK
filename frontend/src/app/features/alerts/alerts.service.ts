import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Alarm, AlarmApiResponse } from './alerts.model';

@Injectable({
  providedIn: 'root'
})
export class AlertsService {
  private apiUrl = `${environment.apiBaseUrl}/alarms`;

  constructor(private http: HttpClient) { }

  private getAuthHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token') || '';
    return new HttpHeaders({ Authorization: `Bearer ${token}` });
  }

  getAlarms(pageSize: number = 20, pageToken?: number): Observable<AlarmApiResponse> {
    let params = new HttpParams().set('page_size', pageSize.toString());
    if (pageToken) {
      params = params.set('page_token', pageToken.toString());
    }
    return this.http.get<AlarmApiResponse>(this.apiUrl, {
      headers: this.getAuthHeaders(),
      params: params
    });
  }

  acknowledgeAlarm(alarmId: number): Observable<Alarm> {
    const updatePayload = { is_acknowledged: true };
    return this.http.patch<Alarm>(`${this.apiUrl}/${alarmId}`, updatePayload, {
      headers: this.getAuthHeaders()
    });
  }

  /**
   * Sends a PATCH request to set an alarm back to its active state.
   * @param alarmId The ID of the alarm to re-activate.
   * @returns An Observable of the updated alarm object.
   */
  unacknowledgeAlarm(alarmId: number): Observable<Alarm> {
    const updatePayload = { is_acknowledged: false };
    return this.http.patch<Alarm>(`${this.apiUrl}/${alarmId}`, updatePayload, {
      headers: this.getAuthHeaders()
    });
  }
}