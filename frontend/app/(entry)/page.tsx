import Link from 'next/link';
import { RootRedirect } from '@/features/root-redirect';
export default function Page(){return <main style={{padding:40}}><RootRedirect/><h1>Los Espinosaurios</h1><Link href="/en/">Enter the research hub →</Link></main>;}
