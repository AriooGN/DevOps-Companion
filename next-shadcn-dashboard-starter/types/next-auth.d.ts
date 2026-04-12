import NextAuth, { DefaultSession } from 'next-auth';

declare module 'next-auth' {
  type UserSession = DefaultSession['user'];
  interface Session {
    user: UserSession;
    token?: string;
  }

  interface CredentialsInputs {
    email: string;
    password: string;
  }

}
