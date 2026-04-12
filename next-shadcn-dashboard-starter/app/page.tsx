"use effect"
import { redirect } from 'next/navigation';
import { getServerSession } from 'next-auth';

import { getToken } from 'next-auth/jwt';

export default async function middleware() {
    const session = await getServerSession();
    if (!session) {
        return redirect('/api/auth/signin'); 
    } else {
        return redirect('/dashboard'); 
    }
}
