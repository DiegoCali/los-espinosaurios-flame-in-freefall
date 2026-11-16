'use client';
import {useEffect} from 'react';
import {asset} from '@/shared/config';
export function RootRedirect(){useEffect(()=>{window.location.replace(asset('/en/'));},[]);return null;}
