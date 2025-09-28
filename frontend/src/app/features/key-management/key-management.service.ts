// src/app/key-management/key-management.service.ts

import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { map, tap } from 'rxjs/operators';
import { Key } from './key.model';
import { environment } from '../../../environments/environment';

export interface CreateKeyRequest {
  cloud_provider: 'aws' | 'azure' | 'gcp';
  algorithm: string;
  purpose: 'ENCRYPT_DECRYPT' | 'SIGN_VERIFY';
  protection_level: 'HSM' | 'SOFTWARE';
  description: string;
  labels: Record<string, string>;
  rotation_enabled: boolean;
  rotation_days: number;
}

@Injectable({
  providedIn: 'root'
})
export class KeyManagementService {
  private apiUrl = `${environment.apiBaseUrl}`;
  private keysCache: Key[] | null = null;

  constructor(private http: HttpClient) { }

  private getAuthHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token') || '';
    return new HttpHeaders({ Authorization: `Bearer ${token}` });
  }

  listLocalKeys(filters?: any): Observable<Key[]> {
    let params = new HttpParams();
    if (filters) {
      Object.keys(filters).forEach(key => {
        if (filters[key]) {
          params = params.append(key, filters[key]);
        }
      });
    }
    return this.http.get<Key[]>(`${this.apiUrl}/list-local-keys`, { headers: this.getAuthHeaders(), params })
      .pipe(
        tap(keys => this.keysCache = keys)
      );
  }

  getLocalKeyById(id: number): Observable<Key | undefined> {
    if (this.keysCache) {
      const key = this.keysCache.find(k => k.id === id);
      return of(key);
    }
    return this.listLocalKeys().pipe(
      map(keys => keys.find(k => k.id === id))
    );
  }

  createKey(keyData: CreateKeyRequest): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/create-key`, keyData, { headers: this.getAuthHeaders() })
      .pipe(
        tap(() => {
          this.keysCache = null;
        })
      );
  }
  
  /** POST: Enables or disables a key. */
  setEnabled(provider: string, keyId: string, enabled: boolean): Observable<any> {
    const body = {
      cloud_provider: provider,
      key_id: keyId,
      enabled: enabled
    };
    return this.http.post<any>(`${this.apiUrl}/set-enabled`, body, { headers: this.getAuthHeaders() })
      .pipe(
        tap(() => {
          // Invalidate the cache on success
          this.keysCache = null;
        })
      );
  }

  /** POST: Configures a key's rotation policy. */
  setRotation(provider: string, keyId: string, enabled: boolean, rotation_days: number): Observable<any> {
    // Conditionally build the body
    const body: any = {
      cloud_provider: provider,
      key_id: keyId,
      enabled: enabled,
    };

    if (enabled) {
      body.rotation_days = rotation_days;
    }

    return this.http.post<any>(`${this.apiUrl}/set-rotation`, body, { headers: this.getAuthHeaders() })
      .pipe(
        tap(() => {
          // Invalidate the cache on success
          this.keysCache = null;
        })
      );
  }

  /**
   * POST: Schedules a key for deletion.
   * @param provider The cloud provider ('aws', 'azure', 'gcp').
   * @param keyId The unique identifier for the key.
   * @param scheduleDays The number of days to wait before permanent deletion.
   */
  deleteKey(provider: string, keyId: string, scheduleDays: number): Observable<any> {
    const body = {
      cloud_provider: provider,
      key_id: keyId,
      schedule_days: scheduleDays
    };
    return this.http.post<any>(`${this.apiUrl}/delete-key`, body, { headers: this.getAuthHeaders() })
      .pipe(
        tap(() => {
          // Invalidate the cache on success
          this.keysCache = null;
        })
      );
  }

    /** POST: Encrypts plaintext using a specified key. */
  encrypt(provider: string, keyId: string, plaintext: string): Observable<{ ciphertext: string }> {
    const body = {
      cloud_provider: provider,
      key_id: keyId,
      plaintext: plaintext
    };
    return this.http.post<{ ciphertext: string }>(`${this.apiUrl}/encrypt`, body, { headers: this.getAuthHeaders() });
  }

  /** POST: Decrypts ciphertext using a specified key. */
  decrypt(provider: string, keyId: string, ciphertext: string): Observable<{ plaintext: string }> {
    const body = {
      cloud_provider: provider,
      key_id: keyId,
      ciphertext: ciphertext
    };
    return this.http.post<{ plaintext: string }>(`${this.apiUrl}/decrypt`, body, { headers: this.getAuthHeaders() });
  }
}