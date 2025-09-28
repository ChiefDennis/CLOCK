import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface Log {
  id: number;
  username: string;
  role: string;
  method: string;
  endpoint: string;
  status_code: number;
  request_data: string;
  response_data: string;
  action: string;
  timestamp: string;
}

export interface LogsApiResponse {
  logs: Log[];
  next_page_token: number | null;
}

@Injectable({
  providedIn: 'root'
})
export class LogService {
  private apiUrl = `${environment.apiBaseUrl}/logs`;

  constructor(private http: HttpClient) {}

  private getAuthHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token') || '';
    return new HttpHeaders({ Authorization: `Bearer ${token}` });
  }

  /**
   * Gets a paginated list of logs from the API.
   * @param pageSize The number of log entries per page.
   * @param pageToken The ID from the previous page to fetch the next set.
   */
  getLogs(pageSize: number = 50, pageToken?: number): Observable<LogsApiResponse> {
    let params = new HttpParams().set('page_size', pageSize.toString());
    if (pageToken) {
      params = params.set('page_token', pageToken.toString());
    }

    return this.http.get<LogsApiResponse>(this.apiUrl, {
      headers: this.getAuthHeaders(),
      params: params
    });
  }
}