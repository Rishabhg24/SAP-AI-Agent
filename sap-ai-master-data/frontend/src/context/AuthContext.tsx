import React, { createContext, useContext, useState, useEffect } from 'react';
import type { AuthUser, LoginCredentials, SapCompany } from '../types';
import { api } from '../services/api';

interface AuthContextType {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  activeCompanyDb: string;
  activeCompanyName: string;
  availableCompanies: SapCompany[];
  login: (credentials: LoginCredentials) => Promise<boolean>;
  demoLogin: () => void;
  googleLogin: () => void;
  logout: () => void;
  switchCompany: (companyDb: string) => Promise<boolean>;
  refreshCompanies: () => Promise<void>;
}

const STORAGE_KEY = 'sap_ai_master_data_user';
const COMPANY_STORAGE_KEY = 'sap_ai_master_data_company';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [activeCompanyDb, setActiveCompanyDb] = useState<string>('TEST_SHOES_10SEP26');
  const [activeCompanyName, setActiveCompanyName] = useState<string>('TEST_SHOES_10SEP26 (SAP Live)');
  const [availableCompanies, setAvailableCompanies] = useState<SapCompany[]>([]);

  // Fetch configured companies from backend
  const refreshCompanies = async () => {
    try {
      const res = await api.getSapCompanies();
      if (res?.companies) {
        setAvailableCompanies(res.companies);
        if (res.active_company_db) {
          setActiveCompanyDb(res.active_company_db);
        }
        if (res.active_company_name) {
          setActiveCompanyName(res.active_company_name);
        }
      }
    } catch (e) {
      console.warn('Could not fetch SAP companies list:', e);
    }
  };

  // Rehydrate auth state and company from localStorage on load
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed && parsed.email) {
          setUser(parsed);
          if (parsed.companyDb) {
            setActiveCompanyDb(parsed.companyDb);
          }
          if (parsed.companyName) {
            setActiveCompanyName(parsed.companyName);
          }
        }
      }
      const storedCompany = localStorage.getItem(COMPANY_STORAGE_KEY);
      if (storedCompany) {
        setActiveCompanyDb(storedCompany);
      }
    } catch (e) {
      console.warn('Could not restore auth session:', e);
    } finally {
      setIsLoading(false);
    }

    refreshCompanies();
  }, []);

  const switchCompany = async (companyDb: string): Promise<boolean> => {
    try {
      const res = await api.selectSapCompany(companyDb, user?.email);
      if (res?.success) {
        setActiveCompanyDb(res.active_company_db || companyDb);
        setActiveCompanyName(res.active_company_name || companyDb);
        localStorage.setItem(COMPANY_STORAGE_KEY, res.active_company_db || companyDb);
        if (user) {
          const updatedUser: AuthUser = {
            ...user,
            companyDb: res.active_company_db || companyDb,
            companyName: res.active_company_name || companyDb,
          };
          setUser(updatedUser);
          localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedUser));
        }
        await refreshCompanies();
        return true;
      }
      return false;
    } catch (err) {
      console.error('Failed to switch company database:', err);
      return false;
    }
  };

  const login = async (credentials: LoginCredentials): Promise<boolean> => {
    setIsLoading(true);
    try {
      await new Promise((resolve) => setTimeout(resolve, 350));

      const email = credentials.email.trim();
      const targetDb = credentials.companyDb || activeCompanyDb || 'TEST_SHOES_10SEP26';
      const namePart = email.split('@')[0] || 'User';
      const formattedName = namePart
        .split(/[\._\-]/)
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
        .join(' ') || 'SAP Master User';

      const authUser: AuthUser = {
        email: email,
        name: formattedName,
        role: 'SAP Master Data Specialist',
        companyDb: targetDb,
        companyName: activeCompanyName,
        avatarUrl: '/user_avatars.jpg',
        loginTime: new Date().toISOString()
      };

      setUser(authUser);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(authUser));

      if (targetDb !== activeCompanyDb) {
        await switchCompany(targetDb);
      }

      return true;
    } catch (err) {
      console.error('Login error:', err);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const demoLogin = () => {
    const demoUser: AuthUser = {
      email: 'alex.johnson@cinntra.com',
      name: 'Alex Johnson',
      role: 'Chief SAP Solutions Architect',
      companyDb: activeCompanyDb,
      companyName: activeCompanyName,
      avatarUrl: '/user_avatars.jpg',
      loginTime: new Date().toISOString()
    };
    setUser(demoUser);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(demoUser));
  };

  const googleLogin = () => {
    const googleUser: AuthUser = {
      email: 'alex.enterprise@gmail.com',
      name: 'Alex Johnson',
      role: 'Enterprise Data Admin',
      companyDb: activeCompanyDb,
      companyName: activeCompanyName,
      avatarUrl: '/user_avatars.jpg',
      loginTime: new Date().toISOString()
    };
    setUser(googleUser);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(googleUser));
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem(STORAGE_KEY);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        activeCompanyDb,
        activeCompanyName,
        availableCompanies,
        login,
        demoLogin,
        googleLogin,
        logout,
        switchCompany,
        refreshCompanies
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

