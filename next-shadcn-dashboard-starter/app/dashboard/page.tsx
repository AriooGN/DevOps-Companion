'use client'
import { redirect } from 'next/navigation';
import { getServerSession } from 'next-auth';
export default  function Dashboard() {
  //const session = await getServerSession();

  // if (!session) {
  //   return redirect('/api/auth/signin');
  // } else {
    redirect('/dashboard/overview');
  //}
}
