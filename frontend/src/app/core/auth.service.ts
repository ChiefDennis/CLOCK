import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';
import { jwtDecode } from 'jwt-decode';
import { environment } from '../../environments/environment';

export interface UserProfile {
  username: string;
}

interface JwtPayload {
  sub: string;
  exp: number;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private authUrl = `${environment.apiAuthUrl}/login`;
  currentUser = signal<UserProfile | null>(null);

  constructor(private http: HttpClient, private router: Router) {
    this._initializeUserState();
  }

  private _initializeUserState(): void {
    const token = localStorage.getItem('access_token');
    if (token) {
      this._updateUserFromToken(token);
    }
  }

  login(username: string, password: string): Observable<{ access_token: string }> {
    const body = { username, password };

    return this.http.post<{ access_token: string }>(this.authUrl, body).pipe(
      tap(response => {
        if (response?.access_token) {
          localStorage.setItem('access_token', response.access_token);
          this._updateUserFromToken(response.access_token);
          this.router.navigate(['/app/dashboard']);
        }
      })
    );
  }
  
  logout(): void {
    localStorage.removeItem('access_token');
    this.currentUser.set(null);
    this.router.navigate(['/login']);
  }

  // NOTE: This helper method is now the single place where the token is decoded and the user state is set.
  private _updateUserFromToken(token: string): void {
    try {
      const decodedToken: JwtPayload = jwtDecode(token);

      if (Date.now() >= decodedToken.exp * 1000) {
        this.logout();
        return;
      }
      
      // Map the 'sub' property from the token to the 'username' property.
      const userProfile: UserProfile = {
        username: decodedToken.sub
      };
      
      this.currentUser.set(userProfile);

    } catch (error) {
      console.error("Failed to process token:", error);
      this.currentUser.set(null);
    }
  }

  isAuthenticated(): boolean {
    const token = localStorage.getItem('access_token');
    if (!token) return false;

    try {
      const decodedToken: JwtPayload = jwtDecode(token);
      return !this.isTokenExpired(decodedToken);
    } catch (error) {
      return false;
    }
  }

  private isTokenExpired(token: any): boolean {
    if (!token.exp) return true;
    const isExpired = Date.now() >= token.exp * 1000;
    return isExpired;
  }
}