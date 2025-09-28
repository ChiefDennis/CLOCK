// src/app/features/users/user.service.ts

import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface User {
  id: number;
  username: string;
  role: 'admin' | 'user';
  enabled: boolean;
}

export interface CreateUserPayload {
  username: string;
  role: 'admin' | 'user';
  password?: string;
}

// Added the 'export' keyword here
export type UpdateUserPayload = Partial<Omit<User, 'id'>>;

@Injectable({
  providedIn: 'root'
})
export class UserService {
  private apiUrl = `${environment.apiBaseUrl}/users`;

  constructor(private http: HttpClient) {}

  private getAuthHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token') || '';
    return new HttpHeaders({ Authorization: `Bearer ${token}` });
  }

  getUsers(): Observable<User[]> {
    return this.http.get<User[]>(this.apiUrl, { headers: this.getAuthHeaders() });
  }

  createUser(user: CreateUserPayload): Observable<User> {
    return this.http.post<User>(this.apiUrl, user, { headers: this.getAuthHeaders() });
  }

  updateUser(id: number, payload: UpdateUserPayload): Observable<User> {
    return this.http.patch<User>(`${this.apiUrl}/${id}`, payload, { headers: this.getAuthHeaders() });
  }

  deleteUser(id: number): Observable<any> {
    return this.http.delete<any>(`${this.apiUrl}/${id}`, { headers: this.getAuthHeaders() });
  }
}