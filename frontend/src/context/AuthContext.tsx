import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authService } from '@/services';

interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  user_type: 'worker' | 'employer';
  avatar?: string;
  is_verified?: boolean;
  phone?: string;
  location?: string;
  company_name?: string;
  bio?: string;
  hourly_rate?: string | number;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: Record<string, unknown>) => Promise<void>;
  logout: () => void;
  updateUser: (data: Partial<User>) => void;
  fetchProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchProfile = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setIsLoading(false);
        return;
      }
      const { data } = await authService.getProfile();
      const normalizedUser = {
        ...data,
        user_type: (data.user_type || '').toLowerCase()
      };
      setUser(normalizedUser);
    } catch {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  const login = async (email: string, password: string) => {
    const { data } = await authService.login({ email, password });
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    await fetchProfile();
  };

  const register = async (regData: Record<string, unknown>) => {
    try {
      console.log('Registration data being sent:', regData);
      const response = await authService.register(regData);
      console.log('Registration response:', response);

      const { data } = response;
      console.log('Registration data:', data);

      if (!data.access || !data.refresh) {
        console.error('Missing tokens in response:', data);
        throw new Error('Invalid response from server - missing authentication tokens');
      }

      localStorage.setItem('access_token', data.access);
      localStorage.setItem('refresh_token', data.refresh);
      await fetchProfile();
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  };

  const updateUser = (data: Partial<User>) => {
    setUser(prev => prev ? { ...prev, ...data } : null);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, isAuthenticated: !!user, login, register, logout, updateUser, fetchProfile }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
