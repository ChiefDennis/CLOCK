// src/app/core/pending-actions.service.ts

import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface PendingAction {
  id: number;
  action_type: string;
  resource_id: string;
  created_by: string;
  created_at: string;
  expires_at: string;
  status: string;
  reviewed_by?: string;
  reviewed_at?: string;
}

@Injectable({
  providedIn: 'root'
})
export class PendingActionsService {
  private apiUrl = `${environment.apiBaseUrl}/pending-actions`;

  constructor(private http: HttpClient) {}

  private getAuthHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token') || '';
    return new HttpHeaders({ Authorization: `Bearer ${token}` });
  }

  getPendingActions(): Observable<PendingAction[]> {
    return this.http.get<PendingAction[]>(this.apiUrl, { headers: this.getAuthHeaders() });
  }

  approveAction(id: number): Observable<any> {
    return this.http.post(`${this.apiUrl}/${id}/approve`, {}, { headers: this.getAuthHeaders() });
  }

  denyAction(id: number): Observable<any> {
    return this.http.post(`${this.apiUrl}/${id}/deny`, {}, { headers: this.getAuthHeaders() });
  }
}
