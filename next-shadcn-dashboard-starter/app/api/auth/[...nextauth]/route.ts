import NextAuth from "next-auth";
import AzureADProvider from "next-auth/providers/azure-ad";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { flaskApiUrl } from "@/lib/flask-api";

const { AZURE_AD_CLIENT_ID, AZURE_AD_CLIENT_SECRET, AZURE_AD_TENANT_ID } =
  process.env;

const azureConfigured = Boolean(
  AZURE_AD_CLIENT_ID && AZURE_AD_CLIENT_SECRET && AZURE_AD_TENANT_ID
);

const authHandler = azureConfigured
  ? NextAuth({
      secret: process.env.NEXTAUTH_SECRET,
      providers: [
        AzureADProvider({
          clientId: AZURE_AD_CLIENT_ID!,
          clientSecret: AZURE_AD_CLIENT_SECRET!,
          tenantId: AZURE_AD_TENANT_ID!,
        }),
      ],
      callbacks: {
        async jwt({ token, account }) {
          if (account) {
            token = Object.assign({}, token, {
              access_token: account.access_token,
            });
          }
          return token;
        },
        async session({ session, token }) {
          if (session) {
            session = Object.assign({}, session, {
              access_token: token.access_token,
            });
          }
          try {
            const response = await fetch(
              flaskApiUrl("/api/receive-token"),
              {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                },
                body: JSON.stringify(session),
              }
            );
            await response.json();
          } catch {
            // Flask backend may be offline during local dev
          }
          return session;
        },
      },
    })
  : null;

function envMissingResponse() {
  return NextResponse.json(
    {
      error: "The Azure AD environment variables are not set.",
      required: [
        "AZURE_AD_CLIENT_ID",
        "AZURE_AD_CLIENT_SECRET",
        "AZURE_AD_TENANT_ID",
        "NEXTAUTH_SECRET",
        "NEXTAUTH_URL",
      ],
      hint: "Copy .env.example to .env.local in the project root and set the variables. Add redirect URI http://localhost:3000/api/auth/callback/azure-ad in Azure.",
    },
    { status: 503 }
  );
}

export async function GET(
  req: NextRequest,
  context: { params: { nextauth: string[] } }
) {
  if (!authHandler) return envMissingResponse();
  return authHandler(req, context);
}

export async function POST(
  req: NextRequest,
  context: { params: { nextauth: string[] } }
) {
  if (!authHandler) return envMissingResponse();
  return authHandler(req, context);
}
