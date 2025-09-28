// core/auth-interceptor.ts

import { HttpInterceptorFn } from '@angular/common/http';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  // 1. Get the token from localStorage
  const authToken = localStorage.getItem('auth_token');

  if (authToken) {
    // 2. If the token exists, clone the request and add the Authorization header
    const clonedReq = req.clone({
      headers: req.headers.set('Authorization', `Bearer ${authToken}`)
    });
    // 3. Pass the new, cloned request to the next handler
    return next(clonedReq);
  }

  // If no token, pass the original request along
  return next(req);
};