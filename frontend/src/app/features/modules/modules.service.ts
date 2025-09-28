import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface ModuleStatus {
  provider_name: 'aws' | 'azure' | 'gcp';
  is_enabled: boolean;
  last_synced_at?: string | null;
}

export interface SyncResult {
  provider: string;
  status: string;
  summary: {
    added: number;
    updated: number;
    removed: number;
    finalized: number;
  };
}

@Injectable({
  providedIn: 'root'
})
export class ModulesService {
  private apiUrl = `${environment.apiBaseUrl}`;

  constructor(private http: HttpClient) {}

  private getAuthHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token') || '';
    return new HttpHeaders({
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    });
  }

  getModulesStatus(): Observable<ModuleStatus[]> {
    return this.http.get<ModuleStatus[]>(`${this.apiUrl}/modules/status`, { headers: this.getAuthHeaders() });
  }

  setModuleStatus(provider: string, isEnabled: boolean): Observable<ModuleStatus> {
    const body = { is_enabled: isEnabled };
    return this.http.patch<ModuleStatus>(`${this.apiUrl}/modules/status/${provider}`, body, { headers: this.getAuthHeaders() });
  }

  syncProvider(provider: string): Observable<SyncResult> {
    const body = { cloud_provider: provider };
    return this.http.post<SyncResult>(`${this.apiUrl}/sync`, body, { headers: this.getAuthHeaders() });
  }
}